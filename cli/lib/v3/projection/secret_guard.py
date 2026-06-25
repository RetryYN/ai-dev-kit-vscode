from __future__ import annotations

import re

from cli.lib.v3.schema.registry import TableDef

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{12,}|api[_-]?key|secret|token|password|-----BEGIN|AKIA[0-9A-Z]{16})",
    re.IGNORECASE,
)
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
TRANSCRIPT_PATTERN = re.compile(r"(^|\n)\s*(system|user|assistant):", re.IGNORECASE)


class SensitivePayloadError(ValueError):
    """Raised when projection input contains a likely secret or raw transcript."""


def _exempt_columns(table: TableDef) -> set[str]:
    return {
        column.name
        for column in table.columns
        if column.primary_key or column.name.endswith("_id") or column.references is not None
    }


def assert_no_sensitive_payload(row: dict[str, object], table: TableDef) -> None:
    exempt = _exempt_columns(table)
    for column_name, value in row.items():
        if column_name in exempt or not isinstance(value, str):
            continue
        if SECRET_PATTERN.search(value) or EMAIL_PATTERN.search(value) or SSN_PATTERN.search(value):
            raise SensitivePayloadError(f"sensitive payload detected in {table.name}.{column_name}")
        if TRANSCRIPT_PATTERN.search(value):
            raise SensitivePayloadError(f"raw transcript detected in {table.name}.{column_name}")
