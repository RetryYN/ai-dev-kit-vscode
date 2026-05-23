---
doc_id: process-L13
title: "L13 デプロイ後検証 + 実環境運用"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L13
pairs_with: null
canonical_source: HELIX-workflows/helix-process/L13-post-deployment-verification.md
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

---

## 正本 (HELIX-workflows) 抽出 — 2026-05-24 V2 完全移行

> 正本: [L13-post-deployment-verification.md](../../../HELIX-workflows/helix-process/L13-post-deployment-verification.md)
> 本 doc は HELIX-workflows に同期。差分は HELIX-workflows を優先。

### 工程の位置づけ (HELIX-workflows 正本)

| 項目 | 内容 |
|---|---|
| 区分 | V字 右腕（運用フェーズ） |
| 入力 | L12 デプロイ |
| 出力 | L14 への入力 |
| 対応する設計 | — |

### この工程の PLAN (HELIX-workflows 正本)

PLAN は機能（ドキュメント）単位で起票し、工程表（作成手順＋進捗）と実装計画を内蔵する。

### `L13-デプロイ後検証plan`
- 本番動作確認
- 初期監視

### `L13-実環境運用plan`
- 運用開始
- 運用手順

> **PLAN が内蔵するもの** (HELIX-workflows 共通):
> - **工程表**: そのドキュメントを完成させる手順 (例: 参考調査 Web 検索 → 既存資料整理 → ドラフト → TL レビュー → 確定) と各手順の進捗
> - **実装計画**: 記載項目をどう埋めるかの計画

