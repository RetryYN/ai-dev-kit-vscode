---
doc_id: test-perspective-gate
title: "テスト観点ゲート（W字補強）"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# テスト観点ゲート（W字補強）

## 概要

Vモデルの弱点「テスト工程の重複・抜け漏れ」を、テストレベル間の観点チェックで補強する。W字モデル（テスト設計を上流に早期参加させる考え方）に相当する。モード追加ではなく、ゲート/lint 側の補強。

## テストレベル（vmodel layer 対応）

各設計レベルに対応するテストレベルが既に定義されている。

| 設計レベル | テストレベル | 対応工程 |
|---|---|---|
| planning | operational（運用テスト） | L1 ⇔ L14 |
| requirement | acceptance（受入テスト） | L3 ⇔ L12 |
| architecture | system_integration（総合テスト） | L4 ⇔ L9 |
| detailed | integration（結合テスト） | L5 ⇔ L8 |
| functional | unit（単体テスト） | L6 ⇔ L7 |

## 補強する検出

| 検出 | 仕組み |
|---|---|
| 抜け漏れ（設計項目にテスト設計がない） | 設計 ⇔ テスト設計の双方向 trace（4 artifact）で欠落を検出 |
| 重複（同一観点が複数レベルで重複） | レベル間の観点重複を検出（新規ゲート観点） |
| カバレッジ劣化 | axis-02 coverage-erosion |
| テスト品質 | axis-09 test-quality 系 |

## ゲート設計

各テストレベルの観点を定義し、static チェックで2点を fail-close で検証する。

1. 観点の網羅: 設計項目に対応するテスト観点が、該当レベルに存在するか（抜け検出）。
2. レベル間の非重複: 同一観点が複数テストレベルで重複していないか（重複検出）。下位レベルで担保済みの観点を上位で再テストしていないか。

## 既存との接続

- 基盤は 4 artifact 双方向 trace（設計 ⇔ テスト設計の 1:1 対応）。
- これに「観点の重複」検出を加えることで、W字の狙い（早期にテスト観点を設計と並走させ、重複・抜けを防ぐ）を機械化する。
- すべて差分・対応関係の照合なので AI 判断を要さず、`--static-only` で実行できる。

## FE detector との関係

FE 系（fe-detector-spec.md）の visual-regression / a11y-regression も、テスト観点として functional レベルに位置づく。FE detector の実装が進めば、本ゲートの観点網羅に FE 観点が加わる。
