from typing import Any

import deliverable_gate


def _make_index(features: dict[str, Any], waivers: list | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"features": features}
    if waivers is not None:
        payload["waivers"] = waivers
    return payload


def _make_state(features: dict[str, Any]) -> dict[str, Any]:
    return {"features": features}


def test_pre_release_gates_share_l7_mapping() -> None:
    for gate in ("G6.5", "G6.7", "G6.9"):
        result = deliverable_gate.evaluate_gate(_make_index({}), _make_state({}), gate)

        assert result["layers"] == ["L7"]
        assert result["result"] == "pass"


def test_pre_release_gate_fails_pending_l7_deliverable() -> None:
    index = _make_index(
        {
            "release": {
                "requires": {"L7": ["D-ROLLBACK"]},
            }
        }
    )
    state = _make_state(
        {
            "release": {
                "deliverables": {"D-ROLLBACK": {"status": "pending"}},
            }
        }
    )

    result = deliverable_gate.evaluate_gate(index, state, "G6.9")

    assert result["result"] == "fail"
    assert result["summary"]["pending"] == 1
    assert result["features"]["release"]["layers"]["L7"]["result"] == "fail"


def test_pre_release_gate_honors_l7_waiver() -> None:
    index = _make_index(
        {
            "release": {
                "requires": {"L7": ["D-MONITORING"]},
            }
        },
        waivers=[{"feature_id": "release", "deliverable_id": "D-MONITORING"}],
    )
    state = _make_state(
        {
            "release": {
                "deliverables": {"D-MONITORING": {"status": "pending"}},
            }
        }
    )

    result = deliverable_gate.evaluate_gate(index, state, "G6.7")

    assert result["result"] == "pass"
    assert result["summary"]["waived"] == 1
    assert result["features"]["release"]["layers"]["L7"]["deliverables"][0]["status"] == "waived"
