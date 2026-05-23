#!/usr/bin/env python3
"""HELIX workspace state snapshot generator (PLAN-156 / ADR-040 D3)."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path


def _now_iso8601() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def generate_snapshot(
    project_root: Path,
    target_path: Path,
    *,
    task_id: str,
    base_sha: str,
) -> dict:
    """Generate snapshot json using plan_registry + handover + memory metadata."""
    payload = {
        "schema_version": 1,
        "task_id": task_id,
        "base_sha": base_sha,
        "generated_at": _now_iso8601(),
        "plan_registry": _extract_plan_registry(project_root, task_id),
        "handover_snapshot": _extract_handover_snapshot(project_root),
        "memory_links": _extract_memory_links(project_root, task_id),
    }
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def _extract_plan_registry(project_root: Path, task_id: str) -> list[dict]:
    """Extract task plan + related parent/requires/blocks plans from helix.db."""
    db_path = project_root / ".helix" / "helix.db"
    if not db_path.exists():
        return []

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            if not _table_exists(conn, "plan_registry"):
                return []

            related_ids = _collect_related_plan_ids(conn, task_id)
            if not related_ids:
                return []

            parent_map = _load_parent_map(conn, related_ids)
            rows = _select_plan_rows(conn, related_ids[:50])
    except (OSError, sqlite3.Error):
        return []

    order = {plan_id: index for index, plan_id in enumerate(related_ids)}
    payload = []
    for row in rows:
        item = {
            "plan_id": row["plan_id"],
            "title": row["title"],
            "status": row["status"],
            "kind": row["kind"],
            "drive": row["drive"],
            "layer": row["layer"],
            "parent": parent_map.get(row["plan_id"]),
        }
        payload.append(item)
    payload.sort(key=lambda item: order.get(item["plan_id"], len(order)))
    return payload[:50]


def _extract_handover_snapshot(project_root: Path) -> dict:
    """Extract read-only handover snapshot from CURRENT.json."""
    handover_path = project_root / ".helix" / "handover" / "CURRENT.json"
    if not handover_path.exists():
        return {}

    try:
        payload = json.loads(handover_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    task = payload.get("task") if isinstance(payload, dict) else {}
    if not isinstance(task, dict):
        task = {}
    next_actions = payload.get("next_actions", [])
    if not isinstance(next_actions, list):
        next_actions = []

    return {
        "task": {
            "id": task.get("id"),
            "title": task.get("title"),
            "status": task.get("status"),
        },
        "phase": payload.get("phase"),
        "sprint": payload.get("sprint"),
        "next_actions": next_actions,
    }


def _extract_memory_links(project_root: Path, task_id: str) -> list[str]:
    """Extract MEMORY.md lines containing the target task id."""
    memory_path = os.environ.get("HELIX_MEMORY_PATH")
    if memory_path:
        candidate = Path(memory_path).expanduser()
    else:
        slug = project_root.resolve().as_posix().replace("/", "-")
        candidate = Path.home() / ".claude" / "projects" / slug / "memory" / "MEMORY.md"

    if not candidate.exists():
        return []

    try:
        lines = candidate.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    matches: list[str] = []
    for line in lines:
        if task_id not in line:
            continue
        entry = line.strip()
        if not entry or entry in matches:
            continue
        matches.append(entry)
        if len(matches) >= 20:
            break
    return matches


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _collect_related_plan_ids(conn: sqlite3.Connection, task_id: str) -> list[str]:
    related_ids: list[str] = []

    def _append(plan_id: str | None) -> None:
        if not plan_id or plan_id in related_ids:
            return
        related_ids.append(plan_id)

    _append(task_id)
    if not _table_exists(conn, "plan_dependencies"):
        return related_ids

    rows = conn.execute(
        """
        SELECT dep_type, dep_plan_id
        FROM plan_dependencies
        WHERE plan_id = ?
          AND dep_type IN ('parent', 'requires', 'blocks')
        ORDER BY id ASC
        """,
        (task_id,),
    ).fetchall()
    for row in rows:
        _append(row["dep_plan_id"])
    return related_ids


def _load_parent_map(conn: sqlite3.Connection, plan_ids: list[str]) -> dict[str, str | None]:
    if not plan_ids or not _table_exists(conn, "plan_dependencies"):
        return {}
    placeholders = ",".join("?" for _ in plan_ids)
    rows = conn.execute(
        f"""
        SELECT plan_id, dep_plan_id
        FROM plan_dependencies
        WHERE dep_type = 'parent'
          AND plan_id IN ({placeholders})
        """,
        plan_ids,
    ).fetchall()
    return {row["plan_id"]: row["dep_plan_id"] for row in rows}


def _select_plan_rows(conn: sqlite3.Connection, plan_ids: list[str]) -> list[sqlite3.Row]:
    if not plan_ids:
        return []
    placeholders = ",".join("?" for _ in plan_ids)
    rows = conn.execute(
        f"""
        SELECT plan_id, title, status, kind, drive, layer
        FROM plan_registry
        WHERE plan_id IN ({placeholders})
        """,
        plan_ids,
    ).fetchall()
    return list(rows)
