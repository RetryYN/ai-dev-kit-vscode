"""registry 由来の L7 worklist checker."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from fn_ut_pair_coverage_checks import _expected_fn_for_ut
from g7_subcheck import load_anchor_map

WAIVER_KEY = "fn_ut_pair_waivers"


def _normalize_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    value = str(raw).strip()
    return [value] if value else []


def _resolve_path(path_like: str | Path, root: Path) -> Path:
    path = Path(path_like)
    return path if path.is_absolute() else root / path


def _expected_ut_for_fn(fn_id: str) -> str | None:
    if fn_id.startswith("FN-RD-"):
        return f"RD-UT-{fn_id.removeprefix('FN-RD-')}"
    if fn_id.startswith("FN-"):
        return f"UT-{fn_id.removeprefix('FN-')}"
    return None


def _load_waivers(payload: dict[str, Any]) -> dict[tuple[str, str], dict[str, str]]:
    raw_waivers = payload.get(WAIVER_KEY) or []
    if not isinstance(raw_waivers, list):
        return {}

    waivers: dict[tuple[str, str], dict[str, str]] = {}
    for item in raw_waivers:
        if not isinstance(item, dict):
            continue
        fn_id = str(item.get("fn") or "").strip()
        ut_id = str(item.get("ut") or "").strip()
        reason = str(item.get("reason") or "").strip()
        owner = str(item.get("owner") or "").strip()
        if fn_id and ut_id and reason and owner:
            waivers[(fn_id, ut_id)] = {
                "fn": fn_id,
                "ut": ut_id,
                "reason": reason,
                "owner": owner,
            }
    return waivers


def _pick_ut_for_fn(fn_id: str, test_design_ids: list[str]) -> str | None:
    for ut_id in test_design_ids:
        if _expected_fn_for_ut(ut_id) == fn_id:
            return ut_id
    return _expected_ut_for_fn(fn_id)


def collect_l7_worklist(
    registry_path: str | Path,
    anchor_map_path: str | Path,
    root: str | Path,
) -> dict[str, Any]:
    root_path = Path(root).resolve()
    registry = _resolve_path(registry_path, root_path)
    anchor_map = _resolve_path(anchor_map_path, root_path)
    payload = yaml.safe_load(registry.read_text(encoding="utf-8")) or {}
    entries = payload.get("entries", [])
    waivers = _load_waivers(payload)
    anchored_tests = set(load_anchor_map(anchor_map))

    worklist: list[dict[str, Any]] = []
    for entry in entries:
        if entry.get("status") != "active" or entry.get("coverage_layer") != "L6_required":
            continue
        entry_id = str(entry.get("id", "?"))
        code_paths = _normalize_list(entry.get("code_paths"))
        test_design_ids = _normalize_list(entry.get("test_design_ids"))
        for fn_id in _normalize_list(entry.get("design_ids")):
            if not fn_id.startswith("FN-"):
                continue
            ut_id = _pick_ut_for_fn(fn_id, test_design_ids)
            status = "missing_ut"
            item: dict[str, Any] = {
                "entry_id": entry_id,
                "fn": fn_id,
                "ut": ut_id,
                "status": status,
                "code_path": code_paths[0] if code_paths else "",
            }
            if ut_id is not None and ut_id.startswith("RD-UT-"):
                item["status"] = "separate_inventory"
            elif ut_id is not None and (fn_id, ut_id) in waivers:
                waiver = waivers[(fn_id, ut_id)]
                item["status"] = "waived"
                item["waiver_reason"] = waiver["reason"]
                item["waiver_owner"] = waiver["owner"]
            elif ut_id is not None and ut_id in anchored_tests:
                item["status"] = "ut_anchored"
            worklist.append(item)

    worklist.sort(key=lambda item: item["fn"])
    summary = {
        "total": len(worklist),
        "anchored": sum(1 for item in worklist if item["status"] == "ut_anchored"),
        "waived": sum(1 for item in worklist if item["status"] == "waived"),
        "separate_inventory": sum(1 for item in worklist if item["status"] == "separate_inventory"),
        "missing": sum(1 for item in worklist if item["status"] == "missing_ut"),
    }
    return {
        "advisory": True,
        "exit_code": 0,
        "summary": summary,
        "worklist": worklist,
    }


def summary_counts(report: dict[str, Any]) -> dict[str, int]:
    summary = report.get("summary") or {}
    return {
        "total": int(summary.get("total", 0)),
        "anchored": int(summary.get("anchored", 0)),
        "waived": int(summary.get("waived", 0)),
        "separate_inventory": int(summary.get("separate_inventory", 0)),
        "missing_ut": int(summary.get("missing", 0)),
    }


def render_text(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "L7 worklist (advisory)",
        "summary: "
        f"total={summary['total']} anchored={summary['anchored']} "
        f"waived={summary['waived']} separate_inventory={summary['separate_inventory']} "
        f"missing={summary['missing']}",
    ]
    for item in report["worklist"]:
        detail = f"{item['fn']} -> {item.get('ut') or '<missing>'} [{item['status']}]"
        if item.get("code_path"):
            detail += f" {item['code_path']}"
        lines.append(detail)
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry-path", default="cli/config/functional-registry.yaml")
    ap.add_argument("--anchor-map-path", default="docs/v2/L7-test-design/g7-test-anchor-map.yaml")
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    report = collect_l7_worklist(args.registry_path, args.anchor_map_path, args.root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
