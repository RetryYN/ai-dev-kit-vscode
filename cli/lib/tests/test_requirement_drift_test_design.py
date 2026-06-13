from __future__ import annotations

import re
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_DESIGN = REPO_ROOT / "docs/v2/L7-test-design/requirement-drift-単体テスト設計.md"
PROCESS_PLAN = REPO_ROOT / "docs/plans/process/process-2026-06-08-verification-forward-gate.md"


def _read_design() -> tuple[dict[str, object], str]:
    text = TEST_DESIGN.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    _, frontmatter_text, body = text.split("---", 2)
    return yaml.safe_load(frontmatter_text) or {}, body


def test_requirement_drift_test_design_frontmatter_matches_current_state() -> None:
    frontmatter, _body = _read_design()

    assert frontmatter["doc_id"] == "L7-TEST-DESIGN-REQUIREMENT-DRIFT"
    assert frontmatter["layer"] == "L7"
    assert frontmatter["pairs_design"] == "docs/v2/L6-functional-design/requirement-drift-機能設計.md"
    assert frontmatter["pairs_with"] == "L6-functional-design"

    implementation_path = REPO_ROOT / "cli/lib/requirement_drift.py"
    if implementation_path.exists():
        assert frontmatter["implementation_status"] != "not-implemented"
    else:
        assert frontmatter["implementation_status"] == "not-implemented"


def test_requirement_drift_test_design_keeps_output_contract_keys() -> None:
    _frontmatter, body = _read_design()

    for key in (
        "missing_downstream",
        "orphan_design",
        "orphan_code",
        "semantic_label_mismatch",
        "stale_freeze",
        "waived_with_reason",
    ):
        assert f"{key}:" in body

    for summary_key in ("requirements", "design_links", "code_links", "test_links"):
        assert f"{summary_key}:" in body
    assert "focus:" in body
    assert "scope: L1_FR -> L3_FR -> L4-L6_design" in body


def test_requirement_drift_test_design_declares_all_mvp_planned_unit_tests() -> None:
    _frontmatter, body = _read_design()

    test_ids = sorted(set(re.findall(r"\bRD-UT-\d{2}\b", body)))
    assert test_ids == [f"RD-UT-{index:02d}" for index in range(1, 18)]
    assert "| UT-" not in body
    assert "G7 UT inventory へ混入させない" in body
    assert "L6 focus ignores code/test" in body
    assert "L7 focus counts code/test" in body
    assert "L1 parent to L3 child trace" in body
    assert "placeholder FR ignored" in body
    assert "generic downstream label ignored" in body
    assert "stale check opt-in" in body

    for finding_name in (
        "missing downstream design",
        "orphan design",
        "orphan code",
        "semantic label mismatch",
        "stale freeze opt-in",
        "waiver requires reason",
        "waiver with reason",
    ):
        assert finding_name in body


def test_requirement_drift_test_design_declares_cli_gate_acceptance() -> None:
    _frontmatter, body = _read_design()

    assert "collect_requirement_drift(project_root)" in body
    assert "python3 -m cli.lib.requirement_drift --json" in body
    assert "helix doctor check_requirement_drift --json" in body
    assert "--focus L7" in body
    assert "G-vg-overview" in body
    assert "required_clean.requirement_drift" in body


def test_forward_gate_process_tracks_requirement_drift_test_design() -> None:
    plan_text = PROCESS_PLAN.read_text(encoding="utf-8")

    assert "docs/v2/L7-test-design/requirement-drift-単体テスト設計.md" in plan_text
    assert "cli/lib/requirement_drift.py" in plan_text
    assert "requirement_drift MVP 実装" in plan_text
