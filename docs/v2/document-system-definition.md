---
doc_id: v2-document-system-definition
title: HELIX-workflows V2 L単位ドキュメント体系定義
status: frozen
created: 2026-05-30
frozen_date: 2026-05-30
owner: PM
parent: docs/v2/process/README.md
related_sources:
  - HELIX-workflows/helix-process/L3-requirements-definition.md
  - HELIX-workflows/helix-process/L4-basic-design.md
  - HELIX-workflows/helix-process/L5-detailed-design.md
  - HELIX-workflows/helix-process/L6-functional-design.md
  - HELIX-workflows/helix-process/L7-implementation.md
  - HELIX-workflows/HELIX-process-L0-L14.md
  - skills/workflow/doc-system-architect/references/design-coverage-baseline.md
  - docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md
  - docs/v2/L3-requirements/helix-workflows-functional-registry.md
---

# HELIX-workflows V2 L単位ドキュメント体系定義

## §1 適用工程

HELIX-workflows V2 は CLI / フレームワーク寄りの `drive=be` 系であり、適用 L は `L0 / L1 / L3 / L4 / L5 / L6`、テスト設計は `L7 / L8 / L9`、運用・受入は `L12 / L14` とする。

| 層 | 適用 | 理由 |
|---|---|---|
| L0 | 適用 | 全体の SSoT と glossary / principles の起点のため |
| L1 | 適用 | 機能要求・技術要求の関所であり、下流設計の入力になるため |
| L2 | 最小 | CLI 中心のため画面設計は原則不要。必要時のみ wireframe 相当の N/A 宣言 doc を置く |
| L3 | 適用 | FR / NFR を確定し、L4 以降の唯一入力にするため |
| L4 | 適用 | 外部視点の基本設計を固定するため |
| L5 | 適用 | 内部構造・IF・物理データを固定するため |
| L6 | 適用 | 実装直前粒度の関数・クラス・境界ケースを固定するため |
| L7 | 適用 | L6 に対応する単体テスト設計・実装の谷であるため |
| L8 | 適用 | L5 に対応する結合テスト設計・実行の右腕であるため |
| L9 | 適用 | L4 に対応する総合テスト設計・実行の右腕であるため |
| L10 | skip | CLI 中心で UX 磨き上げの主要対象がないため |
| L12 | 適用 | 受入テストと環境差異巻き取りの右腕であるため |
| L14 | 適用 | 運用検証と機能改善の終端であり、L1 の運用要求を回収するため |

## §2 L単位 成果物マップ

| L | 工程 | 必須doc(ファイル名) | 生成PLAN(Lx-○○plan) | 粒度 | SSoT | V-model pair テスト設計doc | coverage-baseline ID |
|---|---|---|---|---|---|---|---|
| L0 | 企画書 | `concept.md` | `L0-企画書plan` | 目的・背景・価値・制約 | `HELIX-workflows/HELIX-process-L0-L14.md` | 要PM確定 | 要PM確定 |
| L1 | 要求定義 | `L1-requirements.md` | `L1-要求定義plan` | 要求の確定と下流入力化 | `HELIX-workflows/HELIX-process-L0-L14.md` | 運用テスト設計 | 要PM確定 |
| L2 | 画面設計 | `L2-ui-design.md` | `L2-画面設計plan` | 最小 / 原則 N/A | `HELIX-workflows/HELIX-process-L0-L14.md` | UX 期待 / a11y チェック | 要PM確定 |
| L3 | 要件定義 | `L3-requirements-definition.md` | `L3-要件定義plan` | FR / NFR / 受入条件 | `HELIX-workflows/HELIX-process-L0-L14.md` | 受入テスト設計 | 要PM確定 |
| L4 | 基本設計 | `L4-basic-design.md` | `L4-方式設計plan` / `L4-機能設計plan` / `L4-データ設計plan` / `L4-外部IF設計plan` | 外部視点の概要 | `HELIX-workflows/HELIX-process-L0-L14.md` | 総合テスト設計 | L4-01〜L4-09 |
| L5 | 詳細設計 | `L5-detailed-design.md` | `L5-内部処理設計plan` / `L5-モジュール分割plan` / `L5-物理データ設計plan` / `L5-IF詳細設計plan` | 内部視点の詳細 | `HELIX-workflows/HELIX-process-L0-L14.md` | 結合テスト設計 | L5-01〜L5-09 |
| L6 | 機能設計 | `L6-functional-design.md` | `L6-関数仕様plan` / `L6-クラス設計plan` / `L6-エッジケースplan` | 実装直前粒度 | `HELIX-workflows/HELIX-process-L0-L14.md` | 単体テスト設計 | L6-01〜L6-05 |
| L7 | 実装 | `L7-<機能名>plan` | `L7-<機能名>plan` | 機能単位の実装手順 | `HELIX-workflows/HELIX-process-L0-L14.md` | L6 由来の単体テスト | L7 実装ゲート |
| L8 | 結合テスト | `L8-結合テストplan` | `L8-結合テストplan` | モジュール結合検証 | `HELIX-workflows/HELIX-process-L0-L14.md` | L5 由来の結合テスト | L8 実行ゲート |
| L9 | 総合テスト | `L9-総合テストplan` | `L9-総合テストplan` | システム総合検証 | `HELIX-workflows/HELIX-process-L0-L14.md` | L4 由来の総合テスト | L9 実行ゲート |
| L12 | デプロイ・受入 | `L12-デプロイplan` | `L12-デプロイplan` | 受入と環境差異巻き取り | `HELIX-workflows/HELIX-process-L0-L14.md` | L3 由来の受入テスト | 要PM確定 |
| L14 | 運用検証 | `L14-運用検証plan` | `L14-運用検証plan` | 運用観測と改善 | `HELIX-workflows/HELIX-process-L0-L14.md` | L1 由来の運用テスト | 要PM確定 |

## §3 L4機能設計 vs L6機能設計の境界

L4 の機能設計は、機能構成と機能間連携の概要だけを書く。書くのはシステム視点での配置、責務分担、接続関係までであり、機能本体の詳細ロジックは書かない。

L6 の機能設計は、機能ごとの関数仕様、クラス設計、エッジケースを書く。ここが実装直前粒度であり、単体テストと 1:1 で対になる。

削除済み `functional-design.md` が 1704 行相当の機能本体 `F1-F10` を L4 に詰め込んだのは逸脱例であり、今後の禁止事項とする。L4 は概要、L6 は実装直前粒度という分離を崩さない。

## §4 機能単位の母集団

L6 フォルダ配下の機能単位は、`docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md` と `docs/v2/L3-requirements/helix-workflows-functional-registry.md` を SSoT とし、FR 単位で列挙する。

### 4.1 コード資産 bucket

`CLI 80 / lib 139 / hook 17 / agent 19 = 255` は **関数仕様必須** とする。実装直前粒度で個別の function / class / edge case に落とし込む。

### 4.2 registry-only bucket

`skill 130 + workflow 49 + template 114 = 293` は **registry-only** とする。単体テスト pair は免除し、L3 registry と資産 inventory で追跡する。

### 4.3 FR 単位一覧

| FR-ID | 機能名 | bucket | L6 配置方針 |
|---|---|---|---|
| FR-NSM-01 | NSM 計測・整合スコア機能 | code | `docs/v2/L6-functional-design/FR-NSM-01/` |
| FR-GR-01 | Guardrail fail-close 機能 | code | `docs/v2/L6-functional-design/FR-GR-01/` |
| FR-TDD-01 | TDD 順序強制機能 | code | `docs/v2/L6-functional-design/FR-TDD-01/` |
| FR-9MODE-01 | 9 mode 入口判定機能 | code | `docs/v2/L6-functional-design/FR-9MODE-01/` |
| FR-GATE-01 | gate 合成判定機能 | code | `docs/v2/L6-functional-design/FR-GATE-01/` |
| FR-IMPACT-01 | 影響範囲 query 機能 | code | `docs/v2/L6-functional-design/FR-IMPACT-01/` |
| FR-EVT-01 | Forward 復帰 event 機能 | code | `docs/v2/L6-functional-design/FR-EVT-01/` |
| FR-4ART-01 | 4 artifact / pair freeze 監査機能 | code | `docs/v2/L6-functional-design/FR-4ART-01/` |
| FR-INV-01 | 資産 inventory / density 可視化機能 | code | `docs/v2/L6-functional-design/FR-INV-01/` |
| FR-CTX-01 | layer context injection 機能 | code | `docs/v2/L6-functional-design/FR-CTX-01/` |
| FR-DRIFT-01 | discrepancy routing 機能 | code | `docs/v2/L6-functional-design/FR-DRIFT-01/` |
| FR-PLAN-01 | PLAN dependency / generates trace 機能 | code | `docs/v2/L6-functional-design/FR-PLAN-01/` |
| FR-DOCTOR-01 | doctor 総合監査機能 | code | `docs/v2/L6-functional-design/FR-DOCTOR-01/` |
| FR-MIGR-01 | schema migration / retrofit 機能 | code | `docs/v2/L6-functional-design/FR-MIGR-01/` |
| FR-DOCREVIEW-01 | ドキュメント品質レビュー機能 | code | `docs/v2/L6-functional-design/FR-DOCREVIEW-01/` |
| FR-CHANGEPROP-01 | 変更追跡 + デグレ禁止 ratchet 機能 | code | `docs/v2/L6-functional-design/FR-CHANGEPROP-01/` |
| FR-FNREG-01 | 機能一覧 SSoT + 自動チェック機能 | registry-only | (注1) L4 carry 完了後に再評価 |
| FR-GLOSSARY-01 | ドメイン用語 SSoT + 自動チェック機能 | registry-only | (注1) L4 carry 完了後に再評価 |

> **bucket 確定 (2026-05-30、registry 照合済)**: code 16 件 / registry-only 2 件。当初 registry-only 判定だった FR-NSM-01 / FR-INV-01 / FR-DOCTOR-01 / FR-MIGR-01 / FR-DOCREVIEW-01 / FR-CHANGEPROP-01 の 6 件は、CLI binary / cli/lib モジュール / hook / agent の実装コードが registry §11 に実在する (完全実装〜部分実装) ため **code** に確定。
> **(注1)** FR-FNREG-01 / FR-GLOSSARY-01 は専用コード資産 0 件 (yaml / check CLI 未実装、L4 carry)。実装が無い段階で関数仕様 doc を作ると trace が破綻するため registry-only を維持し、L4 carry (yaml 化 + check CLI) 完了後に code 昇格を再評価する。

## §5 frontmatter contract

双方向 trace に必要な frontmatter フィールドを以下に固定する。

### 5.1 設計doc

必須 field: `doc_id / process_layer / parent_plan / pairs_test_design`

```yaml
doc_id: v2-document-system-definition
process_layer: L4
parent_plan: L4-方式設計plan
pairs_test_design: docs/v2/L9-test-design/L4-architecture-system-test-design.md
```

### 5.2 関数仕様doc

必須 field: `asset_id / asset_path / parent_concept / pairs_test_design / test_case_prefix / bucket`

```yaml
asset_id: FR-GATE-01
asset_path: cli/lib/gate_policy.py
parent_concept: gate 合成判定機能
pairs_test_design: docs/v2/L7-test-design/FR-GATE-01-unit-test-design.md
test_case_prefix: U-GATE-
bucket: code
```

### 5.3 テスト設計doc

必須 field: `parent_design / pairs_design`

```yaml
parent_design: docs/v2/L6-functional-design/FR-GATE-01/function-spec.md
pairs_design: docs/v2/L6-functional-design/FR-GATE-01
```

## §6 ファイル命名・配置規約

### 6.1 配置

- `docs/v2/L4-basic-design/`
- `docs/v2/L5-detailed-design/`
- `docs/v2/L6-functional-design/`
- `docs/v2/L7-test-design/`
- `docs/v2/L8-test-design/`
- `docs/v2/L9-test-design/`

### 6.2 命名

- L4: `L4-方式設計plan.md` など、工程名と対象を一致させる
- L5: `L5-内部処理設計plan.md` など、工程名と対象を一致させる
- L6: `FR-<ID>/function-spec.md`、`FR-<ID>/class-design.md`、`FR-<ID>/edge-cases.md`
- テスト設計: `FR-<ID>-unit-test-design.md` など、`pairs_design` との対応を明示する

### 6.3 逸脱禁止

- 生物学 metaphor は完全廃止
- `F1-F10` 由来の命名は使わない
- FR 番号は registry の ID を優先し、ローカル独自番号を増やさない

## §7 helix doctor 量閉じ lint 候補

Phase 1 は advisory、Phase 2 は fail-close とする。

### 7.1 候補 lint

- 各設計 doc に pair が存在すること
- 逆向き参照が整合していること
- `asset_id` が registry に存在すること
- `coverage-baseline` の必須 ID を満たすこと

### 7.2 判定順

1. `pairs_test_design` / `pairs_design` の存在確認
2. 逆向き参照の一致確認
3. `asset_id` と FR registry の照合
4. coverage-baseline ID の充足確認
5. Phase 2 で fail-close

### 7.3 要PM確定

- L0 / L1 / L2 / L3 / L12 / L14 の coverage-baseline ID は正本に明記されていないため、現時点では `要PM確定`
- L6 配下の機能ごとの file path の最終命名も、個別 registry との同期が必要なため `要PM確定`

