"""HELIX recipe store.

責務: レシピの保存・検索・推薦。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


_HISTORY_QUERY_TOKEN_PATTERN = re.compile(r"[\s,]+")
_REDACTION_TOKENS = (
    "password",
    "passwd",
    "token",
    "secret",
    "apikey",
    "api_key",
    "api-key",
    "access_token",
    "refresh_token",
    "private_key",
    "credential",
    "authorization",
    "bearer",
    "ssh-rsa",
    "-----begin",
    "/home",
)


def _truncate(text: str, limit: int = 220) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _redact_text(value: str) -> str:
    lowered = value.lower()
    if any(token in lowered for token in _REDACTION_TOKENS):
        return "[REDACTED]"
    return value


def _history_query_tokens(query: str) -> list[str]:
    text = str(query or "").strip().lower()
    if not text:
        return []
    return [token for token in _HISTORY_QUERY_TOKEN_PATTERN.split(text) if token]


def _history_recipe_text(recipe: dict[str, Any]) -> str:
    classification = recipe.get("classification", {})
    notes = recipe.get("notes", {})
    source = recipe.get("source", {})

    if not isinstance(classification, dict):
        classification = {}
    if not isinstance(notes, dict):
        notes = {}
    if not isinstance(source, dict):
        source = {}

    parts: list[str] = []
    for key in ("pattern_key", "recipe_id", "failure_type"):
        value = recipe.get(key)
        if value:
            parts.append(str(value))
    for key in ("task_type", "role", "builder_type"):
        value = classification.get(key)
        if value:
            parts.append(str(value))
    for key in ("failure_reason", "recurrence_prevention", "why_it_worked", "applicability"):
        value = notes.get(key)
        if value:
            parts.append(str(value))
    for key in ("task_id", "plan_goal"):
        value = source.get(key)
        if value:
            parts.append(str(value))
    return " ".join(parts).lower()


def _match_score(tokens: list[str], recipe: dict[str, Any]) -> float:
    """query token と recipe の一致度スコアを返す。"""
    text = _history_recipe_text(recipe)
    classification = recipe.get("classification", {})
    tags: set[str] = set()
    if isinstance(classification, dict):
        raw_tags = classification.get("tags", [])
        if isinstance(raw_tags, list):
            tags = {str(item).lower() for item in raw_tags}

    metrics = recipe.get("metrics", {})
    if not isinstance(metrics, dict):
        metrics = {}
    try:
        quality = float(metrics.get("quality_score", 0.0) or 0.0)
    except (TypeError, ValueError):
        quality = 0.0
    quality = min(max(quality, 0.0), 100.0) / 100.0

    if not tokens:
        return quality * 100.0

    text_hits = sum(1 for token in tokens if token in text)
    tag_hits = sum(1 for token in tokens if any(token in tag for tag in tags))
    summary = str(recipe.get("summary") or "").lower()
    summary_hits = sum(1 for token in tokens if token in summary) if summary else 0
    return (
        (text_hits / len(tokens)) * 70.0
        + (tag_hits / len(tokens)) * 20.0
        + quality * 10.0
        + (summary_hits / len(tokens)) * 10.0
    )


def _rank_recipes(query: str, recipes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """query に対して recipe をスコア順に並べる。"""
    tokens = _history_query_tokens(query)
    scored: list[dict[str, Any]] = []
    for recipe in recipes:
        if not isinstance(recipe, dict):
            continue
        score = _match_score(tokens, recipe)
        if tokens and score <= 0.0:
            continue
        scored.append({**recipe, "_score": score})

    scored.sort(key=lambda item: float(item.get("_score", 0.0) or 0.0), reverse=True)
    return scored


def list_recipes(project_root: str) -> list[dict[str, Any]]:
    """.helix/recipes 下の recipe 一覧を返す。"""
    recipe_dir = Path(project_root) / ".helix" / "recipes"
    if not recipe_dir.exists():
        return []

    recipes: list[dict[str, Any]] = []
    for recipe_file in sorted(recipe_dir.glob("*.json")):
        try:
            payload = json.loads(recipe_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        payload["_path"] = str(recipe_file)
        recipes.append(payload)
    return recipes


def from_history(query: str, project_root: str, limit: int = 5) -> dict[str, Any]:
    """履歴 recipe から候補を検索し、失敗パターンは警告として返す。"""
    recipes = list_recipes(project_root)
    if not recipes:
        return {
            "query": str(query or ""),
            "recommendations": [],
            "warnings": [],
            "failure_recipes": [],
        }

    scored = _rank_recipes(query=query, recipes=recipes)

    recommendations: list[dict[str, Any]] = []
    warning_messages: list[str] = []
    failure_recipes: list[dict[str, Any]] = []

    for item in scored:
        failure_type = str(item.get("failure_type") or "").strip()
        explicit_success = item.get("success")
        is_failure = explicit_success is False or bool(failure_type)

        if not is_failure:
            clean = dict(item)
            clean.pop("_score", None)
            recommendations.append(clean)
            if len(recommendations) >= max(1, int(limit)):
                break
            continue

        notes = item.get("notes", {}) if isinstance(item.get("notes"), dict) else {}
        source = item.get("source", {}) if isinstance(item.get("source"), dict) else {}
        reason_raw = (
            notes.get("failure_reason")
            or source.get("error_text")
            or source.get("output_log")
            or failure_type
            or "原因不明"
        )
        reason = _truncate(_redact_text(str(reason_raw)), limit=200)
        warning = f"このパターンは過去に失敗しています: {reason}"
        warning_messages.append(warning)

        failure_detail = dict(item)
        failure_detail.pop("_score", None)
        failure_detail["warning"] = warning
        failure_recipes.append(failure_detail)

    safe_limit = max(1, int(limit))
    return {
        "query": str(query or ""),
        "recommendations": recommendations[:safe_limit],
        "warnings": warning_messages[:safe_limit],
        "failure_recipes": failure_recipes[:safe_limit],
    }


def _load_recipe_file(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    payload["_path"] = str(path)
    return payload


def load_recipe(recipe_id: str, project_root: str) -> dict[str, Any] | None:
    """Search order(project-local -> user-global) で recipe を解決する。"""
    clean_id = str(recipe_id or "").strip()
    if not clean_id:
        return None

    file_name = clean_id if clean_id.endswith(".json") else f"{clean_id}.json"

    local_path = Path(project_root) / ".helix" / "recipes" / file_name
    local_payload = _load_recipe_file(local_path)
    if local_payload is not None:
        return local_payload

    user_global = Path.home() / ".helix" / "recipes" / file_name
    return _load_recipe_file(user_global)


def find_recipe(recipe_id: str, project_root: str) -> dict[str, Any] | None:
    """互換 API。"""
    return load_recipe(recipe_id=recipe_id, project_root=project_root)
