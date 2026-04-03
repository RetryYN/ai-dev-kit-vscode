#!/usr/bin/env python3
"""HELIX deliverable gate checker."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

GATE_LAYERS = {
    "G2": ["L1", "L2"],
    "G3": ["L1", "L2", "L3"],
    "G4": ["L1", "L2", "L3", "L4"],
    "G5": ["L5"],
    "G6": ["L1", "L2", "L3", "L4", "L5", "L6"],
    "G7": ["L1", "L2", "L3", "L4", "L5", "L6", "L7"],
}

PASS_STATUSES = {"done", "waived", "not_applicable"}


class DeliverableGateError(Exception):
    """ユーザー向けエラー。"""


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise DeliverableGateError(f"ファイルが見つかりません: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DeliverableGateError(f"JSON が不正です: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise DeliverableGateError(f"トップレベルがオブジェクトではありません: {path}")
    return payload


def _status_from_state(entry: Any) -> str:
    if isinstance(entry, dict):
        raw = entry.get("status", "pending")
        return str(raw).strip() or "pending"
    if isinstance(entry, str):
        return entry.strip() or "pending"
    return "pending"


def _collect_waivers(index_payload: dict[str, Any]) -> set[tuple[str, str]]:
    waivers_raw = index_payload.get("waivers", [])
    if not isinstance(waivers_raw, list):
        return set()

    waivers: set[tuple[str, str]] = set()
    for item in waivers_raw:
        if not isinstance(item, dict):
            continue
        feature_id = item.get("feature_id")
        deliverable_id = item.get("deliverable_id")
        if isinstance(feature_id, str) and isinstance(deliverable_id, str):
            waivers.add((feature_id, deliverable_id))
    return waivers


def _is_pass(status: str) -> bool:
    return status in PASS_STATUSES


def _catalog_ids(index_payload: dict[str, Any]) -> set[str]:
    rules = index_payload.get("rules", {})
    if not isinstance(rules, dict):
        return set()

    deliverables = rules.get("deliverables", [])
    if not isinstance(deliverables, list):
        return set()

    ids: set[str] = set()
    for item in deliverables:
        if not isinstance(item, dict):
            continue
        did = item.get("id")
        if isinstance(did, str):
            ids.add(did)
    return ids


def _validate_fullstack_requirements(index_payload: dict[str, Any]) -> None:
    catalog_ids = _catalog_ids(index_payload)
    if catalog_ids and "D-CONTRACT" not in catalog_ids:
        raise DeliverableGateError("deliverables catalog に D-CONTRACT がありません")

    features = index_payload.get("features", {})
    if not isinstance(features, dict):
        return

    errors: list[str] = []
    for feature_id, feature_raw in features.items():
        if not isinstance(feature_raw, dict):
            continue
        if str(feature_raw.get("drive", "")).strip().lower() != "fullstack":
            continue
        requires = feature_raw.get("requires", {})
        if not isinstance(requires, dict):
            errors.append(f"{feature_id}: requires が不正です")
            continue
        l3_raw = requires.get("L3", [])
        l3 = {x for x in l3_raw if isinstance(x, str)} if isinstance(l3_raw, list) else set()
        missing = [did for did in ("D-CONTRACT", "D-STATE") if did not in l3]
        if missing:
            errors.append(f"{feature_id}: L3 に不足 {', '.join(missing)}")

    if errors:
        raise DeliverableGateError("fullstack 成果物定義エラー: " + "; ".join(errors))


def evaluate_gate(
    index_payload: dict[str, Any],
    state_payload: dict[str, Any],
    gate: str,
) -> dict[str, Any]:
    if gate not in GATE_LAYERS:
        raise DeliverableGateError(f"サポート外の gate です: {gate}")

    features = index_payload.get("features", {})
    if not isinstance(features, dict):
        raise DeliverableGateError("index.json の features が辞書ではありません")

    _validate_fullstack_requirements(index_payload)

    state_features = state_payload.get("features", {})
    if not isinstance(state_features, dict):
        state_features = {}

    layers = GATE_LAYERS[gate]
    waivers = _collect_waivers(index_payload)

    summary = {
        "total": 0,
        "pass": 0,
        "fail": 0,
        "done": 0,
        "waived": 0,
        "not_applicable": 0,
        "pending": 0,
        "in_progress": 0,
        "partial": 0,
        "unknown": 0,
    }

    result_features: dict[str, Any] = {}
    overall_pass = True

    for feature_id in sorted(features.keys()):
        feature_raw = features.get(feature_id)
        feature = feature_raw if isinstance(feature_raw, dict) else {}
        requires = feature.get("requires", {})
        if not isinstance(requires, dict):
            requires = {}

        feature_state_raw = state_features.get(feature_id, {})
        feature_state = feature_state_raw if isinstance(feature_state_raw, dict) else {}
        deliverables_state = feature_state.get("deliverables", {})
        if not isinstance(deliverables_state, dict):
            deliverables_state = {}

        ui_required = bool(feature.get("ui", False))
        is_ui_skip = gate == "G5" and not ui_required

        feature_pass = True
        layer_results: dict[str, Any] = {}

        for layer in layers:
            deliverable_ids_raw = requires.get(layer, [])
            deliverable_ids = [x for x in deliverable_ids_raw if isinstance(x, str)] if isinstance(deliverable_ids_raw, list) else []

            deliverable_results: list[dict[str, Any]] = []
            layer_pass = True

            for did in deliverable_ids:
                if is_ui_skip:
                    status = "not_applicable"
                else:
                    status = _status_from_state(deliverables_state.get(did))
                    if (feature_id, did) in waivers and status not in {"waived", "not_applicable", "done"}:
                        status = "waived"

                passed = _is_pass(status)
                if not passed:
                    layer_pass = False
                    feature_pass = False
                    overall_pass = False

                summary["total"] += 1
                if passed:
                    summary["pass"] += 1
                else:
                    summary["fail"] += 1

                if status in summary:
                    summary[status] += 1
                else:
                    summary["unknown"] += 1

                deliverable_results.append(
                    {
                        "id": did,
                        "status": status,
                        "result": "pass" if passed else "fail",
                    }
                )

            layer_results[layer] = {
                "result": "pass" if layer_pass else "fail",
                "deliverables": deliverable_results,
                "ui_skipped": bool(is_ui_skip),
            }

        result_features[feature_id] = {
            "result": "pass" if feature_pass else "fail",
            "ui_required": ui_required,
            "layers": layer_results,
        }

    return {
        "gate": gate,
        "layers": layers,
        "result": "pass" if overall_pass else "fail",
        "features": result_features,
        "summary": summary,
    }


def _format_summary(result: dict[str, Any]) -> str:
    summary = result.get("summary", {}) if isinstance(result, dict) else {}
    total = int(summary.get("total", 0))
    done = int(summary.get("done", 0))
    waived = int(summary.get("waived", 0))
    not_applicable = int(summary.get("not_applicable", 0))
    pending = int(summary.get("pending", 0))
    in_progress = int(summary.get("in_progress", 0))
    partial = int(summary.get("partial", 0))
    unknown = int(summary.get("unknown", 0))
    gate_result = str(result.get("result", "fail")).upper()

    parts = [f"deliverable: {done}/{total} done"]
    if waived:
        parts.append(f"{waived} waived")
    if not_applicable:
        parts.append(f"{not_applicable} not_applicable")
    if pending:
        parts.append(f"{pending} pending")
    if in_progress:
        parts.append(f"{in_progress} in_progress")
    if partial:
        parts.append(f"{partial} partial")
    if unknown:
        parts.append(f"{unknown} unknown")
    return ", ".join(parts) + f" -> {gate_result}"


def print_text_result(result: dict[str, Any]) -> None:
    layers = result.get("layers", [])
    if not isinstance(layers, list):
        layers = []
    features = result.get("features", {})
    if not isinstance(features, dict):
        features = {}

    for feature_id in sorted(features.keys()):
        feature_raw = features.get(feature_id)
        feature = feature_raw if isinstance(feature_raw, dict) else {}
        print(f"feature: {feature_id}")
        layer_map = feature.get("layers", {}) if isinstance(feature.get("layers"), dict) else {}

        for layer in layers:
            layer_raw = layer_map.get(layer, {})
            layer_result = layer_raw if isinstance(layer_raw, dict) else {}
            deliverables = layer_result.get("deliverables", [])
            if not isinstance(deliverables, list):
                deliverables = []

            token_list: list[str] = []
            for item in deliverables:
                if not isinstance(item, dict):
                    continue
                did = str(item.get("id", "?"))
                status = str(item.get("status", "pending"))
                token_list.append(f"{did}({status})")

            if not token_list:
                if bool(layer_result.get("ui_skipped")):
                    token_list = ["(ui=false, skip)"]
                else:
                    token_list = ["(none)"]

            mark = "OK" if str(layer_result.get("result", "fail")) == "pass" else "NG"
            print(f"  {layer}: {' '.join(token_list)} {mark}")

    print("---")
    print(_format_summary(result))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HELIX deliverable gate checker")
    parser.add_argument("--index", required=True, help="path to .helix/runtime/index.json")
    parser.add_argument("--state", required=True, help="path to .helix/state/deliverables.json")
    parser.add_argument("--gate", required=True, choices=sorted(GATE_LAYERS.keys()), help="gate name")
    parser.add_argument("--json", action="store_true", help="JSON を出力する")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        index_payload = _load_json(Path(args.index))
        state_payload = _load_json(Path(args.state))
        result = evaluate_gate(index_payload=index_payload, state_payload=state_payload, gate=args.gate)
    except DeliverableGateError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    else:
        print_text_result(result)
    return 0 if result.get("result") == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
