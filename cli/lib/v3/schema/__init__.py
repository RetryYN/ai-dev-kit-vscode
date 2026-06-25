from .ddl import index_ddl, migrate, schema_ddl, table_ddl
from .identifiers import SQL_IDENTIFIER, SchemaError, assert_sql_identifier
from .registry import INDEXES, SCHEMA_VERSION, TABLES, TABLE_BY_NAME, ColumnDef, IndexDef, TableDef, validate_registry

validate_registry()

__all__ = [
    "ColumnDef",
    "IndexDef",
    "INDEXES",
    "SCHEMA_VERSION",
    "SQL_IDENTIFIER",
    "SchemaError",
    "TABLES",
    "TABLE_BY_NAME",
    "TableDef",
    "assert_sql_identifier",
    "index_ddl",
    "migrate",
    "schema_ddl",
    "table_ddl",
    "validate_registry",
]
