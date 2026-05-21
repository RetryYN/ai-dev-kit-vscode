from __future__ import annotations

import time
from typing import Any

from sprint_lint import check_full_regression, check_py_compile, check_relevant_tests


def run_py_compile(target_paths: list[str]) -> dict[str, Any]:
    """Proxy sprint_lint.check_py_compile()."""
    return check_py_compile(target_paths)


def run_pytest(target_paths: list[str], timeout: int = 120) -> dict[str, Any]:
    """Run relevant pytest checks and normalize the summary."""
    del timeout
    if not target_paths:
        return {"passed": 0, "failed": 0, "errors": ["no target paths"], "duration_sec": 0.0}

    pattern = f"path:{' '.join(target_paths)}"
    started_at = time.perf_counter()
    raw = check_relevant_tests(pattern)
    duration_sec = raw.get("duration_sec")
    if not isinstance(duration_sec, (int, float)):
        duration_sec = round(time.perf_counter() - started_at, 6)

    return {
        "passed": raw.get("passed", 0),
        "failed": raw.get("failed", 0),
        "errors": raw.get("errors", []),
        "duration_sec": float(duration_sec),
    }


def run_full_suite() -> dict[str, Any]:
    """Proxy sprint_lint.check_full_regression()."""
    return check_full_regression()


def auto_check(sprint_id: str, target_paths: list[str]) -> dict[str, Any]:
    """Run sprint step 4 and 5 checks in order."""
    step4 = run_py_compile(target_paths)
    step5_test = run_pytest(target_paths)
    step5_full = run_full_suite()
    overall = (
        step4.get("status") == "pass"
        and step5_test.get("failed", 1) == 0
        and step5_full.get("status") in ("pass", "skip", "skipped")
    )
    return {
        "sprint_id": sprint_id,
        "step4_py_compile": step4,
        "step5_pytest": step5_test,
        "step5_full": step5_full,
        "overall_pass": overall,
    }
