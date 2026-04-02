from __future__ import annotations

from datetime import datetime, timezone

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
