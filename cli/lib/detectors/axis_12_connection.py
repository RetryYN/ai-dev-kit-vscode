from __future__ import annotations

import json
import os
import re
import shlex
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Any

import helix_db

from .base import BaseDetector, DetectorResult

try:
    from ..yaml_parser import parse_yaml  # type: ignore
except Exception:  # pragma: no cover - fallback for direct script execution
    from yaml_parser import parse_yaml  # type: ignore


STDLIB_ALLOWLIST = {
    "argparse",
    "contextlib",
    "datetime",
    "functools",
    "hashlib",
    "io",
    "json",
    "keyword",
    "os",
    "pathlib",
    "re",
    "shlex",
    "sqlite3",
    "subprocess",
    "sys",
    "tempfile",
    "time",
    "tokenize",
    "typing",
    "urllib",
}

ROLE_OPTION_RE = re.compile(r"--[a-z][a-z0-9-]*")
LOCAL_IMPORT_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")


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


def _load_code_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
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
    rows = conn.execute(query, params).fetchall()
    return [{key: row[key] for key in row.keys()} for row in rows]


def _load_code_edges(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
        ("code_edges",),
    ).fetchone()
    if row is None:
        return []
    rows = conn.execute("SELECT * FROM code_edges ORDER BY id").fetchall()
    return [{key: row[key] for key in row.keys()} for row in rows]


def _local_name_variants(entry: dict[str, Any]) -> set[str]:
    variants: set[str] = set()
    path = str(entry.get("path") or "")
    if path:
        rel = Path(path)
        variants.add(rel.stem)
        variants.add(path.replace("/", ".").removesuffix(".py"))
        variants.add(path)
    for key in ("id", "symbol_id", "symbol"):
        value = entry.get(key)
        if value is not None:
            text = str(value).strip()
            if text:
                variants.add(text)
    return {variant for variant in variants if variant}


def _should_check_import(target: str) -> bool:
    lowered = target.lower().strip()
    if not lowered:
        return False
    head = lowered.split(".")[0]
    if head in STDLIB_ALLOWLIST or lowered in STDLIB_ALLOWLIST:
        return False
    if lowered.startswith(("cli.", "helix.", "skills.", "docs.")):
        return True
    if LOCAL_IMPORT_RE.fullmatch(lowered):
        return True
    return lowered.count(".") >= 1 and not lowered.split(".")[0] in STDLIB_ALLOWLIST


def _normalize_command(command: str, root: Path) -> str:
    env = os.environ.copy()
    env.setdefault("HELIX_ROOT", str(root))
    expanded = os.path.expandvars(os.path.expanduser(command))
    return expanded.replace("$HELIX_ROOT", str(root))


def _read_settings(root: Path) -> dict[str, Any] | None:
    path = root / ".claude" / "settings.json"
    if not path.is_file():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return loaded if isinstance(loaded, dict) else None


def _collect_hook_commands(settings: dict[str, Any]) -> list[str]:
    commands: list[str] = []
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return commands
    for entries in hooks.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            nested_hooks = entry.get("hooks")
            if not isinstance(nested_hooks, list):
                continue
            for hook in nested_hooks:
                if not isinstance(hook, dict):
                    continue
                command = hook.get("command")
                if isinstance(command, str) and command.strip():
                    commands.append(command.strip())
    return commands


def _collect_role_map_options(role_map_text: str) -> set[str]:
    return {match.group(0) for match in ROLE_OPTION_RE.finditer(role_map_text)}


def _run_help(script: Path, root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(script), "--help"],
        check=False,
        capture_output=True,
        text=True,
        cwd=root,
    )


def _skill_triggers(skill_text: str) -> list[str]:
    frontmatter_end = skill_text.find("\n---\n", 4)
    if not skill_text.startswith("---\n") or frontmatter_end == -1:
        return []
    frontmatter = skill_text[4:frontmatter_end]
    try:
        parsed = parse_yaml(frontmatter)
    except Exception:
        return []
    if not isinstance(parsed, dict):
        return []
    metadata = parsed.get("metadata")
    if not isinstance(metadata, dict):
        return []
    triggers = metadata.get("triggers")
    if not isinstance(triggers, list):
        return []
    return [str(item).strip() for item in triggers if str(item).strip()]


class Axis12ConnectionDeficiency(BaseDetector):
    id = "axis-12"
    name = "connection deficiency"
    phase_gate = "G2"
    kind = "detector"

    def run(self, db_path: str | Path) -> DetectorResult:
        started = time.perf_counter()
        target_db = Path(db_path)
        helix_db._prepare_db_path(str(target_db))
        conn = helix_db.get_connection(target_db)
        root = _project_root(db_path)
        findings: list[dict[str, Any]] = []

        try:
            code_rows = _load_code_rows(conn)
            edge_rows = _load_code_edges(conn)
            if not code_rows or not edge_rows:
                cost_ms = max(1, int((time.perf_counter() - started) * 1000))
                return DetectorResult(
                    verdict="blocked",
                    findings=[],
                    cost_ms=cost_ms,
                    raw={"reason": "code_edges/code_index rows are missing", "project_root": str(root)},
                )

            code_names: set[str] = set()
            for entry in code_rows:
                code_names.update(_local_name_variants(entry))

            for edge in edge_rows:
                if str(edge.get("edge_type") or "").strip() != "import":
                    continue
                target = str(edge.get("to_external_ref") or "").strip()
                if not target:
                    continue
                if not _should_check_import(target):
                    continue
                if target in code_names:
                    continue
                if any(target == variant or target.endswith(f".{variant}") for variant in code_names):
                    continue
                findings.append(
                    {
                        "kind": "import_broken",
                        "path": str(edge.get("to_external_ref") or ""),
                        "detail": f"import target '{target}' not found in code_index/code_entries",
                    }
                )
                break

            settings = _read_settings(root)
            if settings is not None:
                commands = _collect_hook_commands(settings)
                for command in commands:
                    normalized = _normalize_command(command, root)
                    script = shlex.split(normalized)[0] if normalized else ""
                    script_path = Path(script)
                    if script_path.exists():
                        continue
                    findings.append(
                        {
                            "kind": "hook_orphan",
                            "path": str(script_path),
                            "detail": f"hook command '{command}' points to missing script",
                        }
                    )
                    break

            role_map_path = root / "cli" / "ROLE_MAP.md"
            role_map_text = role_map_path.read_text(encoding="utf-8") if role_map_path.is_file() else ""
            expected_options = _collect_role_map_options(role_map_text)
            cli_root = root / "cli"
            help_texts: list[str] = []
            for script in sorted(cli_root.glob("helix-*")):
                if not script.is_file():
                    continue
                completed = _run_help(script, root)
                if completed.returncode != 0 and not completed.stdout and not completed.stderr:
                    continue
                help_texts.append(f"{completed.stdout}\n{completed.stderr}")
            if expected_options and help_texts:
                observed_options = {match.group(0) for text in help_texts for match in ROLE_OPTION_RE.finditer(text)}
                missing_options = sorted(option for option in expected_options if option not in observed_options)
                if missing_options:
                    findings.append(
                        {
                            "kind": "cli_option_drift",
                            "path": "cli/ROLE_MAP.md",
                            "detail": f"missing options: {', '.join(missing_options)}",
                        }
                    )

            skills_root = root / "skills"
            skill_map_path = skills_root / "SKILL_MAP.md"
            skill_map_text = skill_map_path.read_text(encoding="utf-8") if skill_map_path.is_file() else ""
            if skills_root.exists() and skill_map_text:
                for skill_md in sorted(skills_root.rglob("SKILL.md")):
                    text = skill_md.read_text(encoding="utf-8")
                    triggers = _skill_triggers(text)
                    if not triggers:
                        continue
                    skill_id = skill_md.parent.name
                    if skill_id in skill_map_text or skill_md.stem in skill_map_text:
                        continue
                    findings.append(
                        {
                            "kind": "trigger_orphan",
                            "path": str(skill_md.relative_to(root)),
                            "detail": f"triggers {', '.join(triggers)} are not represented in SKILL_MAP/catalog",
                        }
                    )
                    break
        finally:
            conn.close()

        verdict = "passed" if not findings else "failed"
        cost_ms = max(1, int((time.perf_counter() - started) * 1000))
        return DetectorResult(
            verdict=verdict,
            findings=findings,
            cost_ms=cost_ms,
            raw={"project_root": str(root)},
        )
