import json
import sqlite3
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
import observability_helper as observe


def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "project" / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))
    return db_path


def _fetch_one(db_path: Path, query: str, params: tuple = ()) -> sqlite3.Row:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(query, params).fetchone()
    finally:
        conn.close()


def test_log_records_event_with_redaction(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    row_id = observe.record_event(
        str(db_path),
        "deploy",
        observe.redact_data({"key": "val", "password": "open-sesame"}, []),
        severity="info",
        source="test",
    )
    row = _fetch_one(db_path, "SELECT * FROM events WHERE id = ?", (row_id,))
    assert row["event_name"] == "deploy"
    assert row["severity"] == "info"
    assert json.loads(row["data_json"]) == {"key": "val", "password": "***"}


def test_metric_records_value_and_tags(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    row_id = observe.record_metric(str(db_path), "latency", 12.3, tags=observe.parse_tags("env=prod,route=/v1"))
    row = _fetch_one(db_path, "SELECT * FROM metrics WHERE id = ?", (row_id,))
    assert row["metric_name"] == "latency"
    assert row["value"] == 12.3
    assert json.loads(row["tags_json"]) == {"env": "prod", "route": "/v1"}


def test_redaction_applies_to_password_field() -> None:
    assert observe.redact_data({"nested": {"password": "secret-value"}}, []) == {"nested": {"password": "***"}}


def test_redaction_applies_to_api_key() -> None:
    redacted = observe.redact_data({"config": {"api_key": "abc123"}, "message": "uses sk-test"}, [])
    assert redacted == {"config": {"api_key": "***"}, "message": "***"}


def test_export_to_quarantine_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    observe.record_event(str(db_path), "test", {"key": "val"})
    output = home / ".helix" / "quarantine" / "observe.json"
    rc = observe.main(["--db-path", str(db_path), "export", "--format", "json", "--output", str(output)])
    assert rc == 0
    assert json.loads(output.read_text(encoding="utf-8"))[0]["event_name"] == "test"


def test_export_outside_quarantine_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    rc = observe.main(["--db-path", str(db_path), "export", "--format", "json", "--output", str(tmp_path / "out.json")])
    captured = capsys.readouterr()
    assert rc == 1
    assert "OBS_05" in captured.err
    assert not (tmp_path / "out.json").exists()


def test_no_redact_flag_logs_warning(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    rc = observe.main([
        "--db-path", str(db_path), "log", "--event", "unsafe",
        "--data", '{"password":"raw"}', "--no-redact",
    ])
    captured = capsys.readouterr()
    assert rc == 0
    assert "--no-redact is PM-only" in captured.err
    row = _fetch_one(db_path, "SELECT data_json FROM events WHERE event_name = ?", ("unsafe",))
    assert json.loads(row["data_json"]) == {"password": "raw"}
    observe.main(["--db-path", str(db_path), "report", "--event", "unsafe", "--format", "json"])
    report = capsys.readouterr().out
    assert '"password": "***"' in report
    assert "raw" not in report


def test_report_filters_by_event_name(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    observe.record_event(str(db_path), "kept", {"a": 1})
    observe.record_event(str(db_path), "dropped", {"a": 2})
    assert [event["event_name"] for event in observe.query_events(str(db_path), event="kept")] == ["kept"]


def test_report_filters_by_severity(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    observe.record_event(str(db_path), "info_event", {}, severity="info")
    observe.record_event(str(db_path), "error_event", {}, severity="error")
    assert [event["event_name"] for event in observe.query_events(str(db_path), severity="error")] == ["error_event"]


def test_format_prometheus_output() -> None:
    output = observe.format_prometheus([
        {"type": "metric", "metric_name": "latency_ms", "value": 12.3, "tags": {"env": "prod"}, "recorded_at": 1},
        {"type": "event", "event_name": "deploy", "severity": "info", "source": "ci", "occurred_at": 2},
    ])
    assert "# TYPE helix_latency_ms gauge" in output
    assert 'helix_latency_ms{env="prod"} 12.3 1000' in output
    assert 'helix_events_total{event="deploy",severity="info",source="ci"} 1 2000' in output
