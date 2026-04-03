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
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class MatrixError(Exception):
    """ユーザー向けエラー。"""


VALID_STATE_STATUSES = {"pending", "in_progress", "done", "waived", "not_applicable"}
MANUAL_LOCKED_STATUSES = {"waived", "not_applicable"}
ALLOWED_DRIVES = {"be", "fe", "db", "fullstack", "agent"}
ALLOWED_SCOPES = {"feature", "shared", "platform"}
UI_REQUIRED_DRIVES = {"fe", "fullstack", "agent"}
FEATURE_ID_REGEX_DEFAULT = r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$"
MIN_ARTIFACT_BYTES = 10

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


def _path_sort_key(gate: str) -> tuple[int, str]:
    m = re.match(r"^G(\d+)", gate)
    if m:
        return int(m.group(1)), gate
    return 999, gate


def _escape_yaml_double(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


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


def _select_gate(layer: str, deliverable: dict[str, Any]) -> str | None:
    preferred = {"L2": "G2", "L3": "G3", "L5": "G5"}.get(layer)
    ownership = deliverable.get("gate_ownership")
    gate_list = ownership if isinstance(ownership, list) else []
    if preferred and preferred in gate_list:
        return preferred
    for gate in gate_list:
        if isinstance(gate, str) and re.fullmatch(r"G\d+", gate):
            return gate
    return preferred


def _choose_design_ref(
    feature_id: str,
    feature: dict[str, Any],
    requires: dict[str, Any],
    structure: dict[str, Any],
) -> str | None:
    candidates: list[str] = []
    for key in ("L3", "L2"):
        ids = requires.get(key)
        if isinstance(ids, list):
            candidates.extend([str(x) for x in ids if isinstance(x, str)])

    priority = ["D-API", "D-ARCH", "D-DB", "D-TEST", "D-PLAN", "D-ADR"]
    for did in priority:
        if did in candidates:
            resolved = _resolve_paths(feature_id, feature, did, structure)
            if resolved.primary:
                return resolved.primary
    if candidates:
        resolved = _resolve_paths(feature_id, feature, candidates[0], structure)
        if resolved.primary:
            return resolved.primary
    return None


def build_doc_map(
    matrix: dict[str, Any],
    deliverables_rules: dict[str, Any],
    structure: dict[str, Any],
) -> dict[str, Any]:
    features = matrix.get("features", {})
    if not isinstance(features, dict):
        raise MatrixError("matrix.features が辞書ではありません")

    catalog = _catalog_index(deliverables_rules)
    triggers: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str | None, str | None]] = set()
    for feature_id, feature_raw in features.items():
        if not isinstance(feature_raw, dict):
            continue
        requires = feature_raw.get("requires", {})
        if not isinstance(requires, dict):
            continue

        for layer in ("L2", "L3", "L4", "L5"):
            deliverable_ids = requires.get(layer, [])
            if not isinstance(deliverable_ids, list):
                continue

            for did_raw in deliverable_ids:
                if not isinstance(did_raw, str):
                    continue
                did = did_raw
                if layer == "L3" and did == "D-CONTRACT":
                    pattern = _d_contract_doc_pattern(feature_id, feature_raw, structure)
                    trigger = {
                        "pattern": pattern,
                        "phase": "L3",
                        "on_write": "gate_ready",
                        "gate": "G3",
                    }
                    signature = (pattern, "L3", "gate_ready", "G3", None)
                    if signature in seen:
                        continue
                    seen.add(signature)
                    triggers.append(trigger)
                    continue

                resolved = _resolve_paths(feature_id, feature_raw, did, structure)
                if layer == "L4":
                    pattern = resolved.capture[0] if resolved.capture else resolved.primary
                    design_ref = _choose_design_ref(feature_id, feature_raw, requires, structure)
                    if not pattern or not design_ref:
                        continue
                    trigger = {
                        "pattern": pattern,
                        "phase": "L4",
                        "on_write": "design_sync",
                        "design_ref": design_ref,
                    }
                    signature = (pattern, "L4", "design_sync", None, design_ref)
                else:
                    pattern = resolved.primary or (resolved.capture[0] if resolved.capture else None)
                    if not pattern:
                        continue
                    gate = _select_gate(layer, catalog.get(did, {}))
                    if not gate:
                        continue
                    trigger = {
                        "pattern": pattern,
                        "phase": layer,
                        "on_write": "gate_ready",
                        "gate": gate,
                    }
                    signature = (pattern, layer, "gate_ready", gate, None)

                if signature in seen:
                    continue
                seen.add(signature)
                triggers.append(trigger)

    return {"triggers": triggers}


def _gate_name(gate: str) -> str:
    names = {
        "G2": "設計凍結ゲート",
        "G3": "実装着手ゲート",
        "G4": "実装凍結ゲート",
        "G5": "デザイン凍結ゲート",
        "G6": "RC判定ゲート",
        "G7": "安定性ゲート",
    }
    return names.get(gate, f"{gate} ゲート")

GATE_REQUIRED_LAYERS = {
    "G2": ("L1", "L2"),
    "G3": ("L1", "L2", "L3"),
    "G4": ("L1", "L2", "L3", "L4"),
    "G5": ("L5",),
    "G6": ("L1", "L2", "L3", "L4", "L5", "L6"),
    "G7": ("L1", "L2", "L3", "L4", "L5", "L6", "L7"),
}


def _build_exists_cmd(path: str) -> str:
    if any(ch in path for ch in ("*", "?", "[")):
        return f"ls {path} >/dev/null 2>&1"
    return f"test -e {shlex.quote(path)}"


def _build_file_cmd(path: str) -> str:
    return f"test -f {shlex.quote(path)}"


def _build_heading_cmd(path: str, headings: list[str]) -> str:
    escaped_path = shlex.quote(path)
    checks = [f"grep -q {shlex.quote(h)} {escaped_path}" for h in headings]
    return f"test -f {escaped_path} && " + " && ".join(checks)


def _framework_defaults(detected: str) -> dict[str, str]:
    fw = detected.strip().lower()
    if fw == "python":
        return {
            "lint": "ruff check src/",
            "typecheck": "mypy src/",
            "test": "pytest",
        }
    if fw == "go":
        return {
            "lint": "staticcheck ./...",
            "typecheck": "go vet ./...",
            "test": "go test ./...",
        }
    if fw == "rust":
        return {
            "lint": "cargo clippy -- -D warnings",
            "typecheck": "cargo check",
            "test": "cargo test",
        }
    return {}


def _build_framework_checks(framework: dict[str, Any] | None) -> list[dict[str, str]]:
    if not isinstance(framework, dict):
        return []

    detected_raw = framework.get("detected", "")
    detected = str(detected_raw).strip().lower()
    if detected not in {"python", "go", "rust"}:
        return []

    tools_raw = framework.get("tools")
    tools = tools_raw if isinstance(tools_raw, dict) else {}
    defaults = _framework_defaults(detected)

    checks: list[dict[str, str]] = []
    for key, label in (("lint", "lint"), ("typecheck", "typecheck"), ("test", "test")):
        cmd_raw = tools.get(key, defaults.get(key))
        if not isinstance(cmd_raw, str):
            continue
        cmd = cmd_raw.strip()
        if not cmd:
            continue
        checks.append(
            {
                "name": f"framework {detected} {label}",
                "cmd": f"{cmd} >/dev/null 2>&1",
            }
        )
    return checks


def _build_policy_g4_checks() -> list[dict[str, str]]:
    return [
        {
            "name": "技術負債台帳の存在",
            "cmd": "test -f .helix/debt-register.yaml || echo 'SKIP: 負債台帳なし（helix debt add で作成）'",
        },
        {
            "name": "要件→実装マッピング存在（あれば）",
            "cmd": (
                "python3 -c \"import sqlite3,sys; c=sqlite3.connect('.helix/helix.db'); "
                "r=c.execute('SELECT COUNT(*) FROM requirements').fetchone()[0]; "
                "m=c.execute('SELECT COUNT(*) FROM req_impl_map').fetchone()[0]; "
                "print(f'REQ:{r} MAP:{m}'); sys.exit(0 if r==0 or m>=r else 1)\" "
                "2>/dev/null || echo 'SKIP: 要件テーブルなし'"
            ),
        },
        {
            "name": "API エンドポイント整合チェック",
            "cmd": "$HELIX_HOME/cli/helix-gate-api-check",
        },
        {
            "name": "テストカバレッジ（あれば）",
            "cmd": (
                "if [ -f coverage/coverage-summary.json ]; then "
                "python3 -c \"import json; d=json.load(open('coverage/coverage-summary.json')); "
                "pct=d.get('total',{}).get('lines',{}).get('pct',0); exit(0 if pct>=70 else 1)\"; "
                "elif [ -f .coverage ]; then echo 'coverage exists'; "
                "else echo 'SKIP: カバレッジ未計測'; fi"
            ),
        },
        {
            "name": "モック/ダミー残存チェック",
            "cmd": (
                "! rg -n '(?i)(localhost:[0-9]|mock-api|dummy-data|FIXME|TODO.*mock)' src/ "
                "--type ts --type js --type tsx --type jsx 2>/dev/null "
                "| grep -v '.*\\.test\\.' | grep -v '.*\\.spec\\.' | head -1"
            ),
        },
        {
            "name": "console.log/debugger 残存チェック",
            "cmd": (
                "! rg -n '^\\s*(console\\.(log|debug|warn|error)|debugger)' src/ "
                "--type ts --type js --type tsx --type jsx 2>/dev/null "
                "| grep -v '.*\\.test\\.' | grep -v '.*\\.spec\\.' | head -1"
            ),
        },
        {
            "name": "開発用語の UI 露出チェック",
            "cmd": (
                "! rg -n '(Exception|NullPointerException|undefined is not|Cannot read prop|Stack trace|Error:.*at )' src/ "
                "--type ts --type js --type tsx --type jsx 2>/dev/null "
                "| grep -v 'catch\\|throw\\|Error(' | head -1"
            ),
        },
        {
            "name": "AI っぽい出力チェック",
            "cmd": (
                "! rg -n '(もちろんです|お手伝いします|ご質問にお答えします|As an AI|I apologize)' src/ "
                "--type ts --type js --type tsx --type jsx 2>/dev/null | head -1"
            ),
        },
        {
            "name": "ハードコード URL チェック",
            "cmd": (
                "! rg -n 'https?://(localhost|127\\.0\\.0\\.1|0\\.0\\.0\\.0)' src/ "
                "--type ts --type js --type tsx --type jsx 2>/dev/null "
                "| grep -v '.*\\.test\\.' | grep -v 'env\\.' | head -1"
            ),
        },
        {
            "name": "CSS マジックナンバーチェック",
            "cmd": "! rg -n 'z-index:\\s*[0-9]{3,}' src/ --type css 2>/dev/null | head -1",
        },
    ]


def build_gate_checks(
    matrix: dict[str, Any],
    deliverables_rules: dict[str, Any],
    structure: dict[str, Any],
    framework: dict[str, Any] | None = None,
) -> dict[str, Any]:
    catalog = _catalog_index(deliverables_rules)
    features = matrix.get("features", {})
    if not isinstance(features, dict):
        raise MatrixError("matrix.features が辞書ではありません")

    gates: dict[str, dict[str, Any]] = {}
    static_seen: dict[str, set[str]] = {}
    ai_seen: dict[str, set[tuple[str, str]]] = {}

    for feature_id, feature_raw in features.items():
        if not isinstance(feature_raw, dict):
            continue
        requires = feature_raw.get("requires", {})
        if not isinstance(requires, dict):
            continue

        for deliverable_ids in requires.values():
            if not isinstance(deliverable_ids, list):
                continue
            for did_raw in deliverable_ids:
                if not isinstance(did_raw, str):
                    continue
                did = did_raw
                deliverable = catalog.get(did)
                if not isinstance(deliverable, dict):
                    continue
                gate_ownership = deliverable.get("gate_ownership", [])
                if not isinstance(gate_ownership, list):
                    continue
                validators = deliverable.get("validators", [])
                if not isinstance(validators, list):
                    validators = []

                resolved = _resolve_paths(feature_id, feature_raw, did, structure)
                primary = resolved.primary or (resolved.capture[0] if resolved.capture else None)

                for gate_raw in gate_ownership:
                    if not isinstance(gate_raw, str):
                        continue
                    if not re.fullmatch(r"G\d+", gate_raw):
                        continue
                    gate = gate_raw
                    bucket = gates.setdefault(gate, {"name": _gate_name(gate), "static": [], "ai": []})
                    static_seen.setdefault(gate, set())
                    ai_seen.setdefault(gate, set())

                    for validator in validators:
                        if not isinstance(validator, dict):
                            continue
                        vtype = validator.get("type")
                        params = validator.get("params", {})
                        if not isinstance(params, dict):
                            params = {}

                        if vtype == "exists" and primary:
                            cmd = _build_exists_cmd(primary)
                            if cmd not in static_seen[gate]:
                                static_seen[gate].add(cmd)
                                bucket["static"].append(
                                    {"name": f"{feature_id} {did} 存在", "cmd": cmd}
                                )
                        elif vtype == "heading_check" and primary:
                            required = params.get("required", [])
                            headings = [str(h) for h in required] if isinstance(required, list) else []
                            if headings:
                                cmd = _build_heading_cmd(primary, headings)
                                if cmd not in static_seen[gate]:
                                    static_seen[gate].add(cmd)
                                    bucket["static"].append(
                                        {"name": f"{feature_id} {did} 見出しチェック", "cmd": cmd}
                                    )
                        elif vtype == "ai_review":
                            role = str(params.get("role", "tl"))
                            focus = str(params.get("focus", "成果物整合性"))
                            deliverable_name = str(deliverable.get("name", did))
                            task = (
                                f"{gate} 検証: {feature_id} の {did}（{deliverable_name}）を確認する。"
                                f"観点: {focus}"
                            )
                            signature = (role, task)
                            if signature not in ai_seen[gate]:
                                ai_seen[gate].add(signature)
                                bucket["ai"].append({"role": role, "task": task})

        for gate, layers in GATE_REQUIRED_LAYERS.items():
            if gate == "G5" and not bool(feature_raw.get("ui", False)):
                continue
            bucket = gates.setdefault(gate, {"name": _gate_name(gate), "static": [], "ai": []})
            static_seen.setdefault(gate, set())
            ai_seen.setdefault(gate, set())

            for layer in layers:
                required = requires.get(layer, [])
                if not isinstance(required, list):
                    continue
                for did_raw in required:
                    if not isinstance(did_raw, str):
                        continue
                    if gate == "G3" and did_raw == "D-CONTRACT":
                        cmd = _build_exists_cmd(_d_contract_doc_pattern(feature_id, feature_raw, structure))
                    else:
                        resolved = _resolve_paths(feature_id, feature_raw, did_raw, structure)
                        if not resolved.primary:
                            continue
                        cmd = _build_file_cmd(resolved.primary)
                    cmd_key = f"deliverable_file::{cmd}"
                    if cmd_key in static_seen[gate]:
                        continue
                    static_seen[gate].add(cmd_key)
                    bucket["static"].append(
                        {"name": f"{feature_id} {did_raw} file", "cmd": cmd}
                    )

    g4_bucket = gates.setdefault("G4", {"name": _gate_name("G4"), "static": [], "ai": []})
    static_seen.setdefault("G4", set())
    for check in _build_policy_g4_checks():
        cmd = check.get("cmd", "")
        if cmd in static_seen["G4"]:
            continue
        static_seen["G4"].add(cmd)
        g4_bucket["static"].append(check)
    for check in _build_framework_checks(framework):
        cmd = check.get("cmd", "")
        if cmd in static_seen["G4"]:
            continue
        static_seen["G4"].add(cmd)
        g4_bucket["static"].append(check)

    return {gate: gates[gate] for gate in sorted(gates.keys(), key=_path_sort_key)}


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
    lines: list[str] = []
    lines.append("triggers:")
    triggers = doc_map.get("triggers", [])
    if not isinstance(triggers, list):
        triggers = []
    for item in triggers:
        if not isinstance(item, dict):
            continue
        pattern = _escape_yaml_double(str(item.get("pattern", "")))
        phase = str(item.get("phase", ""))
        on_write = str(item.get("on_write", ""))
        lines.append(f'  - pattern: "{pattern}"')
        lines.append(f"    phase: {phase}")
        lines.append(f"    on_write: {on_write}")
        if "gate" in item:
            lines.append(f"    gate: {item['gate']}")
        if "design_ref" in item:
            design_ref = _escape_yaml_double(str(item["design_ref"]))
            lines.append(f'    design_ref: "{design_ref}"')
    return "\n".join(lines) + "\n"


def dump_gate_checks_yaml(gate_checks: dict[str, Any]) -> str:
    lines: list[str] = []
    for gate in sorted(gate_checks.keys(), key=_path_sort_key):
        entry = gate_checks.get(gate, {})
        if not isinstance(entry, dict):
            continue
        name = _escape_yaml_double(str(entry.get("name", _gate_name(gate))))
        lines.append(f"{gate}:")
        lines.append(f'  name: "{name}"')

        static_items = entry.get("static", [])
        if not isinstance(static_items, list) or not static_items:
            lines.append("  static: []")
        else:
            lines.append("  static:")
            for static in static_items:
                if not isinstance(static, dict):
                    continue
                static_name = _escape_yaml_double(str(static.get("name", "unnamed")))
                static_cmd = _escape_yaml_double(str(static.get("cmd", "true")))
                lines.append(f'    - name: "{static_name}"')
                lines.append(f'      cmd: "{static_cmd}"')

        ai_items = entry.get("ai", [])
        if not isinstance(ai_items, list) or not ai_items:
            lines.append("  ai: []")
        else:
            lines.append("  ai:")
            for ai in ai_items:
                if not isinstance(ai, dict):
                    continue
                role = str(ai.get("role", "tl"))
                task = str(ai.get("task", "")).strip()
                lines.append(f"    - role: {role}")
                lines.append("      task: |")
                if task:
                    for task_line in task.splitlines():
                        lines.append(f"        {task_line}")
                else:
                    lines.append("        (task omitted)")
    return "\n".join(lines) + "\n"


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
