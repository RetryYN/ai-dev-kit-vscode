from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass

from cli.lib.v3.schema import registry

from .projectors import PROJECTORS, ProjectionContext, record_parse_failures
from .sources import SourceRecord, load_sources
from .upsert import upsert_row


@dataclass(frozen=True)
class RebuildResult:
    counts: dict[str, int]
    warnings: tuple[str, ...]
    fails: tuple[str, ...]


def truncate_projection_tables(db: sqlite3.Connection) -> None:
    for table in registry.TABLES:
        if table.kind == "projection":
            db.execute(f"DELETE FROM {table.name}")


def _coerce_sources(sources: os.PathLike[str] | str | list[SourceRecord]) -> list[SourceRecord]:
    if isinstance(sources, (str, os.PathLike)):
        return load_sources(sources)
    return list(sources)


def rebuild_projection(
    db: sqlite3.Connection,
    sources: os.PathLike[str] | str | list[SourceRecord],
) -> RebuildResult:
    records = _coerce_sources(sources)
    ctx = ProjectionContext(db=db, sources=records)
    db.execute("BEGIN IMMEDIATE")
    try:
        truncate_projection_tables(db)
        record_parse_failures(ctx)
        for project_fn in PROJECTORS:
            project_fn(ctx)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return RebuildResult(counts=dict(ctx.counts), warnings=tuple(ctx.warnings), fails=tuple(ctx.fails))


def append_event(db: sqlite3.Connection, event: dict[str, object]) -> dict[str, str]:
    payload = dict(event)
    table_name = str(payload.pop("table"))
    table = registry.TABLE_BY_NAME[table_name]
    if table.kind != "append_event":
        raise ValueError(f"append_event target must be append_event table: {table_name}")
    row_id = upsert_row(db, table, payload)
    db.commit()
    return {"table": table_name, "id": row_id}
