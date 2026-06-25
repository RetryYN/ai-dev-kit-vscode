from __future__ import annotations

import sqlite3

from .registry import INDEXES, SCHEMA_VERSION, TABLES, ColumnDef, IndexDef, TableDef, validate_registry


def _column_ddl(column: ColumnDef) -> str:
    parts = [column.name, column.sql_type]
    if column.primary_key:
        parts.append("PRIMARY KEY")
    elif not column.nullable:
        parts.append("NOT NULL")
    if column.references is not None:
        target_table, target_column = column.references
        parts.append(f"REFERENCES {target_table}({target_column})")
    return " ".join(parts)


def table_ddl(table: TableDef) -> str:
    columns = ", ".join(_column_ddl(column) for column in table.columns)
    return f"CREATE TABLE IF NOT EXISTS {table.name} ({columns})"


def index_ddl(index: IndexDef) -> str:
    qualifier = "UNIQUE " if index.unique else ""
    column_sql = ", ".join(index.column_names)
    return f"CREATE {qualifier}INDEX IF NOT EXISTS {index.name} ON {index.table_name} ({column_sql})"


def schema_ddl() -> list[str]:
    validate_registry()
    return [table_ddl(table) for table in TABLES] + [index_ddl(index) for index in INDEXES]


def migrate(db: sqlite3.Connection) -> None:
    validate_registry()
    for statement in schema_ddl():
        db.execute(statement)
    db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    db.commit()
