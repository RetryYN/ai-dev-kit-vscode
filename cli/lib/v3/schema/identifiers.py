from __future__ import annotations

import re


class SchemaError(ValueError):
    """Raised when the schema registry violates a fail-close contract."""


SQL_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def assert_sql_identifier(name: str) -> None:
    if not isinstance(name, str) or not SQL_IDENTIFIER.fullmatch(name):
        raise SchemaError(f"invalid SQL identifier: {name!r}")
