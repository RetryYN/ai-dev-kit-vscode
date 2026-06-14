"""L7 worklist checker の単体テスト."""

import json
import sys
from pathlib import Path

import yaml


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from l7_worklist import collect_l7_worklist  # noqa: E402


def _write_registry(
    tmp_path: Path,
    entries: list[dict],
    waivers: list[dict] | None = None,
) -> Path:
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


def _entry(entry_id: str, fn_id: str, ut_id: str) -> dict:
    return {
        "id": entry_id,
        "name": entry_id.lower(),
        "domain": "lib",
        "status": "active",
        "coverage_layer": "L6_required",
        "design_ids": [fn_id],
        "test_design_ids": [ut_id],
        "code_paths": [f"cli/lib/{entry_id.lower()}.py"],
        "doc_paths": [],
    }


def test_collect_l7_worklist_classifies_anchor_waiver_and_missing(tmp_path: Path) -> None:
    registry_path = _write_registry(
        tmp_path,
        [
            _entry("FR-A", "FN-WSC-221", "UT-WSC-221"),
            _entry("FR-B", "FN-WSC-222", "UT-WSC-222"),
            _entry("FR-C", "FN-WSC-223", "UT-WSC-223"),
        ],
        waivers=[
            {
                "fn": "FN-WSC-222",
                "ut": "UT-WSC-222",
                "reason": "L7 UT 実装 deferred",
                "owner": "TL",
            }
        ],
    )
    anchor_map_path = _write_anchor_map(
        tmp_path,
        {"UT-WSC-221": ["cli/lib/tests/test_fn_ut_pair_coverage_checks.py"]},
    )

    report = collect_l7_worklist(registry_path, anchor_map_path, tmp_path)

    statuses = {item["fn"]: item["status"] for item in report["worklist"]}
    assert statuses == {
        "FN-WSC-221": "ut_anchored",
        "FN-WSC-222": "waived",
        "FN-WSC-223": "missing_ut",
    }
    assert report["summary"] == {
        "total": 3,
        "anchored": 1,
        "waived": 1,
        "separate_inventory": 0,
        "missing": 1,
    }
    json.dumps(report, ensure_ascii=False)


def test_collect_l7_worklist_treats_requirement_drift_inventory_as_separate(tmp_path: Path) -> None:
    registry_path = _write_registry(
        tmp_path,
        [
            _entry("FR-A", "FN-RD-01", "RD-UT-01"),
            _entry("FR-B", "FN-WSC-223", "UT-WSC-223"),
        ],
    )
    anchor_map_path = _write_anchor_map(tmp_path, {})

    report = collect_l7_worklist(registry_path, anchor_map_path, tmp_path)

    statuses = {item["fn"]: item["status"] for item in report["worklist"]}
    assert statuses == {
        "FN-RD-01": "separate_inventory",
        "FN-WSC-223": "missing_ut",
    }
    assert report["summary"] == {
        "total": 2,
        "anchored": 0,
        "waived": 0,
        "separate_inventory": 1,
        "missing": 1,
    }
