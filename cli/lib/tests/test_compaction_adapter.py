"""L7-auto-run-poc-compaction-apiplan compaction_adapter 単体テスト."""

from __future__ import annotations

import json
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import compaction_adapter


def test_fake_adapter_records_request(tmp_path: Path, monkeypatch) -> None:
    """DoD 検証: L7-auto-run-poc-compaction-apiplan fake adapter records request and saves state."""
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))
    adapter = compaction_adapter.FakeCompactionAdapter()

    payload = adapter.request_compaction()
    state = json.loads((tmp_path / ".helix" / "auto-run" / "compaction.json").read_text(encoding="utf-8"))

    assert payload["status"] == "success"
    assert len(adapter.requests) == 1
    assert payload["compacted_at"] == adapter.last_compaction_at
    assert state["compaction_count"] == 1
    assert state["last_drift"] == 0.0


def test_fake_adapter_unavailable_returns_failed(tmp_path: Path, monkeypatch) -> None:
    """DoD 検証: L7-auto-run-poc-compaction-apiplan unavailable fake returns failed without state update."""
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))
    adapter = compaction_adapter.FakeCompactionAdapter(available=False)

    payload = adapter.request_compaction()

    assert payload["status"] == "failed"
    assert len(adapter.requests) == 1
    assert payload["compacted_at"] is None
    assert not (tmp_path / ".helix" / "auto-run" / "compaction.json").exists()


def test_dry_run_adapter_no_real_call(tmp_path: Path, monkeypatch) -> None:
    """DoD 検証: L7-auto-run-poc-compaction-apiplan dry-run request only logs and returns dry_run."""
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))
    adapter = compaction_adapter.DryRunCompactionAdapter()

    payload = adapter.request_compaction()

    assert payload["status"] == "dry_run"
    assert len(adapter.log) == 1
    assert "request_compaction" in adapter.log[0]
    assert not (tmp_path / ".helix" / "auto-run" / "compaction.json").exists()


def test_check_drift_threshold_exceeds() -> None:
    """DoD 検証: L7-auto-run-poc-compaction-apiplan drift above threshold requests compaction."""
    payload = compaction_adapter.check_drift_threshold(0.6, threshold=0.5)

    assert payload == {
        "ok": False,
        "drift": 0.6,
        "threshold": 0.5,
        "recommendation": "request_compaction",
    }


def test_check_drift_threshold_within() -> None:
    """DoD 検証: L7-auto-run-poc-compaction-apiplan drift within threshold continues execution."""
    payload = compaction_adapter.check_drift_threshold(0.3, threshold=0.5)

    assert payload == {
        "ok": True,
        "drift": 0.3,
        "threshold": 0.5,
        "recommendation": "continue",
    }


def test_sync_handover_after_compaction_dry_run(tmp_path: Path, monkeypatch) -> None:
    """DoD 検証: L7-auto-run-compaction-handover-syncplan dry-run returns handover snapshot only."""
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))
    handover_path = tmp_path / ".helix" / "handover" / "CURRENT.json"
    handover_path.parent.mkdir(parents=True, exist_ok=True)
    handover_path.write_text(
        json.dumps(
            {
                "updated_at": "2026-05-25T00:00:00+09:00",
                "next_action": "Resume compaction follow-up and validate audit sync.",
            }
        ),
        encoding="utf-8",
    )

    payload = compaction_adapter.sync_handover_after_compaction(
        compaction_adapter.FakeCompactionAdapter(),
        project_root=tmp_path,
        dry_run=True,
    )

    assert payload["status"] == "dry_run"
    assert payload["compaction_status"]["status"] == "success"
    assert payload["handover_snapshot"] == {
        "exists": True,
        "updated_at": "2026-05-25T00:00:00+09:00",
        "next_action_summary": "Resume compaction follow-up and validate audit sync.",
    }


def test_sync_handover_after_compaction_writes_when_not_dry_run(tmp_path: Path, monkeypatch) -> None:
    """DoD 検証: L7-auto-run-compaction-handover-syncplan non-dry-run writes audit snapshot."""
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))
    handover_path = tmp_path / ".helix" / "handover" / "CURRENT.json"
    handover_path.parent.mkdir(parents=True, exist_ok=True)
    handover_path.write_text(
        json.dumps(
            {
                "updated_at": "2026-05-25T00:00:00+09:00",
                "next_action": "Persist compaction audit output.",
            }
        ),
        encoding="utf-8",
    )

    payload = compaction_adapter.sync_handover_after_compaction(
        compaction_adapter.FakeCompactionAdapter(),
        project_root=tmp_path,
        dry_run=False,
    )

    audit_path = tmp_path / ".helix" / "handover" / "COMPACTION-SYNC.json"
    assert payload["status"] == "synced"
    assert audit_path.exists()
    assert json.loads(audit_path.read_text(encoding="utf-8")) == payload["handover_snapshot"]


def test_sync_handover_after_compaction_handles_missing_handover(tmp_path: Path, monkeypatch) -> None:
    """DoD 検証: L7-auto-run-compaction-handover-syncplan missing handover returns no_handover."""
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))

    payload = compaction_adapter.sync_handover_after_compaction(
        compaction_adapter.FakeCompactionAdapter(),
        project_root=tmp_path,
        dry_run=True,
    )

    assert payload["status"] == "no_handover"
    assert payload["compaction_status"]["status"] == "success"
    assert payload["handover_snapshot"] == {
        "exists": False,
        "updated_at": None,
        "next_action_summary": "",
    }
