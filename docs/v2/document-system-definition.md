---
doc_id: v2-document-system-definition
title: HELIX-workflows V2 L単位ドキュメント体系定義
status: frozen
created: 2026-05-30
frozen_date: 2026-05-31
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

### 表1 工程定義 SSoT

| L | 工程 | SSoT |
|---|---|---|
| L0 | 企画書 | `HELIX-workflows/helix-process/L0-concept.md` |
| L1 | 要求定義 | `HELIX-workflows/helix-process/L1-requirements.md` |
| L2 | 画面設計 | `HELIX-workflows/helix-process/screen-design-workflow.md` |
| L3 | 要件定義 | `HELIX-workflows/helix-process/L3-requirements-definition.md` |
| L4 | 基本設計 | `HELIX-workflows/helix-process/L4-basic-design.md` |
| L5 | 詳細設計 | `HELIX-workflows/helix-process/L5-detailed-design.md` |
| L6 | 機能設計 | `HELIX-workflows/helix-process/L6-functional-design.md` |
| L7 | 実装 | `HELIX-workflows/helix-process/L7-implementation.md` |
| L8 | 結合テスト | `HELIX-workflows/helix-process/L8-integration-test.md` |
| L9 | 総合テスト | `HELIX-workflows/helix-process/L9-system-test.md` |
| L12 | デプロイ・受入 | `HELIX-workflows/helix-process/L12-deployment.md` |
| L14 | 運用検証 | `HELIX-workflows/helix-process/L14-operation-verification.md` |

### 表2 成果物生成

| 生成PLAN | generates 設計doc | pair テスト設計doc |
|---|---|---|
| `docs/plans/L4/L4-helix-workflows-方式設計plan.md` | `docs/v2/L4-basic-design/方式設計.md` | `docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md` |
| `docs/plans/L4/L4-helix-workflows-機能構成設計plan.md` | `docs/v2/L4-basic-design/機能構成設計.md` | `docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md` |
| `docs/plans/L4/L4-helix-workflows-データ設計plan.md` | `docs/v2/L4-basic-design/データ設計.md` | `docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md` |
| `docs/plans/L4/L4-helix-workflows-外部IF設計plan.md` | `docs/v2/L4-basic-design/外部IF設計.md` | `docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md` |
| `docs/plans/L5/L5-helix-workflows-内部処理設計plan.md` | `docs/v2/L5-detailed-design/内部処理設計.md` | `docs/v2/L8-test-design/L5-detailed-design-結合テスト設計.md` |
| `docs/plans/L5/L5-helix-workflows-モジュール分割設計plan.md` | `docs/v2/L5-detailed-design/モジュール分割設計.md` | `docs/v2/L8-test-design/L5-detailed-design-結合テスト設計.md` |
| `docs/plans/L5/L5-helix-workflows-物理データ設計plan.md` | `docs/v2/L5-detailed-design/物理データ設計.md` | `docs/v2/L8-test-design/L5-detailed-design-結合テスト設計.md` |
| `docs/plans/L5/L5-helix-workflows-IF詳細設計plan.md` | `docs/v2/L5-detailed-design/IF詳細設計.md` | `docs/v2/L8-test-design/L5-detailed-design-結合テスト設計.md` |
| `docs/plans/L6/L6-helix-workflows-関数仕様plan.md` | `docs/v2/L6-functional-design/FR-XXX/function-spec.md` | `docs/v2/L7-test-design/FR-XXX/unit-test-design.md` |
| `docs/plans/L6/L6-helix-workflows-クラス設計plan.md` | `docs/v2/L6-functional-design/FR-XXX/class-design.md` | `docs/v2/L7-test-design/FR-XXX/unit-test-design.md` |
| `docs/plans/L6/L6-helix-workflows-エッジケースplan.md` | `docs/v2/L6-functional-design/FR-XXX/edge-cases.md` | `docs/v2/L7-test-design/FR-XXX/unit-test-design.md` |

L2 画面設計 plan は `N/A: L2最小・UI対象なし` と明示し、無言削除しない。
L6 は `docs/v2/L6-functional-design/FR-XXX/index.md` を bundle manifest とし、`function-spec.md` / `class-design.md` / `edge-cases.md` を generates する。

### 表3 V-model pair

| 設計doc | テスト設計doc | 実行層 |
|---|---|---|
| `docs/v2/L4-basic-design/方式設計.md` | `docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md` | L9 |
| `docs/v2/L4-basic-design/機能構成設計.md` | `docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md` | L9 |
| `docs/v2/L4-basic-design/データ設計.md` | `docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md` | L9 |
| `docs/v2/L4-basic-design/外部IF設計.md` | `docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md` | L9 |
| `docs/v2/L5-detailed-design/内部処理設計.md` | `docs/v2/L8-test-design/L5-detailed-design-結合テスト設計.md` | L8 |
| `docs/v2/L5-detailed-design/モジュール分割設計.md` | `docs/v2/L8-test-design/L5-detailed-design-結合テスト設計.md` | L8 |
| `docs/v2/L5-detailed-design/物理データ設計.md` | `docs/v2/L8-test-design/L5-detailed-design-結合テスト設計.md` | L8 |
| `docs/v2/L5-detailed-design/IF詳細設計.md` | `docs/v2/L8-test-design/L5-detailed-design-結合テスト設計.md` | L8 |
| `docs/v2/L6-functional-design/FR-XXX/function-spec.md` | `docs/v2/L7-test-design/FR-XXX/unit-test-design.md` | L7 |
| `docs/v2/L6-functional-design/FR-XXX/class-design.md` | `docs/v2/L7-test-design/FR-XXX/unit-test-design.md` | L7 |
| `docs/v2/L6-functional-design/FR-XXX/edge-cases.md` | `docs/v2/L7-test-design/FR-XXX/unit-test-design.md` | L7 |

## §3 L4機能設計 vs L6機能設計の境界

L4 の「機能構成設計」は、機能構成と機能間連携の概要だけを書く。書くのはシステム視点での配置、責務分担、接続関係までであり、機能本体の詳細ロジックは書かない。

L6 の機能設計は、機能ごとの関数仕様、クラス設計、エッジケースを書く。ここが実装直前粒度であり、単体テストと 1:1 で対になる。

削除済み `functional-design.md` が 1704 行相当の機能本体 `F1-F10` を L4 に詰め込んだのは逸脱例であり、今後の禁止事項とする。L4 は概要、L6 は実装直前粒度という分離を崩さない。

## §4 機能単位の母集団

L6 フォルダ配下の機能単位は、`docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md` と `docs/v2/L3-requirements/helix-workflows-functional-registry.md` を SSoT とし、FR 単位で列挙する。

### 4.1 コード資産 bucket

`CLI 80 / lib 139 / hook 17 / agent 19 = 255` は **関数仕様必須** とする。実装直前粒度で個別の function / class / edge case に落とし込む。

### 4.2 registry-only bucket

`skill 130 + workflow 49 + template 114 = 293` は **registry-only** とする。単体テスト pair は免除し、L3 registry と資産 inventory で追跡する。

### 4.3 L6 折衷案

L6 PLAN は正本どおり 3 本固定とする。`function-spec` / `class-design` / `edge-cases` を FR 単位 bundle に生成するが、FR 単位 PLAN 16 本へ増やさない。正本衝突を避けるため、この 3 PLAN は `docs/v2/L6-functional-design/FR-XXX/` の bundle manifest と pair テスト設計を生成する役割に限定する。

### 4.4 FR 単位一覧

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
parent_plan: docs/plans/L4/L4-helix-workflows-方式設計plan.md
pairs_test_design: docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md
```

### 5.2 関数仕様doc

必須 field: `asset_id / asset_path / parent_concept / pairs_test_design / test_case_prefix / bucket`

```yaml
asset_id: FR-GATE-01
asset_path: cli/lib/gate_policy.py
parent_concept: gate 合成判定機能
pairs_test_design: docs/v2/L7-test-design/FR-GATE-01/unit-test-design.md
test_case_prefix: U-GATE-
bucket: code
```

### 5.3 テスト設計doc

必須 field: `parent_design / pairs_design`

```yaml
parent_design: docs/v2/L6-functional-design/FR-GATE-01/function-spec.md
pairs_design: docs/v2/L6-functional-design/FR-GATE-01/
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

- PLAN: `docs/plans/Lx/Lx-helix-workflows-<対象>plan.md`
- 生成doc: `docs/v2/Lx-<layer>/<doc-name>.md`
- 生成doc名に `plan` を入れない。PLAN 名を生成doc名へ流用しない
- L4 生成doc: `方式設計.md` / `機能構成設計.md` / `データ設計.md` / `外部IF設計.md`
- L5 生成doc: `内部処理設計.md` / `モジュール分割設計.md` / `物理データ設計.md` / `IF詳細設計.md`
- L6 生成doc: `FR-<ID>/function-spec.md` / `class-design.md` / `edge-cases.md` / `index.md`
- L7: `docs/v2/L7-test-design/FR-XXX/unit-test-design.md`
- L8: `docs/v2/L8-test-design/<L5-doc-stem>-結合テスト設計.md`
- L9: `docs/v2/L9-test-design/<L4-doc-stem>-総合テスト設計.md`
- frontmatter `parent_plan` は PLAN stem または plan_path で実在 PLAN に解決可能であること
- frontmatter `pairs_design` は `docs/v2/L6-functional-design/FR-XXX/` の bundle manifest を指すこと

### 6.3 逸脱禁止

- 生物学 metaphor は完全廃止
- `F1-F10` 由来の命名は使わない
- FR 番号は registry の ID を優先し、ローカル独自番号を増やさない

## §7 helix doctor 量閉じ lint 候補

Phase 1 は advisory、Phase 2 は fail-close とする。

### 7.1 候補 lint

- 生成doc名に `plan` が含まれないこと
- `parent_plan` / `plan_path` が `docs/plans/Lx/` に実在すること
- 各 PLAN の `generates` が実在 doc に解決すること
- L6 code FR 16 件は `function-spec` / `class-design` / `edge-cases` / `unit-test-design` を持つこと
- registry-only FR は免除理由を持つこと
- `pairs_test_design` と `parent_design` の逆参照が一致すること

### 7.2 判定順

1. `pairs_test_design` / `pairs_design` の存在確認
2. 逆向き参照の一致確認
3. `asset_id` と FR registry の照合
4. coverage-baseline ID の充足確認
5. Phase 2 で fail-close

### 7.3 要PM確定

- L0 / L1 / L2 / L3 / L12 / L14 の coverage-baseline ID は正本に明記されていないため、現時点では `要PM確定`
- L6 配下の機能ごとの file path の最終命名も、個別 registry との同期が必要なため `要PM確定`

## §8 残リスク・carry

`docs/v2/process/` 配下に旧 `PLAN は L7 のみ` 記述が残る可能性がある。これは再 drift 源になりうるため、次段で process doc の整合レビューを carry として実施すること。
