from __future__ import annotations

import hashlib
import sqlite3

from cli.lib.v3.schema.registry import TableDef

LOCAL_LOGICAL_KEYS: dict[str, tuple[str, ...]] = {
    "artifact_registry": ("path",),
    "document_export_artifacts": ("path", "hash"),
    "findings": ("kind", "severity", "subject_id", "source", "status"),
    "gate_runs": ("gate_id", "plan_id", "checked_at"),
    "plan_registry": ("plan_id",),
    "trace_edges": ("from_artifact", "to_artifact", "edge_kind"),
}


def stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _logical_keys(table: TableDef) -> tuple[str, ...]:
    if table.logical_keys:
        candidate = table.logical_keys[0]
        return tuple(candidate if isinstance(candidate, tuple) else tuple(candidate))
    primary_key = next((column.name for column in table.columns if column.primary_key), None)
    if primary_key is not None and table.name not in LOCAL_LOGICAL_KEYS:
        return (primary_key,)
    return LOCAL_LOGICAL_KEYS.get(table.name, ())


def upsert_row(db: sqlite3.Connection, table: TableDef, row: dict[str, object]) -> str:
    logical_keys = _logical_keys(table)
    row_to_write = dict(row)
    primary_key = next(column.name for column in table.columns if column.primary_key)

    if primary_key not in row_to_write:
        if primary_key in logical_keys and primary_key in row_to_write:
            row_to_write[primary_key] = row_to_write[primary_key]
        elif len(logical_keys) == 1:
            row_to_write[primary_key] = stable_id(table.name, str(row_to_write[logical_keys[0]]))
        else:
            logical_value = "|".join(str(row_to_write[key]) for key in logical_keys)
            row_to_write[primary_key] = stable_id(table.name, logical_value)

    conflict_keys = logical_keys if logical_keys else (primary_key,)
    where_clause = " AND ".join(f"{column}=?" for column in conflict_keys)
    existing = db.execute(
        f"SELECT {primary_key} FROM {table.name} WHERE {where_clause}",
        tuple(row_to_write[column] for column in conflict_keys),
    ).fetchone()
    if existing is not None:
        row_to_write[primary_key] = existing[0]
        assignments = [column for column in row_to_write if column != primary_key]
        if assignments:
            update_sql = (
                f"UPDATE {table.name} SET "
                + ", ".join(f"{column}=?" for column in assignments)
                + f" WHERE {primary_key}=?"
            )
            db.execute(
                update_sql,
                tuple(row_to_write[column] for column in assignments) + (row_to_write[primary_key],),
            )
        return str(row_to_write[primary_key])

    column_names = list(row_to_write)
    placeholders = ", ".join("?" for _ in column_names)
    insert_sql = f"INSERT INTO {table.name} ({', '.join(column_names)}) VALUES ({placeholders})"
    db.execute(insert_sql, tuple(row_to_write[column] for column in column_names))
    return str(row_to_write[primary_key])
