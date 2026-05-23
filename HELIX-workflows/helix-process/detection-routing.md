---
doc_id: detection-routing
title: "HELIX DB 検出 → モード連携"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# HELIX DB 検出 → モード連携

## 概要

helix_db で管理することで検出できる異常（drift・劣化・暴走・障害）を、trigger 経由で適切なモード（Recovery / Incident / Reverse 等）へ自動ルーティングする仕組み。Discovery の trigger（detect → evaluate 4象限 → transition）方式を、DB 検出全般に拡張する。

## DB で検出できるもの

| 検出 | 仕組み | 意味 |
|---|---|---|
| drift（設計 ⇔ 実装 ⇔ doc 乖離） | drift-check / drift_db_diff | API / 契約 / DB スキーマの乖離 |
| 劣化（コード品質） | detector axis-01〜14 | dead code / coverage erosion / 負債 |
| trace 不整合 | vmodel lint | 設計 ⇔ テスト設計の対応欠落 |
| 暴走 | agent_mandatory / budget | 役割逸脱・過剰消費 |
| 本番障害 | post-deploy trigger / SLO | KPI / SLO 逸脱 |

## 検出 → モードルーティング

検出シグナルを、対応するモードへ振り分けて起票する。

| 検出 | ルーティング先 | 起票 kind |
|---|---|---|
| 設計 ⇔ 実装 drift | Reverse（normalization type） | reverse |
| コード劣化・負債蓄積 | Refactor | refactor |
| AI 暴走（逸脱 / 過剰消費） | Recovery | recovery |
| 本番障害（SLO 逸脱） | Incident | troubleshoot / recovery |
| 設計 unknown 多発 | Reverse（code type） | reverse |

## 連携フロー

```
DB 検出（drift / 劣化 / 暴走 / 障害）
   → trigger 生成
   → evaluate（uncertainty × impact の 4象限）
   → モード発動（Recovery / Incident / Reverse / Refactor）
   → 対応 kind の PLAN 起票
   → 自動登録（db-auto-registration.md）
```

## 自律的な整合ループ

自動登録（db-auto-registration）と検出連携（本書）は循環する。

```
自動登録で DB が充実
   → DB 検出（drift / 劣化 / 暴走 / 障害）
   → モード発動 → PLAN 起票
   → 自動登録
   → （再検出）
```

この循環により、Vモデル本線 DB が、ドキュメント・コード・テスト・カバレッジの整合を自律的に保ち、ずれた瞬間に適切なモード（Recovery / Incident / Reverse / Refactor）へつながる。検出から対応までが、人手の判断を待たずに起動する。
