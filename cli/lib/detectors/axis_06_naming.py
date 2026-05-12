from __future__ import annotations

import difflib
import os
import re
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


def _symbol_name(entry: dict[str, Any]) -> str:
    return _entry_value(entry, "symbol", "symbol_id", "id")


def _symbol_core(symbol: str) -> str:
    return re.split(r"[./]", symbol)[-1]


def _is_snake_case(symbol: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)+", symbol))


def _is_camel_case(symbol: str) -> bool:
    return bool(re.fullmatch(r"[a-z]+(?:[A-Z][a-z0-9]+)+[a-z0-9]*", symbol)) or bool(
        re.fullmatch(r"[a-z]+[A-Z][a-zA-Z0-9]*", symbol)
    )


def _similarity(left: str, right: str) -> float:
    return difflib.SequenceMatcher(None, left, right).ratio()


def _load_deprecated_skill_hits(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    patterns = ("architecture", "orchestrator", "codex", "vscode-plugins")
    skills_root = root / "skills"
    if not skills_root.exists():
        return findings

    for pattern in patterns:
        regex = re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(pattern)}(?![A-Za-z0-9_-])")
        paths: list[str] = []
        for path in sorted(skills_root.rglob("*.md")):
            if path.name == "SKILL_MAP.md":
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            body = text
            if body.startswith("---"):
                parts = body.split("---", 2)
                if len(parts) >= 3:
                    body = parts[2]
            if not regex.search(body):
                continue
            rel_path = str(path.relative_to(root))
            if rel_path not in paths:
                paths.append(rel_path)
        if paths:
            findings.append(
                {
                    "kind": "deprecated_skill",
                    "symbols": [pattern],
                    "paths": paths,
                }
            )
    return findings


class Axis06NamingConfusion(BaseDetector):
    id = "axis-06"
    name = "naming confusion"
    phase_gate = "G2"
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

        findings: list[dict[str, Any]] = []

        symbols = [entry for entry in rows if _symbol_name(entry)]
        similar_pairs: set[tuple[str, str]] = set()
        for index, left in enumerate(symbols):
            left_name = _symbol_name(left)
            if not left_name:
                continue
            left_core = _symbol_core(left_name)
            for right in symbols[index + 1 :]:
                right_name = _symbol_name(right)
                if not right_name or left_name == right_name:
                    continue
                right_core = _symbol_core(right_name)
                left_norm = left_core.lower()
                right_norm = right_core.lower()
                if left_norm == right_norm:
                    continue
                ratio = _similarity(left_norm, right_norm)
                if ratio < 0.88 or abs(len(left_norm) - len(right_norm)) > 2:
                    continue
                pair_key = tuple(sorted((left_name, right_name)))
                if pair_key in similar_pairs:
                    continue
                similar_pairs.add(pair_key)
                findings.append(
                    {
                        "kind": "similar_pair",
                        "symbols": [left_name, right_name],
                        "paths": sorted(
                            {
                                str(left.get("path") or ""),
                                str(right.get("path") or ""),
                            }
                        ),
                    }
                )

        symbols_by_path: dict[str, list[str]] = defaultdict(list)
        for entry in symbols:
            path = str(entry.get("path") or "").strip()
            name = _symbol_name(entry)
            if not path or not name:
                continue
            symbols_by_path[path].append(_symbol_core(name))

        for path, path_symbols in sorted(symbols_by_path.items()):
            snake_symbols = [symbol for symbol in path_symbols if _is_snake_case(symbol)]
            camel_symbols = [symbol for symbol in path_symbols if _is_camel_case(symbol)]
            if not snake_symbols or not camel_symbols:
                continue
            findings.append(
                {
                    "kind": "case_mix",
                    "symbols": sorted(set(snake_symbols + camel_symbols)),
                    "paths": [path],
                }
            )

        findings.extend(_load_deprecated_skill_hits(root))

        verdict: str = "passed" if not findings else "failed"
        cost_ms = max(1, int((time.perf_counter() - started) * 1000))
        return DetectorResult(
            verdict=verdict,
            findings=findings,
            cost_ms=cost_ms,
            raw={
                "project_root": str(root),
                "entries_scanned": len(rows),
                "findings_count": len(findings),
            },
        )
