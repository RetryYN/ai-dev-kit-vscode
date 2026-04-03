#!/usr/bin/env python3
"""HELIX deliverable gate checker.

責務:
  - gate ごとに必要 deliverable の状態を評価し pass/fail を判定する
  - runtime index を使って空成果物（10 バイト未満）を検知し警告する
"""

from __future__ import annotations

import argparse
import glob
import json
import re
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
MIN_ARTIFACT_BYTES = 10


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


def _contains_glob(path: str) -> bool:
    return any(ch in path for ch in ("*", "?", "["))


def _format_template(template: str, values: dict[str, Any]) -> str:
    def repl(match: re.Match[str]) -> str:
        return str(values.get(match.group(1), match.group(0)))

    return re.sub(r"{([a-zA-Z0-9_]+)}", repl, template)


def _resolve_scope_roots(
    feature_id: str,
    feature: dict[str, Any],
    rules: dict[str, Any],
) -> tuple[str, str]:
    roots = rules.get("roots", {})
    roots = roots if isinstance(roots, dict) else {}
    docs_root = str(roots.get("docs_root", "docs"))
    src_root = str(roots.get("src_root", "src"))

    scope = str(feature.get("scope", "feature"))
    scope_templates = rules.get("scope_templates", {})
    scope_templates = scope_templates if isinstance(scope_templates, dict) else {}
    template_block = scope_templates.get(scope, {})
    template_block = template_block if isinstance(template_block, dict) else {}

    docs_scope_template = str(template_block.get("docs_scope_root", "{docs_root}/features/{scope_id}"))
    src_scope_template = str(template_block.get("src_scope_root", "{src_root}/features/{scope_id}"))
    context = {
        "docs_root": docs_root,
        "src_root": src_root,
        "scope_id": feature_id,
    }
    docs_scope_root = str(feature.get("docs_root", _format_template(docs_scope_template, context)))
    src_scope_root = str(feature.get("src_root", _format_template(src_scope_template, context)))
    return docs_scope_root, src_scope_root


def _resolve_artifact_candidates(
    index_payload: dict[str, Any],
    feature_id: str,
    feature: dict[str, Any],
    deliverable_id: str,
) -> list[str]:
    rules = index_payload.get("rules", {})
    if not isinstance(rules, dict):
        return []
    path_mapping = rules.get("path_mapping", {})
    if not isinstance(path_mapping, dict):
        return []
    mapping = path_mapping.get(deliverable_id)
    if not isinstance(mapping, dict):
        return []

    roots = rules.get("roots", {})
    roots = roots if isinstance(roots, dict) else {}
    docs_scope_root, src_scope_root = _resolve_scope_roots(feature_id, feature, rules)
    default_filename = "manifest.json"
    defaults = mapping.get("default_filenames")
    if isinstance(defaults, list) and defaults:
        default_filename = str(defaults[0])

    context = {
        "docs_root": roots.get("docs_root", "docs"),
        "src_root": roots.get("src_root", "src"),
        "infra_root": roots.get("infra_root", "infra"),
        "state_root": roots.get("state_root", ".helix/state"),
        "runtime_root": roots.get("runtime_root", ".helix/runtime"),
        "scope_id": feature_id,
        "deliverable_id": deliverable_id,
        "docs_scope_root": docs_scope_root,
        "src_scope_root": src_scope_root,
        "filename": default_filename,
    }

    candidates: list[str] = []
    primary = mapping.get("primary_path")
    if isinstance(primary, str) and primary:
        candidates.append(_format_template(primary, context))

    capture_globs = mapping.get("capture_globs")
    if isinstance(capture_globs, list):
        for capture in capture_globs:
            if isinstance(capture, str) and capture:
                path = _format_template(capture, context)
                if path not in candidates:
                    candidates.append(path)

    alternate_paths = mapping.get("alternate_paths")
    if isinstance(alternate_paths, list):
        for alt in alternate_paths:
            if isinstance(alt, str) and alt:
                path = _format_template(alt, context)
                if path not in candidates:
                    candidates.append(path)

    return candidates


def _collect_artifact_paths(project_root: Path, candidates: list[str]) -> list[Path]:
    paths: list[Path] = []
    for candidate in candidates:
        if _contains_glob(candidate):
            for matched in glob.glob(str(project_root / candidate), recursive=True):
                path = Path(matched)
                if path.is_file():
                    paths.append(path)
        else:
            path = project_root / candidate
            if path.is_file():
                paths.append(path)
    return paths


def _filter_small_artifacts(paths: list[Path]) -> list[Path]:
    small: list[Path] = []
    for path in paths:
        try:
            if path.stat().st_size < MIN_ARTIFACT_BYTES:
                small.append(path)
        except OSError:
            continue
    return small


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
    project_root: Path | None = None,
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
        "warnings": 0,
        "empty_artifacts": 0,
    }

    result_features: dict[str, Any] = {}
    overall_pass = True
    warnings: list[dict[str, Any]] = []

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
                    if status == "done" and project_root is not None:
                        candidates = _resolve_artifact_candidates(index_payload, feature_id, feature, did)
                        matched_paths = _collect_artifact_paths(project_root, candidates)
                        if matched_paths:
                            small = _filter_small_artifacts(matched_paths)
                            if len(small) == len(matched_paths):
                                status = "pending"
                                summary["warnings"] += 1
                                summary["empty_artifacts"] += 1
                                sample: list[str] = []
                                for path in small[:3]:
                                    try:
                                        sample.append(str(path.relative_to(project_root)))
                                    except ValueError:
                                        sample.append(str(path))
                                warnings.append(
                                    {
                                        "type": "empty_deliverable",
                                        "feature_id": feature_id,
                                        "deliverable_id": did,
                                        "files": sample,
                                        "message": "空の成果物（10 バイト未満）を検知",
                                    }
                                )

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
        "warnings": warnings,
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
    warnings = int(summary.get("warnings", 0))
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
    if warnings:
        parts.append(f"{warnings} warnings")
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
    warning_items = result.get("warnings", [])
    if isinstance(warning_items, list) and warning_items:
        for item in warning_items:
            if not isinstance(item, dict):
                continue
            feature_id = str(item.get("feature_id", "?"))
            did = str(item.get("deliverable_id", "?"))
            message = str(item.get("message", "warning"))
            files = item.get("files", [])
            file_part = ""
            if isinstance(files, list) and files:
                file_part = f" ({', '.join(str(x) for x in files[:3])})"
            print(f"WARN: {feature_id}/{did} {message}{file_part}")
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
        index_path = Path(args.index)
        index_payload = _load_json(index_path)
        state_payload = _load_json(Path(args.state))
        project_root: Path | None = None
        resolved = index_path.resolve()
        if len(resolved.parents) >= 3:
            project_root = resolved.parents[2]
        result = evaluate_gate(
            index_payload=index_payload,
            state_payload=state_payload,
            gate=args.gate,
            project_root=project_root,
        )
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
