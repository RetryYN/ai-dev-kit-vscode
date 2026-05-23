---
doc_id: workflow-retrofit
title: "Retrofit HELIX ワークフロー"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# Retrofit HELIX ワークフロー

## 概要

Retrofit は、既存システムの改修・移行（依存更新、基盤移行、構成変更）を行うモード。kind=retrofit、generates=retrofit-matrix + config。要件・機能を大きく変えず、環境・構造を移行する。

## 業界標準との関係

> 注: レガシーマイグレーションに沿う。既存システムのデータ・機能を、要件を変えずに新環境へ段階的に移行する。現状把握 → 影響評価 → 移行計画 → 段階移行 → 検証、の手順を踏み、データ整合性・並行稼働・回帰テスト・ロールバック手順でリスクを抑える。

## 位置づけ

| | Forward（新規） | Retrofit（改修・移行） |
|---|---|---|
| 目的 | 新しい機能を作る | 既存を新環境・新構成へ移行 |
| 対象 | なし（ゼロから） | 既存システム |
| PLAN kind | design / impl | retrofit |
| 成果物 | design + module | retrofit-matrix + config |

Refactor（コード内部の構造改善）より広く、依存・基盤・構成の移行を扱う。Reverse の upgrade type（依存更新の影響評価）を前段に挟むこともある。

## 入口判定

| 状況 | Retrofit を使う理由 |
|---|---|
| 依存・フレームワーク・基盤の更新／移行 | 要件を保ったまま環境を移す |
| レガシー脱却・構成変更 | 段階的に移行しリスクを抑える |
| 要件は概ね維持 | 新規でも単なる構造改善でもない |

## 基本フロー

```
現状把握 → 影響評価（retrofit-matrix）→ 移行計画 → 段階移行（config 更新）→ 検証
```

1. 現状把握: 移行対象の構造・依存を把握
2. 影響評価: retrofit-matrix に移行対応（旧 → 新）と影響範囲を整理
3. 移行計画: 段階・順序・ロールバック手順を決める
4. 段階移行: config 更新・並行稼働で段階的に移す
5. 検証: 回帰テスト・性能テスト・データ整合性を確認

## 起票する PLAN kind

- kind=retrofit、generates=retrofit-matrix（`docs/plans/<slug>-retrofit-matrix.md`）+ config（`cli/config/<slug>.yaml`）
- 逸脱と kind の対応は deviation-plan-map.md を参照。

## Forward 接続

影響範囲に応じて L4 基本設計・L5 詳細設計・L7 実装へ追補する。検証は L8 結合テスト・L9 総合テスト（回帰）。要件自体が変わる場合のみ L1 / L3 へ戻す。
