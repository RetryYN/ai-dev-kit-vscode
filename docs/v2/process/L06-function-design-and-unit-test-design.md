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

> **entry 関所**: 着工前に [design-coverage-baseline.md](../../../skills/workflow/doc-system-architect/references/design-coverage-baseline.md) §0 粒度ペアリング原則 + §3 L6 + §5 L単位ワークフロー を通す。L6 は **単体テスト (L7) 粒度** で書く (関数 1 個 = 単体テスト対象 1 個)。モジュール / クラス止まりは粒度違反。

### Step 1: 関数 / 機能単位設計
- L5 モジュールを **関数 / 機能単位** に分解
- 各関数 signature (input / output / error / 副作用) を確定
- 各関数に Design by Contract を付与: `requires:` (事前条件) / `ensures:` (事後条件) / `invariant:` (不変条件、状態保持 unit のみ)。これが L7 単体テストの入力値・アサーション設計を直接導く

### Step 2: 単体テスト設計のペア凍結 (V-model L7 ペア、実装スプリント直前)
- 関数ごとに **単体テスト** を設計
- `docs/v2/L7-test-design/<feature>-unit-test-design.md` に pair として書く
- 業界 standard: IEEE 829 § TCS / ISO 29119-3 clause 9.2 TestCaseSpecification
- case 構造: precondition / input / expected output / postcondition

#### Current-scope boundary: L6 内の単体テスト設計観点

L7 実装が明示承認されていない監査・設計補正では、L7 test-design artifact を新規作成しない。この場合、L6 仕様内に `*-UT-CAND-*` として単体テスト設計観点を固定し、L6 索引で集約する。

- FR18 の L6 仕様: `docs/v2/L6-functional-design/FR-*/function-spec.md`
- FR18 の L6 単体テスト設計観点索引: `docs/v2/L6-functional-design/fr18-unit-test-design-index.yaml`
- 現在値: FR18 全件、L6 単体テスト設計観点 128 件

この索引は L6 の単体テスト設計観点を示す証跡であり、L7 の単体テスト設計成果物、単体テスト実装、単体テスト実施、カバレッジ確認 / closure ではない。L7 へ進む場合は add-feature 承認後に、対応する L7 test-design artifact とテスト実装を別途作成する。

### Step 3: 工程表 (WBS) 作成
- L6 機能設計から L7 実装スプリントへの WBS を作る
- 各 WBS item = 1 L7 PLAN に対応

### Step 4: G6 機能設計凍結ゲート通過
- **exit 関所**: design-coverage-baseline §5 の L6 exit 条件 (関数粒度 + DbC 充足 + `balance_ratio ≥ 1.0` + 片肺なし) を満たす

## 成果物

- **正本**: `docs/v2/L6-functional-design/FR-XXX/<feature>/<function>.md` (関数 / 機能単位)
- **ペア artifact**: `docs/v2/L7-test-design/<feature>-unit-test-design.md`
- **L6 内単体テスト設計観点索引**: `docs/v2/L6-functional-design/fr18-unit-test-design-index.yaml` (L7 未承認範囲での `*-UT-CAND-*` 集約)
- **工程表**: `docs/v2/L6-functional-design/schedule/<area>-wbs.md` or `.helix/task-plan.yaml`

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
- ❌ L6 内の `*-UT-CAND-*` 索引を L7 実装完了・coverage closure として扱う (証跡の階層違反)
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
