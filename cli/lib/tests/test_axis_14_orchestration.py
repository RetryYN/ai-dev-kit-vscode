from __future__ import annotations

import json
import sqlite3
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import helix_db
from detectors.axis_14_orchestration import Axis14OrchestrationIntegrity


def _init_repo(project_root: Path) -> None:
    project_root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=project_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "qa@example.com"], cwd=project_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "QA"], cwd=project_root, check=True, capture_output=True, text=True)
    (project_root / "README.md").write_text("init\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=project_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=project_root, check=True, capture_output=True, text=True)


def _init_db(project_root: Path) -> Path:
    db_path = project_root / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS routing_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT,
                decision TEXT,
                detail TEXT,
                created_at TEXT,
                role TEXT,
                plan_id TEXT,
                task_id TEXT,
                allowed_files TEXT,
                changed_files TEXT,
                tool_name TEXT
            );
            """
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def _insert_invocation(db_path: Path, *, role: str, plan_id: str = "PLAN-063", task_id: str = "W-9") -> None:
    helix_db.record_invocation(
        str(db_path),
        {
            "timestamp": "2026-05-13T00:00:00+00:00",
            "type": "codex",
            "role": role,
            "model": "gpt-5.4",
            "task_id": task_id,
            "plan_id": plan_id,
            "sprint": ".2",
            "duration_ms": 1200,
            "decision": "passed",
            "raw_meta": {
                "role": role,
                "model": "gpt-5.4",
                "task_id": task_id,
                "plan_id": plan_id,
                "sprint": ".2",
                "decision": "passed",
                "duration_ms": 1200,
            },
        },
    )


def _insert_routing(db_path: Path, **row: str) -> None:
    columns = [
        "path",
        "decision",
        "detail",
        "created_at",
        "role",
        "plan_id",
        "task_id",
        "allowed_files",
        "changed_files",
        "tool_name",
    ]
    values = [row.get(column, "") for column in columns]
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            INSERT INTO routing_decisions (
                path, decision, detail, created_at, role, plan_id, task_id,
                allowed_files, changed_files, tool_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(values),
        )
        conn.commit()
    finally:
        conn.close()


def _write_block_event(project_root: Path, file_path: str) -> None:
    audit_path = project_root / ".helix" / "audit" / "opus-block-events.log"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(
        json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_name": "Edit",
                "file_path": file_path,
                "reason": "blocked",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_handover(project_root: Path, *, status: str, updated_at: datetime) -> None:
    current_path = project_root / ".helix" / "handover" / "CURRENT.json"
    current_path.parent.mkdir(parents=True, exist_ok=True)
    current_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "generated_at": updated_at.isoformat(),
                "updated_at": updated_at.isoformat(),
                "revision": 1,
                "owner": "codex",
                "scope": "backend",
                "git": {"branch": "main", "head_sha": "abc123", "dirty": False},
                "phase": "L4",
                "sprint": ".2",
                "project": "demo",
                "task": {"id": "PLAN-063-W-9", "title": "axis-14", "status": status},
                "files": {"target": ["cli/lib/detectors/axis_14_orchestration.py"], "completed": [], "pending": []},
                "tests": ["pytest"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_axis_14_detects_pm_direct_edit_without_block_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "project"
    _init_repo(project_root)
    db_path = _init_db(project_root)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))
    _insert_invocation(db_path, role="opus")
    _insert_routing(
        db_path,
        path="cli/lib/budget.py",
        decision="direct edit",
        detail="Opus edit bypass",
        created_at="2026-05-13T00:00:00+00:00",
        role="opus",
        plan_id="PLAN-063",
        task_id="W-9",
        tool_name="Edit",
    )

    result = Axis14OrchestrationIntegrity().run(db_path)

    assert result.verdict == "failed"
    assert any(finding["kind"] == "pm_direct_edit" for finding in result.findings)


def test_axis_14_ignores_pm_edit_when_audit_block_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "project"
    _init_repo(project_root)
    db_path = _init_db(project_root)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))
    _insert_invocation(db_path, role="opus")
    _insert_routing(
        db_path,
        path="cli/lib/budget.py",
        decision="direct edit",
        detail="Opus edit blocked by hook",
        created_at="2026-05-13T00:00:00+00:00",
        role="opus",
        plan_id="PLAN-063",
        task_id="W-9",
        tool_name="Edit",
    )
    _write_block_event(project_root, "cli/lib/budget.py")

    result = Axis14OrchestrationIntegrity().run(db_path)

    assert result.verdict == "passed"
    assert result.findings == []


def test_axis_14_detects_scope_violation_from_allowed_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "project"
    _init_repo(project_root)
    db_path = _init_db(project_root)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))
    _insert_invocation(db_path, role="se")
    _insert_routing(
        db_path,
        path="cli/helix",
        decision="allowed_files audit",
        detail="post validation",
        created_at="2026-05-13T00:00:00+00:00",
        role="se",
        plan_id="PLAN-063",
        task_id="W-9",
        allowed_files="cli/lib/detectors/axis_14_orchestration.py,cli/lib/tests/test_axis_14_orchestration.py",
        changed_files='["cli/lib/detectors/axis_14_orchestration.py", "cli/helix"]',
        tool_name="Write",
    )

    result = Axis14OrchestrationIntegrity().run(db_path)

    assert result.verdict == "failed"
    violations = [finding for finding in result.findings if finding["kind"] == "scope_violation"]
    assert len(violations) == 1
    assert "cli/helix" in violations[0]["detail"]


def test_axis_14_detects_handover_ready_for_review_with_clean_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "project"
    _init_repo(project_root)
    db_path = _init_db(project_root)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))
    _write_handover(project_root, status="ready_for_review", updated_at=datetime.now(timezone.utc))

    result = Axis14OrchestrationIntegrity().run(db_path)

    assert result.verdict == "failed"
    assert any("ready_for_review" in finding["detail"] for finding in result.findings if finding["kind"] == "handover_stale")


def test_axis_14_detects_stale_in_progress_handover_and_role_breach(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "project"
    _init_repo(project_root)
    db_path = _init_db(project_root)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))
    _write_handover(
        project_root,
        status="in_progress",
        updated_at=datetime.now(timezone.utc) - timedelta(days=8),
    )
    _insert_invocation(db_path, role="qa")
    _insert_routing(
        db_path,
        path="cli/lib/detectors/axis_08_plan_integrity.py",
        decision="code edit",
        detail="qa touched production code",
        created_at="2026-05-13T00:00:00+00:00",
        role="qa",
        plan_id="PLAN-063",
        task_id="W-9",
        tool_name="Edit",
    )
    _insert_invocation(db_path, role="pmo-sonnet", task_id="W-9b")
    _insert_routing(
        db_path,
        path="cli/lib/handover.py",
        decision="write disallowed",
        detail="pmo edited repo code",
        created_at="2026-05-13T00:10:00+00:00",
        role="pmo-sonnet",
        plan_id="PLAN-063",
        task_id="W-9b",
        tool_name="Write",
    )

    result = Axis14OrchestrationIntegrity().run(db_path)

    assert result.verdict == "failed"
    role_breaches = [finding for finding in result.findings if finding["kind"] == "role_breach"]
    assert len(role_breaches) == 2
    assert any("role=qa" in finding["detail"] for finding in role_breaches)
    assert any("role=pmo-sonnet" in finding["detail"] for finding in role_breaches)
    assert any("older than 7 days" in finding["detail"] for finding in result.findings if finding["kind"] == "handover_stale")
