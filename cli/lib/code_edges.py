#!/usr/bin/env python3
import argparse
import ast
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

import helix_db


EXIT_USAGE = 64
EDGE_INSERT_SQL = """
INSERT INTO code_edges (
    from_entry_id,
    to_entry_id,
    to_external_ref,
    edge_type,
    weight,
    source_line,
    raw_meta
)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""
_SQL_PATTERNS = (
    ("sql_create", re.compile(r"\bCREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)),
    ("sql_insert", re.compile(r"\bINSERT\s+INTO\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)),
    ("sql_from", re.compile(r"\bFROM\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)),
)
_YAML_MATCHERS = (
    ("yaml_anchor", re.compile(r"&([A-Za-z_][A-Za-z0-9_-]*)"), "finditer"),
    ("yaml_ref", re.compile(r"\*([A-Za-z_][A-Za-z0-9_-]*)"), "finditer"),
    ("yaml_ref", re.compile(r"^\s*\$?ref\s*:\s*(.+?)\s*$"), "match"),
    ("yaml_role", re.compile(r"^\s*role\s*:\s*(.+?)\s*$"), "match"),
)


class HelixArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"{self.prog}: error: {message}\n")


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_db_path() -> Path:
    return Path(helix_db.resolve_default_db_path())


def _parser(prog: str) -> HelixArgumentParser:
    return HelixArgumentParser(prog=prog, add_help=True)


def _stable_entry_id(seed: str) -> int:
    return int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:15], 16)


def _raw_meta(path: Path, **extra) -> str:
    return json.dumps({"source_path": path.as_posix(), **extra}, ensure_ascii=False, sort_keys=True)


def _edge(
    path: Path,
    from_entry_id: int,
    to_external_ref: str,
    edge_type: str,
    source_line: int | None,
    **meta,
) -> dict:
    return {
        "from_entry_id": from_entry_id,
        "to_entry_id": None,
        "to_external_ref": to_external_ref,
        "edge_type": edge_type,
        "weight": 1,
        "source_line": source_line,
        "raw_meta": _raw_meta(path, **meta),
    }


def _edge_rows(edges) -> list[tuple]:
    return [
        (
            int(edge["from_entry_id"]),
            edge.get("to_entry_id"),
            edge.get("to_external_ref"),
            edge["edge_type"],
            int(edge.get("weight", 1)),
            edge.get("source_line"),
            edge.get("raw_meta"),
        )
        for edge in edges
    ]


def _name_from_expr(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _name_from_expr(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Call):
        return _name_from_expr(node.func)
    return ""


def _iter_sql_texts(tree: ast.AST) -> list[tuple[int, str]]:
    sql_texts: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "execute":
            continue
        if not node.args:
            continue
        first_arg = node.args[0]
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            sql_texts.append((getattr(first_arg, "lineno", getattr(node, "lineno", 0)), first_arg.value))
    return sql_texts


def _sql_edges_for_text(path: Path, line_no: int, sql_text: str) -> list[dict]:
    from_entry_id = _stable_entry_id(f"{path.as_posix()}#sql")
    edges: list[dict] = []
    for edge_type, pattern in _SQL_PATTERNS:
        for match in pattern.finditer(sql_text):
            edges.append(
                _edge(
                    path,
                    from_entry_id,
                    match.group(1),
                    edge_type,
                    line_no or None,
                    extractor="sql",
                    sql=sql_text.strip(),
                )
            )
    return edges


def extract_python_edges(file_path) -> list[dict]:
    path = Path(file_path)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    module_id = _stable_entry_id(path.as_posix())
    edges: list[dict] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                edges.append(_edge(path, module_id, alias.name, "import", getattr(node, "lineno", None), extractor="python"))
            continue
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                ref = module if alias.name == "*" else ".".join(part for part in (module, alias.name) if part)
                edges.append(_edge(path, module_id, ref or alias.name, "import", getattr(node, "lineno", None), extractor="python"))
            continue
        if isinstance(node, ast.Call):
            call_name = _name_from_expr(node.func)
            if call_name:
                edges.append(_edge(path, module_id, call_name, "call", getattr(node, "lineno", None), extractor="python"))
            continue
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                base_name = _name_from_expr(base)
                if base_name:
                    edges.append(
                        _edge(
                            path,
                            module_id,
                            base_name,
                            "inherit",
                            getattr(node, "lineno", None),
                            extractor="python",
                            class_name=node.name,
                        )
                    )
    return edges


def extract_sql_edges(file_path) -> list[dict]:
    path = Path(file_path)
    text = path.read_text(encoding="utf-8")
    if path.suffix != ".py":
        return _sql_edges_for_text(path, 1, text)
    tree = ast.parse(text)
    edges: list[dict] = []
    for line_no, sql_text in _iter_sql_texts(tree):
        edges.extend(_sql_edges_for_text(path, line_no, sql_text))
    return edges


def extract_yaml_refs(file_path) -> list[dict]:
    path = Path(file_path)
    from_entry_id = _stable_entry_id(f"{path.as_posix()}#yaml")
    edges: list[dict] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for edge_type, pattern, mode in _YAML_MATCHERS:
            if mode == "finditer":
                for match in pattern.finditer(line):
                    edges.append(_edge(path, from_entry_id, match.group(1).strip(), edge_type, line_no, extractor="yaml"))
                continue
            match = pattern.match(line)
            if match:
                edges.append(_edge(path, from_entry_id, match.group(1).strip(), edge_type, line_no, extractor="yaml"))
    return edges


def _connect_write(db_path: Path) -> sqlite3.Connection:
    helix_db._prepare_db_path(db_path)
    conn = helix_db.get_connection(db_path)
    helix_db._ensure_schema(conn)
    return conn


def _insert_edges(conn: sqlite3.Connection, edges) -> int:
    rows = _edge_rows(edges)
    conn.executemany(EDGE_INSERT_SQL, rows)
    return len(rows)


def bulk_insert(db_path, edges) -> int:
    conn = _connect_write(Path(db_path))
    try:
        inserted = _insert_edges(conn, edges)
        conn.commit()
        return inserted
    finally:
        conn.close()


def rebuild_edges(db_path, repo_root) -> int:
    root = Path(repo_root).resolve()
    edges: list[dict] = []
    for path in sorted((root / "cli" / "lib").glob("*.py")):
        edges.extend(extract_python_edges(path))
        edges.extend(extract_sql_edges(path))

    conn = _connect_write(Path(db_path))
    try:
        conn.execute("DELETE FROM code_edges")
        inserted = _insert_edges(conn, edges)
        conn.commit()
        return inserted
    finally:
        conn.close()


def _cmd_rebuild(argv: list[str]) -> int:
    parser = _parser("code_edges.py rebuild")
    parser.add_argument("--repo-root", default=str(_default_repo_root()))
    parser.add_argument("--db-path", default=str(_default_db_path()))
    args = parser.parse_args(argv)
    print(rebuild_edges(args.db_path, args.repo_root))
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: code_edges.py <rebuild>", file=sys.stderr)
        return EXIT_USAGE
    if sys.argv[1] == "rebuild":
        return _cmd_rebuild(sys.argv[2:])
    print(f"Unknown command: {sys.argv[1]}", file=sys.stderr)
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
