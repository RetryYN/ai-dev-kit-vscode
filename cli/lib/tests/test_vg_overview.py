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


def test_collect_vg_overview_aggregates_required_clean_and_pair_status(monkeypatch, tmp_path: Path) -> None:
    _write_l2_waiver(tmp_path)
    monkeypatch.setattr(vg_overview, "check_registry_design_coverage", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_functional_registry", lambda *args, **kwargs: _report("unregistered_asset"))
    monkeypatch.setattr(
        vg_overview,
        "collect_requirement_drift",
        lambda *args, **kwargs: {
            "focus": "L6",
            "clean": True,
            "blocking_clean": True,
            "findings": {
                "missing_downstream": [],
                "orphan_design": [],
                "orphan_code": [],
                "semantic_label_mismatch": [],
                "stale_freeze": [],
                "waived_with_reason": [],
            },
            "summary": {
                "requirements": 1,
                "design_links": 1,
                "code_links": 0,
                "test_links": 0,
                "blocking_findings": 0,
                "advisory_findings": 0,
            },
        },
    )
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
    assert vg["required_clean"]["requirement_drift"]["clean"] is True
    assert vg["required_clean"]["requirement_drift"]["finding_count"] == 0
    assert vg["required_clean"]["requirement_drift"]["focus"] == "L6"
    assert vg["full_flow_execution"]["enforced"] is False
    assert vg["full_flow_execution"]["clean"] is False
    assert vg["full_flow_execution"]["deferred_count"] == 4
    assert vg["full_flow_execution"]["deferred_pairs"][0]["gate_id"].startswith("G")
    assert "next_action" in vg["full_flow_execution"]["deferred_pairs"][0]
    assert vg["full_flow_execution"]["not_applicable_count"] == 1
    assert vg["full_flow_execution"]["not_applicable_pairs"][0]["pair"] == "L2-L10"
    assert vg["full_flow_execution"]["not_applicable_pairs"][0]["waiver"]["reason"] == "ui_absent"
    assert vg["pair_status"]["L6-L7"]["status"] == "applicable"
    assert vg["pair_status"]["L6-L7"]["clean"] is False
    assert vg["pair_status"]["L5-L8"]["status"] == "approved_deferred"
    assert "execution_gate_not_implemented" in vg["pair_status"]["L5-L8"]["reason"]
    assert vg["pair_status"]["L2-L10"]["status"] == "not_applicable"
    assert "ui_absent waiver=" in vg["pair_status"]["L2-L10"]["reason"]
    assert vg["pair_status"]["L2-L10"]["waiver"]["owner"] == "TL"
    assert vg["pair_status"]["L2-L10"]["waiver"]["process_layer"] == "L2"
    assert vg["pair_status"]["L2-L10"]["waiver"]["pairs_with"] == "L10"
    assert vg["pair_status"]["L2-L10"]["waiver"]["unskip_required_when"]


def test_collect_vg_overview_strict_full_flow_fails_approved_deferred_pairs(
    monkeypatch, tmp_path: Path
) -> None:
    _write_l2_waiver(tmp_path)
    monkeypatch.setattr(vg_overview, "check_registry_design_coverage", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_functional_registry", lambda *args, **kwargs: _report())
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
        lambda *args, **kwargs: {
            "pairs": {
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
        },
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

    default_report = vg_overview.collect_vg_overview(tmp_path)
    strict_report = vg_overview.collect_vg_overview(tmp_path, strict_full_flow=True)

    assert default_report["vg_overview"]["overall_clean"] is True
    strict_vg = strict_report["vg_overview"]
    assert strict_vg["overall_clean"] is False
    assert strict_vg["block_condition"] == "approved_deferred execution gate > 0"
    assert strict_vg["full_flow_execution"]["enforced"] is True
    assert strict_vg["full_flow_execution"]["clean"] is False
    assert strict_vg["full_flow_execution"]["deferred_count"] == 4
    assert strict_vg["full_flow_execution"]["not_applicable_count"] == 1
    assert strict_vg["full_flow_execution"]["not_applicable_pairs"][0]["waiver"]["path"].endswith(
        "helix-workflows-ui-absent-waiver.md"
    )
    assert {item["pair"] for item in strict_vg["full_flow_execution"]["deferred_pairs"]} == {
        "L1-L14",
        "L3-L12",
        "L4-L9",
        "L5-L8",
    }
    assert {item["pair"]: item["gate_id"] for item in strict_vg["full_flow_execution"]["deferred_pairs"]} == {
        "L1-L14": "G14",
        "L3-L12": "G12",
        "L4-L9": "G9",
        "L5-L8": "G8",
    }
    assert all(
        item["reference"] == "HELIX-workflows/helix-process/automation-gate-map.md"
        for item in strict_vg["full_flow_execution"]["deferred_pairs"]
    )


def test_l2_l10_status_requires_explicit_waiver(tmp_path: Path) -> None:
    result = vg_overview._l2_l10_status(tmp_path)

    assert result["status"] == "applicable"
    assert result["clean"] is False
    assert "ui waiver missing" in result["reason"]
    assert result["waiver"] is None


def test_l2_l10_status_rejects_incomplete_waiver(tmp_path: Path) -> None:
    waiver_path = tmp_path / vg_overview.L2_L10_WAIVER_PATH
    waiver_path.parent.mkdir(parents=True, exist_ok=True)
    waiver_path.write_text(
        "\n".join(
            [
                "---",
                "applicability: not_applicable",
                "reason: ui_absent",
                "pairs_with: L10",
                "---",
                "# incomplete",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = vg_overview._l2_l10_status(tmp_path)

    assert result["status"] == "applicable"
    assert result["clean"] is False
    assert result["waiver"]["owner"] == ""
    assert result["waiver"]["process_layer"] == ""


def test_collect_vg_overview_fails_required_clean_when_requirement_drift_is_dirty(
    monkeypatch, tmp_path: Path
) -> None:
    _write_l2_waiver(tmp_path)
    monkeypatch.setattr(vg_overview, "check_registry_design_coverage", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_functional_registry", lambda *args, **kwargs: _report())
    monkeypatch.setattr(
        vg_overview,
        "collect_trace_symmetry",
        lambda *args, **kwargs: {
            "pairs": {
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
        },
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
    monkeypatch.setattr(
        vg_overview,
        "collect_requirement_drift",
        lambda *args, **kwargs: {
            "focus": "L6",
            "clean": False,
            "blocking_clean": False,
            "findings": {
                "missing_downstream": [{"requirement_id": "FR-001"}],
                "orphan_design": [],
                "orphan_code": [],
                "semantic_label_mismatch": [],
                "stale_freeze": [],
                "waived_with_reason": [],
            },
            "summary": {
                "requirements": 1,
                "design_links": 0,
                "code_links": 0,
                "test_links": 0,
                "blocking_findings": 1,
                "advisory_findings": 0,
            },
        },
    )

    report = vg_overview.collect_vg_overview(tmp_path)
    requirement = report["vg_overview"]["required_clean"]["requirement_drift"]

    assert report["vg_overview"]["overall_clean"] is False
    assert requirement["clean"] is False
    assert requirement["finding_count"] == 1
    assert requirement["focus"] == "L6"
    assert requirement["requirements"] == 1
    assert requirement["design_links"] == 0
