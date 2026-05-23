---
doc_id: process-overview
title: "HELIX V2 工程定義 — L0 企画 → L14 運用検証 (15 工程)"
status: maintained
created: 2026-05-24
updated: 2026-05-24
owner: PM
canonical_source: HELIX-workflows/HELIX-process-L0-L14.md
note: "正本は repo root の HELIX-workflows/ ディレクトリ。本 doc は HELIX-workflows に同期しつつ既存資産 (Gate / アンチパターン / 関連 skill / 旧体系移行 note) を保持する実装文書。"
---

# HELIX V2 工程定義 — 15 工程構造

> **正本**: [HELIX-workflows/HELIX-process-L0-L14.md](../../../HELIX-workflows/HELIX-process-L0-L14.md) (ユーザー提示)
> **本 doc** は HELIX-workflows を実装文書として整理し、Gate / アンチパターン / 関連 skill / 旧体系移行 note を追補する。本文は HELIX-workflows に従う。

## 基本構造

工程 (process) を起点とする。設計フェーズ (V 字 左腕) で **設計と対応するテスト設計を同時にペア凍結**、L7 (谷) で実装、検証フェーズ (右腕) で左腕のテスト設計を実行・検証する。

**L7 は実装工程内の機能 PLAN (`L7-<機能名>plan` × N) を抱える上位概念**。L7 工程表が **実装する機能の順番** を定義し、各 `L7-<機能名>plan` が 1 機能の実装手順書になる (L7 内全機能の実装進捗を L7 が管理)。**PLAN は全工程 (L0-L14) で機能 (ドキュメント) 単位に起票**し、ある工程から次の工程へ進むために「どのドキュメントを・どの順番で・どんな手順を踏んで作るか」を **工程表として定義**する。各工程 PLAN は `process_layer` ごとに独立し、L7 は他工程の PLAN の親ではない。PLAN は **工程表 (進捗) + 実装計画** の両方を内蔵し、作業が中断してもどこまで進んだかを再開可能にする。

```
                                                       L0 企画書
                                                          │
[左腕：設計＋テスト設計ペア凍結]              [右腕：検証・運用]
  L1 要求定義 / 運用テスト設計  ───────────────  L14 運用検証 / 機能改善
   L2 画面設計・フロントUI / ワイヤーモック作成 ──  L10 フロントUX・ビジネスデザイン磨き上げ
    L3 要件定義 / 受け入れテスト設計 ────────────  L12 デプロイ / 受入テスト / 環境差異巻き取り
     L4 基本設計 / 総合テスト設計 ──────────────  L9 総合テスト / 依存関係解消
      L5 詳細設計 / 結合テスト設計 ─────────────  L8 結合テスト / 依存関係解消
       L6 機能設計 / 単体テスト設計 ───────────  （単体テストは L7 内で実施）
                          \                    /
                       [谷] L7 テスト実装 → 本体実装 → 3点レビュー
                            → テストパターン追加 → テスト実施 → 修正 / 実装完了
```

## 工程一覧 (L0-L14) + V-model ペア対応

| 層 | 区分 | 設計フェーズ | 対応するテスト設計 / テスト | V-model ペア |
|---|---|---|---|---|
| **L0** | 起点 | 企画書 | — | (L11 最終突合) |
| **L1** | 左腕 | 要求定義 | 運用テスト設計 | **↔ L14** |
| **L2** | 左腕 | 画面設計・フロントUI | ワイヤーモック作成 | **↔ L10** |
| **L3** | 左腕 | 要件定義 | 受け入れテスト設計 | **↔ L12** |
| **L4** | 左腕 | 基本設計 (外部設計) | 総合テスト設計 | **↔ L9** |
| **L5** | 左腕 | 詳細設計 (内部設計) | 結合テスト設計 | **↔ L8** |
| **L6** | 左腕 | 機能設計 | 単体テスト設計 | **↔ L7 内 単体テスト** |
| **L7** | 谷 | テスト実装 → 本体実装 → 3 点レビュー → テスト追加 → テスト実施 → 修正/完了 | (単体テスト実行を内包) | (上位概念) |
| **L8** | 右腕 | 結合テスト | 依存関係解消 | (L5 設計を実行) |
| **L9** | 右腕 | 総合テスト | 依存関係解消 | (L4 設計を実行) |
| **L10** | 右腕 | フロントデザインUX・ビジネスデザイン磨き上げ | — | (L2 ワイヤーモック磨き) |
| **L11** | 右腕 | 総合レビュー | ユーザー検証 / 要件巻き取り | (L1/L3 最終突合) |
| **L12** | 右腕 | デプロイ | 受入テスト / 環境差異巻き取り | (L3 設計を実行) |
| **L13** | 右腕 | デプロイ後検証 | 実環境運用 | — |
| **L14** | 右腕 | 運用検証 | 機能改善 | (L1 設計を実行、次サイクル L0 フィードバック) |

## PLAN の位置づけ (重要訂正、2026-05-24)

### 役割

- **PLAN は機能 (ドキュメント) 単位で全工程 L0-L14 に起票する**
- PLAN は、ある工程から次の工程へ進む (例: L0 → L1) ために、**どのドキュメントを・どの順番で・どんな手順を踏んで作るか** を工程表として定義する
- 各ステップには作業種類を含む。例: Web 検索を挟む / GitHub を調査してから書く / TL レビューを入れる
- PLAN は **工程表 (進捗) と実装計画の両方を内蔵**。ドキュメント作成が途中で中断しても、どこまで進んだかを追跡し再開できる

### L7 との関係

- **L7 (実装工程) は L7 配下の機能実装 PLAN (`L7-<機能名>plan` × N) を抱える上位概念**。L7 内全機能 PLAN の進捗を L7 が管理する (他工程 PLAN の親ではない)
- **L7 の工程表**: 実装する機能の順番を定義
- **L7 における PLAN**: 機能の中身の実装手順書として起票

### 命名規則

PLAN 名称は工程プレフィックスを付ける。形式: `L<工程番号>-○○○plan`

- `○○○` はその PLAN が進める対象を表し、**工程によって変わる**
  - **L7 (実装工程)**: 機能名 (例: `L7-helix-workspace-mergeplan`)
  - **L7 以外 (ドキュメント作成工程)**: その工程で作成・遂行する対象 (機能名とは限らない)
- プレフィックスと `○○○` により、その PLAN が「どの工程の何を進めるものか」を識別する

### 配置

PLAN 起票のフォルダは工程ごとに **分離** する:

```
docs/plans/
├── L0/
│   └── L0-企画書plan.md
├── L1/
│   ├── L1-業務要求plan.md
│   ├── L1-機能要求plan.md
│   ├── L1-画面要求plan.md
│   ├── L1-技術要求plan.md
│   └── L1-非機能要求plan.md
├── L2/
│   ├── L2-画面一覧plan.md
│   ├── L2-画面遷移plan.md
│   ├── L2-ワイヤーフレームplan.md
│   └── L2-UI要素plan.md
├── L3/ L4/ L5/ L6/
├── L7/
│   └── L7-<機能名>plan.md
└── L8/ ... L14/
```

### 既存 PLAN (V1) の扱い — 参考扱い、製本にしない (2026-05-24 確立)

> **完全 V2 移行ポリシー**: 既存 V1 PLAN (`PLAN-NNN-slug`) は **参考プラン**として保持するのみ。**製本 (HELIX V2 の正本) にはしない**。製本したい場合は **新命名規則 `L<NN>-○○○plan` で新規書き直し**する。
>
> - **既存 V1 PLAN 223 件**: `docs/plans/legacy/` に隔離 (or frontmatter に `is_reference: true` / `status: legacy` で marking)
> - **retrofit (rename / 内容更新) は行わない**: V1 → V2 の機械 rename は前提が違うため意味がない。書き直す
> - **plan_validator / helix doctor の対象は V2 形式のみ**: V1 形式は legacy として skip
> - **新規 PLAN は V2 形式必須**: `docs/plans/L<NN>/L<NN>-○○○plan.md` + 新 frontmatter

## 各工程の PLAN 一覧 (HELIX-workflows 正本)

| 工程 | 起票する PLAN |
|---|---|
| **L0** | `L0-企画書plan` |
| **L1** | `L1-業務要求plan` / `L1-機能要求plan` / `L1-画面要求plan` / `L1-技術要求plan` / `L1-非機能要求plan` |
| **L2** | `L2-画面一覧plan` / `L2-画面遷移plan` / `L2-ワイヤーフレームplan` / `L2-UI要素plan` |
| **L3** | `L3-業務要件plan` / `L3-機能要件plan` / `L3-非機能要件plan` |
| **L4** | `L4-方式設計plan` / `L4-機能設計plan` / `L4-画面設計plan` / `L4-データ設計plan` / `L4-外部IF設計plan` |
| **L5** | `L5-内部処理設計plan` / `L5-モジュール分割plan` / `L5-物理データ設計plan` / `L5-IF詳細設計plan` |
| **L6** | `L6-関数仕様plan` / `L6-クラス設計plan` / `L6-エッジケースplan` |
| **L7** | `L7-<機能名>plan` (機能ごとに起票) |
| **L8** | `L8-結合テストplan` / `L8-依存関係解消plan` |
| **L9** | `L9-総合テストplan` / `L9-依存関係解消plan` |
| **L10** | `L10-UX磨き上げplan` / `L10-ビジネスデザインplan` |
| **L11** | `L11-総合レビューplan` / `L11-ユーザー検証plan` / `L11-要件巻き取りplan` |
| **L12** | `L12-デプロイplan` / `L12-受入テストplan` / `L12-環境差異plan` |
| **L13** | `L13-デプロイ後検証plan` / `L13-実環境運用plan` |
| **L14** | `L14-運用検証plan` / `L14-機能改善plan` |

各 PLAN の記載項目は HELIX-workflows 配下の工程別 doc を正本とする (本 doc の §工程ごとの process doc を参照)。

## PLAN frontmatter 必須 field

```yaml
plan_id: L<NN>-<slug>plan       # 新命名規則 (例: L7-helix-workspace-mergeplan)
process_layer: L<NN>            # 該当工程 (L0-L14)
parent_process: HELIX-workflows/L<NN>-*.md  # 工程定義 doc への path
pairs_test_design:              # V-model ペア (L7 のみ必須、他工程は任意)
  - docs/v2/L<NN>-test-design/<feature>-test-design.md
kind: design | requirements | ui-design | impl | test | review | deployment | operation
status: draft | active | complete | blocked | abandoned
```

L7 (kind=impl) の場合は `parent_design:` 必須 (L6 機能設計 doc への path)。他工程は `parent_process:` 必須 (HELIX-workflows/L<NN>-*.md)。

PLAN.md 本文は **工程表 (作業手順 + 進捗) + 実装計画**。背景 / 要件 / 設計詳細は parent doc 群を参照、PLAN.md に重複転載しない。

## 工程ごとの process doc

| 工程 | 本 doc | 正本 (HELIX-workflows) | ペア |
|---|---|---|---|
| L0 企画書 | [L00-planning.md](L00-planning.md) | [L0-concept.md](../../../HELIX-workflows/helix-process/L0-concept.md) | — |
| L1 要求定義 + 運用テスト設計 | [L01-requirements-and-operational-test-design.md](L01-requirements-and-operational-test-design.md) | [L1-requirements.md](../../../HELIX-workflows/helix-process/L1-requirements.md) | L14 |
| L2 画面設計 + ワイヤーモック | [L02-screen-design-and-wireframe.md](L02-screen-design-and-wireframe.md) | [L2-ui-design.md](../../../HELIX-workflows/helix-process/L2-ui-design.md) | L10 |
| L3 要件定義 + 受入テスト設計 | [L03-requirements-definition-and-acceptance-test-design.md](L03-requirements-definition-and-acceptance-test-design.md) | [L3-requirements-definition.md](../../../HELIX-workflows/helix-process/L3-requirements-definition.md) | L12 |
| L4 基本設計 + 総合テスト設計 | [L04-architecture-design-and-system-test-design.md](L04-architecture-design-and-system-test-design.md) | [L4-basic-design.md](../../../HELIX-workflows/helix-process/L4-basic-design.md) | L9 |
| L5 詳細設計 + 結合テスト設計 | [L05-detailed-design-and-integration-test-design.md](L05-detailed-design-and-integration-test-design.md) | [L5-detailed-design.md](../../../HELIX-workflows/helix-process/L5-detailed-design.md) | L8 |
| L6 機能設計 + 単体テスト設計 | [L06-function-design-and-unit-test-design.md](L06-function-design-and-unit-test-design.md) | [L6-functional-design.md](../../../HELIX-workflows/helix-process/L6-functional-design.md) | L7 |
| L7 実装スプリント | [L07-implementation-sprint.md](L07-implementation-sprint.md) | [L7-implementation.md](../../../HELIX-workflows/helix-process/L7-implementation.md) | L6 |
| L8 結合テスト | [L08-integration-testing.md](L08-integration-testing.md) | [L8-integration-test.md](../../../HELIX-workflows/helix-process/L8-integration-test.md) | L5 |
| L9 総合テスト | [L09-system-testing.md](L09-system-testing.md) | [L9-system-test.md](../../../HELIX-workflows/helix-process/L9-system-test.md) | L4 |
| L10 フロント UX 磨き上げ | [L10-frontend-ux-polish.md](L10-frontend-ux-polish.md) | [L10-ux-refinement.md](../../../HELIX-workflows/helix-process/L10-ux-refinement.md) | L2 |
| L11 総合レビュー + ユーザー検証 | [L11-review-and-user-validation.md](L11-review-and-user-validation.md) | [L11-final-review.md](../../../HELIX-workflows/helix-process/L11-final-review.md) | L1/L3 最終突合 |
| L12 デプロイ + 受入テスト | [L12-deployment-and-acceptance-test.md](L12-deployment-and-acceptance-test.md) | [L12-deployment.md](../../../HELIX-workflows/helix-process/L12-deployment.md) | L3 |
| L13 デプロイ後検証 + 実環境運用 | [L13-post-deployment-verification.md](L13-post-deployment-verification.md) | [L13-post-deployment-verification.md](../../../HELIX-workflows/helix-process/L13-post-deployment-verification.md) | — |
| L14 運用検証 + 機能改善 | [L14-operations-and-improvement.md](L14-operations-and-improvement.md) | [L14-operation-verification.md](../../../HELIX-workflows/helix-process/L14-operation-verification.md) | L1 |

## 既存資産との関係 (移行)

### 旧 L1-L11 から新 L0-L14 への対応

| 旧 (L1-L11) | 新 (L0-L14) | 備考 |
|---|---|---|
| L1 要件定義 | **L1** 要求定義 + **L3** 要件定義 に分割 | 業務要求 ↔ システム要件で 2 段階 |
| L2 全体設計 | **L4** 基本設計 | (L2 は画面設計に再割当) |
| L3 詳細設計 | **L5** 詳細設計 + **L6** 機能設計 に分割 | 詳細 ↔ 機能で 2 段階 |
| L4 実装 | **L7** 実装スプリント | 3 点レビュー (設計⇔テスト⇔実装) 構造を追加 |
| L5 Visual Refinement | **L2** 画面設計 (前段) + **L10** UX 磨き (後段) | 画面設計を上流に、磨きを下流に分割 |
| L6 統合検証 | **L8** 結合テスト + **L9** 総合テスト + **L11** レビュー に分割 | 検証粒度で 3 段階 |
| L7 デプロイ | **L12** デプロイ | — |
| L8 受入 | **L12** 受入テスト | (L12 でデプロイと統合) |
| L9 デプロイ検証 | **L13** デプロイ後検証 | — |
| L10 観測 | **L13/L14** に統合 | — |
| L11 運用学習 | **L14** 運用検証 + 機能改善 | — |

### 既存設計 doc / PLAN の扱い — 参考扱いで隔離、書き直しで V2 製本

> **完全 V2 移行ポリシー (2026-05-24)**: 既存 V1 資産は参考扱い、製本は V2 で書き直す。

- `docs/v2/L1-REQUIREMENTS.md` → 参考保持。製本したい部分は新 `docs/v2/L1-requirements/` + 新 `docs/v2/L3-requirements-definition/` で書き直し (carry)
- `docs/v2/L2-MASTER.md` → 参考保持。製本したい部分は新 `docs/v2/L4-basic-design/` で書き直し (carry)
- `docs/v2/L3-detailed-design/{D-API,D-DB,D-CONTRACT}/` → 参考保持。製本は新 `docs/v2/L5-detailed-design/` + 新 `docs/v2/L6-function-design/` で書き直し (carry)
- `docs/v2/L4-test-design/` → 参考保持。製本は新 `docs/v2/L<NN>-test-design/` (NN=7,8,9,12,14) に分散書き直し (carry)
- 既存 PLAN-001〜PLAN-225 → **参考扱い、製本にしない**。`docs/plans/legacy/` 隔離 or `is_reference: true` marking (carry)

### 既存 skills/SKILL_MAP.md との同期 carry

- `SKILL_MAP.md §オーケストレーションフロー` の「PLAN は L7 のみ」前提を「PLAN は全工程で起票、L7 は上位概念」に訂正 (carry)
- `helix/HELIX_CORE.md` の同様訂正 (carry)
- `gate-policy.md` の G1〜G11 → G0-G14 再採番 (carry)

## 改革のポイント (HELIX-workflows 正本反映後)

1. **PLAN は全工程で起票** (L0-L14 各工程に PLAN を立て、工程ごとのドキュメント作成手順 + 進捗を管理)
2. **L7 は PLAN の上位概念** (機能ごとの実装 PLAN を束ね、全体進捗管理)
3. **PLAN 命名規則** `L<NN>-○○○plan` (工程プレフィックス + 対象)
4. **PLAN 配置のフォルダ分離** (`docs/plans/L0/` 〜 `docs/plans/L14/`)
5. **PLAN は工程表 + 実装計画の 2 要素内蔵** (作業手順 + 進捗で再開可能)
6. **設計とテスト設計をペア凍結** (V-model 左右同時進行、各設計工程の成果物にペアとなるテスト設計が必須)
7. **L7 実装スプリント内で 3 点レビュー** (設計 ⇔ テスト ⇔ 実装の三位一体)
8. **plan_validator で命名規則 + 工程 + kind を検証** (warn-only P1、retrofit 完了後 P3 fail-close)
