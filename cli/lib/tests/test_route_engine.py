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


@pytest.mark.parametrize(
    ("drift_type", "mode", "kind", "subtype"),
    [
        ("schema", "Reverse", "reverse", "normalization"),
        ("contract", "Reverse", "reverse", "normalization"),
        ("code_smell", "Refactor", "refactor", None),
        ("structural", "Refactor", "refactor", None),
        ("dependency_outdated", "Retrofit", "retrofit", "dependency"),
        ("upgrade", "Retrofit", "retrofit", "upgrade"),
        ("config_drift", "Retrofit", "retrofit", "config"),
        ("production_incident", "incident", "incident", None),
        ("agent_runaway", "recovery", "recovery", None),
        ("feature_addition", "add_feature", "add_feature", None),
        ("user_feedback_iteration", "scrum_agile", "scrum_agile", None),
    ],
)
def test_drift_type_overrides_route(drift_type: str, mode: str, kind: str, subtype: str | None) -> None:
    """DoD 検証: L7-route-engine-drift-type-retrofit-ext-test-design.md U-EXT-001-U-EXT-007."""
    result = route_engine.RouteEngine().evaluate("drift", drift_type=drift_type)

    assert result.mode == mode
    assert result.kind == kind
    assert result.subtype == subtype
    assert result.drift_type == drift_type


@pytest.mark.parametrize(
    ("signal", "subtype", "drift_type"),
    [
        ("dependency_outdated", "dependency", "dependency_outdated"),
        ("upgrade", "upgrade", "upgrade"),
        ("config_drift", "config", "config_drift"),
    ],
)
def test_shortcut_signals_route_to_retrofit(signal: str, subtype: str, drift_type: str) -> None:
    """DoD 検証: L7-route-engine-drift-type-retrofit-ext-test-design.md U-EXT-009-U-EXT-011."""
    result = route_engine.RouteEngine().evaluate(signal)

    assert result.mode == "Retrofit"
    assert result.kind == "retrofit"
    assert result.subtype == subtype
    assert result.drift_type == drift_type


def test_non_drift_signal_keeps_drift_type_none() -> None:
    """DoD 検証: L7-route-engine-drift-type-retrofit-ext-test-design.md U-EXT-013."""
    result = route_engine.RouteEngine().evaluate("unknown_design")

    assert result.drift_type is None


def test_recommended_command_for_retrofit_is_json_object() -> None:
    """DoD 検証: L7-route-engine-drift-type-retrofit-ext-test-design.md U-EXT-014,U-EXT-023."""
    result = route_engine.RouteEngine().evaluate("upgrade")

    assert result.recommended_command == {
        "schema_version": "v1",
        "command": "helix plan draft",
        "args": {"kind": "retrofit", "drift_type": "upgrade"},
        "safety": {
            "auto_apply": False,
            "requires_human_approval": False,
            "requires_preflight": False,
        },
    }


def test_high_risk_upgrade_requires_reverse_preflight() -> None:
    """DoD 検証: L7-route-engine-drift-type-retrofit-ext-test-design.md U-EXT-024."""
    result = route_engine.RouteEngine().evaluate("upgrade", uncertainty="high", impact="high")

    assert result.recommended_command["command"] == "helix reverse upgrade R0"
    assert result.recommended_command["args"] == {}
    assert result.recommended_command["safety"] == {
        "auto_apply": False,
        "requires_human_approval": False,
        "requires_preflight": True,
    }


def test_recommended_command_for_reverse_and_refactor() -> None:
    """DoD 検証: L7-route-engine-drift-type-retrofit-ext-test-design.md U-EXT-015,U-EXT-016,U-EXT-026."""
    reverse_result = route_engine.RouteEngine().evaluate("drift", drift_type="schema")
    refactor_result = route_engine.RouteEngine().evaluate("drift", drift_type="code_smell")

    assert reverse_result.recommended_command == {
        "schema_version": "v1",
        "command": "helix reverse normalization R0",
        "args": {},
        "safety": {
            "auto_apply": False,
            "requires_human_approval": False,
            "requires_preflight": False,
        },
    }
    assert refactor_result.recommended_command == {
        "schema_version": "v1",
        "command": "helix plan draft",
        "args": {"kind": "refactor"},
        "safety": {
            "auto_apply": False,
            "requires_human_approval": False,
            "requires_preflight": False,
        },
    }


def test_to_dict_contains_drift_type_and_recommended_command() -> None:
    """DoD 検証: L7-route-engine-drift-type-retrofit-ext-test-design.md U-EXT-017."""
    result = route_engine.RouteEngine().evaluate("dependency_outdated")

    payload = result.to_dict()

    assert payload["drift_type"] == "dependency_outdated"
    assert payload["recommended_command"]["args"]["kind"] == "retrofit"


def test_from_detect_output_reads_drift_type_when_present() -> None:
    """DoD 検証: L7-route-engine-drift-type-retrofit-ext-test-design.md U-EXT-018,U-EXT-019."""
    payload = [
        {
            "detector": "axis_01_drift",
            "status": "drift",
            "result": {
                "uncertainty": "low",
                "impact": "high",
                "env": "dev",
                "drift_type": "config_drift",
            },
        },
        {
            "detector": "axis_01_drift",
            "status": "drift",
            "result": {"uncertainty": "low", "impact": "low", "env": "dev"},
        },
    ]

    results = route_engine.RouteEngine().from_detect_output(payload)

    assert results[0].mode == "Retrofit"
    assert results[0].drift_type == "config_drift"
    assert results[1].mode == "Reverse"
    assert results[1].drift_type == "schema"


def test_shortcut_signal_with_conflicting_drift_type_raises() -> None:
    """DoD 検証: L7-route-engine-drift-type-retrofit-ext-test-design.md U-EXT-025."""
    with pytest.raises(route_engine.RouteEngineError, match="矛盾"):
        route_engine.RouteEngine().evaluate("upgrade", drift_type="config_drift")


@pytest.mark.parametrize(
    ("signal", "mode", "kind", "drift_type"),
    [
        ("user_feedback_iteration", "scrum_agile", "scrum_agile", "user_feedback_iteration"),
        ("requirement_continuous_refinement", "scrum_agile", "scrum_agile", "user_feedback_iteration"),
        ("production_incident", "incident", "incident", "production_incident"),
        ("hotfix_required", "incident", "incident", "production_incident"),
        ("feature_addition", "add_feature", "add_feature", "feature_addition"),
        ("scope_extension", "add_feature", "add_feature", "feature_addition"),
        ("agent_runaway", "recovery", "recovery", "agent_runaway"),
        ("context_exhaustion", "recovery", "recovery", "agent_runaway"),
    ],
)
def test_new_mode_shortcut_signals_route_to_expected_mode(
    signal: str,
    mode: str,
    kind: str,
    drift_type: str,
) -> None:
    """DoD 検証: 4 mode shortcut signal は additive に mode と drift_type を固定する。"""
    result = route_engine.RouteEngine().evaluate(signal)

    assert result.mode == mode
    assert result.kind == kind
    assert result.drift_type == drift_type


@pytest.mark.parametrize(
    ("signal", "command", "args", "requires_human_approval"),
    [
        ("user_feedback_iteration", "helix scrum-agile init", {}, False),
        (
            "production_incident",
            "helix incident detect",
            {
                "incident_id": "<incident-id>",
                "summary": "auto-routed from production_incident",
                "severity": "P1",
                "env": "prod",
            },
            True,
        ),
        (
            "feature_addition",
            "helix add-feature add-design",
            {
                "feature": "<feature-id>",
                "summary": "auto-routed from feature_addition",
                "requires_plan": "<plan-id>",
            },
            False,
        ),
        (
            "agent_runaway",
            "helix recovery start",
            {
                "plan_id": "<plan-id>",
                "reopen_point": "HEAD",
            },
            True,
        ),
    ],
)
def test_recommended_command_for_new_modes_uses_mode_cli_contract(
    signal: str,
    command: str,
    args: dict[str, str],
    requires_human_approval: bool,
) -> None:
    """DoD 検証: 新 4 mode は mode CLI へ直接つながる RecommendedCommandV1 を返す。"""
    result = route_engine.RouteEngine().evaluate(signal)

    assert result.recommended_command == {
        "schema_version": "v1",
        "command": command,
        "args": args,
        "safety": {
            "auto_apply": False,
            "requires_human_approval": requires_human_approval,
            "requires_preflight": False,
        },
    }


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
    """DoD 検証: L7-route-engine-drift-type-retrofit-ext-test-design.md U-EXT-020,U-EXT-021."""
    items = route_engine.RouteEngine().list_signals()

    assert len(items) == 19
    assert [item["signal"] for item in items[:18]] == [
        "drift",
        "debt_degradation",
        "regression_prod",
        "regression_dev",
        "runaway",
        "incident",
        "unknown_design",
        "dependency_outdated",
        "upgrade",
        "config_drift",
        "user_feedback_iteration",
        "requirement_continuous_refinement",
        "production_incident",
        "hotfix_required",
        "feature_addition",
        "scope_extension",
        "agent_runaway",
        "context_exhaustion",
    ]
    drift_entry = items[0]
    assert drift_entry["drift_types"] == [
        "schema",
        "contract",
        "code_smell",
        "structural",
        "dependency_outdated",
        "upgrade",
        "config_drift",
        "production_incident",
        "agent_runaway",
        "feature_addition",
        "user_feedback_iteration",
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
        ("user_feedback_iteration", "dev", "scrum_agile"),
        ("production_incident", "dev", "incident"),
        ("feature_addition", "dev", "add_feature"),
        ("agent_runaway", "dev", "recovery"),
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
