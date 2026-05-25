---
plan_id: L7-vmodel-pair-freeze-stale-applyplan
title: "L7-vmodel-pair-freeze-stale-applyplan: stale PLAN 自動 revised 反映 --apply 連携"
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
  requires:
    - docs/plans/L7/L7-vmodel-pair-freeze-stale-suggestionplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — apply_stale_revisions helper と doctor --apply-stale-revisions 実装"
  - role: qa
    slot_label: "QA — pytest / bats / plan lint / settings 差分検証"
generates:
  - artifact_path: docs/plans/L7/L7-vmodel-pair-freeze-stale-applyplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/vmodel_pair_freeze.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_vmodel_pair_freeze.py
    artifact_type: test
  - artifact_path: cli/helix-doctor
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-doctor-pmo.bats
    artifact_type: test
---

## §0 PLAN concept

`suggest_stale_revisions()` の dry-run 提案を正本にしつつ、`apply_stale_revisions()` で stale PLAN の frontmatter `revised` を安全に更新する。`helix doctor --apply-stale-revisions` は dry-run default とし、明示 `--apply` 時のみ実 write を許可する。

## §1 背景

- `L7-vmodel-pair-freeze-stale-suggestionplan` で stale PLAN の候補列挙までは自動化された
- ただし運用では suggestion を見てから手で `revised` を更新しており、carry が残っている
- frontmatter rewrite は他 field を壊さないことが最優先のため、write path を限定した helper 契約で固定する

## §2 scope

1. `cli/lib/vmodel_pair_freeze.py` に `apply_stale_revisions(layer, *, project_root, since_days=30, dry_run=True)` を追加する
2. helper は `suggest_stale_revisions()` の結果を起点にし、dry-run では返却のみ、`dry_run=False` で `revised` を当日 ISO 日付へ更新する
3. frontmatter write は `revised` 行の置換または安全な追記に限定し、他 field を保持する
4. `cli/helix-doctor` に `--apply-stale-revisions` と `--apply` を追加し、default は dry-run、`--apply` 指定時のみ実 write とする
5. pytest 3 件、bats 1 件で helper 契約と CLI dry-run 契約を固定する

scope 外:

- stale suggestion policy 自体の変更
- revised 更新に伴う本文 skeleton 生成
- doctor の fail policy 変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 件 / bats 1 件追加 (Red) | apply helper と doctor dry-run 契約が test で固定される | planned |
| .2 | `apply_stale_revisions()` 実装 + frontmatter rewrite 追加 | dry-run / updated / no-pair の 3 条件が helper で判定できる | planned |
| .3 | doctor `--apply-stale-revisions [--apply]` 実装 + 回帰検証 | pytest 26 件 PASS / bats 10 件 PASS / plan lint PASS / settings 差分 0 | planned |

## §4 受入条件

- `apply_stale_revisions("L4", project_root=..., since_days=30, dry_run=True)` は stale PLAN を返すが file を更新しない
- `apply_stale_revisions(..., dry_run=False)` は `revised` を当日 ISO 日付に更新し、`status: updated` を返す
- pair を持たない layer は空 list を返す
- write 失敗時は `status: skipped` と `reason` を返す
- `helix doctor --vmodel-pair-freeze-since-days 30 --apply-stale-revisions` は exit 0 を維持し、dry-run 候補件数を表示する
- `helix doctor --vmodel-pair-freeze-since-days 30 --apply-stale-revisions --apply` は stale PLAN の `revised` を更新する
- 既存 23 vmodel pytest / 9 doctor-pmo bats / doctor baseline 25/0/105 を破壊しない

## §5 検証

- `python3 -m py_compile cli/lib/vmodel_pair_freeze.py`
- `python3 -m pytest cli/lib/tests/test_vmodel_pair_freeze.py -q`
- `bats cli/tests/test-helix-doctor-pmo.bats`
- `grep -c 'apply_stale_revisions\\|apply-stale-revisions' cli/lib/vmodel_pair_freeze.py cli/helix-doctor cli/tests/test-helix-doctor-pmo.bats`
- `helix plan lint docs/plans/L7/L7-vmodel-pair-freeze-stale-applyplan.md`
- `git diff --stat .claude/settings.json`

## §11 carry

- apply 結果を review queue や handover へ自動転記する連携は別 PLAN
- doctor 出力から対象 PLAN を選択して部分 apply する UI は別 PLAN
