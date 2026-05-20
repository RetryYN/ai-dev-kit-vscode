from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
import sys

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import escalation_integration
import helix_db


def _init_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / ".helix" / "helix.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HELIX_DB_PATH", str(db_path))
    helix_db.init_db(str(db_path))
    return db_path


def _entries(
    *,
    count: int,
    failure_type: str = "missing-artifact",
    plan_id: str = "PLAN-097",
    created_at: str | None = None,
) -> list[dict]:
    timestamp = created_at or datetime.now(UTC).isoformat()
    return [
        {
            "plan_id": plan_id,
            "failure_type": failure_type,
            "context": f"{failure_type}-context-{index}",
            "created_at": timestamp,
        }
        for index in range(count)
    ]


def _fetch_pattern_row(db_path: Path, pattern_id: str):
    conn = helix_db.get_connection(str(db_path))
    try:
        return conn.execute(
            """
            SELECT id, pattern_id, escalation_level, occurrence_count
            FROM refactor_degrade_pattern
            WHERE pattern_id = ?
            """,
            (pattern_id,),
        ).fetchone()
    finally:
        conn.close()


def test_integrate_with_curator_persists_warn_pattern(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: PLAN-097 §12 U-097-005 (単発 failure は warn として保存される)"""
    db_path = _init_db(tmp_path, monkeypatch)

    result = escalation_integration.integrate_with_curator(_entries(count=1))
    row = _fetch_pattern_row(db_path, "PLAN-097:missing-artifact")

    assert result["pattern_id"] == "PLAN-097:missing-artifact"
    assert result["escalation_level"] == "warn"
    assert row is not None
    assert row["id"] == result["row_id"]
    assert row["escalation_level"] == "warn"
    assert row["occurrence_count"] == 1


def test_integrate_with_curator_promotes_error_threshold(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: PLAN-097 §12 U-097-006 (同種失敗 3 件で error へ昇格する)"""
    db_path = _init_db(tmp_path, monkeypatch)

    result = escalation_integration.integrate_with_curator(_entries(count=3, failure_type="stale-plan"))
    row = _fetch_pattern_row(db_path, "PLAN-097:stale-plan")

    assert result["escalation_level"] == "error"
    assert row is not None
    assert row["escalation_level"] == "error"
    assert row["occurrence_count"] == 3


def test_integrate_with_curator_promotes_fail_close_for_stale_pattern(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: PLAN-097 §12 U-097-007 (90 日超 stale pattern は fail-close へ昇格する)"""
    db_path = _init_db(tmp_path, monkeypatch)
    stale_created_at = (datetime.now(UTC) - timedelta(days=91)).isoformat()

    result = escalation_integration.integrate_with_curator(
        _entries(count=1, failure_type="dependency-cycle", created_at=stale_created_at)
    )
    row = _fetch_pattern_row(db_path, "PLAN-097:dependency-cycle")

    assert result["days_active"] >= 90
    assert result["escalation_level"] == "fail-close"
    assert row is not None
    assert row["escalation_level"] == "fail-close"


def test_integrate_with_curator_upserts_existing_pattern(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: PLAN-097 §12 U-097-008 (同一 pattern は row を増やさず upsert 更新する)"""
    db_path = _init_db(tmp_path, monkeypatch)

    first = escalation_integration.integrate_with_curator(_entries(count=1, failure_type="repeat"))
    second = escalation_integration.integrate_with_curator(_entries(count=3, failure_type="repeat"))
    row = _fetch_pattern_row(db_path, "PLAN-097:repeat")

    assert first["row_id"] == second["row_id"]
    assert second["escalation_level"] == "error"
    assert row is not None
    assert row["id"] == first["row_id"]
    assert row["occurrence_count"] == 3
