---
plan_id: L7-cli-helix-retrofit-implplan
doc_id: L7-cli-helix-retrofit-impl-design
title: "L7 helix retrofit CLI 実装設計"
status: draft
artifact_role: "① 設計 (V-model 4 artifact のうち)"
created: 2026-05-25
revised: 2026-05-25
owner: SE
related_docs:
  - docs/plans/L7/L7-cli-helix-retrofit-implplan.md
  - HELIX-workflows/helix-process/retrofit-workflow.md
  - docs/v2/L7-test-design/L7-cli-helix-retrofit-impl-test-design.md
phases: L7
gates: G6,G7
---

# L7 helix retrofit CLI 実装設計

## §0 概要

本書は `L7-cli-helix-retrofit-implplan` の ① 設計 artifact であり、② 実装コード・③ テスト設計・④ テストコードとは分離して管理する。

- 対象 PLAN: `docs/plans/L7/L7-cli-helix-retrofit-implplan.md`
- 対応 ② 実装コード: `cli/helix-retrofit`, `cli/lib/retrofit_engine.py`
- 対応 ③ テスト設計: `docs/v2/L7-test-design/L7-cli-helix-retrofit-impl-test-design.md`
- 対応 ④ テストコード: `cli/lib/tests/test_retrofit_engine.py`, `cli/lib/tests/bats/helix_retrofit.bats`

本実装の責務は Retrofit mode の state manager を direct invocation で成立させることに限定する。`helix route suggest` との接続は C' scope のため触れない。

## §1 CLI surface

| Subcommand | 入力 | 出力 | 失敗時 |
|---|---|---|---|
| `init` | `--slug`, 任意 `--plan-id`, `--drive`, `--drift-type` | matrix/config/plan の 3 点生成 JSON | duplicate/slug 不正で exit 2 |
| `matrix list` | `--slug` | matrix table | slug 不在で exit 2 |
| `matrix add` | `--slug --from --to --scope [--phase] [--notes]` | 追加 row JSON | 入力不正で exit 2 |
| `matrix update` | `--slug --row --status [--notes]` | 更新 row JSON | row 不在で exit 2 |
| `matrix show --summary` | `--slug` | 完了率サマリ | slug 不在で exit 2 |
| `status` | 任意 `--slug`, `--json` | active retrofit の状態 | active 不在でも exit 0 |
| `done` | `--slug --row [--run-regression]` | 更新後 summary JSON | blocked 行あり exit 2、回帰失敗 exit 3 |
| `plan` | `--slug`, 任意 `--plan-id`, `--drive`, `--drift-type` | draft plan path | duplicate で exit 2 |

## §2 データ設計

### 2.1 retrofit-matrix

正本は `docs/plans/<slug>-retrofit-matrix.md` の YAML frontmatter `rows`。Markdown table は frontmatter から再生成されるビューであり、直接編集しない。

各 row の必須 field:

| Field | 型 | 説明 |
|---|---|---|
| `id` | string | `R001` 形式の一意 ID |
| `from` / `to` | string | 旧状態と目標状態 |
| `scope` | string | 影響範囲 |
| `phase` | string | `L4/L5/L7/L8/L9` など |
| `status` | enum | `todo/in_progress/done/blocked` |
| `done_at` | string or null | `done` 到達時刻 |
| `regression_failed` | bool | `done --run-regression` の失敗痕跡 |
| `notes` | string | 補足 |

### 2.2 config YAML

`cli/config/<slug>-retrofit.yaml` の正本 field:

| Field | 説明 |
|---|---|
| `phases.design_supplement` | L4/L5 追補対象 |
| `phases.regression` | L8/L9 回帰対象 |
| `rollback.strategy/checkpoint` | 手動 rollback の宣言 |
| `parallel_run` | 並行稼働の有無 |
| `regression_scope.pytest/bats/filter` | `done --run-regression` 実行対象 |

## §3 実装方針

1. `cli/helix-retrofit` は `helix-recover` と同じ bash shim とし、Python entrypoint に委譲する。
2. `RetrofitMatrix` は frontmatter parse/render を内包し、保存時に table を必ず再生成する。
3. `RetrofitConfig` は template 作成と差分表示のみを持ち、実行状態は持たない。
4. `KindChecker` は内部 utility として signal 優先・file pattern 補助の最小判定に留める。
5. `done --run-regression` は同期実行のみ。失敗時は row を `in_progress` へ巻き戻す。

## §4 セキュリティ/運用

- `config_drift` の route 連携は scope 外だが、config 更新は常にファイル宣言に限定し auto apply はしない。
- matrix/config/plan の生成先は repo 配下に固定し、path traversal を受けない。
- `status` は blocked 行と plan status mismatch を警告として表示し、fail-close 判断の材料を残す。

## §5 Trace

- ① 本書 → ② 実装: `cli/helix-retrofit`, `cli/lib/retrofit_engine.py`
- ① 本書 → ③ テスト設計: `docs/v2/L7-test-design/L7-cli-helix-retrofit-impl-test-design.md`
- ③ テスト設計 → ④ テストコード: `cli/lib/tests/test_retrofit_engine.py`, `cli/lib/tests/bats/helix_retrofit.bats`
