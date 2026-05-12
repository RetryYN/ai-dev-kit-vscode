from __future__ import annotations

import fnmatch
import json
import os
import re
import sqlite3
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import helix_db

from .base import BaseDetector, DetectorResult


ROLE_RE = re.compile(r"\brole\s*[:=]\s*([A-Za-z0-9_-]+)", re.IGNORECASE)
TASK_RE = re.compile(r"\b(?:task_id|wbs_id)\s*[:=]\s*([A-Za-z0-9._-]+)", re.IGNORECASE)
PLAN_RE = re.compile(r"\bplan_id\s*[:=]\s*(PLAN-[0-9]{3})", re.IGNORECASE)
ALLOWED_RE = re.compile(r"\ballowed_files\s*[:=]\s*([^\n;]+)", re.IGNORECASE)

PM_ROLES = {"opus", "pm"}
PMO_PREFIXES = ("pmo",)
CODE_SUFFIXES = {
    ".py",
    ".sh",
    ".bash",
    ".zsh",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".sql",
    ".rb",
    ".go",
    ".rs",
}

IGNORED_GIT_STATUS_PREFIXES = (".helix/",)
IGNORED_GIT_STATUS_SUFFIXES = (".db", ".db-shm", ".db-wal")


def _project_root(db_path: str | Path) -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root)
    target = Path(db_path).resolve()
    if target.parent.name == ".helix":
        return target.parent.parent
    return Path.cwd()


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _parse_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text or text[0] not in "[{":
        return value
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return value


def _row_text(row: dict[str, Any]) -> str:
    values: list[str] = []
    for value in row.values():
        if value is None:
            continue
        parsed = _parse_json(value)
        if isinstance(parsed, (dict, list)):
            values.append(json.dumps(parsed, ensure_ascii=False, sort_keys=True))
            continue
        values.append(str(parsed))
    return " ".join(values)


def _normalize_role(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().lower().replace(" ", "-")


def _extract_match(row: dict[str, Any], regex: re.Pattern[str], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    match = regex.search(_row_text(row))
    return match.group(1).strip() if match else ""


def _split_patterns(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not isinstance(value, str):
        return []
    compact = value.replace("\n", ",")
    parts = [item.strip().strip("'\"") for item in compact.split(",")]
    return [item for item in parts if item]


def _extract_allowed_patterns(row: dict[str, Any]) -> list[str]:
    for key in ("allowed_files", "allowed_paths"):
        patterns = _split_patterns(_parse_json(row.get(key)))
        if patterns:
            return patterns
    match = ALLOWED_RE.search(_row_text(row))
    return _split_patterns(match.group(1)) if match else []


def _normalize_path(value: str) -> str:
    normalized = value.strip().strip("'\"")
    if not normalized:
        return ""
    if "://" in normalized:
        return normalized
    return normalized.replace("\\", "/")


def _collect_path_values(value: Any) -> list[str]:
    parsed = _parse_json(value)
    if isinstance(parsed, list):
        return [_normalize_path(str(item)) for item in parsed if _normalize_path(str(item))]
    if isinstance(parsed, str):
        return [_normalize_path(item) for item in _split_patterns(parsed) if _normalize_path(item)]
    return []


def _extract_paths(row: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for key in (
        "path",
        "file_path",
        "source_path",
        "target_path",
        "changed_files",
        "diff_files",
        "actual_files",
        "write_paths",
        "violations",
    ):
        paths.extend(_collect_path_values(row.get(key)))
    unique: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if not path or path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _load_rows(conn: sqlite3.Connection, table_name: str, order_by: str) -> list[dict[str, Any]]:
    rows = conn.execute(f"SELECT * FROM {table_name} ORDER BY {order_by}").fetchall()
    return [{key: row[key] for key in row.keys()} for row in rows]


def _build_invocation_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str], str]:
    index: dict[tuple[str, str], str] = {}
    fallback = ""
    for row in rows:
        role = _normalize_role(str(row.get("role") or ""))
        if not role:
            continue
        fallback = role
        plan_id = str(row.get("plan_id") or "").strip()
        task_id = str(row.get("task_id") or "").strip()
        if plan_id or task_id:
            index[(plan_id, task_id)] = role
        if plan_id:
            index[(plan_id, "")] = role
        if task_id:
            index[("", task_id)] = role
    if fallback:
        index[("", "")] = fallback
    return index


def _resolve_role(row: dict[str, Any], invocation_index: dict[tuple[str, str], str]) -> str:
    direct = _normalize_role(
        _extract_match(row, ROLE_RE, "role", "owner", "agent_role", "requested_role")
    )
    if direct:
        return direct
    plan_id = _extract_match(row, PLAN_RE, "plan_id")
    task_id = _extract_match(row, TASK_RE, "task_id", "wbs_id")
    return invocation_index.get((plan_id, task_id), invocation_index.get((plan_id, ""), invocation_index.get(("", task_id), invocation_index.get(("", ""), ""))))


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                loaded = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(loaded, dict):
                rows.append(loaded)
    except OSError:
        return []
    return rows


def _git_has_changes(root: Path) -> bool | None:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        check=False,
        capture_output=True,
        text=True,
        cwd=root,
    )
    if result.returncode != 0:
        return None
    changed_paths: list[str] = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        path = _normalize_path(line[3:])
        if path.startswith(IGNORED_GIT_STATUS_PREFIXES):
            continue
        if path.endswith(IGNORED_GIT_STATUS_SUFFIXES):
            continue
        changed_paths.append(path)
    return bool(changed_paths)


def _matches_allowed(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _is_pm_role(role: str) -> bool:
    return role in PM_ROLES


def _is_pmo_role(role: str) -> bool:
    return role == "pmo" or role.startswith(PMO_PREFIXES)


def _is_code_path(path: str) -> bool:
    normalized = _normalize_path(path)
    if not normalized:
        return False
    if normalized.startswith(("cli/", "app/", "src/", "server/", "lib/")):
        return True
    return Path(normalized).suffix in CODE_SUFFIXES


def _collect_handover_findings(root: Path) -> list[dict[str, Any]]:
    current = _load_json(root / ".helix" / "handover" / "CURRENT.json")
    if current is None:
        return []

    task = current.get("task")
    if not isinstance(task, dict):
        return []
    status = str(task.get("status") or "").strip()
    updated_at = _parse_timestamp(current.get("updated_at"))
    findings: list[dict[str, Any]] = []

    if status == "ready_for_review":
        has_changes = _git_has_changes(root)
        if has_changes is False:
            findings.append(
                {
                    "kind": "handover_stale",
                    "detail": "handover status=ready_for_review but git status is clean",
                }
            )
    if status == "in_progress" and updated_at is not None:
        if datetime.now(timezone.utc) - updated_at > timedelta(days=7):
            findings.append(
                {
                    "kind": "handover_stale",
                    "detail": f"handover status=in_progress but updated_at is older than 7 days ({updated_at.isoformat()})",
                }
            )
    return findings


class Axis14OrchestrationIntegrity(BaseDetector):
    id = "axis-14"
    name = "orchestration integrity"
    phase_gate = "G4"
    kind = "detector"

    def run(self, db_path: str | Path) -> DetectorResult:
        started = time.perf_counter()
        target_db = Path(db_path)
        helix_db._prepare_db_path(str(target_db))
        conn = helix_db.get_connection(target_db)
        try:
            invocation_rows = _load_rows(conn, "invocation_log", "timestamp, id") if _table_exists(conn, "invocation_log") else []
            routing_rows = _load_rows(conn, "routing_decisions", "rowid") if _table_exists(conn, "routing_decisions") else []
        finally:
            conn.close()

        root = _project_root(db_path)
        audit_rows = _load_jsonl(root / ".helix" / "audit" / "opus-block-events.log")
        blocked_paths = {
            _normalize_path(str(row.get("file_path") or ""))
            for row in audit_rows
            if _normalize_path(str(row.get("file_path") or ""))
        }
        hook_present = (root / ".claude" / "hooks" / "pretooluse-opus-repo-block.sh").is_file()

        if not invocation_rows and not routing_rows and not audit_rows and not (root / ".helix" / "handover" / "CURRENT.json").exists():
            cost_ms = max(1, int((time.perf_counter() - started) * 1000))
            return DetectorResult(
                verdict="blocked",
                findings=[],
                cost_ms=cost_ms,
                raw={"reason": "no invocation_log, routing_decisions, audit log, or current handover state"},
            )

        findings: list[dict[str, Any]] = []
        invocation_index = _build_invocation_index(invocation_rows)

        for row in routing_rows:
            role = _resolve_role(row, invocation_index)
            paths = _extract_paths(row)
            detail_text = _row_text(row)

            if _is_pm_role(role):
                for path in paths:
                    if path in blocked_paths:
                        continue
                    findings.append(
                        {
                            "kind": "pm_direct_edit",
                            "detail": (
                                f"Opus direct edit/write bypass detected for {path}"
                                if hook_present
                                else f"Opus direct edit/write detected for {path} while PreToolUse hook is missing"
                            ),
                        }
                    )

            allowed_patterns = _extract_allowed_patterns(row)
            if allowed_patterns:
                for path in paths:
                    if _matches_allowed(path, allowed_patterns):
                        continue
                    findings.append(
                        {
                            "kind": "scope_violation",
                            "detail": f"{path} is outside allowed_files ({', '.join(allowed_patterns)})",
                        }
                    )

            if role == "qa":
                for path in paths:
                    if _is_code_path(path):
                        findings.append(
                            {
                                "kind": "role_breach",
                                "detail": f"role=qa edited code path {path}",
                            }
                        )
            if _is_pmo_role(role):
                for path in paths:
                    if path.startswith(("docs/", ".helix/")):
                        continue
                    findings.append(
                        {
                            "kind": "role_breach",
                            "detail": f"role={role} edited write-disallowed path {path}",
                        }
                    )

            if not paths and _is_pm_role(role) and "edit" in detail_text.lower():
                findings.append(
                    {
                        "kind": "pm_direct_edit",
                        "detail": "Opus direct edit/write bypass detected without path metadata",
                    }
                )

        findings.extend(_collect_handover_findings(root))

        unique_findings: list[dict[str, Any]] = []
        seen_pairs: set[tuple[str, str]] = set()
        for finding in findings:
            pair = (str(finding.get("kind") or ""), str(finding.get("detail") or ""))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            unique_findings.append(finding)

        verdict = "failed" if unique_findings else "passed"
        cost_ms = max(1, int((time.perf_counter() - started) * 1000))
        return DetectorResult(
            verdict=verdict,
            findings=unique_findings,
            cost_ms=cost_ms,
            raw={
                "project_root": str(root),
                "invocation_rows": len(invocation_rows),
                "routing_rows": len(routing_rows),
                "opus_block_events": len(audit_rows),
                "hook_present": hook_present,
            },
        )
