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
