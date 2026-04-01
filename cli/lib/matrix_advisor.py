#!/usr/bin/env python3
"""HELIX matrix advisory checker (Phase 3: advisory only)."""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

COMPLETE_STATUSES = {"done", "waived", "not_applicable"}
SRC_COLLECTION_TO_SCOPE = {
    "features": "feature",
    "shared": "shared",
    "platform": "platform",
}
SCOPE_TO_SRC_COLLECTION = {v: k for k, v in SRC_COLLECTION_TO_SCOPE.items()}
DELIVERABLE_DIR_RE = re.compile(r"^(D-[A-Z0-9]+(?:-[A-Z0-9]+)*)(?:/|$)")


@dataclass
class PathInfo:
    rel_path: str
    root_kind: str | None = None
    scope_collection: str | None = None
    scope_type: str | None = None
    scope_id: str | None = None
    deliverable_id: str | None = None
    is_src_scope_path: bool = False


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} のトップレベルがオブジェクトではありません")
    return payload


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


def _extract_deliverable_id(remainder: str | None) -> str | None:
    if not remainder:
        return None
    m = DELIVERABLE_DIR_RE.match(remainder)
    if m:
        return m.group(1)
    return None


def infer_path_info(rel_path: str) -> PathInfo:
    info = PathInfo(rel_path=rel_path)

    src_match = re.match(r"^src/(features|shared|platform)/([^/]+)(?:/(.*))?$", rel_path)
    if src_match:
        collection = src_match.group(1)
        info.root_kind = "src"
        info.scope_collection = collection
        info.scope_type = SRC_COLLECTION_TO_SCOPE.get(collection)
        info.scope_id = src_match.group(2)
        info.deliverable_id = _extract_deliverable_id(src_match.group(3))
        info.is_src_scope_path = True
        return info

    docs_match = re.match(r"^docs/(features|shared|platform)/([^/]+)(?:/(.*))?$", rel_path)
    if docs_match:
        collection = docs_match.group(1)
        info.root_kind = "docs"
        info.scope_collection = collection
        info.scope_type = SRC_COLLECTION_TO_SCOPE.get(collection)
        info.scope_id = docs_match.group(2)
        info.deliverable_id = _extract_deliverable_id(docs_match.group(3))
        return info

    infra_match = re.match(r"^infra/([^/]+)(?:/(.*))?$", rel_path)
    if infra_match:
        info.root_kind = "infra"
        info.scope_type = "platform"
        info.scope_id = infra_match.group(1)
        info.deliverable_id = _extract_deliverable_id(infra_match.group(2))
        return info

    return info


def _format_template(template: str, values: dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return str(values.get(key, match.group(0)))

    return re.sub(r"{([a-zA-Z0-9_]+)}", replace, template)


def _resolve_scope_roots(
    scope_id: str,
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

    context = {
        "docs_root": docs_root,
        "src_root": src_root,
        "infra_root": roots.get("infra_root", "infra"),
        "scope_id": scope_id,
    }

    docs_scope_template = str(
        template_block.get("docs_scope_root", "{docs_root}/features/{scope_id}")
    )
    src_scope_template = str(
        template_block.get("src_scope_root", "{src_root}/features/{scope_id}")
    )

    docs_scope_root = str(feature.get("docs_root", _format_template(docs_scope_template, context)))
    src_scope_root = str(feature.get("src_root", _format_template(src_scope_template, context)))
    return docs_scope_root, src_scope_root


def _build_template_context(
    scope_id: str,
    feature: dict[str, Any],
    rules: dict[str, Any],
    deliverable_id: str,
) -> dict[str, Any]:
    roots = rules.get("roots", {})
    if not isinstance(roots, dict):
        roots = {}
    docs_scope_root, src_scope_root = _resolve_scope_roots(scope_id, feature, rules)

    return {
        "docs_root": roots.get("docs_root", "docs"),
        "src_root": roots.get("src_root", "src"),
        "infra_root": roots.get("infra_root", "infra"),
        "state_root": roots.get("state_root", ".helix/state"),
        "runtime_root": roots.get("runtime_root", ".helix/runtime"),
        "scope_id": scope_id,
        "deliverable_id": deliverable_id,
        "docs_scope_root": docs_scope_root,
        "src_scope_root": src_scope_root,
        "filename": "manifest.json",
    }


def _collect_required_deliverables(feature: dict[str, Any], layers: tuple[str, ...]) -> list[str]:
    requires = feature.get("requires", {})
    if not isinstance(requires, dict):
        return []

    ordered: list[str] = []
    for layer in layers:
        items = requires.get(layer, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, str) and item not in ordered:
                ordered.append(item)
    return ordered


def _candidate_paths_for_doc_deliverable(
    scope_id: str,
    feature: dict[str, Any],
    rules: dict[str, Any],
    deliverable_id: str,
) -> list[str]:
    path_mapping = rules.get("path_mapping", {})
    if not isinstance(path_mapping, dict):
        path_mapping = {}
    mapping = path_mapping.get(deliverable_id, {})
    if not isinstance(mapping, dict):
        return []

    if str(mapping.get("root", "")) != "docs":
        return []

    primary_template = mapping.get("primary_path")
    if not isinstance(primary_template, str) or not primary_template:
        return []

    context = _build_template_context(scope_id, feature, rules, deliverable_id)

    default_filenames = mapping.get("default_filenames")
    if isinstance(default_filenames, list) and default_filenames:
        context["filename"] = str(default_filenames[0])

    primary = _format_template(primary_template, context)
    candidates = [primary]

    allowed_extensions = mapping.get("allowed_extensions")
    if isinstance(allowed_extensions, list):
        stem, dot, _ext = primary.rpartition(".")
        if dot:
            for ext in allowed_extensions:
                if not isinstance(ext, str) or not ext:
                    continue
                alt = f"{stem}.{ext}"
                if alt not in candidates:
                    candidates.append(alt)

    alternate_paths = mapping.get("alternate_paths")
    if isinstance(alternate_paths, list):
        for alt_template in alternate_paths:
            if not isinstance(alt_template, str) or not alt_template:
                continue
            alt_path = _format_template(alt_template, context)
            if alt_path not in candidates:
                candidates.append(alt_path)

    return candidates


def _path_exists(project_root: Path, rel_path: str) -> bool:
    return (project_root / rel_path).exists()


def _warn_unregistered(scope_collection: str, scope_id: str) -> None:
    scope_root = f"src/{scope_collection}/{scope_id}/"
    print(f"[helix-advisory] ⚠ 未登録: {scope_root} は対照表に登録されていません")
    print("[helix-advisory]   'helix matrix init' で matrix.yaml に追加してください")


def _warn_missing_docs(scope_id: str, deliverable_id: str, suggested_path: str) -> None:
    print(f"[helix-advisory] ⚠ docs 欠落: {scope_id} の {deliverable_id} が見つかりません")
    print(f"[helix-advisory]   {suggested_path} を作成してください")


def _warn_phase_skip(scope_id: str, incomplete: list[tuple[str, str]]) -> None:
    preview = incomplete[:8]
    summary = ", ".join(f"{did}({status})" for did, status in preview)
    if len(incomplete) > len(preview):
        summary += f", ... +{len(incomplete) - len(preview)}"
    print(f"[helix-advisory] ⚠ フェーズ飛ばし: {scope_id} の L3 成果物が未完了です")
    print(f"[helix-advisory]   未完了: {summary}")
    print("[helix-advisory]   L3 を完了してから実装に進むことを推奨します")


def _detect_missing_docs(
    project_root: Path,
    scope_id: str,
    feature: dict[str, Any],
    rules: dict[str, Any],
) -> tuple[str, str] | None:
    required = _collect_required_deliverables(feature, ("L1", "L2", "L3"))
    if not required:
        return None

    docs_scope_root, _src_scope_root = _resolve_scope_roots(scope_id, feature, rules)
    docs_scope_exists = _path_exists(project_root, docs_scope_root)

    for did in required:
        candidate_paths = _candidate_paths_for_doc_deliverable(scope_id, feature, rules, did)
        if candidate_paths:
            if any(_path_exists(project_root, path) for path in candidate_paths):
                continue
            return did, candidate_paths[0]
        if docs_scope_exists and _path_exists(project_root, f"{docs_scope_root}/{did}"):
            continue
        return did, f"{docs_scope_root}/{did}/"

    return None


def _is_l4_change(path_info: PathInfo, feature: dict[str, Any]) -> bool:
    if path_info.root_kind not in {"src", "infra"}:
        return False

    requires = feature.get("requires", {})
    l4_list = requires.get("L4", []) if isinstance(requires, dict) else []
    l4_ids = {did for did in l4_list if isinstance(did, str)}
    if not l4_ids:
        return True

    effective_did = path_info.deliverable_id or "D-IMPL"
    if effective_did in l4_ids:
        return True
    if path_info.deliverable_id is None and "D-IMPL" in l4_ids:
        return True
    return False


def _extract_feature_state(state_payload: dict[str, Any], scope_id: str) -> dict[str, Any]:
    features = state_payload.get("features", {})
    if not isinstance(features, dict):
        return {}
    feature_state = features.get(scope_id, {})
    if not isinstance(feature_state, dict):
        return {}
    deliverables = feature_state.get("deliverables", {})
    if not isinstance(deliverables, dict):
        return {}
    return deliverables


def _detect_phase_skip(
    scope_id: str,
    feature: dict[str, Any],
    state_payload: dict[str, Any],
) -> list[tuple[str, str]]:
    required = _collect_required_deliverables(feature, ("L1", "L2", "L3"))
    if not required:
        return []

    state_deliverables = _extract_feature_state(state_payload, scope_id)

    incomplete: list[tuple[str, str]] = []
    for did in required:
        entry = state_deliverables.get(did)
        status = "pending"
        if isinstance(entry, dict):
            raw = entry.get("status", "pending")
            status = str(raw)
        elif isinstance(entry, str):
            status = entry
        if status not in COMPLETE_STATUSES:
            incomplete.append((did, status))
    return incomplete


def run_advisory(
    index_path: Path,
    state_path: Path,
    rel_path: str,
    project_root: Path,
) -> None:
    if not index_path.exists():
        return

    index_payload = _load_json(index_path)
    features = index_payload.get("features", {})
    if not isinstance(features, dict):
        features = {}
    rules = index_payload.get("rules", {})
    if not isinstance(rules, dict):
        rules = {}

    state_payload: dict[str, Any] = {}
    if state_path.exists():
        state_payload = _load_json(state_path)

    path_info = infer_path_info(rel_path)
    if not path_info.scope_id:
        return

    feature_raw = features.get(path_info.scope_id)
    feature = feature_raw if isinstance(feature_raw, dict) else None

    if path_info.is_src_scope_path:
        if feature is None:
            _warn_unregistered(path_info.scope_collection or "features", path_info.scope_id)
            return
        actual_scope = feature.get("scope")
        if isinstance(actual_scope, str):
            expected_collection = SCOPE_TO_SRC_COLLECTION.get(actual_scope)
            if expected_collection and expected_collection != path_info.scope_collection:
                _warn_unregistered(path_info.scope_collection or "features", path_info.scope_id)
                return

    if feature is None:
        return

    if path_info.root_kind in {"src", "infra"}:
        missing = _detect_missing_docs(
            project_root=project_root,
            scope_id=path_info.scope_id,
            feature=feature,
            rules=rules,
        )
        if missing:
            did, suggested_path = missing
            _warn_missing_docs(path_info.scope_id, did, suggested_path)

        if _is_l4_change(path_info, feature):
            incomplete = _detect_phase_skip(path_info.scope_id, feature, state_payload)
            if incomplete:
                _warn_phase_skip(path_info.scope_id, incomplete)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HELIX matrix advisory checker")
    parser.add_argument("--index", required=True, help="path to .helix/runtime/index.json")
    parser.add_argument("--state", required=True, help="path to .helix/state/deliverables.json")
    parser.add_argument("--file", required=True, help="changed file path (relative or absolute)")
    parser.add_argument("--project-root", required=True, help="project root path")
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
    except SystemExit:
        return 0

    try:
        project_root = Path(args.project_root).resolve()
        rel_path = _normalize_rel_path(args.file, project_root)
        if not rel_path:
            return 0

        run_advisory(
            index_path=Path(args.index),
            state_path=Path(args.state),
            rel_path=rel_path,
            project_root=project_root,
        )
    except Exception as exc:  # advisory failure must not break hook
        print(f"[helix-advisory] ERROR: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
