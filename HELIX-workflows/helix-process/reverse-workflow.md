---
doc_id: workflow-reverse
title: "Reverse HELIX ワークフロー"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# Reverse HELIX ワークフロー

## 概要

Reverse HELIX は、既存コードや既存設計から事実を集め、Forward HELIX に安全に接続するための逆引きフロー。新規開発ではなく、現状理解・設計復元・差分整理が主目的。

## 業界標準との関係

> 注: 標準のソフトウェア・リバースエンジニアリング（既存の製品・コードを逆方向に解析し、設計・仕様を復元して文書化する技術。静的解析 = 逆アセンブラ / 逆コンパイル、動的解析）と整合する。HELIX の Reverse は、設計復元（R0–R4）に加えて Forward HELIX への接続（RGC / routing）まで含む点が拡張になっている。

## 5 type

| type | 用途 |
|---|---|
| `code` | コード・DB・設定・外部接続から R0–R4 を作る |
| `design` | docs/plans, docs/design, docs/features から DAG と routing を作る |
| `upgrade` | バージョンアップ・依存更新の compatibility / impact / routing を作る |
| `normalization` | 実装と設計文書の drift を正規化する |
| `fullback` | 完了実装から文書整合と handover checklist を作る |

迷った場合は、対象がコードなら `code`、設計資産なら `design`、完了後の整合なら `fullback`。

## 基本フロー（code）

```
R0 evidence → R1 observed contracts → R2 as-is design → R3 intent hypotheses → R4 gap register → RGC
```

```bash
helix reverse code R0 --target src/
helix reverse code R1
helix reverse code R2
helix reverse code R3
helix reverse code R4
helix reverse code rgc
```

## Gate 判定

| Gate | 判定対象 | pass の意味 | fail 時 |
|---|---|---|---|
| `RG0` | 証拠収集 | 対象範囲の evidence が作られた | R0 をやり直す。対象 path / source を増やす |
| `RG1` | 観測契約 | API / DB / 型 / 互換契約の観測が揃った | R1 をやり直す。契約抽出対象を追加する |
| `RG2` | As-Is / DAG / impact | 現状設計・DAG・影響評価が説明できる | R2 をやり直す。矛盾や unknown を潰す |
| `RG3` | 仮説 / routing | Forward に渡す仮説・gap・routing がある | R3 / R4 を見直す。PO / TL 確認質問を追加する |
| `RGC` | gap closure | Forward 側で gap の閉塞状態を確認した | open / partial を Forward の debt / plan に戻す |

`design` と `normalization` は RG1 を持たず `RG0 → RG2 → RG3 → RGC`。`upgrade` は RGC を持たず R4 routing を Forward 接続点とする。各 gate は成果物ファイルが存在し空でなく、YAML なら top-level mapping として解析できることを最低条件に validation する。

## type 別 成果物

| type | 主な成果物 |
|---|---|
| `code` | `R0-evidence-map.yaml`, `R1-observed-contracts.yaml`, `R2-as-is-design.md`, `R3-intent-hypotheses.md`, `R4-gap-register.yaml` |
| `design` | `D0-design-evidence-map.yaml`, `D2-design-dag.yaml`, `D3-impl-order.yaml`, `D4-design-routing.yaml` |
| `upgrade` | `U0-upgrade-context.yaml`, `U1-upgrade-contracts.yaml`, `U2-assessment-impact.yaml`, `U3-upgrade-hypotheses.md`, `U4-upgrade-routing.md` |
| `normalization` | `N0-drift-evidence.yaml`, `N2-normalization-drift.yaml`, `N3-normalization-hypotheses.md`, `N4-normalization-gap-register.yaml` |
| `fullback` | `F0-fullback-evidence.yaml`, `F1-fullback-contracts.yaml`, `F2-fullback-as-is-review.md`, `F3-fullback-handover-checklist.yaml`, `F4-fullback-routing.md` |

## Forward 接続

R4 で作った routing は、Reverse の結論に応じて Forward HELIX のどこへ戻すかを決める。

| Reverse の結論 | Forward 側の戻し先 |
|---|---|
| 要件そのものが曖昧 | L1 要求定義 / L3 要件定義（`helix plan` 前に再定義） |
| 設計判断が不足 | L4 基本設計（ADR / design-doc） |
| API / DB / contract が不明 | L5 詳細設計（api-contract / db） |
| 実装だけで閉じる | L7 実装（sprint） |
| 運用・受入・文書整合 | L8–L11（fullback） |

`--invalidate-forward`（code type の R2/R3/R4/run/retry）は、Reverse の結果が Forward の既存 gate 前提を崩す場合に該当ゲートを invalidated に戻す。RGC は「Reverse で見つけた gap が Forward 側で閉じたか」の閉塞チェックで、open が残る場合は `debt` / `readiness defer` / 新規 `plan` に戻す。

## 起票する PLAN kind

各 type は `reverse` kind の PLAN として起票され、R4 routing で Forward へ接続する。逸脱と kind の対応は deviation-plan-map.md を参照。
