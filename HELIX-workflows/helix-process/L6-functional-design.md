---
doc_id: process-l6-functional-design
title: L6 機能設計 — 工程定義
status: accepted
accepted_date: 2026-05-24
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
integration_target:
  docs_path: docs/design
  category: L0-L14 工程
---

# L6 機能設計

## 工程の位置づけ

| 項目 | 内容 |
|---|---|
| 区分 | V字 左腕（設計フェーズ・最下層） |
| 入力 | L5 詳細設計 |
| 出力 | L7 実装 への入力 |
| ペアとなるテスト設計 | 単体テスト設計（谷 L7 単体テストで実行） |

> 注: 標準では機能設計は基本設計（外部設計）の一部だが、本定義では実装直前の最下層設計として独立。

## 粒度規律（設計⇔検証の粒度ペアリング）

L6 機能設計は **単体テスト (L7) の粒度** で書く。これは HELIX Core §1 V モデルの「設計⇔検証の対」を粒度軸で閉じる規律であり、L6 が薄くなる事故を防ぐ正本。

- **関数粒度**: L5 モジュールを関数 / メソッド 1 個まで分解する。モジュール / クラス止まり (L5 粒度) は粒度違反。
- **Design by Contract**: 各関数仕様に `requires:` (事前) / `ensures:` (事後) / `invariant:` (不変、状態保持 unit のみ) を持たせ、L7 単体テストの入力値・アサーションを直接導く。
- **量保証 (Chargaff)**: 関数仕様 1 件に対し単体テストケース ≥ 1 件 (`balance_ratio ≥ 1.0`)。
- **片肺禁止**: 機能設計と単体テスト設計の一方だけの存在を許さない (G6 fail-close)。

> 着工前 / 凍結前に [design-coverage-baseline.md](../../skills/workflow/doc-system-architect/references/design-coverage-baseline.md) §0 粒度ペアリング原則 + §3 L6 + §4 薄化防止機構 + §5 L単位ワークフロー を entry / exit 関所として通す。
>
> **G6 機能設計凍結ゲート exit 条件**: 関数 signature 確定 + V-model 単体テスト設計ペア凍結 + WBS 完備 + DbC (`requires`/`ensures`) 充足 + `balance_ratio ≥ 1.0`。

## この工程の PLAN

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

## PLAN が内蔵するもの

- **工程表**: そのドキュメントを完成させる手順（例: 参考調査の Web 検索 → 既存資料・ヒアリング整理 → ドラフト → TL レビュー → 確定）と各手順の進捗
- **実装計画**: 記載項目をどう埋めるかの計画
