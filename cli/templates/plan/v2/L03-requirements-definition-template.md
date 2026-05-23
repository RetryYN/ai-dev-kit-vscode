---
plan_id: L3-業務要件plan
title: "L3-業務要件plan: <タイトル placeholder>"
kind: requirements
layer: L3
drive: be              # be|fullstack
status: draft
created: 2026-MM-DD
owner: PM
process_layer: L3             # ★必須: 工程番号 (HELIX-workflows 正本)
parent_process: HELIX-workflows/helix-process/L3-requirements-definition.md   # ★必須: 工程定義 doc
# parent_design: <L7 のみ必須、本工程は不要>
pairs_test_design: []  # 本工程は不要 (L7 のみ V-model trace 必須)
is_reference: false        # V2 製本対象 = false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
generates:
  - artifact_path: docs/v2/L3-<feature>/<feature>.md
    artifact_type: design_doc
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/L3-requirements-definition.md
  - docs/v2/process/L03-requirements-definition-and-acceptance-test-design.md
---

## §0 PLAN concept

> **工程**: L3 (L3↔L12 pair freeze)
> **正本**: HELIX-workflows/helix-process/L3-requirements-definition.md
> **本 PLAN の対象**: <この PLAN が進める対象を書く>

## §1 工程表 (作業手順 + 進捗)

PLAN は **工程表 (作業手順 + 進捗) + 実装計画** の 2 要素を内蔵し、作業中断時に再開可能にする。

| Step | 作業内容 | 進捗 |
|---|---|---|
| 1 | 参考調査 (Web 検索 / 既存資料整理 / GitHub 探索) | □ pending |
| 2 | ヒアリング / 既存仕様確認 | □ pending |
| 3 | ドラフト起草 (本 PLAN 配下の対象 doc) | □ pending |
| 4 | TL レビュー (helix codex --role tl) | □ pending |
| 5 | 修正反映 | □ pending |
| 6 | 確定 → 次工程へ引き渡し | □ pending |

## §2 実装計画 (記載項目をどう埋めるか)

### この工程で起票する PLAN 群 (HELIX-workflows 正本)

- `L3-業務要件plan`: 業務要件
- `L3-機能要件plan`: 機能要件
- `L3-非機能要件plan`: 非機能要件

### 各 PLAN の記載項目

詳細は [HELIX-workflows/helix-process/L3-requirements-definition.md](../../../../HELIX-workflows/helix-process/L3-requirements-definition.md) §この工程の PLAN を参照。

## §3 成果物

- **製本対象 doc**: `docs/v2/L3-<area>/<feature>.md` (本 PLAN が完成させる正本)
- **HELIX-workflows 正本**: [HELIX-workflows/helix-process/L3-requirements-definition.md](../../../../HELIX-workflows/helix-process/L3-requirements-definition.md)
- **ペア凍結**: L3↔L12 pair freeze

## §4 受入条件 / DoD

- [ ] §1 工程表の Step 1-6 すべて完了
- [ ] §2 実装計画の全 PLAN 起票 + 製本 doc 完成
- [ ] TL レビュー pass
- [ ] V-model ペア工程 (L12) との対応確認 (該当する場合)

## §5 関連 PLAN / ADR / docs

- HELIX-workflows: HELIX-workflows/helix-process/L3-requirements-definition.md
- 工程 doc: docs/v2/process/L03-requirements-definition-and-acceptance-test-design.md
