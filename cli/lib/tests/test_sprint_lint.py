"""Sprint completion audit 単体テスト (PLAN-082 Phase 3)

対象設計 (① D-API): docs/plans/PLAN-082-subagent-sprint-mechanization.md
対象実装 (② D-IMPL): cli/lib/sprint_lint.py
テスト設計 (③): 本ファイル docstring 内 inline case
テストコード (④ D-TEST-CODE-UNIT): cli/lib/tests/test_sprint_lint.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import sprint_lint


def test_check_py_compile_passes_for_valid_python_file(tmp_path: Path) -> None:
    """DoD 検証: inline U-001 valid Python file は py_compile pass を返す"""
    target = tmp_path / "ok.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")

    result = sprint_lint.check_py_compile([target.as_posix()])

    assert result["status"] == "pass"
    assert result["files_checked"] == 1
    assert result["errors"] == []


def test_check_py_compile_fails_for_syntax_error(tmp_path: Path) -> None:
    """DoD 検証: inline U-002 syntax error を含む file は py_compile fail を返す"""
    target = tmp_path / "broken.py"
    target.write_text("def broken(:\n    pass\n", encoding="utf-8")

    result = sprint_lint.check_py_compile([target.as_posix()])

    assert result["status"] == "fail"
    assert result["files_checked"] == 1
    assert result["errors"]


def test_check_relevant_tests_supports_path_selector(tmp_path: Path) -> None:
    """DoD 検証: inline U-003 path: selector で対象 pytest file のみ実行できる"""
    target = tmp_path / "test_selected.py"
    target.write_text(
        "\n".join(
            [
                "def test_selected_case():",
                "    assert True",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = sprint_lint.check_relevant_tests(f"path:{target.as_posix()}")

    assert result["status"] == "pass"
    assert result["tests_run"] == 1
    assert result["passed"] == 1
    assert result["failed"] == 0


def test_check_full_regression_skip_short_circuits() -> None:
    """DoD 検証: inline U-004 skip=True は heavy command を実行せず skipped を返す"""
    result = sprint_lint.check_full_regression(skip=True)

    assert result == {
        "status": "skipped",
        "pytest_passed": 0,
        "bats_passed": 0,
        "errors": [],
    }


def test_check_review_passes_with_recent_plan_review_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: inline U-005 .helix/reviews/plans/PLAN-XXX.json が 24h 以内なら review pass"""
    project_root = tmp_path
    review_dir = project_root / ".helix" / "reviews" / "plans"
    review_dir.mkdir(parents=True)
    review_path = review_dir / "PLAN-082.json"
    review_path.write_text(
        json.dumps({"summary": "pmo-sonnet と codex review approve"}, ensure_ascii=False),
        encoding="utf-8",
    )

    monkeypatch.setattr(sprint_lint, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(sprint_lint, "HELIX_DIR", project_root / ".helix")
    monkeypatch.setattr(sprint_lint, "REVIEW_DIR", review_dir)
    monkeypatch.setattr(sprint_lint, "AUDIT_RUN_DIR", project_root / ".helix" / "audit" / "codex-runs")
    monkeypatch.setattr(sprint_lint, "DB_PATH", project_root / ".helix" / "helix.db")

    result = sprint_lint.check_review("PLAN-082")

    assert result["status"] == "pass"
    assert "pmo-sonnet" in result["reviewers"]
    assert result["evidence"] == [".helix/reviews/plans/PLAN-082.json"]


def test_audit_sprint_completion_warns_when_review_missing_and_full_regression_skipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: inline U-006 review missing または full regression skipped なら overall=warn"""
    monkeypatch.setattr(sprint_lint, "_collect_changed_files", lambda: [Path("/tmp/sample.py")])
    monkeypatch.setattr(sprint_lint, "_unique_existing_python_files", lambda paths: ["/tmp/sample.py"])
    monkeypatch.setattr(sprint_lint, "_build_relevant_test_selector", lambda files, plan_id: "sample")
    monkeypatch.setattr(
        sprint_lint,
        "check_py_compile",
        lambda target_files: {"status": "pass", "files_checked": len(target_files), "errors": []},
    )
    monkeypatch.setattr(
        sprint_lint,
        "check_relevant_tests",
        lambda pattern: {"status": "pass", "tests_run": 2, "passed": 2, "failed": 0, "selection": pattern, "errors": []},
    )
    monkeypatch.setattr(
        sprint_lint,
        "check_full_regression",
        lambda skip=False: {"status": "skipped", "pytest_passed": 0, "bats_passed": 0, "errors": []},
    )
    monkeypatch.setattr(
        sprint_lint,
        "check_review",
        lambda plan_id=None: {"status": "missing", "reviewers": [], "evidence": []},
    )

    result = sprint_lint.audit_sprint_completion("PLAN-082", ".3", skip_full_regression=True)

    assert result["overall"] == "warn"
    assert result["checks"]["full_regression"]["status"] == "skipped"
    assert result["checks"]["review"]["status"] == "missing"


def test_main_json_strict_returns_nonzero_on_fail(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """DoD 検証: inline U-007 --json --strict は overall=fail のとき exit 1 を返す"""
    monkeypatch.setattr(
        sprint_lint,
        "audit_sprint_completion",
        lambda plan_id, sprint, skip_full_regression=False: {
            "plan_id": plan_id,
            "sprint": sprint,
            "checks": {
                "py_compile": {"status": "fail", "files_checked": 1, "errors": ["boom"]},
                "relevant_tests": {"status": "pass", "tests_run": 1, "passed": 1, "failed": 0, "selection": "x", "errors": []},
                "full_regression": {"status": "pass", "pytest_passed": 1, "bats_passed": 1, "errors": []},
                "review": {"status": "pass", "reviewers": ["codex"], "evidence": ["x"]},
            },
            "overall": "fail",
            "target_files": ["sample.py"],
            "relevant_test_selector": "x",
        },
    )

    exit_code = sprint_lint.main(["--plan-id", "PLAN-082", "--sprint", ".3", "--json", "--strict"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["overall"] == "fail"
    assert payload["checks"]["py_compile"]["status"] == "fail"


def test_collect_changed_files_prefers_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: inline U-008 HELIX_SPRINT_TARGET_FILES override が git status より優先される"""
    monkeypatch.setenv("HELIX_SPRINT_TARGET_FILES", "/tmp/a.py:/tmp/b.py")

    result = sprint_lint._collect_changed_files()

    assert [path.as_posix() for path in result] == ["/tmp/a.py", "/tmp/b.py"]
    monkeypatch.delenv("HELIX_SPRINT_TARGET_FILES")
