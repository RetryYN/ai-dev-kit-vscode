from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
import sqlite3
import sys


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from curator.curator_engine import analyze_pattern, register_pattern


def test_analyze_empty() -> None:
    """DoD 検証: PLAN-093-test-design.md U-093-010 (空入力は warn の空パターンとして扱う)"""
    result = analyze_pattern([])

    assert result["pattern_id"] == "global:unclassified"
    assert result["violation_count"] == 0
    assert result["escalation_level"] == "warn"


def test_analyze_single() -> None:
    """DoD 検証: PLAN-093-test-design.md U-093-011 (単一 failure_log から pattern を抽出する)"""
    result = analyze_pattern(
        [
            {
                "plan_id": "PLAN-093",
                "failure_type": "missing-artifact",
                "context": "cli/lib/curator/curator_engine.py missing",
                "created_at": datetime.now(UTC).isoformat(),
            }
        ]
    )

    assert result["pattern_id"] == "PLAN-093:missing-artifact"
    assert result["trigger"] == "missing-artifact"
    assert result["violation_count"] == 1
    assert result["escalation_level"] == "warn"


def test_analyze_threshold_promotes() -> None:
    """DoD 検証: PLAN-093-test-design.md U-093-012 (同種失敗 3 件で promotion 候補になる)"""
    now = datetime.now(UTC).isoformat()
    entries = [
        {"plan_id": "PLAN-093", "failure_type": "stale-plan", "context": "entry-1", "created_at": now},
        {"plan_id": "PLAN-093", "failure_type": "stale-plan", "context": "entry-2", "created_at": now},
        {"plan_id": "PLAN-093", "failure_type": "stale-plan", "context": "entry-3", "created_at": now},
    ]

    result = analyze_pattern(entries)

    assert result["promotion_candidate"] is True
    assert result["escalation_level"] == "error"
    assert result["occurrence_count"] == 3


def test_register_pattern() -> None:
    """DoD 検証: PLAN-093-test-design.md U-093-013 (pattern register は SQLite row を upsert する)"""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE refactor_degrade_pattern (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_id TEXT UNIQUE NOT NULL,
            trigger TEXT NOT NULL,
            description TEXT,
            escalation_level TEXT NOT NULL DEFAULT 'warn',
            occurrence_count INTEGER NOT NULL DEFAULT 0,
            promoted_at TEXT,
            demoted_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    first_seen = (datetime.now(UTC) - timedelta(days=31)).isoformat()
    pattern = analyze_pattern(
        [
            {"plan_id": "PLAN-093", "failure_type": "dependency-cycle", "context": "A->B->A", "created_at": first_seen},
            {"plan_id": "PLAN-093", "failure_type": "dependency-cycle", "context": "A->B->A", "created_at": first_seen},
            {"plan_id": "PLAN-093", "failure_type": "dependency-cycle", "context": "A->B->A", "created_at": first_seen},
        ]
    )

    row_id = register_pattern(conn, pattern)
    conn.commit()
    row = conn.execute(
        """
        SELECT id, pattern_id, escalation_level, occurrence_count, promoted_at
        FROM refactor_degrade_pattern
        WHERE pattern_id = ?
        """,
        (pattern["pattern_id"],),
    ).fetchone()
    conn.close()

    assert row is not None
    assert row[0] == row_id
    assert row[1] == "PLAN-093:dependency-cycle"
    assert row[2] == "error"
    assert row[3] == 3
    assert row[4] is not None
