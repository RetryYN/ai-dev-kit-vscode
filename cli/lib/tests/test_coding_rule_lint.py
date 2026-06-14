from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import coding_rule_lint


def _write_file(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    return path


def _write_registry(path: Path) -> Path:
    return _write_file(
        path,
        """
        entries:
          - id: CR-CODE-BASH
            rule: bash scripts stay mechanically linted
            sot_section: コーディング規約
            linter_tool:
              - bash_n
              - shellcheck
            enforcement:
              kind: ci_gate
              paths: []
              status: partial
          - id: CR-CODE-PY
            rule: python scripts stay mechanically linted
            sot_section: コーディング規約
            linter_tool:
              - py_compile
              - ruff
            enforcement:
              kind: ci_gate
              paths: []
              status: partial
        """,
    )


def _write_baseline(path: Path, findings: list[dict[str, object]]) -> Path:
    payload = {
        "intentional_baseline": True,
        "owner": "codex",
        "created": "2026-06-14",
        "expiry": "2026-09-12",
        "generated_by": "test",
        "reports": [
            {
                "check_name": "check_coding_rule_lint",
                "mode": "advisory",
                "findings": findings,
                "metrics": {"finding_count": len(findings)},
            }
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


@pytest.fixture()
def baseline_matched_project(tmp_path: Path) -> dict[str, Path]:
    registry_path = _write_registry(tmp_path / "cli/config/coding-rule-registry.yaml")
    bad_python = _write_file(
        tmp_path / "bad.py",
        """
        def broken(
            return 1
        """,
    )
    baseline_path = _write_baseline(
        tmp_path / "cli/config/coding-rule-registry-baseline.json",
        [
            {
                "rule_id": "CR-CODE-PY",
                "file": "bad.py",
                "line": 1,
                "tool": "py_compile",
                "message": "'(' was never closed",
                "fingerprint": coding_rule_lint.fingerprint_violation(
                    {
                        "rule_id": "CR-CODE-PY",
                        "file": "bad.py",
                        "line": 1,
                        "tool": "py_compile",
                        "message": "'(' was never closed",
                    }
                ),
            }
        ],
    )
    return {
        "project_root": tmp_path,
        "registry_path": registry_path,
        "baseline_path": baseline_path,
        "bad_python": bad_python,
    }


@pytest.fixture()
def new_violation_project(tmp_path: Path) -> dict[str, Path]:
    registry_path = _write_registry(tmp_path / "cli/config/coding-rule-registry.yaml")
    bad_python = _write_file(
        tmp_path / "new_bad.py",
        """
        def broken(
            return 1
        """,
    )
    baseline_path = _write_baseline(tmp_path / "cli/config/coding-rule-registry-baseline.json", [])
    return {
        "project_root": tmp_path,
        "registry_path": registry_path,
        "baseline_path": baseline_path,
        "bad_python": bad_python,
    }


def test_gate_passes_when_violation_is_already_in_baseline(
    baseline_matched_project: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-B baseline 内違反は changed-files gate で fail しない。"""

    monkeypatch.setattr(
        coding_rule_lint,
        "changed_files",
        lambda upstream=None: {"files": ["bad.py"], "source_status": "available_nonempty"},
    )

    report = coding_rule_lint.evaluate_coding_rule_lint(
        repo_root=baseline_matched_project["project_root"],
        registry_path=baseline_matched_project["registry_path"],
        baseline_path=baseline_matched_project["baseline_path"],
        gate=True,
    )

    assert report["exit_code"] == 0
    assert report["clean"] is True
    assert report["new_findings"] == []
    assert report["source_status"] == "available_nonempty"


def test_gate_fails_when_changed_files_add_new_violation(
    new_violation_project: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-B changed-files 上の baseline 外違反だけ gate fail になる。"""

    monkeypatch.setattr(
        coding_rule_lint,
        "changed_files",
        lambda upstream=None: {"files": ["new_bad.py"], "source_status": "available_nonempty"},
    )

    report = coding_rule_lint.evaluate_coding_rule_lint(
        repo_root=new_violation_project["project_root"],
        registry_path=new_violation_project["registry_path"],
        baseline_path=new_violation_project["baseline_path"],
        gate=True,
    )

    assert report["exit_code"] == 1
    assert report["clean"] is False
    assert len(report["new_findings"]) == 1
    assert report["new_findings"][0]["file"] == "new_bad.py"
    assert report["new_findings"][0]["tool"] == "py_compile"


def test_collect_runs_required_tools_even_when_optional_linters_are_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-B ruff/shellcheck 不在でも bash -n/py_compile は必須実行される。"""

    registry_path = _write_registry(tmp_path / "cli/config/coding-rule-registry.yaml")
    _write_file(
        tmp_path / "bad.sh",
        """
        #!/usr/bin/env bash
        if then
          echo broken
        fi
        """,
    )
    _write_file(
        tmp_path / "bad.py",
        """
        def broken(
            return 1
        """,
    )

    monkeypatch.setattr(coding_rule_lint.shutil, "which", lambda name: None if name in {"ruff", "shellcheck"} else f"/usr/bin/{name}")

    findings = coding_rule_lint.collect_violations(
        repo_root=tmp_path,
        registry_path=registry_path,
    )

    tools = {(finding["tool"], finding["file"]) for finding in findings}
    assert ("bash_n", "bad.sh") in tools
    assert ("py_compile", "bad.py") in tools
    assert all(tool not in {"ruff", "shellcheck"} for tool, _file in tools)


def test_gate_treats_available_empty_as_clean(
    new_violation_project: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-B changed-files available_empty は clean 扱い。"""

    monkeypatch.setattr(
        coding_rule_lint,
        "changed_files",
        lambda upstream=None: {"files": [], "source_status": "available_empty"},
    )

    report = coding_rule_lint.evaluate_coding_rule_lint(
        repo_root=new_violation_project["project_root"],
        registry_path=new_violation_project["registry_path"],
        baseline_path=new_violation_project["baseline_path"],
        gate=True,
    )

    assert report["exit_code"] == 0
    assert report["clean"] is True
    assert report["source_status"] == "available_empty"
    assert report["new_findings"] == []


def test_gate_skips_without_failing_when_changed_files_is_unavailable(
    new_violation_project: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-B changed-files unavailable は skip であり fail しない。"""

    monkeypatch.setattr(
        coding_rule_lint,
        "changed_files",
        lambda upstream=None: {"files": [], "source_status": "unavailable"},
    )

    report = coding_rule_lint.evaluate_coding_rule_lint(
        repo_root=new_violation_project["project_root"],
        registry_path=new_violation_project["registry_path"],
        baseline_path=new_violation_project["baseline_path"],
        gate=True,
    )

    assert report["exit_code"] == 0
    assert report["clean"] is False
    assert report["skipped_reason"] == "changed-files unavailable"
    assert report["source_status"] == "unavailable"
