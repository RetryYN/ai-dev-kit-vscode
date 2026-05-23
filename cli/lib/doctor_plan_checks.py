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

# 新 15 工程 (commit eeb0530): kind=impl は process_layer=L7 + parent_design 必須。
IMPL_KIND = "impl"
REQUIRED_PROCESS_LAYER_FOR_IMPL = "L7"


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


def run_check_process_layer(conn: sqlite3.Connection | None = None) -> list[dict[str, Any]]:
    """新 15 工程契約: kind=impl は process_layer=L7 必須 (warn-only P1)。

    V2 完全移行 (2026-05-24): V1 legacy PLAN (is_reference: true) は check 対象外。
    L<NN>-<slug>plan 形式 (V2) のみ製本対象。
    frontmatter 直接 parse 方式 (plan_registry schema 拡張不要)。
    """
    plans_dir = _project_root() / "docs" / "plans"
    if not plans_dir.exists():
        return []

    results: list[dict[str, Any]] = []
    # PLAN-* (V1 legacy) + L*plan (V2) の両方を scan
    plan_files = list(plans_dir.glob("PLAN-*.md")) + list(plans_dir.glob("L*plan.md"))
    for plan_path in sorted(set(plan_files)):
        frontmatter = plan_parser.parse_frontmatter(str(plan_path))
        if not frontmatter:
            continue
        # V1 legacy reference は skip (V2 製本対象外)
        if frontmatter.get("is_reference") is True:
            continue
        plan_id = str(frontmatter.get("plan_id") or plan_path.stem)
        kind = str(frontmatter.get("kind") or "")
        if kind != IMPL_KIND:
            continue

        process_layer = frontmatter.get("process_layer")
        if process_layer is None:
            results.append(
                {
                    "plan_id": plan_id,
                    "doc_path": str(plan_path.relative_to(_project_root())),
                    "status": "warning",
                    "reason": "missing_process_layer",
                    "expected": REQUIRED_PROCESS_LAYER_FOR_IMPL,
                }
            )
        elif process_layer != REQUIRED_PROCESS_LAYER_FOR_IMPL:
            results.append(
                {
                    "plan_id": plan_id,
                    "doc_path": str(plan_path.relative_to(_project_root())),
                    "status": "warning",
                    "reason": "wrong_process_layer",
                    "actual": process_layer,
                    "expected": REQUIRED_PROCESS_LAYER_FOR_IMPL,
                }
            )
    return results


def run_check_parent_design_existence(conn: sqlite3.Connection | None = None) -> list[dict[str, Any]]:
    """新 15 工程契約: kind=impl は parent_design 必須 + path 存在確認 (warn-only P1)。

    V2 完全移行 (2026-05-24): V1 legacy PLAN (is_reference: true) は check 対象外。
    parent_design は L6 機能設計 doc を指す (V-model L6↔L7 pair freeze)。
    """
    plans_dir = _project_root() / "docs" / "plans"
    if not plans_dir.exists():
        return []

    results: list[dict[str, Any]] = []
    plan_files = list(plans_dir.glob("PLAN-*.md")) + list(plans_dir.glob("L*plan.md"))
    for plan_path in sorted(set(plan_files)):
        frontmatter = plan_parser.parse_frontmatter(str(plan_path))
        if not frontmatter:
            continue
        if frontmatter.get("is_reference") is True:
            continue
        plan_id = str(frontmatter.get("plan_id") or plan_path.stem)
        kind = str(frontmatter.get("kind") or "")
        if kind != IMPL_KIND:
            continue

        parent_design = frontmatter.get("parent_design")
        if not parent_design:
            results.append(
                {
                    "plan_id": plan_id,
                    "doc_path": str(plan_path.relative_to(_project_root())),
                    "status": "warning",
                    "reason": "missing_parent_design",
                }
            )
            continue

        parent_path = _project_root() / str(parent_design)
        if not parent_path.exists():
            results.append(
                {
                    "plan_id": plan_id,
                    "doc_path": str(plan_path.relative_to(_project_root())),
                    "status": "warning",
                    "reason": "parent_design_not_found",
                    "parent_design": str(parent_design),
                }
            )
    return results
