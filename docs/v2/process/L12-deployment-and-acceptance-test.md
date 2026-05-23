---
doc_id: process-L12
title: "L12 デプロイ + 受入テスト + 環境差異巻き取り"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L12
pairs_with: L3
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
