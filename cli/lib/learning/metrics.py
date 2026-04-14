"""Learning Engine Metrics — プロジェクトメトリクス収集.

責務: テスト結果・カバレッジ・lint・security・契約検証のメトリクスを
プロジェクトから収集する。

## Public API（_collect_* の underscore を外した公開版）

- `collect_test_results(project_root)` — テスト実行結果
- `collect_quality_results(project_root)` — 品質メトリクス（lint/type/security/textlint）
- `collect_contract_results(project_root)` — 契約検証結果
- `collect_verification(project_root)` — 検証総合

## 現在の実装

Facade-first approach: learning_engine.py から re-export。
将来的に Group C（メトリクス収集）を本モジュールへ移動予定。
"""

from __future__ import annotations

import sys
from pathlib import Path

_LIB_DIR = Path(__file__).resolve().parents[1]
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

# Private 関数を import して Public として再公開
from learning_engine import (
    _collect_test_results as collect_test_results,
    _collect_quality_results as collect_quality_results,
    _collect_contract_results as collect_contract_results,
    _collect_verification as collect_verification,
)

__all__ = [
    "collect_test_results",
    "collect_quality_results",
    "collect_contract_results",
    "collect_verification",
]
