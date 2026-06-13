#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

import plan_validator
from vg_overview import collect_vg_overview


PYTEST_TESTS_CMD = ["python3", "-m", "pytest", "cli/lib/tests/", "-q"]
PYTEST_CATALOG_CMD = ["python3", "-m", "pytest", "cli/lib/tests/test_command_catalog.py", "-q"]
SECRET_CMD = ["pre-commit", "run", "--all-files"]
DESTRUCTIVE_PATTERNS = [
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bgit\s+branch\s+-D\b"),
    re.compile(r"\brm\s+-rf\b"),
    re.compile(r"(?:^|[^\w-])--force(?:[=\s]|$)"),
    re.compile(r"(?:^|[^\w-])--no-verify(?:[=\s]|$)"),
]
DESTRUCTIVE_EXCLUDED_PREFIXES = (
    "cli/lib/tests/",
    "cli/tests/",
    # cli/helix-test is the bats-lite runner and cleans mktemp tmpdirs like cli/tests/ test infra.
    "cli/helix-test",
    "tests/",
    "docs/",
)
DESTRUCTIVE_ROLLBACK_PREFIX = "cli/migrations/rollback/"
DESTRUCTIVE_DIFF_HEADER = re.compile(r"^diff --git a/(.+) b/(.+)$")
CONTRACT_GATE_ENUM_RE = re.compile(r"enum:\s*\[([^\]]+)\]")
GATE_IDS = (
    "G-tests",
    "G-catalog",
    "G-secret",
    "G-ff",
    "G-attr",
    "G-nondestructive",
    "G-review",
)
MAIN_BRANCH = "main"


def _repo_root() -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git repository not found")
    return Path(proc.stdout.strip()).resolve()


def _run_command(
    command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def _hermetic_test_env() -> dict[str, str]:
    """テスト subprocess へ渡す env から gate/automation 文脈変数を除去する。

    gate (helix push) は自身の automation run のため HELIX_AUTOMATION_RUN_ID を
    ambient に設定する。これを pytest/bats が継承すると、tmp DB に存在しない run_id を
    参照して FK 違反/automation 記録汚染を起こし hermetic test が間欠 fail する
    (pytest 側 conftest scrub と同じ隔離を runner 側でも適用し bats もカバーする)。
    """
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("HELIX_AUTOMATION_") and key != "HELIX_ASKUSERQUESTION_NOW"
    }


def _result(gate_id: str, passed: bool, detail: str, fix: str) -> dict:
    return {
        "id": gate_id,
        "passed": passed,
        "detail": detail,
        "fix": fix,
    }


def _parse_pytest_count(stdout: str, stderr: str) -> str | None:
    text = "\n".join(part for part in (stdout, stderr) if part).strip()
    match = re.search(r"(\d+)\s+passed", text)
    if match:
        return match.group(1)
    return None


def _parse_bats_count(stdout: str, stderr: str) -> str | None:
    text = "\n".join(part for part in (stdout, stderr) if part).strip()
    match = re.search(r"1\.\.(\d+)", text)
    if match:
        return match.group(1)
    match = re.search(r"(\d+)\s+tests?,\s+0\s+failures", text)
    if match:
        return match.group(1)
    return None


def _format_failure(proc: subprocess.CompletedProcess[str]) -> str:
    text = (proc.stderr or proc.stdout or "").strip()
    if not text:
        return f"exit {proc.returncode}"
    return text.splitlines()[-1]


def _parse_diff_path(raw_line: str) -> str | None:
    match = DESTRUCTIVE_DIFF_HEADER.match(raw_line)
    if not match:
        return None
    return match.group(2)


def _is_excluded_destructive_path(path: str) -> bool:
    pure_path = PurePosixPath(path)
    path_text = pure_path.as_posix()
    if path_text.startswith(DESTRUCTIVE_EXCLUDED_PREFIXES):
        return True
    return path_text.startswith(DESTRUCTIVE_ROLLBACK_PREFIX) and path_text.endswith(".sql")


def _plan_doc_matches(project_root: Path, plan_id: str) -> list[Path]:
    docs_plans = project_root / "docs" / "plans"
    if not docs_plans.exists():
        return []
    return sorted(path for path in docs_plans.glob(f"**/{plan_id}.md") if path.is_file())


def _resolve_plan_path(project_root: Path, plan_id: str) -> Path:
    matches = _plan_doc_matches(project_root, plan_id)
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ValueError(f"plan markdown not found: {plan_id}")
    raise ValueError(f"multiple plan markdown files found: {plan_id}")


def _load_handover_plan_id(project_root: Path) -> str | None:
    handover_path = project_root / ".helix" / "handover" / "CURRENT.json"
    if not handover_path.is_file():
        return None
    try:
        payload = json.loads(handover_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    candidates = _collect_plan_ids(payload)
    unique = sorted({candidate for candidate in candidates if candidate})
    if len(unique) != 1:
        return None
    return unique[0]


def _collect_plan_ids(value: Any) -> list[str]:
    if isinstance(value, dict):
        collected: list[str] = []
        for key, item in value.items():
            if key == "plan_id" and isinstance(item, str) and item.strip():
                collected.append(item.strip())
            else:
                collected.extend(_collect_plan_ids(item))
        return collected
    if isinstance(value, list):
        collected: list[str] = []
        for item in value:
            collected.extend(_collect_plan_ids(item))
        return collected
    return []


def _git_upstream_ref(project_root: Path) -> str | None:
    proc = _run_command(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
        cwd=project_root,
    )
    if proc.returncode != 0:
        return None
    upstream = (proc.stdout or "").strip()
    return upstream or None


def _ahead_commit_plan_ids(project_root: Path) -> list[str]:
    upstream = _git_upstream_ref(project_root)
    if not upstream:
        return []
    proc = _run_command(
        ["git", "diff", "--name-only", f"{upstream}..HEAD", "--", "docs/plans"],
        cwd=project_root,
    )
    if proc.returncode != 0:
        return []
    plan_ids = {
        Path(line.strip()).stem
        for line in proc.stdout.splitlines()
        if line.strip().startswith("docs/plans/") and line.strip().endswith(".md")
    }
    return sorted(plan_ids)


def _resolve_review_plan_id(plan_id: str | None, project_root: Path) -> str:
    explicit = plan_id.strip() if isinstance(plan_id, str) and plan_id.strip() else None
    handover = _load_handover_plan_id(project_root)
    ahead = _ahead_commit_plan_ids(project_root)

    if explicit and handover and explicit != handover:
        raise ValueError(f"plan_id mismatch: explicit={explicit} handover={handover}")
    if explicit and len(ahead) == 1 and explicit != ahead[0]:
        raise ValueError(f"plan_id mismatch: explicit={explicit} ahead={ahead[0]}")
    if explicit and len(ahead) > 1 and explicit not in ahead:
        raise ValueError(f"plan_id mismatch: explicit={explicit} ahead={ahead}")
    if handover and len(ahead) > 1 and handover not in ahead:
        raise ValueError(f"plan_id mismatch: handover={handover} ahead={ahead}")
    if handover and len(ahead) == 1 and handover != ahead[0]:
        raise ValueError(f"plan_id mismatch: handover={handover} ahead={ahead[0]}")
    if len(ahead) > 1 and not explicit:
        raise ValueError(f"multiple ahead PLAN candidates: {ahead}")

    chosen = explicit or handover
    if chosen:
        return chosen
    if len(ahead) == 1:
        return ahead[0]
    if len(ahead) > 1:
        raise ValueError(f"multiple ahead PLAN candidates: {ahead}")
    raise ValueError("plan_id is required: explicit/handover/ahead commit candidate not found")


def _all_review_plan_ids(plan_id: str | None, project_root: Path) -> list[str]:
    resolved_plan_id = _resolve_review_plan_id(plan_id, project_root)
    ahead = _ahead_commit_plan_ids(project_root)
    if len(ahead) > 1:
        return ahead
    if len(ahead) == 1:
        return ahead
    return [resolved_plan_id]


def _contract_gate_ids(contract_path: Path) -> list[str]:
    text = contract_path.read_text(encoding="utf-8")
    match = CONTRACT_GATE_ENUM_RE.search(text)
    if not match:
        raise ValueError(f"gate enum not found: {contract_path}")
    return [item.strip() for item in match.group(1).split(",") if item.strip()]


def run_gate_tests() -> dict:
    repo_root = _repo_root()
    test_env = _hermetic_test_env()
    pytest_proc = _run_command(PYTEST_TESTS_CMD, cwd=repo_root, env=test_env)
    if pytest_proc.returncode != 0:
        return _result(
            "G-tests",
            False,
            f"pytest FAIL: {_format_failure(pytest_proc)}",
            "テスト fail を修正してから再実行",
        )

    bats_files = sorted(str(path.relative_to(repo_root)) for path in (repo_root / "cli" / "tests").glob("*.bats"))
    if not bats_files:
        return _result(
            "G-tests",
            False,
            "bats FAIL: no .bats files found under cli/tests",
            "テスト fail を修正してから再実行",
        )

    bats_proc = _run_command(["bats", *bats_files], cwd=repo_root, env=test_env)
    if bats_proc.returncode != 0:
        return _result(
            "G-tests",
            False,
            f"bats FAIL: {_format_failure(bats_proc)}",
            "テスト fail を修正してから再実行",
        )

    pytest_count = _parse_pytest_count(pytest_proc.stdout, pytest_proc.stderr) or "pytest PASS"
    bats_count = _parse_bats_count(bats_proc.stdout, bats_proc.stderr) or "bats PASS"
    return _result("G-tests", True, f"pytest {pytest_count} + bats {bats_count}", "なし")


def run_gate_catalog() -> dict:
    repo_root = _repo_root()
    proc = _run_command(PYTEST_CATALOG_CMD, cwd=repo_root)
    if proc.returncode != 0:
        return _result(
            "G-catalog",
            False,
            f"test_command_catalog FAIL: {_format_failure(proc)}",
            "help/docs 同期不足、`helix commands` 確認",
        )

    count = _parse_pytest_count(proc.stdout, proc.stderr) or "PASS"
    return _result("G-catalog", True, f"{count} PASS", "なし")


def run_gate_secret() -> dict:
    repo_root = _repo_root()
    try:
        proc = _run_command(SECRET_CMD, cwd=repo_root)
    except FileNotFoundError:
        # pre-commit 不在: scripts/git-hooks/pre-commit (in-repo gitleaks) を直接呼ぶ
        in_repo_hook = repo_root / "scripts" / "git-hooks" / "pre-commit"
        if in_repo_hook.exists():
            proc = _run_command(["bash", str(in_repo_hook)], cwd=repo_root)
            if proc.returncode != 0:
                return _result(
                    "G-secret",
                    False,
                    f"in-repo pre-commit hook FAIL: {_format_failure(proc)}",
                    "secret detected、staged change を確認",
                )
            return _result("G-secret", True, "in-repo pre-commit hook PASS", "なし")
        return _result(
            "G-secret",
            True,
            "pre-commit / in-repo hook 不在 → skip (warning)",
            "pre-commit インストール推奨: pip install pre-commit",
        )
    if proc.returncode != 0:
        return _result(
            "G-secret",
            False,
            f"pre-commit FAIL: {_format_failure(proc)}",
            "secret detected、staged change を確認",
        )
    return _result("G-secret", True, "pre-commit PASS", "なし")


def run_gate_ff(remote: str = "origin", branch: str = "main") -> dict:
    repo_root = _repo_root()
    fetch_proc = _run_command(["git", "fetch", remote, branch], cwd=repo_root)
    if fetch_proc.returncode != 0:
        return _result(
            "G-ff",
            False,
            f"git fetch FAIL: {_format_failure(fetch_proc)}",
            "rebase 必要、`git pull --rebase origin main`",
        )

    target_ref = f"{remote}/{branch}"
    proc = _run_command(["git", "merge-base", "--is-ancestor", target_ref, "HEAD"], cwd=repo_root)
    if proc.returncode != 0:
        return _result(
            "G-ff",
            False,
            f"{target_ref} is not an ancestor of HEAD",
            "rebase 必要、`git pull --rebase origin main`",
        )
    return _result("G-ff", True, f"{target_ref} fast-forward OK", "なし")


def run_gate_attr(remote: str = "origin", branch: str = "main") -> dict:
    repo_root = _repo_root()
    range_ref = f"{remote}/{branch}..HEAD"
    count_proc = _run_command(["git", "rev-list", "--count", range_ref], cwd=repo_root)
    if count_proc.returncode != 0:
        return _result(
            "G-attr",
            False,
            f"git rev-list FAIL: {_format_failure(count_proc)}",
            "commit 修正必要 (amend or rebase -i)",
        )

    total = int((count_proc.stdout or "0").strip() or "0")
    match_proc = _run_command(
        ["git", "log", range_ref, "--format=%H", "--grep", "Co-Authored-By"],
        cwd=repo_root,
    )
    if match_proc.returncode != 0:
        return _result(
            "G-attr",
            False,
            f"git log FAIL: {_format_failure(match_proc)}",
            "commit 修正必要 (amend or rebase -i)",
        )

    matched = len([line for line in match_proc.stdout.splitlines() if line.strip()])
    if matched != total:
        return _result(
            "G-attr",
            False,
            f"{total} commits / {matched} with Co-Authored-By",
            "commit 修正必要 (amend or rebase -i)",
        )
    return _result("G-attr", True, f"{total} commits / {matched} with Co-Authored-By", "なし")


def run_gate_nondestructive(remote: str = "origin", branch: str = "main") -> dict:
    repo_root = _repo_root()
    range_ref = f"{remote}/{branch}..HEAD"
    proc = _run_command(["git", "diff", "--unified=0", range_ref], cwd=repo_root)
    if proc.returncode != 0:
        return _result(
            "G-nondestructive",
            False,
            f"git diff FAIL: {_format_failure(proc)}",
            "destructive operation 検出、manual-confirm 必要",
        )

    offenders: list[str] = []
    current_path: str | None = None
    for raw_line in proc.stdout.splitlines():
        parsed_path = _parse_diff_path(raw_line)
        if parsed_path is not None:
            current_path = parsed_path
            continue
        if not raw_line.startswith("+") or raw_line.startswith("+++"):
            continue
        if current_path and _is_excluded_destructive_path(current_path):
            continue
        line = raw_line[1:]
        for pattern in DESTRUCTIVE_PATTERNS:
            match = pattern.search(line)
            if match:
                path = current_path or "<unknown>"
                offenders.append(f"{match.group(0).strip()} in {path}")
                break

    if offenders:
        return _result(
            "G-nondestructive",
            False,
            f"destructive pattern: {offenders[0]}",
            "destructive operation 検出、manual-confirm 必要",
        )
    return _result("G-nondestructive", True, "no destructive pattern", "なし")


def _is_approved_deferred_add_feature_boundary(frontmatter: dict[str, Any]) -> bool:
    """Return True only for strictly guarded deferred add-feature boundary tickets.

    `layer == "L7"` は条件に含めない。実データでは正当な境界チケット 11 件の layer が
    L7 だけでなく L6 / L5-L6 / L8-L14 に分散しており、layer 固定にすると正当な
    boundary ticket を誤って拒否する。一方で workflow/add-feature, draft+approve,
    approval boundary 文言, YAML boolean の approval_required_before_*,
    current_task_scope, unlock_conditions の AND で十分に狭く特定できる。
    """

    approval_boundary = frontmatter.get("approval_boundary")
    unlock_conditions = frontmatter.get("unlock_conditions")
    return (
        # plan_scope は default 補完せず明示要求する。gate 本体の default("action") より厳格にし、未宣言 draft の誤 exempt を防ぐ。
        frontmatter.get("plan_scope") == "action"
        and frontmatter.get("workflow") == "add-feature"
        and str(frontmatter.get("status", "")).strip() == "draft"
        and str(frontmatter.get("tl_review", "")).strip() == "approve"
        and isinstance(approval_boundary, str)
        and approval_boundary.strip() != ""
        and "approv" in approval_boundary.lower()
        and any(
            key.startswith("approval_required_before_") and value is True
            for key, value in frontmatter.items()
        )
        and frontmatter.get("current_task_scope")
        in {"feature_ticket_only", "L4_L6_design_closed_feature_ticketed"}
        and (
            (isinstance(unlock_conditions, str) and unlock_conditions.strip() != "")
            or (isinstance(unlock_conditions, list) and len(unlock_conditions) > 0)
        )
    )


def run_gate_review(plan_id: str | None, project_root: str | Path) -> dict:
    root = Path(project_root).resolve()
    try:
        review_plan_ids = _all_review_plan_ids(plan_id, root)
    except ValueError as exc:
        return _result(
            "G-review",
            False,
            str(exc),
            "PLAN 特定 (--plan-id / handover / ahead commit) と docs/plans frontmatter を確認",
        )

    reviewed: list[str] = []
    violations: list[str] = []
    try:
        for review_plan_id in review_plan_ids:
            plan_path = _resolve_plan_path(root, review_plan_id)
            frontmatter = plan_validator.load_frontmatter(plan_path)
            status = str(frontmatter.get("status", "")).strip()
            tl_review = str(frontmatter.get("tl_review", "")).strip()
            plan_scope = str(frontmatter.get("plan_scope", "action")).strip() or "action"
            is_boundary = _is_approved_deferred_add_feature_boundary(frontmatter)
            reviewed.append(
                f"{review_plan_id} scope={plan_scope} "
                f"status={status or '<missing>'} tl_review={tl_review or '<missing>'}"
            )
            missing_fields: list[str] = []
            # process-scope PLAN は長命の親 (全 Action の L7 完了で収束、plan-model)。
            # incremental Action landing 中は未完了が正常なため status 完了は要求しない
            # (TL 判定A 2026-06-05)。tl_review=approve のみで守る。action-scope は両方必須。
            if plan_scope != "process" and not is_boundary and status not in {"completed", "finalized"}:
                missing_fields.append(f"status={status or '<missing>'}")
            if tl_review != "approve":
                missing_fields.append(f"tl_review={tl_review or '<missing>'}")
            if missing_fields:
                violations.append(f"{review_plan_id} {' '.join(missing_fields)}")
    except ValueError as exc:
        return _result(
            "G-review",
            False,
            str(exc),
            "PLAN 特定 (--plan-id / handover / ahead commit) と docs/plans frontmatter を確認",
        )

    if violations:
        return _result(
            "G-review",
            False,
            f"review prerequisites missing: {'; '.join(violations)}",
            "PLAN frontmatter の status∈{completed,finalized} と tl_review=approve を満たすこと。承認済み deferred add-feature 境界チケットのみ、厳格ガード充足時は status=draft を許容。",
        )

    detail = reviewed[0] if len(reviewed) == 1 else "; ".join(reviewed)
    return _result(
        "G-review",
        True,
        detail,
        "なし",
    )


def _has_vg_overview_assets(project_root: Path) -> bool:
    return (
        (project_root / "docs" / "v2" / "L7-test-design" / "g7-test-anchor-map.yaml").is_file()
        and (project_root / "cli" / "config" / "functional-registry.yaml").is_file()
    )


def run_gate_vg_overview(project_root: str | Path) -> dict:
    root = Path(project_root).resolve()
    if not _has_vg_overview_assets(root):
        return _result(
            "G-vg-overview",
            True,
            "not applicable: VG-overview assets not present",
            "なし",
        )

    previous_skip = os.environ.get("HELIX_DOCTOR_SKIP_EXEC_TESTS")
    os.environ["HELIX_DOCTOR_SKIP_EXEC_TESTS"] = previous_skip if previous_skip is not None else "1"
    try:
        report = collect_vg_overview(root)
    except Exception as exc:  # pragma: no cover - defensive boundary for push UX
        return _result(
            "G-vg-overview",
            False,
            f"VG-overview error: {exc}",
            "helix doctor check_vg_overview --json で詳細確認",
        )
    finally:
        if previous_skip is None:
            os.environ.pop("HELIX_DOCTOR_SKIP_EXEC_TESTS", None)
        else:
            os.environ["HELIX_DOCTOR_SKIP_EXEC_TESTS"] = previous_skip

    vg = report["vg_overview"]
    g7 = report["g7_subcheck"]
    if vg["overall_clean"]:
        return _result(
            "G-vg-overview",
            True,
            (
                "overall_clean=true "
                f"anchored={g7['anchored']}/{g7['ut_total']} "
                f"exec_pass={g7['exec_pass']} "
                f"missing={g7['missing']} "
                f"unanchored={g7['unanchored_but_exists']}"
            ),
            "なし",
        )

    failing_required = [
        f"{name}:{item['finding_count']}"
        for name, item in vg["required_clean"].items()
        if not item["clean"]
    ]
    failing_pairs = [
        f"{name}:{item['reason']}"
        for name, item in vg["pair_status"].items()
        if item["status"] == "applicable" and not item["clean"]
    ]
    return _result(
        "G-vg-overview",
        False,
        "; ".join(failing_required + failing_pairs) or "overall_clean=false",
        "G7 anchor/test pass と registry/trace findings を解消",
    )


def run_all_gates(
    execute: bool = False,
    remote: str = "origin",
    branch: str = "main",
    plan_id: str | None = None,
    allow_main: bool = False,
) -> dict:
    repo_root = _repo_root()
    gates = [
        run_gate_tests(),
        run_gate_catalog(),
        run_gate_secret(),
        run_gate_ff(remote, branch),
        run_gate_attr(remote, branch),
        run_gate_nondestructive(remote, branch),
        run_gate_review(plan_id, repo_root),
        run_gate_vg_overview(repo_root),
    ]
    failed = [gate for gate in gates if not gate["passed"]]
    result = {
        "ok": not failed,
        "failed_count": len(failed),
        "gates": gates,
        "execute_requested": execute,
        "remote": remote,
        "branch": branch,
        "plan_id": plan_id,
        "allow_main": allow_main,
        "push": {
            "attempted": False,
            "ok": False,
            "detail": "",
        },
    }

    if failed or not execute:
        return result

    if branch == MAIN_BRANCH and not allow_main:
        result["ok"] = False
        result["push"]["detail"] = "main branch requires --allow-main"
        return result

    push_proc = _run_command(["git", "push", remote, branch], cwd=repo_root)
    result["push"]["attempted"] = True
    result["push"]["ok"] = push_proc.returncode == 0
    result["push"]["detail"] = _format_failure(push_proc) if push_proc.returncode != 0 else f"git push {remote} {branch}"
    result["ok"] = push_proc.returncode == 0
    return result


def _print_report(payload: dict) -> None:
    print("[helix push] gate verification...")
    for gate in payload["gates"]:
        mark = "✓" if gate["passed"] else "✗"
        print(f"{mark} {gate['id']:<15} ({gate['detail']})")
        if not gate["passed"]:
            print(f"  Fix: {gate['fix']}")

    if not payload["ok"]:
        if payload["failed_count"]:
            suffix = "gate failed" if payload["failed_count"] == 1 else "gates failed"
            print(f"\n[helix push] BLOCKED ({payload['failed_count']} {suffix})")
        else:
            print(f"\n[helix push] git push failed: {payload['push']['detail']}")
        return

    if payload["execute_requested"]:
        print(
            f"\n[helix push] all gates PASS -> executing git push "
            f"{payload['remote']} {payload['branch']}"
        )
    else:
        print("\n[helix push] all gates PASS")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--plan-id", default=None)
    parser.add_argument("--allow-main", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--help", "-h", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args, extra = parser.parse_known_args(argv)
    if args.help:
        parser.print_help()
        return 0
    if extra:
        print(f"エラー: 不明なオプションです: {extra[0]}", file=sys.stderr)
        return 2

    payload = run_all_gates(
        execute=args.execute,
        remote=args.remote,
        branch=args.branch,
        plan_id=args.plan_id,
        allow_main=args.allow_main,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_report(payload)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
