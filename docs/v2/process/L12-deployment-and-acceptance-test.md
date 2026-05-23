---
doc_id: process-L12
title: "L12 デプロイ + 受入テスト + 環境差異巻き取り"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L12
pairs_with: L3
canonical_source: HELIX-workflows/helix-process/L12-deployment.md
---

# L12 デプロイ + 受入テスト + 環境差異巻き取り

## 入力

- L3 要件 + L12 受入テスト設計 (L3 でペア凍結済)
- L11 総合レビュー通過物
- skill: `workflow/deploy` / `workflow/observability-sre` / `common/infrastructure` / `automation/init-setup`

## 進め方

### Step 1: 環境差異の事前確認 (staging / production)
- dev / staging / prod の環境変数 / シークレット / DB schema / 外部 API endpoint 差異を確認

### Step 2: staging デプロイ + 受入テスト
- L3 でペア凍結された **受入テスト** を staging で実施
- AC ごとに PO 判定

### Step 3: production デプロイ + 受入テスト
- staging 結果問題なしで本番デプロイ
- 本番受入テスト (smoke / canary)

### Step 4: 環境差異巻き取り
- 環境固有の差異 (例: タイムゾーン / 文字コード / 性能) を本工程内で解消
- L4 基本設計 / L5 詳細設計に差し戻すべき差異は該当工程に carry

### Step 5: G12 デプロイ通過 + L8 受入承認

## 成果物

- **デプロイ記録**: `docs/v2/L12-deploy/<area>-deploy-log.md`
- **受入テスト結果**: `docs/v2/L12-test-results/<area>-acceptance-test-result.md`
- **環境差異記録**: `docs/v2/L12-deploy/<area>-env-diff.md`

## ペア凍結相手 (上流対応)

L3 要件定義 (L3 でペア凍結された受入テストを本工程で実施)

## ゲート

- **G12 デプロイ + 受入ゲート**: PM + PO 判定、環境差異巻き取り済 + 受入テスト全 PASS

## 関連 skill

- `workflow/deploy`
- `workflow/observability-sre`
- `common/infrastructure`
- `automation/init-setup`
- `common/security` (本番投入セキュリティ④)

## アンチパターン

- ❌ staging skip して直接 production デプロイ
- ❌ 環境差異の事前確認 skip (本番事故リスク)
- ❌ L3 でペア凍結されていない受入テストを本工程で起こす (V-model 違反、L3 差し戻し)
- ❌ PLAN 起票 (受入は doc + テスト結果が成果物)

---

## 正本 (HELIX-workflows) 抽出 — 2026-05-24 V2 完全移行

> 正本: [L12-deployment.md](../../../HELIX-workflows/helix-process/L12-deployment.md)
> 本 doc は HELIX-workflows に同期。差分は HELIX-workflows を優先。

### 工程の位置づけ (HELIX-workflows 正本)

| 項目 | 内容 |
|---|---|
| 区分 | V字 右腕（検証フェーズ） |
| 入力 | L11・L3 受け入れテスト設計 |
| 出力 | L13 への入力 |
| 対応する設計 | L3 要件定義 / 受け入れテスト設計 |

### この工程の PLAN (HELIX-workflows 正本)

PLAN は機能（ドキュメント）単位で起票し、工程表（作成手順＋進捗）と実装計画を内蔵する。

### `L12-デプロイplan`
- デプロイ手順
- リリース計画

### `L12-受入テストplan`
- 受入基準での検証

### `L12-環境差異plan`
- 本番環境との差異解消

> **PLAN が内蔵するもの** (HELIX-workflows 共通):
> - **工程表**: そのドキュメントを完成させる手順 (例: 参考調査 Web 検索 → 既存資料整理 → ドラフト → TL レビュー → 確定) と各手順の進捗
> - **実装計画**: 記載項目をどう埋めるかの計画

