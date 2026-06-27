#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

import plan_validator
import changed_files as changed_files_module
from vg_overview import collect_vg_overview


PYTEST_TESTS_CMD = ["python3", "-m", "pytest", "cli/lib/tests/", "-q"]
PYTEST_FULL_TESTS_CMD = [*PYTEST_TESTS_CMD, "-n", "auto"]
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
CONTRACT_GATE_ENUM_RE = re.compile(r"id:\s*\{[^}]*enum:\s*\[([^\]]+)\]")
GATE_IDS = (
    "G-tests",
    "G-catalog",
    "G-secret",
    "G-ff",
    "G-attr",
    "G-nondestructive",
    "G-review",
    "G-vg-overview",
)
MAIN_BRANCH = "main"
AUTO_TEST_TIER = "auto"
FULL_TEST_TIER = "full"
FULL_TRIGGER_GLOBS = (
    "pyproject.toml",
    "requirements*.txt",
    ".github/workflows/*",
    "cli/lib/tests/conftest.py",
    "cli/helix-test",
    "cli/tests/_helix-bats-helper.bash",
    "cli/tests/test-bats-lite-runner.bats",
    "cli/lib/push_gate.py",
    "cli/lib/changed_files.py",
    "cli/lib/vg_overview.py",
    "cli/lib/helix_db.py",
    "cli/lib/plan_validator.py",
    "docs/v2/L3-detailed-design/D-CONTRACT/*",
    "HELIX-workflows/helix-process/github-operations.md",
    "docs/commands/push.md",
    "cli/config/functional-registry.yaml",
    "HELIX-workflows/helix-process/automation-gate-map.md",
    "cli/lib/tests/test_helix_l0_l14_flow_contract.py",
    "cli/tests/test-helix-l0-l14-flow-contract.bats",
)
COMPLETED_REVIEW_STATUSES = {"completed", "finalized"}
HANDOVER_PLAN_ID_ABSENT = "absent"
HANDOVER_PLAN_ID_SINGLE = "single"
HANDOVER_PLAN_ID_AMBIGUOUS = "ambiguous"


def _is_nonempty_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(
        isinstance(item, str) and item.strip() for item in value
    )


def _normalized_string_list(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            return None
        stripped = item.strip()
        if not stripped:
            return None
        normalized.append(stripped)
    return normalized


def _selector_payload_is_valid(selector_payload: Any) -> bool:
    if not isinstance(selector_payload, dict):
        return False
    if not isinstance(selector_payload.get("has_code_changes"), bool):
        return False
    for key in ("pytest_targets", "bats_targets", "unmapped_code_files"):
        if not isinstance(selector_payload.get(key), list):
            return False
        if not _normalized_string_list(selector_payload.get(key, [])) and selector_payload.get(key):
            return False
    return True


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

    同様に HELIX_DB_CUTOVER / HELIX_DB_DISCOVERY (db_cli preflight 既定 CUTOVER="1")
    が pytest/bats に漏れると compatibility_adapter の split-DB routing が有効化し、
    explicit legacy seed と routed SUT の DB 分裂で cross-DB FK 不一致を起こすため除去する。
    HELIX_DB_PATH (test isolation の DB path) は温存する。
    """
    scrub_keys = {"HELIX_ASKUSERQUESTION_NOW", "HELIX_DB_CUTOVER", "HELIX_DB_DISCOVERY"}
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("HELIX_AUTOMATION_") and key not in scrub_keys
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


def _resolve_handover_plan_id_state(project_root: Path) -> tuple[str, str | None]:
    handover_path = project_root / ".helix" / "handover" / "CURRENT.json"
    if not handover_path.is_file():
        return HANDOVER_PLAN_ID_ABSENT, None
    try:
        payload = json.loads(handover_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return HANDOVER_PLAN_ID_AMBIGUOUS, None
    candidates = _collect_plan_ids(payload)
    unique = sorted({candidate for candidate in candidates if candidate})
    if not unique:
        return HANDOVER_PLAN_ID_ABSENT, None
    if len(unique) == 1:
        return HANDOVER_PLAN_ID_SINGLE, unique[0]
    return HANDOVER_PLAN_ID_AMBIGUOUS, None


def _load_handover_plan_id(project_root: Path) -> str | None:
    state, plan_id = _resolve_handover_plan_id_state(project_root)
    if state == HANDOVER_PLAN_ID_SINGLE:
        return plan_id
    return None


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


def _git_ref_exists(project_root: Path, ref: str) -> bool:
    proc = _run_command(["git", "rev-parse", "--verify", "--quiet", ref], cwd=project_root)
    return proc.returncode == 0


def _remote_default_branch_refs(project_root: Path, remote: str) -> list[str]:
    candidates: list[str] = []
    head_proc = _run_command(
        ["git", "symbolic-ref", "--quiet", f"refs/remotes/{remote}/HEAD"],
        cwd=project_root,
    )
    if head_proc.returncode == 0:
        head_ref = (head_proc.stdout or "").strip()
        if head_ref.startswith("refs/remotes/"):
            candidates.append(head_ref.removeprefix("refs/remotes/"))
    candidates.extend([f"{remote}/main", f"{remote}/master"])

    unique: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            unique.append(candidate)
    return unique


def _collect_vg_overview_changed_files_context(
    project_root: Path,
    *,
    remote: str,
    branch: str,
) -> dict[str, Any]:
    upstream_ref = f"{remote}/{branch}" if remote and branch else ""
    diff_range: str | None = None
    source = "upstream"
    base_ref: str | None = upstream_ref or None
    reason_parts: list[str] = []

    if upstream_ref and _git_ref_exists(project_root, upstream_ref):
        diff_range = f"{upstream_ref}..HEAD"
    else:
        if upstream_ref:
            reason_parts.append(f"upstream {upstream_ref} missing")
        else:
            reason_parts.append("upstream unresolved")

        source = "merge-base"
        base_ref = None
        merge_base_ref: str | None = None
        for candidate in _remote_default_branch_refs(project_root, remote):
            if not _git_ref_exists(project_root, candidate):
                continue
            merge_base_proc = _run_command(["git", "merge-base", "HEAD", candidate], cwd=project_root)
            merge_base = (merge_base_proc.stdout or "").strip()
            if merge_base_proc.returncode != 0 or not merge_base:
                continue
            merge_base_ref = candidate
            base_ref = candidate
            diff_range = f"{merge_base}..HEAD"
            break

        if diff_range is None:
            default_refs = _remote_default_branch_refs(project_root, remote)
            if default_refs:
                reason_parts.append(
                    f"merge-base with {default_refs[0]} unavailable"
                )
            else:
                reason_parts.append(f"default branch for {remote} unresolved")
            return {
                "status": "unavailable",
                "source": "unresolved",
                "base_ref": None,
                "files": [],
                "env_value": None,
                "reason": "changed-files unavailable: " + "; ".join(reason_parts),
            }

    diff_proc = _run_command(["git", "diff", "--name-only", diff_range], cwd=project_root)
    if diff_proc.returncode != 0:
        detail = _format_failure(diff_proc)
        return {
            "status": "unavailable",
            "source": source,
            "base_ref": base_ref,
            "files": [],
            "env_value": None,
            "reason": f"changed-files unavailable: git diff failed for {diff_range} ({detail})",
        }

    untracked_proc = _run_command(["git", "ls-files", "--others", "--exclude-standard"], cwd=project_root)
    if untracked_proc.returncode != 0:
        detail = _format_failure(untracked_proc)
        return {
            "status": "unavailable",
            "source": source,
            "base_ref": base_ref,
            "files": [],
            "env_value": None,
            "reason": f"changed-files unavailable: git ls-files failed ({detail})",
        }

    files: list[str] = []
    seen: set[str] = set()
    for raw_path in [
        *(line.strip() for line in diff_proc.stdout.splitlines()),
        *(line.strip() for line in untracked_proc.stdout.splitlines()),
    ]:
        if not raw_path or raw_path in seen:
            continue
        seen.add(raw_path)
        files.append(raw_path)

    return {
        "status": "available",
        "source": source,
        "base_ref": base_ref,
        "files": files,
        "env_value": "\n".join(files),
        "reason": None,
    }


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
    handover_state, handover = _resolve_handover_plan_id_state(project_root)
    ahead = _ahead_commit_plan_ids(project_root)

    if handover_state == HANDOVER_PLAN_ID_AMBIGUOUS:
        raise ValueError("handover plan_id is ambiguous")

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


def _review_fallback_allowed(plan_id: str | None, project_root: Path) -> bool:
    explicit = plan_id.strip() if isinstance(plan_id, str) and plan_id.strip() else None
    if explicit:
        return False
    handover_state, _handover_plan_id = _resolve_handover_plan_id_state(project_root)
    if handover_state != HANDOVER_PLAN_ID_ABSENT:
        return False
    return len(_ahead_commit_plan_ids(project_root)) == 0


def _load_handover_review_record(project_root: Path) -> dict[str, str] | None:
    handover_path = project_root / ".helix" / "handover" / "CURRENT.json"
    if not handover_path.is_file():
        return None
    try:
        payload = json.loads(handover_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    task = payload.get("task") if isinstance(payload.get("task"), dict) else {}
    review = payload.get("review") if isinstance(payload.get("review"), dict) else {}
    task_id = str(task.get("id", "")).strip()
    if not task_id:
        return None

    return {
        "kind": "handover_task",
        "id": task_id,
        "status": str(task.get("status", "")).strip(),
        "tl_review": str(review.get("tl_review", "")).strip(),
        "review_status": str(review.get("review_status", "")).strip(),
        "reviewed_at": str(review.get("reviewed_at", "")).strip(),
        "reviewed_by": str(review.get("reviewed_by", "")).strip(),
    }


def _is_valid_iso8601_datetime(value: str) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip()
    if not normalized:
        return False
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return True


def _handover_review_missing_fields(record: dict[str, Any]) -> list[str]:
    missing_fields: list[str] = []
    status = str(record.get("status", "")).strip()
    review_status = str(record.get("review_status", "")).strip()
    tl_review = str(record.get("tl_review", "")).strip()
    reviewed_at = str(record.get("reviewed_at", "")).strip()
    reviewed_by = str(record.get("reviewed_by", "")).strip()

    if status not in COMPLETED_REVIEW_STATUSES:
        missing_fields.append(f"status={status or '<missing>'}")
    if review_status not in COMPLETED_REVIEW_STATUSES:
        missing_fields.append(f"review_status={review_status or '<missing>'}")
    if tl_review != "approve":
        missing_fields.append(f"tl_review={tl_review or '<missing>'}")
    if not _is_valid_iso8601_datetime(reviewed_at):
        missing_fields.append(f"reviewed_at={reviewed_at or '<missing>'}")
    if not reviewed_by:
        missing_fields.append("reviewed_by=<missing>")
    return missing_fields


def is_handover_review_approved(state: dict[str, Any]) -> bool:
    return not _handover_review_missing_fields(state)


def _contract_gate_ids(contract_path: Path) -> list[str]:
    text = contract_path.read_text(encoding="utf-8")
    match = CONTRACT_GATE_ENUM_RE.search(text)
    if not match:
        raise ValueError(f"gate enum not found: {contract_path}")
    return [item.strip() for item in match.group(1).split(",") if item.strip()]


def _matches_full_trigger(path: str) -> bool:
    pure_path = PurePosixPath(path)
    path_text = pure_path.as_posix()
    return any(path_text == pattern or pure_path.match(pattern) for pattern in FULL_TRIGGER_GLOBS)


def _is_test_path(path: str) -> bool:
    pure_path = PurePosixPath(path)
    path_text = pure_path.as_posix()
    return (
        path_text.startswith("cli/lib/tests/")
        or path_text.startswith("cli/tests/")
        or path_text == "cli/helix-test"
    )


def _has_deleted_or_renamed_tests(project_root: Path, upstream: str | None) -> bool:
    if not upstream:
        return False
    proc = _run_command(["git", "diff", "--name-status", f"{upstream}..HEAD"], cwd=project_root)
    if proc.returncode != 0:
        return False
    for line in proc.stdout.splitlines():
        parts = [item for item in line.split("\t") if item]
        if not parts:
            continue
        status = parts[0]
        if not status.startswith(("D", "R")):
            continue
        for path in parts[1:]:
            if _is_test_path(path):
                return True
    return False


def decide_test_tier(
    changed_payload: dict[str, Any],
    branch: str,
    flags: dict[str, Any],
    *,
    selector: dict[str, Any] | None = None,
    has_deleted_or_renamed_tests: bool = False,
) -> str:
    requested_tier = str(flags.get("test_tier", AUTO_TEST_TIER)).strip().lower() or AUTO_TEST_TIER
    if flags.get("full") or requested_tier == FULL_TEST_TIER:
        return FULL_TEST_TIER
    if flags.get("allow_main"):
        return FULL_TEST_TIER
    if branch == MAIN_BRANCH or branch.startswith("release/"):
        return FULL_TEST_TIER
    if not isinstance(changed_payload, dict):
        return FULL_TEST_TIER
    source_status_raw = changed_payload.get("source_status")
    if not isinstance(source_status_raw, str):
        return FULL_TEST_TIER
    source_status = source_status_raw.strip()
    if source_status not in changed_files_module.KNOWN_SOURCE_STATUSES:
        return FULL_TEST_TIER
    if source_status == "unavailable":
        return FULL_TEST_TIER
    files = _normalized_string_list(changed_payload.get("files"))
    if files is None:
        return FULL_TEST_TIER
    if source_status == "available_nonempty" and not files:
        return FULL_TEST_TIER
    if source_status == "available_empty" and files:
        return FULL_TEST_TIER

    if has_deleted_or_renamed_tests or any(_matches_full_trigger(path) for path in files):
        return FULL_TEST_TIER

    selector_payload = selector if selector is not None else changed_files_module.select_test_targets(files)
    if not _selector_payload_is_valid(selector_payload):
        return FULL_TEST_TIER
    if selector_payload.get("unmapped_code_files"):
        return FULL_TEST_TIER
    has_selected_tests = bool(selector_payload.get("pytest_targets") or selector_payload.get("bats_targets"))
    if selector_payload.get("has_code_changes") and not has_selected_tests:
        return FULL_TEST_TIER
    return AUTO_TEST_TIER


def _run_test_commands(
    repo_root: Path,
    test_env: dict[str, str],
    *,
    tier: str,
    pytest_command: list[str] | None,
    bats_command: list[str] | None,
) -> dict:
    pytest_count = "0"
    bats_count = "0"

    if pytest_command:
        pytest_proc = _run_command(pytest_command, cwd=repo_root, env=test_env)
        if pytest_proc.returncode != 0:
            return _result(
                "G-tests",
                False,
                f"pytest FAIL: {_format_failure(pytest_proc)}",
                "テスト fail を修正してから再実行",
            )
        pytest_count = _parse_pytest_count(pytest_proc.stdout, pytest_proc.stderr) or "pytest PASS"

    if bats_command:
        bats_proc = _run_command(bats_command, cwd=repo_root, env=test_env)
        if bats_proc.returncode != 0:
            return _result(
                "G-tests",
                False,
                f"bats FAIL: {_format_failure(bats_proc)}",
                "テスト fail を修正してから再実行",
            )
        bats_count = _parse_bats_count(bats_proc.stdout, bats_proc.stderr) or "bats PASS"

    return _result("G-tests", True, f"tier={tier}, pytest {pytest_count} + bats {bats_count}", "なし")


def run_gate_tests(
    *,
    remote: str = "origin",
    branch: str = "main",
    test_tier: str = AUTO_TEST_TIER,
    allow_main: bool = False,
) -> dict:
    repo_root = _repo_root()
    test_env = _hermetic_test_env()
    upstream = f"{remote}/{branch}" if remote and branch else None
    changed_payload = changed_files_module.changed_files(upstream=upstream)
    selector = changed_files_module.select_test_targets(
        [str(item) for item in changed_payload.get("files", []) if isinstance(item, str)],
        repo_root=repo_root,
    )
    tier = decide_test_tier(
        changed_payload,
        branch,
        {
            "full": test_tier == FULL_TEST_TIER,
            "test_tier": test_tier,
            "allow_main": allow_main,
        },
        selector=selector,
        has_deleted_or_renamed_tests=_has_deleted_or_renamed_tests(repo_root, upstream),
    )

    if tier == FULL_TEST_TIER:
        bats_files = sorted(
            str(path.relative_to(repo_root))
            for path in (repo_root / "cli" / "tests").glob("*.bats")
        )
        if not bats_files:
            return _result(
                "G-tests",
                False,
                "bats FAIL: no .bats files found under cli/tests",
                "テスト fail を修正してから再実行",
            )
        return _run_test_commands(
            repo_root,
            test_env,
            tier=tier,
            pytest_command=PYTEST_FULL_TESTS_CMD,
            bats_command=["bats", *bats_files],
        )

    return _run_test_commands(
        repo_root,
        test_env,
        tier=tier,
        pytest_command=["python3", "-m", "pytest", *selector["pytest_targets"], "-q"]
        if selector["pytest_targets"]
        else None,
        bats_command=["bats", *selector["bats_targets"]] if selector["bats_targets"] else None,
    )


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


def _review_record_missing_fields(record: dict[str, Any]) -> list[str]:
    missing_fields: list[str] = []
    status = str(record.get("status", "")).strip()
    tl_review = str(record.get("tl_review", "")).strip()
    record_kind = str(record.get("kind", "")).strip()

    requires_completed_status = True
    if record_kind == "plan":
        requires_completed_status = (
            str(record.get("plan_scope", "action")).strip() != "process"
            and not bool(record.get("is_boundary"))
        )

    if requires_completed_status and status not in COMPLETED_REVIEW_STATUSES:
        missing_fields.append(f"status={status or '<missing>'}")
    if tl_review != "approve":
        missing_fields.append(f"tl_review={tl_review or '<missing>'}")
    return missing_fields


def run_gate_review(plan_id: str | None, project_root: str | Path) -> dict:
    root = Path(project_root).resolve()
    try:
        review_plan_ids = _all_review_plan_ids(plan_id, root)
    except ValueError as exc:
        if _review_fallback_allowed(plan_id, root):
            record = _load_handover_review_record(root)
            if record is None:
                return _result(
                    "G-review",
                    False,
                    str(exc),
                    "PLAN 特定 (--plan-id / handover / ahead commit) と docs/plans frontmatter を確認",
                )

            detail = (
                f"{record['id']} kind=handover_task "
                f"status={record['status'] or '<missing>'} "
                f"tl_review={record['tl_review'] or '<missing>'} "
                f"review_status={record['review_status'] or '<missing>'}"
            )
            if not is_handover_review_approved(record):
                missing_fields = _handover_review_missing_fields(record)
                return _result(
                    "G-review",
                    False,
                    f"review prerequisites missing: {record['id']} {' '.join(missing_fields)}",
                    "handover review block の tl_review=approve と task.status∈{completed,finalized} を満たすこと。ready_for_review は未レビュー扱い。",
                )
            return _result("G-review", True, detail, "なし")

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
            record = {
                "kind": "plan",
                "id": review_plan_id,
                "status": status,
                "tl_review": tl_review,
                "review_status": status,
                "plan_scope": plan_scope,
                "is_boundary": is_boundary,
            }
            reviewed.append(
                f"{review_plan_id} scope={plan_scope} "
                f"status={status or '<missing>'} tl_review={tl_review or '<missing>'}"
            )
            missing_fields = _review_record_missing_fields(record)
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


def _format_vg_required_detail(
    name: str,
    item: dict[str, Any],
    *,
    changed_files_reason: str | None = None,
) -> str:
    suffix_parts: list[str] = []
    source_status = str(item.get("source_status", "")).strip()
    skipped_reason = str(item.get("skipped_reason", "")).strip()
    if source_status:
        suffix_parts.append(f"source_status={source_status}")
    if skipped_reason:
        suffix_parts.append(f"reason={skipped_reason}")
    if source_status == "unavailable" and changed_files_reason:
        suffix_parts.append(changed_files_reason)
    suffix = f" ({'; '.join(suffix_parts)})" if suffix_parts else ""
    return f"{name}:{item.get('finding_count', 0)}{suffix}"


def _collect_vg_skipped_required_details(
    required_clean: dict[str, Any],
    *,
    changed_files_reason: str | None = None,
) -> list[str]:
    details: list[str] = []
    for name, item in required_clean.items():
        if str(item.get("source_status", "")).strip() != "unavailable":
            continue
        details.append(
            _format_vg_required_detail(
                name,
                item,
                changed_files_reason=changed_files_reason,
            )
        )
    return details


def run_gate_vg_overview(
    project_root: str | Path,
    *,
    remote: str = "origin",
    branch: str = "main",
) -> dict:
    root = Path(project_root).resolve()
    if not _has_vg_overview_assets(root):
        return _result(
            "G-vg-overview",
            True,
            "not applicable: VG-overview assets not present",
            "なし",
        )

    previous_skip = os.environ.get("HELIX_DOCTOR_SKIP_EXEC_TESTS")
    previous_changed_files = os.environ.get("HELIX_CHANGED_FILES")
    changed_files_context = _collect_vg_overview_changed_files_context(root, remote=remote, branch=branch)
    os.environ["HELIX_DOCTOR_SKIP_EXEC_TESTS"] = previous_skip if previous_skip is not None else "1"
    if changed_files_context["status"] == "available":
        os.environ["HELIX_CHANGED_FILES"] = str(changed_files_context["env_value"])
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
        if previous_changed_files is None:
            os.environ.pop("HELIX_CHANGED_FILES", None)
        else:
            os.environ["HELIX_CHANGED_FILES"] = previous_changed_files

    vg = report["vg_overview"]
    g7 = report["g7_subcheck"]
    skipped_required = _collect_vg_skipped_required_details(
        vg.get("required_clean", {}),
        changed_files_reason=changed_files_context.get("reason"),
    )
    if vg["overall_clean"]:
        detail = (
            "overall_clean=true "
            f"anchored={g7['anchored']}/{g7['ut_total']} "
            f"exec_pass={g7['exec_pass']} "
            f"missing={g7['missing']} "
            f"unanchored={g7['unanchored_but_exists']}"
        )
        if skipped_required:
            detail += " skipped_required_clean=" + "; ".join(skipped_required)
        return _result(
            "G-vg-overview",
            True,
            detail,
            "なし",
        )

    failing_required = [
        _format_vg_required_detail(
            name,
            item,
            changed_files_reason=changed_files_context.get("reason"),
        )
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
    test_tier: str = AUTO_TEST_TIER,
) -> dict:
    repo_root = _repo_root()
    gates = [
        run_gate_tests(
            remote=remote,
            branch=branch,
            test_tier=test_tier,
            allow_main=allow_main,
        ),
        run_gate_catalog(),
        run_gate_secret(),
        run_gate_ff(remote, branch),
        run_gate_attr(remote, branch),
        run_gate_nondestructive(remote, branch),
        run_gate_review(plan_id, repo_root),
        run_gate_vg_overview(repo_root, remote=remote, branch=branch),
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
        "test_tier": test_tier,
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
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--test-tier", choices=(AUTO_TEST_TIER, FULL_TEST_TIER), default=AUTO_TEST_TIER)
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
        test_tier=FULL_TEST_TIER if args.full else args.test_tier,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_report(payload)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
