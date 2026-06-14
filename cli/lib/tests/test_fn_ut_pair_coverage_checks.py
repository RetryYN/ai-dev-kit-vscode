"""fn_ut_pair_coverage detector の単体テスト."""

import sys
from pathlib import Path

import yaml


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from fn_ut_pair_coverage_checks import check_fn_ut_pair_coverage  # noqa: E402


def _write_registry(tmp_path: Path, entries: list[dict], waivers: list[dict] | None = None) -> Path:
    payload = {"entries": entries}
    if waivers is not None:
        payload["fn_ut_pair_waivers"] = waivers
    path = tmp_path / "cli/config/functional-registry.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def _write_anchor_map(tmp_path: Path, anchors: dict[str, list[str]]) -> Path:
    path = tmp_path / "docs/v2/L7-test-design/g7-test-anchor-map.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"anchors": anchors}, allow_unicode=True, sort_keys=True), encoding="utf-8")
    return path


def _write_l7_test_design_doc(tmp_path: Path, rows: list[str]) -> Path:
    path = tmp_path / "docs/v2/L7-test-design/test-design.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# L7 Test Design",
                "",
                "| UT-ID | Summary | Module |",
                "| --- | --- | --- |",
                *rows,
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _l6_entry(entry_id: str, design_ids: list[str], test_design_ids: list[str] | None = None) -> dict:
    entry = {
        "id": entry_id,
        "name": entry_id.lower(),
        "domain": "lib",
        "status": "active",
        "coverage_layer": "L6_required",
        "design_ids": design_ids,
        "code_paths": [f"cli/lib/{entry_id.lower()}.py"],
        "doc_paths": [],
    }
    if test_design_ids is not None:
        entry["test_design_ids"] = test_design_ids
    return entry


def _kinds(report) -> set[str]:
    return {finding.kind for finding in report.findings}


def test_missing_test_design_is_reported(tmp_path: Path) -> None:
    registry_path = _write_registry(tmp_path, [_l6_entry("FR-A", ["FN-WSC-101"])])
    anchor_map_path = _write_anchor_map(tmp_path, {"UT-WSC-101": ["cli/lib/tests/test_alpha.py"]})

    report = check_fn_ut_pair_coverage(registry_path, anchor_map_path, tmp_path)

    assert "missing_test_design" in _kinds(report)


def test_unanchored_ut_is_reported_except_requirement_drift_inventory(tmp_path: Path) -> None:
    registry_path = _write_registry(
        tmp_path,
        [
            _l6_entry("FR-A", ["FN-WSC-101"], ["UT-WSC-101"]),
            _l6_entry("FR-B", ["FN-RD-01"], ["RD-UT-01"]),
        ],
    )
    anchor_map_path = _write_anchor_map(tmp_path, {})

    report = check_fn_ut_pair_coverage(registry_path, anchor_map_path, tmp_path)

    assert "unanchored_ut" in _kinds(report)
    assert not any("RD-UT-01" in finding.message for finding in report.findings)


def test_ut_missing_from_l7_test_design_inventory_is_reported_except_requirement_drift_inventory(
    tmp_path: Path,
) -> None:
    registry_path = _write_registry(
        tmp_path,
        [
            _l6_entry("FR-A", ["FN-WSC-101"], ["UT-WSC-101"]),
            _l6_entry("FR-B", ["FN-RD-01"], ["RD-UT-01"]),
        ],
    )
    anchor_map_path = _write_anchor_map(
        tmp_path,
        {
            "UT-WSC-101": ["cli/lib/tests/test_alpha.py"],
            "RD-UT-01": ["cli/lib/tests/test_requirement_drift.py"],
        },
    )
    _write_l7_test_design_doc(tmp_path, [])

    report = check_fn_ut_pair_coverage(registry_path, anchor_map_path, tmp_path)

    assert "ut_not_in_l7_design" in _kinds(report)
    assert not any("RD-UT-01" in finding.message for finding in report.findings)


def test_orphan_ut_is_reported(tmp_path: Path) -> None:
    registry_path = _write_registry(tmp_path, [_l6_entry("FR-A", ["FN-WSC-101"], ["UT-WSC-101"])])
    anchor_map_path = _write_anchor_map(
        tmp_path,
        {
            "UT-WSC-101": ["cli/lib/tests/test_alpha.py"],
            "UT-ROUTE-01": ["cli/lib/tests/test_route_engine.py"],
        },
    )

    report = check_fn_ut_pair_coverage(registry_path, anchor_map_path, tmp_path)

    assert "orphan_ut" in _kinds(report)


def test_duplicate_test_design_is_reported(tmp_path: Path) -> None:
    registry_path = _write_registry(
        tmp_path,
        [
            _l6_entry("FR-A", ["FN-WSC-101"], ["UT-WSC-101"]),
            _l6_entry("FR-B", ["FN-WSC-102"], ["UT-WSC-101"]),
        ],
    )
    anchor_map_path = _write_anchor_map(tmp_path, {"UT-WSC-101": ["cli/lib/tests/test_alpha.py"]})

    report = check_fn_ut_pair_coverage(registry_path, anchor_map_path, tmp_path)

    assert "duplicate_test_design" in _kinds(report)


def test_approved_deferred_waiver_suppresses_gap_findings(tmp_path: Path) -> None:
    registry_path = _write_registry(
        tmp_path,
        [_l6_entry("FR-A", ["FN-WSC-219"])],
        waivers=[
            {
                "fn": "FN-WSC-219",
                "ut": "UT-WSC-219",
                "reason": "L7 UT 実装 deferred",
                "owner": "TL",
            }
        ],
    )
    anchor_map_path = _write_anchor_map(tmp_path, {})

    report = check_fn_ut_pair_coverage(registry_path, anchor_map_path, tmp_path)

    assert report.findings == []
