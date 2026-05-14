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


def test_code_investigation_can_use_execution_role() -> None:
    payload = agent_policy_guard.check_team_definition(
        {"strategy": "sequential", "members": [{"role": "se", "engine": "codex", "task": "影響範囲調査"}]}
    )

    assert payload["ok"] is True


def test_single_member_policy_blocks_research_task() -> None:
    payload = agent_policy_guard.check_member("se", "codex", "Web検索でSDKを調査")

    assert payload["ok"] is False
    assert any(item["code"] == "research_task_wrong_role" for item in payload["errors"])


def test_plan023_impl_keyword_overrides_research_misjudgment() -> None:
    """PLAN-023 W-1: 実装系キーワードがあれば research 誤判定を緩和。

    W-P2-1a/W-P2-1b で発生した false positive (機械的な conf 編集タスクが
    research と誤判定されたケース) の再現と解消確認。
    """
    payload = agent_policy_guard.check_team_definition(
        {
            "strategy": "sequential",
            "members": [
                {
                    "role": "pg",
                    "engine": "codex",
                    "task": "以下のファイルを Read してから conf を編集して codex_thinking を追加",
                }
            ],
        }
    )

    assert payload["ok"] is True
    assert not any(
        item["code"] == "research_task_wrong_role" for item in payload["errors"]
    )


def test_plan023_pure_research_still_blocked() -> None:
    """PLAN-023 W-1: 純 research タスクは引き続き block (回帰なし)。

    実装系キーワードを含まない investigate / 比較系タスクは従来通り
    research 役割への誘導が必要。
    """
    payload = agent_policy_guard.check_team_definition(
        {
            "strategy": "sequential",
            "members": [
                {
                    "role": "pg",
                    "engine": "codex",
                    "task": "React の最新 SDK を investigate して比較",
                }
            ],
        }
    )

    assert payload["ok"] is False
    assert any(
        item["code"] == "research_task_wrong_role" for item in payload["errors"]
    )


def test_execution_roles_cannot_pin_tl_class_model() -> None:
    payload = agent_policy_guard.check_team_definition(
        {"strategy": "sequential", "members": [{"role": "pg", "engine": "codex", "model": "gpt-5.4", "task": "実装"}]}
    )

    assert payload["ok"] is False
    assert any(item["code"] == "overpowered_execution_model" for item in payload["errors"])


def test_allowed_roles_includes_internal() -> None:
    assert "recommender" in agent_policy_guard.ALLOWED_ROLES
    assert "classifier" in agent_policy_guard.ALLOWED_ROLES
    assert "effort-classifier" in agent_policy_guard.ALLOWED_ROLES


def test_recommender_passes_check() -> None:
    payload = agent_policy_guard.check_member("recommender", "codex", "task description")

    assert payload["ok"] is True
    assert not any(item["code"] == "invalid_role" for item in payload["errors"])


def test_policy_allows_pdm_tech_innovation() -> None:
    payload = agent_policy_guard.check_member("pdm-tech-innovation", "codex", "subagent 仕様同期")

    assert payload["ok"] is True
    assert not any(item["code"] == "invalid_role" for item in payload["errors"])


def test_policy_allows_pdm_marketing_innovation() -> None:
    payload = agent_policy_guard.check_member("pdm-marketing-innovation", "codex", "subagent 仕様同期")

    assert payload["ok"] is True
    assert not any(item["code"] == "invalid_role" for item in payload["errors"])


def test_policy_allows_pdm_innovation_manager() -> None:
    payload = agent_policy_guard.check_member("pdm-innovation-manager", "codex", "subagent 仕様同期")

    assert payload["ok"] is True
    assert not any(item["code"] == "invalid_role" for item in payload["errors"])
