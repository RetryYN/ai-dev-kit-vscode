# Dead Code Candidates Audit (2026-05-11)

## 概要

PLAN-058 W-3 の dead code 検出結果。`vulture` (Python static analyzer) で `cli/lib/` を min-confidence 60 で scan、119 件の候補を抽出。

**注意**: HELIX は動的 dispatch (auto-discover / dynamic import / CLI hook) を多用するため、vulture の検出には false positive が多い。実削除前に grep + 動作検証が必要。

## 検出統計

| 信頼度 | 件数 | 備考 |
|---|---|---|
| 90% (unused import) | 16 件 | すべて `cli/lib/builders/cli.py` の `_auto_discover_builders` 経由動的 import → **false positive、削除不可** |
| 60% (unused function/class/method) | 100+ 件 | 動的呼び出し / CLI hook 経由 / test fixture を疑う必要あり |

## 検出ファイル別カテゴリ

### Category 1: false positive 確定 (削除しない)
- `cli/lib/builders/cli.py` line 13-33: `_auto_discover_builders` で必要な module import
- `*.row_factory` 系: SQLite cursor 設定属性、vulture が静的検出できない

### Category 2: 要精査 (PLAN-061 candidate)
以下は呼び出し元 0 件の可能性、grep で再確認後に削除候補化:

#### audit 系
- `audit_a1.py` line 72: `class A1ImportEngine` (PLAN-002 v3-v5 関連、廃止確認要)
- `audit_inventory.py` line 46/85: `generate_decisions_draft` / `dump_decisions_yaml`

#### deferred_findings 系
- `deferred_findings.py` line 297-560: 8 関数 (add/update/list/carry/sync/adjust/compute)
- 用途: 当初設計の P0/P1/P2/P3 carry 管理、CLI からの呼び出し有無確認要

#### code_catalog 系
- `code_catalog.py` line 263-269: 7 変数 (is_non_indexable_path 等)
- `code_catalog.py` line 455/490/727/728/732/912: 関数 6 件
- PLAN-011/012/013 で実装、現行 CLI からの参照経路確認要

#### learning_engine / global_store 系
- `learning_engine.py`: row_factory 5 件 (SQLite 関連、削除不可)
- `global_store.py` line 227/478/509/542/581: 5 関数 (sync/search/get/promote)
- PLAN-002/003 関連、現行 helix recipe コマンドからの参照要

#### codex_post_validation / concurrent_lock / context_guard / effort_classifier 系
- `codex_post_validation.py` line 78: `count_actual_diff_lines`
- `concurrent_lock.py` line 175/199: `inspect_stale_locks` / `cleanup_stale`
- `context_guard.py` line 29: `REQUIRED_CONTEXT_FILES`
- `effort_classifier.py` line 185/197: `call_classifier` / `effort_classify`

#### entry_helper / helix_db / matrix_advisor / migrate / model_registry / plan_schema
- 各々 1-5 関数の検出、grep で呼び出し元確認後判断

### Category 3: llm_guard / merge_settings 系の private helper
- `llm_guard.py` line 261/3462/3466: 3 関数 (`_without_quoted_strings` / `has_raw_codex_exec` / `has_raw_claude_cli`)
- `merge_settings.py` line 124: `_has_helix_hook`

## 推奨アクション

1. **PLAN-058 内では削除しない** (false positive risk が高い)
2. **PLAN-061 として後続起票**: vulture 候補を 1 件ずつ grep + dynamic call 確認 + テスト実行で精査、安全な dead code のみ削除
3. PLAN-061 推定 size: L (60% 候補 100+ 件、1 件あたり 5-15 分の精査)

## 詳細レポート

`vulture cli/lib/ --min-confidence 60 --exclude tests` の出力を `/tmp/vulture-cli-lib.txt` に保管 (119 行)。

```bash
python3 -m vulture cli/lib/ --min-confidence 60 --exclude "tests"
```

## メタデータ

- 監査日: 2026-05-11
- ツール: vulture 2.16
- スコープ: `cli/lib/` (excluding tests)
- 検出件数: 119 件 (90%: 16, 60%: 103)
- 確定削除可能: 0 件 (vulture 90% はすべて false positive)
- 要精査: ~80 件 (動的 dispatch / CLI hook / test fixture 疑いを除外後)
