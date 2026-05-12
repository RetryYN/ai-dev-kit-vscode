from __future__ import annotations

import ast
import io
import keyword
import os
import sqlite3
import time
import tokenize
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


def _load_candidate_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    table_name = _table_name(conn)
    if table_name is None:
        return []

    columns = _table_columns(conn, table_name)
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
    if "path" not in select_columns:
        return []

    query = f"SELECT {', '.join(select_columns)} FROM {table_name}"
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
    return [{key: row[key] for key in row.keys()} for row in rows]


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


def _is_entrypoint(entry: dict[str, Any]) -> bool:
    symbol = _entry_value(entry, "symbol", "symbol_id", "id")
    path = Path(str(entry.get("path") or ""))
    if symbol in {"main", "__main__", "__init__"}:
        return True
    if path.name.startswith("helix-"):
        return True
    if path.name == "__main__.py":
        return True
    return False


def _read_python_source(root: Path, rel_path: str) -> str | None:
    path = root / rel_path
    if path.suffix != ".py" or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _function_node_at_line(tree: ast.AST, line_no: int) -> ast.AST | None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and getattr(node, "lineno", 0) == line_no:
            return node
    return None


def _body_source(text: str, node: ast.AST) -> str:
    body = getattr(node, "body", [])
    segments: list[str] = []
    for stmt in body:
        segment = ast.get_source_segment(text, stmt)
        if segment:
            segments.append(segment)
    return "\n".join(segments).strip()


def _normalize_token(token: tokenize.TokenInfo) -> str | None:
    if token.type in {
        tokenize.ENCODING,
        tokenize.ENDMARKER,
        tokenize.NEWLINE,
        tokenize.NL,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.COMMENT,
    }:
        return None
    if token.type == tokenize.NAME:
        return token.string if keyword.iskeyword(token.string) else "NAME"
    if token.type == tokenize.STRING:
        return "STRING"
    if token.type == tokenize.NUMBER:
        return "NUMBER"
    return token.string


def _tokenize_body(body: str) -> list[str]:
    if not body:
        return []
    tokens: list[str] = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(body).readline):
            normalized = _normalize_token(token)
            if normalized is not None:
                tokens.append(normalized)
    except tokenize.TokenError:
        return []
    return tokens


def _similarity(tokens_a: list[str], tokens_b: list[str]) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


class Axis03RealDuplicate(BaseDetector):
    id = "axis-03"
    name = "real duplicate"
    phase_gate = "G4"
    kind = "detector"

    def run(self, db_path: str | Path) -> DetectorResult:
        started = time.perf_counter()
        target_db = Path(db_path)
        helix_db._prepare_db_path(str(target_db))
        conn = helix_db.get_connection(target_db)
        try:
            rows = _load_candidate_rows(conn)
        finally:
            conn.close()

        root = _project_root(db_path)
        if not rows:
            cost_ms = max(1, int((time.perf_counter() - started) * 1000))
            return DetectorResult(
                verdict="blocked",
                findings=[],
                cost_ms=cost_ms,
                raw={
                    "reason": "no code_index/code_entries rows available",
                    "project_root": str(root),
                },
            )

        candidates: list[dict[str, Any]] = []
        files_scanned = 0
        skipped_missing = 0
        skipped_parse = 0
        for entry in rows:
            if _is_entrypoint(entry):
                continue
            rel_path = str(entry.get("path") or "")
            text = _read_python_source(root, rel_path)
            if text is None:
                skipped_missing += 1
                continue
            files_scanned += 1
            line_no = _entry_line(entry)
            if line_no <= 0:
                continue
            try:
                tree = ast.parse(text)
            except SyntaxError:
                skipped_parse += 1
                continue
            node = _function_node_at_line(tree, line_no)
            if node is None:
                continue
            body = _body_source(text, node)
            tokens = _tokenize_body(body)
            if not tokens:
                continue
            candidates.append(
                {
                    "symbol": _entry_value(entry, "symbol", "symbol_id", "id") or f"{rel_path}:{line_no}",
                    "path": rel_path,
                    "line": line_no,
                    "tokens": tokens,
                }
            )

        if not candidates:
            cost_ms = max(1, int((time.perf_counter() - started) * 1000))
            return DetectorResult(
                verdict="blocked",
                findings=[],
                cost_ms=cost_ms,
                raw={
                    "reason": "no parseable python functions available for duplicate analysis",
                    "project_root": str(root),
                    "rows_scanned": len(rows),
                    "files_scanned": files_scanned,
                    "skipped_missing": skipped_missing,
                    "skipped_parse": skipped_parse,
                },
            )

        findings: list[dict[str, Any]] = []
        for index, left in enumerate(candidates):
            for right in candidates[index + 1 :]:
                similarity = _similarity(left["tokens"], right["tokens"])
                if similarity < 0.85:
                    continue
                findings.append(
                    {
                        "symbol_a": left["symbol"],
                        "symbol_b": right["symbol"],
                        "similarity": round(similarity, 3),
                        "kind": "real_duplicate",
                    }
                )

        findings.sort(key=lambda item: (item["symbol_a"], item["symbol_b"]))
        verdict: str = "passed" if not findings else "failed"
        cost_ms = max(1, int((time.perf_counter() - started) * 1000))
        return DetectorResult(
            verdict=verdict,
            findings=findings,
            cost_ms=cost_ms,
            raw={
                "rows_scanned": len(rows),
                "candidates": len(candidates),
                "findings_count": len(findings),
                "project_root": str(root),
                "skipped_missing": skipped_missing,
                "skipped_parse": skipped_parse,
            },
        )
