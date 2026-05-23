---
doc_id: deviation-plan-map
title: "Vモデル逸脱と PLAN 起票マップ"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# Vモデル逸脱と PLAN 起票マップ

## 概要

各ワークフロー（モード）が標準Vモデル（design → impl の素直な流れ）から逸脱する場合、対応する PLAN kind を起票する。PLAN kind が逸脱パターンを表現し、固有の generates（成果物）でドキュメントに落ちる。逸脱もすべて PLAN として記録されるため、HELIX DB で一元管理できる。

## モード × 逸脱パターン × PLAN kind × generates

| モード | 逸脱パターン | PLAN kind | 主な generates（成果物） |
|---|---|---|---|
| Forward（標準） | 逸脱なし | design / impl | design_doc + ADR / module + test |
| Discovery | Vモデル前段で検証する | poc | verify script + test |
| Reverse | Vモデルを逆行する | reverse | evidence + as-is-design |
| Incident | Vモデル外で緊急対応する | troubleshoot / recovery | module + test / recovery-log |
| Recovery | AI 暴走・独断専行を収束する | recovery | recovery-log（再開ポイント・認識訂正） |
| Add-feature | 既存への差分追補 | add-design / add-impl | design 追補 / module 追補 |
| Refactor | 構造改善（振る舞い不変） | refactor | module |
| Retrofit | 既存改修・移行 | retrofit | retrofit-matrix + config |
| Research | 事前調査・意思決定 | research | research-memo + ADR |

## PLAN 起票 ＝ 逸脱記録 ＝ ドキュメント生成計画

PLAN の frontmatter が逸脱を構造化する。

- `kind`: どの逸脱パターンか（上表）
- `generates`: 生成する成果物パス＝ドキュメント生成計画
- `requires`: 標準フロー（design / impl）や前提 PLAN への接続
- `layer` / `gate`: どの工程・ゲートに紐づくか

起票した時点で generates が成果物パスを定義するので、逸脱作業の成果が自動的にドキュメントとして追跡対象になる。

## HELIX DB 管理体制

- 標準・逸脱を問わず、全 PLAN が DB（SQLite FTS5）で一元管理される。
- `kind` で逸脱種別を分類でき、`generates` でドキュメントを追跡、`requires` で依存（標準フローへの戻り）を追跡できる。
- Vモデルからの分岐（Discovery / Reverse / Incident / Add-feature 等）も、すべて PLAN レコードとして DB に残るため、どのワークフローがどこで逸脱し、どの成果物を生み、どこで標準フローに戻ったかを機械的に辿れる。

この構造により、逸脱は「例外的な手作業」ではなく「kind 付き PLAN の起票」という定型操作になり、ドキュメント化と DB 管理が同時に成立する。
