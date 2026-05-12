from __future__ import annotations

import ast
import json
import os
import sqlite3
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import helix_db

from .base import BaseDetector, DetectorResult


def _project_root(db_path: str | Path) -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root)
    target = Path(db_path).resolve()
    if target.parent.name == ".helix":
        return target.parent.parent
    return Path.cwd()


def _table_name(conn: sqlite3.Connection) -> str | None:
    for table_name in ("code_index", "code_entries"):
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
            (table_name,),
        ).fetchone()
        if row is not None:
            return table_name
    return None


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row[1]) for row in rows}


def _routing_table_exists(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
        ("routing_decisions",),
    ).fetchone()
    return row is not None


def _load_rows(conn: sqlite3.Connection) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    code_table = _table_name(conn)
    code_rows: list[dict[str, Any]] = []
    if code_table is not None:
        columns = _table_columns(conn, code_table)
        select_columns = [
            column
            for column in (
                "id",
                "symbol_id",
                "symbol",
                "path",
                "line_no",
                "symbol_line",
                "bucket",
                "kind",
            )
            if column in columns
        ]
        if "path" in select_columns:
            query = f"SELECT {', '.join(select_columns)} FROM {code_table}"
            params: tuple[Any, ...] = ()
            if "bucket" in columns:
                query += " WHERE bucket = ?"
                params = ("coverage_eligible",)
            line_terms = [column for column in ("symbol_line", "line_no") if column in columns]
            line_expr = f"COALESCE({', '.join(line_terms)}, 0)" if line_terms else "0"
            id_terms = [column for column in ("symbol_id", "id", "symbol") if column in columns]
            id_expr = f"COALESCE({', '.join(id_terms)}, '')" if id_terms else "''"
            query += f" ORDER BY path, {line_expr}, {id_expr}"
            rows = conn.execute(query, params).fetchall()
            code_rows = [{key: row[key] for key in row.keys()} for row in rows]

    routing_rows: list[dict[str, Any]] = []
    if _routing_table_exists(conn):
        rows = conn.execute("SELECT * FROM routing_decisions ORDER BY rowid").fetchall()
        routing_rows = [{key: row[key] for key in row.keys()} for row in rows]

    return code_rows, routing_rows


def _entry_value(entry: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = entry.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _entry_line(entry: dict[str, Any]) -> int:
    for key in ("symbol_line", "line_no"):
        try:
            value = int(entry.get(key) or 0)
        except (TypeError, ValueError):
            continue
        if value > 0:
            return value
    return 0


def _read_python_source(root: Path, rel_path: str) -> str | None:
    path = root / rel_path
    if path.suffix != ".py" or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _function_arg_count(node: ast.AST) -> int:
    args = getattr(node, "args", None)
    if args is None:
        return 0
    total = (
        len(getattr(args, "posonlyargs", []))
        + len(getattr(args, "args", []))
        + len(getattr(args, "kwonlyargs", []))
    )
    if getattr(args, "vararg", None) is not None:
        total += 1
    if getattr(args, "kwarg", None) is not None:
        total += 1
    positional = list(getattr(args, "posonlyargs", [])) + list(getattr(args, "args", []))
    if positional and positional[0].arg in {"self", "cls"}:
        total -= 1
    return max(0, total)


def _routing_text(row: dict[str, Any]) -> str:
    values: list[str] = []
    for value in row.values():
        if value is None:
            continue
        if isinstance(value, (dict, list)):
            values.append(json.dumps(value, ensure_ascii=False, sort_keys=True))
            continue
        values.append(str(value))
    return " ".join(values).lower()


def _routing_path(row: dict[str, Any]) -> str:
    return _entry_value(
        row,
        "path",
        "source_path",
        "file_path",
        "symbol_path",
        "entry_path",
        "target_path",
        "route_path",
    )


def _is_refactor_carry(row: dict[str, Any]) -> bool:
    text = _routing_text(row)
    return "refactor" in text and "carry" in text


def _iter_functions(tree: ast.AST) -> list[ast.AST]:
    functions: list[ast.AST] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node)
    return functions


class Axis09RefactorOpportunity(BaseDetector):
    id = "axis-09"
    name = "refactoring opportunity"
    phase_gate = "G4"
    kind = "detector"

    def run(self, db_path: str | Path) -> DetectorResult:
        started = time.perf_counter()
        target_db = Path(db_path)
        helix_db._prepare_db_path(str(target_db))
        conn = helix_db.get_connection(target_db)
        try:
            code_rows, routing_rows = _load_rows(conn)
        finally:
            conn.close()

        root = _project_root(db_path)
        if not code_rows and not routing_rows:
            cost_ms = max(1, int((time.perf_counter() - started) * 1000))
            return DetectorResult(
                verdict="blocked",
                findings=[],
                cost_ms=cost_ms,
                raw={
                    "reason": "no code_index/code_entries or routing_decisions rows available",
                    "project_root": str(root),
                },
            )

        findings: list[dict[str, Any]] = []

        symbols_by_path: dict[str, int] = defaultdict(int)
        for entry in code_rows:
            path = str(entry.get("path") or "").strip()
            if not path:
                continue
            symbols_by_path[path] += 1

        for path, count in sorted(symbols_by_path.items()):
            if count < 30:
                continue
            findings.append(
                {
                    "kind": "god_file",
                    "path": path,
                    "detail": f"{count} symbols in a single file",
                }
            )

        seen_function_locations: set[tuple[str, int]] = set()
        for entry in code_rows:
            path = str(entry.get("path") or "").strip()
            line_no = _entry_line(entry)
            if not path or line_no <= 0:
                continue
            text = _read_python_source(root, path)
            if text is None:
                continue
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            for node in _iter_functions(tree):
                if getattr(node, "lineno", 0) != line_no:
                    continue
                location = (path, line_no)
                if location in seen_function_locations:
                    continue
                seen_function_locations.add(location)
                arg_count = _function_arg_count(node)
                if arg_count > 6:
                    findings.append(
                        {
                            "kind": "arg_explosion",
                            "path": path,
                            "detail": f"{getattr(node, 'name', 'function')} has {arg_count} args",
                        }
                    )
                break

        current_path = ""
        current_streak = 0
        max_streaks: dict[str, int] = defaultdict(int)
        max_rows: dict[str, dict[str, Any]] = {}
        for row in routing_rows:
            path = _routing_path(row) or "__global__"
            if _is_refactor_carry(row):
                if path == current_path:
                    current_streak += 1
                else:
                    current_path = path
                    current_streak = 1
                if current_streak > max_streaks[path]:
                    max_streaks[path] = current_streak
                    max_rows[path] = row
            else:
                current_path = ""
                current_streak = 0

        for path, streak in sorted(max_streaks.items()):
            if streak < 2:
                continue
            row = max_rows[path]
            findings.append(
                {
                    "kind": "refactor_carry",
                    "path": "" if path == "__global__" else path,
                    "detail": f"{streak} consecutive refactor carry decisions",
                    "last_decision": _routing_text(row),
                }
            )

        findings.sort(key=lambda item: (item["kind"], item["path"], item["detail"]))
        verdict: str = "passed" if not findings else "failed"
        cost_ms = max(1, int((time.perf_counter() - started) * 1000))
        return DetectorResult(
            verdict=verdict,
            findings=findings,
            cost_ms=cost_ms,
            raw={
                "code_rows_scanned": len(code_rows),
                "routing_rows_scanned": len(routing_rows),
                "findings_count": len(findings),
                "project_root": str(root),
            },
        )
