#!/usr/bin/env python3
"""HELIX freeze-break checker (runtime/index.json driven)."""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import subprocess
import sys
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from yaml_parser import get_nested, parse_yaml

LAYER_ORDER = [f"L{i}" for i in range(1, 9)]
LAYER_TO_GATE = {
    "L1": "G1",
    "L2": "G2",
    "L3": "G3",
    "L4": "G4",
    "L5": "G5",
    "L6": "G6",
    "L7": "G7",
}
GATE_ORDER = ["G1", "G2", "G3", "G4", "G5", "G6", "G7"]
FREEZE_LABELS = {
    "G2": "設計凍結違反",
    "G3": "API凍結違反",
    "G5": "Visual凍結違反",
}


def _normalize_rel_path(raw_path: str, project_root: Path) -> str:
    path = raw_path.strip()
    if not path:
        return ""
    if os.path.isabs(path):
        try:
            rel = os.path.relpath(path, project_root)
            if not rel.startswith(".."):
                path = rel
        except ValueError:
            pass
    path = path.replace("\\", "/")
    if path.startswith("./"):
        path = path[2:]
    normalized = posixpath.normpath(path)
    if normalized == ".":
        return ""
    return normalized


def _load_phase(path: Path) -> dict[str, Any]:
    payload = parse_yaml(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    return payload


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _format_template(template: str, values: dict[str, Any]) -> str:
    return re.sub(r"{([a-zA-Z0-9_]+)}", lambda m: str(values.get(m.group(1), m.group(0))), template)


def _resolve_scope_roots(
    feature_id: str,
    feature: dict[str, Any],
    rules: dict[str, Any],
) -> tuple[str, str]:
    roots = rules.get("roots", {})
    if not isinstance(roots, dict):
        roots = {}
    docs_root = str(roots.get("docs_root", "docs"))
    src_root = str(roots.get("src_root", "src"))
    scope = str(feature.get("scope", "feature"))

    scope_templates = rules.get("scope_templates", {})
    if not isinstance(scope_templates, dict):
        scope_templates = {}
    template_block = scope_templates.get(scope, {})
    if not isinstance(template_block, dict):
        template_block = {}

    values = {
        "docs_root": docs_root,
        "src_root": src_root,
        "infra_root": roots.get("infra_root", "infra"),
        "scope_id": feature_id,
    }
    docs_template = str(template_block.get("docs_scope_root", "{docs_root}/features/{scope_id}"))
    src_template = str(template_block.get("src_scope_root", "{src_root}/features/{scope_id}"))
    docs_scope_root = str(feature.get("docs_root", _format_template(docs_template, values)))
    src_scope_root = str(feature.get("src_root", _format_template(src_template, values)))
    return docs_scope_root, src_scope_root


def _path_matches(rel_path: str, pattern: str) -> bool:
    if any(ch in pattern for ch in ("*", "?", "[")):
        return Path(rel_path).match(pattern) or fnmatchcase(rel_path, pattern)
    return rel_path == pattern


def _unique(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _candidate_patterns_for_deliverable(
    feature_id: str,
    feature: dict[str, Any],
    deliverable_id: str,
    rules: dict[str, Any],
) -> list[str]:
    roots = rules.get("roots", {})
    if not isinstance(roots, dict):
        roots = {}
    path_mapping = rules.get("path_mapping", {})
    if not isinstance(path_mapping, dict):
        path_mapping = {}
    mapping = path_mapping.get(deliverable_id, {})
    if not isinstance(mapping, dict):
        mapping = {}

    docs_scope_root, src_scope_root = _resolve_scope_roots(feature_id, feature, rules)
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
        "filename": "manifest.json",
    }

    defaults = mapping.get("default_filenames")
    if isinstance(defaults, list) and defaults:
        first = defaults[0]
        if isinstance(first, str) and first:
            context["filename"] = first

    patterns: list[str] = []
    primary = mapping.get("primary_path")
    if isinstance(primary, str) and primary:
        resolved_primary = _format_template(primary, context)
        patterns.append(resolved_primary)
        parent = posixpath.dirname(resolved_primary)
        if parent and parent != ".":
            patterns.append(f"{parent}/**/*")

    capture_globs = mapping.get("capture_globs")
    if isinstance(capture_globs, list):
        for item in capture_globs:
            if isinstance(item, str) and item:
                patterns.append(_format_template(item, context))

    alternate_paths = mapping.get("alternate_paths")
    if isinstance(alternate_paths, list):
        for item in alternate_paths:
            if isinstance(item, str) and item:
                alt = _format_template(item, context)
                patterns.append(alt)
                parent = posixpath.dirname(alt)
                if parent and parent != ".":
                    patterns.append(f"{parent}/**/*")

    patterns.append(f"{docs_scope_root}/{deliverable_id}/**/*")
    patterns.append(f"{src_scope_root}/{deliverable_id}/**/*")
    patterns.append(f"{roots.get('infra_root', 'infra')}/{feature_id}/{deliverable_id}/**/*")
    return _unique(patterns)


def _catalog_layers(index_payload: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    rules = index_payload.get("rules", {})
    if not isinstance(rules, dict):
        return out
    for item in rules.get("deliverables", []):
        if not isinstance(item, dict):
            continue
        did = item.get("id")
        layer = item.get("layer")
        if isinstance(did, str) and isinstance(layer, str):
            out[did] = layer
    return out


def _infer_by_path(index_payload: dict[str, Any], rel_path: str) -> tuple[str | None, str | None, str | None]:
    features = index_payload.get("features", {})
    if not isinstance(features, dict):
        return None, None, None

    rules = index_payload.get("rules", {})
    if not isinstance(rules, dict):
        rules = {}
    layers = _catalog_layers(index_payload)

    for feature_id, feature_raw in features.items():
        if not isinstance(feature_raw, dict):
            continue
        requires = feature_raw.get("requires", {})
        if not isinstance(requires, dict):
            continue
        for layer in LAYER_ORDER:
            did_list = requires.get(layer, [])
            if not isinstance(did_list, list):
                continue
            for did_raw in did_list:
                if not isinstance(did_raw, str):
                    continue
                did = did_raw
                for pattern in _candidate_patterns_for_deliverable(feature_id, feature_raw, did, rules):
                    if _path_matches(rel_path, pattern):
                        return feature_id, did, layers.get(did, layer)

    fallback = re.match(r"^(?:docs|src)/(?:features|shared|platform)/([^/]+)/((D-[A-Z0-9]+(?:-[A-Z0-9]+)*)/.*)$", rel_path)
    if fallback:
        did = fallback.group(3)
        return fallback.group(1), did, layers.get(did)
    return None, None, None


def _legacy_layer(rel_path: str) -> str | None:
    if re.match(r"^docs/design/L2-[^/]+", rel_path):
        return "L2"
    if re.match(r"^src/api/.*", rel_path):
        return "L3"
    if re.match(r"^src/components/.*", rel_path):
        return "L5"
    return None


def _status(value: Any) -> str:
    if value is None:
        return "pending"
    return str(value).strip().lower()


def _downstream_gates(gate: str) -> list[str]:
    if gate not in GATE_ORDER:
        return []
    idx = GATE_ORDER.index(gate)
    return GATE_ORDER[idx + 1 :]


def _invalidate_gates(phase_file: Path, gates: list[str]) -> list[str]:
    changed: list[str] = []
    parser_path = SCRIPT_DIR / "yaml_parser.py"
    phase_data = _load_phase(phase_file)
    for gate in gates:
        current = _status(get_nested(phase_data, f"gates.{gate}.status"))
        if current != "passed":
            continue
        subprocess.run(
            ["python3", str(parser_path), "write", str(phase_file), f"gates.{gate}.status", "invalidated"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        changed.append(gate)
    return changed


def run(phase_file: Path, index_file: Path, file_path: str) -> int:
    phase_data = _load_phase(phase_file)
    if not phase_data:
        return 0

    project_root = phase_file.parent.parent.resolve()
    rel_path = _normalize_rel_path(file_path, project_root)
    if not rel_path:
        return 0

    index_payload = _load_json(index_file)
    feature_id, deliverable_id, layer = _infer_by_path(index_payload, rel_path)
    if layer is None:
        layer = _legacy_layer(rel_path)
    if layer is None:
        return 0

    gate = LAYER_TO_GATE.get(layer)
    if gate is None:
        return 0
    gate_status = _status(get_nested(phase_data, f"gates.{gate}.status"))
    if gate_status != "passed":
        return 0

    label = FREEZE_LABELS.get(gate, f"{gate}凍結違反")
    print(f"[helix-hook] WARN: {label} — {gate} passed 後に {rel_path} を変更")
    if feature_id and deliverable_id:
        print(f"[helix-hook]   deliverable: {feature_id}/{deliverable_id} ({layer})")

    invalidated = _invalidate_gates(phase_file, _downstream_gates(gate))
    if invalidated:
        print(f"[helix-hook]   下流ゲート無効化: {' '.join(invalidated)}")
        print("[helix-hook]   freeze-break 手続きが必要です（gate-policy.md §freeze-break 参照）")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HELIX freeze checker")
    parser.add_argument("--phase-file", required=True, help="path to .helix/phase.yaml")
    parser.add_argument("--index", required=True, help="path to .helix/runtime/index.json")
    parser.add_argument("--file", required=True, help="changed file path")
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        return run(
            phase_file=Path(args.phase_file),
            index_file=Path(args.index),
            file_path=str(args.file),
        )
    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(main())
