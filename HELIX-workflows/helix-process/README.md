---
doc_id: workflows-index
title: "HELIX ワークフロー索引"
status: draft
created: 2026-05-24
owner: PM
---

# HELIX ワークフロー索引

HELIX のワークフローは、中核の Forward（Vモデル L0–L14）と、入口に応じた5つのモード、FE/UX 工程の2つの専門ワークフローで構成される。**すべてのモードは最終的に Forward のドキュメント体系（L0–L14）へ収束・昇華する。**

## 1. Forward HELIX（Vモデル L0–L14）

中核。新規開発を L0–L14 の工程で進める。正本は [HELIX-process-L0-L14.md](HELIX-process-L0-L14.md)。

| 区分 | 工程ファイル |
|---|---|
| 起点 | L0-concept |
| 左腕（設計＋テスト設計ペア凍結） | L1-requirements / L2-ui-design / L3-requirements-definition / L4-basic-design / L5-detailed-design / L6-functional-design |
| 谷（実装） | L7-implementation |
| 右腕（検証・運用） | L8-integration-test / L9-system-test / L10-ux-refinement / L11-final-review / L12-deployment / L13-post-deployment-verification / L14-operation-verification |

## 2. 入口モード（5）

要件・状況の入口に応じて選び、最終的に Forward へ昇華する。

| モード | ファイル | 入口 | Forward への昇華 |
|---|---|---|---|
| Scrum | scrum-workflow.md | 作るものは明確、要件をユーザーと合わせたい | 完成機能を Reverse fullback で文書化 → L0–L14 |
| Discovery | discovery-workflow.md | 計画上の不明点・実現性が未確定（Reverse と組み合わせ可） | confirmed → L1/L3/L4–L6 へ昇格 |
| Reverse | reverse-workflow.md | 既存コード・設計資産を逆引きしたい | R4 routing → L1/L3/L4/L7/L8–L11 |
| Incident | incident-workflow.md | 本番稼働中に障害が発生した | 暫定収束後、恒久対策を L1/L3/L4–L6、postmortem を L14 |
| Add-feature | add-feature-workflow.md | 既存システムに新機能を追加したい | add-design / add-impl を L4–L7 に追補 → L0–L14 |

## 3. 工程専門ワークフロー（FE / UX、2）

FE/UX 弱点（FE detector が定義先行・未実装）を補う、特定工程の専門化。

| ワークフロー | ファイル | 対応工程 | 補強する FE detector |
|---|---|---|---|
| 画面設計（UI / ワイヤーフレーム） | screen-design-workflow.md | L2 画面設計 | state-transition-drift / mock-promotion |
| フロントデザイン（UX / ビジュアル） | frontend-design-workflow.md | L10 UX 磨き上げ | design-token-drift / a11y-regression / visual-regression |

## ファイル構成

```
HELIX-process-L0-L14.md            # Forward 全体インデックス（正本）
helix-process/
├── L0-concept.md … L14-operation-verification.md   # Forward 工程別（15）
├── scrum-workflow.md              # 入口モード：反復開発
├── discovery-workflow.md          # 入口モード：仮説検証（× Reverse）
├── reverse-workflow.md            # 入口モード：逆引き
├── incident-workflow.md           # 入口モード：緊急対応
├── add-feature-workflow.md        # 入口モード：機能追加
├── screen-design-workflow.md      # 工程専門：L2 画面設計
├── frontend-design-workflow.md    # 工程専門：L10 フロントデザイン
└── README.md                      # 本索引
```

## 設計思想

多様な入口（新規 / 反復 / 探索 / 逆引き / 緊急 / 追加）から始めても、最終的に Forward（Vモデル）の単一ドキュメント体系へ収束する。これにより、入口の柔軟さ（アジャイル・探索・緊急対応）と、Vモデルの厳格さ（双方向 trace・ゲート・トレーサビリティ）を両立する。
