"""effort_classifier.py — タスク難度 → effort (low/medium/high/xhigh) 自動判定。

ルールベース (5 軸ヒューリスティック) + gpt-5.4-mini 境界値判定ハイブリッド。
詳細: docs/features/helix-budget-autothinking/D-API/api-contract.yaml §helix budget classify
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

CACHE_DIR = Path(".helix/budget/cache/classify")
CACHE_TTL_SEC = 3600
BOUNDARY_SCORES = {3, 4, 7, 8, 12, 13}
LLM_TIMEOUT_SEC = 10

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


def _cache_key(task_text: str, role: str | None, size: str | None) -> str:
    payload = f"{task_text}|{role or ''}|{size or ''}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _cache_get(key: str) -> dict[str, Any] | None:
    p = CACHE_DIR / f"{key}.json"
    if not p.exists():
        return None
    if time.time() - p.stat().st_mtime > CACHE_TTL_SEC:
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        data["cached"] = True
        return data
    except (json.JSONDecodeError, OSError):
        return None


def _cache_set(key: str, value: dict[str, Any]) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (CACHE_DIR / f"{key}.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError:
        pass


def call_classifier(
    task_text: str,
    role: str | None = None,
    size: str | None = None,
    files: int | None = None,
    lines: int | None = None,
) -> dict[str, Any] | None:
    codex = shutil.which("codex")
    if not codex:
        return None

    prompt_path = Path(__file__).resolve().parent.parent / "templates" / "effort-classify-prompt.md"
    if not prompt_path.exists():
        return None
    system_prompt = prompt_path.read_text(encoding="utf-8", errors="ignore")

    payload = {"task": task_text[:2000], "role": role, "size": size,
               "files": files, "lines": lines}
    full_prompt = (
        system_prompt
        + "\n\n## 入力\n```json\n"
        + json.dumps(payload, ensure_ascii=False)
        + "\n```\n\n## 出力\nJSON のみを出力 ({\"effort\": \"...\", \"score\": N, ...})。"
    )

    try:
        result = subprocess.run(
            [codex, "exec", "-m", "gpt-5.4-mini", full_prompt],
            capture_output=True, text=True, timeout=LLM_TIMEOUT_SEC,
        )
        if result.returncode != 0:
            return None
        output = result.stdout.strip()
        m = re.search(r"\{[\s\S]*\}", output)
        if not m:
            return None
        parsed = json.loads(m.group(0))
        if "effort" not in parsed:
            return None
        return parsed
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return None


def classify(
    task_text: str,
    role: str | None = None,
    size: str | None = None,
    files: int | None = None,
    lines: int | None = None,
    use_llm: bool = True,
) -> dict[str, Any]:
    key = _cache_key(task_text, role, size)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    scored = score_task(task_text, role, size, files, lines)
    effort = map_to_effort(scored["score"])
    llm_used = False

    if use_llm and scored["score"] in BOUNDARY_SCORES:
        llm_result = call_classifier(task_text, role, size, files, lines)
        if llm_result is not None and llm_result.get("effort") in {"low", "medium", "high", "xhigh"}:
            llm_used = True
            levels = ["low", "medium", "high", "xhigh"]
            rule_idx = levels.index(effort)
            llm_idx = levels.index(llm_result["effort"])
            effort = levels[max(rule_idx, llm_idx)]
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
    if llm_used:
        reason_bits.append("LLM 境界値判定")
    reason = " / ".join(reason_bits) if reason_bits else "標準難度"

    result = {
        "effort": effort,
        "score": scored["score"],
        "breakdown": scored["breakdown"],
        "reason": reason,
        "recommended_thinking": recommended_thinking,
        "split_recommended": split_recommended,
        "role_default_thinking": role_default,
        "llm_used": llm_used,
        "cached": False,
    }
    _cache_set(key, result)
    return result
