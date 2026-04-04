#!/usr/bin/env python3
"""HELIX matrix compiler.

責務:
  - matrix.yaml と rules から HELIX の派生ファイルを生成する
  - 成果物の自動検知（auto-detect）で状態を更新する

matrix.yaml + rules/*.yaml から以下を生成する:
- .helix/doc-map.yaml
- .helix/gate-checks.yaml
- .helix/state/deliverables.json
- .helix/runtime/index.json

PyYAML は使わず、既知テンプレート構造向けの YAML サブセットパーサーを内蔵する。
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .gate_check_generator import (
        build_doc_map as _build_doc_map_impl,
        build_gate_checks as _build_gate_checks_impl,
        dump_doc_map_yaml as _dump_doc_map_yaml_impl,
        dump_gate_checks_yaml as _dump_gate_checks_yaml_impl,
    )
except ImportError:
    from gate_check_generator import (
        build_doc_map as _build_doc_map_impl,
        build_gate_checks as _build_gate_checks_impl,
        dump_doc_map_yaml as _dump_doc_map_yaml_impl,
        dump_gate_checks_yaml as _dump_gate_checks_yaml_impl,
    )


class MatrixError(Exception):
    """ユーザー向けエラー。"""


VALID_STATE_STATUSES = {"pending", "in_progress", "done", "waived", "not_applicable"}
MANUAL_LOCKED_STATUSES = {"waived", "not_applicable"}
ALLOWED_DRIVES = {"be", "fe", "db", "fullstack", "agent"}
ALLOWED_SCOPES = {"feature", "shared", "platform"}
UI_REQUIRED_DRIVES = {"fe", "fullstack", "agent"}
FEATURE_ID_REGEX_DEFAULT = r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$"
MIN_ARTIFACT_BYTES = 10
HELIX_TEMPLATE_VERSION = 3

COMMON_REQUIRES = {
    "L1": ["D-REQ-F", "D-REQ-NF", "D-ACC"],
    "L2": ["D-ARCH", "D-ADR", "D-THREAT"],
    "L6": ["D-E2E", "D-PERF", "D-SECV", "D-OPS"],
    "L7": ["D-DEPLOY", "D-RELNOTE", "D-OBS"],
    "L8": ["D-UAT", "D-HANDOVER", "D-RETRO"],
}

DRIVE_L3_REQUIRES = {
    "be": ["D-API", "D-DB", "D-MIG-PLAN", "D-DEP", "D-TEST", "D-PLAN"],
    "fe": ["D-UI", "D-STATE", "D-API-CONS", "D-DEP", "D-TEST", "D-PLAN"],
    "db": ["D-DB", "D-MIG-PLAN", "D-DATA-ACCESS", "D-DEP", "D-TEST", "D-PLAN"],
    "fullstack": [
        "D-API",
        "D-DB",
        "D-MIG-PLAN",
        "D-DEP",
        "D-TEST",
        "D-PLAN",
        "D-CONTRACT",
        "D-UI",
        "D-STATE",
    ],
    "agent": ["D-TOOL", "D-PROMPT", "D-EVAL-PLAN", "D-DEP", "D-TEST", "D-PLAN"],
}

DRIVE_L4_REQUIRES = {
    "be": ["D-IMPL", "D-MIG", "D-CONFIG"],
    "fe": ["D-IMPL", "D-CONFIG"],
    "db": ["D-IMPL", "D-MIG", "D-CONFIG"],
    "fullstack": ["D-IMPL", "D-MIG", "D-CONFIG"],
    "agent": ["D-IMPL", "D-CONFIG"],
}


def _strip_inline_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for i, ch in enumerate(line):
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            continue
        if ch == "#" and not in_single and not in_double:
            if i == 0 or line[i - 1].isspace():
                return line[:i]
    return line


def _unquote(text: str) -> str:
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        quote = text[0]
        body = text[1:-1]
        body = body.replace(f"\\{quote}", quote).replace("\\\\", "\\")
        return body
    return text


def _find_unquoted(text: str, token: str) -> int:
    in_single = False
    in_double = False
    escaped = False
    depth_square = 0
    depth_curly = 0
    for i, ch in enumerate(text):
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single or in_double:
            continue
        if ch == "[":
            depth_square += 1
            continue
        if ch == "]":
            depth_square -= 1
            continue
        if ch == "{":
            depth_curly += 1
            continue
        if ch == "}":
            depth_curly -= 1
            continue
        if ch == token and depth_square == 0 and depth_curly == 0:
            return i
    return -1


def _split_top_level(text: str, delimiter: str = ",") -> list[str]:
    parts: list[str] = []
    in_single = False
    in_double = False
    escaped = False
    depth_square = 0
    depth_curly = 0
    start = 0
    for i, ch in enumerate(text):
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single or in_double:
            continue
        if ch == "[":
            depth_square += 1
            continue
        if ch == "]":
            depth_square -= 1
            continue
        if ch == "{":
            depth_curly += 1
            continue
        if ch == "}":
            depth_curly -= 1
            continue
        if ch == delimiter and depth_square == 0 and depth_curly == 0:
            parts.append(text[start:i])
            start = i + 1
    parts.append(text[start:])
    return parts


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if value == "":
        return ""

    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return _unquote(value)

    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in _split_top_level(inner, ",") if part.strip()]

    if value.startswith("{") and value.endswith("}"):
        inner = value[1:-1].strip()
        result: dict[str, Any] = {}
        if not inner:
            return result
        for pair in _split_top_level(inner, ","):
            if not pair.strip():
                continue
            pos = _find_unquoted(pair, ":")
            if pos < 0:
                raise MatrixError(f"インライン辞書の構文エラー: {pair.strip()}")
            key = _unquote(pair[:pos].strip())
            val = pair[pos + 1 :].strip()
            result[key] = _parse_scalar(val)
        return result

    lowered = value.lower()
    if lowered in ("null", "none", "~"):
        return None
    if lowered in ("true", "yes"):
        return True
    if lowered in ("false", "no"):
        return False
    if re.fullmatch(r"[-+]?\d+", value):
        try:
            return int(value)
        except ValueError:
            pass
    if re.fullmatch(r"[-+]?\d+\.\d+", value):
        try:
            return float(value)
        except ValueError:
            pass
    return value


def _split_key_value(text: str, source: Path, lineno: int) -> tuple[str, str]:
    pos = _find_unquoted(text, ":")
    if pos < 0:
        raise MatrixError(f"{source}:{lineno}: キー:値 形式ではありません: {text}")
    key = _unquote(text[:pos].strip())
    if not key:
        raise MatrixError(f"{source}:{lineno}: キーが空です")
    return key, text[pos + 1 :].strip()


def _looks_like_mapping(text: str) -> bool:
    pos = _find_unquoted(text, ":")
    return pos > 0


class SimpleYamlParser:
    """既知テンプレート向け YAML サブセットパーサー。"""

    def __init__(self, text: str, source: Path) -> None:
        self.source = source
        self.lines: list[tuple[int, str, int]] = []
        for lineno, raw in enumerate(text.splitlines(), start=1):
            line = _strip_inline_comment(raw.rstrip("\n"))
            if not line.strip():
                continue
            if "\t" in line:
                raise MatrixError(f"{source}:{lineno}: タブインデントは未対応です")
            indent = len(line) - len(line.lstrip(" "))
            content = line[indent:]
            self.lines.append((indent, content, lineno))

    def parse(self) -> Any:
        if not self.lines:
            return {}
        node, index = self._parse_block(0, self.lines[0][0])
        if index != len(self.lines):
            source_lineno = self.lines[index][2]
            raise MatrixError(f"{self.source}:{source_lineno}: 解析できない行があります")
        return node

    def _parse_block(self, index: int, _expected_indent: int) -> tuple[Any, int]:
        if index >= len(self.lines):
            return {}, index
        indent, content, _ = self.lines[index]
        if content.startswith("- "):
            return self._parse_list(index, indent)
        return self._parse_dict(index, indent)

    def _parse_dict(self, index: int, indent: int) -> tuple[dict[str, Any], int]:
        result: dict[str, Any] = {}
        while index < len(self.lines):
            line_indent, content, lineno = self.lines[index]
            if line_indent < indent:
                break
            if line_indent > indent:
                raise MatrixError(f"{self.source}:{lineno}: 不正なインデントです")
            if content.startswith("- "):
                break

            key, raw_value = _split_key_value(content, self.source, lineno)
            index += 1

            if raw_value == "":
                if index < len(self.lines) and self.lines[index][0] > line_indent:
                    child, index = self._parse_block(index, self.lines[index][0])
                    result[key] = child
                else:
                    result[key] = {}
            else:
                result[key] = _parse_scalar(raw_value)
        return result, index

    def _parse_list(self, index: int, indent: int) -> tuple[list[Any], int]:
        result: list[Any] = []
        while index < len(self.lines):
            line_indent, content, lineno = self.lines[index]
            if line_indent < indent:
                break
            if line_indent > indent:
                raise MatrixError(f"{self.source}:{lineno}: 不正なインデントです")
            if not content.startswith("- "):
                break

            rest = content[2:].strip()
            index += 1

            if rest == "":
                if index < len(self.lines) and self.lines[index][0] > line_indent:
                    item, index = self._parse_block(index, self.lines[index][0])
                else:
                    item = None
                result.append(item)
                continue

            if _looks_like_mapping(rest):
                key, raw_value = _split_key_value(rest, self.source, lineno)
                item: dict[str, Any] = {}
                if raw_value == "":
                    if index < len(self.lines) and self.lines[index][0] > line_indent:
                        child, index = self._parse_block(index, self.lines[index][0])
                    else:
                        child = {}
                    item[key] = child
                else:
                    item[key] = _parse_scalar(raw_value)

                if index < len(self.lines) and self.lines[index][0] > line_indent:
                    next_indent = self.lines[index][0]
                    if self.lines[index][1].startswith("- "):
                        child, index = self._parse_list(index, next_indent)
                        first_key = next(iter(item.keys()))
                        if item[first_key] in ({}, None):
                            item[first_key] = child
                        else:
                            item["_items"] = child
                    else:
                        extra, index = self._parse_dict(index, next_indent)
                        item.update(extra)
                result.append(item)
                continue

            scalar_item = _parse_scalar(rest)
            if index < len(self.lines) and self.lines[index][0] > line_indent:
                raise MatrixError(f"{self.source}:{lineno}: 複数行スカラーは未対応です")
            result.append(scalar_item)

        return result, index


def load_yaml(path: Path) -> Any:
    if not path.exists():
        raise MatrixError(f"ファイルが見つかりません: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise MatrixError(f"ファイル読込に失敗しました: {path}: {exc}") from exc
    parser = SimpleYamlParser(text, path)
    return parser.parse()


def _format_template(template: str, values: dict[str, Any]) -> str:
    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise MatrixError(f"テンプレート変数 {{{key}}} を解決できません: {template}")
        return str(values[key])

    return re.sub(r"{([a-zA-Z0-9_]+)}", replacer, template)


@dataclass
class ResolveResult:
    primary: str | None
    capture: list[str]


def _resolve_scope_roots(feature_id: str, feature: dict[str, Any], structure: dict[str, Any]) -> tuple[str, str]:
    roots = structure.get("roots", {}) if isinstance(structure.get("roots"), dict) else {}
    docs_root = str(roots.get("docs_root", "docs"))
    src_root = str(roots.get("src_root", "src"))

    scope = str(feature.get("scope", "feature"))
    scope_templates = structure.get("scope_templates", {}) if isinstance(structure.get("scope_templates"), dict) else {}
    template_block = scope_templates.get(scope, {}) if isinstance(scope_templates.get(scope), dict) else {}

    context = {
        "docs_root": docs_root,
        "src_root": src_root,
        "scope_id": feature_id,
    }
    docs_scope_template = str(template_block.get("docs_scope_root", "{docs_root}/features/{scope_id}"))
    src_scope_template = str(template_block.get("src_scope_root", "{src_root}/features/{scope_id}"))

    docs_scope_root = str(feature.get("docs_root", _format_template(docs_scope_template, context)))
    src_scope_root = str(feature.get("src_root", _format_template(src_scope_template, context)))
    return docs_scope_root, src_scope_root


def _d_contract_doc_pattern(feature_id: str, feature: dict[str, Any], structure: dict[str, Any]) -> str:
    docs_scope_root, _ = _resolve_scope_roots(feature_id, feature, structure)
    return f"{docs_scope_root}/D-CONTRACT/*"


def _resolve_paths(
    feature_id: str,
    feature: dict[str, Any],
    deliverable_id: str,
    structure: dict[str, Any],
) -> ResolveResult:
    path_mapping = structure.get("path_mapping", {})
    if not isinstance(path_mapping, dict):
        return ResolveResult(primary=None, capture=[])

    mapping = path_mapping.get(deliverable_id)
    if not isinstance(mapping, dict):
        return ResolveResult(primary=None, capture=[])

    roots = structure.get("roots", {}) if isinstance(structure.get("roots"), dict) else {}
    docs_scope_root, src_scope_root = _resolve_scope_roots(feature_id, feature, structure)
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

    primary = None
    primary_template = mapping.get("primary_path")
    if isinstance(primary_template, str) and primary_template:
        primary = _format_template(primary_template, context)

    capture: list[str] = []
    capture_globs = mapping.get("capture_globs")
    if isinstance(capture_globs, list):
        for glob_pattern in capture_globs:
            if isinstance(glob_pattern, str) and glob_pattern:
                capture.append(_format_template(glob_pattern, context))
    alternate_paths = mapping.get("alternate_paths")
    if isinstance(alternate_paths, list):
        for alt_template in alternate_paths:
            if isinstance(alt_template, str) and alt_template:
                formatted = _format_template(alt_template, context)
                if formatted not in capture:
                    capture.append(formatted)
    if not capture and primary:
        capture = [primary]

    return ResolveResult(primary=primary, capture=capture)


def _catalog_index(deliverables_rules: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    items = deliverables_rules.get("deliverables")
    if not isinstance(items, list):
        return result
    for item in items:
        if not isinstance(item, dict):
            continue
        did = item.get("id")
        if isinstance(did, str):
            result[did] = item
    return result


def build_doc_map(
    matrix: dict[str, Any],
    deliverables_rules: dict[str, Any],
    structure: dict[str, Any],
) -> dict[str, Any]:
    try:
        return _build_doc_map_impl(
            matrix,
            deliverables_rules,
            structure,
            catalog_index=_catalog_index,
            resolve_paths=_resolve_paths,
            d_contract_doc_pattern=_d_contract_doc_pattern,
        )
    except ValueError as exc:
        raise MatrixError(str(exc)) from exc


def build_gate_checks(
    matrix: dict[str, Any],
    deliverables_rules: dict[str, Any],
    structure: dict[str, Any],
    framework: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        return _build_gate_checks_impl(
            matrix,
            deliverables_rules,
            structure,
            framework=framework,
            catalog_index=_catalog_index,
            resolve_paths=_resolve_paths,
            d_contract_doc_pattern=_d_contract_doc_pattern,
        )
    except ValueError as exc:
        raise MatrixError(str(exc)) from exc


def _ordered_deliverables(feature: dict[str, Any]) -> list[str]:
    requires = feature.get("requires", {})
    if not isinstance(requires, dict):
        return []
    ordered: list[str] = []
    for layer in ("L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8"):
        values = requires.get(layer, [])
        if not isinstance(values, list):
            continue
        for value in values:
            if isinstance(value, str) and value not in ordered:
                ordered.append(value)
    return ordered


def build_state(matrix: dict[str, Any], generated_at: str) -> dict[str, Any]:
    features = matrix.get("features", {})
    if not isinstance(features, dict):
        raise MatrixError("matrix.features が辞書ではありません")

    out_features: dict[str, Any] = {}
    for feature_id, feature_raw in features.items():
        if not isinstance(feature_raw, dict):
            continue
        deliverables = _ordered_deliverables(feature_raw)
        out_features[feature_id] = {
            "deliverables": {
                did: {"status": "pending", "updated_at": generated_at}
                for did in deliverables
            }
        }

    return {
        "_meta": {
            "purpose": "Runtime state template for deliverable completion status",
            "generated_at": generated_at,
            "ignore_keys_prefix": "_",
        },
        "features": out_features,
    }


def build_runtime_index(
    matrix: dict[str, Any],
    deliverables_rules: dict[str, Any],
    structure: dict[str, Any],
    naming: dict[str, Any],
    common_defs: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    catalog = _catalog_index(deliverables_rules)
    gate_ownership = {
        did: item.get("gate_ownership", [])
        for did, item in catalog.items()
        if isinstance(item, dict)
    }
    return {
        "_meta": {
            "generated_at": generated_at,
            "generator": "cli/lib/matrix_compiler.py",
            "contract": "top-level keys that start with '_' must be ignored by consumers",
        },
        "project": matrix.get("project", {}),
        "features": matrix.get("features", {}),
        "waivers": matrix.get("waivers", []),
        "rules": {
            "catalog_version": deliverables_rules.get("catalog_version"),
            "deliverables": deliverables_rules.get("deliverables", []),
            "roots": structure.get("roots", {}),
            "scope_templates": structure.get("scope_templates", {}),
            "path_mapping": structure.get("path_mapping", {}),
            "gate_ownership": gate_ownership,
            "naming": naming,
            "common_defs": common_defs,
        },
    }


def dump_doc_map_yaml(doc_map: dict[str, Any]) -> str:
    return _dump_doc_map_yaml_impl(doc_map, helix_template_version=HELIX_TEMPLATE_VERSION)


def dump_gate_checks_yaml(gate_checks: dict[str, Any]) -> str:
    return _dump_gate_checks_yaml_impl(gate_checks, helix_template_version=HELIX_TEMPLATE_VERSION)


def _read_rules(project_root: Path, cli_root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    helix_rules = project_root / ".helix" / "rules"
    template_rules = cli_root / "templates" / "rules"

    def pick(name: str) -> Path:
        local_path = helix_rules / name
        if local_path.exists():
            return local_path
        template_path = template_rules / name
        if template_path.exists():
            return template_path
        raise MatrixError(f"rules ファイルが見つかりません: {name}")

    deliverables = load_yaml(pick("deliverables.yaml"))
    structure = load_yaml(pick("structure.yaml"))
    naming = load_yaml(pick("naming.yaml"))
    common_defs = load_yaml(pick("common-defs.yaml"))
    if not isinstance(deliverables, dict) or not isinstance(structure, dict):
        raise MatrixError("rules YAML の構造が不正です")
    return deliverables, structure, naming if isinstance(naming, dict) else {}, common_defs if isinstance(common_defs, dict) else {}


def _detect_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def dfs(node: str) -> list[str] | None:
        visiting.add(node)
        stack.append(node)
        for nxt in graph.get(node, []):
            if nxt in visiting:
                idx = stack.index(nxt)
                return stack[idx:] + [nxt]
            if nxt in visited:
                continue
            path = dfs(nxt)
            if path:
                return path
        stack.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for key in graph.keys():
        if key in visited:
            continue
        cycle = dfs(key)
        if cycle:
            return cycle
    return None


def validate_matrix(
    matrix: dict[str, Any],
    deliverables_rules: dict[str, Any],
    naming: dict[str, Any],
) -> None:
    errors: list[str] = []
    if not isinstance(matrix, dict):
        raise MatrixError("matrix.yaml のトップレベルが辞書ではありません")

    if not isinstance(matrix.get("project"), dict):
        errors.append("project セクションが必要です")

    features = matrix.get("features")
    if not isinstance(features, dict):
        errors.append("features セクションが辞書ではありません")
        raise MatrixError("\n".join(errors))

    catalog_ids = set(_catalog_index(deliverables_rules).keys())
    feature_regex = _feature_id_regex(naming)
    deliverable_regex = str(
        (
            naming.get("deliverable_id", {}).get("regex")
            if isinstance(naming.get("deliverable_id"), dict)
            else ""
        )
        or r"^D-[A-Z0-9]+(?:-[A-Z0-9]+)*$"
    )

    feature_ids = list(features.keys())
    graph: dict[str, list[str]] = {}
    for feature_id, feature_raw in features.items():
        if not re.fullmatch(feature_regex, feature_id):
            errors.append(f"feature_id が命名規則違反です: {feature_id}")
        if not isinstance(feature_raw, dict):
            errors.append(f"features.{feature_id} が辞書ではありません")
            continue

        scope = feature_raw.get("scope")
        if scope not in ("feature", "shared", "platform"):
            errors.append(f"features.{feature_id}.scope が不正です: {scope}")

        requires = feature_raw.get("requires")
        if not isinstance(requires, dict):
            errors.append(f"features.{feature_id}.requires が辞書ではありません")
            requires = {}

        for layer, deliverable_ids in requires.items():
            if not re.fullmatch(r"L[1-8]", str(layer)):
                errors.append(f"features.{feature_id}.requires の layer が不正です: {layer}")
            if not isinstance(deliverable_ids, list):
                errors.append(f"features.{feature_id}.requires.{layer} は配列である必要があります")
                continue
            for did in deliverable_ids:
                if not isinstance(did, str):
                    errors.append(f"features.{feature_id}.requires.{layer} に文字列以外があります")
                    continue
                if not re.fullmatch(deliverable_regex, did):
                    errors.append(f"deliverable_id 形式不正: {feature_id}:{layer}:{did}")
                if did not in catalog_ids:
                    errors.append(f"未定義 deliverable_id: {feature_id}:{layer}:{did}")

        shared_uses = feature_raw.get("shared_uses", [])
        if shared_uses is None:
            shared_uses = []
        if not isinstance(shared_uses, list):
            errors.append(f"features.{feature_id}.shared_uses は配列である必要があります")
            shared_uses = []
        deps: list[str] = []
        for sid in shared_uses:
            if not isinstance(sid, str):
                errors.append(f"features.{feature_id}.shared_uses に文字列以外があります")
                continue
            if sid == feature_id:
                errors.append(f"features.{feature_id}.shared_uses に自己参照があります")
                continue
            if sid not in features:
                errors.append(f"features.{feature_id}.shared_uses が未知IDを参照しています: {sid}")
                continue
            deps.append(sid)
        graph[feature_id] = deps

    waivers = matrix.get("waivers", [])
    if waivers is not None:
        if not isinstance(waivers, list):
            errors.append("waivers は配列である必要があります")
        else:
            for idx, waiver in enumerate(waivers):
                if not isinstance(waiver, dict):
                    errors.append(f"waivers[{idx}] が辞書ではありません")
                    continue
                feature_id = waiver.get("feature_id")
                deliverable_id = waiver.get("deliverable_id")
                if feature_id not in feature_ids:
                    errors.append(f"waivers[{idx}].feature_id が不正です: {feature_id}")
                if not isinstance(deliverable_id, str) or deliverable_id not in catalog_ids:
                    errors.append(f"waivers[{idx}].deliverable_id が不正です: {deliverable_id}")

    cycle = _detect_cycle(graph)
    if cycle:
        errors.append("shared_uses に循環参照があります: " + " -> ".join(cycle))

    if errors:
        raise MatrixError("matrix validate 失敗:\n- " + "\n- ".join(errors))


def _feature_id_regex(naming: dict[str, Any]) -> str:
    raw = (
        naming.get("feature_id", {}).get("regex")
        if isinstance(naming.get("feature_id"), dict)
        else ""
    )
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return FEATURE_ID_REGEX_DEFAULT


def _build_requires_for_drive(drive: str, ui: bool) -> dict[str, list[str]]:
    if drive not in ALLOWED_DRIVES:
        raise MatrixError(
            f"drive が不正です: {drive}（be|fe|db|fullstack|agent を指定）"
        )

    requires: dict[str, list[str]] = {
        "L1": list(COMMON_REQUIRES["L1"]),
        "L2": list(COMMON_REQUIRES["L2"]),
        "L3": list(DRIVE_L3_REQUIRES[drive]),
        "L4": list(DRIVE_L4_REQUIRES[drive]),
        "L6": list(COMMON_REQUIRES["L6"]),
        "L7": list(COMMON_REQUIRES["L7"]),
        "L8": list(COMMON_REQUIRES["L8"]),
    }
    if ui:
        requires["L5"] = ["D-VIS", "D-A11Y"]
    return requires


def _normalize_risk_flags(raw_risk: str) -> list[str]:
    if not raw_risk:
        return []
    flags: list[str] = []
    for token in raw_risk.split(","):
        value = token.strip()
        if value and value not in flags:
            flags.append(value)
    return flags


def _feature_scope_paths(matrix: dict[str, Any], scope: str, feature_id: str) -> tuple[str, str]:
    project = matrix.get("project", {})
    roots = project.get("roots", {}) if isinstance(project, dict) else {}
    docs_root = str(roots.get("docs_root", "docs"))
    src_root = str(roots.get("src_root", "src"))
    segment = {"feature": "features", "shared": "shared", "platform": "platform"}[scope]
    return f"{docs_root}/{segment}/{feature_id}", f"{src_root}/{segment}/{feature_id}"


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _dump_yaml_node(value: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent
    lines: list[str] = []
    if isinstance(value, dict):
        for key, node in value.items():
            key_text = str(key)
            if isinstance(node, dict):
                if node:
                    lines.append(f"{prefix}{key_text}:")
                    lines.extend(_dump_yaml_node(node, indent + 2))
                else:
                    lines.append(f"{prefix}{key_text}: {{}}")
            elif isinstance(node, list):
                if not node:
                    lines.append(f"{prefix}{key_text}: []")
                elif all(not isinstance(item, (dict, list)) for item in node):
                    rendered = ", ".join(_yaml_scalar(item) for item in node)
                    lines.append(f"{prefix}{key_text}: [{rendered}]")
                else:
                    lines.append(f"{prefix}{key_text}:")
                    for item in node:
                        item_prefix = " " * (indent + 2)
                        if isinstance(item, (dict, list)):
                            lines.append(f"{item_prefix}-")
                            lines.extend(_dump_yaml_node(item, indent + 4))
                        else:
                            lines.append(f"{item_prefix}- {_yaml_scalar(item)}")
            else:
                lines.append(f"{prefix}{key_text}: {_yaml_scalar(node)}")
        return lines

    if isinstance(value, list):
        if not value:
            return [f"{prefix}[]"]
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(_dump_yaml_node(item, indent + 2))
            else:
                lines.append(f"{prefix}- {_yaml_scalar(item)}")
        return lines

    return [f"{prefix}{_yaml_scalar(value)}"]


def dump_matrix_yaml(matrix: dict[str, Any]) -> str:
    ordered: dict[str, Any] = {}
    for key in ("project", "features", "waivers"):
        if key in matrix:
            ordered[key] = matrix[key]
    for key, value in matrix.items():
        if key not in ordered:
            ordered[key] = value
    return "\n".join(_dump_yaml_node(ordered)) + "\n"


def _write_matrix(project_root: Path, matrix: dict[str, Any]) -> None:
    matrix_path = project_root / ".helix" / "matrix.yaml"
    _write_text(matrix_path, dump_matrix_yaml(matrix))


def _upsert_feature_state(
    project_root: Path,
    matrix: dict[str, Any],
    feature_id: str,
    feature: dict[str, Any],
) -> None:
    state_path = project_root / ".helix" / "state" / "deliverables.json"
    state_payload = _ensure_state_payload(matrix, state_path)
    now = _now_iso()
    changed = 0
    for did in _ordered_deliverables(feature):
        entry = _ensure_feature_deliverable(state_payload, feature_id, did)
        if "status" not in entry:
            entry["status"] = "pending"
            changed += 1
        if not entry.get("updated_at"):
            entry["updated_at"] = now
            changed += 1

    meta = state_payload.setdefault("_meta", {})
    if isinstance(meta, dict):
        meta["generated_at"] = now

    if changed > 0:
        _write_json(state_path, state_payload)


def add_matrix_feature(
    project_root: Path,
    name: str,
    drive: str,
    scope: str,
    ui: bool,
    risk: str,
) -> None:
    normalized_name = name.strip()
    normalized_drive = drive.strip().lower()
    normalized_scope = scope.strip().lower()
    normalized_ui = bool(ui) or normalized_drive in UI_REQUIRED_DRIVES

    if normalized_scope not in ALLOWED_SCOPES:
        raise MatrixError(
            f"scope が不正です: {scope}（feature|shared|platform を指定）"
        )

    cli_root = Path(__file__).resolve().parents[1]
    _deliverables_rules, _structure, naming, _common_defs = _read_rules(project_root, cli_root)
    feature_regex = _feature_id_regex(naming)
    if not re.fullmatch(feature_regex, normalized_name):
        raise MatrixError(
            f"feature 名が不正です: {normalized_name}（kebab-case を指定）"
        )

    matrix = _load_matrix(project_root)
    features = matrix.get("features")
    if features is None:
        matrix["features"] = {}
        features = matrix["features"]
    if not isinstance(features, dict):
        raise MatrixError("matrix.features が辞書ではありません")
    if normalized_name in features:
        raise MatrixError(f"feature は既に存在します: {normalized_name}")

    docs_root, src_root = _feature_scope_paths(matrix, normalized_scope, normalized_name)
    feature = {
        "drive": normalized_drive,
        "scope": normalized_scope,
        "risk_flags": _normalize_risk_flags(risk),
        "ui": normalized_ui,
        "docs_root": docs_root,
        "src_root": src_root,
        "requires": _build_requires_for_drive(normalized_drive, normalized_ui),
    }
    features[normalized_name] = feature

    _write_matrix(project_root, matrix)
    print(f"追加: {normalized_name} (drive={normalized_drive}, scope={normalized_scope}, ui={str(normalized_ui).lower()})")
    compile_matrix(project_root, force_state=False)
    _upsert_feature_state(project_root, matrix, normalized_name, feature)


def _load_matrix(project_root: Path) -> dict[str, Any]:
    matrix_path = project_root / ".helix" / "matrix.yaml"
    matrix = load_yaml(matrix_path)
    if not isinstance(matrix, dict):
        raise MatrixError("matrix.yaml の内容が辞書ではありません")
    return matrix


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_framework(project_root: Path) -> dict[str, Any]:
    framework_path = project_root / ".helix" / "framework.yaml"
    if not framework_path.exists():
        return {}
    payload = load_yaml(framework_path)
    if not isinstance(payload, dict):
        raise MatrixError(f"framework.yaml の構造が不正です: {framework_path}")
    return payload


def _ensure_state_payload(matrix: dict[str, Any], state_path: Path) -> dict[str, Any]:
    if state_path.exists():
        try:
            payload = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise MatrixError(f"state/deliverables.json の JSON が不正です: {exc}") from exc
        if isinstance(payload, dict):
            return payload
    return build_state(matrix, _now_iso())


def _ensure_feature_deliverable(state_payload: dict[str, Any], feature_id: str, did: str) -> dict[str, Any]:
    features = state_payload.setdefault("features", {})
    if not isinstance(features, dict):
        state_payload["features"] = {}
        features = state_payload["features"]
    feature_state = features.setdefault(feature_id, {})
    if not isinstance(feature_state, dict):
        features[feature_id] = {}
        feature_state = features[feature_id]
    deliverables = feature_state.setdefault("deliverables", {})
    if not isinstance(deliverables, dict):
        feature_state["deliverables"] = {}
        deliverables = feature_state["deliverables"]
    entry = deliverables.setdefault(did, {})
    if not isinstance(entry, dict):
        deliverables[did] = {}
        entry = deliverables[did]
    return entry


def _is_valid_deliverable_for_feature(feature: dict[str, Any], deliverable_id: str) -> bool:
    return deliverable_id in _ordered_deliverables(feature)


def _contains_glob(path: str) -> bool:
    return any(ch in path for ch in ("*", "?", "["))


def _glob_scan_files(project_root: Path, pattern: str) -> tuple[bool, list[str]]:
    abs_pattern = str(project_root / pattern)
    has_sufficient = False
    small_files: list[str] = []
    for matched in glob.glob(abs_pattern, recursive=True):
        candidate = Path(matched)
        if not candidate.is_file():
            continue
        try:
            size = candidate.stat().st_size
        except OSError:
            continue
        if size >= MIN_ARTIFACT_BYTES:
            has_sufficient = True
        else:
            try:
                small_files.append(str(candidate.relative_to(project_root)))
            except ValueError:
                small_files.append(str(candidate))
    return has_sufficient, small_files


def _deliverable_artifact_scan(
    project_root: Path,
    feature_id: str,
    feature: dict[str, Any],
    deliverable_id: str,
    structure: dict[str, Any],
) -> tuple[bool, list[str]]:
    resolved = _resolve_paths(feature_id, feature, deliverable_id, structure)
    candidates: list[str] = []
    if resolved.primary:
        candidates.append(resolved.primary)
    candidates.extend([x for x in resolved.capture if x not in candidates])

    small_files: list[str] = []
    for candidate in candidates:
        if _contains_glob(candidate):
            has_sufficient, small = _glob_scan_files(project_root, candidate)
            small_files.extend(small)
            if has_sufficient:
                return True, small_files
        else:
            path = project_root / candidate
            if not path.is_file():
                continue
            try:
                size = path.stat().st_size
            except OSError:
                continue
            if size >= MIN_ARTIFACT_BYTES:
                return True, small_files
            small_files.append(candidate)

    if resolved.primary:
        primary_parent = Path(resolved.primary).parent.as_posix()
        has_sufficient, small = _glob_scan_files(project_root, f"{primary_parent}/**/*")
        small_files.extend(small)
        if has_sufficient:
            return True, small_files
    return False, small_files


def update_matrix_state(project_root: Path, feature_id: str, deliverable_id: str, status: str) -> None:
    normalized_status = status.strip()
    if normalized_status not in VALID_STATE_STATUSES - {"pending"}:
        raise MatrixError(
            "status は done|waived|not_applicable|in_progress を指定してください"
        )

    matrix = _load_matrix(project_root)
    features = matrix.get("features", {})
    if not isinstance(features, dict):
        raise MatrixError("matrix.features が辞書ではありません")
    feature_raw = features.get(feature_id)
    if not isinstance(feature_raw, dict):
        raise MatrixError(f"feature が見つかりません: {feature_id}")

    did = deliverable_id.strip()
    if not re.fullmatch(r"D-[A-Z0-9]+(?:-[A-Z0-9]+)*", did):
        raise MatrixError(f"deliverable_id の形式が不正です: {did}")
    if not _is_valid_deliverable_for_feature(feature_raw, did):
        raise MatrixError(f"{feature_id} に deliverable {did} は定義されていません")

    state_path = project_root / ".helix" / "state" / "deliverables.json"
    state_payload = _ensure_state_payload(matrix, state_path)
    entry = _ensure_feature_deliverable(state_payload, feature_id, did)
    now = _now_iso()
    entry["status"] = normalized_status
    entry["updated_at"] = now

    meta = state_payload.setdefault("_meta", {})
    if isinstance(meta, dict):
        meta["generated_at"] = now

    _write_json(state_path, state_payload)
    print(f"更新: {feature_id} {did} -> {normalized_status}")


def auto_detect_state(project_root: Path) -> None:
    cli_root = Path(__file__).resolve().parents[1]
    matrix = _load_matrix(project_root)
    deliverables_rules, structure, naming, _common_defs = _read_rules(project_root, cli_root)
    validate_matrix(matrix, deliverables_rules, naming)

    state_path = project_root / ".helix" / "state" / "deliverables.json"
    state_payload = _ensure_state_payload(matrix, state_path)

    features = matrix.get("features", {})
    if not isinstance(features, dict):
        raise MatrixError("matrix.features が辞書ではありません")

    changed = 0
    scanned = 0
    warnings = 0
    now = _now_iso()
    for feature_id, feature_raw in features.items():
        if not isinstance(feature_raw, dict):
            continue
        for did in _ordered_deliverables(feature_raw):
            scanned += 1
            has_artifact, small_files = _deliverable_artifact_scan(
                project_root=project_root,
                feature_id=feature_id,
                feature=feature_raw,
                deliverable_id=did,
                structure=structure,
            )
            entry = _ensure_feature_deliverable(state_payload, feature_id, did)
            current_status = str(entry.get("status", "pending")).strip() or "pending"

            if has_artifact:
                if current_status != "done" and current_status not in MANUAL_LOCKED_STATUSES:
                    entry["status"] = "done"
                    entry["updated_at"] = now
                    changed += 1
            else:
                if current_status not in MANUAL_LOCKED_STATUSES and current_status != "pending":
                    entry["status"] = "pending"
                    entry["updated_at"] = now
                    changed += 1
                elif "status" not in entry:
                    entry["status"] = "pending"
                    entry["updated_at"] = now
                    changed += 1
                if small_files:
                    warnings += 1
                    samples = ", ".join(small_files[:3])
                    if len(small_files) > 3:
                        samples += f", ... +{len(small_files) - 3}"
                    print(
                        f"WARN: 空の成果物を検知 {feature_id}/{did} "
                        f"(10 bytes 未満): {samples}"
                    )

    meta = state_payload.setdefault("_meta", {})
    if isinstance(meta, dict):
        meta["generated_at"] = now

    _write_json(state_path, state_payload)
    print(f"auto-detect: {changed} 更新 / {scanned} deliverables, warnings={warnings}")


def compile_matrix(project_root: Path, force_state: bool = False) -> None:
    cli_root = Path(__file__).resolve().parents[1]
    helix_dir = project_root / ".helix"
    if not helix_dir.exists():
        raise MatrixError(f".helix が見つかりません: {helix_dir}")

    matrix = _load_matrix(project_root)
    deliverables_rules, structure, naming, common_defs = _read_rules(project_root, cli_root)
    validate_matrix(matrix, deliverables_rules, naming)

    generated_at = _now_iso()
    doc_map = build_doc_map(matrix, deliverables_rules, structure)
    framework = _load_framework(project_root)
    gate_checks = build_gate_checks(matrix, deliverables_rules, structure, framework=framework)
    state = build_state(matrix, generated_at)
    runtime_index = build_runtime_index(
        matrix=matrix,
        deliverables_rules=deliverables_rules,
        structure=structure,
        naming=naming,
        common_defs=common_defs,
        generated_at=generated_at,
    )

    doc_map_path = helix_dir / "doc-map.yaml"
    gate_checks_path = helix_dir / "gate-checks.yaml"
    state_path = helix_dir / "state" / "deliverables.json"
    runtime_index_path = helix_dir / "runtime" / "index.json"

    _write_text(doc_map_path, dump_doc_map_yaml(doc_map))
    _write_text(gate_checks_path, dump_gate_checks_yaml(gate_checks))

    if state_path.exists() and not force_state:
        print("state/deliverables.json は既存のため上書きしません（--force で上書き）")
    else:
        _write_json(state_path, state)
        print(f"生成: {state_path}")

    _write_json(runtime_index_path, runtime_index)
    print(f"生成: {doc_map_path}")
    print(f"生成: {gate_checks_path}")
    print(f"生成: {runtime_index_path}")


def validate_only(project_root: Path) -> None:
    cli_root = Path(__file__).resolve().parents[1]
    matrix = _load_matrix(project_root)
    deliverables_rules, _structure, naming, _common_defs = _read_rules(project_root, cli_root)
    validate_matrix(matrix, deliverables_rules, naming)
    print("OK: matrix.yaml は有効です")


def status_matrix(project_root: Path) -> None:
    matrix = _load_matrix(project_root)
    helix_dir = project_root / ".helix"
    state_path = helix_dir / "state" / "deliverables.json"

    state_payload: dict[str, Any] = {}
    if state_path.exists():
        try:
            state_payload = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise MatrixError(f"state/deliverables.json の JSON が不正です: {exc}") from exc

    state_features = state_payload.get("features", {}) if isinstance(state_payload, dict) else {}
    if not isinstance(state_features, dict):
        state_features = {}

    features = matrix.get("features", {})
    if not isinstance(features, dict):
        raise MatrixError("matrix.features が辞書ではありません")

    print("=== HELIX Matrix Status ===")
    for feature_id, feature_raw in features.items():
        if not isinstance(feature_raw, dict):
            continue
        print(f"[{feature_id}]")
        ordered = _ordered_deliverables(feature_raw)
        state_deliverables = {}
        feature_state = state_features.get(feature_id, {})
        if isinstance(feature_state, dict):
            state_deliverables = feature_state.get("deliverables", {})
        if not isinstance(state_deliverables, dict):
            state_deliverables = {}

        for did in ordered:
            entry = state_deliverables.get(did, {})
            status = "pending"
            updated_at = "-"
            if isinstance(entry, dict):
                status = str(entry.get("status", "pending"))
                updated_raw = entry.get("updated_at")
                updated_at = str(updated_raw) if updated_raw else "-"
            print(f"  - {did:<14} {status:<12} {updated_at}")
        print("")

    if not state_path.exists():
        print("注記: state/deliverables.json が未作成です。`helix matrix compile` を実行してください。")


def detect_project_root(arg_value: str | None) -> Path:
    if arg_value:
        return Path(arg_value).resolve()
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path.cwd().resolve()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HELIX matrix compiler")
    parser.add_argument(
        "--project-root",
        default=None,
        help="対象プロジェクトのルート。未指定時は HELIX_PROJECT_ROOT またはカレントディレクトリ",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser = subparsers.add_parser("compile", help="matrix/rules から派生ファイルを生成")
    compile_parser.add_argument("--force", action="store_true", help="state/deliverables.json を上書き")

    subparsers.add_parser("validate", help="matrix.yaml の構造検証")
    subparsers.add_parser("status", help="feature x deliverable の状態表示")
    subparsers.add_parser("auto-detect", help="実ファイルから deliverable state を自動更新")
    add_feature_parser = subparsers.add_parser(
        "add-feature",
        help="matrix.yaml に feature を追加し、compile を実行",
    )
    add_feature_parser.add_argument("name", help="feature id (kebab-case)")
    add_feature_parser.add_argument(
        "--drive",
        required=True,
        choices=["be", "fe", "db", "fullstack", "agent"],
        help="駆動タイプ",
    )
    add_feature_parser.add_argument(
        "--scope",
        default="feature",
        choices=["feature", "shared", "platform"],
        help="スコープ種別",
    )
    add_feature_parser.add_argument(
        "--ui",
        action="store_true",
        help="UI deliverables（L5）を含める",
    )
    add_feature_parser.add_argument(
        "--risk",
        default="",
        help="risk flag（カンマ区切り）",
    )
    update_parser = subparsers.add_parser("update", help="deliverable state を手動更新")
    update_parser.add_argument("--feature", required=True, help="feature id")
    update_parser.add_argument("--deliverable", required=True, help="deliverable id (D-*)")
    update_parser.add_argument(
        "--status",
        required=True,
        choices=["done", "waived", "not_applicable", "in_progress"],
        help="更新後ステータス",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    project_root = detect_project_root(args.project_root)

    try:
        if args.command == "compile":
            compile_matrix(project_root, force_state=bool(args.force))
        elif args.command == "validate":
            validate_only(project_root)
        elif args.command == "status":
            status_matrix(project_root)
        elif args.command == "auto-detect":
            auto_detect_state(project_root)
        elif args.command == "add-feature":
            add_matrix_feature(
                project_root=project_root,
                name=str(args.name),
                drive=str(args.drive),
                scope=str(args.scope),
                ui=bool(args.ui),
                risk=str(args.risk),
            )
        elif args.command == "update":
            update_matrix_state(
                project_root=project_root,
                feature_id=str(args.feature),
                deliverable_id=str(args.deliverable),
                status=str(args.status),
            )
        else:
            parser.print_help()
            return 1
        return 0
    except MatrixError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
