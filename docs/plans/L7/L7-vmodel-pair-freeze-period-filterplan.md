---
plan_id: L7-vmodel-pair-freeze-period-filterplan
title: "L7-vmodel-pair-freeze-period-filterplan: vmodel pair freeze の期間別 filter"
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
    - docs/plans/L7/L7-vmodel-pair-freeze-status-breakdownplan.md
    - docs/plans/L7/L7-vmodel-pair-freeze-critical-logic-extplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — revised date based period filter 実装"
  - role: qa
    slot_label: "QA — pytest / bats / doctor / plan lint 検証"
generates:
  - artifact_path: docs/plans/L7/L7-vmodel-pair-freeze-period-filterplan.md
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

`check_pair_freeze()` に `since_days` を追加し、`helix doctor --vmodel-pair-freeze-since-days N` で最近 revised された pair PLAN のみを集計できるようにする。既存の default / strict / active-only 契約は維持し、期間 filter はそれらと直交に組み合わせる。

## §1 背景

- 全 pair PLAN を集計すると、古い completed / superseded PLAN も含まれて運用判断が鈍る
- active-only は status 起点の絞り込みだが、「最近更新された作業だけ見たい」というニーズは別軸
- `revised` を主、`created` を次、frontmatter 不在時は file mtime を fallback にすれば、既存 PLAN 体系でも段階導入できる

## §2 scope

1. `check_pair_freeze(layer, *, project_root, active_only=False, since_days=None)` を追加する
2. date source は `revised` → `created` → file mtime fallback の順で解決する
3. 返却 dict に `since_days` field を追加する
4. `helix doctor --vmodel-pair-freeze-since-days N` を追加する
5. doctor 出力に `(since Nd)` marker を追加する
6. pytest 3 件、bats 1 件を追加する

scope 外:

- stale PLAN detection (`since_days` 超過の列挙)
- strict severity policy の変更
- pair PLAN の status policy 追加

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 件 + bats 1 件追加 (Red) | 新規 test が fail-first を示す | planned |
| .2 | `vmodel_pair_freeze.py` に since_days filter と日付解決 helper 実装 | 既存 default 挙動維持 + result に `since_days` を返す | planned |
| .3 | `helix-doctor` flag/marker 実装 + 回帰検証 | pytest 17 件以上 PASS / bats 7 件以上 PASS / doctor marker 確認 | planned |

## §4 受入条件

- `since_days=None` では既存挙動を維持する
- `since_days=30` では 30 日以内に revised された pair PLAN のみ集計する
- `revised` 不在時は `created` を使い、両方なければ file mtime を使う
- `check_pair_freeze()` の返却 dict に `since_days` field が含まれる
- `helix doctor --vmodel-pair-freeze-since-days 30` は exit 0 を維持し、`(since 30d)` marker を表示する
- `--strict-vmodel-pair-freeze` / `--vmodel-pair-freeze-active-only` と組み合わせても既存契約を壊さない

## §11 carry

- stale PLAN detection (`since_days` 超過分の警告 / 別表示) は別 PLAN で扱う
