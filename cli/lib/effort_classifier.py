"""effort_classifier.py - タスク難度 -> effort 自動判定。"""
from __future__ import annotations

import hashlib, json, re
from pathlib import Path
from typing import Any

try:
    from .llm_classifier_base import CodexInvocationError, CodexResponseError, LLMClassifierBase
    from .model_registry import resolve_role_model
except ImportError:  # pragma: no cover
    from llm_classifier_base import CodexInvocationError, CodexResponseError, LLMClassifierBase
    from model_registry import resolve_role_model

CACHE_DIR = Path(".helix/budget/cache/classify")
CACHE_TTL_SEC = 3600
BOUNDARY_SCORES = {3, 4, 7, 8, 12, 13}
LLM_TIMEOUT_SEC = 10
LEVELS = ["low", "medium", "high", "xhigh"]
ROLE_DEFAULT_THINKING = {
    "tl": "high", "se": "high", "pg": "medium", "fe": "medium", "qa": "medium",
    "security": "high", "dba": "high", "devops": "high", "docs": "medium",
    "research": "medium", "legacy": "high", "perf": "high",
}

_BUG_FIX = re.compile(r"\b(bug|fix|typo|patch|誤字|修正)\b", re.IGNORECASE)
_NEW_DESIGN = re.compile(r"\b(新規|設計|architect|design|ADR)\b", re.IGNORECASE)
_API_DB = re.compile(r"\b(API|DB|migration|schema|endpoint|table)\b", re.IGNORECASE)
_TEST = re.compile(r"\b(test|テスト|E2E|regression|回帰)\b", re.IGNORECASE)
_CROSS = re.compile(r"\b(refactor|横断|cross|multi|複数モジュール)\b", re.IGNORECASE)


def _files_score(files: int | None) -> int:
    return 1 if files is None or files <= 2 else 2 if files <= 5 else 3 if files <= 10 else 4


def score_task(task_text: str, role: str | None = None, size: str | None = None, files: int | None = None, lines: int | None = None) -> dict[str, Any]:
    text = task_text or ""
    breakdown = {
        "files": _files_score(files),
        "cross_module": 2 if _CROSS.search(text) else 1,
        "spec_understanding": 1 if _BUG_FIX.search(text) else (3 if _NEW_DESIGN.search(text) else 2),
        "side_effect": 4 if re.search(r"migration|migrate", text, re.IGNORECASE) else (2 if _API_DB.search(text) else 0),
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
    return "low" if score <= 3 else "medium" if score <= 7 else "high" if score <= 12 else "xhigh"


def _cache_key(task_text: str, role: str | None, size: str | None) -> str:
    return hashlib.sha256(f"{task_text}|{role or ''}|{size or ''}".encode("utf-8")).hexdigest()[:32]


class EffortClassifier(LLMClassifierBase):
    role = resolve_role_model("effort-classifier", default="gpt-5.4-mini")
    classifier_name = "effort_classifier"
    cache_ttl_sec = CACHE_TTL_SEC
    codex_timeout_sec = LLM_TIMEOUT_SEC

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path=db_path)
        self.cache_dir = CACHE_DIR

    def _cache_key(self, query: str, context: dict | None) -> str:
        return _cache_key(query, (context or {}).get("role"), (context or {}).get("size"))

    def _cache_store(self, key: str, value: dict) -> None:
        try:
            super()._cache_store(key, value)
        except OSError:
            pass

    def _build_prompt(self, query: str, context: dict | None) -> str:
        prompt_path = Path(__file__).resolve().parent.parent / "templates" / "effort-classify-prompt.md"
        if not prompt_path.exists():
            raise CodexInvocationError("effort-classify-prompt.md not found")
        payload = {"task": query[:2000], **(context or {})}
        return prompt_path.read_text(encoding="utf-8", errors="ignore") + "\n\n## 入力\n```json\n" + json.dumps(payload, ensure_ascii=False) + "\n```\n\n## 出力\nJSON のみを出力 ({\"effort\": \"...\", \"score\": N, ...})。"

    def _parse_response(self, raw: str) -> dict:
        parsed = super()._parse_response(raw)
        if parsed.get("effort") not in set(LEVELS):
            raise CodexResponseError("effort must be low/medium/high/xhigh")
        return parsed

    def classify(self, task_text: str, role: str | None = None, size: str | None = None, files: int | None = None, lines: int | None = None, use_llm: bool = True) -> dict[str, Any]:
        context = {"role": role, "size": size, "files": files, "lines": lines}
        key = self._cache_key(task_text, context)
        cached = self._cache_lookup(key)
        if cached is not None:
            cached["cached"] = True
            self._last_cache_key = key
            self._record_decision(task_text, cached, source="cache")
            return cached

        scored = score_task(task_text, role, size, files, lines)
        effort, llm_used = map_to_effort(scored["score"]), False
        if use_llm and scored["score"] in BOUNDARY_SCORES:
            llm_result = call_classifier(task_text, role, size, files, lines)
            if llm_result is not None:
                effort, llm_used = LEVELS[max(LEVELS.index(effort), LEVELS.index(llm_result["effort"]))], True

        role_default = ROLE_DEFAULT_THINKING.get(role or "", "medium")
        recommended = "medium" if effort == "low" and role_default in ("high", "xhigh") else ("low" if effort == "low" else effort)
        b, split = scored["breakdown"], effort == "xhigh" and size == "S"
        reason_bits = (
            ([f"side_effect={b['side_effect']}"] if b["side_effect"] >= 2 else [])
            + (["新規設計系"] if b["spec_understanding"] >= 3 else [])
            + ([f"ファイル数 score={b['files']}"] if b["files"] >= 3 else [])
            + (["S サイズに xhigh → 分割推奨"] if split else [])
            + (["LLM 境界値判定"] if llm_used else [])
        )
        result = {
            "effort": effort, "score": scored["score"], "breakdown": b,
            "reason": " / ".join(reason_bits) if reason_bits else "標準難度",
            "recommended_thinking": recommended, "split_recommended": split,
            "role_default_thinking": role_default, "llm_used": llm_used, "cached": False,
        }
        self._last_cache_key = key
        self._cache_store(key, result)
        self._record_decision(task_text, result, source="codex" if llm_used else "rule")
        return result


def call_classifier(task_text: str, role: str | None = None, size: str | None = None, files: int | None = None, lines: int | None = None) -> dict[str, Any] | None:
    classifier = EffortClassifier()
    try:
        return classifier._parse_response(classifier._invoke_codex(task_text, {"role": role, "size": size, "files": files, "lines": lines}))
    except (CodexInvocationError, CodexResponseError, OSError):
        return None


def classify(task_text: str, role: str | None = None, size: str | None = None, files: int | None = None, lines: int | None = None, use_llm: bool = True) -> dict[str, Any]:
    return EffortClassifier().classify(task_text, role, size, files, lines, use_llm)


def effort_classify(*args, **kwargs) -> dict[str, Any]:
    return classify(*args, **kwargs)
