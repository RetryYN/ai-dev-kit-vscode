import sqlite3
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import deferred_findings
import helix_db


def _yaml_path(tmp_path: Path) -> Path:
    return tmp_path / ".helix" / "audit" / "deferred-findings.yaml"


def _db_path(tmp_path: Path) -> Path:
    db_path = tmp_path / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))
    return db_path


def _finding(**overrides):
    data = {
        "plan_id": "PLAN-007",
        "phase": "L2",
        "severity": "high",
        "source": ".helix/reviews/plans/PLAN-007.json#/findings/0",
        "title": "Missing redaction",
        "body": "Do not expose plain tokens",
        "recommendation": "Apply shared redaction helper",
    }
    data.update(overrides)
    return data


def _fetch_one(db_path: Path, query: str, params: tuple = ()) -> sqlite3.Row:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(query, params).fetchone()
    finally:
        conn.close()


def _fetch_count(db_path: Path, table: str) -> int:
    return int(_fetch_one(db_path, f"SELECT COUNT(*) AS count FROM {table}")["count"])


def test_add_finding_assigns_unique_ids(tmp_path: Path) -> None:
    yaml_path = _yaml_path(tmp_path)

    first_id = deferred_findings.add_finding(yaml_path, _finding())
    second_id = deferred_findings.add_finding(yaml_path, _finding())

    assert first_id == "DF-PLAN-007-L2-001"
    assert second_id == "DF-PLAN-007-L2-002"


def test_add_finding_redacts_secret_body(tmp_path: Path) -> None:
    yaml_path = _yaml_path(tmp_path)

    fake_aws_key = "AK" + "IA" + "ABCDEFGHIJKLMNOP"
    finding_id = deferred_findings.add_finding(
        yaml_path,
        _finding(body=f"leaked access key {fake_aws_key}"),
    )

    finding = deferred_findings.list_findings(yaml_path)[0]
    assert finding["id"] == finding_id
    assert finding["body"] == "[REDACTED]"
    assert fake_aws_key[:4] not in yaml_path.read_text(encoding="utf-8")


def test_add_finding_preserves_explicit_null_target(tmp_path: Path) -> None:
    yaml_path = _yaml_path(tmp_path)

    deferred_findings.add_finding(yaml_path, _finding(target=None))

    finding = deferred_findings.list_findings(yaml_path)[0]
    assert finding["target"] is None


def test_update_finding_restricts_status_values(tmp_path: Path) -> None:
    yaml_path = _yaml_path(tmp_path)
    finding_id = deferred_findings.add_finding(yaml_path, _finding())

    with pytest.raises(ValueError, match="invalid status"):
        deferred_findings.update_finding(yaml_path, finding_id, status="closed")

    updated = deferred_findings.update_finding(yaml_path, finding_id, status="resolved")
    assert updated["status"] == "resolved"
    assert updated["resolved_at"].endswith("Z")


def test_carry_finding_requires_approval_for_p1(tmp_path: Path) -> None:
    yaml_path = _yaml_path(tmp_path)
    finding_id = deferred_findings.add_finding(yaml_path, _finding())

    with pytest.raises(ValueError, match="approved_by is required"):
        deferred_findings.carry_finding(yaml_path, finding_id, "PLAN-007", "G3")

    carried = deferred_findings.carry_finding(
        yaml_path,
        finding_id,
        "PLAN-007",
        "G3",
        approved_by="PM",
    )
    assert carried["status"] == "carried"
    assert carried["target"] == {"plan_id": "PLAN-007", "phase": "G3"}
    assert carried["pm_approval"]["approved_by"] == "PM"


def test_sync_yaml_to_db_upserts_new_and_existing_rows(tmp_path: Path, capsys) -> None:
    yaml_path = _yaml_path(tmp_path)
    db_path = _db_path(tmp_path)
    capsys.readouterr()
    first_id = deferred_findings.add_finding(yaml_path, _finding())

    assert deferred_findings.sync_yaml_to_db(yaml_path, db_path) == {
        "inserted": 1,
        "updated": 0,
        "unchanged": 0,
    }

    deferred_findings.update_finding(yaml_path, first_id, status="resolved")
    second_id = deferred_findings.add_finding(yaml_path, _finding(phase="L3"))

    assert deferred_findings.sync_yaml_to_db(yaml_path, db_path) == {
        "inserted": 1,
        "updated": 1,
        "unchanged": 0,
    }
    assert _fetch_count(db_path, "deferred_findings") == 2
    assert _fetch_one(db_path, "SELECT status FROM deferred_findings WHERE id = ?", (first_id,))["status"] == "resolved"
    assert _fetch_one(db_path, "SELECT phase FROM deferred_findings WHERE id = ?", (second_id,))["phase"] == "L3"


def test_adjust_score_inserts_adjustment(tmp_path: Path, capsys) -> None:
    yaml_path = _yaml_path(tmp_path)
    db_path = _db_path(tmp_path)
    capsys.readouterr()
    finding_id = deferred_findings.add_finding(yaml_path, _finding())
    deferred_findings.sync_yaml_to_db(yaml_path, db_path)

    adjustment_id = deferred_findings.adjust_score(db_path, finding_id, "G4", "accuracy")

    assert adjustment_id == 1
    row = _fetch_one(db_path, "SELECT * FROM accuracy_score_adjustments WHERE id = ?", (adjustment_id,))
    assert row["finding_id"] == finding_id
    assert row["penalty"] == pytest.approx(0.70)


def test_compute_effective_score_reads_view(tmp_path: Path, capsys) -> None:
    yaml_path = _yaml_path(tmp_path)
    db_path = _db_path(tmp_path)
    capsys.readouterr()
    finding_id = deferred_findings.add_finding(yaml_path, _finding())
    deferred_findings.sync_yaml_to_db(yaml_path, db_path)
    helix_db.record_accuracy_score(str(db_path), "PLAN-007", "G4", "accuracy", 4)
    deferred_findings.adjust_score(db_path, finding_id, "G4", "accuracy")

    rows = deferred_findings.compute_effective_score(db_path, "PLAN-007", "G4")

    assert len(rows) == 1
    assert rows[0]["raw_score"] == 4.0
    assert rows[0]["total_penalty"] == pytest.approx(0.70)
    assert rows[0]["effective_score"] == pytest.approx(3.30)
