---
doc_id: L6-functional-design-helix-workflows
title: HELIX-workflows V2 機能設計（関数仕様 / DbC）
status: frozen
freeze_evidence: "2026-06-03 V-model pair-freeze (L6↔L7): FN-* 14 を DbC (requires/ensures/invariant) で定義し L7 UT-* と 1:1、trace_symmetry detector で coverage100%/uncovered0/orphan0/missing-pair0/wrong_layer_pair0/balance1.0、tl-advisor adversarial check (P1 wrong_layer_pair=parent_design→upstream_design 修正済 / P2 FN-CONTRACT invariant 補完済)、Reverse 源泉 unit テスト実在確認 / 2026-06-03 Phase2 総合見直し (whole-coverage audit, tl-advisor changes_required[P1×2]+pmo 事実監査): 観測契約 subset freeze と確認し universe 分類(§5.1)+粒度 caveat(§5.2 DF-WCAUDIT-L6L7-002)を明示して freeze 範囲を honest 化。2026-06-12 L1-L6 監査で FR18 追補を L6 仕様 + UT-CAND 索引として分割展開済み。L7 実装・単体テスト設計成果物・実行・coverage closure は未承認であり、進める場合は add-feature 承認を必要とする。"
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
- **範囲**: 観測済 public contract（既存 pytest が対象とする関数 / handler）と、2026-06-12 L1-L6 監査で L6_required と判定した FR18 追補仕様。private helper の細分化や全 139 lib 関数の無差別網羅は行わず、対象外は理由付き除外、L6_required は FR18 `function-spec.md` と `UT-CAND` へ展開済みとする。
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

## 5. カバレッジ universe と FR18 追補（旧 gap の閉塞）

> 本書の初期 freeze は **観測済 public contract subset** だった。2026-06-03 Phase2 総合見直し（whole-coverage audit、tl-advisor + pmo 二重 audit）の P1 指摘で、universe を covered / excluded_with_reason / gap に分けた。その後、2026-06-12 L1-L6 監査で L6_required と判定した gap は FR18 の L6 `function-spec.md` と `UT-CAND` 索引へ追補済みである。現在の L1-L6 スコープでは、未閉塞の L6_required 設計 gap は残さない。

### 5.1 universe 分類
| 区分 | 内容 | 件数 / 根拠 |
|---|---|---|
| **covered** | §3 の `FN-*` 14（L7 `UT-*` と 1:1、DbC 固定） | 14 |
| **excluded_with_reason** | private helper / 例外型の完全列挙 / option 単位 validation（粒度爆発回避）。builder / curator / dashboard 系の未観測 public（観測テスト不在で契約を起こせない） | 観測契約なし=対象外 |
| **superseded_gap_closed_by_FR18** | `code_catalog` / `contract_registry` / `doc_map_matcher` / `deliverable_gate` 由来の旧未定義クラスタ。2026-06-12 L1-L6 監査で L6_required 分を FR18 の `function-spec.md` と `UT-CAND` へ分割展開済み。旧 DF-WCAUDIT-L6L7-001 は L1-L6 設計漏れではなく、L7 実装・実行・coverage closure が必要な場合だけ add-feature 承認後に扱う。 | 旧 4 module -> L6_required は FR18 追補で閉塞 |

### 5.2 粒度 caveat（DF-WCAUDIT-L6L7-002）
- `FN-*` は Reverse 由来の **観測済公開契約 / 責務粒度**で起こしており、`FN-AGENT-01`（fire / release）`FN-CONTRACT-01`（登録 / 照合）`FN-DB-01`（接続 / CRUD）`FN-HANDOVER-01`（resume / stale）等は **1 FN に複数オペレーションを束ねている**。HELIX 粒度ペアリング原則の厳密形（関数 1 個 = UT 1 個 / callable・入力型・例外型を明示）から見ると粗い（`FN-ROUTE-01` のみ単一関数 `RouteEngine.evaluate()`）。
- 現状は「1 FN ↔ 1 UT」で内部整合し detector green だが、**厳密な単一関数分割と callable / error contract の明示は、2026-06-12 L1-L6 監査で FR 単位の L6 仕様追補へ分割展開した**。
- L7 実装、FR 別 L7 単体テスト設計成果物、単体テスト実装、単体テスト実施、coverage closure へ進む場合は、承認済み add-feature を入口にする。

### 5.3 FR18 追補と L6 単体テスト設計観点索引（2026-06-12）

2026-06-12 の L1-L6 監査で、§5.2 の後続拡張を L7 実装ではなく **L6 仕様の分割追補**として実施した。FR18 の各仕様は `docs/v2/L6-functional-design/FR-*/function-spec.md` に置き、各仕様内で `*-FN-*` と `*-UT-CAND-*` を対応させる。

`*-UT-CAND-*` は L6 の「単体テスト設計観点」であり、L7 の単体テスト設計成果物、単体テスト実装、単体テスト実施、coverage closure ではない。L7 へ進める場合は add-feature 承認後に、該当 FR の L7 test-design artifact とテスト実装を別途作成する。

| 追補 | 正本 |
|---|---|
| FR18 L6 仕様 | `docs/v2/L6-functional-design/FR-*/function-spec.md` |
| FR18 L6 単体テスト設計観点索引 | `docs/v2/L6-functional-design/fr18-unit-test-design-index.yaml` |
| L1-L6 粒度監査 | `docs/v2/audit/2026-06-12-l1-l6-grain-balance-audit.md` |
| 目的カバレッジ監査 | `docs/v2/audit/2026-06-12-objective-l1-l6-coverage.yaml` |

索引の現在値は FR18 全件、L6 単体テスト設計観点 128 件である。`FR-FNREG-01` / `FR-GLOSSARY-01` を含む registry-only FR も L6 仕様化済みだが、対応する L7 成果物は現在タスクでは作成しない。

## 6. 自己検証チェックリスト

- [x] 既存 frozen 範囲の `FN-*` は `requires/ensures/invariant` を持つ。
- [x] 既存 frozen 範囲の `FN-*` は既存 L7 `UT-*` と 1:1 対応し、detector で uncovered 0 / orphan 0 を維持している。
- [x] `所属 MOD` が L5 モジュール分割設計の実在 ID を指す。
- [x] §5.1 universe（covered / excluded_with_reason / superseded_gap_closed_by_FR18）が宣言され、旧 gap は FR18 L6 追補で閉塞済みであることが明示されている。
- [x] §5.2 粒度 caveat（責務粒度・複数オペレーション束ね）と厳密分割の defer 先が記録されている。
- [x] §5.3 FR18 追補と `fr18-unit-test-design-index.yaml` が L6 の単体テスト設計観点 128 件を示し、L7 成果物と混同されない。
- [x] FR18 追補は `*-FN-*` と `*-UT-CAND-*` の対応を L6 内で示すだけで、L7 単体テスト設計成果物、単体テスト実装、単体テスト実施、coverage closure の証跡として扱わない。
