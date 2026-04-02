from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .learning_engine import analyze_success, list_recipes
except ImportError:  # pragma: no cover
    from learning_engine import analyze_success, list_recipes


PRAGMA_JOURNAL_MODE = "WAL"
PRAGMA_BUSY_TIMEOUT_MS = 5000

SCHEMA = """
CREATE TABLE IF NOT EXISTS recipe_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id TEXT NOT NULL,
    pattern_key TEXT NOT NULL,
    builder_type TEXT DEFAULT '',
    project_id TEXT NOT NULL,
    success_rate REAL DEFAULT 0.0,
    quality_score_mean REAL DEFAULT 0.0,
    tags_json TEXT DEFAULT '[]',
    context_json TEXT DEFAULT '{}',
    local_path TEXT DEFAULT '',
    global_path TEXT DEFAULT '',
    promotion_status TEXT DEFAULT 'none',
    success_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(pattern_key, project_id)
);

CREATE INDEX IF NOT EXISTS idx_recipe_pattern ON recipe_index(pattern_key);
CREATE INDEX IF NOT EXISTS idx_recipe_success ON recipe_index(success_count, success_rate);
CREATE INDEX IF NOT EXISTS idx_recipe_promotion ON recipe_index(promotion_status);
CREATE INDEX IF NOT EXISTS idx_recipe_recipe_id ON recipe_index(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipe_recipe_project ON recipe_index(recipe_id, project_id);

CREATE TABLE IF NOT EXISTS promotion_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    promotion_id TEXT UNIQUE NOT NULL,
    recipe_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    builder_type TEXT NOT NULL,
    artifact_ref TEXT DEFAULT '',
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_promotion_recipe ON promotion_records(recipe_id, created_at);
"""

_QUERY_TOKEN_PATTERN = re.compile(r"[\s,]+")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _global_root() -> Path:
    override = os.environ.get("HELIX_GLOBAL_HOME", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / ".helix").resolve()


def _global_db_path() -> Path:
    return _global_root() / "global.db"


def _global_recipe_dir() -> Path:
    return _global_root() / "recipes"


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(f"PRAGMA journal_mode={PRAGMA_JOURNAL_MODE}")
    conn.execute(f"PRAGMA busy_timeout={PRAGMA_BUSY_TIMEOUT_MS}")
    return conn


def _json_load(value: str, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _redact_text(value: str) -> str:
    lowered = value.lower()
    tokens = ("password", "token", "secret", "apikey", "api_key", "authorization", "bearer", "/home")
    if any(token in lowered for token in tokens):
        return "[REDACTED]"
    return value


def _sanitize_recipe(recipe: dict[str, Any]) -> dict[str, Any]:
    def _walk(item: Any) -> Any:
        if isinstance(item, dict):
            sanitized: dict[str, Any] = {}
            for key, value in item.items():
                key_text = str(key)
                if any(token in key_text.lower() for token in ("password", "token", "secret", "apikey", "api_key", "authorization")):
                    sanitized[key_text] = "[REDACTED]"
                else:
                    sanitized[key_text] = _walk(value)
            return sanitized
        if isinstance(item, list):
            return [_walk(value) for value in item]
        if isinstance(item, str):
            return _redact_text(item)
        return item

    return _walk(recipe)


def init_global_db() -> str:
    """~/.helix/global.db を初期化し、DB パスを返す。"""
    root = _global_root()
    root.mkdir(parents=True, exist_ok=True)
    _global_recipe_dir().mkdir(parents=True, exist_ok=True)

    db_path = _global_db_path()
    conn = _connect(str(db_path))
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    return str(db_path)


def _load_local_recipes_by_run(project_root: Path) -> dict[int, dict[str, Any]]:
    recipes = list_recipes(str(project_root))
    mapped: dict[int, dict[str, Any]] = {}
    for recipe in recipes:
        source = recipe.get("source", {}) if isinstance(recipe, dict) else {}
        if not isinstance(source, dict):
            continue
        run_id = source.get("task_run_id")
        if isinstance(run_id, int):
            mapped[run_id] = recipe
    return mapped


def _project_root_from_local_db(local_db: str) -> Path:
    path = Path(local_db).resolve()
    parent = path.parent
    if parent.name == ".helix":
        return parent.parent
    return parent


def _project_id_short(project_root: Path) -> str:
    project_name = project_root.name or "project"
    digest = hashlib.sha1(str(project_root).encode("utf-8")).hexdigest()[:8]
    return f"{project_name}-{digest}"


def _safe_task_run_id(recipe: dict[str, Any], fallback: int) -> int:
    source = recipe.get("source", {}) if isinstance(recipe, dict) else {}
    if isinstance(source, dict):
        raw = source.get("task_run_id")
        if isinstance(raw, int):
            return raw
        if isinstance(raw, str) and raw.isdigit():
            return int(raw)
    return int(fallback)


def _build_recipe_id(project_root: Path, task_run_id: int, pattern_key: str) -> str:
    pattern_hash = hashlib.sha1(pattern_key.encode("utf-8")).hexdigest()[:10]
    return f"{_project_id_short(project_root)}-{int(task_run_id)}-{pattern_hash}"


def _copy_to_global_recipe(recipe: dict[str, Any], recipe_id: str, project_id: str, task_run_id: int) -> str:
    target = _global_recipe_dir() / f"{recipe_id}.json"
    sanitized = _sanitize_recipe(recipe)
    sanitized["recipe_id"] = recipe_id
    sanitized["project_id"] = project_id
    source = sanitized.get("source", {})
    if not isinstance(source, dict):
        source = {}
    source["task_run_id"] = int(task_run_id)
    source["project_id"] = project_id
    sanitized["source"] = source
    target.write_text(json.dumps(sanitized, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(target)


def sync_from_local(local_db: str, project_id: str) -> dict[str, Any]:
    """ローカル DB の成功レコードを global.db に同期する。"""
    if not Path(local_db).exists():
        raise ValueError(f"local db not found: {local_db}")

    global_db = init_global_db()
    project_root = _project_root_from_local_db(local_db)

    local_recipe_by_run = _load_local_recipes_by_run(project_root)

    local_conn = _connect(local_db)
    local_conn.row_factory = sqlite3.Row

    success_rows = local_conn.execute(
        "SELECT id, task_type FROM task_runs WHERE status = 'completed' ORDER BY id ASC"
    ).fetchall()
    total_by_task_type_rows = local_conn.execute(
        "SELECT task_type, COUNT(*) AS cnt FROM task_runs GROUP BY task_type"
    ).fetchall()
    total_by_task_type = {
        str(row["task_type"]): int(row["cnt"] or 0)
        for row in total_by_task_type_rows
    }
    local_conn.close()

    if not success_rows:
        return {
            "project_id": project_id,
            "synced_patterns": 0,
            "synced_runs": 0,
            "global_db": global_db,
        }

    grouped: dict[str, dict[str, Any]] = {}

    for row in success_rows:
        run_id = int(row["id"])
        task_type = str(row["task_type"] or "unknown")

        recipe = local_recipe_by_run.get(run_id)
        if recipe is None:
            try:
                recipe = analyze_success(run_id, local_db)
            except Exception as exc:  # noqa: BLE001
                print(
                    f"Warning: task_run_id={run_id} の解析に失敗したためスキップします: {exc}",
                    file=sys.stderr,
                )
                continue

        if recipe is None:
            print(
                f"Warning: task_run_id={run_id} は action_logs 不足のためスキップします。",
                file=sys.stderr,
            )
            continue
        if not isinstance(recipe, dict):
            print(
                f"Warning: task_run_id={run_id} の recipe 形式が不正のためスキップします。",
                file=sys.stderr,
            )
            continue

        pattern_key = str(recipe.get("pattern_key") or "").strip()
        if not pattern_key:
            continue
        task_run_id = _safe_task_run_id(recipe, run_id)
        recipe_id = _build_recipe_id(project_root, task_run_id, pattern_key)

        bucket = grouped.setdefault(
            pattern_key,
            {
                "pattern_key": pattern_key,
                "task_type": task_type,
                "success_count": 0,
                "quality_sum": 0.0,
                "tags": set(),
                "builder_type": "task",
                "recipe_ids": [],
                "sample_recipe": recipe,
                "latest_recipe_id": recipe_id,
                "latest_task_run_id": task_run_id,
            },
        )

        bucket["success_count"] += 1
        metrics = recipe.get("metrics", {}) if isinstance(recipe, dict) else {}
        if isinstance(metrics, dict):
            try:
                bucket["quality_sum"] += float(metrics.get("quality_score", 0.0) or 0.0)
            except (TypeError, ValueError):
                pass

        classification = recipe.get("classification", {}) if isinstance(recipe, dict) else {}
        if isinstance(classification, dict):
            builder_type = str(classification.get("builder_type") or "").strip()
            if builder_type:
                bucket["builder_type"] = builder_type
            tags = classification.get("tags", [])
            if isinstance(tags, list):
                for tag in tags:
                    bucket["tags"].add(str(tag))

        bucket["recipe_ids"].append(recipe_id)
        bucket["sample_recipe"] = recipe
        bucket["latest_recipe_id"] = recipe_id
        bucket["latest_task_run_id"] = task_run_id

    global_conn = _connect(global_db)
    global_conn.row_factory = sqlite3.Row

    synced = 0
    now = _now_iso()

    for pattern_key, bucket in grouped.items():
        sample_recipe = bucket["sample_recipe"]
        task_type = bucket["task_type"]
        success_count = int(bucket["success_count"])
        total_count = max(int(total_by_task_type.get(task_type, success_count) or success_count), success_count)
        success_rate = (success_count / total_count) if total_count > 0 else 0.0
        quality_mean = (float(bucket["quality_sum"]) / success_count) if success_count > 0 else 0.0

        recipe_id = str(bucket.get("latest_recipe_id") or _build_recipe_id(project_root, 0, pattern_key))
        task_run_id = int(bucket.get("latest_task_run_id") or 0)
        local_path = str(sample_recipe.get("_path") or "")
        global_path = _copy_to_global_recipe(sample_recipe, recipe_id, project_id, task_run_id)
        tags = sorted(bucket["tags"])

        context = {
            "project_id": project_id,
            "task_type": task_type,
            "success_count": success_count,
            "total_count": total_count,
            "recipe_ids": sorted(set(bucket["recipe_ids"])),
        }

        global_conn.execute(
            """
            INSERT INTO recipe_index (
                recipe_id,
                pattern_key,
                builder_type,
                project_id,
                success_rate,
                quality_score_mean,
                tags_json,
                context_json,
                local_path,
                global_path,
                promotion_status,
                success_count,
                total_count,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'none', ?, ?, ?, ?)
            ON CONFLICT(pattern_key, project_id)
            DO UPDATE SET
                recipe_id = excluded.recipe_id,
                builder_type = excluded.builder_type,
                success_rate = excluded.success_rate,
                quality_score_mean = excluded.quality_score_mean,
                tags_json = excluded.tags_json,
                context_json = excluded.context_json,
                local_path = excluded.local_path,
                global_path = excluded.global_path,
                success_count = excluded.success_count,
                total_count = excluded.total_count,
                updated_at = excluded.updated_at
            """,
            (
                recipe_id,
                pattern_key,
                str(bucket["builder_type"]),
                project_id,
                float(success_rate),
                float(quality_mean),
                _json_dump(tags),
                _json_dump(context),
                local_path,
                global_path,
                success_count,
                total_count,
                now,
                now,
            ),
        )
        synced += 1

    global_conn.commit()
    global_conn.close()

    return {
        "project_id": project_id,
        "synced_patterns": synced,
        "synced_runs": len(success_rows),
        "global_db": global_db,
    }


def _tokenize_query(query: str) -> list[str]:
    text = (query or "").strip().lower()
    if not text:
        return []
    return [token for token in _QUERY_TOKEN_PATTERN.split(text) if token]


def _score_global_row(tokens: list[str], row: dict[str, Any]) -> float:
    pattern_key = str(row.get("pattern_key") or "").lower()
    tags = {str(tag).lower() for tag in row.get("tags", [])}

    success_count = int(row.get("success_count", 0) or 0)
    quality_mean = float(row.get("quality_score_mean", 0.0) or 0.0)

    if not tokens:
        return min(success_count / 5.0, 1.0) * 60.0 + min(quality_mean / 100.0, 1.0) * 40.0

    pattern_hits = sum(1 for token in tokens if token in pattern_key)
    tag_hits = sum(1 for token in tokens if any(token in tag for tag in tags))

    pattern_score = (pattern_hits / len(tokens)) * 55.0
    tag_score = (tag_hits / len(tokens)) * 25.0
    success_score = min(success_count / 5.0, 1.0) * 10.0
    quality_score = min(quality_mean / 100.0, 1.0) * 10.0

    return pattern_score + tag_score + success_score + quality_score


def search_global(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """global.db の recipe_index を pattern_key / tags で検索する。"""
    db_path = init_global_db()
    conn = _connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT recipe_id, pattern_key, builder_type, project_id, success_rate,
               quality_score_mean, tags_json, context_json, local_path, global_path,
               promotion_status, success_count, total_count
        FROM recipe_index
        ORDER BY success_count DESC, quality_score_mean DESC, updated_at DESC
        """
    ).fetchall()
    conn.close()

    tokens = _tokenize_query(query)
    scored: list[dict[str, Any]] = []

    for row in rows:
        payload = dict(row)
        payload["tags"] = _json_load(str(payload.get("tags_json") or ""), [])
        payload["context"] = _json_load(str(payload.get("context_json") or ""), {})
        payload["score"] = round(_score_global_row(tokens, payload), 2)
        scored.append(payload)

    scored.sort(key=lambda item: item.get("score", 0.0), reverse=True)
    return scored[: max(1, int(limit))]


def get_recipe_by_id(recipe_id: str) -> dict[str, Any] | None:
    """recipe_id で recipe_index から 1 件取得する。"""
    clean_id = str(recipe_id or "").strip()
    if not clean_id:
        return None

    db_path = init_global_db()
    conn = _connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT recipe_id, pattern_key, builder_type, project_id, success_rate,
               quality_score_mean, tags_json, context_json, local_path, global_path,
               promotion_status, success_count, total_count
        FROM recipe_index
        WHERE recipe_id = ?
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        (clean_id,),
    ).fetchone()
    conn.close()

    if row is None:
        return None

    payload = dict(row)
    payload["tags"] = _json_load(str(payload.get("tags_json") or ""), [])
    payload["context"] = _json_load(str(payload.get("context_json") or ""), {})
    return payload


def get_promotion_candidates(threshold: int = 3) -> list[dict[str, Any]]:
    """昇格候補を返す（同一 pattern_key の成功回数しきい値）。"""
    db_path = init_global_db()
    conn = _connect(db_path)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT recipe_id, pattern_key, builder_type, project_id, success_rate,
               quality_score_mean, tags_json, context_json, local_path, global_path,
               promotion_status, success_count, total_count
        FROM recipe_index
        WHERE success_count >= ?
          AND COALESCE(promotion_status, 'none') NOT IN ('promoted', 'generated')
        ORDER BY success_count DESC, quality_score_mean DESC, success_rate DESC
        """,
        (max(1, int(threshold)),),
    ).fetchall()
    conn.close()

    candidates: list[dict[str, Any]] = []
    for row in rows:
        payload = dict(row)
        payload["tags"] = _json_load(str(payload.get("tags_json") or ""), [])
        payload["context"] = _json_load(str(payload.get("context_json") or ""), {})
        candidates.append(payload)
    return candidates


def record_promotion(
    recipe_id: str,
    artifact_type: str,
    builder_type: str,
    artifact_ref: str,
    status: str,
    project_id: str,
) -> str:
    """promotion_records に記録し、promotion_id を返す。"""
    db_path = init_global_db()
    conn = _connect(db_path)

    now = _now_iso()
    project_scope = str(project_id or "").strip()
    digest = hashlib.sha1(f"{recipe_id}|{project_scope}|{artifact_type}|{now}".encode("utf-8")).hexdigest()[:8]
    promotion_id = f"promo-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{digest}"

    conn.execute(
        """
        INSERT INTO promotion_records (
            promotion_id, recipe_id, artifact_type, builder_type, artifact_ref, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (promotion_id, recipe_id, artifact_type, builder_type, artifact_ref, status, now),
    )

    if project_scope:
        conn.execute(
            "UPDATE recipe_index SET promotion_status = ? WHERE recipe_id = ? AND project_id = ?",
            (status, recipe_id, project_scope),
        )
    else:
        conn.execute(
            "UPDATE recipe_index SET promotion_status = ? WHERE recipe_id = ?",
            (status, recipe_id),
        )

    conn.commit()
    conn.close()
    return promotion_id
