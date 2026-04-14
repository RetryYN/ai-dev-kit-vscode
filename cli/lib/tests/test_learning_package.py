"""learning パッケージ（facade）のテスト.

GAP-037 Phase 1+2 の動作確認。learning.core / learning.metrics / learning.recipe が
learning_engine.py と同一の関数を公開することを検証する。
"""

from __future__ import annotations

import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))


def test_learning_package_importable() -> None:
    """learning パッケージ自体が import できる."""
    import learning

    assert learning.__migration_phase__ == "facade"


def test_learning_core_exposes_analyze_functions() -> None:
    """learning.core が analyze_success/analyze_failure を公開する."""
    from learning.core import analyze_success, analyze_failure

    assert callable(analyze_success)
    assert callable(analyze_failure)


def test_learning_metrics_exposes_collect_functions() -> None:
    """learning.metrics が collect_* 関数を公開する."""
    from learning.metrics import (
        collect_test_results,
        collect_quality_results,
        collect_contract_results,
        collect_verification,
    )

    assert callable(collect_test_results)
    assert callable(collect_quality_results)
    assert callable(collect_contract_results)
    assert callable(collect_verification)


def test_learning_recipe_exposes_recipe_functions() -> None:
    """learning.recipe が save/list/find/from_history を公開する."""
    from learning.recipe import (
        save_recipe,
        list_recipes,
        find_recipe,
        from_history,
        resolve_success_run_ids,
    )

    assert callable(save_recipe)
    assert callable(list_recipes)
    assert callable(find_recipe)
    assert callable(from_history)
    assert callable(resolve_success_run_ids)


def test_facade_functions_are_same_as_learning_engine() -> None:
    """facade が re-export する関数は learning_engine のものと同一."""
    import learning_engine
    from learning.core import analyze_success
    from learning.recipe import save_recipe, find_recipe

    assert analyze_success is learning_engine.analyze_success
    assert save_recipe is learning_engine.save_recipe
    assert find_recipe is learning_engine.find_recipe


def test_backward_compat_still_works() -> None:
    """既存の learning_engine 直接 import も動作する（後方互換）."""
    from learning_engine import analyze_success, save_recipe, find_recipe

    assert callable(analyze_success)
    assert callable(save_recipe)
    assert callable(find_recipe)
