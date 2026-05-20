"""契約: PLAN-093 §5

helix doctor 用の PLAN registry advisory checks。
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from . import plan_parser
except ImportError:  # pragma: no cover
    import plan_parser


STALE_GENERATES_DAYS = 30
L2_BIG_PICTURE_KINDS = {"design"}
L2_BIG_PICTURE_LAYERS = {"L2"}


def _project_root() -> Path:
    configured = os.environ.get("HELIX_PROJECT_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path.cwd().resolve()


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {str(row[0]) for row in rows}


def _missing_tables_result(required: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "status": "warning",
            "reason": "missing_tables",
            "missing_tables": required,
        }
    ]


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    for parser in (
        lambda raw: datetime.fromisoformat(raw),
        lambda raw: datetime.strptime(raw, "%Y-%m-%d %H:%M:%S"),
        lambda raw: datetime.strptime(raw, "%Y-%m-%d"),
    ):
        try:
            parsed = parser(text)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def _days_stale(updated_at: Any) -> int | None:
    parsed = _parse_timestamp(updated_at)
    if parsed is None:
        return None
    return (datetime.now(timezone.utc) - parsed).days


def _artifact_path(path_text: str) -> Path:
    artifact = Path(path_text)
    if artifact.is_absolute():
        return artifact
    return _project_root() / artifact


def _related_adr_present(value: Any) -> bool:
    if value is None:
        return False
    return any(part.strip() for part in str(value).split(","))


def _normalize_cycle(cycle: list[str]) -> tuple[str, ...]:
    if len(cycle) <= 1:
        return tuple(cycle)
    nodes = cycle[:-1] if cycle[0] == cycle[-1] else cycle[:]
    if not nodes:
        return tuple(cycle)
    rotations = [tuple(nodes[index:] + nodes[:index]) for index in range(len(nodes))]
    canonical = min(rotations)
    return canonical + (canonical[0],)


def run_check_plan_drift(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """契約: PLAN-093 §5.2."""
    required_tables = {"plan_generates", "plan_registry"}
    table_names = _table_names(conn)
    missing = sorted(required_tables - table_names)
    if missing:
        return _missing_tables_result(missing)

    rows = conn.execute(
        """
        SELECT
            g.plan_id,
            g.artifact_path,
            g.artifact_type,
            p.status,
            p.updated_at
        FROM plan_generates AS g
        LEFT JOIN plan_registry AS p ON p.plan_id = g.plan_id
        ORDER BY g.plan_id, g.artifact_path
        """
    ).fetchall()

    results: list[dict[str, Any]] = []
    with conn:
        for row in rows:
            plan_id = str(row[0])
            artifact_path = str(row[1])
            artifact_type = str(row[2])
            plan_status = str(row[3] or "")
            updated_at = row[4]
            artifact_exists = _artifact_path(artifact_path).exists()
            conn.execute(
                """
                UPDATE plan_generates
                SET exists_check = ?, last_checked_at = datetime('now')
                WHERE plan_id = ? AND artifact_path = ?
                """,
                (1 if artifact_exists else 0, plan_id, artifact_path),
            )

            reason = "ok"
            status = "ok"
            days_stale = _days_stale(updated_at)
            if not artifact_exists:
                reason = "missing_artifact"
                status = "warning"
            elif plan_status == "active" and days_stale is not None and days_stale > STALE_GENERATES_DAYS:
                reason = "stale_generates"
                status = "warning"

            results.append(
                {
                    "plan_id": plan_id,
                    "artifact_path": artifact_path,
                    "artifact_type": artifact_type,
                    "status": status,
                    "reason": reason,
                    "days_stale": days_stale,
                }
            )

    return results


def run_check_plan_cycle(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """契約: PLAN-093 §5.5."""
    required_tables = {"plan_dependencies"}
    table_names = _table_names(conn)
    missing = sorted(required_tables - table_names)
    if missing:
        return _missing_tables_result(missing)

    plan_ids = sorted(
        {
            str(row[0])
            for row in conn.execute(
                """
                SELECT plan_id FROM plan_dependencies
                UNION
                SELECT dep_plan_id FROM plan_dependencies
                """
            ).fetchall()
            if row[0]
        }
    )

    results: list[dict[str, Any]] = []
    seen_cycles: set[tuple[str, ...]] = set()
    for plan_id in plan_ids:
        cycle = plan_parser.detect_cycle(conn, plan_id)
        cycle_key = _normalize_cycle(cycle)
        if not cycle or cycle_key in seen_cycles:
            continue
        seen_cycles.add(cycle_key)
        results.append(
            {
                "plan_id": plan_id,
                "cycle": cycle,
                "status": "warning",
                "reason": "dependency_cycle",
            }
        )
    return results


def run_check_plan_adr_snapshot(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """契約: PLAN-093 §5."""
    required_tables = {"plan_registry", "plan_generates"}
    table_names = _table_names(conn)
    missing = sorted(required_tables - table_names)
    if missing:
        return _missing_tables_result(missing)

    adr_snapshot_plan_ids = {
        str(row[0])
        for row in conn.execute(
            "SELECT DISTINCT plan_id FROM plan_generates WHERE artifact_type = 'adr_snapshot'"
        ).fetchall()
        if row[0]
    }

    rows = conn.execute(
        """
        SELECT plan_id, kind, layer, related_adr, doc_path
        FROM plan_registry
        WHERE kind = 'design' OR layer = 'L2'
        ORDER BY plan_id
        """
    ).fetchall()

    results: list[dict[str, Any]] = []
    for row in rows:
        plan_id = str(row[0])
        kind = str(row[1] or "")
        layer = str(row[2] or "")
        related_adr = row[3]
        doc_path = str(row[4] or "")

        has_big_picture_decision = kind in L2_BIG_PICTURE_KINDS or layer in L2_BIG_PICTURE_LAYERS
        has_adr_snapshot = plan_id in adr_snapshot_plan_ids or _related_adr_present(related_adr)
        if not has_big_picture_decision or has_adr_snapshot:
            continue

        results.append(
            {
                "plan_id": plan_id,
                "kind": kind,
                "layer": layer,
                "doc_path": doc_path,
                "status": "warning",
                "reason": "missing_adr_snapshot",
            }
        )
    return results
