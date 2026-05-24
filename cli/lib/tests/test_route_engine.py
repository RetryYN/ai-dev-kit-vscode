"""L7-helix-route-implplan unit tests.

契約: docs/plans/L7/L7-helix-route-implplan.md §2.B-§2.D
DoD 検証: docs/plans/L7/L7-helix-route-implplan.md §4
"""

from __future__ import annotations

import json
import py_compile
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import route_engine


MODULE_PATH = LIB_DIR / "route_engine.py"


def _sample_detect_payload() -> list[dict[str, object]]:
    return [
        {
            "detector": "axis_01_drift",
            "status": "drift",
            "result": {"uncertainty": "low", "impact": "high", "env": "dev"},
        },
        {
            "detector": "axis_07_runaway",
            "status": "runaway",
            "result": {"uncertainty": "high", "impact": "high", "env": "dev"},
        },
    ]


def test_module_py_compile() -> None:
    """DoD 検証: route_engine.py が py_compile を通る。"""
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_drift_routes_to_reverse_normalization() -> None:
    """DoD 検証: drift は Reverse/normalization へ固定される。"""
    result = route_engine.RouteEngine().evaluate("drift")

    assert result.mode == "Reverse"
    assert result.kind == "reverse"
    assert result.subtype == "normalization"
    assert result.priority == "P3"
    assert result.action == "suggest_only"


def test_debt_degradation_routes_to_refactor() -> None:
    """DoD 検証: debt_degradation は Refactor へ固定される。"""
    result = route_engine.RouteEngine().evaluate("debt_degradation", impact="high")

    assert result.mode == "Refactor"
    assert result.kind == "refactor"
    assert result.priority == "P1"
    assert result.suggest_command == "helix plan draft --kind refactor"


def test_runaway_routes_to_recovery() -> None:
    """DoD 検証: runaway は Recovery/recovery へ固定される。"""
    result = route_engine.RouteEngine().evaluate("runaway")

    assert result.mode == "Recovery"
    assert result.kind == "recovery"
    assert result.env == "dev"
    assert result.recover_args == {
        "signal_id": "runaway",
        "reopen_point": "HEAD",
        "auto_routed_from": "helix-route",
    }


def test_unknown_design_routes_to_reverse_code() -> None:
    """DoD 検証: unknown_design は Reverse/code へ固定される。"""
    result = route_engine.RouteEngine().evaluate("unknown_design", uncertainty="high")

    assert result.mode == "Reverse"
    assert result.kind == "reverse"
    assert result.subtype == "code"
    assert result.priority == "P2"
    assert result.action == "discovery_first"


def test_suggest_command_format_for_plan_draft() -> None:
    """DoD 検証: plan draft 系 signal は suggest_command を返す。"""
    result = route_engine.RouteEngine().evaluate("drift", impact="high")

    assert result.suggest_command == "helix plan draft --kind reverse"
    assert result.recover_args is None


def test_from_detect_output_batch() -> None:
    """DoD 検証: detect schema の list を batch 評価できる。"""
    results = route_engine.RouteEngine().from_detect_output(_sample_detect_payload())

    assert [item.signal for item in results] == ["drift", "runaway"]
    assert results[0].priority == "P1"
    assert results[1].priority == "P0"


def test_invalid_signal_and_invalid_schema_raise() -> None:
    """DoD 検証: 未登録 signal と scope 外 schema は fail-close。"""
    engine = route_engine.RouteEngine()

    with pytest.raises(route_engine.RouteEngineError, match="unknown signal"):
        engine.evaluate("mystery")

    with pytest.raises(ValueError, match="adapter"):
        engine.from_detect_output({"route_events": []})


def test_list_signals_returns_all() -> None:
    """DoD 検証: 7 signal + 1 alias が列挙される。"""
    items = route_engine.RouteEngine().list_signals()

    assert len(items) == 8
    assert [item["signal"] for item in items[:7]] == [
        "drift",
        "debt_degradation",
        "regression_prod",
        "regression_dev",
        "runaway",
        "incident",
        "unknown_design",
    ]
    assert items[-1]["signal"] == "degradation"
    assert items[-1]["deprecated"] is True


def test_incident_routes_by_env() -> None:
    """DoD 検証: incident は env で recovery/troubleshoot に分岐する。"""
    engine = route_engine.RouteEngine()

    prod = engine.evaluate("incident", env="prod")
    dev = engine.evaluate("incident", env="dev")

    assert prod.mode == "Incident"
    assert prod.kind == "recovery"
    assert prod.suggest_command == "helix recover plan --signal-id incident --reopen-point HEAD --auto-routed-from helix-route"
    assert dev.mode == "Incident"
    assert dev.kind == "troubleshoot"
    assert dev.suggest_command == "helix plan draft --kind troubleshoot"


def test_regression_signals_route_by_mode() -> None:
    """DoD 検証: regression_prod/dev は別 mode に固定される。"""
    engine = route_engine.RouteEngine()

    prod = engine.evaluate("regression_prod", env="prod")
    dev = engine.evaluate("regression_dev")

    assert prod.mode == "Incident"
    assert prod.kind == "recovery"
    assert prod.suggest_command == "helix plan draft --kind recovery"
    assert dev.mode == "Recovery"
    assert dev.kind == "recovery"
    assert dev.suggest_command == "helix recover plan --signal-id regression_dev --reopen-point HEAD --auto-routed-from helix-route"


@pytest.mark.parametrize(
    ("signal", "env", "mode"),
    [
        ("drift", "dev", "Reverse"),
        ("debt_degradation", "dev", "Refactor"),
        ("regression_prod", "prod", "Incident"),
        ("regression_dev", "dev", "Recovery"),
        ("runaway", "dev", "Recovery"),
        ("incident", "prod", "Incident"),
        ("unknown_design", "dev", "Reverse"),
    ],
)
def test_all_signals_high_high_keep_mode_and_force_p0(signal: str, env: str, mode: str) -> None:
    """DoD 検証: 全 signal × high/high で mode は不変、priority は P0。"""
    result = route_engine.RouteEngine().evaluate(
        signal,
        uncertainty="high",
        impact="high",
        env=env,
    )

    assert result.mode == mode
    assert result.priority == "P0"
    assert result.action == "emergency_routing"


def test_suggest_command_recover_connection() -> None:
    """DoD 検証: recover 連携 signal は --signal-id を渡す。"""
    result = route_engine.RouteEngine().evaluate("runaway", reopen_point="HEAD~2")

    assert result.suggest_command == (
        "helix recover plan --signal-id runaway --reopen-point HEAD~2 --auto-routed-from helix-route"
    )
    assert result.recover_args == {
        "signal_id": "runaway",
        "reopen_point": "HEAD~2",
        "auto_routed_from": "helix-route",
    }


def test_degradation_alias_warning(capsys: pytest.CaptureFixture[str]) -> None:
    """DoD 検証: degradation alias は warning を stderr に出して継続する。"""
    result = route_engine.RouteEngine().evaluate("degradation")
    captured = capsys.readouterr()

    assert result.signal == "debt_degradation"
    assert result.mode == "Refactor"
    assert "deprecation warning" in captured.err
    assert "use debt_degradation or regression_{prod,dev}" in captured.err


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"signal": "drift", "uncertainty": "maybe"}, "invalid uncertainty"),
        ({"signal": "drift", "impact": "maybe"}, "invalid impact"),
    ],
)
def test_invalid_uncertainty_or_impact_raises(kwargs: dict[str, str], match: str) -> None:
    """DoD 検証: invalid uncertainty/impact は fail-close。"""
    with pytest.raises(route_engine.RouteEngineError, match=match):
        route_engine.RouteEngine().evaluate(**kwargs)


def test_from_detect_output_fixture(tmp_path: Path) -> None:
    """DoD 検証: fixture JSON を読んで batch evaluate できる。"""
    fixture_path = tmp_path / "detect-run.json"
    fixture_path.write_text(json.dumps(_sample_detect_payload()), encoding="utf-8")

    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    results = route_engine.RouteEngine().from_detect_output(payload)

    assert len(results) == 2
    assert results[0].source_schema == "helix_detect_run_json_v1"
    assert results[1].suggest_command.startswith("helix recover plan --signal-id runaway")


def test_env_required_fail_close() -> None:
    """DoD 検証: incident / regression_prod は env 必須。"""
    engine = route_engine.RouteEngine()

    with pytest.raises(ValueError, match="env is required"):
        engine.evaluate("incident")

    with pytest.raises(ValueError, match="env is required"):
        engine.evaluate("regression_prod")
