"""registry_design_coverage detector の単体テスト (zero-omission B' 機械証明)."""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from registry_design_coverage_checks import check_registry_design_coverage  # noqa: E402


def _write(tmp_path, entries):
    p = tmp_path / "freg.yaml"
    p.write_text(yaml.safe_dump({"entries": entries}, allow_unicode=True), encoding="utf-8")
    return str(p)


def _kinds(rep):
    return {f.kind for f in rep.findings}


def test_clean_registry_no_findings(tmp_path):
    entries = [
        {"id": "FR-A", "name": "a", "domain": "lib", "status": "active",
         "coverage_layer": "L4_required", "design_ids": ["DSN-CMD-FAMILY"]},
        {"id": "FR-B", "name": "b", "domain": "skill", "status": "active",
         "coverage_layer": "excluded_with_reason", "design_ids": ["EXCL-SKILL-REFDOC"],
         "excluded_reason": "reference_doc"},
    ]
    rep = check_registry_design_coverage(_write(tmp_path, entries), ".")
    assert rep.findings == []
    assert rep.metrics["unknown_coverage_layer"] == 0


def test_unknown_coverage_layer(tmp_path):
    entries = [{"id": "FR-X", "name": "x", "domain": "lib", "status": "active"}]
    rep = check_registry_design_coverage(_write(tmp_path, entries), ".")
    assert "unknown_coverage_layer" in _kinds(rep)
    assert rep.metrics["unknown_coverage_layer"] == 1


def test_invalid_coverage_layer_value(tmp_path):
    entries = [{"id": "FR-X", "name": "x", "domain": "lib", "status": "active",
                "coverage_layer": "L99_bogus", "design_ids": ["DSN-LIB-MODULE"]}]
    rep = check_registry_design_coverage(_write(tmp_path, entries), ".")
    assert "unknown_coverage_layer" in _kinds(rep)


def test_design_id_missing_for_l4(tmp_path):
    entries = [{"id": "FR-X", "name": "x", "domain": "cli", "status": "active",
                "coverage_layer": "L4_required", "design_ids": []}]
    rep = check_registry_design_coverage(_write(tmp_path, entries), ".")
    assert "design_id_missing" in _kinds(rep)


def test_l6_empty_design_ids_is_pending_not_missing(tmp_path):
    entries = [{"id": "FR-X", "name": "x", "domain": "lib", "status": "active",
                "coverage_layer": "L6_required", "design_ids": []}]
    rep = check_registry_design_coverage(_write(tmp_path, entries), ".")
    assert "l6_design_pending" in _kinds(rep)
    assert "design_id_missing" not in _kinds(rep)


def test_excluded_reason_invalid(tmp_path):
    entries = [{"id": "FR-X", "name": "x", "domain": "skill", "status": "active",
                "coverage_layer": "excluded_with_reason", "design_ids": ["EXCL-OTHER"],
                "excluded_reason": "bogus"}]
    rep = check_registry_design_coverage(_write(tmp_path, entries), ".")
    assert "excluded_reason_invalid" in _kinds(rep)


def test_design_id_unresolved(tmp_path):
    entries = [{"id": "FR-X", "name": "x", "domain": "lib", "status": "active",
                "coverage_layer": "L5_required", "design_ids": ["NOPE-123"]}]
    rep = check_registry_design_coverage(_write(tmp_path, entries), ".")
    assert "design_id_unresolved" in _kinds(rep)


def test_wrong_layer_prefix(tmp_path):
    # L6_required に L4 anchor を付けると wrong_layer
    entries = [{"id": "FR-X", "name": "x", "domain": "lib", "status": "active",
                "coverage_layer": "L6_required", "design_ids": ["DSN-CMD-FAMILY"]}]
    rep = check_registry_design_coverage(_write(tmp_path, entries), ".")
    assert "wrong_layer" in _kinds(rep)


def test_l6_with_fn_is_clean(tmp_path):
    entries = [{"id": "FR-X", "name": "x", "domain": "lib", "status": "active",
                "coverage_layer": "L6_required", "design_ids": ["FN-GUARD-01"]}]
    rep = check_registry_design_coverage(_write(tmp_path, entries), ".")
    assert rep.findings == []


def test_inactive_entries_skipped(tmp_path):
    entries = [{"id": "FR-X", "name": "x", "domain": "lib", "status": "deprecated"}]
    rep = check_registry_design_coverage(_write(tmp_path, entries), ".")
    assert rep.findings == []
    assert rep.metrics["active_entries"] == 0
