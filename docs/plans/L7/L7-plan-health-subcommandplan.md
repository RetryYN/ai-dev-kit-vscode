---
plan_id: L7-plan-health-subcommandplan
title: "L7-plan-health-subcommandplan: helix plan health subcommand 追加"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-25
revised: 2026-05-25
process_layer: L7
parent_design: HELIX-workflows/HELIX-process-L0-L14.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - docs/plans/L7/L7-plan-lint-frontmatter-validationplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — plan health 実装"
  - role: qa
    slot_label: "QA — pytest / bats / plan lint / settings 差分検証"
generates:
  - artifact_path: docs/plans/L7/L7-plan-health-subcommandplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/plan_health.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_plan_health.py
    artifact_type: test
  - artifact_path: cli/helix-plan
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-plan.bats
    artifact_type: bats
---

## §0 PLAN concept

`helix plan health` を追加し、`docs/plans/` 配下の `*plan.md` を走査して frontmatter 整合性と status / kind の分布を即時確認できるようにする。既存 `helix plan lint` の単一ファイル検査と役割を分け、複数 PLAN の全体健全性を軽量に可視化する。

## §1 背景

- `validate_plan_frontmatter` は単体で使えるようになったが、全 PLAN を横断する集計コマンドがない
- V2 PLAN が `docs/plans/L0-L14/` に散在するため、frontmatter 逸脱の早期発見に一覧性が必要
- `helix doctor` を重くせず、任意実行の health subcommand として切り出したい

## §2 scope

1. `cli/lib/plan_health.py` に `scan_all_plans(plans_root: Path)` を追加する
2. `docs/plans/**/*plan.md` を scan し、`validate_plan_frontmatter` で各 file を検証する
3. `status_distribution` と `kind_distribution` を集計する
4. invalid frontmatter の代表例を `file + errors` で返す
5. `helix plan health [--json] [--plans-root PATH]` を追加する
6. pytest 3 件と bats 1 件で TDD する

scope 外:

- `helix doctor` のチェック拡張
- `helix plan lint` の exit 条件変更
- legacy PLAN の一括 retrofit

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest/bats 追加 (Red) | 3 pytest + 1 bats が health 未実装で失敗する | planned |
| .2 | `plan_health.py` 実装 + `helix plan` 配線 | `helix plan health` が集計結果を返す | planned |
| .3 | 回帰検証 + review + settings 差分確認 | py_compile / pytest / bats / plan lint / review が通る | planned |

## §4 受入条件

- `scan_all_plans(Path("docs/plans"))` が `total / valid_frontmatter / invalid_frontmatter / status_distribution / kind_distribution / invalid_examples` を返す
- `status_distribution` は `draft / in_progress / completed / finalized / other` の固定 bucket を持つ
- invalid frontmatter は `invalid_examples[].errors[]` に field 単位の error を残す
- `helix plan health` は既定で human-readable、`--json` では JSON を返す
- 既存 `helix plan lint` / `helix doctor` の挙動を壊さない

## §5 検証

- `git status --short`
- `python3 -m py_compile cli/lib/plan_health.py cli/lib/tests/test_plan_health.py`
- `python3 -m pytest cli/lib/tests/test_plan_health.py -q`
- `bats cli/tests/test-helix-plan.bats`
- `grep -R -c 'scan_all_plans' cli/helix-plan cli/lib/plan_health.py cli/lib/tests/test_plan_health.py`
- `helix plan health --json`
- `helix plan lint docs/plans/L7/L7-plan-health-subcommandplan.md`
- `git diff -- .vscode/settings.json`

## §11 carry

- `plan_lint.py` と `plan_validator.py` の schema 共通化は別 PLAN
- invalid_examples の件数上限や severity 分離は利用実績を見て別タスク化する
