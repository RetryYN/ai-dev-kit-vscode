---
plan_id: L7-handover-stale-checkplan
title: "L7-handover-stale-checkplan: time-based stale check for helix-handover"
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
    slot_label: "SE — stale helper と status 拡張"
  - role: qa
    slot_label: "QA — pytest / py_compile / plan lint 検証"
generates:
  - artifact_path: docs/plans/L7/L7-handover-stale-checkplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/handover.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_handover_stale.py
    artifact_type: test
---

## §0 PLAN concept

`CURRENT.json` の `updated_at` を用いた時間ベースの stale 判定を helper として分離し、`helix handover status` の JSON 出力へ補助情報として追加する。既存の branch/head_sha を含む stale 判定は維持し、追加機能は read-only な status 拡張に限定する。

## §1 背景

- 既存 `stale_check()` は branch/head_sha/updated_at を一括で扱っており、時間ベースの鮮度情報を単独再利用しにくい
- handover 継続判定では「総合 stale」だけでなく、`updated_at` 基準の経過時間を単独で参照したい
- 既存 subcommand は維持し、`status` の payload 拡張だけで用途を満たす

## §2 scope

1. `cli/lib/handover.py` に `check_handover_staleness()` を追加する
2. `CURRENT.json` を優先し、必要時は `CURRENT.md` から timestamp を読む
3. helper は `fresh | stale | no_handover` と `updated_at` / `hours_since_update` を返す
4. `cli/lib/handover.py` の `status` payload に時間ベース stale 情報を追加する
5. pytest 3 件で fresh/stale/no_handover を固定する

scope 外:

- `dump` / `update` / `clear` / `resume` / `escalate` の挙動変更
- branch/head_sha stale policy の変更
- doctor や settings hook への接続

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + stale helper test 3 件追加 (Red) | fresh/stale/no_handover 契約が test で固定される | planned |
| .2 | `handover_stale.py` 実装 + `handover.py` status 接続 | 既存 stale API を壊さず時間ベース情報を追加 | planned |
| .3 | py_compile / pytest / plan lint / settings diff 確認 | 指定自己検証が全件 PASS | planned |

## §4 受入条件

- `check_handover_staleness(project_root=tmp_path)` が `CURRENT.json.updated_at` を読み fresh/stale を返す
- handover ファイル不在時は `status='no_handover'`
- `helix handover status --json` の payload に時間ベース stale 情報が含まれる
- 既存 `stale` / `stale_reasons` の互換性を維持する
- `pytest cli/lib/tests/test_handover_stale.py -q` が 3/3 PASS

## §11 carry

- 時間ベース stale 情報の doctor 統合
- stale threshold の CLI option 化
