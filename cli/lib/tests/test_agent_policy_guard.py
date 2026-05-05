import py_compile
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import agent_policy_guard


MODULE_PATH = LIB_DIR / "agent_policy_guard.py"


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_valid_team_definition_passes() -> None:
    payload = agent_policy_guard.check_team_definition(
        {
            "strategy": "parallel",
            "members": [
                {"role": "se", "engine": "codex", "task": "API 実装"},
                {"role": "fe", "engine": "claude", "task": "画面実装"},
            ],
        }
    )

    assert payload["ok"] is True


def test_opus_style_self_delegation_is_blocked() -> None:
    payload = agent_policy_guard.check_team_definition(
        {"strategy": "sequential", "members": [{"role": "opus", "engine": "codex", "task": "実装"}]}
    )

    assert payload["ok"] is False
    assert any(item["code"] == "blocked_self_delegation" for item in payload["errors"])


def test_research_task_must_route_to_research_role() -> None:
    payload = agent_policy_guard.check_team_definition(
        {"strategy": "sequential", "members": [{"role": "se", "engine": "codex", "task": "Web検索でSDKを調査"}]}
    )

    assert payload["ok"] is False
    assert any(item["code"] == "research_task_wrong_role" for item in payload["errors"])


def test_execution_roles_cannot_pin_tl_class_model() -> None:
    payload = agent_policy_guard.check_team_definition(
        {"strategy": "sequential", "members": [{"role": "pg", "engine": "codex", "model": "gpt-5.4", "task": "実装"}]}
    )

    assert payload["ok"] is False
    assert any(item["code"] == "overpowered_execution_model" for item in payload["errors"])
