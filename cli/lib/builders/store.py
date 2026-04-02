from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

SCHEMA = """
CREATE TABLE IF NOT EXISTS builder_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT UNIQUE NOT NULL,
    builder_type TEXT NOT NULL,
    builder_name TEXT DEFAULT '',
    task_id TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'running',
    success INTEGER DEFAULT 0,
    schema_version TEXT DEFAULT '1.0',
    input_signature_json TEXT DEFAULT '{}',
    input_hash TEXT DEFAULT '',
    pattern_tags_json TEXT DEFAULT '[]',
    artifact_refs_json TEXT DEFAULT '[]',
    current_step TEXT DEFAULT '',
    step_count INTEGER DEFAULT 0,
    step_trace_json TEXT DEFAULT '[]',
    quality_score REAL DEFAULT 0.0,
    validation_summary_json TEXT DEFAULT '{}',
    source_execution_id TEXT DEFAULT '',
    error_text TEXT DEFAULT '',
    started_at TEXT NOT NULL,
    finished_at TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_be_type_success
    ON builder_executions(builder_type, success, finished_at);
CREATE INDEX IF NOT EXISTS idx_be_task
    ON builder_executions(task_id);
CREATE INDEX IF NOT EXISTS idx_be_hash
    ON builder_executions(input_hash);
"""

_JSON_COLUMNS = {
    "input_signature_json": "input_signature",
    "pattern_tags_json": "pattern_tags",
    "artifact_refs_json": "artifact_refs",
    "step_trace_json": "step_trace",
    "validation_summary_json": "validation_summary",
}

_REDACTION_TOKENS = (
    "/home",
    "password",
    "token",
    "secret",
    "key",
    "credential",
    "authorization",
    "bearer",
    "api_key",
    "api-key",
    "apikey",
    "access_token",
    "refresh_token",
    "private_key",
    "ssh-rsa",
    "-----begin",
)

_REDACTION_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+\b", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9._-]+\b"),
    re.compile(r"\bghp_[A-Za-z0-9]+\b"),
    re.compile(r"\bxoxb-[A-Za-z0-9-]+\b"),
    re.compile(r"\bxoxp-[A-Za-z0-9-]+\b"),
)

PRAGMA_JOURNAL_MODE = "WAL"
PRAGMA_BUSY_TIMEOUT_MS = 5000


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(f"PRAGMA journal_mode={PRAGMA_JOURNAL_MODE}")
    conn.execute(f"PRAGMA busy_timeout={PRAGMA_BUSY_TIMEOUT_MS}")
    return conn


class BuilderStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db(db_path)

    @staticmethod
    def init_db(db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = _connect(db_path)
        conn.execute(f"PRAGMA journal_mode={PRAGMA_JOURNAL_MODE}")
        conn.execute(f"PRAGMA busy_timeout={PRAGMA_BUSY_TIMEOUT_MS}")
        conn.executescript(SCHEMA)
        conn.commit()
        conn.close()

    def create_execution(
        self,
        builder_type: str,
        task_id: str,
        input_params: dict,
        schema_version: str,
    ) -> str:
        now = _now_iso()
        execution_id = f"be-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
        signature = _build_input_signature(input_params)
        input_hash = _build_input_hash(input_params)
        pattern_tags = _extract_pattern_tags(input_params)

        conn = _connect(self.db_path)
        conn.execute(
            """
            INSERT INTO builder_executions (
                execution_id, builder_type, task_id, status, success,
                schema_version, input_signature_json, input_hash, pattern_tags_json,
                started_at, created_at, updated_at
            ) VALUES (?, ?, ?, 'running', 0, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                execution_id,
                builder_type,
                task_id,
                schema_version,
                _dump_json(signature),
                input_hash,
                _dump_json(pattern_tags),
                now,
                now,
                now,
            ),
        )
        conn.commit()
        conn.close()
        return execution_id

    def add_step(self, execution_id: str, name: str, data: dict):
        conn = _connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT step_count, step_trace_json FROM builder_executions WHERE execution_id = ?",
            (execution_id,),
        ).fetchone()
        if row is None:
            conn.close()
            raise ValueError(f"Execution not found: {execution_id}")

        trace = _load_json(row["step_trace_json"], default=[])
        redacted_data = _redact(data)
        trace.append(
            {
                "name": name,
                "data": redacted_data,
                "timestamp": _now_iso(),
            }
        )

        conn.execute(
            """
            UPDATE builder_executions
            SET current_step = ?,
                step_count = ?,
                step_trace_json = ?,
                updated_at = ?
            WHERE execution_id = ?
            """,
            (
                name,
                int(row["step_count"] or 0) + 1,
                _dump_json(trace),
                _now_iso(),
                execution_id,
            ),
        )
        conn.commit()
        conn.close()

    def finish_execution(
        self,
        execution_id: str,
        success: bool,
        artifacts: list[dict],
        validation: dict,
        error: str | None,
    ):
        validation_summary = validation or {}
        quality_score = _to_quality_score(validation_summary)
        status = "completed" if success else "failed"

        conn = _connect(self.db_path)
        conn.execute(
            """
            UPDATE builder_executions
            SET status = ?,
                success = ?,
                artifact_refs_json = ?,
                validation_summary_json = ?,
                quality_score = ?,
                error_text = ?,
                finished_at = ?,
                updated_at = ?
            WHERE execution_id = ?
            """,
            (
                status,
                1 if success else 0,
                _dump_json(artifacts or []),
                _dump_json(validation_summary),
                quality_score,
                error or "",
                _now_iso(),
                _now_iso(),
                execution_id,
            ),
        )
        conn.commit()
        conn.close()

    def get_execution(self, execution_id: str) -> dict:
        conn = _connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM builder_executions WHERE execution_id = ?",
            (execution_id,),
        ).fetchone()
        conn.close()
        if row is None:
            raise ValueError(f"Execution not found: {execution_id}")
        return _row_to_dict(row)

    def list_executions(
        self,
        builder_type: str,
        success_only: bool,
        limit: int,
    ) -> list[dict]:
        clauses = ["builder_type = ?"]
        params: list[Any] = [builder_type]
        if success_only:
            clauses.append("success = 1")

        sql = (
            "SELECT * FROM builder_executions WHERE "
            + " AND ".join(clauses)
            + " ORDER BY "
            + "CASE WHEN finished_at = '' THEN 1 ELSE 0 END, finished_at DESC, started_at DESC, id DESC "
            + "LIMIT ?"
        )
        params.append(max(1, int(limit)))

        conn = _connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, tuple(params)).fetchall()
        conn.close()
        return [_row_to_dict(row) for row in rows]


def _build_input_signature(input_params: Any) -> dict[str, list[str]]:
    if not isinstance(input_params, dict):
        return {"keys": []}
    return {"keys": sorted(str(key) for key in input_params.keys())}


def _extract_pattern_tags(input_params: Any) -> list[str]:
    if not isinstance(input_params, dict):
        return []
    tags = input_params.get("pattern_tags", [])
    if not isinstance(tags, list):
        return []
    return [str(tag) for tag in tags if isinstance(tag, (str, int, float))]


def _build_input_hash(input_params: Any) -> str:
    canonical = _dump_json(input_params)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _to_quality_score(validation_summary: dict) -> float:
    raw = validation_summary.get("quality_score", 0.0)
    try:
        score = float(raw)
    except (TypeError, ValueError):
        return 0.0
    if score < 0:
        return 0.0
    if score > 100:
        return 100.0
    return score


def _row_to_dict(row: sqlite3.Row) -> dict:
    payload = dict(row)
    for json_key, output_key in _JSON_COLUMNS.items():
        payload[output_key] = _load_json(payload.get(json_key, ""), default={} if output_key.endswith("summary") or output_key.endswith("signature") else [])
    return payload


def _load_json(value: str, default: Any):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _should_redact(text: str) -> bool:
    lowered = text.lower()
    if any(token in lowered for token in _REDACTION_TOKENS):
        return True
    return any(pattern.search(text) for pattern in _REDACTION_PATTERNS)


def _redact(value: Any, key_hint: str = "") -> Any:
    if isinstance(key_hint, str) and key_hint and _should_redact(key_hint):
        return "[REDACTED]"

    if isinstance(value, str):
        if _should_redact(value):
            return "[REDACTED]"
        return value

    if isinstance(value, dict):
        return {str(key): _redact(item, key_hint=str(key)) for key, item in value.items()}

    if isinstance(value, list):
        return [_redact(item, key_hint=key_hint) for item in value]

    if isinstance(value, tuple):
        return [_redact(item, key_hint=key_hint) for item in value]

    return value
