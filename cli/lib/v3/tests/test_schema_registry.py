from __future__ import annotations

import importlib
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import pytest

from cli.lib.v3.schema.ddl import migrate, schema_ddl
from cli.lib.v3.schema.enums import PlanKind
from cli.lib.v3.schema.identifiers import SchemaError, assert_sql_identifier
from cli.lib.v3.schema.registry import ColumnDef, INDEXES, SCHEMA_VERSION, TABLES, TABLE_BY_NAME, TableDef, validate_registry


def _statement_name(statement: str) -> str:
    match = re.match(r"^CREATE\s+(?:TABLE|INDEX)\s+IF\s+NOT\s+EXISTS\s+([A-Za-z_][A-Za-z0-9_]*)", statement)
    assert match, statement
    return match.group(1)


def test_ut_c1_01_schema_ddl_matches_registry_only() -> None:
    statements = schema_ddl()
    assert len(statements) == len(TABLES) + len(INDEXES)
    table_names = {_statement_name(statement) for statement in statements if statement.startswith("CREATE TABLE")}
    assert table_names == set(TABLE_BY_NAME)
    assert all(statement.startswith(("CREATE TABLE", "CREATE INDEX", "CREATE UNIQUE INDEX")) for statement in statements)


@pytest.mark.parametrize("name", ["1bad", "a-b", "drop;", ""])
def test_ut_c1_02_assert_sql_identifier_rejects_invalid_names(name: str) -> None:
    with pytest.raises(SchemaError):
        assert_sql_identifier(name)


def test_ut_c1_03_schema_import_validates_invalid_names(tmp_path: Path) -> None:
    package_dir = tmp_path / "bad_schema_pkg"
    package_dir.mkdir()
    source_init = Path(__file__).resolve().parents[1] / "schema" / "__init__.py"
    (package_dir / "__init__.py").write_text(source_init.read_text(encoding="utf-8"), encoding="utf-8")
    (package_dir / "identifiers.py").write_text(
        """
from cli.lib.v3.schema.identifiers import SQL_IDENTIFIER, SchemaError, assert_sql_identifier
""",
        encoding="utf-8",
    )
    (package_dir / "ddl.py").write_text(
        """
def index_ddl(index):
    return index.name


def migrate(db):
    return None


def schema_ddl():
    return []


def table_ddl(table):
    return table.name
""",
        encoding="utf-8",
    )
    (package_dir / "registry.py").write_text(
        """
from dataclasses import dataclass

from cli.lib.v3.schema.identifiers import SchemaError, assert_sql_identifier


@dataclass(frozen=True)
class ColumnDef:
    name: str
    sql_type: str
    primary_key: bool = False
    references: tuple[str, str] | None = None


@dataclass(frozen=True)
class TableDef:
    name: str
    kind: str
    columns: tuple[ColumnDef, ...]


@dataclass(frozen=True)
class IndexDef:
    name: str
    table_name: str
    column_names: tuple[str, ...]


TABLES = [TableDef(name="1bad", kind="projection", columns=(ColumnDef(name="id", sql_type="TEXT"),))]
INDEXES = []
SCHEMA_VERSION = 18
TABLE_BY_NAME = {table.name: table for table in TABLES}


def validate_registry(tables=None, indexes=None):
    tables = TABLES if tables is None else tables
    indexes = INDEXES if indexes is None else indexes
    for table in tables:
        assert_sql_identifier(table.name)
        for column in table.columns:
            assert_sql_identifier(column.name)
    for index in indexes:
        assert_sql_identifier(index.name)
        assert_sql_identifier(index.table_name)
""",
        encoding="utf-8",
    )
    sys.path.insert(0, str(tmp_path))
    try:
        with pytest.raises(SchemaError):
            importlib.import_module("bad_schema_pkg")
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop("bad_schema_pkg", None)
        sys.modules.pop("bad_schema_pkg.registry", None)


def test_ut_c1_04_table_kind_inventory_counts() -> None:
    counts = Counter(table.kind for table in TABLES)
    assert set(counts) == {"projection", "append_event", "config"}
    assert counts["projection"] == 49
    assert counts["append_event"] == 3
    assert counts["config"] == 6
    assert len(TABLES) == 58


def test_ut_c1_05_append_event_inventory() -> None:
    names = {table.name for table in TABLES if table.kind == "append_event"}
    assert names == {"test_result_events", "guardrail_decisions", "hook_events"}


def test_ut_c1_06_config_inventory() -> None:
    names = {table.name for table in TABLES if table.kind == "config"}
    assert names == {
        "impact_rules",
        "mcp_server_profiles",
        "mcp_profile_triggers",
        "verification_profiles",
        "document_export_profiles",
        "document_export_triggers",
    }


def test_ut_c1_07_schema_version_is_18() -> None:
    assert SCHEMA_VERSION == 18


def test_ut_c1_08_cross_db_foreign_keys_are_rejected() -> None:
    bad_table = TableDef(
        name="bad_fk_table",
        kind="projection",
        columns=(
            ColumnDef(name="id", sql_type="TEXT", primary_key=True),
            ColumnDef(name="plan_id", sql_type="TEXT", references=("other_db.plan_registry", "id")),
        ),
    )
    with pytest.raises(SchemaError):
        validate_registry([bad_table], [])


def test_ut_c1_09_plan_kind_inventory() -> None:
    values = {member.value for member in PlanKind}
    assert values == {
        "impl",
        "design",
        "poc",
        "reverse",
        "add-design",
        "add-impl",
        "refactor",
        "retrofit",
        "recovery",
        "troubleshoot",
        "research",
    }
    assert "charter" not in values


def test_ut_c1_10_table_by_name_covers_all_tables() -> None:
    assert len(TABLE_BY_NAME) == len(TABLES) == 58
    assert set(TABLE_BY_NAME) == {table.name for table in TABLES}


def test_ut_c1_10b_migrate_is_idempotent() -> None:
    conn = sqlite3.connect(":memory:")
    try:
        migrate(conn)
        first_tables = conn.execute(
            "SELECT count(*) FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchone()[0]
        migrate(conn)
        second_tables = conn.execute(
            "SELECT count(*) FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchone()[0]
        user_version = conn.execute("PRAGMA user_version").fetchone()[0]
    finally:
        conn.close()
    assert first_tables == second_tables == len(TABLES)
    assert user_version == SCHEMA_VERSION


def test_ut_c1_11_indexes_match_registry_constraints() -> None:
    """DoD 検証: L7-v3-engine-c1-schema-registryplan UT-C1-11"""
    assert len(INDEXES) == 41
    assert TABLE_BY_NAME["test_result_events"].logical_keys == (("ut_id", "run_id", "seq"),)
    for index in INDEXES:
        assert_sql_identifier(index.name)
        table = TABLE_BY_NAME[index.table_name]
        table_columns = {column.name for column in table.columns}
        assert index.column_names
        for column_name in index.column_names:
            assert_sql_identifier(column_name)
            assert column_name in table_columns


def test_ut_c1_12_migrate_applies_all_tables_and_indexes_in_memory_sqlite() -> None:
    """DoD 検証: L7-v3-engine-c1-schema-registryplan UT-C1-12"""
    conn = sqlite3.connect(":memory:")
    try:
        migrate(conn)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        indexes = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    finally:
        conn.close()

    assert len(tables) == len(TABLES) == 58
    assert len(indexes) == len(INDEXES) == 41
    assert {name for (name,) in tables} == set(TABLE_BY_NAME)
    assert {name for (name,) in indexes} == {index.name for index in INDEXES}
