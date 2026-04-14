"""Learning Engine Core — 成功/失敗分析.

責務: task_run / builder_execution の履歴から成功・失敗パターンを分析する。

## Public API

- `analyze_success(task_run_id, db_path)` — 成功パターン分析
- `analyze_failure(task_run_id, db_path)` — 失敗パターン分析

## 現在の実装

Facade-first approach: learning_engine.py から re-export。
将来的に Group A（ユーティリティ）+ Group B（分析ロジック）を本モジュールへ移動予定。
"""

from __future__ import annotations

import sys
from pathlib import Path

# learning_engine.py を親ディレクトリから import
_LIB_DIR = Path(__file__).resolve().parents[1]
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

# Public API の re-export
from learning_engine import (
    analyze_success,
    analyze_failure,
)

__all__ = [
    "analyze_success",
    "analyze_failure",
]
