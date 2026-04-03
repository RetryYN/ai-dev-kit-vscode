from __future__ import annotations

from datetime import datetime, timezone
import re

from .store import BuilderStore


class BuilderHistory:
    def __init__(self, store: BuilderStore):
        self.store = store

    def search(self, builder_type: str, query: dict, limit: int = 5) -> list[dict]:
        """成功履歴から類似パターンを検索"""
        candidates = self.store.list_executions(builder_type, success_only=True, limit=50)
        scored = []
        for candidate in candidates:
            score = self._compute_score(query, candidate)
            scored.append({**candidate, "_score": score})
        scored.sort(key=lambda item: item["_score"], reverse=True)
        return scored[: max(1, int(limit))]

    def _compute_score(self, query: dict, candidate: dict) -> float:
        """スコアリング: structural 40 + tag 25 + role 15 + quality 10 + recency 10"""
        structural = _jaccard(_signature_keys(query), _signature_keys(candidate))

        query_tags = _tag_set(query)
        candidate_tags = _tag_set(candidate)
        tag = _overlap(query_tags, candidate_tags)

        query_role_skill = _role_skill_tags(query_tags)
        candidate_role_skill = _role_skill_tags(candidate_tags)
        role_skill = _overlap(query_role_skill, candidate_role_skill)

        quality_raw = candidate.get("quality_score", 0.0)
        try:
            quality_norm = float(quality_raw) / 100.0
        except (TypeError, ValueError):
            quality_norm = 0.0
        quality_norm = min(max(quality_norm, 0.0), 1.0)

        recency = _recency_score(candidate.get("finished_at", ""))

        return (
            (structural * 40.0)
            + (tag * 25.0)
            + (role_skill * 15.0)
            + (quality_norm * 10.0)
            + (recency * 10.0)
        )

    @staticmethod
    def search_recipe_candidates(query: str, candidates: list[dict], limit: int = 5) -> list[dict]:
        """recipe 検索向けのスコアリング。"""
        tokens = _query_tokens(query)
        scored: list[dict] = []

        for candidate in candidates:
            score = _recipe_score(tokens, candidate)
            scored.append({**candidate, "_score": score})

        scored.sort(key=lambda item: item.get("_score", 0.0), reverse=True)
        return scored[: max(1, int(limit))]


def _signature_keys(payload: dict) -> set[str]:
    signature = payload.get("input_signature")
    if signature is None and isinstance(payload.get("input_params"), dict):
        signature = {"keys": list(payload["input_params"].keys())}
    if signature is None and isinstance(payload, dict):
        ignored = {"input_signature", "input_params", "pattern_tags"}
        return {str(key) for key in payload.keys() if str(key) not in ignored}

    if isinstance(signature, dict):
        keys = signature.get("keys")
        if isinstance(keys, list):
            return {str(item) for item in keys}
        return {str(item) for item in signature.keys()}

    if isinstance(signature, list):
        return {str(item) for item in signature}

    return set()


def _tag_set(payload: dict) -> set[str]:
    tags = payload.get("pattern_tags", [])
    if not isinstance(tags, list):
        return set()
    return {str(tag) for tag in tags}


def _role_skill_tags(tags: set[str]) -> set[str]:
    return {tag for tag in tags if tag.startswith("role:") or tag.startswith("skill:")}


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def _overlap(left: set[str], right: set[str]) -> float:
    denominator = max(len(left), len(right))
    if denominator == 0:
        return 0.0
    return len(left & right) / denominator


def _recency_score(finished_at: str) -> float:
    if not finished_at:
        return 0.0
    raw = finished_at.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"

    try:
        done_at = datetime.fromisoformat(raw)
    except ValueError:
        return 0.0

    if done_at.tzinfo is None:
        done_at = done_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    days_since = max((now - done_at.astimezone(timezone.utc)).total_seconds() / 86400.0, 0.0)
    return 1.0 - min(days_since / 90.0, 1.0)


def _query_tokens(query: str) -> list[str]:
    text = (query or "").strip().lower()
    if not text:
        return []
    return [token for token in re.split(r"[\s,]+", text) if token]


def _recipe_text(candidate: dict) -> str:
    classification = candidate.get("classification", {})
    if not isinstance(classification, dict):
        classification = {}
    notes = candidate.get("notes", {})
    if not isinstance(notes, dict):
        notes = {}

    parts: list[str] = []
    for key in ("pattern_key", "recipe_id", "builder_type", "task_type"):
        value = candidate.get(key)
        if value is not None:
            parts.append(str(value))
    for key in ("task_type", "role", "builder_type"):
        value = classification.get(key)
        if value is not None:
            parts.append(str(value))
    for key in ("why_it_worked", "applicability"):
        value = notes.get(key)
        if value is not None:
            parts.append(str(value))
    summary = candidate.get("summary")
    if summary is not None:
        parts.append(str(summary))
    return " ".join(parts).lower()


def _recipe_tags(candidate: dict) -> set[str]:
    tags = set()

    root_tags = candidate.get("tags")
    if isinstance(root_tags, list):
        tags |= {str(tag).lower() for tag in root_tags}

    classification = candidate.get("classification", {})
    if isinstance(classification, dict):
        cls_tags = classification.get("tags")
        if isinstance(cls_tags, list):
            tags |= {str(tag).lower() for tag in cls_tags}

    return tags


def _recipe_quality(candidate: dict) -> float:
    metrics = candidate.get("metrics", {})
    if not isinstance(metrics, dict):
        metrics = {}
    raw = metrics.get("quality_score", candidate.get("quality_score_mean", 0.0))
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    if value < 0.0:
        return 0.0
    if value > 100.0:
        return 100.0
    return value


def _recipe_score(tokens: list[str], candidate: dict) -> float:
    text = _recipe_text(candidate)
    tags = _recipe_tags(candidate)
    quality = _recipe_quality(candidate) / 100.0

    verification_bonus = 0.0
    verification = candidate.get("verification", {})
    if isinstance(verification, dict):
        tests = verification.get("tests", {})
        contracts = verification.get("contracts", {})
        quality_info = verification.get("quality", {})

        if isinstance(tests, dict):
            try:
                tests_failed = int(tests.get("failed", -1))
            except (TypeError, ValueError):
                tests_failed = -1
            try:
                tests_total = int(tests.get("total", 0))
            except (TypeError, ValueError):
                tests_total = 0
            if tests_failed == 0 and tests_total > 0:
                verification_bonus += 5.0  # テスト全 pass

        if isinstance(contracts, dict) and contracts.get("schema_valid") is True:
            verification_bonus += 3.0  # 契約検証 OK

        if isinstance(quality_info, dict):
            try:
                lint_errors = int(quality_info.get("lint_errors", -1))
            except (TypeError, ValueError):
                lint_errors = -1
            if lint_errors == 0:
                verification_bonus += 2.0  # lint clean

    if not tokens:
        return (quality * 60.0) + (min(len(tags), 5) / 5.0 * 40.0) + verification_bonus

    text_hits = sum(1 for token in tokens if token in text)
    tag_hits = sum(1 for token in tokens if any(token in tag for tag in tags))
    summary = str(candidate.get("summary") or "").lower()
    summary_hits = sum(1 for token in tokens if token in summary) if summary else 0

    text_score = (text_hits / len(tokens)) * 65.0
    tag_score = (tag_hits / len(tokens)) * 25.0
    quality_score = quality * 10.0
    summary_score = (summary_hits / len(tokens)) * 15.0

    return text_score + tag_score + quality_score + summary_score + verification_bonus
