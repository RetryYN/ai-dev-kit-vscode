"""effort_classifier.py — タスク難度 → effort (low/medium/high/xhigh) 自動判定。

Minimum Viable: ルールベース (5 軸ヒューリスティック)。LLM 呼び出しは後続スプリントで追加。
詳細: docs/features/helix-budget-autothinking/D-API/api-contract.yaml §helix budget classify
"""
from __future__ import annotations

import re
from typing import Any

_BUG_FIX = re.compile(r"\b(bug|fix|typo|patch|誤字|修正)\b", re.IGNORECASE)
_NEW_DESIGN = re.compile(r"\b(新規|設計|architect|design|ADR)\b", re.IGNORECASE)
_API_DB = re.compile(r"\b(API|DB|migration|schema|endpoint|table)\b", re.IGNORECASE)
_TEST = re.compile(r"\b(test|テスト|E2E|regression|回帰)\b", re.IGNORECASE)
_CROSS = re.compile(r"\b(refactor|横断|cross|multi|複数モジュール)\b", re.IGNORECASE)


def _files_score(files: int | None) -> int:
    if files is None or files <= 0:
        return 1
    if files <= 2:
        return 1
    if files <= 5:
        return 2
    if files <= 10:
        return 3
    return 4


def score_task(
    task_text: str,
    role: str | None = None,
    size: str | None = None,
    files: int | None = None,
    lines: int | None = None,
) -> dict[str, Any]:
    text = task_text or ""
    breakdown = {
        "files": _files_score(files),
        "cross_module": 2 if _CROSS.search(text) else 1,
        "spec_understanding": 1 if _BUG_FIX.search(text) else (3 if _NEW_DESIGN.search(text) else 2),
        "side_effect": 4 if re.search(r"migration|migrate", text, re.IGNORECASE)
                        else (2 if _API_DB.search(text) else 0),
        "test_complexity": 2 if _TEST.search(text) else 1,
    }
    total = sum(breakdown.values())
    if size == "L":
        total = max(total, 8)
    elif size == "S":
        total = min(total, 7)
    if lines and lines > 500:
        total += 2
    return {"score": total, "breakdown": breakdown}


def map_to_effort(score: int) -> str:
    if score <= 3:
        return "low"
    if score <= 7:
        return "medium"
    if score <= 12:
        return "high"
    return "xhigh"


ROLE_DEFAULT_THINKING = {
    "tl": "high", "se": "high", "pg": "medium", "fe": "medium",
    "qa": "medium", "security": "high", "dba": "high", "devops": "high",
    "docs": "medium", "research": "medium", "legacy": "high", "perf": "high",
}


def classify(
    task_text: str,
    role: str | None = None,
    size: str | None = None,
    files: int | None = None,
    lines: int | None = None,
) -> dict[str, Any]:
    scored = score_task(task_text, role, size, files, lines)
    effort = map_to_effort(scored["score"])
    role_default = ROLE_DEFAULT_THINKING.get(role or "", "medium")
    if effort == "low" and role_default in ("high", "xhigh"):
        recommended_thinking = "medium"
    else:
        recommended_thinking = effort if effort != "low" else "low"
    split_recommended = effort == "xhigh" and size == "S"
    reason_bits = []
    b = scored["breakdown"]
    if b["side_effect"] >= 2:
        reason_bits.append(f"side_effect={b['side_effect']}")
    if b["spec_understanding"] >= 3:
        reason_bits.append("新規設計系")
    if b["files"] >= 3:
        reason_bits.append(f"ファイル数 score={b['files']}")
    if split_recommended:
        reason_bits.append("S サイズに xhigh → 分割推奨")
    reason = " / ".join(reason_bits) if reason_bits else "標準難度"

    return {
        "effort": effort,
        "score": scored["score"],
        "breakdown": scored["breakdown"],
        "reason": reason,
        "recommended_thinking": recommended_thinking,
        "split_recommended": split_recommended,
        "role_default_thinking": role_default,
        "cached": False,
    }
