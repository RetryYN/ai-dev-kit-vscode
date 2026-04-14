# D-LEARNING-REFACTOR: learning_engine.py 責務分割設計

> Status: Draft（段階実装）
> Date: 2026-04-14
> Authors: TL

---

## 1. 目的

`cli/lib/learning_engine.py`（2000行・48関数/クラス）が単一ファイルに複数責務を抱え、保守性・テスト容易性が低下している問題（GAP-037）を解消するため、責務別に3ファイルへ分割する設計を提案する。

---

## 2. 現状分析

### 2.1 ファイル概要

- **ファイル**: `cli/lib/learning_engine.py`
- **行数**: 2000行
- **関数/クラス数**: 48
- **主要責務**（分析結果）:
  1. ユーティリティ関数（slugify, redact, truncate 等）
  2. パターン抽出・推論（analyze_success, analyze_failure）
  3. Recipe 生成・構造化
  4. 品質評価（coverage, lint, security collecting）
  5. Recipe 永続化（save_recipe, list_recipes）
  6. Recipe 検索（find_recipe, from_history）

### 2.2 主要関数グルーピング

**Group A: 共通ユーティリティ（共通部分）**
- `_connect`, `_now_iso`, `_slugify`, `_json_load_or_none`, `_truncate`, `_redact`
- `_extract_parameters`, `_build_pattern_key`, `_guess_builder_type`
- `_infer_why_it_worked`, `_infer_applicability`, `_collect_summary`
- `_project_root_from_db_path`, `_resolve_tool`, `_run_command`, `_parse_json_from_text`

**Group B: 成功/失敗分析（Core）**
- `analyze_success`, `analyze_failure`
- `_analyze_builder_success`, `_analyze_builder_failure`
- `_collect_failure_text`, `_classify_failure_type`, `_failure_reason`, `_failure_prevention_template`
- `_encode_builder_execution_run_id`, `_decode_builder_execution_run_id`

**Group C: メトリクス収集（Metrics）**
- `_find_test_result_in_text`, `_latest_helix_test_result`
- `_count_python_source_lines`
- `_extract_python_coverage_percent`, `_extract_go_coverage_percent`
- `_collect_test_results`, `_validate_matrix_schema`, `_collect_contract_results`
- `_parse_ruff_errors`, `_collect_lint_errors`, `_collect_security_issues`, `_collect_textlint_errors`
- `_collect_quality_results`, `_collect_verification`

**Group D: Recipe 生成・永続化（Recipe）**
- `save_recipe`, `list_recipes`, `from_history`, `find_recipe`
- `resolve_success_run_ids`
- `_history_query_tokens`, `_history_recipe_text`, `_history_recipe_score`

---

## 3. 分割設計

### 3.1 推奨ファイル構成（3ファイル分割）

```
cli/lib/
├── learning_engine.py              ← 後方互換ラッパー（50-100行）
├── learning/                        ← 新規ディレクトリ
│   ├── __init__.py
│   ├── core.py                      ← Group A + Group B（約 900行）
│   ├── metrics.py                   ← Group C（約 600行）
│   └── recipe.py                    ← Group D（約 500行）
```

### 3.2 各ファイルの責務

**`learning/core.py` (約 900行)**

責務: ユーティリティ関数 + 成功/失敗分析ロジック

主要 API:
- `analyze_success(task_run_id, db_path) -> dict | None`
- `analyze_failure(task_run_id, db_path) -> dict | None`

内部関数（プライベート）:
- 共通ユーティリティ（Group A 全て）
- 失敗分析系（Group B の `_classify_failure_type` 等）

**`learning/metrics.py` (約 600行)**

責務: プロジェクトメトリクス収集（coverage / lint / security / contract）

主要 API:
- `collect_test_results(project_root) -> dict`
- `collect_quality_results(project_root) -> dict`
- `collect_contract_results(project_root) -> dict`
- `collect_verification(project_root) -> dict`

内部関数:
- 言語別 coverage パーサー（Python, Go）
- lint / security / textlint 集計

**`learning/recipe.py` (約 500行)**

責務: Recipe の生成・永続化・検索

主要 API:
- `save_recipe(recipe, project_root) -> str`  # recipe_id を返す
- `list_recipes(project_root) -> list[dict]`
- `find_recipe(recipe_id, project_root) -> dict | None`
- `from_history(query, project_root, limit=5) -> dict`
- `resolve_success_run_ids(db_path, task_id=None, all_success=False) -> list[int]`

内部関数:
- パターンマッチング・スコアリング（`_history_*`）
- ファイル I/O（YAML 読み書き）

---

## 4. 後方互換ラッパー

`cli/lib/learning_engine.py` は全ての public API を re-export する薄いラッパーとする:

```python
# cli/lib/learning_engine.py (新)
"""Learning Engine — 後方互換ラッパー.

責務分割後のファサード。
新規コードは cli/lib/learning/ 配下のモジュールを直接 import することを推奨。
"""

# Core analysis
from learning.core import analyze_success, analyze_failure

# Metrics collection
from learning.metrics import (
    collect_test_results,
    collect_quality_results,
    collect_contract_results,
    collect_verification,
)

# Recipe management
from learning.recipe import (
    save_recipe,
    list_recipes,
    find_recipe,
    from_history,
    resolve_success_run_ids,
)

__all__ = [
    "analyze_success",
    "analyze_failure",
    "collect_test_results",
    "collect_quality_results",
    "collect_contract_results",
    "collect_verification",
    "save_recipe",
    "list_recipes",
    "find_recipe",
    "from_history",
    "resolve_success_run_ids",
]
```

既存コードの `from learning_engine import X` は無変更で動作する。

---

## 5. マイグレーション手順

### Phase 1: 準備（0.5 Sprint）

1. `cli/lib/learning/` ディレクトリ作成
2. 既存 `test_learning_engine.py` の全テスト通過を確認（baseline）
3. `learning_engine.py` を `learning_engine_original.py` として複製（rollback 用）

### Phase 2: Metrics 抽出（0.5 Sprint）

1. Group C の関数を `learning/metrics.py` に移動
2. `learning_engine.py` から Group C 関数を削除、`from learning.metrics import *` 追加
3. テスト実行 → 全件 pass 確認
4. コミット（小さく）

### Phase 3: Recipe 抽出（0.5 Sprint）

1. Group D の関数を `learning/recipe.py` に移動
2. 同様の import 変換
3. テスト実行 → pass 確認

### Phase 4: Core 抽出（0.5 Sprint）

1. Group A + B の関数を `learning/core.py` に移動
2. 残る `learning_engine.py` は re-export のみに
3. テスト全件 pass 確認
4. 最終コミット

### Phase 5: 既存呼び出し元更新（1 Sprint）

1. `cli/helix-learn`, `cli/helix-promote`, `cli/helix-discover` 等の import を `from learning.core import X` に更新（任意）
2. 後方互換は維持、新規コードのみ分割先を直接 import 推奨

### Rollback 手順

問題発生時:
1. `git revert` で直近のコミットを戻す
2. または `cli/lib/learning_engine_original.py` を `learning_engine.py` に置き換え
3. `cli/lib/learning/` を削除

---

## 6. テスト戦略

### 6.1 baseline tests

既存 `test_learning_engine.py`（12テスト）を全件 pass させる。分割中は継続的に確認。

### 6.2 新規テスト（各分割ファイル）

- `test_learning_core.py` — Group A+B の単体テスト（推奨: 15 テスト）
- `test_learning_metrics.py` — Group C の単体テスト（推奨: 10 テスト）
- `test_learning_recipe.py` — Group D の単体テスト（推奨: 12 テスト）

合計 37+ テスト（現状 12 → 49+）で、カバレッジ向上も同時達成。

### 6.3 統合テスト

既存 `test_learning_engine.py` は削除せず、後方互換の確認用テストとして維持。

---

## 7. リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| 循環 import の発生 | metrics / recipe → core 方向の一方向依存を徹底 |
| テスト失敗 | 各 Phase ごとに全件 pass を必須チェック |
| 既存コード破壊 | 後方互換ラッパーで API 維持 |
| パフォーマンス劣化 | 分割前後でベンチマーク取得・比較 |
| Rollback 困難 | `learning_engine_original.py` を rollback 用に保持、各 Phase 独立コミット |

---

## 8. 既知の制約・今後の課題

| 項目 | 内容 | 優先度 |
|------|------|------|
| 実装未着手 | 本文書は設計のみ、実装は別スプリント | P2（GAP-037 本体） |
| 更なる分割 | core.py が 900行なので将来さらに分割の可能性 | P3 |
| 関数名の統一 | Public/Private の命名規則を分割時に再整理 | P3 |
| 型ヒント完備 | 移行時に型ヒントを厳密化 | P3 |

---

## 9. References

- `cli/lib/learning_engine.py` (2000行, 48関数/クラス)
- [ADR-003: Learning Engine Foundations](../adr/ADR-003-learning-engine.md)
- [ADR-008: ビルダー抽象化](../adr/ADR-008-builder-abstraction.md)
- [docs/design/L2-learning-engine.md](./L2-learning-engine.md)
- `cli/lib/tests/test_learning_engine.py` (12テスト, baseline)
