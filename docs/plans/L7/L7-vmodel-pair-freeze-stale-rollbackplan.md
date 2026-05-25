---
plan_id: L7-vmodel-pair-freeze-stale-rollbackplan
title: "L7-vmodel-pair-freeze-stale-rollbackplan: stale PLAN apply rollback / undo"
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
    - docs/plans/L7/L7-vmodel-pair-freeze-stale-applyplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — apply audit log 追加と rollback_stale_revisions helper / doctor rollback 実装"
  - role: qa
    slot_label: "QA — pytest / bats / plan lint / settings 差分検証"
generates:
  - artifact_path: docs/plans/L7/L7-vmodel-pair-freeze-stale-rollbackplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/vmodel_pair_freeze.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_vmodel_pair_freeze.py
    artifact_type: test
  - artifact_path: cli/helix-doctor
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-doctor-pmo.bats
    artifact_type: bats
---

## §0 PLAN concept

`apply_stale_revisions()` の実 write に監査証跡を追加し、最新 audit record を正本として stale revised 更新を undo できる rollback 導線を `helix doctor` に追加する。

## §1 背景

- `L7-vmodel-pair-freeze-stale-applyplan` で stale PLAN の revised apply は自動化済み
- ただし apply の取り消し導線がなく、誤反映時に手戻りが手作業になる
- `revised` は frontmatter の限定更新で戻せるため、apply 時の audit を残せば安全に rollback できる

## §2 scope

1. `cli/lib/vmodel_pair_freeze.py` の `apply_stale_revisions()` に audit log 追記を追加する
2. `.helix/audit/stale-revisions.json` を append-only で運用し、`applied_at` / `layer` / `changes[]` を記録する
3. `rollback_stale_revisions(project_root, dry_run=True)` を追加し、latest audit record を preview / apply できるようにする
4. `cli/helix-doctor` に `--rollback-stale-revisions [--apply]` を追加する
5. pytest 3 件、bats 1 件で rollback 契約を固定する

scope 外:

- audit 履歴の pruning / rotation
- audit record 選択 UI
- rollback 結果の handover / review queue 連携

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + rollback pytest 3 件 / bats 1 件追加 (Red) | rollback helper / doctor dry-run 契約が test で固定される | planned |
| .2 | apply audit / rollback helper 実装 | latest audit の dry-run / write / no_audit が helper で判定できる | planned |
| .3 | doctor `--rollback-stale-revisions [--apply]` 実装 + 回帰検証 | pytest 32 件 PASS / bats 11 件 PASS / plan lint PASS / settings 差分 0 | planned |

## §4 受入条件

- `apply_stale_revisions(..., dry_run=False)` は `.helix/audit/stale-revisions.json` に audit record を append する
- audit record は `applied_at`, `layer`, `changes[{plan_path,before_revised,after_revised}]` を持つ
- `rollback_stale_revisions(project_root=..., dry_run=True)` は `status=dry_run` と rollback 候補を返し file を更新しない
- `rollback_stale_revisions(..., dry_run=False)` は latest audit record を使って `revised` を `before_revised` に戻し `status=rolled_back` を返す
- audit file 不在時は `status=no_audit` を返す
- `helix doctor --rollback-stale-revisions` は exit 0 を維持し、dry-run 候補件数を表示する
- `helix doctor --rollback-stale-revisions --apply` は latest audit record を実 file に反映する
- 既存 29 vmodel pytest / 10 doctor-pmo bats / doctor baseline を破壊しない

## §5 検証

- `python3 -m py_compile cli/lib/vmodel_pair_freeze.py`
- `python3 -m pytest cli/lib/tests/test_vmodel_pair_freeze.py -q`
- `bats cli/tests/test-helix-doctor-pmo.bats`
- `grep -c 'rollback_stale_revisions\\|rollback-stale-revisions' cli/lib/vmodel_pair_freeze.py cli/helix-doctor cli/tests/test-helix-doctor-pmo.bats`
- `helix plan lint docs/plans/L7/L7-vmodel-pair-freeze-stale-rollbackplan.md`
- `git diff --stat .claude/settings.json`

## §11 carry

- latest 以外の audit record を指定して rollback する導線は別 PLAN
- apply / rollback を 1 transaction として束ねる複数 layer 一括 undo は別 PLAN
