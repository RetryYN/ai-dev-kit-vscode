---
plan_id: L7-cli-helix-retrofit-implplan
doc_id: L7-cli-helix-retrofit-impl-test-design
title: "L7 helix retrofit CLI テスト設計"
status: draft
artifact_role: "③ テスト設計 (V-model 4 artifact のうち)"
created: 2026-05-25
revised: 2026-05-25
owner: SE
related_docs:
  - docs/plans/L7/L7-cli-helix-retrofit-implplan.md
  - docs/v2/L7-design/L7-cli-helix-retrofit-impl-design.md
phases: L7
gates: G6,G7
---

# L7 helix retrofit CLI テスト設計

## §0 概要

本書は `L7-cli-helix-retrofit-implplan` の ③ テスト設計 artifact であり、① 設計・② 実装コード・④ テストコードとは分離して管理する。

- 対応 ① 設計 doc: `docs/v2/L7-design/L7-cli-helix-retrofit-impl-design.md`
- 対応 ② 実装コード: `cli/helix-retrofit`, `cli/lib/retrofit_engine.py`
- 対応 ④ テストコード: `cli/lib/tests/test_retrofit_engine.py`, `cli/lib/tests/bats/helix_retrofit.bats`

## §1 単体テスト設計

| Case ID | 観点 | 期待結果 |
|---|---|---|
| `U-001` | `py_compile` | module が構文エラーなく import 可能 |
| `U-002` | `init_retrofit()` | matrix/config/plan を 3 点生成 |
| `U-003` | `RetrofitMatrix.add_row()` | 連番 row を追加し保存後も保持 |
| `U-004` | `RetrofitMatrix.update_row()/summary()` | done_at と completion を正しく更新 |
| `U-005` | `RetrofitConfig.save_template()` | `phases.regression` 等の必須 key が存在 |
| `U-006` | matrix frontmatter/table | frontmatter `rows` を正本として table を再生成 |
| `U-007` | `KindChecker.check()` | signal 優先、file pattern は補助 |
| `U-008` | `status` warning | blocked 行、plan mismatch、design supplement pending を警告 |
| `U-009` | `done --run-regression` rollback | 失敗時に row を `in_progress` に戻し exit 3 |
| `U-010` | slug validation | kebab-case 以外は fail-close |
| `U-011` | `plan` subcommand | PLAN draft 単独生成ができる |

## §2 CLI/Bats テスト設計

| Case ID | 観点 | 期待結果 |
|---|---|---|
| `B-001` | `helix retrofit --help` | usage と subcommand 一覧を表示 |
| `B-002` | `helix help` | `retrofit` が router/help に登録済み |
| `B-003` | `helix retrofit init --slug smoke-test` | 3 ファイルを生成 |
| `B-004` | `matrix list` | table 形式で row を表示 |
| `B-005` | `matrix update --status done` | JSON 出力と保存結果が一致 |
| `B-006` | `status --json` | `completion_pct` と `next_row` を返す |
| `B-007` | `done --row R001` | row 完了で completion 100% |
| `B-008` | blocked 行あり `done` | exit 2 で禁止 |
| `B-009` | `helix commands check` | router/help/docs の同期 PASS |

## §3 Trace

- ③ 本書 → ④ pytest: `cli/lib/tests/test_retrofit_engine.py`
- ③ 本書 → ④ bats: `cli/lib/tests/bats/helix_retrofit.bats`
- ④ pytest → ③ 本書: docstring で `U-*` を参照
- ④ bats → ③ 本書: test 名で `B-*` 相当の観点を固定
