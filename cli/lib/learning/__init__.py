"""HELIX Learning Engine — モジュラーパッケージ.

D-LEARNING-REFACTOR.md 準拠の責務分割パッケージ。

## 推奨インポート

- 新規コード: サブモジュール経由
  ```python
  from learning.core import analyze_success, analyze_failure
  from learning.metrics import collect_test_results, collect_quality_results
  from learning.recipe import save_recipe, list_recipes, find_recipe
  ```

- 既存コード: learning_engine 直接（後方互換）
  ```python
  from learning_engine import analyze_success, save_recipe
  ```

## 現在の実装段階

本パッケージは Phase 1+2（facade-first approach）:
- サブモジュールは learning_engine.py から re-export
- 段階的に実体を各サブモジュールに移動予定（別スプリント）

詳細は docs/design/D-LEARNING-REFACTOR.md を参照。
"""

# バージョン情報
__version__ = "0.1.0"
__migration_phase__ = "facade"  # facade → partial → full の3段階
