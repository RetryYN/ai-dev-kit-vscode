from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import plan_dependency_gate


def _write_file(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    return path


def _write_plan(project_root: Path, relative_path: str, frontmatter: str) -> Path:
    return _write_file(
        project_root / relative_path,
        f"---\n{textwrap.dedent(frontmatter).strip()}\n---\n\n# Body\n",
    )


def _write_baseline(path: Path, warnings: list[dict[str, object]]) -> Path:
    payload = {
        "intentional_baseline": True,
        "owner": "codex",
        "created": "2026-06-14",
        "expiry": "2026-09-12",
        "generated_by": "test",
        "accepted_dependency_warning": warnings,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


@pytest.fixture()
def baseline_warning_project(tmp_path: Path) -> dict[str, Path]:
    plan_a = _write_plan(
        tmp_path,
        "docs/plans/L7/L7-401-alpha-plan.md",
        """
        plan_id: L7-401-alpha-plan
        title: Alpha
        plan_scope: action
        kind: impl
        layer: L7
        drive: be
        status: draft
        dependencies:
          parent: null
          requires: []
          blocks:
            - L7-402-beta-plan
        """,
    )
    _write_plan(
        tmp_path,
        "docs/plans/L7/L7-402-beta-plan.md",
        """
        plan_id: L7-402-beta-plan
        title: Beta
        plan_scope: action
        kind: impl
        layer: L7
        drive: be
        status: draft
        dependencies:
          parent: null
          requires: []
          blocks: []
        """,
    )
    baseline_path = _write_baseline(
        tmp_path / "cli/config/plan-dependency-baseline.json",
        [
            {
                "plan_id": "L7-401-alpha-plan",
                "field": "dependencies.blocks",
                "reason": "L7-402-beta-plan does not require L7-401-alpha-plan",
                "kind": "missing_reciprocal",
                "fingerprint": plan_dependency_gate.fingerprint_dependency_warning(
                    "L7-401-alpha-plan",
                    "dependencies.blocks",
                    "L7-402-beta-plan does not require L7-401-alpha-plan",
                ),
            }
        ],
    )
    return {"project_root": tmp_path, "baseline_path": baseline_path, "changed_plan": plan_a}


@pytest.fixture()
def cycle_project(tmp_path: Path) -> dict[str, Path]:
    plan_a = _write_plan(
        tmp_path,
        "docs/plans/L7/L7-501-alpha-plan.md",
        """
        plan_id: L7-501-alpha-plan
        title: Alpha
        plan_scope: action
        kind: impl
        layer: L7
        drive: be
        status: draft
        dependencies:
          parent: null
          requires:
            - L7-502-beta-plan
          blocks: []
        """,
    )
    _write_plan(
        tmp_path,
        "docs/plans/L7/L7-502-beta-plan.md",
        """
        plan_id: L7-502-beta-plan
        title: Beta
        plan_scope: action
        kind: impl
        layer: L7
        drive: be
        status: draft
        dependencies:
          parent: null
          requires:
            - L7-501-alpha-plan
          blocks: []
        """,
    )
    baseline_path = _write_baseline(tmp_path / "cli/config/plan-dependency-baseline.json", [])
    return {"project_root": tmp_path, "baseline_path": baseline_path, "changed_plan": plan_a}


@pytest.fixture()
def missing_reciprocal_project(tmp_path: Path) -> dict[str, Path]:
    plan_a = _write_plan(
        tmp_path,
        "docs/plans/L7/L7-601-alpha-plan.md",
        """
        plan_id: L7-601-alpha-plan
        title: Alpha
        plan_scope: action
        kind: impl
        layer: L7
        drive: be
        status: draft
        dependencies:
          parent: null
          requires: []
          blocks:
            - L7-602-beta-plan
        """,
    )
    _write_plan(
        tmp_path,
        "docs/plans/L7/L7-602-beta-plan.md",
        """
        plan_id: L7-602-beta-plan
        title: Beta
        plan_scope: action
        kind: impl
        layer: L7
        drive: be
        status: draft
        dependencies:
          parent: null
          requires: []
          blocks: []
        """,
    )
    baseline_path = _write_baseline(tmp_path / "cli/config/plan-dependency-baseline.json", [])
    return {"project_root": tmp_path, "baseline_path": baseline_path, "changed_plan": plan_a}


def test_gate_passes_when_warning_is_already_waived_in_baseline(
    baseline_warning_project: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-C 既存 WARN は baseline waiver で gate fail しない。"""

    monkeypatch.setattr(
        plan_dependency_gate,
        "changed_files",
        lambda upstream=None: {
            "files": ["docs/plans/L7/L7-401-alpha-plan.md"],
            "source_status": "available_nonempty",
        },
    )

    report = plan_dependency_gate.check_plan_dependency_gate(
        repo_root=baseline_warning_project["project_root"],
        baseline_path=baseline_warning_project["baseline_path"],
        gate=True,
    )

    assert report["exit_code"] == 0
    assert report["clean"] is True
    assert report["finding_count"] == 1
    assert report["new_finding_count"] == 0


def test_gate_fails_for_new_cycle_on_changed_plan(
    cycle_project: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-C 新規 real cycle は changed plan で gate fail になる。"""

    monkeypatch.setattr(
        plan_dependency_gate,
        "changed_files",
        lambda upstream=None: {
            "files": ["docs/plans/L7/L7-501-alpha-plan.md"],
            "source_status": "available_nonempty",
        },
    )

    report = plan_dependency_gate.check_plan_dependency_gate(
        repo_root=cycle_project["project_root"],
        baseline_path=cycle_project["baseline_path"],
        gate=True,
    )

    assert report["exit_code"] == 1
    assert report["clean"] is False
    assert report["blocking_finding_count"] == 1
    assert report["blocking_findings"][0]["kind"] == "cycle"


def test_gate_fails_for_new_missing_reciprocal_on_changed_plan(
    missing_reciprocal_project: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-C 新規 missing reciprocal は changed plan で gate fail になる。"""

    monkeypatch.setattr(
        plan_dependency_gate,
        "changed_files",
        lambda upstream=None: {
            "files": ["docs/plans/L7/L7-601-alpha-plan.md"],
            "source_status": "available_nonempty",
        },
    )

    report = plan_dependency_gate.check_plan_dependency_gate(
        repo_root=missing_reciprocal_project["project_root"],
        baseline_path=missing_reciprocal_project["baseline_path"],
        gate=True,
    )

    assert report["exit_code"] == 1
    assert report["clean"] is False
    assert report["blocking_finding_count"] == 1
    assert report["blocking_findings"][0]["kind"] == "missing_reciprocal"


def test_gate_treats_available_empty_as_clean(
    cycle_project: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-C plan dependency gate は available_empty を clean 扱いする。"""

    monkeypatch.setattr(
        plan_dependency_gate,
        "changed_files",
        lambda upstream=None: {"files": [], "source_status": "available_empty"},
    )

    report = plan_dependency_gate.check_plan_dependency_gate(
        repo_root=cycle_project["project_root"],
        baseline_path=cycle_project["baseline_path"],
        gate=True,
    )

    assert report["exit_code"] == 0
    assert report["clean"] is True
    assert report["findings"] == []


def test_gate_skips_without_failing_when_changed_files_is_unavailable(
    cycle_project: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-C plan dependency gate は unavailable を skip にする。"""

    monkeypatch.setattr(
        plan_dependency_gate,
        "changed_files",
        lambda upstream=None: {"files": [], "source_status": "unavailable"},
    )

    report = plan_dependency_gate.check_plan_dependency_gate(
        repo_root=cycle_project["project_root"],
        baseline_path=cycle_project["baseline_path"],
        gate=True,
    )

    assert report["exit_code"] == 0
    assert report["clean"] is False
    assert report["source_status"] == "unavailable"
    assert report["skipped_reason"] == "changed-files unavailable"
