from __future__ import annotations

from cli.lib.v3.detectors.core import (
    CORE_DETECTORS,
    DbProjectionCoverageInput,
    LintWiringInput,
    SchemaSsotInput,
    analyze_db_projection_coverage,
    analyze_lint_wiring,
    analyze_schema_ssot,
    load_lint_wiring_input,
)


def test_fn_det_11_empty_key_table_is_violation():
    inp = DbProjectionCoverageInput(
        table_counts=(("plan_registry", 5), ("artifact_registry", 0), ("test_cases", 0))
    )
    res = analyze_db_projection_coverage(inp)
    assert res.ok is False
    assert res.empty_tables == ("artifact_registry", "test_cases")


def test_fn_det_11_all_populated_ok():
    inp = DbProjectionCoverageInput(
        table_counts=(("plan_registry", 5), ("artifact_registry", 3))
    )
    res = analyze_db_projection_coverage(inp)
    assert res.ok is True
    assert res.empty_tables == ()


def test_fn_det_12_clean_schema_ok():
    inp = SchemaSsotInput(db_tables=frozenset({"a", "b"}), registry_tables=frozenset({"a", "b"}))
    assert analyze_schema_ssot(inp).ok is True


def test_fn_det_12_rogue_table_fails():
    inp = SchemaSsotInput(db_tables=frozenset({"a", "rogue"}), registry_tables=frozenset({"a", "b"}))
    res = analyze_schema_ssot(inp)
    assert res.ok is False
    assert res.rogue_tables == ("rogue",)
    assert res.missing_tables == ("b",)


def test_fn_det_12_empty_db_is_absence():
    # absence=ok=false: 全 registry table が DB 未作成
    inp = SchemaSsotInput(db_tables=frozenset(), registry_tables=frozenset({"a", "b"}))
    res = analyze_schema_ssot(inp)
    assert res.ok is False
    assert res.missing_tables == ("a", "b")


def test_fn_det_10_real_registry_is_healthy():
    # 実 CORE_DETECTORS registry は形式健全(重複なし/有効 source_kind/severity)
    import sqlite3

    res = analyze_lint_wiring(load_lint_wiring_input(sqlite3.connect(":memory:")))
    assert res.ok is True
    assert res.duplicate_ids == ()
    assert res.invalid_source_kinds == ()
    assert len(CORE_DETECTORS) >= 6


def test_fn_det_10_detects_duplicate_and_invalid():
    inp = LintWiringInput(
        detector_ids=("A", "A", "B"),
        source_kinds=("db_projection", "bogus", "db_projection"),
        severities=("hard", "hard", "weird"),
    )
    res = analyze_lint_wiring(inp)
    assert res.ok is False
    assert res.duplicate_ids == ("A",)
    assert res.invalid_source_kinds == ("bogus",)
    assert res.invalid_severities == ("weird",)


def test_fn_det_10_empty_registry_is_absence():
    res = analyze_lint_wiring(LintWiringInput(detector_ids=(), source_kinds=(), severities=()))
    assert res.ok is False
