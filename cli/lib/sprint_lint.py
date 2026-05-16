#!/usr/bin/env python3
"""Sprint completion audit helpers (PLAN-082 Phase 3).

対象設計 (① D-API): docs/plans/PLAN-082-subagent-sprint-mechanization.md
対象実装 (② D-IMPL): cli/lib/sprint_lint.py
テスト設計 (③): cli/lib/tests/test_sprint_lint.py docstring 内 inline case
テストコード (④ D-TEST-CODE-UNIT): cli/lib/tests/test_sprint_lint.py
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


REVIEW_WINDOW_SECONDS = 24 * 60 * 60
PYTEST_SUMMARY_PATTERN = re.compile(r"(\d+)\s+(passed|failed|skipped|xfailed|xpassed|error|errors)\b")
DEFAULT_FULL_REGRESSION_TIMEOUT = 600
_PYTEST_COMMAND: list[str] | None = None


def _resolve_project_root() -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()

    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".helix").exists() or (candidate / ".git").exists():
            return candidate

    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _resolve_project_root()
HELIX_DIR = PROJECT_ROOT / ".helix"
REVIEW_DIR = HELIX_DIR / "reviews" / "plans"
AUDIT_RUN_DIR = HELIX_DIR / "audit" / "codex-runs"
DB_PATH = HELIX_DIR / "helix.db"


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _split_path_list(value: str) -> list[str]:
    if not value.strip():
        return []
    normalized = value.replace(",", "\n")
    if os.pathsep != "\n":
        normalized = normalized.replace(os.pathsep, "\n")
    return [item.strip() for item in normalized.splitlines() if item.strip()]


def _collect_changed_files() -> list[Path]:
    override = os.environ.get("HELIX_SPRINT_TARGET_FILES")
    if override:
        return [Path(item).resolve() for item in _split_path_list(override)]

    try:
        proc = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "status", "--porcelain", "--untracked-files=all"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    changed: list[Path] = []
    for raw_line in proc.stdout.splitlines():
        if not raw_line.strip():
            continue
        rel_path = raw_line[3:]
        if " -> " in rel_path:
            rel_path = rel_path.split(" -> ", 1)[1]
        changed.append((PROJECT_ROOT / rel_path).resolve())
    return changed


def _unique_existing_python_files(paths: list[Path | str]) -> list[str]:
    seen: set[str] = set()
    python_files: list[str] = []
    for item in paths:
        path = Path(item).resolve()
        if path.suffix != ".py" or not path.exists():
            continue
        value = path.as_posix()
        if value in seen:
            continue
        seen.add(value)
        python_files.append(value)
    return python_files


def _run_command(command: list[str], *, timeout: int, cwd: Path | None = None) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            cwd=str(cwd or PROJECT_ROOT),
            timeout=timeout,
        )
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timed_out": False,
        }
    except FileNotFoundError as exc:
        return {
            "returncode": 127,
            "stdout": "",
            "stderr": str(exc),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "returncode": 124,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or f"timeout after {timeout} seconds",
            "timed_out": True,
        }


def _resolve_pytest_command() -> list[str]:
    global _PYTEST_COMMAND
    override = os.environ.get("HELIX_SPRINT_PYTEST_CMD")
    if override:
        return [item for item in override.split() if item]
    if _PYTEST_COMMAND is not None:
        return list(_PYTEST_COMMAND)

    candidates = (
        ["python3", "-m", "pytest"],
        ["pytest"],
    )
    for candidate in candidates:
        probe = _run_command([*candidate, "--version"], timeout=30)
        if probe["returncode"] == 0:
            _PYTEST_COMMAND = list(candidate)
            return list(candidate)

    _PYTEST_COMMAND = ["python3", "-m", "pytest"]
    return list(_PYTEST_COMMAND)


def _trim_errors(*chunks: str) -> list[str]:
    lines: list[str] = []
    for chunk in chunks:
        for line in chunk.splitlines():
            text = line.strip()
            if text:
                lines.append(text)
    return lines[-20:]


def _parse_pytest_counts(output: str) -> dict[str, int]:
    counts = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "xfailed": 0,
        "xpassed": 0,
        "errors": 0,
    }
    for raw_count, label in PYTEST_SUMMARY_PATTERN.findall(output):
        key = "errors" if label in {"error", "errors"} else label
        counts[key] += int(raw_count)
    return counts


def _count_bats_ok(output: str) -> int:
    return len(re.findall(r"(?m)^ok\b", output))


def _build_relevant_test_selector(changed_files: list[Path], plan_id: str) -> str:
    override = os.environ.get("HELIX_SPRINT_TEST_PATTERN")
    if override:
        return override

    pytest_targets = [
        path.resolve().as_posix()
        for path in changed_files
        if path.suffix == ".py" and path.name.startswith("test_") and path.exists()
    ]
    if pytest_targets:
        return "path:" + " ".join(pytest_targets)

    tokens: list[str] = []
    seen: set[str] = set()
    ignored = {"test", "tests", "cli", "lib", "py", "sh", "md", "json", "yaml", "yml"}
    for path in changed_files:
        for token in re.split(r"[^a-zA-Z0-9]+", path.stem.lower()):
            if len(token) < 3 or token in ignored or token in seen:
                continue
            seen.add(token)
            tokens.append(token)
    if tokens:
        return " or ".join(tokens[:4])
    return plan_id.lower().replace("-", "_") or "sprint"


def _extract_reviewers(text: str) -> list[str]:
    reviewers: list[str] = []
    for candidate in ("pmo-sonnet", "tl-advisor", "codex", "review"):
        if candidate in text and candidate not in reviewers:
            reviewers.append(candidate)
    return reviewers


# @helix:index id=sprint-lint.check-py-compile domain=cli/lib summary=変更済み Python ファイルへ py_compile を実行する
def check_py_compile(target_files: list[str]) -> dict[str, Any]:
    """python3 -m py_compile を target_files に対して実行する。"""
    python_files = _unique_existing_python_files(target_files)
    if not python_files:
        return {"status": "pass", "files_checked": 0, "errors": []}

    result = _run_command(["python3", "-m", "py_compile", *python_files], timeout=120)
    return {
        "status": "pass" if result["returncode"] == 0 else "fail",
        "files_checked": len(python_files),
        "errors": [] if result["returncode"] == 0 else _trim_errors(result["stderr"], result["stdout"]),
    }


# @helix:index id=sprint-lint.check-relevant-tests domain=cli/lib summary=該当 pytest を path 指定または -k 式で実行する
def check_relevant_tests(pattern: str) -> dict[str, Any]:
    """pytest の該当テストを実行する。"""
    pytest_command = _resolve_pytest_command()
    if pattern.startswith("path:"):
        targets = [item for item in pattern[len("path:") :].split() if item]
        command = [*pytest_command, *targets, "-q", "--tb=short"]
    else:
        command = [*pytest_command, "-k", pattern, "-q", "--tb=short"]

    result = _run_command(command, timeout=300)
    combined_output = "\n".join(part for part in (result["stdout"], result["stderr"]) if part)
    counts = _parse_pytest_counts(combined_output)
    tests_run = sum(counts.values())
    status = "pass" if result["returncode"] == 0 and tests_run > 0 else "fail"
    return {
        "status": status,
        "tests_run": tests_run,
        "passed": counts["passed"],
        "failed": counts["failed"] + counts["errors"],
        "selection": pattern,
        "errors": [] if status == "pass" else _trim_errors(result["stdout"], result["stderr"]),
    }


# @helix:index id=sprint-lint.check-full-regression domain=cli/lib summary=pytest 全量と bats 全量を順に実行する
def check_full_regression(skip: bool = False) -> dict[str, Any]:
    """pytest 全 + bats 全を実行する。"""
    if skip:
        return {"status": "skipped", "pytest_passed": 0, "bats_passed": 0, "errors": []}

    pytest_command = _resolve_pytest_command()
    pytest_result = _run_command(
        [*pytest_command, "-q", "--tb=short"],
        timeout=DEFAULT_FULL_REGRESSION_TIMEOUT,
    )
    bats_result = _run_command(["bats", "tests"], timeout=DEFAULT_FULL_REGRESSION_TIMEOUT)

    pytest_counts = _parse_pytest_counts("\n".join((pytest_result["stdout"], pytest_result["stderr"])))
    bats_output = "\n".join(part for part in (bats_result["stdout"], bats_result["stderr"]) if part)
    errors: list[str] = []
    if pytest_result["returncode"] != 0:
        errors.extend(_trim_errors(pytest_result["stdout"], pytest_result["stderr"]))
    if bats_result["returncode"] != 0:
        errors.extend(_trim_errors(bats_result["stdout"], bats_result["stderr"]))

    status = "pass" if pytest_result["returncode"] == 0 and bats_result["returncode"] == 0 else "fail"
    return {
        "status": status,
        "pytest_passed": pytest_counts["passed"],
        "bats_passed": _count_bats_ok(bats_output),
        "errors": errors[-20:],
    }


# @helix:index id=sprint-lint.check-review domain=cli/lib summary=24h 以内の review 実施証跡を plan 単位または全体で監査する
def check_review(plan_id: str | None = None) -> dict[str, Any]:
    """過去 24h の review 実施証跡を監査する。"""
    now = time.time()
    reviewers: list[str] = []
    evidence: list[str] = []
    normalized_plan = (plan_id or "").strip().upper()

    if normalized_plan:
        review_file = REVIEW_DIR / f"{normalized_plan}.json"
        if review_file.exists() and now - review_file.stat().st_mtime <= REVIEW_WINDOW_SECONDS:
            evidence.append(_display_path(review_file))
            reviewers.extend(_extract_reviewers(review_file.read_text(encoding="utf-8", errors="replace")))
            if not reviewers:
                reviewers.append("plan-review")

    if AUDIT_RUN_DIR.exists():
        for candidate in sorted(AUDIT_RUN_DIR.glob("*review*")):
            if not candidate.is_file():
                continue
            if now - candidate.stat().st_mtime > REVIEW_WINDOW_SECONDS:
                continue
            if normalized_plan and normalized_plan not in candidate.name.upper():
                continue
            evidence.append(_display_path(candidate))
            if "codex" not in reviewers:
                reviewers.append("codex")
            if len(evidence) >= 5:
                break

    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT event_type, result, created_at
                FROM hook_events
                WHERE event_type = 'codex_review'
                  AND created_at >= datetime('now', '-1 day')
                ORDER BY id DESC
                LIMIT 5
                """
            ).fetchall()
            if rows:
                evidence.append("db:hook_events/codex_review")
                if "codex_review" not in reviewers:
                    reviewers.append("codex_review")

            audit_rows = conn.execute(
                """
                SELECT check_name, plan_id, triggered_at
                FROM harness_check_events
                WHERE triggered_at >= datetime('now', '-1 day')
                  AND check_name LIKE '%review%'
                ORDER BY id DESC
                LIMIT 5
                """
            ).fetchall()
            for row in audit_rows:
                row_plan = (row["plan_id"] or "").strip().upper()
                if normalized_plan and row_plan and row_plan != normalized_plan:
                    continue
                evidence.append(f"db:harness_check_events/{row['check_name']}")
                if "harness-audit" not in reviewers:
                    reviewers.append("harness-audit")
                break
        finally:
            conn.close()

    return {
        "status": "pass" if reviewers else "missing",
        "reviewers": reviewers,
        "evidence": evidence[:5],
    }


def _overall_status(checks: dict[str, dict[str, Any]]) -> str:
    if any(checks[name]["status"] == "fail" for name in ("py_compile", "relevant_tests", "full_regression")):
        return "fail"
    if checks["review"]["status"] == "missing" or checks["full_regression"]["status"] == "skipped":
        return "warn"
    return "pass"


# @helix:index id=sprint-lint.audit-sprint-completion domain=cli/lib summary=Sprint Exit mandatory 4 種チェックを統合監査する
def audit_sprint_completion(plan_id: str, sprint: str, *, skip_full_regression: bool = False) -> dict[str, Any]:
    """Sprint Exit mandatory 4 種チェックを統合監査する。"""
    changed_files = _collect_changed_files()
    target_files = _unique_existing_python_files(changed_files)
    test_selector = _build_relevant_test_selector(changed_files, plan_id)
    checks = {
        "py_compile": check_py_compile(target_files),
        "relevant_tests": check_relevant_tests(test_selector),
        "full_regression": check_full_regression(skip=skip_full_regression),
        "review": check_review(plan_id),
    }
    return {
        "plan_id": plan_id,
        "sprint": sprint,
        "checks": checks,
        "overall": _overall_status(checks),
        "target_files": [_display_path(Path(path)) for path in target_files],
        "relevant_test_selector": test_selector,
    }


def _format_text(payload: dict[str, Any]) -> str:
    checks = payload["checks"]
    lines = [
        "=== Sprint Completion Audit (PLAN-082) ===",
        f"plan_id: {payload['plan_id']}",
        f"sprint: {payload['sprint']}",
        f"overall: {payload['overall']}",
        f"py_compile: {checks['py_compile']['status']} ({checks['py_compile']['files_checked']} files)",
        (
            "relevant_tests: "
            f"{checks['relevant_tests']['status']} ({checks['relevant_tests']['tests_run']} tests, "
            f"selector={payload['relevant_test_selector']})"
        ),
        (
            "full_regression: "
            f"{checks['full_regression']['status']} "
            f"(pytest={checks['full_regression']['pytest_passed']}, bats={checks['full_regression']['bats_passed']})"
        ),
        f"review: {checks['review']['status']} ({', '.join(checks['review']['reviewers']) or 'none'})",
    ]
    return "\n".join(lines)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sprint completion audit (PLAN-082)")
    parser.add_argument("--plan-id", default=os.environ.get("HELIX_PLAN_ID", "PLAN-UNKNOWN"))
    parser.add_argument("--sprint", default=os.environ.get("HELIX_SPRINT_STEP", "unknown"))
    parser.add_argument("--skip-full-regression", action="store_true")
    parser.add_argument("--strict", action="store_true", help="overall=fail の場合 exit 1")
    parser.add_argument("--json", action="store_true")
    return parser


# @helix:index id=sprint-lint.main domain=cli/lib summary=sprint complete --auto-check 用 CLI entrypoint
def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    payload = audit_sprint_completion(
        args.plan_id,
        args.sprint,
        skip_full_regression=args.skip_full_regression,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_format_text(payload))

    if args.strict and payload["overall"] == "fail":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
