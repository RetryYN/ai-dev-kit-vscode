---
doc_id: workflow-research
title: "Research HELIX ワークフロー"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# Research HELIX ワークフロー

## 概要

Research は、実装前の技術調査・方式比較・意思決定を行うモード。kind=research、generates=research-memo + ADR。机上で調べて決めることが目的で、成果は意思決定記録（ADR）として残す。

## 位置づけ（Discovery との違い）

| | Discovery（仮説検証） | Research（事前調査） |
|---|---|---|
| 方法 | PoC を作って検証する | 調べて比較し決める（机上中心） |
| 問い | 作れるか／成立するか | 何を選ぶか／どう作るか |
| 成果物 | verify script + 判定 | research-memo + ADR |

「作って試す」のが Discovery、「調べて決める」のが Research。

## 入口判定

| 状況 | Research を使う理由 |
|---|---|
| 技術選定・方式比較が必要 | 候補を比較し意思決定を残す |
| 実装前に調査したい | ADR で判断根拠を記録する |
| 作って試すより調べて決める方が適切 | PoC 不要な意思決定 |

## 基本フロー

```
調査課題の定義 → 候補の調査 → 比較評価 → ADR で意思決定 → research-memo
```

1. 調査課題: 何を決めるための調査か
2. 候補調査: 選択肢・先行事例・制約を集める
3. 比較評価: 基準を立てて候補を比較
4. ADR: 意思決定と理由を記録（Architecture Decision Record）
5. research-memo: 調査内容をまとめる

## 起票する PLAN kind

- kind=research、generates=research-memo（`docs/research/<slug>-research-memo.md`）+ ADR（`docs/adr/ADR-NNN-<slug>.md`）
- 逸脱と kind の対応は deviation-plan-map.md を参照。

## Forward 接続

ADR は L1 要求定義・L4 基本設計の判断材料として接続する。調査の結果、「作れるか不明」になれば Discovery（PoC 検証）へ、「既存実装を調べる必要がある」となれば Reverse へ切り替える。
