#!/usr/bin/env python3
"""Gate/doc-map generator extracted from matrix_compiler."""

from __future__ import annotations

import re
import shlex
from typing import Any, Callable


def _path_sort_key(gate: str) -> tuple[int, str]:
    m = re.fullmatch(r"G(\d+)", gate)
    if m:
        return (int(m.group(1)), gate)
    return (999, gate)


def _escape_yaml_double(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _resolved_primary(resolved: Any) -> str | None:
    if isinstance(resolved, dict):
        raw = resolved.get("primary")
    else:
        raw = getattr(resolved, "primary", None)
    return raw if isinstance(raw, str) and raw else None


def _resolved_capture(resolved: Any) -> list[str]:
    if isinstance(resolved, dict):
        raw = resolved.get("capture", [])
    else:
        raw = getattr(resolved, "capture", [])
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if isinstance(item, str)]


def _build_static_check(name: str, cmd: str) -> dict[str, str]:
    return {"name": name, "cmd": cmd}


def _build_ai_check(role: str, task: str) -> dict[str, str]:
    return {"role": role, "task": task}


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
    resolve_paths: Callable[[str, dict[str, Any], str, dict[str, Any]], Any],
) -> str | None:
    candidates: list[str] = []
    for key in ("L3", "L2"):
        ids = requires.get(key)
        if isinstance(ids, list):
            candidates.extend([str(x) for x in ids if isinstance(x, str)])

    priority = ["D-API", "D-ARCH", "D-DB", "D-TEST", "D-PLAN", "D-ADR"]
    for did in priority:
        if did in candidates:
            resolved = resolve_paths(feature_id, feature, did, structure)
            primary = _resolved_primary(resolved)
            if primary:
                return primary
    if candidates:
        resolved = resolve_paths(feature_id, feature, candidates[0], structure)
        primary = _resolved_primary(resolved)
        if primary:
            return primary
    return None


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
        checks.append(_build_static_check(f"framework {detected} {label}", f"{cmd} >/dev/null 2>&1"))
    return checks


def _build_policy_g4_checks() -> list[dict[str, str]]:
    return [
        _build_static_check(
            "技術負債台帳の存在",
            "test -f .helix/debt-register.yaml || echo 'SKIP: 負債台帳なし（helix debt add で作成）'",
        ),
        _build_static_check(
            "要件→実装マッピング存在（あれば）",
            (
                "python3 -c \"import sqlite3,sys; c=sqlite3.connect('.helix/helix.db'); "
                "r=c.execute('SELECT COUNT(*) FROM requirements').fetchone()[0]; "
                "m=c.execute('SELECT COUNT(*) FROM req_impl_map').fetchone()[0]; "
                "print(f'REQ:{r} MAP:{m}'); sys.exit(0 if r==0 or m>=r else 1)\" "
                "2>/dev/null || echo 'SKIP: 要件テーブルなし'"
            ),
        ),
        _build_static_check("API エンドポイント整合チェック", "$HELIX_HOME/cli/helix-gate-api-check"),
        _build_static_check(
            "テストカバレッジ（あれば）",
            (
                "if [ -f coverage/coverage-summary.json ]; then "
                "python3 -c \"import json; d=json.load(open('coverage/coverage-summary.json')); "
                "pct=d.get('total',{}).get('lines',{}).get('pct',0); exit(0 if pct>=70 else 1)\"; "
                "elif [ -f .coverage ]; then echo 'coverage exists'; "
                "else echo 'SKIP: カバレッジ未計測'; fi"
            ),
        ),
        _build_static_check(
            "モック/ダミー残存チェック",
            (
                "! rg -n '(?i)(localhost:[0-9]|mock-api|dummy-data|FIXME|TODO.*mock)' src/ "
                "--type ts --type js --type tsx --type jsx 2>/dev/null "
                "| grep -v '.*\\.test\\.' | grep -v '.*\\.spec\\.' | head -1"
            ),
        ),
        _build_static_check(
            "console.log/debugger 残存チェック",
            (
                "! rg -n '^\\s*(console\\.(log|debug|warn|error)|debugger)' src/ "
                "--type ts --type js --type tsx --type jsx 2>/dev/null "
                "| grep -v '.*\\.test\\.' | grep -v '.*\\.spec\\.' | head -1"
            ),
        ),
        _build_static_check(
            "開発用語の UI 露出チェック",
            (
                "! rg -n '(Exception|NullPointerException|undefined is not|Cannot read prop|Stack trace|Error:.*at )' src/ "
                "--type ts --type js --type tsx --type jsx 2>/dev/null "
                "| grep -v 'catch\\|throw\\|Error(' | head -1"
            ),
        ),
        _build_static_check(
            "AI っぽい出力チェック",
            (
                "! rg -n '(もちろんです|お手伝いします|ご質問にお答えします|As an AI|I apologize)' src/ "
                "--type ts --type js --type tsx --type jsx 2>/dev/null | head -1"
            ),
        ),
        _build_static_check(
            "ハードコード URL チェック",
            (
                "! rg -n 'https?://(localhost|127\\.0\\.0\\.1|0\\.0\\.0\\.0)' src/ "
                "--type ts --type js --type tsx --type jsx 2>/dev/null "
                "| grep -v '.*\\.test\\.' | grep -v 'env\\.' | head -1"
            ),
        ),
        _build_static_check(
            "CSS マジックナンバーチェック",
            "! rg -n 'z-index:\\s*[0-9]{3,}' src/ --type css 2>/dev/null | head -1",
        ),
    ]


def _apply_security_checks(gates: dict[str, dict[str, Any]], static_seen: dict[str, set[str]]) -> None:
    g4_bucket = gates.setdefault("G4", {"name": _gate_name("G4"), "static": [], "ai": []})
    static_seen.setdefault("G4", set())
    for check in _build_policy_g4_checks():
        cmd = check.get("cmd", "")
        if cmd in static_seen["G4"]:
            continue
        static_seen["G4"].add(cmd)
        g4_bucket["static"].append(check)


def _apply_framework_checks(
    gates: dict[str, dict[str, Any]],
    static_seen: dict[str, set[str]],
    framework: dict[str, Any] | None,
) -> None:
    g4_bucket = gates.setdefault("G4", {"name": _gate_name("G4"), "static": [], "ai": []})
    static_seen.setdefault("G4", set())
    for check in _build_framework_checks(framework):
        cmd = check.get("cmd", "")
        if cmd in static_seen["G4"]:
            continue
        static_seen["G4"].add(cmd)
        g4_bucket["static"].append(check)


def _apply_fe_checks(
    gates: dict[str, dict[str, Any]],
    static_seen: dict[str, set[str]],
    matrix: dict[str, Any],
) -> None:
    _ = gates
    _ = static_seen
    _ = matrix


def _generate_doc_map(
    matrix: dict[str, Any],
    deliverables_rules: dict[str, Any],
    structure: dict[str, Any],
    *,
    catalog_index: Callable[[dict[str, Any]], dict[str, dict[str, Any]]],
    resolve_paths: Callable[[str, dict[str, Any], str, dict[str, Any]], Any],
    d_contract_doc_pattern: Callable[[str, dict[str, Any], dict[str, Any]], str],
) -> dict[str, Any]:
    features = matrix.get("features", {})
    if not isinstance(features, dict):
        raise ValueError("matrix.features が辞書ではありません")

    catalog = catalog_index(deliverables_rules)
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
                    pattern = d_contract_doc_pattern(feature_id, feature_raw, structure)
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

                resolved = resolve_paths(feature_id, feature_raw, did, structure)
                primary = _resolved_primary(resolved)
                capture = _resolved_capture(resolved)
                if layer == "L4":
                    pattern = capture[0] if capture else primary
                    design_ref = _choose_design_ref(
                        feature_id,
                        feature_raw,
                        requires,
                        structure,
                        resolve_paths,
                    )
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
                    pattern = primary or (capture[0] if capture else None)
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


def build_doc_map(
    matrix: dict[str, Any],
    deliverables_rules: dict[str, Any],
    structure: dict[str, Any],
    *,
    catalog_index: Callable[[dict[str, Any]], dict[str, dict[str, Any]]],
    resolve_paths: Callable[[str, dict[str, Any], str, dict[str, Any]], Any],
    d_contract_doc_pattern: Callable[[str, dict[str, Any], dict[str, Any]], str],
) -> dict[str, Any]:
    return _generate_doc_map(
        matrix,
        deliverables_rules,
        structure,
        catalog_index=catalog_index,
        resolve_paths=resolve_paths,
        d_contract_doc_pattern=d_contract_doc_pattern,
    )


def _generate_gate_checks(
    matrix: dict[str, Any],
    deliverables_rules: dict[str, Any],
    structure: dict[str, Any],
    framework: dict[str, Any] | None = None,
    *,
    catalog_index: Callable[[dict[str, Any]], dict[str, dict[str, Any]]],
    resolve_paths: Callable[[str, dict[str, Any], str, dict[str, Any]], Any],
    d_contract_doc_pattern: Callable[[str, dict[str, Any], dict[str, Any]], str],
) -> dict[str, Any]:
    catalog = catalog_index(deliverables_rules)
    features = matrix.get("features", {})
    if not isinstance(features, dict):
        raise ValueError("matrix.features が辞書ではありません")

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

                resolved = resolve_paths(feature_id, feature_raw, did, structure)
                primary = _resolved_primary(resolved)
                capture = _resolved_capture(resolved)
                target_path = primary or (capture[0] if capture else None)

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

                        if vtype == "exists" and target_path:
                            cmd = _build_exists_cmd(target_path)
                            if cmd not in static_seen[gate]:
                                static_seen[gate].add(cmd)
                                bucket["static"].append(_build_static_check(f"{feature_id} {did} 存在", cmd))
                        elif vtype == "heading_check" and target_path:
                            required = params.get("required", [])
                            headings = [str(h) for h in required] if isinstance(required, list) else []
                            if headings:
                                cmd = _build_heading_cmd(target_path, headings)
                                if cmd not in static_seen[gate]:
                                    static_seen[gate].add(cmd)
                                    bucket["static"].append(
                                        _build_static_check(f"{feature_id} {did} 見出しチェック", cmd)
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
                                bucket["ai"].append(_build_ai_check(role, task))

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
                        cmd = _build_exists_cmd(d_contract_doc_pattern(feature_id, feature_raw, structure))
                    else:
                        resolved = resolve_paths(feature_id, feature_raw, did_raw, structure)
                        primary = _resolved_primary(resolved)
                        if not primary:
                            continue
                        cmd = _build_file_cmd(primary)
                    cmd_key = f"deliverable_file::{cmd}"
                    if cmd_key in static_seen[gate]:
                        continue
                    static_seen[gate].add(cmd_key)
                    bucket["static"].append(_build_static_check(f"{feature_id} {did_raw} file", cmd))

    _apply_security_checks(gates, static_seen)
    _apply_framework_checks(gates, static_seen, framework)
    _apply_fe_checks(gates, static_seen, matrix)
    return {gate: gates[gate] for gate in sorted(gates.keys(), key=_path_sort_key)}


def build_gate_checks(
    matrix: dict[str, Any],
    deliverables_rules: dict[str, Any],
    structure: dict[str, Any],
    framework: dict[str, Any] | None = None,
    *,
    catalog_index: Callable[[dict[str, Any]], dict[str, dict[str, Any]]],
    resolve_paths: Callable[[str, dict[str, Any], str, dict[str, Any]], Any],
    d_contract_doc_pattern: Callable[[str, dict[str, Any], dict[str, Any]], str],
) -> dict[str, Any]:
    return _generate_gate_checks(
        matrix,
        deliverables_rules,
        structure,
        framework=framework,
        catalog_index=catalog_index,
        resolve_paths=resolve_paths,
        d_contract_doc_pattern=d_contract_doc_pattern,
    )


def dump_doc_map_yaml(doc_map: dict[str, Any], helix_template_version: int = 3) -> str:
    lines: list[str] = []
    lines.append("# doc-map.yaml — matrix compile generated")
    lines.append(f"# helix_template_version: {helix_template_version}")
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


def dump_gate_checks_yaml(gate_checks: dict[str, Any], helix_template_version: int = 3) -> str:
    lines: list[str] = []
    lines.append("# gate-checks.yaml — matrix compile generated")
    lines.append(f"# helix_template_version: {helix_template_version}")
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
