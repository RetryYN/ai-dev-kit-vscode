from __future__ import annotations

import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import vg_overview
from registry_checks import DetectorReport, Finding


def _report(kind: str | None = None) -> DetectorReport:
    findings = []
    if kind is not None:
        findings = [
            Finding(
                severity="P3",
                kind=kind,
                entry_id="FR-001",
                path="cli/config/functional-registry.yaml",
                message=kind,
                remediation="fix",
            )
        ]
    return DetectorReport.build(
        check_name="sample",
        domain="test",
        mode="advisory",
        findings=findings,
        metrics={},
        baseline=set(),
    )


def test_collect_vg_overview_aggregates_required_clean_and_pair_status(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(vg_overview, "check_registry_design_coverage", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_functional_registry", lambda *args, **kwargs: _report("unregistered_asset"))
    monkeypatch.setattr(
        vg_overview,
        "collect_trace_symmetry",
        lambda *args, **kwargs: {
            "pairs": {
                "L6-L7": {
                    "coverage_pct": 100.0,
                    "uncovered_req": {"count": 0},
                    "orphan_test": {"count": 0},
                    "duplicate_id": {"count": 0},
                    "missing_pair_frontmatter": {"count": 0},
                    "missing_pair": {"count": 0},
                    "wrong_layer_pair": {"count": 0},
                },
                "L5-L8": {
                    "coverage_pct": 100.0,
                    "uncovered_req": {"count": 0},
                    "orphan_test": {"count": 0},
                    "duplicate_id": {"count": 0},
                    "missing_pair_frontmatter": {"count": 0},
                    "missing_pair": {"count": 0},
                    "wrong_layer_pair": {"count": 0},
                },
                "L4-L9": {
                    "coverage_pct": 100.0,
                    "uncovered_req": {"count": 0},
                    "orphan_test": {"count": 0},
                    "duplicate_id": {"count": 0},
                    "missing_pair_frontmatter": {"count": 0},
                    "missing_pair": {"count": 0},
                    "wrong_layer_pair": {"count": 0},
                },
                "L3-L12": {
                    "coverage_pct": 100.0,
                    "uncovered_req": {"count": 0},
                    "orphan_test": {"count": 0},
                    "duplicate_id": {"count": 0},
                    "missing_pair_frontmatter": {"count": 0},
                    "missing_pair": {"count": 0},
                    "wrong_layer_pair": {"count": 0},
                },
                "L1-L14": {
                    "coverage_pct": 100.0,
                    "uncovered_req": {"count": 0},
                    "orphan_test": {"count": 0},
                    "duplicate_id": {"count": 0},
                    "missing_pair_frontmatter": {"count": 0},
                    "missing_pair": {"count": 0},
                    "wrong_layer_pair": {"count": 0},
                },
            }
        },
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_g7_subcheck",
        lambda *args, **kwargs: {
            "ut_total": 88,
            "anchored": {"count": 84},
            "exec_pass": {"count": 84},
            "missing": {"count": 1},
            "unanchored_but_exists": {"count": 3},
        },
    )

    report = vg_overview.collect_vg_overview(tmp_path)
    vg = report["vg_overview"]

    assert vg["required_clean"]["registry_design_coverage"]["clean"] is True
    assert vg["required_clean"]["source_scan_vs_registry"]["clean"] is False
    assert vg["pair_status"]["L6-L7"]["status"] == "applicable"
    assert vg["pair_status"]["L6-L7"]["clean"] is False
    assert vg["pair_status"]["L5-L8"]["status"] == "approved_deferred"
    assert "execution_gate_not_implemented" in vg["pair_status"]["L5-L8"]["reason"]
    assert vg["pair_status"]["L2-L10"]["status"] == "not_applicable"
    assert vg["pair_status"]["L2-L10"]["reason"] == "ui_absent"
