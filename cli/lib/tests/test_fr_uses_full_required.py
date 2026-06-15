from __future__ import annotations

import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import fr_uses_checks
import vg_overview


def _write_file(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    return path


def _write_registry(path: Path, entries: str) -> Path:
    return _write_file(path, f"entries:\n{entries}")


def _write_l2_waiver(root: Path) -> None:
    waiver_path = root / vg_overview.L2_L10_WAIVER_PATH
    waiver_path.parent.mkdir(parents=True, exist_ok=True)
    waiver_path.write_text(
        "\n".join(
            [
                "---",
                "applicability: not_applicable",
                "reason: ui_absent",
                "owner: TL",
                "process_layer: L2",
                "pairs_with: L10",
                "---",
                "",
                "# waiver",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _clean_report() -> SimpleNamespace:
    return SimpleNamespace(findings=[])


def _clean_pairs() -> dict[str, dict[str, dict[str, int] | float]]:
    return {
        name: {
            "coverage_pct": 100.0,
            "uncovered_req": {"count": 0},
            "orphan_test": {"count": 0},
            "duplicate_id": {"count": 0},
            "missing_pair_frontmatter": {"count": 0},
            "missing_pair": {"count": 0},
            "wrong_layer_pair": {"count": 0},
        }
        for name in vg_overview.PAIR_NAMES
    }


def test_full_required_summary_fails_when_full_scan_has_missing_target(tmp_path: Path) -> None:
    """DoD 検証: C-3a full-scan forward に missing-target があれば fail-close。"""

    registry_path = _write_registry(
        tmp_path / "cli/config/functional-registry.yaml",
        """
          - id: FR-A
            name: alpha
            domain: cli
            status: active
            uses: [FR-MISSING]
        """,
    )

    summary = fr_uses_checks.collect_fr_uses_full_required_summary(
        repo_root=tmp_path,
        registry_path=registry_path,
    )

    assert summary["clean"] is False
    assert summary["finding_count"] == 1
    assert summary["blocking_finding_count"] == 1
    assert summary["warning_count"] == 0
    assert summary["source_status"] == "full_required"


def test_full_required_summary_keeps_repo_clean_when_only_reverse_warnings_exist() -> None:
    """DoD 検証: C-3a reverse warning のみなら clean を維持する。"""

    repo_root = Path(__file__).resolve().parents[3]

    summary = fr_uses_checks.collect_fr_uses_full_required_summary(repo_root=repo_root)

    assert summary["clean"] is True
    assert summary["finding_count"] == 3
    assert summary["blocking_finding_count"] == 0
    assert summary["warning_count"] == 3
    assert summary["source_status"] == "full_required"


def test_full_required_summary_does_not_depend_on_changed_files_availability(tmp_path: Path, monkeypatch) -> None:
    """DoD 検証: C-3a full-required は changed-files unavailable に依存しない。"""

    registry_path = _write_registry(
        tmp_path / "cli/config/functional-registry.yaml",
        """
          - id: FR-A
            name: alpha
            domain: cli
            status: active
            uses: [FR-B]
          - id: FR-B
            name: beta
            domain: cli
            status: active
        """,
    )

    def _should_not_run(*args, **kwargs):
        raise AssertionError("changed_files should not be called in full-required mode")

    monkeypatch.setattr(fr_uses_checks, "changed_files", _should_not_run)

    summary = fr_uses_checks.collect_fr_uses_full_required_summary(
        repo_root=tmp_path,
        registry_path=registry_path,
    )

    assert summary["clean"] is True
    assert summary["finding_count"] == 1
    assert summary["blocking_finding_count"] == 0
    assert summary["warning_count"] == 1
    assert summary["source_status"] == "full_required"


def test_collect_vg_overview_uses_full_required_fr_uses_summary(monkeypatch, tmp_path: Path) -> None:
    """DoD 検証: vg_overview.required_clean.fr_uses_checks は full-required source を使う。"""

    _write_l2_waiver(tmp_path)

    monkeypatch.setattr(vg_overview, "check_registry_design_coverage", lambda *args, **kwargs: _clean_report())
    monkeypatch.setattr(vg_overview, "check_design_id_existence", lambda *args, **kwargs: _clean_report())
    monkeypatch.setattr(vg_overview, "check_fn_ut_pair_coverage", lambda *args, **kwargs: _clean_report())
    monkeypatch.setattr(vg_overview, "check_bc_anti_corruption", lambda *args, **kwargs: _clean_report())
    monkeypatch.setattr(vg_overview, "check_bc_mode_coverage", lambda *args, **kwargs: _clean_report())
    monkeypatch.setattr(
        vg_overview,
        "collect_coding_rule_lint_gate_summary",
        lambda *args, **kwargs: {
            "clean": True,
            "finding_count": 0,
            "source_status": "available_empty",
            "skipped_reason": None,
        },
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_dependency_cycle_gate_summary",
        lambda *args, **kwargs: {
            "clean": True,
            "finding_count": 0,
            "source_status": "available_empty",
            "skipped_reason": None,
        },
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_plan_dependency_gate_summary",
        lambda *args, **kwargs: {
            "clean": True,
            "finding_count": 0,
            "source_status": "available_empty",
            "skipped_reason": None,
        },
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_fr_uses_full_required_summary",
        lambda *args, **kwargs: {
            "clean": True,
            "finding_count": 3,
            "blocking_finding_count": 0,
            "warning_count": 3,
            "source_status": "full_required",
            "skipped_reason": None,
            "mode": "full_required",
        },
    )
    monkeypatch.setattr(vg_overview, "check_functional_registry", lambda *args, **kwargs: _clean_report())
    monkeypatch.setattr(
        vg_overview,
        "collect_requirement_drift",
        lambda *args, **kwargs: {
            "focus": "L6",
            "clean": True,
            "blocking_clean": True,
            "findings": {"waived_with_reason": []},
            "summary": {
                "requirements": 1,
                "design_links": 1,
                "blocking_findings": 0,
                "advisory_findings": 0,
            },
        },
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_trace_symmetry",
        lambda *args, **kwargs: {"pairs": _clean_pairs()},
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_g7_subcheck",
        lambda *args, **kwargs: {
            "ut_total": 88,
            "anchored": {"count": 88},
            "exec_pass": {"count": 88},
            "missing": {"count": 0},
            "unanchored_but_exists": {"count": 0},
        },
    )

    report = vg_overview.collect_vg_overview(tmp_path)
    required = report["vg_overview"]["required_clean"]["fr_uses_checks"]

    assert required["clean"] is True
    assert required["finding_count"] == 3
    assert required["blocking_finding_count"] == 0
    assert required["warning_count"] == 3
    assert required["source_status"] == "full_required"
    assert required["mode"] == "full_required"
    assert report["vg_overview"]["overall_clean"] is True
