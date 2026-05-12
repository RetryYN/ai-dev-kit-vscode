from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import json
import os
import sqlite3
import statistics
import time
from pathlib import Path
from typing import Any

import helix_db

from .base import BaseDetector, DetectorResult


ERROR_DECISIONS = {"blocked", "changes_required", "error", "failed", "timeout"}
ROLE_ERROR_RATE_THRESHOLD = 0.25
SKILL_FAILURE_RATE_THRESHOLD = 0.50
FALLBACK_RATE_THRESHOLD = 0.30
THINKING_DURATION_THRESHOLD_MS = 60_000
TREND_WINDOW_DAYS = 7


def _project_root(db_path: str | Path) -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root)
    target = Path(db_path).resolve()
    if target.parent.name == ".helix":
        return target.parent.parent
    return Path.cwd()


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row[1]) for row in rows}


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _parse_meta(raw_meta: Any) -> dict[str, Any]:
    if isinstance(raw_meta, dict):
        return raw_meta
    if not isinstance(raw_meta, str) or not raw_meta.strip():
        return {}
    try:
        parsed = json.loads(raw_meta)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    for candidate in (text, text.replace(" ", "T", 1)):
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            continue
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None


def _estimate_tokens(row: dict[str, Any]) -> int:
    meta = _parse_meta(row.get("raw_meta"))
    for key in ("total_tokens", "tokens_total", "tokens_used"):
        value = _coerce_int(meta.get(key))
        if value is not None and value >= 0:
            return value

    prompt_tokens = 0
    completion_tokens = 0
    for key in ("prompt_tokens", "input_tokens"):
        value = _coerce_int(meta.get(key))
        if value is not None and value >= 0:
            prompt_tokens = value
            break
    for key in ("completion_tokens", "output_tokens"):
        value = _coerce_int(meta.get(key))
        if value is not None and value >= 0:
            completion_tokens = value
            break
    if prompt_tokens or completion_tokens:
        return prompt_tokens + completion_tokens

    input_bytes = _coerce_int(row.get("input_bytes")) or 0
    output_bytes = _coerce_int(row.get("output_bytes")) or 0
    return max(0, input_bytes + output_bytes)


def _load_role_thinking(root: Path) -> dict[str, str]:
    roles_dir = root / "cli" / "roles"
    if not roles_dir.is_dir():
        return {}

    mapping: dict[str, str] = {}
    for path in sorted(roles_dir.glob("*.conf")):
        role = path.stem
        codex_thinking = ""
        thinking = ""
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            if line.startswith("codex_thinking="):
                codex_thinking = line.split("=", 1)[1].strip()
            elif line.startswith("thinking="):
                thinking = line.split("=", 1)[1].strip()
        resolved = codex_thinking or thinking
        if resolved:
            mapping[role] = resolved
    return mapping


def _thinking_bucket(row: dict[str, Any], role_thinking: dict[str, str]) -> str:
    meta = _parse_meta(row.get("raw_meta"))
    for key in ("thinking", "thinking_level", "reasoning_effort", "codex_thinking"):
        value = meta.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    role = str(row.get("role") or "").strip()
    if role and role in role_thinking:
        return role_thinking[role]
    return "unknown"


def _load_invocation_rows(conn: sqlite3.Connection) -> tuple[list[dict[str, Any]], str | None]:
    if not _table_exists(conn, "invocation_log"):
        return [], "invocation_log table is missing"

    columns = _table_columns(conn, "invocation_log")
    required = {"timestamp", "role", "model", "input_bytes", "output_bytes", "duration_ms", "decision", "cost_cents", "raw_meta"}
    missing = sorted(required - columns)
    if missing:
        return [], f"invocation_log columns are missing: {', '.join(missing)}"

    rows = conn.execute(
        """
        SELECT timestamp, role, model, input_bytes, output_bytes, duration_ms, decision, cost_cents, raw_meta
        FROM invocation_log
        ORDER BY timestamp, id
        """
    ).fetchall()
    return [{key: row[key] for key in row.keys()} for row in rows], None


def _load_skill_rows(conn: sqlite3.Connection) -> tuple[list[dict[str, Any]], list[str], str | None]:
    if not _table_exists(conn, "skill_usage"):
        return [], [], "skill_usage table is missing"

    columns = _table_columns(conn, "skill_usage")
    required = {"skill_id", "outcome"}
    missing = sorted(required - columns)
    if missing:
        return [], sorted(columns), f"skill_usage columns are missing: {', '.join(missing)}"

    select_columns = [
        column
        for column in (
            "skill_id",
            "outcome",
            "created_at",
            "agent_used",
            "model_used",
            "fallback_applied",
            "tokens_used",
        )
        if column in columns
    ]
    query = f"SELECT {', '.join(select_columns)} FROM skill_usage ORDER BY id"
    rows = conn.execute(query).fetchall()
    return [{key: row[key] for key in row.keys()} for row in rows], sorted(columns), None


def _is_error_decision(value: Any) -> bool:
    decision = str(value or "").strip().lower()
    return decision in ERROR_DECISIONS


def _high_sigma_keys(values_by_key: dict[str, float]) -> set[str]:
    values = list(values_by_key.values())
    if len(values) < 2:
        return set()
    sigma = statistics.pstdev(values)
    if sigma <= 0:
        return set()
    threshold = statistics.mean(values) + (3 * sigma)
    return {key for key, value in values_by_key.items() if value > threshold}


class Axis13ModelSkillAnalytics(BaseDetector):
    id = "axis-13"
    name = "model & skill analytics"
    phase_gate = None
    kind = "detector"

    def run(self, db_path: str | Path) -> DetectorResult:
        started = time.perf_counter()
        target_db = Path(db_path)
        helix_db._prepare_db_path(str(target_db))
        conn = helix_db.get_connection(target_db)
        try:
            invocation_rows, invocation_error = _load_invocation_rows(conn)
            skill_rows, skill_columns, skill_error = _load_skill_rows(conn)
        finally:
            conn.close()

        root = _project_root(db_path)
        if invocation_error is not None:
            cost_ms = max(1, int((time.perf_counter() - started) * 1000))
            return DetectorResult(
                verdict="blocked",
                findings=[],
                cost_ms=cost_ms,
                raw={"reason": invocation_error, "project_root": str(root)},
            )
        if not invocation_rows:
            cost_ms = max(1, int((time.perf_counter() - started) * 1000))
            return DetectorResult(
                verdict="blocked",
                findings=[],
                cost_ms=cost_ms,
                raw={"reason": "invocation_log has no rows", "project_root": str(root)},
            )

        role_thinking = _load_role_thinking(root)
        findings: list[dict[str, Any]] = []

        model_counts: Counter[str] = Counter()
        model_tokens: defaultdict[str, int] = defaultdict(int)
        model_costs: defaultdict[str, float] = defaultdict(float)
        role_counts: Counter[str] = Counter()
        role_errors: Counter[str] = Counter()
        thinking_counts: Counter[str] = Counter()
        thinking_durations: defaultdict[str, int] = defaultdict(int)
        invocation_trend: Counter[str] = Counter()

        for row in invocation_rows:
            model = str(row.get("model") or "unknown").strip() or "unknown"
            role = str(row.get("role") or "unknown").strip() or "unknown"
            thinking = _thinking_bucket(row, role_thinking)
            tokens = _estimate_tokens(row)
            cost = _coerce_float(row.get("cost_cents")) or 0.0
            duration_ms = _coerce_int(row.get("duration_ms")) or 0
            parsed_at = _parse_timestamp(row.get("timestamp"))

            model_counts[model] += 1
            model_tokens[model] += tokens
            model_costs[model] += cost
            role_counts[role] += 1
            if _is_error_decision(row.get("decision")):
                role_errors[role] += 1
            thinking_counts[thinking] += 1
            thinking_durations[thinking] += max(0, duration_ms)
            if parsed_at is not None:
                invocation_trend[parsed_at.date().isoformat()] += tokens

        model_summary: list[dict[str, Any]] = []
        model_avg_tokens: dict[str, float] = {}
        model_avg_costs: dict[str, float] = {}
        for model in sorted(model_counts, key=lambda key: (-model_counts[key], key)):
            count = model_counts[model]
            avg_tokens = model_tokens[model] / count if count else 0.0
            avg_cost = model_costs[model] / count if count else 0.0
            model_avg_tokens[model] = avg_tokens
            model_avg_costs[model] = avg_cost
            model_summary.append(
                {
                    "model": model,
                    "invocations": count,
                    "avg_tokens": round(avg_tokens, 2),
                    "avg_cost_cents": round(avg_cost, 4),
                }
            )

        for model in sorted(_high_sigma_keys(model_avg_tokens)):
            findings.append(
                {
                    "kind": "model_avg_tokens_high",
                    "model": model,
                    "value": round(model_avg_tokens[model], 2),
                }
            )
        for model in sorted(_high_sigma_keys(model_avg_costs)):
            findings.append(
                {
                    "kind": "model_avg_cost_high",
                    "model": model,
                    "value": round(model_avg_costs[model], 4),
                }
            )

        role_summary: list[dict[str, Any]] = []
        for role in sorted(role_counts, key=lambda key: (-role_counts[key], key)):
            count = role_counts[role]
            error_count = role_errors[role]
            error_rate = error_count / count if count else 0.0
            role_summary.append(
                {
                    "role": role,
                    "invocations": count,
                    "error_rate": round(error_rate, 4),
                }
            )
            if count >= 3 and error_rate > ROLE_ERROR_RATE_THRESHOLD:
                findings.append(
                    {
                        "kind": "role_error_rate",
                        "role": role,
                        "value": round(error_rate, 4),
                        "threshold": ROLE_ERROR_RATE_THRESHOLD,
                    }
                )

        skill_summary: list[dict[str, Any]] = []
        fallback_summary: list[dict[str, Any]] = []

        if skill_error is None and skill_rows:
            skill_counts: Counter[str] = Counter()
            skill_outcomes: defaultdict[str, Counter[str]] = defaultdict(Counter)
            fallback_counts: Counter[str] = Counter()
            fallback_totals: Counter[str] = Counter()
            skill_trend: Counter[str] = Counter()

            for row in skill_rows:
                skill_id = str(row.get("skill_id") or "unknown").strip() or "unknown"
                outcome = str(row.get("outcome") or "unknown").strip().lower() or "unknown"
                skill_counts[skill_id] += 1
                skill_outcomes[skill_id][outcome] += 1

                created_at = _parse_timestamp(row.get("created_at"))
                if "tokens_used" in row:
                    token_value = _coerce_int(row.get("tokens_used")) or 0
                    if created_at is not None and token_value > 0:
                        skill_trend[created_at.date().isoformat()] += token_value

                if "fallback_applied" in row:
                    agent = str(row.get("agent_used") or "unknown").strip() or "unknown"
                    target_model = str(row.get("model_used") or "unknown").strip() or "unknown"
                    label = f"{agent}->{target_model}"
                    fallback_totals[label] += 1
                    if bool(_coerce_int(row.get("fallback_applied"))):
                        fallback_counts[label] += 1

            for skill_id in sorted(skill_counts, key=lambda key: (-skill_counts[key], key)):
                count = skill_counts[skill_id]
                outcome_counts = dict(sorted(skill_outcomes[skill_id].items()))
                skill_summary.append(
                    {
                        "skill_id": skill_id,
                        "usage_count": count,
                        "outcomes": outcome_counts,
                    }
                )
                failed = skill_outcomes[skill_id].get("failed", 0)
                fail_rate = failed / count if count else 0.0
                if count >= 3 and fail_rate > SKILL_FAILURE_RATE_THRESHOLD:
                    findings.append(
                        {
                            "kind": "skill_failure_rate",
                            "skill_id": skill_id,
                            "value": round(fail_rate, 4),
                            "threshold": SKILL_FAILURE_RATE_THRESHOLD,
                        }
                    )

            for label in sorted(fallback_totals, key=lambda key: (-fallback_totals[key], key)):
                total = fallback_totals[label]
                fallback_count = fallback_counts[label]
                fallback_rate = fallback_count / total if total else 0.0
                agent, target_model = label.split("->", 1)
                fallback_summary.append(
                    {
                        "label": label,
                        "agent": agent,
                        "target_model": target_model,
                        "samples": total,
                        "fallback_rate": round(fallback_rate, 4),
                    }
                )
                if total >= 3 and fallback_rate > FALLBACK_RATE_THRESHOLD:
                    findings.append(
                        {
                            "kind": "fallback_rate",
                            "label": label,
                            "value": round(fallback_rate, 4),
                            "threshold": FALLBACK_RATE_THRESHOLD,
                        }
                    )

            if skill_trend:
                invocation_trend = skill_trend

        thinking_summary: list[dict[str, Any]] = []
        thinking_avg_durations: dict[str, float] = {}
        for thinking in sorted(thinking_counts, key=lambda key: (-thinking_counts[key], key)):
            count = thinking_counts[thinking]
            avg_duration = thinking_durations[thinking] / count if count else 0.0
            thinking_avg_durations[thinking] = avg_duration
            thinking_summary.append(
                {
                    "thinking": thinking,
                    "samples": count,
                    "avg_duration_ms": round(avg_duration, 2),
                }
            )
            if count >= 2 and avg_duration > THINKING_DURATION_THRESHOLD_MS:
                findings.append(
                    {
                        "kind": "thinking_duration_high",
                        "thinking": thinking,
                        "value": round(avg_duration, 2),
                        "threshold_ms": THINKING_DURATION_THRESHOLD_MS,
                    }
                )

        for thinking in sorted(_high_sigma_keys(thinking_avg_durations)):
            findings.append(
                {
                    "kind": "thinking_duration_sigma_high",
                    "thinking": thinking,
                    "value": round(thinking_avg_durations[thinking], 2),
                }
            )

        now = datetime.now(timezone.utc).date()
        trend_days = [(now - timedelta(days=offset)).isoformat() for offset in range(TREND_WINDOW_DAYS - 1, -1, -1)]
        trend_summary = [{"date": day, "tokens": int(invocation_trend.get(day, 0))} for day in trend_days]
        trend_values = [item["tokens"] for item in trend_summary]
        if len(trend_values) >= 2:
            sigma = statistics.pstdev(trend_values)
            if sigma > 0:
                threshold = statistics.mean(trend_values) + (3 * sigma)
                for item in trend_summary:
                    if item["tokens"] > threshold:
                        findings.append(
                            {
                                "kind": "daily_token_spike",
                                "date": item["date"],
                                "value": item["tokens"],
                            }
                        )

        summary = {
            "models": model_summary,
            "roles": role_summary,
            "skills": skill_summary,
            "thinking_levels": thinking_summary,
            "fallback_rates": fallback_summary,
            "daily_tokens": trend_summary,
            "token_estimation": "raw_meta tokens if present, otherwise input_bytes + output_bytes",
        }
        if skill_error is not None:
            summary["skill_usage_notice"] = skill_error
        elif "tokens_used" not in skill_columns:
            summary["skill_usage_notice"] = "tokens_used column is unavailable; daily trend uses invocation_log estimates"

        verdict = "passed" if not findings else "failed"
        cost_ms = max(1, int((time.perf_counter() - started) * 1000))
        return DetectorResult(
            verdict=verdict,
            findings=findings,
            cost_ms=cost_ms,
            raw={
                "summary": summary,
                "project_root": str(root),
                "anomaly_count": len(findings),
            },
        )
