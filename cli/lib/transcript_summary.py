"""契約: PLAN-099 §8

SessionStart/UserPromptSubmit 向けの transcript 要約 PoC。
raw transcript は保存せず、機密情報を除外した短い要約だけを返す。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._\-+/=]+\b", re.IGNORECASE)
ASSIGNMENT_SECRET_RE = re.compile(
    r"\b(api[_-]?key|token|password|credential|secret)\b\s*[:=]\s*([^\s,;]+)",
    re.IGNORECASE,
)
OPAQUE_KEY_RE = re.compile(r"\b(sk|rk|pk)-[A-Za-z0-9]{10,}\b", re.IGNORECASE)
WHITESPACE_RE = re.compile(r"\s+")


def filter_secrets(text: str) -> str:
    """Transcript から secret/PII を除外する。"""
    filtered = EMAIL_RE.sub("[REDACTED:email]", text)
    filtered = BEARER_RE.sub("Bearer [REDACTED:token]", filtered)
    filtered = OPAQUE_KEY_RE.sub("[REDACTED:api_key]", filtered)

    def _replace_assignment(match: re.Match[str]) -> str:
        label = match.group(1).lower().replace("-", "_")
        return f"{match.group(1)}=[REDACTED:{label}]"

    return ASSIGNMENT_SECRET_RE.sub(_replace_assignment, filtered)


def summarize_transcript(transcript_path: str | Path, max_chars: int = 5000) -> str:
    """Transcript を読み、secret/PII を除外した短い要約文字列を返す。"""
    limit = max(1, int(max_chars))
    raw_text = Path(transcript_path).read_text(encoding="utf-8")
    extracted = _extract_text(raw_text)
    filtered = filter_secrets(extracted)
    compact = WHITESPACE_RE.sub(" ", filtered).strip()
    if len(compact) <= limit:
        return compact
    if limit == 1:
        return compact[:1]
    return compact[: limit - 1] + "…"


def _extract_text(raw_text: str) -> str:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return ""

    extracted_parts: list[str] = []
    json_line_count = 0
    for line in lines:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            extracted_parts.append(line)
            continue
        json_line_count += 1
        _append_strings(payload, extracted_parts)

    if json_line_count == len(lines):
        return "\n".join(part for part in extracted_parts if part.strip())
    return raw_text


def _append_strings(value: Any, parts: list[str]) -> None:
    if isinstance(value, str):
        text = value.strip()
        if text:
            parts.append(text)
        return
    if isinstance(value, list):
        for item in value:
            _append_strings(item, parts)
        return
    if isinstance(value, dict):
        preferred_keys = ("role", "type", "text", "content", "message", "prompt", "summary")
        for key in preferred_keys:
            if key in value:
                _append_strings(value[key], parts)
        for key, item in value.items():
            if key not in preferred_keys:
                _append_strings(item, parts)
