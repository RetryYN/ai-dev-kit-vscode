---
doc_id: automation-gate-map
title: "Vモデル自動化・ゲートマップ"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# Vモデル自動化・ゲートマップ

## 概要

新Vモデル（L0–L14）全体の自動化。各 layer（工程）に detector が自動紐づき、各ゲートは `gate-checks.yaml` の static シェルコマンドで決定論的に判定する。FE に限らず全工程が対象で、AI判断は中身の評価のみに使う。

## layer × detector（工程別の自動検証）

vmodel-semantics.yaml で、各 layer の design 側・test 側にそれぞれ detector が紐づく。

| layer（対応工程） | design 側 detector | test 側 detector |
|---|---|---|
| planning（L0–L1） | axis-08 plan-integrity / axis-14 orchestration | axis-11 regression / axis-14 |
| requirement（L3） | axis-07 contract-drift / axis-08 / axis-12 connection | axis-09 test-quality / axis-11 |
| architecture（L4） | axis-02 coverage-erosion / axis-07 / axis-10 relation-graph | axis-09 / axis-11 / axis-12 |
| detailed（L5） | axis-06 naming / axis-07 / axis-12 | axis-02 / axis-09 / axis-11 |
| functional（L6） | axis-01 dead-code / axis-02 / axis-09 refactor | axis-02 |
| FE（L2 / L10） | axis-15 mock-promotion / axis-19 state-transition-drift | axis-16 design-token / axis-17 a11y / axis-18 visual |

axis-01〜14 は実装済み。axis-15〜19（FE）は未実装で、同じ枠に差し込む対象（fe-detector-spec.md 参照）。

## ゲート（決定論的 static チェック）

`gate-checks.yaml` の static はシェルコマンドで、exit 0 = pass の機械判定。

| ゲート | static チェック例 |
|---|---|
| G2 | plan_schema.py g2-check |
| G4 | helix-gate-api-check |
| G5 | visual-checks（desktop / tablet / mobile.png の存在） |
| G3 / G6 / G7 / G9 | 各 static シェルコマンド群 |

いずれも fail-close。`helix-gate --static-only` で AI を呼ばずに実行できる。

## 機械 vs AI の境界

| 機械（static / detector） | AI（ai-only） |
|---|---|
| detector 判定、成果物存在、trace 整合 | 設計の良し悪し |
| schema、命名、依存充足 | 要件の解釈・抽出 |
| 数値品質（カバレッジ、コントラスト比、差分率） | レビュー判断・トレードオフ |

Scrum を除く全モードは、入口分類（size / drive / kind）が決まれば、この機械側だけで工程を進行・検証できる。
