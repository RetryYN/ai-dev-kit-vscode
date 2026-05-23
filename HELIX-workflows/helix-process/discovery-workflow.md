---
doc_id: workflow-discovery
title: "Discovery ワークフロー"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# Discovery ワークフロー

## 概要

Discovery は、計画上の不明点（要件・実現性が未確定なもの）を、仮説・PoC・検証スクリプト・判定で潰す探索・検証モード。Forward HELIX（L0–L14）に入る前の不確実性を潰す前段。既存資産が絡む不明点は Reverse と組み合わせる（Discovery × Reverse）。検証スクリプトは `verify/` に蓄積され、以後の回帰チェックとして残る。

## 業界標準との関係

> 注: プロダクト開発の Product Discovery（何を作るべきか・作れるかが未確定な状態を、検証で明らかにする段階）に対応する。確定後に Forward へ昇格させる前段モードである。

## Discovery × Reverse

- 未知の探索（Discovery: 仮説検証で新たに明らかにする）と、既知の解明（Reverse: 既存資産を逆引きする）を組み合わせる。
- 計画上の不明点が既存コード・設計に起因する場合は、まず Reverse（code / design / normalization）で事実を集め、その上で Discovery の仮説検証にかける。
- 既存の `scrum_reverse_matrix` の役割をこのモードが引き継ぐ。

## 入口判定

| 状況 | Discovery に入れる理由 |
|---|---|
| 要件が未確定、成功条件が曖昧 | 先に仮説と acceptance を固定する |
| 技術的にできるか分からない | PoC と verify script で確認する |
| UI / UX の方向性が複数ある | `ui` 系 trigger と PoC で比較する |
| 実装前に新事実が出た | `trigger detect` で差し込み候補化する |
| 不明点が既存コード・設計に起因する | Reverse と組み合わせて事実を集めてから検証する |

## 基本フロー

```
init → backlog add（仮説）→ plan → poc → verify → decide → review
```

fail-close: `confirmed` は対象 hypothesis の verify script 成功が必須、`review` は verify 失敗時に sprint を completed にしない。

## Hypothesis 判定

| status | 意味 | 次アクション |
|---|---|---|
| `queued` | backlog にあるが未着手 | `plan` で sprint に入れる |
| `testing` | 現在検証中 | `poc` と `verify` を実行 |
| `confirmed` | acceptance を満たした | handoff / promotion plan で Forward へ接続 |
| `rejected` | 仮説が成立しない | backlog から外し、学びを記録 |
| `pivot` | 仮説を修正して再検証 | 新しい仮説として次 sprint へ |

## Trigger 判定（4 象限）

`detect → evaluate（uncertainty × impact）→ transition（pending → triaged → adopted / rejected → archived）`。`priority_score` = impact 0.6 + uncertainty 0.4。

## Forward 接続

`confirmed` で handoff / promotion plan draft が生成される。PoC をそのまま本実装にせず、L1 要求定義 / L3 要件定義 / L4–L6 設計へ昇格させる。verify script は L6（機能設計 / 単体テスト）の回帰検証に残す。

## 起票する PLAN kind

検証は `poc` kind を起票する。confirmed 後の Forward 接続では、PoC をそのまま本実装にせず L1 / L3 / L4–L6 へ昇格させる。逸脱と kind の対応は deviation-plan-map.md を参照。
