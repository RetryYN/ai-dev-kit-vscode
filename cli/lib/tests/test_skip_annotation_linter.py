from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from datetime import date
from pathlib import Path

import py_compile


LIB_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import skip_annotation_linter


MODULE_PATH = LIB_DIR / "skip_annotation_linter.py"


def _write_module(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "sample_skip.py"
    path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")
    return path


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_clean_fixture_with_helix_skip_format_returns_exit_zero(tmp_path: Path) -> None:
    file_path = _write_module(
        tmp_path,
        """
        import pytest

        @pytest.mark.skip(reason="HELIX-SKIP: env_dependent | PLAN-065 | due_date: 2026-06-01")
        def test_sample():
            assert True
        """,
    )

    result = skip_annotation_linter.lint_skip_annotations([file_path], today=date(2026, 5, 13))

    assert result.exit_code == 0
    assert result.findings == ()


def test_invalid_category_yields_one_finding(tmp_path: Path) -> None:
    file_path = _write_module(
        tmp_path,
        """
        import pytest

        @pytest.mark.skip(reason="HELIX-SKIP: invalid_category | PLAN-065 | due_date: 2026-06-01")
        def test_sample():
            assert True
        """,
    )

    result = skip_annotation_linter.lint_skip_annotations([file_path], today=date(2026, 5, 13))

    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.code == "INVALID_SKIP_ANNOTATION"
    assert finding.message == "invalid category: invalid_category"


def test_invalid_plan_id_yields_one_finding(tmp_path: Path) -> None:
    file_path = _write_module(
        tmp_path,
        """
        import pytest

        @pytest.mark.skip(reason="HELIX-SKIP: env_dependent | PLAN-65 | due_date: 2026-06-01")
        def test_sample():
            assert True
        """,
    )

    result = skip_annotation_linter.lint_skip_annotations([file_path], today=date(2026, 5, 13))

    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.code == "INVALID_SKIP_ANNOTATION"
    assert finding.message == "invalid plan id: PLAN-65"


def test_invalid_due_date_format_yields_one_finding(tmp_path: Path) -> None:
    file_path = _write_module(
        tmp_path,
        """
        import pytest

        @pytest.mark.skip(reason="HELIX-SKIP: env_dependent | PLAN-065 | due_date: 2026/06/01")
        def test_sample():
            assert True
        """,
    )

    result = skip_annotation_linter.lint_skip_annotations([file_path], today=date(2026, 5, 13))

    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.code == "INVALID_SKIP_ANNOTATION"
    assert finding.message == "invalid due date: 2026/06/01"


def test_overdue_skip_is_warning_and_strict_mode_escalates_to_error(tmp_path: Path) -> None:
    file_path = _write_module(
        tmp_path,
        """
        import pytest

        @pytest.mark.skip(reason="HELIX-SKIP: env_dependent | PLAN-065 | due_date: 2026-04-01")
        def test_sample():
            assert True
        """,
    )

    warning_result = skip_annotation_linter.lint_skip_annotations([file_path], today=date(2026, 5, 13))
    strict_result = skip_annotation_linter.lint_skip_annotations([file_path], today=date(2026, 5, 13), strict=True)

    assert len(warning_result.findings) == 1
    assert warning_result.findings[0].severity == "warning"
    assert warning_result.findings[0].code == "OVERDUE_SKIP_ANNOTATION"
    assert strict_result.findings[0].severity == "error"
    assert strict_result.exit_code == 1


def test_unstructured_skip_reason_emits_warning(tmp_path: Path) -> None:
    file_path = _write_module(
        tmp_path,
        """
        import pytest

        @pytest.mark.skip(reason="temporary skip")
        def test_sample():
            assert True
        """,
    )

    result = skip_annotation_linter.lint_skip_annotations([file_path], today=date(2026, 5, 13))

    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.code == "UNSTRUCTURED_SKIP"
    assert finding.severity == "warning"


def test_plain_string_literals_and_helper_calls_are_ignored(tmp_path: Path) -> None:
    file_path = _write_module(
        tmp_path,
        """
        import re

        HELIX_SKIP_RE = re.compile(r"^HELIX-SKIP: env_dependent | PLAN-065 | due_date: 2026-06-01$")

        def _maybe_record_skip(value):
            return value

        def build_message():
            return "HELIX-SKIP: env_dependent | PLAN-065 | due_date: 2026-06-01"

        def test_sample():
            _maybe_record_skip("temporary")
            assert build_message().startswith("HELIX-SKIP:")
        """,
    )

    result = skip_annotation_linter.lint_skip_annotations([file_path], today=date(2026, 5, 13))

    assert result.exit_code == 0
    assert result.findings == ()


def test_cli_json_format_is_executable(tmp_path: Path) -> None:
    file_path = _write_module(
        tmp_path,
        """
        import pytest

        @pytest.mark.skip(reason="HELIX-SKIP: env_dependent | PLAN-065 | due_date: 2026-06-01")
        def test_sample():
            assert True
        """,
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.lib.skip_annotation_linter",
            "--path",
            str(file_path),
            "--format",
            "json",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["summary"]["findings"] == 0
    assert payload["summary"]["files_scanned"] == 1
