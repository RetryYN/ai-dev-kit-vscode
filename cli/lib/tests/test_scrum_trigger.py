import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import scrum_trigger


def _db_path(tmp_path: Path) -> Path:
    return tmp_path / ".helix" / "helix.db"


def _fetch_one(db_path: Path, query: str, params: tuple = ()) -> sqlite3.Row:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(query, params).fetchone()
    finally:
        conn.close()


def _trigger(**overrides):
    data = {
        "scrum_type": "unit",
        "source_id": "docs/features/auth/D-API.md",
        "artifact_ref": "D-API",
        "event_type": "uncertainty_marker",
        "detected_at": "2026-05-02T00:00:00Z",
        "last_seen_at": "2026-05-02T00:00:00Z",
        "ttl_at": "2026-05-09T00:00:00Z",
        "uncertainty_score": 3,
        "impact_score": 3,
        "confidence": 0.8,
        "evidence_count": 1,
        "normalized_signature": "sig-auth",
        "content_hash": "hash-auth",
        "status": "pending",
        "reason_code": "uncertainty_marker",
        "evidence_path_hint": "docs/features/auth/D-API.md:1-1",
        "source_path": "docs/features/auth/D-API.md",
        "source_line_start": 1,
        "source_line_end": 1,
        "created_by": "pytest",
        "created_at": "2026-05-02T00:00:00Z",
    }
    data.update(overrides)
    return data


def test_detect_triggers_finds_uncertain_tbd_and_kpi_markers(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs" / "features" / "billing"
    docs_dir.mkdir(parents=True)
    (docs_dir / "D-API.md").write_text(
        "\n".join(
            [
                "# D-API",
                "- 未確定: 契約の詳細は要確認",
                "- TBD: 境界値は実装前に確認",
                "- KPI 逸脱: エラー率が閾値を超過",
            ]
        ),
        encoding="utf-8",
    )

    triggers = scrum_trigger.detect_triggers(["docs/features"], project_root=tmp_path)

    assert {trigger["event_type"] for trigger in triggers} >= {"uncertainty_marker", "new_fact", "pre_impl_uncertain"}
    assert all("raw" not in trigger and "body" not in trigger for trigger in triggers)
    assert any(trigger["scrum_type"] == "post-deploy" for trigger in triggers)


def test_evaluate_quadrant_maps_each_quadrant() -> None:
    assert scrum_trigger.evaluate_quadrant({"uncertainty_score": 1, "impact_score": 1})["recommended_scrum_type"] == "unit"
    assert scrum_trigger.evaluate_quadrant({"uncertainty_score": 4, "impact_score": 1})["recommended_scrum_type"] == "unit"
    assert (
        scrum_trigger.evaluate_quadrant(
            {"uncertainty_score": 1, "impact_score": 4, "source_path": "docs/features/ui/D-UI.md"}
        )["recommended_scrum_type"]
        == "ui"
    )
    assert (
        scrum_trigger.evaluate_quadrant(
            {"uncertainty_score": 4, "impact_score": 4, "source_path": "docs/run/L10-observe.md"}
        )["recommended_scrum_type"]
        == "post-deploy"
    )


def test_redact_trigger_fields_removes_raw_and_redacts_secret_and_pii() -> None:
    fake_aws_key = "AK" + "IA" + "ABCDEFGHIJKLMNOP"
    redacted = scrum_trigger.redact_trigger_fields(
        {
            "title": f"leaked {fake_aws_key}",
            "evidence": "owner alice@example.com",
            "reason": "safe reason",
            "recommendation": "rotate token",
            "raw_body": "do not persist this",
        }
    )

    assert redacted["title"] == "[REDACTED]"
    assert redacted["evidence"] == "[REDACTED]"
    assert redacted["recommendation"] == "[REDACTED]"
    assert "raw_body" not in redacted


def test_save_to_db_upserts_duplicate_by_dedup_key(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path)
    trigger = _trigger()

    first = scrum_trigger.save_to_db([trigger], db_path)
    second = scrum_trigger.save_to_db([trigger], db_path)

    row = _fetch_one(db_path, "SELECT trigger_id, evidence_count FROM scrum_trigger")
    assert first["inserted"] == 1
    assert second["updated"] == 1
    assert row["trigger_id"] == first["ids"][0]
    assert row["evidence_count"] == 2


def test_transition_status_validates_lifecycle(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path)
    trigger_id = scrum_trigger.save_to_db([_trigger()], db_path)["ids"][0]

    with pytest.raises(ValueError, match="invalid transition"):
        scrum_trigger.transition_status(trigger_id, "adopted", "PM", db_path=db_path)

    updated = scrum_trigger.transition_status(trigger_id, "triaged", "PM", "looks valid", db_path)

    assert updated["status"] == "triaged"
    assert updated["status_owner"] == "PM"


def test_check_ttl_reports_and_applies_transitions(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path)
    now = datetime(2026, 5, 20, tzinfo=timezone.utc)
    old_pending = _trigger(
        source_id="pending",
        normalized_signature="sig-pending",
        detected_at="2026-05-10T00:00:00Z",
        last_seen_at="2026-05-10T00:00:00Z",
    )
    old_triaged = _trigger(
        source_id="triaged",
        normalized_signature="sig-triaged",
        status="triaged",
        detected_at="2026-05-01T00:00:00Z",
        last_seen_at="2026-05-01T00:00:00Z",
    )
    retained = _trigger(
        source_id="retention",
        normalized_signature="sig-retention",
        detected_at=(now - timedelta(days=91)).isoformat().replace("+00:00", "Z"),
        last_seen_at=(now - timedelta(days=91)).isoformat().replace("+00:00", "Z"),
    )
    ids = scrum_trigger.save_to_db([old_pending, old_triaged, retained], db_path)["ids"]

    result = scrum_trigger.check_ttl(db_path, apply=True, now=now)

    assert {(action["from_status"], action["to_status"]) for action in result["actions"]} == {
        ("pending", "triaged"),
        ("triaged", "archived"),
        ("pending", "archived"),
    }
    assert _fetch_one(db_path, "SELECT status FROM scrum_trigger WHERE trigger_id = ?", (ids[0],))["status"] == "triaged"
    assert _fetch_one(db_path, "SELECT status FROM scrum_trigger WHERE trigger_id = ?", (ids[1],))["status"] == "archived"
    assert _fetch_one(db_path, "SELECT status FROM scrum_trigger WHERE trigger_id = ?", (ids[2],))["status"] == "archived"


def test_cap_per_sprint_keeps_highest_priority_oldest_first() -> None:
    triggers = [
        _trigger(sprint_id="S1", source_id="a", impact_score=3, uncertainty_score=5, detected_at="2026-05-03T00:00:00Z"),
        _trigger(sprint_id="S1", source_id="b", impact_score=5, uncertainty_score=2, detected_at="2026-05-02T00:00:00Z"),
        _trigger(sprint_id="S1", source_id="c", impact_score=5, uncertainty_score=2, detected_at="2026-05-01T00:00:00Z"),
        _trigger(sprint_id="S2", source_id="d", impact_score=5, uncertainty_score=5, detected_at="2026-05-01T00:00:00Z"),
    ]

    kept = scrum_trigger.cap_per_sprint(triggers, "S1", cap=2)

    assert [trigger["source_id"] for trigger in kept] == ["c", "b"]
