---
plan_id: PLAN-NNN-design-slug
title: "PLAN-NNN: (設計タイトル placeholder)"
kind: design
layer: L2
drive: be
status: draft
created: 2026-MM-DD
owner: PM
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: tl-advisor
    slot_label: "TL — 設計判断・adversarial check"
  - role: pmo-sonnet
    slot_label: "PMO — ドキュメントチェック・整合確認"
generates:
  - artifact_path: docs/design/<design-doc>.md
    artifact_type: design_doc
  - artifact_path: docs/adr/ADR-NNN-<slug>.md
    artifact_type: adr_snapshot
dependencies:
  parent: PLAN-091
  requires: []
  blocks: []
related_adr:
  - ADR-NNN-related
related_docs:
  - docs/plans/PLAN-NNN-parent.md
---

## §0 PLAN
PLAN-091 のデザイン系実行準備として、design kind の PLAN を起票し、V-model 4 artifact の ① 設計 / ③ テスト設計への接続点を明示する。

## §1 目的
設計判断に必要な前提情報を揃え、PLAN 起票前に合意形成を前提とした実装可否条件（設計、ADR、回帰観点）を定義する。

## §2 背景
- PLAN-091 §8 の plan embed 設計に従い、kind 固有テンプレートの差分を一元化する。
- 旧運用テンプレートでは kind による Step 期待値が不明瞭であり、運用自動化との整合を強化する必要がある。

## §3 実装計画
### Step 1: Web 検索 3 query（PLAN-087 ガードレール）
- Query A: `PLAN-087 ADR-021 Web 検索ガードレール 実装計画の先行調査`
- Query B: `V5 framework PLAN-091 plan embed design kind template`
- Query C: `設計 PLAN 4 artifact 双方向 trace 参照方式`

### Step 2: tl-advisor adversarial
- `helix codex --role tl-advisor --task "PLAN-091 design kind のステップ構成と ADR 連携を adversarial review"` により反証観点を取得し、重大な欠落がないか確認。

### Step 3: ADR snapshot 起票判断
- Step 1/2 の結果をもとに ADR 参照先（既存 / 新規）を決定。
- 重要設計判断が発生する場合は ADR 追記 or ADR snapshot 作成を判断。

### Step 4: PLAN 起票
- 本テンプレートをベースに 11 kind テンプレートを起票し、依存関係・ドライバ・受入条件を明文化。
- `frontmatter`、§0〜§5、関連 PLAN/ADR をテンプレート差分として統一。

### Step 5: 双方向 trace 確立
- 該当 design plan とテスト設計（`test-design`）間のリファレンスを双方向で明記。
- 既存 PLAN / ADR / docs へ `対象: PLAN-091` を追記し、戻し参照が可能な状態を確認。

## §4 受入条件 / DoD
- plan_id: PLAN-NNN-... が一意で、`kind: design` が一致。
- Step 1〜5 を順序どおり埋めた内容が `cli/templates/plan/design/template.md` に反映。
- 受入: 設計起票時点で ADR 参照の有無が明示されていること。

## §5 関連 PLAN / ADR / docs
- PLAN: PLAN-091
- ADR: ADR-021（Web 検索ガードレール）
- docs: `helix/HELIX_CORE.md`, `docs/commands/index.md`, `skills/SKILL_MAP.md`, `cli/ROLE_MAP.md`
