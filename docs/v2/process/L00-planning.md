---
doc_id: process-L00
title: "L0 企画書"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L0
pairs_with: null
canonical_source: HELIX-workflows/helix-process/L0-concept.md
---

# L0 企画書

## 入力

- ユーザー要望 (チャット / ヒアリング)
- 市場調査 / 競合分析
- ビジネス目標 / 採算試算
- skill: `advanced/innovation-mgr` / `advanced/tech-innovation` / `advanced/marketing-innovation`

## 進め方

### Step 1: 企画の発想 + 仮説化
- ユーザー価値 + ビジネス価値 + 技術実現性の 3 軸で仮説を立てる
- JTBD (Jobs-to-be-Done) / North Star Metric / 顧客課題仮説を skill 経由で構造化

### Step 2: 業界 / 海外事例の翻案
- PdM Innovation skill (tech / marketing) で海外思想を日本版に翻案
- 重複競合プロダクトとの差分を明示

### Step 3: G0.5 企画突合ゲート判定 (前段)
- PdM Innovation Manager skill が `tl-advisor` を 1 回 adversarial check として呼ぶ
- 翻案結果 + 仮説 + 差分が妥当か確認

### Step 4: L1 要求定義への接続
- 企画書から L1 要求定義工程へ渡す入力 (ビジネス要求 / ユーザー要求 / 機能カテゴリ) を整理

## 成果物

- **正本**: `docs/v0/<product>-concept.md` (HELIX 本体は `docs/v2/CONCEPT.md`)
- **PdM 翻案結果**: `docs/v0/pdm/{tech,marketing}-innovation.md`
- **G0.5 突合記録**: 企画書の全項目が L1 に反映されているか PM 判定

## ペア凍結相手

なし (V-model 最上流、運用検証 (L14) との緩いペア)

## ゲート

- **G0.5 企画突合ゲート** (PM 判定): 企画書の全項目が L1 要求定義に反映可能か

## 関連 skill

- `advanced/innovation-mgr` (PdM 統合判断)
- `advanced/tech-innovation` (海外技術思想翻案)
- `advanced/marketing-innovation` (海外マーケ翻案)
- `writing/god-writing` (LP / セールス文書、必要に応じ)

## アンチパターン

- ❌ 企画書なしで L1 要求定義に進む (ビジネス目標が不明)
- ❌ 業界事例調査を skip (差別化困難)
- ❌ G0.5 で tl-advisor adversarial check を skip

---

## 正本 (HELIX-workflows) 抽出 — 2026-05-24 V2 完全移行

> 正本: [L0-concept.md](../../../HELIX-workflows/helix-process/L0-concept.md)
> 本 doc は HELIX-workflows に同期。差分は HELIX-workflows を優先。

### 工程の位置づけ (HELIX-workflows 正本)

| 項目 | 内容 |
|---|---|
| 区分 | 起点 |
| 入力 | 事業課題・アイデア |
| 出力 | L1 要求定義 への入力 |
| ペアとなるテスト設計 | なし（L11 総合レビュー / ユーザー検証で最終確認） |

### この工程の PLAN (HELIX-workflows 正本)

PLAN は機能（ドキュメント）単位で起票し、工程表（作成手順＋進捗）と実装計画を内蔵する。

### `L0-企画書plan`
- 背景・目的
- 解決する課題
- スコープ（対象 / 対象外）
- 投資対効果
- 成功条件・KGI / KPI
- 想定リスク

> **PLAN が内蔵するもの** (HELIX-workflows 共通):
> - **工程表**: そのドキュメントを完成させる手順 (例: 参考調査 Web 検索 → 既存資料整理 → ドラフト → TL レビュー → 確定) と各手順の進捗
> - **実装計画**: 記載項目をどう埋めるかの計画

