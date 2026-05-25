---
plan_id: L7-plan-lint-frontmatter-validationplan
title: "L7-plan-lint-frontmatter-validationplan: helix plan lint の frontmatter validation 強化"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-25
revised: 2026-05-25
process_layer: L7
parent_design: HELIX-workflows/helix-process/HELIX-process-L0-L14.md
pairs_test_design: []
dependencies:
  parent: null
  requires: []
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — plan lint frontmatter validation 実装"
  - role: qa
    slot_label: "QA — pytest / py_compile / plan lint / settings 差分検証"
generates:
  - artifact_path: docs/plans/L7/L7-plan-lint-frontmatter-validationplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/plan_lint.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_plan_frontmatter_lint.py
    artifact_type: test
---

## §0 PLAN concept

`helix plan lint` の既存 status assertion lint に加え、V2 PLAN frontmatter の required field 存在確認と enum 検証を同時実行する。既存の legacy PLAN (`PLAN-xxx`) は不破壊を優先し、frontmatter schema lint の対象を V2 PLAN (`L<NN>-<slug>plan`) に限定する。

## §1 背景

- 既存 `cli/lib/plan_lint.py` は `frontmatter.status` と本文断定文の矛盾検出に特化している
- V2 PLAN 起票が `docs/plans/L0-L14/` に移行したため、`kind/layer/drive/status/process_layer` の基本整合を `helix plan lint` でも即時検知したい
- 既存 `helix doctor` と legacy PLAN lint を壊さないため、検証範囲は V2 PLAN に限定する

## §2 scope

1. `cli/lib/plan_lint.py` に `validate_plan_frontmatter(frontmatter)` を追加する
2. validator は required field の存在と enum 値を検証し、`list[dict[str, str]]` を返す
3. optional field (`parent_design`, `dependencies`, `generates`) は型/構造の warning のみ返す
4. `helix plan lint` の通常実行時に frontmatter error があれば exit 1 にする
5. 既存の duplicate lint / status lint / retroactive skip の挙動は維持する
6. `cli/lib/tests/test_plan_frontmatter_lint.py` に pytest 3 件を追加する

scope 外:

- `helix plan lint --v5` (`plan_validator.py`) の仕様変更
- `helix doctor` のチェック追加
- legacy PLAN frontmatter の一括 retrofit

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 件追加 (Red) | missing required / invalid enum / valid case が test 固定される | planned |
| .2 | `plan_lint.py` に frontmatter validator 実装 | V2 PLAN で frontmatter error を検知できる | planned |
| .3 | 回帰検証 + plan lint + settings 差分確認 | py_compile / pytest / plan lint / settings 0 diff が通る | planned |

## §4 受入条件

- `validate_plan_frontmatter({"plan_id": "...", ...})` は missing required field を `level=error` で返す
- `kind/layer/drive/status/process_layer` の enum 不正を `level=error` で返す
- valid な V2 frontmatter は空 list を返す
- legacy `PLAN-xxx` に対する既存 `helix plan lint` の回帰を発生させない
- `helix doctor` の既存挙動を変えない

## §5 検証

- `git status --short`
- `python3 -m py_compile cli/lib/plan_lint.py cli/lib/tests/test_plan_frontmatter_lint.py`
- `python3 -m pytest cli/lib/tests/test_plan_frontmatter_lint.py -q`
- `grep -c 'validate_plan_frontmatter' docs/plans/L7/L7-plan-lint-frontmatter-validationplan.md cli/lib/plan_lint.py cli/lib/tests/test_plan_frontmatter_lint.py`
- `helix plan lint docs/plans/L7/L7-plan-lint-frontmatter-validationplan.md`
- `git diff -- .vscode/settings.json`

## §11 carry

- `plan_validator.py` との enum 定義共通化は別タスク
- optional field の path existence まで fail-close にするかは別検討
