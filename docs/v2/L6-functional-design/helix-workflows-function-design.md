---
doc_id: L6-functional-design-helix-workflows
title: HELIX-workflows V2 機能設計（関数仕様 / DbC）
status: frozen
freeze_evidence: "2026-06-03 V-model pair-freeze (L6↔L7): FN-* 14 を DbC (requires/ensures/invariant) で定義し L7 UT-* と 1:1、trace_symmetry detector で coverage100%/uncovered0/orphan0/missing-pair0/wrong_layer_pair0/balance1.0、tl-advisor adversarial check (P1 wrong_layer_pair=parent_design→upstream_design 修正済 / P2 FN-CONTRACT invariant 補完済)、Reverse 源泉 unit テスト実在確認 / 2026-06-03 Phase2 総合見直し (whole-coverage audit, tl-advisor changes_required[P1×2]+pmo 事実監査): 観測契約 subset freeze と確認し universe 分類(§5.1)+粒度 caveat(§5.2 DF-WCAUDIT-L6L7-002)を明示して freeze 範囲を honest 化、実設計 expansion は Phase3 L7 へ defer (re-freeze=範囲宣言の明確化のみ、FN-*/UT-*/DbC の design 変更なし・detector green 不変)"
owner: SE
process_layer: L6
pairs_test_design: docs/v2/L7-test-design/helix-workflows-unit-test-design.md
upstream_design:
  - docs/v2/L5-detailed-design/モジュール分割設計.md
  - docs/v2/L5-detailed-design/内部処理設計.md
related_requirements:
  - docs/v2/L3-requirements/helix-workflows-functional-registry.md
related_decision: docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
---

# 機能設計（関数仕様 / Design by Contract）

> 本書は L5 詳細設計（モジュール `MOD-*` / 内部処理 `IP-*`）を **関数 / 公開契約粒度**へ落とす L6 正本。HELIX-workflows は稼働中システムのため、各 `FN-*` は **観測済 public contract（既存 unit テストが realize しているふるまい）から Reverse** で起こし、`requires / ensures / invariant`（DbC）を実装と既存テストから推定可能な範囲で固定する。各 `FN-*` は L7 単体テスト設計の `UT-*` と **1:1 で対**になる（単体粒度ペアリング: 関数 / 公開契約 1 個 = 単体テスト 1 個）。

## 1. 目的と範囲

- **目的**: 主要 public 関数 / API の入出力契約と不変条件を固定し、単体テスト（L7）の合格基準を与える。
- **範囲**: 観測済 public contract（既存 pytest が対象とする関数 / handler）。private helper の細分化や全 139 lib 関数の網羅は行わず、未観測は gap として残す（粒度爆発回避）。
- **対ペア**: L7 単体テスト設計 doc（`pairs_test_design` で相互宣言）。上位は L5 `MOD-*` / `IP-*`。

## 2. DbC 表記

- `requires`: 事前条件（呼出側が満たすべき入力 / 状態）。
- `ensures`: 事後条件（正常終了時の保証）。
- `invariant`: 実行を通じて保たれる制約（多くは fail-close / backward compatibility）。

## 3. 機能設計（FN-* 定義）

各 `FN-*` に安定 ID を付与する（L6↔L7 trace 用。L7 の `UT-*` はこの ID と 1:1 対）。`所属 MOD` は L5 モジュールへの trace-up。

| FN ID | 関数 / 公開契約 | 所属 MOD | requires | ensures | invariant |
|---|---|---|---|---|---|
| FN-ROUTE-01 | `RouteEngine.evaluate()`（signal→mode/kind/action 決定） | MOD-02 | signal / uncertainty / impact / env / drift_type | `mode/kind/subtype/priority/action` を持つ RouteResult | 不正 signal は `RouteEngineError` で fail-close |
| FN-PLAN-01 | `plan_validator` の frontmatter 検証 | MOD-02 | PLAN markdown path | 必須 field 抽出 + warning 群を返す | warn-only（gate 側が fail-close 昇格） |
| FN-HANDOVER-01 | handover resume / stale 判定 | MOD-02 | `CURRENT.json` 存在 | stale verdict + owner/status/phase 検査 | 不正 status 遷移を拒否 |
| FN-WS-01 | `workspace_manager` の merge | MOD-02 | main repo clean + workspace diff | patch 適用 + `workspace_registry.status=merged` | conflict 検出時は適用しない |
| FN-DB-01 | `helix_db` 接続 / CRUD helper | MOD-04 | schema_version 整合・WAL | row 永続化 + lock 取得 | 破壊的変更なし（additive 前提） |
| FN-DB-02 | additive migration（`v31`〜`v35`） | MOD-04 | 直前 schema_version | `schema_version` 更新 | backward compatible（逆方向依存なし） |
| FN-GUARD-01 | `context_guard` の context 検査 | MOD-03 | tool context 入力 | allow / block verdict | 必須 context 欠如で block |
| FN-GUARD-02 | `llm_guard`（raw LLM CLI guard） | MOD-03 | command 入力 | raw LLM CLI を block | bypass は evidence 必須 |
| FN-GUARD-03 | `agent_policy_guard`（role/model guard） | MOD-03 | agent / model 指定 | 許可 role/model のみ通過 | 不許可は fail-close（deny） |
| FN-HTTP-01 | HTTP route handler（push/pr trigger） | MOD-05 | `plan_id` + body 必須 field | `automation_runs` 記録 + envelope 返却 | localhost+bearer 必須・`trace_id` 返却 |
| FN-AUDIT-01 | `audit_log` 記録 / `audit_validator` | MOD-04 | audit payload | `audit_log` row 追記 | `run_id` 存在必須 |
| FN-CATALOG-01 | `code_catalog` 索引生成 | MOD-06 | code tree | `code_index` / `entries` 生成 | 索引は read-only source から導出 |
| FN-CONTRACT-01 | `contract_registry` 登録 / 照合 | MOD-06 | contract 定義 | `contract_entries` 整合 | 登録済 contract の entry/hash 整合を保つ（重複登録で破壊しない） |
| FN-AGENT-01 | `agent_slots` fire / release | MOD-07 | role / task | slot 記録（fire/release） | stale slot は release 可能 |

## 4. 合格基準（G6）

- 各 `FN-*` が `requires/ensures/invariant` を持ち、L7 の `UT-*` と 1:1 で対になる（trace_symmetry detector で L6↔L7 coverage 100% / uncovered 0 / orphan 0 / missing-pair 0）。
- DbC は実装と既存 unit テストから推定可能なもののみ固定し、不明な intent は L7 側で仮説として扱う。

## 5. カバレッジ universe と gap（観測契約 subset freeze の明示）

> 本書は **観測済 public contract subset の freeze** であり「HELIX 全機能（≈139 lib 関数）の機能設計 freeze」ではない。2026-06-03 Phase2 総合見直し（whole-coverage audit、tl-advisor + pmo 二重 audit）の P1 指摘を受け、universe を明示分類して freeze 範囲を honest にする（covered / excluded_with_reason / gap）。

### 5.1 universe 分類
| 区分 | 内容 | 件数 / 根拠 |
|---|---|---|
| **covered** | §3 の `FN-*` 14（L7 `UT-*` と 1:1、DbC 固定） | 14 |
| **excluded_with_reason** | private helper / 例外型の完全列挙 / option 単位 validation（粒度爆発回避）。builder / curator / dashboard 系の未観測 public（観測テスト不在で契約を起こせない） | 観測契約なし=対象外 |
| **gap（設計未定義・要追補）** | `code_catalog` / `contract_registry` / `doc_map_matcher` / `deliverable_gate` の内部実装設計。`FN-CATALOG-01` / `FN-CONTRACT-01` は公開契約を起こしたが背後モジュール群の内部設計は未定義。**L8 の `IT-MOD-06` / `IT-DB-03` / `IT-DB-05` 結合テスト gap と同根クラスタ**（[DF-WCAUDIT-L6L7-001](../L1-requirements/helix-workflows-verification-strategy.md)） | 4 module |

### 5.2 粒度 caveat（DF-WCAUDIT-L6L7-002）
- `FN-*` は Reverse 由来の **観測済公開契約 / 責務粒度**で起こしており、`FN-AGENT-01`（fire / release）`FN-CONTRACT-01`（登録 / 照合）`FN-DB-01`（接続 / CRUD）`FN-HANDOVER-01`（resume / stale）等は **1 FN に複数オペレーションを束ねている**。HELIX 粒度ペアリング原則の厳密形（関数 1 個 = UT 1 個 / callable・入力型・例外型を明示）から見ると粗い（`FN-ROUTE-01` のみ単一関数 `RouteEngine.evaluate()`）。
- 現状は「1 FN ↔ 1 UT」で内部整合し detector green だが、**厳密な単一関数分割と callable / error contract の明示は後続拡張（Phase3 L7 実装時に TDD で sharpening）へ defer**する。
- 後続拡張は FR 単位で `docs/v2/L6-functional-design/<FR>/` へ分割展開する。

## 6. 自己検証チェックリスト

- [ ] 全 `FN-*` が `requires/ensures/invariant` を持つ。
- [ ] 全 `FN-*` が L7 `UT-*` と 1:1 対応（detector で uncovered 0 / orphan 0）。
- [ ] `所属 MOD` が L5 モジュール分割設計の実在 ID を指す。
- [ ] §5.1 universe（covered / excluded_with_reason / gap）が宣言され、freeze 範囲が観測契約 subset であることが明示されている。
- [ ] §5.2 粒度 caveat（責務粒度・複数オペレーション束ね）と厳密分割の defer 先（Phase3）が記録されている。
