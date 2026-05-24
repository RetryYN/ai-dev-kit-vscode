---
plan_id: L7-workflow-protocol-layer-integrationplan
title: "L7-workflow-protocol-layer-integrationplan: workflow doc と .md プロトコル層の統合 roadmap"
kind: design
layer: L7
drive: be
status: draft
process_layer: L7
parent_design: HELIX-workflows/HELIX-process-L0-L14.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - HELIX-workflows/helix-process/integration-map.md
    - HELIX-workflows/HELIX-process-L0-L14.md
    - AGENTS.md
    - CLAUDE.md
  blocks: []
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — .md プロトコル層との整合確認"
  - role: tl-advisor
    slot_label: "TL — 参照点移譲と受入条件のレビュー"
generates:
  - artifact_path: docs/plans/L7/L7-workflow-protocol-layer-integrationplan.md
    artifact_type: design_doc
  - artifact_path: .helix/protocol-integration-notes.md
    artifact_type: markdown_doc
---

## §0 PLAN concept

`CLAUDE.md` / `AGENTS.md` / `.claude/CLAUDE.md` から `HELIX-workflows` への直接参照導線を roadmap として起票する。

対象:
- SoT: `HELIX-workflows/HELIX-process-L0-L14.md`
- 目的: プロトコル層で workflow doc が一次参照源として扱われる導線を設計
- スコープ: PLAN 起票のみ（実装は別 session）

## §1 背景

- 2nd-level 導線として `.md` プロトコルがある一方、workflow doc への直接参照が分散していない。
- セッション継続性に必要な「次に読むべき文書」を 4 mode 全体で固定化するため、参照設計を先に整える。
- 本 PLAN は実装対象として `AGENTS.md` / `CLAUDE.md` の更新方針を定義する。

## §2 scope

1. `.md プロトコル層` の主要エントリから `HELIX-workflows` 参照追加を想定した変更点を列挙。
2. `integration-map.md` の未統合行へ `PLAN-roadmap-起票 (2026-05-25)` を追記。
3. protocol 側の受入条件（変更理由、参照優先順位、更新トリガ）を明文化。
4. 将来更新用に notes ファイル案を `generates` に保持。

scope 外:
- 各 `.md` ファイルの本文詳細改稿
- CI / hook 自体の実装

## §3 工程表 (placeholder)

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | 参照接続対象の優先度整理 | 4 mode を跨いだ direct reference 方針を決定 | planned |
| .2 | 変更トランジションルール作成 | 参照追加時のレビュー基準を明記 | planned |
| .3 | 実装 session 用 handoff 資産作成 | 実装開始前に carry 条件が確定 | planned |

## §11 carry

- carry-1: プロトコル層に workflow 参照が固定化されないと handover 再現性が低下する問題を緩和
- carry-2: `.md` 参照更新ルールを次回実装へ引き継ぐ
- carry-3: 実装前提文書として継続的に監査可能にする

