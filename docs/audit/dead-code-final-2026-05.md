# Dead Code Final Audit (2026-05-11)

## 概要

PLAN-061 W-1: PLAN-058 W-3 で生成した dead-code-candidates-2026-05.md (vulture 119 件) を
1 件ずつ精査し、確定削除候補を抽出。

## 精査方法

機械的 3 段階フィルタ:
1. **vulture 出力 (119 件)** から既知 false positive (39 件) を除外:
   - `*.row_factory` (SQLite cursor 設定)
   - `whitespace_split` / `commenters` (shlex.shlex 属性)
   - `cli/lib/builders/cli.py` line 13-33 (`_auto_discover_builders` 経由動的 import)
2. **残 80 件** から caller 数を grep で算出:
   - cli/ skills/ docs/ 内の `.py` / `.sh` / `.bats` ファイル
   - `cli/helix*` bash scripts
   - 定義ファイル自身を除外
3. **callers = 0 の 19 件** をさらに 3 条件で精査:
   - 同一ファイル内自己参照 = 1 (定義行のみ、内部使用なし)
   - bash scripts からの参照 = 0
   - `__all__` 未登録

## 精査結果

| カテゴリ | 件数 | 備考 |
|---|---|---|
| 全 vulture 候補 | 119 | --min-confidence 60 |
| 確定 false positive 除外 | -39 | row_factory / shlex / auto_discover |
| caller >= 1 (要確認) | -44 | 外部参照あり、削除しない |
| tests のみ参照 (caller=1) | -17 | tests 経由のみ、本体実装は dead だが test も同時削除要 → carry |
| **callers = 0 + 安全条件 3 つ満たす** | **19** | **削除候補確定** |

## 削除候補 19 件

| # | filepath | line | name | type |
|---|---|---|---|---|
| 1 | `cli/lib/code_catalog.py` | 263 | `is_non_indexable_path` | variable |
| 2 | `cli/lib/code_catalog.py` | 264 | `is_excluded_path` | variable |
| 3 | `cli/lib/code_catalog.py` | 266 | `default_seed_metadata` | variable |
| 4 | `cli/lib/code_catalog.py` | 268 | `extract_top_level_symbols` | variable |
| 5 | `cli/lib/code_catalog.py` | 269 | `resolve_symbol_line` | variable |
| 6 | `cli/lib/code_catalog.py` | 727 | `filter_coverage_items` | variable |
| 7 | `cli/lib/codex_post_validation.py` | 78 | `count_actual_diff_lines` | function |
| 8 | `cli/lib/context_guard.py` | 29 | `REQUIRED_CONTEXT_FILES` | variable |
| 9 | `cli/lib/deferred_findings.py` | 495 | `sync_db_to_yaml` | function |
| 10 | `cli/lib/effort_classifier.py` | 185 | `call_classifier` | function |
| 11 | `cli/lib/llm_guard.py` | 261 | `_without_quoted_strings` | function (private) |
| 12 | `cli/lib/llm_guard.py` | 3462 | `has_raw_codex_exec` | function |
| 13 | `cli/lib/llm_guard.py` | 3466 | `has_raw_claude_cli` | function |
| 14 | `cli/lib/merge_settings.py` | 124 | `_has_helix_hook` | function (private) |
| 15 | `cli/lib/migrate.py` | 113 | `TARGETS` | variable |
| 16 | `cli/lib/model_registry.py` | 49 | `get_default_primary` | function |
| 17 | `cli/lib/plan_schema.py` | 19 | `MINI_PLAN_PHASES` | variable |
| 18 | `cli/lib/skill_classifier.py` | 151 | `_run_classifier` | function (private) |
| 19 | `cli/lib/task_type_inference.py` | 7 | `KNOWN_TASK_TYPES` | variable |

## carry: tests-only callers (17 件)

これらは本体実装は dead だが、tests から参照されている。
削除には test ファイル側も同時更新が必要 → 別 PLAN または現 PLAN W-3 carry:

- `cli/lib/code_catalog.py` line 265/267/455/490/732 (5 件)
- `cli/lib/deferred_findings.py` line 371/560 (2 件)
- `cli/lib/effort_classifier.py` line 197 (1 件)
- `cli/lib/helix_db.py` line 1374/1503 (2 件)
- `cli/lib/matrix_advisor.py` line 34/87/98/106 (4 件、scope_type 関連)
- `cli/lib/scrum_trigger.py` line 665 (1 件)
- `cli/lib/session_start_helpers.py` line 20 (1 件)
- `cli/lib/skill_recommender.py` line 304 (1 件)

## 推奨アクション

1. **PLAN-061 W-2/W-3**: 19 件確定削除を Codex SE に並列委譲 (ファイル単位 commit)
2. 削除後 `cli/helix test` で 614 + 1055 + 420 全 PASS 確認
3. tests-only callers 17 件は別 PLAN carry (本体と test 両方の慎重削除要)

## メタデータ

- 監査日: 2026-05-11
- ツール: vulture 2.16 + 自作 triage script (/tmp/dead-code-triage.py)
- スコープ: `cli/lib/` (excluding tests)
- 検出件数: 119 件
- 確定削除候補: 19 件 (16%)
- tests-only callers carry: 17 件 (14%)
- 外部参照あり (削除しない): 44 件 (37%)
- 既知 false positive: 39 件 (33%)
