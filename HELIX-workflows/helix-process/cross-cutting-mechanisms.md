---
doc_id: cross-cutting-mechanisms
title: "HELIX 横断機構（interrupt / debt / drift-check / readiness）"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# HELIX 横断機構

## 概要

入口モード（Forward / Scrum / Discovery 等）とは別に、全工程・全モードから発動する工程横断の支援機構が4つある。これらはモードではなく、Vモデルの進行を止めずに割り込み・負債・乖離・保留を扱う。

## 4つの横断機構

| 機構 | コマンド | 役割 | 連携先 |
|---|---|---|---|
| interrupt | helix-interrupt | 開発中の割り込み（design_gap / new_requirement / constraint / po_change）を sprint interrupted にして対応し resume | 重大・暴走なら Recovery |
| debt | helix-debt | 技術負債台帳（debt-register.yaml）の list / add / resolve | 蓄積したら Refactor |
| drift-check | helix-drift-check | 設計 ⇔ 実装の契約乖離検知（D-API / D-CONTRACT / D-DB） | 検出 → Reverse normalization（detection-routing） |
| readiness | helix-readiness | deferred finding（保留事項）を後工程 PLAN へ先送り（PM 承認） | ゲート通過判断の保留弁 |

## detection-routing との関係

- drift-check と debt は detection-routing.md の検出源になる（drift → Reverse、負債 → Refactor）。
- interrupt は Recovery の前段ガードとして働く（開発中の逸脱を捕捉 → 重大なら Recovery へ）。
- readiness は、ゲートを止めずに未解決事項を後工程へ送る「保留弁」で、fail-close の例外を統制する。

## 位置づけ

これらは「入口モード」に数えない。どのモードの最中でも発動し、工程の進行を維持しながら割り込み・負債・乖離・保留を処理する。モード（縦の流れ）に対する横の支援層と捉える。

| 軸 | 担うもの |
|---|---|
| 縦（入口モード） | Forward / Scrum / Discovery / Reverse / Incident / Add-feature / Refactor / Retrofit / Research / Recovery |
| 横（横断機構） | interrupt / debt / drift-check / readiness |

横断機構が拾った事象（割り込み・負債・乖離・保留）は、必要に応じて対応する縦のモードへ接続され、最終的に PLAN として本線 DB に記録される。
