---
plan_id: L7-v3-engine-c1-schema-registryplan
title: "L7-v3-engine-c1-schema-registryplan: V3 engine C1 schema 単一 registry (Python, cli/lib/v3/schema/, test-first)"
kind: impl
layer: L7
drive: be
status: draft
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: "docs/v3/engine/schema-registry.md"
dependencies:
  requires: []
  blocks:
    - L7-v3-engine-c2-projection-writerplan
pairs_test_design:
  - cli/lib/v3/tests/test_schema_registry.py
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE — C1 schema registry の verify-first 実装 (UT 先行 red → registry/ddl/identifiers/enums 実装 green)"
  - role: qa
    slot_label: "QA — 58-table 分類/識別子 fail-close/enum SSoT/FK 同一DB の境界網羅判定"
generates:
  - artifact_path: cli/lib/v3/schema/registry.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/schema/ddl.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/schema/identifiers.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/schema/enums.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/schema/tables_core.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/schema/tables_evaluation.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/schema/tables_graph.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/schema/__init__.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/tests/test_schema_registry.py
    artifact_type: test
created: 2026-06-26
revised: 2026-06-26
owner: SE
related_docs:
  - docs/v3/engine/schema-registry.md
  - docs/v3/L0-L14/L5-detailed-design.md
  - docs/v3/L0-L14/L6-functional-design.md
---

# L7-v3-engine-c1-schema-registryplan

## 0. 目的

V3 engine keystone **C1 = schema 単一 registry SSoT** を Python で実装する。DDL を単一 registry から機械生成し手書き分散をゼロにする（[C1 設計正本](../../v3/engine/schema-registry.md)）。`SCHEMA_VERSION=18` / **58-table**（harness 56 + V3 `test_result_events` + `functional_registry`）/ DDL 生成口は `schema_ddl()` のみ / 識別子 fail-close / enum 単一正本。

## 0.5 unit 位置づけ（[C6 §4.5 unitized L5-L7 descent](../../v3/engine/doc-workflow-rules.md)）

- **unit_id**: U-ENG-C1
- **parent_l4_component**: L4 §1 「C1 schema 単一 registry」コンポーネント（[L4 基本設計](../../v3/L0-L14/L4-basic-design.md)）
- **trace_edges（上流接続）**: L4 §1 C1 → [L5 §1/§1.5 物理 data + 投影キー](../../v3/L0-L14/L5-detailed-design.md) → [L6 FN-DET-12 schema-ssot](../../v3/L0-L14/L6-functional-design.md) → 本 PLAN
- **descent**: L5/L6 frozen 済 → 本 PLAN は L7（test-first 実装）のみ。L4（parent component）変更時は本 unit closure を invalidated にする。
- **依存**: C2 projection-writer（U-ENG-C2）が本 unit に依存（C1 が TABLE_BY_NAME / kind を供給）。後続 PLAN で blocks 記録。

## 1. 受入条件（DoD）

[schema-registry.md §3/§9](../../v3/engine/schema-registry.md) の DbC を満たし、下記 UT が全 green:

1. `schema_ddl()` は `len(TABLES)+len(INDEXES)` 件かつそれだけ（registry 外 `CREATE TABLE` 不在 = invariant-1）。
2. `assert_sql_identifier(name)` が不正識別子（数字始まり / 記号 / SQL 片）で `SchemaError` raise（fail-close）。
3. `schema/__init__.py` import 時に全 table/column/index 名を検証（不正で import 例外）。
4. 全 `TableDef.kind ∈ {projection, append_event, config}`、件数 = **projection 49 / append_event 3 / config 6 / 計 58**。
5. `append_event` 集合 == `{test_result_events, guardrail_decisions, hook_events}`（[C1 §5](../../v3/engine/schema-registry.md) と一致）。
6. `config` 集合 == `{impact_rules, mcp_server_profiles, mcp_profile_triggers, verification_profiles, document_export_profiles, document_export_triggers}`。
7. `SCHEMA_VERSION == 18`。
8. 物理 `FOREIGN KEY` は同一 DB 内 table のみ（cross-DB FK 宣言で schema check fail = invariant-3）。
9. `PlanKind` は 11 メンバー（impl/design/poc/reverse/add-design/add-impl/refactor/retrofit/recovery/troubleshoot/research）、`charter` を含まない（`charter` は `ArtifactType` 側）。
10. `TABLE_BY_NAME` が 58 table を全網羅、`migrate(db)` は冪等（`CREATE TABLE/INDEX IF NOT EXISTS` + `user_version` set）。
11. `INDEXES` 件数 == **41**、全 index 名が valid identifier、`index_ddl(i)` が `CREATE INDEX` 生成、各 index の参照 column が対象 table に実在。
12. **DDL 妥当性**: `migrate(db)` を実 in-memory sqlite に適用 → 全 58 `CREATE TABLE` + 41 `CREATE INDEX` がエラーなく成功（faithful column port により index 参照 column が実在することの検証）。

## 2. 工程（test-first / verify-first）

1. **RED**: `cli/lib/v3/tests/test_schema_registry.py` に UT-C1-01..11（§1 の DoD を 1:1 に写す）を**先に**書き、`pytest` で fail を確認（実装空）。
2. **GREEN**: `cli/lib/v3/schema/{registry,ddl,identifiers,enums,tables_core,tables_evaluation,tables_graph,__init__}.py` を実装し UT を green に。
3. 3 点レビュー（SE 実装 → QA 境界網羅 → PM 検証）。
4. `python3 -m pytest cli/lib/v3/tests/test_schema_registry.py -q` green + `python3 -m py_compile cli/lib/v3/schema/*.py`。

## 3. 実装方針

- **stdlib のみ**（`dataclasses` + `enum` + `re` + `sqlite3`）。pydantic は C1 では不要（`ColumnDef/TableDef/IndexDef` は dataclass、enum は `enum.Enum`）。後続で validation 強化が必要なら別 unit。
- module 構成は [schema-registry.md §2](../../v3/engine/schema-registry.md) に従う。`col()/pk()` builder で `TableDef` を宣言、`tables_{core,evaluation,graph}.py` に機能群別配置 → `registry.py` が結合。
- **harness 56 table は full column を faithful port**（harness `src/schema/harness-db-tables-{core,evaluation,graph}.ts` = 物理 schema SSoT。`col()/pk()` で全 column 宣言。**faithful 複製は「推測 schema」でない** — 推測回避の caveat は harness 不在の table のみに適用）。**V3-new 2 table（functional_registry / test_result_events）だけ最小 column**（harness 不在＝観測要求ベース）。kind は [§5 inventory](../../v3/engine/schema-registry.md) 正本。
- **41 index を faithful port**（harness `harness-db-indexes.ts`）。各 `IndexDef{name, table, columns}` を宣言、`index_ddl` が `CREATE INDEX name ON table(columns)` 生成。
- enum は [C1 §6](../../v3/engine/schema-registry.md) を正本に `enums.py` へ全列挙（PlanKind/ArtifactType/Layer/Drive/Status/Role/WorkflowPhase/ForwardRouting/PromotionStrategy/OrchestrationMode/V_MODEL_PAIRS/VALID_SUB_DOCS）。

## 4. allowed_files（scope）

- `cli/lib/v3/schema/*.py`（新規）
- `cli/lib/v3/tests/test_schema_registry.py`（新規）
- `cli/lib/v3/__init__.py` / `cli/lib/v3/tests/__init__.py`（package 化、新規）
- **既存 V2 file は触らない**（cutover まで V2 不変 = rollback 保全。cli/lib/ 既存 module を改変しない）。

## 5. escalation

- schema 解釈で設計と矛盾を見つけたら**実装を止めて PM へ**（PLAN 外の schema 変更を独断しない）。物理 column 推測で埋めない。
- secret/PII/外部 API は無し（純 schema 定義）。

## 6. 用語 delta

なし（[C1 設計正本](../../v3/engine/schema-registry.md) の用語に準拠）。

## 7. FR delta

なし（FR-ENG-01 schema 単一 registry の実装。新規 FR 発明禁止）。
