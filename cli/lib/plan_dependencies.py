from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Any

from plan_deps_helper import dependency_payload, list_plan_doc_paths, load_plan_frontmatter


def load_dependencies(plan_id: str, project_root: str | Path | None = None) -> dict[str, Any]:
    """Return the normalized dependency mapping for one PLAN."""
    payload = dependency_payload(plan_id, project_root)
    return payload.get("dependencies", {"parent": None, "requires": [], "blocks": []})


def _resolve_db_path(db_path: str | None = None) -> str:
    if db_path:
        return db_path
    env_path = os.environ.get("HELIX_DB_PATH")
    if env_path:
        return env_path
    return str(Path(__file__).resolve().parents[2] / ".helix" / "helix.db")


def _dependency_rows(plan_id: str, deps: dict[str, Any]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    parent = deps.get("parent")
    if isinstance(parent, str) and parent.strip():
        rows.append((plan_id, "parent", parent.strip()))

    for dep_type in ("requires", "blocks"):
        for dep_plan_id in deps.get(dep_type, []) or []:
            if isinstance(dep_plan_id, str) and dep_plan_id.strip():
                rows.append((plan_id, dep_type, dep_plan_id.strip()))
    return rows


def save_dependencies(plan_id: str, deps: dict[str, Any], db_path: str | None = None) -> None:
    """Upsert dependency rows for one PLAN into helix.db."""
    database = _resolve_db_path(db_path)
    conn = sqlite3.connect(database)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS plan_dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id TEXT NOT NULL,
                dep_type TEXT NOT NULL,
                dep_plan_id TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE (plan_id, dep_type, dep_plan_id)
            )
            """
        )
        conn.execute("DELETE FROM plan_dependencies WHERE plan_id = ?", (plan_id,))
        rows = _dependency_rows(plan_id, deps)
        if rows:
            conn.executemany(
                "INSERT OR IGNORE INTO plan_dependencies(plan_id, dep_type, dep_plan_id) VALUES (?, ?, ?)",
                rows,
            )
        conn.commit()
    finally:
        conn.close()


def check_reciprocal(plan_id: str, project_root: str | Path | None = None) -> list[str]:
    """Warn when required plans do not reciprocally block the current plan."""
    project = Path(project_root) if project_root else Path.cwd()
    warnings: list[str] = []

    try:
        my_deps = dependency_payload(plan_id, project).get("dependencies", {})
        for requirement in my_deps.get("requires", []):
            req_id = re.sub(r"\s.*", "", requirement)
            try:
                their_deps = dependency_payload(req_id, project).get("dependencies", {})
            except Exception:
                warnings.append(f"WARN: {plan_id} requires {req_id} but {req_id} doc not found")
                continue

            if plan_id not in their_deps.get("blocks", []):
                warnings.append(f"WARN: {plan_id} requires {req_id} but {req_id} does not block {plan_id}")
    except Exception as exc:
        warnings.append(f"WARN: Could not load {plan_id}: {exc}")

    return warnings


def build_graph(project_root: str | Path | None = None) -> dict[str, dict[str, list[str]]]:
    """Build a simple requires/blocks graph for every PLAN document."""
    project = Path(project_root) if project_root else Path.cwd()
    graph: dict[str, dict[str, list[str]]] = {}

    for doc_path in list_plan_doc_paths(project):
        try:
            raw_plan_id = re.sub(r"\.md$", "", doc_path.name)
            frontmatter = load_plan_frontmatter(raw_plan_id, project)
        except Exception:
            continue
        plan_id = frontmatter.get("plan_id")
        if not isinstance(plan_id, str) or not plan_id:
            continue
        try:
            payload = dependency_payload(plan_id, project)
        except Exception:
            continue
        deps = payload.get("dependencies", {})
        graph[plan_id] = {
            "requires": deps.get("requires", []),
            "blocks": deps.get("blocks", []),
        }

    return graph
