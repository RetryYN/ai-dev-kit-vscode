import json
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import auto_run_engine


def test_start_initializes_state_and_budget_window(tmp_path: Path) -> None:
    """DoD 検証: L7-auto-run-loop-frameworkplan start initializes skeleton state."""
    engine = auto_run_engine.AutoRunEngine(project_root=tmp_path)

    payload = engine.start(plan_id="L7-auto-run-loop-frameworkplan", duration_minutes=45)

    raw = json.loads((tmp_path / ".helix" / "auto-run" / "current.json").read_text(encoding="utf-8"))
    assert raw["status"] == "running"
    assert raw["plan"]["plan_id"] == "L7-auto-run-loop-frameworkplan"
    assert payload["budget"]["duration_minutes"] == 45
    assert payload["integrations"]["compaction_api"] == "pending_next_phase"


def test_budget_set_minutes_updates_deadline(tmp_path: Path) -> None:
    """DoD 検証: L7-auto-run-loop-frameworkplan budget updates time window."""
    engine = auto_run_engine.AutoRunEngine(project_root=tmp_path)
    engine.start(plan_id="PLAN-A", duration_minutes=30)

    payload = engine.budget(set_minutes=10)

    assert payload["budget"]["duration_minutes"] == 10
    assert payload["budget"]["within_time_window"] is True


def test_heartbeat_marks_resume_ready_from_scheduler(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: L7-auto-run-loop-frameworkplan heartbeat converts carry into resume action."""
    engine = auto_run_engine.AutoRunEngine(project_root=tmp_path)
    engine.start(plan_id="PLAN-B", duration_minutes=30)

    def fake_scheduler(*, within_time_window: bool) -> dict[str, object]:
        assert within_time_window is True
        return {
            "carry_count": 2,
            "should_schedule": True,
            "schedulewakeup_candidate": {
                "kind": "ScheduleWakeup",
                "after_minutes": 15,
                "prompt": "Resume PLAN-B",
            },
        }

    monkeypatch.setattr(engine, "_run_heartbeat_scheduler", fake_scheduler)

    payload = engine.heartbeat()

    assert payload["heartbeat"]["carry_count"] == 2
    assert payload["resume"]["resume_ready"] is True
    assert payload["resume"]["action"] == "resume_plan"


def test_resume_returns_idle_when_window_expired(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: L7-auto-run-loop-frameworkplan resume stays idle after budget expiry."""
    engine = auto_run_engine.AutoRunEngine(project_root=tmp_path)
    engine.start(plan_id="PLAN-C", duration_minutes=30)

    state_path = tmp_path / ".helix" / "auto-run" / "current.json"
    raw = json.loads(state_path.read_text(encoding="utf-8"))
    raw["budget_window"]["deadline_at"] = "2000-01-01T00:00:00+09:00"
    state_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def fake_scheduler(*, within_time_window: bool) -> dict[str, object]:
        assert within_time_window is False
        return {
            "carry_count": 3,
            "should_schedule": False,
            "schedulewakeup_candidate": None,
        }

    monkeypatch.setattr(engine, "_run_heartbeat_scheduler", fake_scheduler)

    payload = engine.resume()

    assert payload["resume"]["resume_ready"] is False
    assert payload["resume"]["reason"] == "budget window expired"


def test_stop_marks_state_stopped(tmp_path: Path) -> None:
    """DoD 検証: L7-auto-run-loop-frameworkplan stop transitions state to stopped."""
    engine = auto_run_engine.AutoRunEngine(project_root=tmp_path)
    engine.start(plan_id="PLAN-D", duration_minutes=15)

    payload = engine.stop()

    assert payload["status"] == "stopped"
    assert payload["resume"]["resume_ready"] is False
