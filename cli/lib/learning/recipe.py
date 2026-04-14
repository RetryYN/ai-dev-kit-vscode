"""Learning Engine Recipe — Recipe 永続化と検索.

責務: Recipe の保存・一覧取得・検索・履歴マッチを提供する。

## Public API

- `save_recipe(recipe, project_root)` — Recipe 永続化
- `list_recipes(project_root)` — Recipe 一覧取得
- `find_recipe(recipe_id, project_root)` — 個別 Recipe 取得
- `from_history(query, project_root, limit=5)` — 履歴検索
- `resolve_success_run_ids(db_path, task_id=None, all_success=False)` — task_run_id 解決

## 現在の実装

Facade-first approach: learning_engine.py から re-export。
将来的に Group D（Recipe 操作）を本モジュールへ移動予定。
"""

from __future__ import annotations

import sys
from pathlib import Path

_LIB_DIR = Path(__file__).resolve().parents[1]
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from learning_engine import (
    save_recipe,
    list_recipes,
    find_recipe,
    from_history,
    resolve_success_run_ids,
)

__all__ = [
    "save_recipe",
    "list_recipes",
    "find_recipe",
    "from_history",
    "resolve_success_run_ids",
]
