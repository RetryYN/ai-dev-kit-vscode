from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import dependency_cycle_checks


def _write_file(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    return path


def _write_import_cycle_baseline(path: Path, cycles: list[dict[str, object]]) -> Path:
    payload = {
        "intentional_baseline": True,
        "owner": "codex",
        "created": "2026-06-14",
        "expiry": "2026-09-12",
        "generated_by": "test",
        "reports": [
            {
                "check_name": "check_import_cycle",
                "mode": "advisory",
                "findings": cycles,
                "metrics": {"cycle_count": len(cycles)},
            }
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


@pytest.fixture()
def python_cycle_project(tmp_path: Path) -> dict[str, Path]:
    _write_file(tmp_path / "cli/lib/alpha.py", "import beta\n")
    _write_file(tmp_path / "cli/lib/beta.py", "import alpha\n")
    baseline_path = _write_import_cycle_baseline(tmp_path / "cli/config/import-cycle-baseline.json", [])
    return {"project_root": tmp_path, "baseline_path": baseline_path}


@pytest.fixture()
def baseline_cycle_project(tmp_path: Path) -> dict[str, Path]:
    _write_file(tmp_path / "cli/lib/alpha.py", "import beta\n")
    _write_file(tmp_path / "cli/lib/beta.py", "import alpha\n")
    baseline_path = _write_import_cycle_baseline(
        tmp_path / "cli/config/import-cycle-baseline.json",
        [
            {
                "language": "python",
                "cycle": ["cli/lib/alpha.py", "cli/lib/beta.py", "cli/lib/alpha.py"],
                "fingerprint": dependency_cycle_checks.fingerprint_cycle(
                    ["cli/lib/alpha.py", "cli/lib/beta.py", "cli/lib/alpha.py"],
                    language="python",
                ),
            }
        ],
    )
    return {"project_root": tmp_path, "baseline_path": baseline_path}


@pytest.fixture()
def clean_project(tmp_path: Path) -> dict[str, Path]:
    _write_file(tmp_path / "cli/lib/alpha.py", "import json\n")
    _write_file(tmp_path / "cli/lib/beta.py", "from pathlib import Path\n")
    _write_file(
        tmp_path / "cli/helix-alpha",
        """
        #!/usr/bin/env bash
        source "$SCRIPT_DIR/lib/helix-common.sh"
        """,
    )
    _write_file(tmp_path / "cli/lib/helix-common.sh", "#!/usr/bin/env bash\n")
    baseline_path = _write_import_cycle_baseline(tmp_path / "cli/config/import-cycle-baseline.json", [])
    return {"project_root": tmp_path, "baseline_path": baseline_path}


def test_collect_cycles_detects_python_and_bash_cycles(tmp_path: Path) -> None:
    """DoD 検証: WI-C import cycle detector は Python/Bash の循環を検出する。"""

    _write_file(tmp_path / "cli/lib/alpha.py", "import beta\n")
    _write_file(tmp_path / "cli/lib/beta.py", "import alpha\n")
    _write_file(
        tmp_path / "cli/loop-a.sh",
        """
        #!/usr/bin/env bash
        source "$SCRIPT_DIR/loop-b.sh"
        """,
    )
    _write_file(
        tmp_path / "cli/loop-b.sh",
        """
        #!/usr/bin/env bash
        source "$SCRIPT_DIR/loop-a.sh"
        """,
    )

    findings = dependency_cycle_checks.collect_dependency_cycle_findings(repo_root=tmp_path)

    languages = {finding["language"] for finding in findings}
    assert languages == {"bash", "python"}
    assert any(finding["cycle"] == ["cli/lib/alpha.py", "cli/lib/beta.py", "cli/lib/alpha.py"] for finding in findings)
    assert any(finding["cycle"] == ["cli/loop-a.sh", "cli/loop-b.sh", "cli/loop-a.sh"] for finding in findings)


def test_gate_fails_only_for_new_cycles(
    python_cycle_project: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-C changed-files 上の baseline 外循環だけ gate fail になる。"""

    monkeypatch.setattr(
        dependency_cycle_checks,
        "changed_files",
        lambda upstream=None: {"files": ["cli/lib/alpha.py"], "source_status": "available_nonempty"},
    )

    report = dependency_cycle_checks.check_dependency_cycle_gate(
        repo_root=python_cycle_project["project_root"],
        baseline_path=python_cycle_project["baseline_path"],
        gate=True,
    )

    assert report["exit_code"] == 1
    assert report["clean"] is False
    assert report["finding_count"] == 1
    assert report["new_finding_count"] == 1
    assert report["findings"][0]["language"] == "python"


def test_gate_passes_for_cycle_already_recorded_in_baseline(
    baseline_cycle_project: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-C baseline 内循環は changed-files gate で fail しない。"""

    monkeypatch.setattr(
        dependency_cycle_checks,
        "changed_files",
        lambda upstream=None: {"files": ["cli/lib/alpha.py"], "source_status": "available_nonempty"},
    )

    report = dependency_cycle_checks.check_dependency_cycle_gate(
        repo_root=baseline_cycle_project["project_root"],
        baseline_path=baseline_cycle_project["baseline_path"],
        gate=True,
    )

    assert report["exit_code"] == 0
    assert report["clean"] is True
    assert report["finding_count"] == 1
    assert report["new_finding_count"] == 0


def test_gate_treats_available_empty_as_clean(
    python_cycle_project: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-C changed-files available_empty は clean 扱い。"""

    monkeypatch.setattr(
        dependency_cycle_checks,
        "changed_files",
        lambda upstream=None: {"files": [], "source_status": "available_empty"},
    )

    report = dependency_cycle_checks.check_dependency_cycle_gate(
        repo_root=python_cycle_project["project_root"],
        baseline_path=python_cycle_project["baseline_path"],
        gate=True,
    )

    assert report["exit_code"] == 0
    assert report["clean"] is True
    assert report["source_status"] == "available_empty"
    assert report["findings"] == []


def test_gate_skips_without_failing_when_changed_files_is_unavailable(
    python_cycle_project: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-C changed-files unavailable は skip であり fail しない。"""

    monkeypatch.setattr(
        dependency_cycle_checks,
        "changed_files",
        lambda upstream=None: {"files": [], "source_status": "unavailable"},
    )

    report = dependency_cycle_checks.check_dependency_cycle_gate(
        repo_root=python_cycle_project["project_root"],
        baseline_path=python_cycle_project["baseline_path"],
        gate=True,
    )

    assert report["exit_code"] == 0
    assert report["clean"] is False
    assert report["source_status"] == "unavailable"
    assert report["skipped_reason"] == "changed-files unavailable"


def test_collect_cycles_ignores_clean_graph(clean_project: dict[str, Path]) -> None:
    """DoD 検証: WI-C 循環が無い import/source graph は clean になる。"""

    report = dependency_cycle_checks.check_dependency_cycle_gate(
        repo_root=clean_project["project_root"],
        baseline_path=clean_project["baseline_path"],
        gate=False,
    )

    assert report["exit_code"] == 0
    assert report["clean"] is True
    assert report["finding_count"] == 0


def test_collect_import_cycle_baseline_required_summary_is_clean_for_existing_cycles(
    baseline_cycle_project: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: C-3e baseline 内既存循環だけなら full-scan clean。"""

    def _unexpected_changed_files(*args, **kwargs):
        raise AssertionError("changed_files should not be used by baseline-required summary")

    monkeypatch.setattr(dependency_cycle_checks, "changed_files", _unexpected_changed_files)

    report = dependency_cycle_checks.collect_import_cycle_baseline_required_summary(
        repo_root=baseline_cycle_project["project_root"],
        baseline_path=baseline_cycle_project["baseline_path"],
    )

    assert report["clean"] is True
    assert report["finding_count"] == 1
    assert report["blocking_finding_count"] == 0
    assert report["warning_count"] == 1
    assert report["source_status"] == "baseline_required"
    assert report["mode"] == "baseline_required"


def test_collect_import_cycle_baseline_required_summary_blocks_new_cycles(
    python_cycle_project: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: C-3e baseline 超の新循環は changed-files 非依存で blocking。"""

    def _unexpected_changed_files(*args, **kwargs):
        raise AssertionError("changed_files should not be used by baseline-required summary")

    monkeypatch.setattr(dependency_cycle_checks, "changed_files", _unexpected_changed_files)

    report = dependency_cycle_checks.collect_import_cycle_baseline_required_summary(
        repo_root=python_cycle_project["project_root"],
        baseline_path=python_cycle_project["baseline_path"],
    )

    assert report["clean"] is False
    assert report["finding_count"] == 1
    assert report["blocking_finding_count"] == 1
    assert report["warning_count"] == 0
    assert report["source_status"] == "baseline_required"
    assert report["mode"] == "baseline_required"
