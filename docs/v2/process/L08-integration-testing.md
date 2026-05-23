---
doc_id: process-L08
title: "L8 結合テスト + 依存関係解消"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L8
pairs_with: L5
canonical_source: HELIX-workflows/helix-process/L8-integration-test.md
---

# L8 結合テスト + 依存関係解消

## 入力

- L5 詳細設計 (必須)
- L8 結合テスト設計 doc (L5 でペア凍結済、`docs/v2/L8-test-design/`)
- L7 実装スプリント完遂物 (コード + 単体テスト PASS)
- skill: `common/testing` / `workflow/verification` / `agent-skills/browser-testing-with-devtools`

## 進め方

### Step 1: 結合テスト実施
- L8 結合テスト設計 (artifact ③) を入力に、結合テストコード (artifact ④) を実行
- モジュール間契約 (D-CONTRACT) が L5 設計通り動くか検証

### Step 2: 依存関係解消
- 外部依存 / 内部依存の解消 (mock / stub / 実環境)
- BE-FE 接続点の state-events 整合確認

### Step 3: 不整合検出時の差し戻し
- L5 詳細設計違反 → L5 工程に差し戻し
- L7 実装違反 → L7 工程に差し戻し
- L8 テスト設計違反 → L5 でペア凍結直し

### Step 4: G8 結合テスト通過判定

## 成果物

- **結合テスト実施結果**: pytest / bats / E2E raw output
- **依存関係解消記録**: `docs/v2/L8-test-results/<feature>-integration-test-result.md`
- **不整合差し戻し記録**: PLAN.md (該当 L7 PLAN) の carry log

## ペア凍結相手 (上流対応)

L5 詳細設計 (L5 でペア凍結済の結合テスト設計を本工程で実施)

## ゲート

- **G8 結合テスト通過ゲート**: TL + PM 判定

## 関連 skill

- `common/testing` (テスト pyramid)
- `workflow/verification` (受入条件 ↔ テスト対応検証)
- `workflow/quality-lv5`
- `agent-skills/browser-testing-with-devtools` (UI 案件)

## アンチパターン

- ❌ L5 でペア凍結されていない結合テスト設計を本工程で起こす (V-model 違反、L5 に差し戻し)
- ❌ PLAN 起票 (L8 は doc + テスト結果が成果物、PLAN は L7 のみ)
- ❌ 依存解消なしで G8 通過 (L9 総合テストで連鎖 fail)

---

## 正本 (HELIX-workflows) 抽出 — 2026-05-24 V2 完全移行

> 正本: [L8-integration-test.md](../../../HELIX-workflows/helix-process/L8-integration-test.md)
> 本 doc は HELIX-workflows に同期。差分は HELIX-workflows を優先。

### 工程の位置づけ (HELIX-workflows 正本)

| 項目 | 内容 |
|---|---|
| 区分 | V字 右腕（検証フェーズ） |
| 入力 | L7 実装・L5 結合テスト設計 |
| 出力 | L9 総合テスト への入力 |
| 対応する設計 | L5 詳細設計 / 結合テスト設計 |

### この工程の PLAN (HELIX-workflows 正本)

PLAN は機能（ドキュメント）単位で起票し、工程表（作成手順＋進捗）と実装計画を内蔵する。

### `L8-結合テストplan`
- モジュール間結合確認
- インターフェース結合確認

### `L8-依存関係解消plan`
- 依存不整合の検出
- 解消対応

> **PLAN が内蔵するもの** (HELIX-workflows 共通):
> - **工程表**: そのドキュメントを完成させる手順 (例: 参考調査 Web 検索 → 既存資料整理 → ドラフト → TL レビュー → 確定) と各手順の進捗
> - **実装計画**: 記載項目をどう埋めるかの計画

