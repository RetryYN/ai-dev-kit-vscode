from __future__ import annotations

import os
import re
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


PLAN_RE = re.compile(r"\bPLAN-(\d{3})\b")


def _project_root(db_path: str | Path) -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root)
    target = Path(db_path).resolve()
    if target.parent.name == ".helix":
        return target.parent.parent
    return Path.cwd()


def _read_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _extract_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    frontmatter = text[4:end]
    body = text[end + 5 :]
    try:
        parsed = parse_yaml(frontmatter)
    except Exception:
        return {}, body
    return parsed if isinstance(parsed, dict) else {}, body


def _git_log_contains_plan(root: Path, plan_id: str) -> bool:
    completed = subprocess.run(
        [
            "git",
            "log",
            "--all",
            f"--grep={plan_id}",
            "--format=%H%x09%s%x09%b",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=root,
    )
    return plan_id in completed.stdout


def _routing_table_exists(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
        ("routing_decisions",),
    ).fetchone()
    return row is not None


def _retro_exists(conn: sqlite3.Connection, plan_id: str, root: Path) -> bool:
    if _routing_table_exists(conn):
        rows = conn.execute("SELECT * FROM routing_decisions ORDER BY rowid").fetchall()
        for row in rows:
            for value in row:
                if value is None:
                    continue
                if plan_id in str(value) or "retro" in str(value).lower():
                    return True

    docs_root = root / "docs"
    if docs_root.exists():
        for path in docs_root.rglob("*.md"):
            text = _read_text(path)
            if not text:
                continue
            lowered = text.lower()
            if plan_id in text and ("retro" in lowered or "retrospective" in lowered):
                return True
    return False


class Axis08PlanIntegrity(BaseDetector):
    id = "axis-08"
    name = "plan-retro integrity"
    phase_gate = "G6"
    kind = "detector"

    def run(self, db_path: str | Path) -> DetectorResult:
        started = time.perf_counter()
        target_db = Path(db_path)
        helix_db._prepare_db_path(str(target_db))
        conn = helix_db.get_connection(target_db)
        root = _project_root(db_path)
        findings: list[dict[str, Any]] = []

        try:
            plan_root = root / "docs" / "plans"
            if not plan_root.exists():
                cost_ms = max(1, int((time.perf_counter() - started) * 1000))
                return DetectorResult(
                    verdict="blocked",
                    findings=[],
                    cost_ms=cost_ms,
                    raw={"reason": "docs/plans is missing", "project_root": str(root)},
                )

            for path in sorted(plan_root.rglob("PLAN-*.md")):
                text = _read_text(path)
                if text is None:
                    continue
                frontmatter, _body = _extract_frontmatter(text)
                if not frontmatter:
                    continue
                status = str(frontmatter.get("status") or "").strip().lower()
                plan_id = str(frontmatter.get("plan_id") or "").strip()
                if not plan_id:
                    plan_match = PLAN_RE.search(path.name)
                    plan_id = f"PLAN-{plan_match.group(1)}" if plan_match else path.stem
                if status != "finalized":
                    findings.append(
                        {
                            "plan_id": plan_id,
                            "status": status or "unknown",
                            "kind": "stale_draft",
                        }
                    )
                    continue

                if not _git_log_contains_plan(root, plan_id):
                    findings.append(
                        {
                            "plan_id": plan_id,
                            "status": status,
                            "kind": "no_commits",
                        }
                    )
                if not _retro_exists(conn, plan_id, root):
                    findings.append(
                        {
                            "plan_id": plan_id,
                            "status": status,
                            "kind": "no_retro",
                        }
                    )
        finally:
            conn.close()

        verdict = "passed" if not any(finding["kind"] in {"no_commits", "no_retro"} for finding in findings) else "failed"
        cost_ms = max(1, int((time.perf_counter() - started) * 1000))
        return DetectorResult(
            verdict=verdict,
            findings=findings,
            cost_ms=cost_ms,
            raw={
                "project_root": str(root),
                "plan_count": len(list((root / "docs" / "plans").rglob("PLAN-*.md"))) if (root / "docs" / "plans").exists() else 0,
            },
        )
