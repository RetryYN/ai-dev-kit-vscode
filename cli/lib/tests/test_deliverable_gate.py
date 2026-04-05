"""deliverable_gate.py のテスト。"""

import json
import sys
from pathlib import Path
from typing import Any

import pytest

LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import deliverable_gate


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_index(features: dict[str, Any], waivers: list | None = None, rules: dict | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"features": features}
    if waivers is not None:
        payload["waivers"] = waivers
    if rules is not None:
        payload["rules"] = rules
    return payload


def _make_state(features: dict[str, Any]) -> dict[str, Any]:
    return {"features": features}


# ---------------------------------------------------------------------------
# evaluate_gate 基本テスト
# ---------------------------------------------------------------------------

class TestEvaluateGateBasic:
    def test_unknown_gate_raises(self) -> None:
        with pytest.raises(deliverable_gate.DeliverableGateError, match="サポート外"):
            deliverable_gate.evaluate_gate({}, {}, "G99")

    def test_non_dict_features_raises(self) -> None:
        with pytest.raises(deliverable_gate.DeliverableGateError, match="features"):
            deliverable_gate.evaluate_gate({"features": "bad"}, {}, "G2")

    def test_empty_features_passes(self) -> None:
        result = deliverable_gate.evaluate_gate(
            _make_index({}),
            _make_state({}),
            "G2",
        )
        assert result["result"] == "pass"
        assert result["gate"] == "G2"

    def test_all_done_passes(self) -> None:
        index = _make_index({
            "feat-a": {
                "requires": {"L1": ["D-REQ-F"]},
            }
        })
        state = _make_state({
            "feat-a": {
                "deliverables": {"D-REQ-F": {"status": "done"}},
            }
        })
        result = deliverable_gate.evaluate_gate(index, state, "G0.5")
        assert result["result"] == "pass"
        assert result["summary"]["done"] == 1

    def test_pending_fails(self) -> None:
        index = _make_index({
            "feat-a": {
                "requires": {"L1": ["D-REQ-F"]},
            }
        })
        state = _make_state({
            "feat-a": {
                "deliverables": {"D-REQ-F": {"status": "pending"}},
            }
        })
        result = deliverable_gate.evaluate_gate(index, state, "G0.5")
        assert result["result"] == "fail"
        assert result["summary"]["pending"] == 1


# ---------------------------------------------------------------------------
# waiver テスト
# ---------------------------------------------------------------------------

class TestEvaluateGateWaivers:
    def test_waiver_overrides_pending(self) -> None:
        index = _make_index(
            features={
                "feat-a": {
                    "requires": {"L1": ["D-REQ-F"]},
                }
            },
            waivers=[{"feature_id": "feat-a", "deliverable_id": "D-REQ-F"}],
        )
        state = _make_state({
            "feat-a": {
                "deliverables": {"D-REQ-F": {"status": "pending"}},
            }
        })
        result = deliverable_gate.evaluate_gate(index, state, "G0.5")
        assert result["result"] == "pass"
        assert result["summary"]["waived"] == 1


# ---------------------------------------------------------------------------
# G5 UI skip テスト
# ---------------------------------------------------------------------------

class TestG5UiSkip:
    def test_g5_skips_non_ui_feature(self) -> None:
        index = _make_index({
            "feat-a": {
                "ui": False,
                "requires": {"L5": ["D-VISUAL"]},
            }
        })
        state = _make_state({
            "feat-a": {
                "deliverables": {"D-VISUAL": {"status": "pending"}},
            }
        })
        result = deliverable_gate.evaluate_gate(index, state, "G5")
        assert result["result"] == "pass"
        layer = result["features"]["feat-a"]["layers"]["L5"]
        assert layer["ui_skipped"] is True


# ---------------------------------------------------------------------------
# _status_from_state
# ---------------------------------------------------------------------------

class TestStatusFromState:
    def test_dict_with_status(self) -> None:
        assert deliverable_gate._status_from_state({"status": "done"}) == "done"

    def test_dict_without_status(self) -> None:
        assert deliverable_gate._status_from_state({}) == "pending"

    def test_string_status(self) -> None:
        assert deliverable_gate._status_from_state("waived") == "waived"

    def test_none_returns_pending(self) -> None:
        assert deliverable_gate._status_from_state(None) == "pending"


# ---------------------------------------------------------------------------
# _format_summary
# ---------------------------------------------------------------------------

class TestFormatSummary:
    def test_basic_summary(self) -> None:
        result = {
            "result": "pass",
            "summary": {
                "total": 2,
                "done": 2,
                "waived": 0,
                "not_applicable": 0,
                "pending": 0,
                "in_progress": 0,
                "partial": 0,
                "unknown": 0,
                "warnings": 0,
            },
        }
        text = deliverable_gate._format_summary(result)
        assert "2/2 done" in text
        assert "PASS" in text


# ---------------------------------------------------------------------------
# fullstack validation
# ---------------------------------------------------------------------------

class TestFullstackValidation:
    def test_fullstack_missing_contract_in_l3_raises(self) -> None:
        index = _make_index(
            features={
                "feat-a": {
                    "drive": "fullstack",
                    "requires": {"L3": ["D-API"]},
                }
            },
            rules={
                "deliverables": [{"id": "D-CONTRACT"}, {"id": "D-API"}],
            },
        )
        with pytest.raises(deliverable_gate.DeliverableGateError, match="fullstack"):
            deliverable_gate.evaluate_gate(index, _make_state({}), "G3")
