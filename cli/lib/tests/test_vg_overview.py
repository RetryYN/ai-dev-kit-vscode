from __future__ import annotations

import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import vg_overview
from registry_checks import DetectorReport, Finding

ST_IDS = [
    "ST-SYS-01",
    "ST-SYS-02",
    "ST-SYS-03",
    "ST-FR-01",
    "ST-FR-02",
    "ST-FR-03",
    "ST-FR-04",
    "ST-DATA-01",
    "ST-DATA-02",
    "ST-IF-01",
    "ST-IF-02",
    "ST-IF-03",
    "ST-NFR-01",
    "ST-NFR-02",
    "ST-NFR-03",
    "ST-IF-04",
    "ST-NEG-01",
    "ST-NEG-02",
]


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


def _stub_clean_ddd_bc_checks(monkeypatch) -> None:
    monkeypatch.setattr(vg_overview, "check_bc_anti_corruption", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_bc_mode_coverage", lambda *args, **kwargs: _report())


def _gate_summary(
    *,
    clean: bool = True,
    finding_count: int = 0,
    source_status: str = "available_empty",
    skipped_reason: str | None = None,
) -> dict[str, object]:
    return {
        "clean": clean,
        "finding_count": finding_count,
        "source_status": source_status,
        "skipped_reason": skipped_reason,
    }


def _stub_clean_ratchet_gate_summaries(monkeypatch) -> None:
    monkeypatch.setattr(
        vg_overview,
        "collect_coding_rule_lint_gate_summary",
        lambda *args, **kwargs: _gate_summary(),
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_dependency_cycle_gate_summary",
        lambda *args, **kwargs: _gate_summary(),
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_plan_dependency_gate_summary",
        lambda *args, **kwargs: _gate_summary(),
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_fr_uses_gate_summary",
        lambda *args, **kwargs: _gate_summary(),
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_fr_uses_full_required_summary",
        lambda *args, **kwargs: {
            "clean": True,
            "finding_count": 0,
            "blocking_finding_count": 0,
            "warning_count": 0,
            "source_status": "full_required",
            "skipped_reason": None,
            "mode": "full_required",
        },
    )


def _stub_clean_g8_subcheck(monkeypatch) -> None:
    monkeypatch.setattr(
        vg_overview,
        "collect_g8_subcheck",
        lambda *args, **kwargs: {
            "it_total": 21,
            "anchored": {"count": 21},
            "exec_pass": {"count": 21},
            "missing": {"count": 0},
            "unanchored_but_exists": {"count": 0},
            "clean": True,
        },
    )


def _stub_clean_g9_subcheck(monkeypatch) -> None:
    monkeypatch.setattr(
        vg_overview,
        "collect_g9_subcheck",
        lambda *args, **kwargs: {
            "implemented": True,
            "passed": False,
            "st_total": 18,
            "gap_count": 13,
            "anchored": {
                "count": 5,
                "ids": ["ST-IF-01", "ST-IF-02", "ST-IF-03", "ST-SYS-01", "ST-SYS-03"],
            },
            "exec_pass": {
                "count": 5,
                "ids": ["ST-IF-01", "ST-IF-02", "ST-IF-03", "ST-SYS-01", "ST-SYS-03"],
            },
            "missing": {"count": 13, "ids": [item for item in ST_IDS if item not in {"ST-IF-01", "ST-IF-02", "ST-IF-03", "ST-SYS-01", "ST-SYS-03"}]},
            "unanchored_but_exists": {"count": 0, "ids": [], "candidates": {}},
        },
    )


def test_collect_vg_overview_aggregates_required_clean_and_pair_status(monkeypatch, tmp_path: Path) -> None:
    _write_l2_waiver(tmp_path)
    _stub_clean_ddd_bc_checks(monkeypatch)
    _stub_clean_ratchet_gate_summaries(monkeypatch)
    _stub_clean_g8_subcheck(monkeypatch)
    _stub_clean_g9_subcheck(monkeypatch)
    monkeypatch.setattr(vg_overview, "check_registry_design_coverage", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_design_id_existence", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_fn_ut_pair_coverage", lambda *args, **kwargs: _report())
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
    assert vg["required_clean"]["design_id_existence"]["clean"] is True
    assert vg["required_clean"]["fn_ut_pair_coverage"]["clean"] is True
    assert vg["required_clean"]["coding_rule_lint"]["clean"] is True
    assert vg["required_clean"]["dependency_cycle_checks"]["clean"] is True
    assert vg["required_clean"]["plan_dependency_gate"]["clean"] is True
    assert vg["required_clean"]["fr_uses_checks"]["clean"] is True
    assert vg["required_clean"]["source_scan_vs_registry"]["clean"] is False
    assert vg["required_clean"]["requirement_drift"]["clean"] is True
    assert vg["required_clean"]["requirement_drift"]["finding_count"] == 0
    assert vg["required_clean"]["requirement_drift"]["focus"] == "L6"
    assert vg["full_flow_execution"]["enforced"] is False
    assert vg["full_flow_execution"]["clean"] is False
    assert vg["full_flow_execution"]["deferred_count"] == 3
    assert vg["full_flow_execution"]["deferred_pairs"][0]["gate_id"].startswith("G")
    assert "next_action" in vg["full_flow_execution"]["deferred_pairs"][0]
    assert vg["full_flow_execution"]["not_applicable_count"] == 1
    assert vg["full_flow_execution"]["not_applicable_pairs"][0]["pair"] == "L2-L10"
    assert vg["full_flow_execution"]["not_applicable_pairs"][0]["waiver"]["reason"] == "ui_absent"
    assert vg["pair_status"]["L6-L7"]["status"] == "applicable"
    assert vg["pair_status"]["L6-L7"]["clean"] is False
    assert vg["pair_status"]["L5-L8"]["status"] == "applicable"
    assert vg["pair_status"]["L5-L8"]["clean"] is True
    assert "anchored=21/21" in vg["pair_status"]["L5-L8"]["reason"]
    assert vg["pair_status"]["L4-L9"]["status"] == "approved_deferred"
    assert vg["pair_status"]["L4-L9"]["clean"] is True
    assert "g9_implemented=true" in vg["pair_status"]["L4-L9"]["reason"]
    assert "anchored=5/18" in vg["pair_status"]["L4-L9"]["reason"]
    assert "gap=13" in vg["pair_status"]["L4-L9"]["reason"]
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
    _stub_clean_ddd_bc_checks(monkeypatch)
    _stub_clean_ratchet_gate_summaries(monkeypatch)
    _stub_clean_g8_subcheck(monkeypatch)
    _stub_clean_g9_subcheck(monkeypatch)
    monkeypatch.setattr(vg_overview, "check_registry_design_coverage", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_design_id_existence", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_fn_ut_pair_coverage", lambda *args, **kwargs: _report())
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
    assert strict_vg["full_flow_execution"]["deferred_count"] == 3
    assert strict_vg["full_flow_execution"]["not_applicable_count"] == 1
    assert strict_vg["full_flow_execution"]["not_applicable_pairs"][0]["waiver"]["path"].endswith(
        "helix-workflows-ui-absent-waiver.md"
    )
    assert {item["pair"] for item in strict_vg["full_flow_execution"]["deferred_pairs"]} == {
        "L1-L14",
        "L3-L12",
        "L4-L9",
    }
    assert {item["pair"]: item["gate_id"] for item in strict_vg["full_flow_execution"]["deferred_pairs"]} == {
        "L1-L14": "G14",
        "L3-L12": "G12",
        "L4-L9": "G9",
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
    _stub_clean_ddd_bc_checks(monkeypatch)
    _stub_clean_ratchet_gate_summaries(monkeypatch)
    _stub_clean_g8_subcheck(monkeypatch)
    _stub_clean_g9_subcheck(monkeypatch)
    monkeypatch.setattr(vg_overview, "check_registry_design_coverage", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_design_id_existence", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_fn_ut_pair_coverage", lambda *args, **kwargs: _report())
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


def test_collect_vg_overview_keeps_overall_clean_when_ddd_bc_checks_are_clean(
    monkeypatch, tmp_path: Path
) -> None:
    _write_l2_waiver(tmp_path)
    _stub_clean_ddd_bc_checks(monkeypatch)
    _stub_clean_ratchet_gate_summaries(monkeypatch)
    _stub_clean_g8_subcheck(monkeypatch)
    _stub_clean_g9_subcheck(monkeypatch)
    monkeypatch.setattr(vg_overview, "check_registry_design_coverage", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_design_id_existence", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_fn_ut_pair_coverage", lambda *args, **kwargs: _report())
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

    report = vg_overview.collect_vg_overview(tmp_path)
    ddd_bc = report["vg_overview"]["required_clean"]["ddd_bc_coverage"]

    assert ddd_bc == {"clean": True, "finding_count": 0}
    assert report["vg_overview"]["overall_clean"] is True


def test_collect_vg_overview_treats_unavailable_ratchet_detectors_as_skipped_clean(
    monkeypatch, tmp_path: Path
) -> None:
    _write_l2_waiver(tmp_path)
    _stub_clean_ddd_bc_checks(monkeypatch)
    _stub_clean_g8_subcheck(monkeypatch)
    _stub_clean_g9_subcheck(monkeypatch)
    monkeypatch.setattr(vg_overview, "check_registry_design_coverage", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_design_id_existence", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_fn_ut_pair_coverage", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_functional_registry", lambda *args, **kwargs: _report())
    monkeypatch.setattr(
        vg_overview,
        "collect_coding_rule_lint_gate_summary",
        lambda *args, **kwargs: _gate_summary(
            clean=False,
            finding_count=0,
            source_status="unavailable",
            skipped_reason="changed-files unavailable",
        ),
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_dependency_cycle_gate_summary",
        lambda *args, **kwargs: _gate_summary(
            clean=False,
            finding_count=0,
            source_status="unavailable",
            skipped_reason="changed-files unavailable",
        ),
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_plan_dependency_gate_summary",
        lambda *args, **kwargs: _gate_summary(),
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_fr_uses_gate_summary",
        lambda *args, **kwargs: _gate_summary(clean=True, finding_count=3),
    )
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

    report = vg_overview.collect_vg_overview(tmp_path)
    required = report["vg_overview"]["required_clean"]

    assert required["coding_rule_lint"]["clean"] is True
    assert required["coding_rule_lint"]["source_status"] == "unavailable"
    assert required["coding_rule_lint"]["skipped_reason"] == "changed-files unavailable"
    assert required["dependency_cycle_checks"]["clean"] is True
    assert required["fr_uses_checks"]["clean"] is True
    assert required["fr_uses_checks"]["finding_count"] == 3
    assert report["vg_overview"]["overall_clean"] is True


def test_collect_vg_overview_uses_full_required_coding_rule_lint_summary(
    monkeypatch, tmp_path: Path
) -> None:
    """DoD 検証: C-3c required_clean.coding_rule_lint は core full-required source を使う。"""

    _write_l2_waiver(tmp_path)
    _stub_clean_ddd_bc_checks(monkeypatch)
    _stub_clean_g8_subcheck(monkeypatch)
    _stub_clean_g9_subcheck(monkeypatch)
    monkeypatch.setattr(vg_overview, "check_registry_design_coverage", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_design_id_existence", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_fn_ut_pair_coverage", lambda *args, **kwargs: _report())
    monkeypatch.setattr(
        vg_overview,
        "collect_coding_rule_lint_full_required_summary",
        lambda *args, **kwargs: {
            "clean": True,
            "finding_count": 0,
            "blocking_finding_count": 0,
            "warning_count": 0,
            "source_status": "full_required",
            "skipped_reason": None,
            "mode": "core_full_required",
        },
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_dependency_cycle_gate_summary",
        lambda *args, **kwargs: _gate_summary(),
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_plan_dependency_gate_summary",
        lambda *args, **kwargs: _gate_summary(),
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_fr_uses_full_required_summary",
        lambda *args, **kwargs: {
            "clean": True,
            "finding_count": 0,
            "blocking_finding_count": 0,
            "warning_count": 0,
            "source_status": "full_required",
            "skipped_reason": None,
            "mode": "full_required",
        },
    )
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

    report = vg_overview.collect_vg_overview(tmp_path)
    required = report["vg_overview"]["required_clean"]["coding_rule_lint"]

    assert required["clean"] is True
    assert required["finding_count"] == 0
    assert required["blocking_finding_count"] == 0
    assert required["warning_count"] == 0
    assert required["source_status"] == "full_required"
    assert required["mode"] == "core_full_required"
    assert report["vg_overview"]["overall_clean"] is True


def test_collect_vg_overview_uses_baseline_required_dependency_summaries(
    monkeypatch, tmp_path: Path
) -> None:
    """DoD 検証: C-3d/e required_clean は baseline-required source を使う。"""

    _write_l2_waiver(tmp_path)
    _stub_clean_ddd_bc_checks(monkeypatch)
    _stub_clean_g8_subcheck(monkeypatch)
    _stub_clean_g9_subcheck(monkeypatch)
    monkeypatch.setattr(vg_overview, "check_registry_design_coverage", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_design_id_existence", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_fn_ut_pair_coverage", lambda *args, **kwargs: _report())
    monkeypatch.setattr(
        vg_overview,
        "collect_coding_rule_lint_full_required_summary",
        lambda *args, **kwargs: {
            "clean": True,
            "finding_count": 0,
            "blocking_finding_count": 0,
            "warning_count": 0,
            "source_status": "full_required",
            "skipped_reason": None,
            "mode": "core_full_required",
        },
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_import_cycle_baseline_required_summary",
        lambda *args, **kwargs: {
            "clean": True,
            "finding_count": 5,
            "blocking_finding_count": 0,
            "warning_count": 5,
            "source_status": "baseline_required",
            "skipped_reason": None,
            "mode": "baseline_required",
        },
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_plan_dependency_baseline_required_summary",
        lambda *args, **kwargs: {
            "clean": True,
            "finding_count": 49,
            "blocking_finding_count": 0,
            "warning_count": 49,
            "source_status": "baseline_required",
            "skipped_reason": None,
            "mode": "baseline_required",
        },
    )
    monkeypatch.setattr(
        vg_overview,
        "collect_fr_uses_full_required_summary",
        lambda *args, **kwargs: {
            "clean": True,
            "finding_count": 0,
            "blocking_finding_count": 0,
            "warning_count": 0,
            "source_status": "full_required",
            "skipped_reason": None,
            "mode": "full_required",
        },
    )
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

    report = vg_overview.collect_vg_overview(tmp_path)
    required = report["vg_overview"]["required_clean"]

    assert required["dependency_cycle_checks"]["clean"] is True
    assert required["dependency_cycle_checks"]["source_status"] == "baseline_required"
    assert required["dependency_cycle_checks"]["mode"] == "baseline_required"
    assert required["plan_dependency_gate"]["clean"] is True
    assert required["plan_dependency_gate"]["source_status"] == "baseline_required"
    assert required["plan_dependency_gate"]["mode"] == "baseline_required"
    assert report["vg_overview"]["overall_clean"] is True


def test_collect_vg_overview_keeps_l5_l8_deferred_when_g8_execution_is_incomplete(
    monkeypatch, tmp_path: Path
) -> None:
    _write_l2_waiver(tmp_path)
    _stub_clean_ddd_bc_checks(monkeypatch)
    _stub_clean_ratchet_gate_summaries(monkeypatch)
    _stub_clean_g9_subcheck(monkeypatch)
    monkeypatch.setattr(vg_overview, "check_registry_design_coverage", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_design_id_existence", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_fn_ut_pair_coverage", lambda *args, **kwargs: _report())
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
    monkeypatch.setattr(
        vg_overview,
        "collect_g8_subcheck",
        lambda *args, **kwargs: {
            "it_total": 21,
            "anchored": {"count": 21},
            "exec_pass": {"count": 20},
            "missing": {"count": 0},
            "unanchored_but_exists": {"count": 0},
            "clean": False,
        },
    )

    report = vg_overview.collect_vg_overview(tmp_path, strict_full_flow=True)
    vg = report["vg_overview"]

    assert vg["pair_status"]["L5-L8"]["status"] == "approved_deferred"
    assert vg["pair_status"]["L5-L8"]["clean"] is True
    assert "exec_pass=20" in vg["pair_status"]["L5-L8"]["reason"]
    assert vg["full_flow_execution"]["deferred_count"] == 4
    assert {item["pair"]: item["gate_id"] for item in vg["full_flow_execution"]["deferred_pairs"]} == {
        "L5-L8": "G8",
        "L4-L9": "G9",
        "L3-L12": "G12",
        "L1-L14": "G14",
    }


def test_collect_vg_overview_reuses_g7_execute_flag_for_g8_when_not_overridden(
    monkeypatch, tmp_path: Path
) -> None:
    _write_l2_waiver(tmp_path)
    _stub_clean_ddd_bc_checks(monkeypatch)
    _stub_clean_ratchet_gate_summaries(monkeypatch)
    monkeypatch.setattr(vg_overview, "check_registry_design_coverage", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_design_id_existence", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_fn_ut_pair_coverage", lambda *args, **kwargs: _report())
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

    seen: dict[str, bool | None] = {}

    def _g7(*args, **kwargs):
        seen["g7"] = kwargs.get("execute_tests")
        return {
            "ut_total": 88,
            "anchored": {"count": 88},
            "exec_pass": {"count": 88},
            "missing": {"count": 0},
            "unanchored_but_exists": {"count": 0},
        }

    def _g8(*args, **kwargs):
        seen["g8"] = kwargs.get("execute_tests")
        return {
            "it_total": 21,
            "anchored": {"count": 21},
            "exec_pass": {"count": 21},
            "missing": {"count": 0},
            "unanchored_but_exists": {"count": 0},
            "clean": True,
        }

    def _g9(*args, **kwargs):
        seen["g9"] = kwargs.get("execute_g7_tests")
        return {
            "implemented": True,
            "passed": False,
            "st_total": 18,
            "gap_count": 13,
            "anchored": {
                "count": 5,
                "ids": ["ST-IF-01", "ST-IF-02", "ST-IF-03", "ST-SYS-01", "ST-SYS-03"],
            },
            "exec_pass": {
                "count": 5,
                "ids": ["ST-IF-01", "ST-IF-02", "ST-IF-03", "ST-SYS-01", "ST-SYS-03"],
            },
            "missing": {
                "count": 13,
                "ids": [
                    "ST-DATA-01",
                    "ST-DATA-02",
                    "ST-FR-01",
                    "ST-FR-02",
                    "ST-FR-03",
                    "ST-FR-04",
                    "ST-IF-04",
                    "ST-NEG-01",
                    "ST-NEG-02",
                    "ST-NFR-01",
                    "ST-NFR-02",
                    "ST-NFR-03",
                    "ST-SYS-02",
                ],
            },
            "unanchored_but_exists": {"count": 0, "ids": [], "candidates": {}},
        }

    monkeypatch.setattr(vg_overview, "collect_g7_subcheck", _g7)
    monkeypatch.setattr(vg_overview, "collect_g8_subcheck", _g8)
    monkeypatch.setattr(vg_overview, "collect_g9_subcheck", _g9)

    report = vg_overview.collect_vg_overview(tmp_path, strict_full_flow=True, execute_g7_tests=False)

    assert seen == {"g7": False, "g8": False, "g9": False}
    assert report["vg_overview"]["pair_status"]["L5-L8"]["status"] == "applicable"


def test_collect_vg_overview_marks_l4_l9_applicable_when_g9_closes(
    monkeypatch, tmp_path: Path
) -> None:
    _write_l2_waiver(tmp_path)
    _stub_clean_ddd_bc_checks(monkeypatch)
    _stub_clean_ratchet_gate_summaries(monkeypatch)
    _stub_clean_g8_subcheck(monkeypatch)
    monkeypatch.setattr(vg_overview, "check_registry_design_coverage", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_design_id_existence", lambda *args, **kwargs: _report())
    monkeypatch.setattr(vg_overview, "check_fn_ut_pair_coverage", lambda *args, **kwargs: _report())
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
                    "semantic_excluded_orphan": (
                        {
                            "count": 18,
                            "items": [
                                {"id": st_id, "reason": "semantic_gate ok"}
                                for st_id in ST_IDS
                            ],
                        }
                        if name == "L4-L9"
                        else {"count": 0, "items": []}
                    ),
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
        "collect_g9_subcheck",
        lambda *args, **kwargs: {
            "implemented": True,
            "passed": True,
            "st_total": 18,
            "gap_count": 0,
            "anchored": {"count": 18, "ids": list(ST_IDS)},
            "exec_pass": {"count": 18, "ids": list(ST_IDS)},
            "missing": {"count": 0, "ids": []},
            "unanchored_but_exists": {"count": 0, "ids": [], "candidates": {}},
        },
    )

    report = vg_overview.collect_vg_overview(tmp_path)

    assert report["vg_overview"]["pair_status"]["L4-L9"]["status"] == "applicable"
    assert "g9_passed=true" in report["vg_overview"]["pair_status"]["L4-L9"]["reason"]


def test_live_strict_deferred_pairs_sorts_gate_ids_and_skips_g7_exec(monkeypatch, tmp_path: Path) -> None:
    seen: dict[str, object] = {}

    def _collect(project_root, **kwargs):
        seen["project_root"] = project_root
        seen["kwargs"] = kwargs
        return {
            "vg_overview": {
                "full_flow_execution": {
                    "deferred_pairs": [
                        {"gate_id": "G14", "pair": "L1-L14"},
                        {"gate_id": "G9", "pair": "L4-L9"},
                        {"gate_id": "G12", "pair": "L3-L12"},
                    ]
                }
            }
        }

    monkeypatch.setattr(vg_overview, "collect_vg_overview", _collect)

    deferred_pairs = vg_overview.live_strict_deferred_pairs(tmp_path)

    assert seen == {
        "project_root": tmp_path.resolve(),
        "kwargs": {"strict_full_flow": True, "execute_g7_tests": False},
    }
    assert [item["gate_id"] for item in deferred_pairs] == ["G9", "G12", "G14"]
