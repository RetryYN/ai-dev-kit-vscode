from __future__ import annotations

from collections import defaultdict
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

import helix_db

from .base import BaseDetector, DetectorResult


def _project_root(db_path: str | Path) -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root)
    target = Path(db_path).resolve()
    if target.parent.name == ".helix":
        return target.parent.parent
    return Path.cwd()


def _table_name(conn: sqlite3.Connection) -> str | None:
    for table_name in ("skill_usage",):
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
            (table_name,),
        ).fetchone()
        if row is not None:
            return table_name
    return None


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row[1]) for row in rows}


def _load_usage_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    table_name = _table_name(conn)
    if table_name is None:
        return []

    columns = _table_columns(conn, table_name)
    if "skill_id" not in columns or "outcome" not in columns:
        return []

    query = "SELECT skill_id, outcome"
    if "created_at" in columns:
        query += ", created_at"
    query += " FROM skill_usage"
    if "created_at" in columns:
        query += " WHERE datetime(created_at) >= datetime('now', '-30 days')"
    query += " ORDER BY skill_id"

    rows = conn.execute(query).fetchall()
    return [{key: row[key] for key in row.keys()} for row in rows]


def _extract_skill_ids(skill_map_path: Path) -> list[str]:
    try:
        text = skill_map_path.read_text(encoding="utf-8")
    except OSError:
        return []

    section_marker = "## スキル群配置"
    start = text.find(section_marker)
    if start < 0:
        return []

    section = text[start:]
    end_markers = [section.find("\n## ", 1), section.find("\n### ", 1)]
    end_candidates = [marker for marker in end_markers if marker > 0]
    section = section[: min(end_candidates)] if end_candidates else section

    skill_ids: list[str] = []
    seen: set[str] = set()
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2 or cells[0] == "カテゴリ":
            continue
        second_cell = cells[1]
        chunks = [
            chunk.strip(" `*_")
            for chunk in second_cell.replace("・", ",").replace("/", ",").split(",")
        ]
        for chunk in chunks:
            if not chunk:
                continue
            token = chunk.split()[0].strip("`*_")
            if not token:
                continue
            if not all(part and part.replace("-", "").replace("_", "").isalnum() for part in token.split("/")):
                continue
            if token in seen:
                continue
            seen.add(token)
            skill_ids.append(token)
    return skill_ids


class Axis04SkillDecay(BaseDetector):
    id = "axis-04"
    name = "skill resolution decay"
    phase_gate = None
    kind = "detector"

    def run(self, db_path: str | Path) -> DetectorResult:
        started = time.perf_counter()
        target_db = Path(db_path)
        helix_db._prepare_db_path(str(target_db))
        conn = helix_db.get_connection(target_db)
        try:
            usage_rows = _load_usage_rows(conn)
        finally:
            conn.close()

        root = _project_root(db_path)
        skill_map_path = root / "skills" / "SKILL_MAP.md"
        registered_skill_ids = _extract_skill_ids(skill_map_path)

        if not registered_skill_ids:
            cost_ms = max(1, int((time.perf_counter() - started) * 1000))
            return DetectorResult(
                verdict="blocked",
                findings=[],
                cost_ms=cost_ms,
                raw={
                    "reason": "skills/SKILL_MAP.md から skill list を取得できません",
                    "project_root": str(root),
                },
            )

        usage_totals: dict[str, int] = defaultdict(int)
        failure_totals: dict[str, int] = defaultdict(int)
        for row in usage_rows:
            skill_id = str(row.get("skill_id") or "").strip()
            if not skill_id:
                continue
            usage_totals[skill_id] += 1
            if str(row.get("outcome") or "").strip().lower() == "failed":
                failure_totals[skill_id] += 1

        findings: list[dict[str, Any]] = []
        for skill_id in registered_skill_ids:
            usage_count = usage_totals.get(skill_id, 0)
            if usage_count == 0:
                findings.append(
                    {
                        "skill_id": skill_id,
                        "kind": "unused",
                        "usage_count": 0,
                    }
                )
                continue

            fail_count = failure_totals.get(skill_id, 0)
            fail_ratio = fail_count / usage_count if usage_count else 0.0
            if fail_ratio > 0.30:
                findings.append(
                    {
                        "skill_id": skill_id,
                        "kind": "failing",
                        "usage_count": usage_count,
                        "fail_ratio": round(fail_ratio, 3),
                    }
                )

        verdict: str = "passed" if not findings else "failed"
        cost_ms = max(1, int((time.perf_counter() - started) * 1000))
        return DetectorResult(
            verdict=verdict,
            findings=findings,
            cost_ms=cost_ms,
            raw={
                "project_root": str(root),
                "skill_count": len(registered_skill_ids),
                "usage_rows": len(usage_rows),
                "window_days": 30,
            },
        )
