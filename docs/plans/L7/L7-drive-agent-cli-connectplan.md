---
plan_id: L7-drive-agent-cli-connectplan
title: "L7-drive-agent-cli-connectplan: two-stage-agent-design Stage2 の CLI 起動 roadmap"
kind: design
layer: L7
drive: fullstack
status: draft
process_layer: L7
parent_design: HELIX-workflows/helix-process/two-stage-agent-design.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - HELIX-workflows/helix-process/integration-map.md
    - HELIX-workflows/helix-process/HELIX-process-L0-L14.md
  blocks: []
agent_slots:
  - role: tl-advisor
    slot_label: "TL — drive=agent CLI 連携仕様の最終整備"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN 構造と SoT 整合性のチェック"
generates:
  - artifact_path: docs/plans/L7/L7-drive-agent-cli-connectplan.md
    artifact_type: design_doc
  - artifact_path: cli/helix-agent
    artifact_type: markdown_doc
---

## §0 PLAN concept

HELIX Workflows two-stage-agent-design の Stage 2（agent）を helix CLI から起動可能にする構成を roadmap として起票する。

対象:
- SoT: `HELIX-workflows/helix-process/two-stage-agent-design.md`
- 目的: `helix agent` 系の起動経路を将来実装可能な状態で定義する
- スコープ: PLAN 起票のみ（実装は別 session）

## §1 背景

- V2 で既存 9 mode CLI は完了しているが、`drive=agent` の orchestration は未接続。
- two-stage-agent-design は文書として存在する一方、helix CLI からの直接起動テンプレート・運用ルートが未確定。
- 本 PLAN は実装に着手しないため、現時点では起票ルート・依存・検証方針を固める。

## §2 scope

1. `helix agent` 想定の PLAN を 1 件起票する（本 PLAN）。
2. `PLAN` frontmatter で SoT、依存、生成物を明示し、plan lint 受け可能な形式で定義。
3. 既存 `integration-map.md` の未統合エントリに本 roadmap を参照する注記を追加する。
4. 実装対象の code/artifact（`cli/helix-agent`）は生成予定として `generates` に残す。

scope 外:
- `helix agent` の CLI 実装
- 二段設計の内部ロジック（実行時状態遷移）の改修

## §3 工程表 (placeholder)

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | SoT/依存再確認と draft 起票 | frontmatter parse が PASS、plan lint 対象として登録 | planned |
| .2 | generate 設計 (doc + skeleton) の整合定義 | 追加の外部依存なし | planned |
| .3 | 実装移行時の受入条件洗い出し | 次 session 向け acceptance が明文化 | planned |

## §11 carry

- carry-1: `drive=agent` の未統合状態をPLAN roadmap化
- carry-2: 二段設計 Stage2 接続の CLI 起動文脈を別 PLAN で実装化
- carry-3: 本PLAN完了時点では実装は未着手（roadmap 生成のみ）

