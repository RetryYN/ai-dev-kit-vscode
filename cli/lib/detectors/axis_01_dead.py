from __future__ import annotations

import os
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Any

import helix_db

from .base import BaseDetector, DetectorResult


SEARCH_ROOTS = ("cli", "skills", "docs")


def _project_root(db_path: str | Path) -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root)
    target = Path(db_path).resolve()
    if target.parent.name == ".helix":
        return target.parent.parent
    return Path.cwd()


def _table_name(conn: sqlite3.Connection) -> str | None:
    for table_name in ("code_entries", "code_index"):
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


def _entry_symbol(entry: dict[str, Any]) -> str:
    return str(entry.get("symbol") or entry.get("symbol_id") or entry.get("id") or "").strip()


def _entry_symbol_id(entry: dict[str, Any]) -> str:
    return str(entry.get("symbol_id") or entry.get("id") or entry.get("symbol") or "").strip()


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
    symbol = _entry_symbol(entry)
    symbol_id = _entry_symbol_id(entry)
    path = str(entry.get("path") or "")
    if symbol in {"main", "__main__"} or symbol_id in {"main", "__main__"}:
        return True
    if Path(path).name.startswith("helix-"):
        return True
    if Path(path).name == "__main__.py":
        return True
    return False


def _reference_terms(entry: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for term in (_entry_symbol_id(entry), _entry_symbol(entry)):
        if term and term not in terms:
            terms.append(term)
    return terms


def _run_rg(root: Path, term: str) -> subprocess.CompletedProcess[str]:
    targets: list[str] = []
    for sub in ("cli", "skills", "docs"):
        target = root / sub
        if target.exists():
            targets.append(str(target))
    if not targets:
        return subprocess.CompletedProcess([], 0, "", "")
    command = ["grep", "-rnF", term, *targets]
    return subprocess.run(command, check=False, capture_output=True, text=True)


def _has_reference(root: Path, entry: dict[str, Any]) -> bool:
    source_path = str(entry.get("path") or "")
    source_line = _entry_line(entry)
    for term in _reference_terms(entry):
        completed = _run_rg(root, term)
        if completed.returncode not in {0, 1}:
            continue
        for line in completed.stdout.splitlines():
            parts = line.split(":", 2)
            if len(parts) < 3:
                continue
            rel_path, line_no_text, _ = parts
            try:
                line_no = int(line_no_text)
            except ValueError:
                continue
            if rel_path == source_path and line_no == source_line:
                continue
            return True
    return False


class Axis01DeadCodeDrift(BaseDetector):
    id = "axis-01"
    name = "dead code drift"
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
                    "entries_scanned": 0,
                    "findings_count": 0,
                    "project_root": str(root),
                    "reason": "no code_index/code_entries rows available",
                },
            )
        findings: list[dict[str, Any]] = []
        for entry in rows:
            if _is_entrypoint(entry):
                continue
            if _has_reference(root, entry):
                continue
            findings.append(
                {
                    "symbol_id": _entry_symbol_id(entry),
                    "path": str(entry.get("path") or ""),
                    "line": _entry_line(entry),
                    "reason": "no references found in cli/, skills/, docs/ and symbol is not an entrypoint",
                }
            )

        verdict: str = "passed" if not findings else "failed"
        cost_ms = max(1, int((time.perf_counter() - started) * 1000))
        return DetectorResult(
            verdict=verdict,
            findings=findings,
            cost_ms=cost_ms,
            raw={
                "entries_scanned": len(rows),
                "findings_count": len(findings),
                "project_root": str(root),
            },
        )
