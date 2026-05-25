---
plan_id: L7-vmodel-pair-freeze-patch-applyplan
title: "L7-vmodel-pair-freeze-patch-applyplan: stale patch を git apply する doctor flag 追加"
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
    - docs/plans/L7/L7-vmodel-pair-freeze-skeleton-patchplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — apply_stale_patches helper と doctor flag 実装"
  - role: qa
    slot_label: "QA — pytest / bats / plan lint / settings 差分検証"
generates:
  - artifact_path: docs/plans/L7/L7-vmodel-pair-freeze-patch-applyplan.md
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

`generate_stale_patch()` が返す unified diff を dry-run 表示または実 `git apply` に流す `apply_stale_patches()` を追加し、`helix doctor --apply-patches [--apply]` から利用できるようにする。既存の frontmatter rewrite 系 `--apply-stale-revisions` は温存し、patch apply 系は別 flag で分離する。

## §1 背景

- `L7-vmodel-pair-freeze-skeleton-patchplan` で stale PLAN 用の unified diff 生成までは固定済み
- carry として残っていた「patch を review だけでなく apply 可能にする」経路を doctor に繋ぐ必要がある
- `git apply` を経由すれば markdown 本文を含む patch 形式をそのまま適用でき、frontmatter rewrite helper とは責務を分離できる

## §2 scope

1. `cli/lib/vmodel_pair_freeze.py` に `apply_stale_patches(layer, *, project_root, since_days=30, dry_run=True)` を追加する
2. helper は `generate_stale_patch()` を呼び、patch なしなら `status=no_patches` を返す
3. dry-run は patch 内容を返すだけに留め、実 file は変更しない
4. `dry_run=False` では patch ごとに一時 file を作り、`git apply --unidiff-zero --allow-empty` を `cwd=project_root` で実行する
5. `cli/helix-doctor` に `--apply-patches` flag を追加し、`--apply` がない場合は dry-run 表示、ある場合だけ実 apply を行う
6. pytest 3 件と bats 1 件で dry-run / no-patches / apply error / doctor 表示契約を固定する

scope 外:

- rollback 機能の追加
- audit log 形式の変更
- `--apply-stale-revisions` の廃止や rename

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 件 / bats 1 件追加 (Red) | patch apply 契約と doctor flag 契約が test で固定される | planned |
| .2 | `apply_stale_patches()` 実装 | dry-run / no-patches / failed を helper で返せる | planned |
| .3 | doctor `--apply-patches` 接続 + 回帰検証 | pytest 35 件以上 PASS / bats 12 件以上 PASS / plan lint PASS | planned |

## §4 受入条件

- `apply_stale_patches("L4", project_root=..., since_days=30, dry_run=True)` は `status=dry_run` と patch list を返し、実 file を変更しない
- patch が 0 件なら `status=no_patches`、`patches=[]`、`errors=[]`
- `dry_run=False` は patch ごとに `git apply --unidiff-zero --allow-empty` を call し、失敗時は `status=failed` と `errors` を返す
- `helix doctor --vmodel-pair-freeze-since-days 30 --apply-patches` は dry-run 行を表示する
- 既存 32 vmodel pytest と 11 doctor-pmo bats を破壊しない

## §5 検証

- `python3 -m py_compile cli/lib/vmodel_pair_freeze.py`
- `python3 -m pytest cli/lib/tests/test_vmodel_pair_freeze.py -q`
- `bats cli/tests/test-helix-doctor-pmo.bats`
- `grep -c 'apply_stale_patches\\|apply-patches' cli/lib/vmodel_pair_freeze.py cli/helix-doctor cli/lib/tests/test_vmodel_pair_freeze.py cli/tests/test-helix-doctor-pmo.bats`
- `helix plan lint docs/plans/L7/L7-vmodel-pair-freeze-patch-applyplan.md`
- `git diff --stat .claude/settings.json`

## §11 carry

- patch apply の詳細結果を JSON 出力へ載せる改善は別 PLAN
- rollback を patch basis に統一する移行判断は別 PLAN
