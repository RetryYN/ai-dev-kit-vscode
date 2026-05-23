---
plan_id: L12-デプロイplan
title: "L12-デプロイplan: <タイトル placeholder>"
kind: deployment
layer: L12
drive: be              # be|fullstack
status: draft
created: 2026-MM-DD
owner: PM
process_layer: L12             # ★必須: 工程番号 (HELIX-model 正本)
parent_process: HELIX-model/L12-deployment.md   # ★必須: 工程定義 doc
# parent_design: <L7 のみ必須、本工程は不要>
pairs_test_design: []  # 本工程は不要 (L7 のみ V-model trace 必須)
is_reference: false        # V2 製本対象 = false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
generates:
  - artifact_path: docs/v2/L12-<feature>/<feature>.md
    artifact_type: design_doc
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - HELIX-model/L12-deployment.md
  - docs/v2/process/L12-deployment-and-acceptance-test.md
---

## §0 PLAN concept

> **工程**: L12 (L12↔L3 pair freeze)
> **正本**: HELIX-model/L12-deployment.md
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

### この工程で起票する PLAN 群 (HELIX-model 正本)

- `L12-デプロイplan`: デプロイ
- `L12-受入テストplan`: 受入テスト
- `L12-環境差異plan`: 環境差異

### 各 PLAN の記載項目

詳細は [HELIX-model/L12-deployment.md](../../../../HELIX-model/L12-deployment.md) §この工程の PLAN を参照。

## §3 成果物

- **製本対象 doc**: `docs/v2/L12-<area>/<feature>.md` (本 PLAN が完成させる正本)
- **HELIX-model 正本**: [HELIX-model/L12-deployment.md](../../../../HELIX-model/L12-deployment.md)
- **ペア凍結**: L12↔L3 pair freeze

## §4 受入条件 / DoD

- [ ] §1 工程表の Step 1-6 すべて完了
- [ ] §2 実装計画の全 PLAN 起票 + 製本 doc 完成
- [ ] TL レビュー pass
- [ ] V-model ペア工程 (L3) との対応確認 (該当する場合)

## §5 関連 PLAN / ADR / docs

- HELIX-model: HELIX-model/L12-deployment.md
- 工程 doc: docs/v2/process/L12-deployment-and-acceptance-test.md
