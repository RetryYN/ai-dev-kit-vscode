---
doc_id: process-L13
title: "L13 デプロイ後検証 + 実環境運用"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L13
pairs_with: null
---

# L13 デプロイ後検証 + 実環境運用

## 入力

- L12 デプロイ完遂物
- skill: `workflow/observability-sre` / `workflow/incident` / `automation/observability`

## 進め方

### Step 1: smoke / canary 監視
- デプロイ直後の smoke test + canary metric 監視
- SLO / SLI / error rate / 外部依存 / latency を観測

### Step 2: 実環境運用開始
- 本番運用 watch (24-48h)
- 監視 dashboard / alert / on-call 体制が機能するか確認

### Step 3: 初期インシデント対応
- インシデント発生時の rollback / hotfix フロー実行
- postmortem 記録

### Step 4: G13 安定性ゲート通過

## 成果物

- **smoke / canary 結果**: `docs/v2/L13-monitoring/<area>-canary-result.md`
- **運用 watch 記録**: `docs/v2/L13-monitoring/<area>-watch-log.md`
- **初期 postmortem**: `docs/v2/L13-incidents/<incident>.md` (発生時のみ)

## ペア凍結相手

なし

## ゲート

- **G13 安定性ゲート**: 自動 + PM 判定、SLO 維持 + 重大インシデント 0

## 関連 skill

- `workflow/observability-sre`
- `workflow/incident`
- `workflow/postmortem`
- `automation/observability`

## アンチパターン

- ❌ smoke / canary なしで直接全 traffic 切替
- ❌ alert / on-call 体制未確認で運用開始
- ❌ PLAN 起票
