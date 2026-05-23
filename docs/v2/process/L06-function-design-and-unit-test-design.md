---
doc_id: process-L06
title: "L6 機能設計 + 単体テスト設計"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L6
pairs_with: L7
canonical_source: HELIX-workflows/helix-process/L6-functional-design.md
---

# L6 機能設計 + 単体テスト設計

## 入力

- L5 詳細設計 (必須)
- skill: `workflow/design-doc` / `workflow/schedule-wbs` / `common/testing`

## 進め方

### Step 1: 関数 / 機能単位設計
- L5 モジュールを **関数 / 機能単位** に分解
- 各関数 signature (input / output / error / 副作用) を確定

### Step 2: 単体テスト設計のペア凍結 (V-model L7 ペア、実装スプリント直前)
- 関数ごとに **単体テスト** を設計
- `docs/v2/L7-test-design/<feature>-unit-test-design.md` に pair として書く
- 業界 standard: IEEE 829 § TCS / ISO 29119-3 clause 9.2 TestCaseSpecification
- case 構造: precondition / input / expected output / postcondition

### Step 3: 工程表 (WBS) 作成
- L6 機能設計から L7 実装スプリントへの WBS を作る
- 各 WBS item = 1 L7 PLAN に対応

### Step 4: G6 機能設計凍結ゲート通過

## 成果物

- **正本**: `docs/v2/L6-function-design/<feature>/<function>.md` (関数 / 機能単位)
- **ペア artifact**: `docs/v2/L7-test-design/<feature>-unit-test-design.md`
- **工程表**: `docs/v2/L6-function-design/schedule/<area>-wbs.md` or `.helix/task-plan.yaml`

## ペア凍結相手

L7 実装スプリント (本工程の単体テスト設計を L7 で実装 + 実施)

## ゲート

- **G6 機能設計凍結ゲート**: TL + PM 判定、関数 signature 確定 + V-model 単体テスト設計ペア凍結 + WBS 完備

## 関連 skill

- `workflow/design-doc`
- `workflow/schedule-wbs`
- `common/testing`
- `agent-skills/api-and-interface-design`

## アンチパターン

- ❌ 単体テスト設計のペア凍結を skip (V-model 違反、L7 で TDD 着手できない)
- ❌ WBS なしで L7 PLAN 起票に進む (Sprint 順序 / 並列衝突判定不能)
- ❌ 関数 signature を曖昧にして L7 に渡す (L7 で 3 点レビューが機能しない)

---

## 正本 (HELIX-workflows) 抽出 — 2026-05-24 V2 完全移行

> 正本: [L6-functional-design.md](../../../HELIX-workflows/helix-process/L6-functional-design.md)
> 本 doc は HELIX-workflows に同期。差分は HELIX-workflows を優先。

### 工程の位置づけ (HELIX-workflows 正本)

| 項目 | 内容 |
|---|---|
| 区分 | V字 左腕（設計フェーズ・最下層） |
| 入力 | L5 詳細設計 |
| 出力 | L7 実装 への入力 |
| ペアとなるテスト設計 | 単体テスト設計（谷 L7 単体テストで実行） |

### この工程の PLAN (HELIX-workflows 正本)

PLAN は機能（ドキュメント）単位で起票し、工程表（作成手順＋進捗）と実装計画を内蔵する。

### `L6-関数仕様plan`
- 関数 / メソッド仕様
- 引数・戻り値

### `L6-クラス設計plan`
- クラス構成
- 責務

### `L6-エッジケースplan`
- 境界値
- 例外・エラー処理パターン

> **PLAN が内蔵するもの** (HELIX-workflows 共通):
> - **工程表**: そのドキュメントを完成させる手順 (例: 参考調査 Web 検索 → 既存資料整理 → ドラフト → TL レビュー → 確定) と各手順の進捗
> - **実装計画**: 記載項目をどう埋めるかの計画

