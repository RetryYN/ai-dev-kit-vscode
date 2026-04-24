#!/usr/bin/env python3
"""HELIX phase guard checker.

責務: 現在フェーズと変更パスを照合し、違反変更をブロックする。

3 層ガードレールアーキテクチャ:
  Layer 1 (Input Guard):
    - フェーズ違反チェック（現在の実装）
    - 未サイジング検出
    - 除外パス判定

  Layer 2 (Process Guard): [将来拡張]
    - 実行中のリソース制限
    - トークン消費上限
    - 実行時間制限

  Layer 3 (Output Guard): [将来拡張]
    - 生成物の品質チェック
    - 安全性チェック（秘密情報混入防止）
    - 契約整合チェック

Usage:
  python3 phase_guard.py --phase-file <path> --file <rel_or_abs_path> [--index <path>]

Exit code:
  0 = allow
  1 = blocked
"""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from yaml_parser import get_nested, parse_yaml

LAYER_ORDER = {f"L{i}": i for i in range(1, 9)}
UNKNOWN_LAYER = "unknown"

GATE_NAMES = {
    "G0.5": "企画突合ゲート",
    "G1": "要件完了ゲート",
    "G2": "設計凍結ゲート",
    "G3": "実装着手ゲート",
    "G4": "実装凍結ゲート",
    "G5": "デザイン凍結ゲート",
    "G6": "RC判定ゲート",
    "G7": "安定性ゲート",
}

LAYER_REQUIRED_GATE = {
    2: "G1",
    3: "G2",
    4: "G3",
    5: "G4",
    6: "G4",
    7: "G6",
    8: "G7",
}

DELIVERABLE_ID_RE = re.compile(r"^(D-[A-Z0-9]+(?:-[A-Z0-9]+)*)")
DOCS_SCOPE_RE = re.compile(r"^docs/(features|shared|platform)/[^/]+(?:/(.*))?$")
SRC_SCOPE_RE = re.compile(r"^src/(features|shared|platform)/[^/]+(?:/(.*))?$")
TEST_FILE_RE = re.compile(r"(^|/)[^/]+\.(?:test|spec)\.[^/]+$", re.IGNORECASE)

EXEMPT_PREFIXES = (
    ".helix/",
    "docs/adr/",
    "docs/debt/",
    "node_modules/",
    "vendor/",
    "dist/",
    "build/",
)

EXEMPT_ROOT_FILES = {
    "README.md",
    "CLAUDE.md",
    ".gitignore",
    ".env.example",
}

STATIC_DELIVERABLE_LAYER = {
    "D-ACC": "L1",
    "D-RES": "L1",
    "D-ARCH": "L2",
    "D-ADR": "L2",
    "D-THREAT": "L2",
    "D-VIS-ARCH": "L2",
    "D-DATA-ARCH": "L2",
    "D-ORCH-ARCH": "L2",
    "D-API": "L3",
    "D-CONTRACT": "L3",
    "D-DB": "L3",
    "D-MIG-PLAN": "L3",
    "D-DEP": "L3",
    "D-TEST": "L3",
    "D-PLAN": "L3",
    "D-STATE": "L3",
    "D-UI": "L3",
    "D-API-CONS": "L3",
    "D-DATA-ACCESS": "L3",
    "D-TOOL": "L3",
    "D-PROMPT": "L3",
    "D-EVAL-PLAN": "L3",
    "D-IMPL": "L4",
    "D-MIG": "L4",
    "D-CONFIG": "L4",
    "D-VIS": "L5",
    "D-A11Y": "L5",
    "D-UX-SIGNOFF": "L5",
    "D-DEMO": "L5",
    "D-E2E": "L6",
    "D-PERF": "L6",
    "D-SECV": "L6",
    "D-OPS": "L6",
    "D-A11Y-VERIFY": "L6",
    "D-DATA-VERIFY": "L6",
    "D-EVAL": "L6",
    "D-DEPLOY": "L7",
    "D-RELNOTE": "L7",
    "D-OBS": "L7",
    "D-UAT": "L8",
    "D-HANDOVER": "L8",
    "D-RETRO": "L8",
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


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} のトップレベルがオブジェクトではありません")
    return payload


def _load_phase(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    payload = parse_yaml(text)
    if not isinstance(payload, dict):
        raise ValueError("phase.yaml の形式が不正です")
    return payload


def _status(value: Any) -> str:
    if value is None:
        return "pending"
    return str(value).strip().lower()


def _is_guard_exempt(rel_path: str) -> bool:
    if not rel_path:
        return True

    if TEST_FILE_RE.search(rel_path):
        return True

    if rel_path in EXEMPT_ROOT_FILES:
        return True

    for prefix in EXEMPT_PREFIXES:
        if rel_path.startswith(prefix):
            return True
    return False


def _extract_deliverable_id(remainder: str | None) -> str | None:
    if not remainder:
        return None
    segment = remainder.split("/", 1)[0]
    m = DELIVERABLE_ID_RE.match(segment.upper())
    if not m:
        return None
    return m.group(1)


def _fallback_deliverable_layer(deliverable_id: str) -> str | None:
    if deliverable_id.startswith("D-REQ-"):
        return "L1"
    return STATIC_DELIVERABLE_LAYER.get(deliverable_id)


def _resolve_deliverable_layer(deliverable_id: str, catalog_layers: dict[str, str]) -> tuple[str | None, str]:
    layer = catalog_layers.get(deliverable_id)
    if layer:
        return layer, "catalog"
    fallback = _fallback_deliverable_layer(deliverable_id)
    if fallback:
        return fallback, "static"
    return None, UNKNOWN_LAYER


def _load_catalog_layers(index_path: Path | None) -> dict[str, str]:
    if index_path is None or not index_path.exists():
        return {}

    payload = _load_json(index_path)

    rules = payload.get("rules", {})
    if not isinstance(rules, dict):
        return {}

    items = rules.get("deliverables", [])
    if not isinstance(items, list):
        return {}

    out: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        did = item.get("id")
        layer = item.get("layer")
        if isinstance(did, str) and isinstance(layer, str) and layer in LAYER_ORDER:
            out[did] = layer
    return out


def _infer_layer(rel_path: str, catalog_layers: dict[str, str]) -> str | None:
    docs_match = DOCS_SCOPE_RE.match(rel_path)
    if docs_match:
        did = _extract_deliverable_id(docs_match.group(2))
        if did:
            layer, source = _resolve_deliverable_layer(did, catalog_layers)
            if source == UNKNOWN_LAYER:
                return UNKNOWN_LAYER
            return layer

    src_match = SRC_SCOPE_RE.match(rel_path)
    if src_match:
        did = _extract_deliverable_id(src_match.group(2))
        if did:
            layer, source = _resolve_deliverable_layer(did, catalog_layers)
            if source == UNKNOWN_LAYER:
                return UNKNOWN_LAYER
            return layer
        return catalog_layers.get("D-IMPL", "L4")

    if re.match(r"^docs/design/L2-[^/]+", rel_path):
        return "L2"
    if re.match(r"^docs/design/L3-[^/]+", rel_path):
        return "L3"
    if re.match(r"^docs/design/L5-[^/]+", rel_path):
        return "L5"
    if rel_path.startswith("src/"):
        return "L4"

    return None


def _compute_allowed_layer(current_phase: str, phase_data: dict[str, Any]) -> int:
    allowed = LAYER_ORDER.get(current_phase, 1)

    gate_status = {
        "G0.5": _status(get_nested(phase_data, "gates.G0.5.status")),
        "G1": _status(get_nested(phase_data, "gates.G1.status")),
        "G2": _status(get_nested(phase_data, "gates.G2.status")),
        "G3": _status(get_nested(phase_data, "gates.G3.status")),
        "G4": _status(get_nested(phase_data, "gates.G4.status")),
        "G5": _status(get_nested(phase_data, "gates.G5.status")),
        "G6": _status(get_nested(phase_data, "gates.G6.status")),
        "G7": _status(get_nested(phase_data, "gates.G7.status")),
    }

    if current_phase == "L1":
        allowed = max(allowed, 1)
    if gate_status["G1"] == "passed":
        allowed = max(allowed, 2)
    if gate_status["G2"] == "passed":
        allowed = max(allowed, 3)
    if gate_status["G3"] == "passed":
        allowed = max(allowed, 4)
    if gate_status["G4"] == "passed":
        allowed = max(allowed, 6)
    if gate_status["G5"] in {"passed", "skipped"}:
        allowed = max(allowed, 6)
    if gate_status["G6"] == "passed":
        allowed = max(allowed, 7)
    if gate_status["G7"] == "passed":
        allowed = max(allowed, 8)

    return min(max(allowed, 1), 8)


def _block_phase_violation(target_layer: str, current_phase: str, required_gate: str | None) -> int:
    print(
        f"[helix-guard] ❌ フェーズ違反: {target_layer} の成果物を変更しようとしていますが、現在 {current_phase} です"
    )
    if required_gate:
        gate_name = GATE_NAMES.get(required_gate, "必要ゲート")
        print(f"[helix-guard]   必要なゲート: {required_gate} ({gate_name})")
        print(
            f"[helix-guard]   'helix gate {required_gate}' を通過してから {target_layer} に進んでください"
        )
    return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HELIX phase guard checker")
    parser.add_argument("--phase-file", required=True, help="path to .helix/phase.yaml")
    parser.add_argument("--file", required=True, help="changed file path (relative or absolute)")
    parser.add_argument("--index", help="path to .helix/runtime/index.json")
    return parser.parse_args()


def _log_guard_error(label: str, path: Path | None, exc: Exception) -> None:
    location = str(path) if path is not None else "(unknown)"
    print(f"[helix-guard] ERROR: {label} 読み込み失敗 ({location}): {exc}", file=sys.stderr)


def main() -> int:
    try:
        args = parse_args()
    except SystemExit:
        return 0

    phase_path = Path(args.phase_file)
    if not phase_path.exists():
        return 0

    try:
        phase_data = _load_phase(phase_path)
    except (FileNotFoundError, OSError):
        raise
    except (json.JSONDecodeError, ValueError) as exc:
        _log_guard_error("phase.yaml", phase_path, exc)
        return 1
    except Exception as exc:
        _log_guard_error("phase.yaml", phase_path, exc)
        return 1

    project_root = phase_path.resolve().parent.parent
    rel_path = _normalize_rel_path(args.file, project_root)
    if not rel_path:
        return 0

    if _is_guard_exempt(rel_path):
        return 0

    current_phase_raw = get_nested(phase_data, "current_phase")
    current_phase = str(current_phase_raw).strip() if current_phase_raw is not None else ""
    normalized_phase = current_phase.upper()
    is_src_change = rel_path.startswith("src/")

    if normalized_phase in {"", "NULL", "NONE", "~"}:
        if is_src_change:
            print("[helix-guard] ❌ 未サイジング: 実装ファイルを変更する前にサイジングが必要です")
            print("[helix-guard]   'helix size --files N --lines N --type TYPE' を実行してください")
            return 1
        return 0

    index_path = Path(args.index) if args.index else None
    try:
        catalog_layers = _load_catalog_layers(index_path)
    except (FileNotFoundError, OSError):
        raise
    except (json.JSONDecodeError, ValueError) as exc:
        _log_guard_error("index.json", index_path, exc)
        return 1
    except Exception as exc:
        _log_guard_error("index.json", index_path, exc)
        return 1
    try:
        target_layer = _infer_layer(rel_path, catalog_layers)
        if target_layer is None:
            return 0
        if target_layer == UNKNOWN_LAYER:
            return 0

        target_layer_num = LAYER_ORDER.get(target_layer)
        if target_layer_num is None:
            return 0

        phase_for_eval = normalized_phase if normalized_phase in LAYER_ORDER else current_phase
        allowed_layer_num = _compute_allowed_layer(phase_for_eval, phase_data)
        if target_layer_num <= allowed_layer_num:
            return 0

        current_label = phase_for_eval if phase_for_eval in LAYER_ORDER else f"L{allowed_layer_num}"
        required_gate = LAYER_REQUIRED_GATE.get(target_layer_num)
        return _block_phase_violation(target_layer, current_label, required_gate)
    except Exception as exc:
        _log_guard_error("guard", None, exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
