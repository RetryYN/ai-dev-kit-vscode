---
doc_id: process-L09
title: "L9 総合テスト + 依存関係解消"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L9
pairs_with: L4
canonical_source: HELIX-workflows/helix-process/L9-system-test.md
---

# L9 総合テスト + 依存関係解消

## 入力

- L4 基本設計 (必須)
- L9 総合テスト設計 doc (L4 でペア凍結済、`docs/v2/L9-test-design/`)
- L8 結合テスト完遂物
- skill: `common/testing` / `workflow/verification` / `workflow/quality-lv5`

## 進め方

### Step 1: 総合テスト実施
- L9 総合テスト設計 (artifact ③) を入力に、E2E / 性能 / セキュリティ総合テストを実行
- L4 アーキテクチャ全体が動くか検証

### Step 2: 依存関係解消 (system level)
- 外部 API / DB / messaging / cache の総合的な依存関係解消
- 環境間差異の検出 (dev / staging)

### Step 3: 不整合差し戻し
- L4 基本設計違反 → L4 に差し戻し (大局判断 ADR の再評価含む)
- L9 テスト設計違反 → L4 ペア凍結直し

### Step 4: G9 総合テスト通過判定 (セキュリティ③)

## 成果物

- **総合テスト実施結果**: E2E / 性能 / セキュリティテスト raw output
- **依存関係解消記録**: `docs/v2/L9-test-results/<area>-system-test-result.md`

## ペア凍結相手 (上流対応)

L4 基本設計

## ゲート

- **G9 総合テスト通過ゲート + セキュリティ③**: TL + PM 判定

## 関連 skill

- `common/testing`
- `workflow/verification`
- `workflow/quality-lv5`
- `common/security` (セキュリティ③)
- `automation/observability` (性能観測)

## アンチパターン

- ❌ L4 でペア凍結されていない総合テスト設計を本工程で起こす (V-model 違反、L4 に差し戻し)
- ❌ PLAN 起票
- ❌ セキュリティ③ を skip (G9 blocking 対象)

---

## 正本 (HELIX-workflows) 抽出 — 2026-05-24 V2 完全移行

> 正本: [L9-system-test.md](../../../HELIX-workflows/helix-process/L9-system-test.md)
> 本 doc は HELIX-workflows に同期。差分は HELIX-workflows を優先。

### 工程の位置づけ (HELIX-workflows 正本)

| 項目 | 内容 |
|---|---|
| 区分 | V字 右腕（検証フェーズ） |
| 入力 | L8 結合テスト・L4 総合テスト設計 |
| 出力 | L10 への入力 |
| 対応する設計 | L4 基本設計 / 総合テスト設計 |

### この工程の PLAN (HELIX-workflows 正本)

PLAN は機能（ドキュメント）単位で起票し、工程表（作成手順＋進捗）と実装計画を内蔵する。

### `L9-総合テストplan`
- システム全体動作
- 機能テスト
- 非機能テスト（性能・セキュリティ等）

### `L9-依存関係解消plan`
- システム全体の依存整合

> **PLAN が内蔵するもの** (HELIX-workflows 共通):
> - **工程表**: そのドキュメントを完成させる手順 (例: 参考調査 Web 検索 → 既存資料整理 → ドラフト → TL レビュー → 確定) と各手順の進捗
> - **実装計画**: 記載項目をどう埋めるかの計画

