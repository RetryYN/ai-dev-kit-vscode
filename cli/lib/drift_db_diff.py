#!/usr/bin/env python3
"""Diff D-DB markdown schema against SQLite DB."""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

CONSTRAINT_PREFIXES = {"constraint", "primary", "unique", "foreign", "check"}
INLINE_CONSTRAINTS = {
    "primary",
    "not",
    "default",
    "unique",
    "check",
    "references",
    "collate",
    "generated",
    "autoincrement",
}


def _normalize_ident(name: str) -> str:
    return name.strip().strip('"').strip("`").lower()


def _normalize_type(type_expr: str) -> str:
    norm = " ".join(type_expr.strip().split())
    return norm.upper()


def _split_definitions(body: str) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")" and depth > 0:
            depth -= 1

        if ch == "," and depth == 0:
            piece = "".join(current).strip()
            if piece:
                chunks.append(piece)
            current = []
            continue

        current.append(ch)

    tail = "".join(current).strip()
    if tail:
        chunks.append(tail)
    return chunks


def _extract_table_blocks(doc: str) -> list[tuple[str, str]]:
    pattern = re.compile(
        r"create\s+table\s+(?:if\s+not\s+exists\s+)?([\"`]?\w+[\"`]?)\s*\((.*?)\)\s*;",
        re.IGNORECASE | re.DOTALL,
    )
    return [(_normalize_ident(m.group(1)), m.group(2)) for m in pattern.finditer(doc)]


def _parse_design_columns(doc: str) -> dict[str, dict[str, str]]:
    design: dict[str, dict[str, str]] = {}
    for table, body in _extract_table_blocks(doc):
        cols: dict[str, str] = {}
        for raw_item in _split_definitions(body):
            item = raw_item.strip()
            if not item:
                continue
            tokens = item.split()
            if not tokens:
                continue
            head = tokens[0].strip('"`').lower()
            if head in CONSTRAINT_PREFIXES:
                continue

            column = _normalize_ident(tokens[0])
            type_parts: list[str] = []
            for token in tokens[1:]:
                low = token.lower().strip(',')
                if low in INLINE_CONSTRAINTS:
                    break
                type_parts.append(token)
            cols[column] = _normalize_type(" ".join(type_parts))

        design[table] = cols
    return design


def _parse_design_indexes(doc: str) -> dict[str, set[str]]:
    pattern = re.compile(
        r"create\s+(?:unique\s+)?index\s+(?:if\s+not\s+exists\s+)?([\"`]?\w+[\"`]?)\s+on\s+([\"`]?\w+[\"`]?)",
        re.IGNORECASE,
    )
    by_table: dict[str, set[str]] = defaultdict(set)
    for match in pattern.finditer(doc):
        index_name = _normalize_ident(match.group(1))
        table_name = _normalize_ident(match.group(2))
        by_table[table_name].add(index_name)
    return dict(by_table)


def _load_actual_schema(db_path: Path) -> tuple[set[str], dict[str, dict[str, str]], dict[str, set[str]]]:
    conn = sqlite3.connect(str(db_path))
    try:
        table_rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        tables = {_normalize_ident(row[0]) for row in table_rows}

        columns: dict[str, dict[str, str]] = {}
        indexes: dict[str, set[str]] = {}
        for table in tables:
            col_rows = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
            columns[table] = {
                _normalize_ident(row[1]): _normalize_type(row[2] or "") for row in col_rows
            }

            idx_rows = conn.execute(f"PRAGMA index_list('{table}')").fetchall()
            indexes[table] = {_normalize_ident(row[1]) for row in idx_rows}

        return tables, columns, indexes
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="D-DB drift diff")
    parser.add_argument("--doc", required=True, help="Path to D-DB markdown file")
    parser.add_argument("--db", required=True, help="Path to SQLite db")
    args = parser.parse_args()

    doc_path = Path(args.doc)
    db_path = Path(args.db)

    if not doc_path.exists():
        print(f"ERROR|missing-doc|設計書が存在しません: {doc_path}")
        return 2
    if not db_path.exists():
        print(f"ERROR|missing-db|SQLite DB が存在しません: {db_path}")
        return 2

    doc_text = doc_path.read_text(encoding="utf-8")
    design_columns = _parse_design_columns(doc_text)
    design_indexes = _parse_design_indexes(doc_text)

    try:
        actual_tables, actual_columns, actual_indexes = _load_actual_schema(db_path)
    except sqlite3.Error as exc:
        print(f"ERROR|sqlite|SQLite 参照に失敗: {exc}")
        return 3

    warnings: list[tuple[str, str]] = []
    design_tables = set(design_columns.keys())

    for table in sorted(design_tables - actual_tables):
        warnings.append(("missing-table", f"設計書のテーブル '{table}' が実 DB に存在しません"))

    for table in sorted(actual_tables - design_tables):
        warnings.append(("orphan", f"実 DB のテーブル '{table}' が設計書に記載されていません"))

    for table in sorted(design_tables & actual_tables):
        expected_cols = design_columns.get(table, {})
        observed_cols = actual_columns.get(table, {})

        for col in sorted(expected_cols.keys() - observed_cols.keys()):
            warnings.append(("schema-drift", f"table={table}: 設計書のカラム '{col}' が実 DB にありません"))
        for col in sorted(observed_cols.keys() - expected_cols.keys()):
            warnings.append(("schema-drift", f"table={table}: 実 DB のカラム '{col}' が設計書にありません"))
        for col in sorted(expected_cols.keys() & observed_cols.keys()):
            expected_type = expected_cols[col]
            observed_type = observed_cols[col]
            if expected_type and observed_type and expected_type != observed_type:
                warnings.append(
                    (
                        "schema-drift",
                        f"table={table}: カラム '{col}' の型差分 (design={expected_type}, db={observed_type})",
                    )
                )

        expected_idx = design_indexes.get(table, set())
        observed_idx = actual_indexes.get(table, set())
        for idx in sorted(expected_idx - observed_idx):
            warnings.append(("index-drift", f"table={table}: 設計書のインデックス '{idx}' が実 DB にありません"))
        for idx in sorted(observed_idx - expected_idx):
            warnings.append(("index-drift", f"table={table}: 実 DB のインデックス '{idx}' が設計書にありません"))

    result = "warn" if warnings else "ok"
    print(f"RESULT|{result}")
    for kind, message in warnings:
        print(f"WARN|{kind}|{message}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
