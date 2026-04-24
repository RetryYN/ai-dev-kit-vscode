"""model_fallback.py — 枯渇モデルからの降格提案。

詳細: docs/features/helix-budget-autothinking/D-ADR/adr.md §ADR-004
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

HELIX_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HELIX_ROOT / "cli" / "lib"))

try:
    from yaml_parser import load_yaml  # type: ignore
except ImportError:
    try:
        from matrix_compiler import load_yaml as _matrix_load_yaml  # type: ignore
    except ImportError:
        _matrix_load_yaml = None

    try:
        from yaml_parser import parse_yaml as _parse_yaml  # type: ignore
    except ImportError:
        _parse_yaml = None

    def load_yaml(path: str | Path) -> Any:
        import json
        p = Path(path)
        text = p.read_text(encoding="utf-8")
        if p.suffix in (".json",):
            return json.loads(text)
        if _matrix_load_yaml is not None:
            return _matrix_load_yaml(p)
        if _parse_yaml is not None:
            return _parse_yaml(text)
        raise RuntimeError("yaml_parser not available")


DEFAULT_RULES = [
    {
        "model": "gpt-5.3-codex-spark",
        "same_tier": ["gpt-5.4-mini"],
        "upgrade": ["gpt-5.3-codex"],
        "trigger_pct": 90,
        "note": "Spark 枯渇時、軽量タスクは 5.4-mini、実装系は 5.3 昇格",
    },
    {
        "model": "gpt-5.3-codex",
        "same_tier": [],
        "upgrade": ["gpt-5.4"],
        "downgrade_small": ["gpt-5.3-codex-spark"],
        "trigger_pct": 90,
        "note": "5.3 枯渇時、雑/判断多は 5.4、S 純粋実装は Spark",
    },
    {
        "model": "gpt-5.4",
        "hold": True,
        "trigger_pct": 95,
        "note": "5.4 は原則降格しない、タスク保留推奨",
    },
]


def load_rules(yaml_path: str | Path | None = None) -> list[dict]:
    if yaml_path is None:
        candidates = [
            Path.home() / ".config" / "helix" / "model-fallback.yaml",
            HELIX_ROOT / "cli" / "config" / "model-fallback.yaml",
        ]
        for c in candidates:
            if c.exists():
                yaml_path = c
                break
    if yaml_path is None:
        return DEFAULT_RULES
    try:
        data = load_yaml(yaml_path)
        rules = data.get("rules") if isinstance(data, dict) else None
        if isinstance(rules, list):
            return rules
    except FileNotFoundError:
        return DEFAULT_RULES
    except Exception as exc:
        print(f"WARN: fallback rules 読込失敗 ({yaml_path}): {exc}", file=sys.stderr)
    return DEFAULT_RULES


def suggest_model(
    current_model: str,
    budget_snapshot: dict | None = None,
    effort: str = "medium",
    size: str = "M",
) -> dict[str, Any]:
    rules = load_rules()
    matched = next((r for r in rules if r.get("model") == current_model), None)
    if matched is None:
        return {
            "recommended_model": current_model,
            "original_model": current_model,
            "fallback_applied": False,
            "reason": "ルール未定義、現行維持",
        }

    if matched.get("hold"):
        return {
            "recommended_model": current_model,
            "original_model": current_model,
            "fallback_applied": False,
            "reason": matched.get("note", "hold policy"),
        }

    pct = 0
    if budget_snapshot:
        codex_pct = budget_snapshot.get("codex", {}).get("weekly_used_pct", 0)
        by_model = budget_snapshot.get("codex", {}).get("by_model", {})
        model_info = by_model.get(current_model, {})
        pct = max(codex_pct, int(model_info.get("used_pct", 0)))

    if pct < matched.get("trigger_pct", 90):
        return {
            "recommended_model": current_model,
            "original_model": current_model,
            "fallback_applied": False,
            "reason": f"残量十分 ({pct}% < {matched['trigger_pct']}%)",
        }

    if size == "S" and matched.get("downgrade_small"):
        target = matched["downgrade_small"][0]
        return {
            "recommended_model": target,
            "original_model": current_model,
            "fallback_applied": True,
            "reason": f"{current_model} 消費 {pct}% + S タスク → {target} に降格",
        }

    if effort in ("high", "xhigh") and matched.get("upgrade"):
        target = matched["upgrade"][0]
        return {
            "recommended_model": target,
            "original_model": current_model,
            "fallback_applied": True,
            "reason": f"{current_model} 消費 {pct}% + effort={effort} → {target} 昇格",
        }

    if matched.get("same_tier"):
        target = matched["same_tier"][0]
        return {
            "recommended_model": target,
            "original_model": current_model,
            "fallback_applied": True,
            "reason": f"{current_model} 消費 {pct}% → 同tier {target} に降格",
        }

    return {
        "recommended_model": current_model,
        "original_model": current_model,
        "fallback_applied": False,
        "reason": "代替ルール未定義",
    }
