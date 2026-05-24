---
plan_id: L7-workflow-skill-cross-ref-integrationplan
title: "L7-workflow-skill-cross-ref-integrationplan: workflow doc と SKILL.md の双方向参照 roadmap"
kind: design
layer: L7
drive: be
status: draft
process_layer: L7
parent_design: HELIX-workflows/helix-process/integration-map.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - HELIX-workflows/helix-process/integration-map.md
    - HELIX-workflows/helix-process/L7-implementation.md
    - skills/SKILL_MAP.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — cross-reference 設計方針を明文化"
  - role: pmo-sonnet
    slot_label: "PMO — 参照整合とリンクチェックの検証"
generates:
  - artifact_path: docs/plans/L7/L7-workflow-skill-cross-ref-integrationplan.md
    artifact_type: design_doc
  - artifact_path: scripts/sync-helix-workflow-skill-refs.py
    artifact_type: script
---

## §0 PLAN concept

`HELIX-workflows/helix-process/*.md` と `skills/*/SKILL.md` の双方向参照を roadmap 起票として明文化する。

対象:
- SoT: `HELIX-workflows/helix-process/integration-map.md` / `skills/SKILL_MAP.md`
- 目的: workflow doc と skill の参照導線を継続運用可能な形で定義
- スコープ: PLAN 起票のみ（実装は別 session）

## §1 背景

- workflow 文書には独立性が高い一方、skills 側参照が追随しづらく、横断的導線が散在。
- `integration-map` は未統合として残るが、実装前に参照設計を固定した方が実装工数を抑えられる。
- 本 PLAN では cross-reference の対象と生成物、更新フローを定義する。

## §2 scope

1. workflow doc 側（`helix-process/*.md`）の参照先として対応する SKILL を明示。
2. skill 側（`skills/*/SKILL.md`）の導線として workflow doc を紐づけるルールを定義。
3. 将来実装予定として、参照同期スクリプトを生成物に含める。
4. `integration-map.md` の未統合エントリへ PLAN-roadmap-起票注記を追記。

scope 外:
- skill 本体（LLM 操作手順）の内容改変
- 参照同期スクリプトの実作成

## §3 工程表 (placeholder)

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | 対象文書の参照関係を棚卸し | 参照ルール表のドラフト作成 | planned |
| .2 | 双方向リンク仕様（相互参照フォーマット）を確定 | map 追記で 4 エントリ更新準備 | planned |
| .3 | 実装 session 受け渡し事項をまとめる | 実装担当へ引き継ぎ可能 | planned |

## §11 carry

- carry-1: workflow doc と skill 定義の整合を roadmap として管理
- carry-2: 運用可能な cross-ref 生成方針を別セッションに委譲
- carry-3: 実装前に更新対象を最小集合へ固定

