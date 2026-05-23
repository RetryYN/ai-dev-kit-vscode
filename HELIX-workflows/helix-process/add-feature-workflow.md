---
doc_id: workflow-add-feature
title: "Add-feature HELIX ワークフロー"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# Add-feature HELIX ワークフロー

## 概要

Add-feature は、既に Forward（Vモデル L0–L14）で作られ、ドキュメント体系を持つ既存システムに新機能を追加するワークフロー。フル工程をゼロから通すのではなく、影響範囲の差分だけを追補する。PLAN kind の `add-design` / `add-impl` を使い、既存の設計・実装 PLAN に紐づける。

## 位置づけ（Forward との違い）

| | Forward（新規） | Add-feature（追加） |
|---|---|---|
| 入口 | ゼロから新規開発 | 既存システムへの機能追加 |
| 工程 | L0–L14 フル | 影響範囲の差分のみ |
| PLAN kind | `design` / `impl` | `add-design` / `add-impl` |
| 既存資産 | なし | 既存の L1–L14 ドキュメントに `requires` で紐づく |

新規ゼロからなら Forward、既存の設計を先に逆引きする必要があれば Reverse、追加要件が未確定なら Discovery を前段に挟む。

## 入口判定

| 状況 | Add-feature を使う理由 |
|---|---|
| 既存システムに新機能を追加したい | フル工程でなく差分だけ追補する |
| 既存の設計・実装を踏まえた追補が必要 | 既存 PLAN に `requires` で紐づける |
| 影響範囲が限定的 | 影響する工程だけを通す |

## 基本フロー

```
影響範囲特定 → 追加要求・要件 → 追加設計（add-design）→ 追加実装（add-impl）
   → 既存テスト影響確認＋追加テスト → Vモデル体系へ統合
```

1. **影響範囲特定**: 既存の L1–L14 ドキュメントのどこに影響するかを洗い出す
2. **追加要求・要件**: 必要なら L1 要求定義 / L3 要件定義に追補する
3. **追加設計（`add-design`）**: 影響する L4 基本設計 / L5 詳細設計 / L6 機能設計に追補する。既存 `design` PLAN に `requires` で紐づく
4. **追加実装（`add-impl`）**: L7 実装で実装する。既存 `impl` PLAN に `requires` で紐づく
5. **既存テスト影響確認＋追加テスト**: L8 結合テスト / L9 総合テストで、既存テストへの影響を確認し追加テストを起こす
6. **Vモデル体系へ統合**: 追補を該当工程ファイルに反映し、双方向 trace（設計⇔テスト）を更新する

## PLAN kind

| kind | 用途 | 紐づけ |
|---|---|---|
| `add-design` | 設計追補（既存設計への追加） | `requires: PLAN-NNN-design` |
| `add-impl` | 実装追補（既存実装への追加） | `requires: PLAN-NNN-impl` |

## Vモデル体系への統合

追加した要求・設計・実装・テストは、新規 Forward と同じく L0–L14 のドキュメント体系に追補として反映し、双方向 trace を保つ。これにより、追加機能も既存機能と同じトレーサビリティ・ゲートで管理される。差分追補であっても、設計とテスト設計のペア（4 artifact 双方向 trace）は新規開発と同じ規律で揃える。
