---
doc_id: workflow-refactor
title: Refactor HELIX ワークフロー
status: accepted
accepted_date: 2026-05-24
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
integration_target:
  docs_path: docs/design
  category: モードワークフロー
---

# Refactor HELIX ワークフロー

## 概要

Refactor は、既存コードの内部構造を、外部から見た振る舞いを変えずに改善するモード。kind=refactor。機能追加ではなく、可読性・保守性・構造の改善が目的。

## 業界標準との関係

> 注: リファクタリングの定義に沿う。外部から見た振る舞いを変えずに内部構造を改善し、テストで保護しながら小さいステップ（変更 → テスト → コミット）で進める。機能追加（新しい振る舞いを加える）やバグ修正（振る舞いを直す）とは区別する。

## 位置づけ

| | Forward（新規） | Refactor（構造改善） |
|---|---|---|
| 目的 | 新しい機能を作る | 内部構造を改善する（振る舞い不変） |
| 要件・設計 | 新規に定義 | 変えない |
| PLAN kind | design / impl | refactor |
| テスト | 新規作成 | 既存を保護網として流用 |

## 入口判定

| 状況 | Refactor を使う理由 |
|---|---|
| コードが複雑化・技術的負債が蓄積 | 振る舞いを変えず構造を整理する |
| 可読性・保守性を上げたい | 内部構造のみ改善する |
| 機能追加・バグ修正ではない | それらは Add-feature / Incident で扱う |

## 基本フロー

```
保護網のテスト整備 → 小さなリファクタリング → テスト緑確認 → コミット → 繰り返し
```

1. 保護網: 対象範囲のテスト（なければゴールデンマスターテストで現挙動を固定）
2. 小さな変更: 一度に大きく変えず、小ステップで
3. テスト緑確認: 各ステップで振る舞い不変を検証
4. コミット: ステップごとに
5. 繰り返し: 負債が解消するまで

## 起票する PLAN kind

- kind=refactor、generates=module（`cli/lib/<module>.py` 等）
- **設計不変の純実装 refactor（`pure_impl`）のみ**、要件・設計 PLAN を起票せず実装の構造改善に閉じてよい。**structural refactor**（モジュール境界変更 → L5↔L8 / 関数責務・DbC・public callable 変更 → L6↔L7）は対の design 層を再凍結する。**契約 / API / DB / schema に触れる**なら Refactor でなく Retrofit / Add-feature / Reverse へ差し戻す（[forward-return-discipline.md §3](forward-return-discipline.md) の `design_change_class` 判定に従う）。逸脱と kind の対応は deviation-plan-map.md を参照。

## HELIX 検証観点

- axis-09 refactor-opportunity（リファクタ候補の検出）
- axis-11 regression（既存テストの緑維持＝振る舞い不変の機械検証）

## Forward 接続

> **Forward 引き戻し規律（共通）**: 本 workflow の forward_return は [forward-return-discipline.md](forward-return-discipline.md) を必須適用する（`design_change_class` 判定 / 対 design 層の再凍結）。固有点: 「設計 PLAN 起票せず」は `pure_impl` に限る。structural / 契約変更は対 design を再凍結 or 上位 workflow へ差し戻し。

振る舞いを変えないため、L1 要求・L4 設計は不変。`pure_impl` refactor は L7 実装の内部構造を改善し、既存テスト（L8 / L9）を保護網として流用する。**ただし内部構造変更で L5 詳細設計（モジュール境界・依存）や L6 機能設計（DbC）が実装と乖離する場合は `design_or_contract_changed` として対の design 層を再凍結する**。設計と実装の双方向 trace は維持する。

## §関連 skill

- [refactoring](../skills/common/refactoring/SKILL.md)
