# C1 — schema 単一 registry SSoT 契約

> keystone C1。base SSoT = [capture §1](../audit/2026-06-26-new-base-comprehensive-capture.md) / 実体 = clean harness `src/schema/{harness-db,harness-db-catalog,harness-db-tables-*,harness-db-indexes,index}.ts`。
> V3 = Python(stdlib `sqlite3` + `pydantic`/`Enum`)。TS/zod は表層、設計意図を盗む。対応: REQ-SCH-01/02/03 / AT-V3-01/02。

## 1. 原則

**DDL を単一 registry から機械生成し、手書き分散をゼロにする。** schema 定義は 1 箇所（registry）に集約し、DDL 文字列化・identifier 検証・enum 定義を同一モジュール群から行う。table 追加 = registry への append + `SCHEMA_VERSION` bump の 1 操作で済む（重複定義が構造的に起きない）。clean harness 実証: `SCHEMA_VERSION=18` / **実 56 table** / DDL 生成口は `schemaDdl()`・`createTableSql()`・`createIndexSql()` のみ。

## 2. registry 構成（Python 版）

```
cli/lib/schema/
  registry.py        # ColumnDef/TableDef/IndexDef dataclass、col()/pk() builder、TABLES/INDEXES 集約、SCHEMA_VERSION
  ddl.py             # table_ddl(t)/index_ddl(i)/schema_ddl()->list[str]、唯一の DDL 文字列化口
  identifiers.py     # SQL_IDENTIFIER 正規表現 + assert_sql_identifier()（fail-close）
  enums.py           # 全 enum（Enum/pydantic）= enum SSoT
  tables_core.py / tables_evaluation.py / tables_graph.py   # TableDef を機能群別に宣言
  __init__.py        # import 時に全 identifier 検証（§4）
```

- `col(name, type)` / `pk(name)` の宣言的 builder で `TableDef` を組む（harness `harness-db-table-builders.ts`）。
- `TableDef` を `tables_{core,evaluation,graph}.py` に機能群別配置 → `registry.py` が結合（harness catalog パターン）。
- `TABLE_BY_NAME: dict[str, TableDef]` 公開（detector が table 仕様を参照、harness `HARNESS_DB_TABLE_BY_NAME`）。

## 3. 契約（DbC）

```
TABLES: list[TableDef]            # 唯一のテーブル定義源（append で増やす）
INDEXES: list[IndexDef]
SCHEMA_VERSION: int               # TABLES/INDEXES 変更で必ず上げる
schema_ddl() -> list[str]         # = [table_ddl(t) for t in TABLES] + [index_ddl(i) for i in INDEXES]
assert_sql_identifier(name)       # 不正識別子を DDL 展開前に fail-close
```

- **requires**: 各 `TableDef.name`/columns/index 名が `assert_sql_identifier` を通る。
- **ensures**: `schema_ddl()` は TABLES/INDEXES の全件かつそれだけ（registry 外で `CREATE TABLE` を書く箇所が存在しない）。
- **invariant-1（単一 SSoT）**: DDL 文字列化の口は `table_ddl`/`index_ddl` のみ。
- **invariant-2（version 整合）**: 実 DDL と `SCHEMA_VERSION` 不整合を検出（migration 起点）。
- **invariant-3（FK 同一 DB）**: 物理 FOREIGN KEY は同一 DB 内 table のみ。境界越えは FK でない列（logical reference）+ consistency detector（過去の cross-DB FK 物理破綻の教訓）。

## 4. 識別子 fail-close（injection 構造排除）

```python
SQL_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
def assert_sql_identifier(name: str) -> None:
    if not SQL_IDENTIFIER.match(name): raise SchemaError(f"invalid SQL identifier: {name!r}")
```

`schema/__init__.py` の import 時に**全 table 名・column 名・index 名を検証**（harness module load 時 `harness-db.ts:79-87`）。不正識別子で import 例外。DDL は builder + `assert_sql_identifier` 経由でのみ生成、値は parameterized query（`?`）。

## 5. table 分類（TL C-1 — projection ⊥ append_event）

各 `TableDef` に `kind: "projection" | "append_event" | "config"` を必須属性で持たせる。

- **projection**: rebuild で全消し再投影。現在状態 = 最新 rebuild 結果。`rebuild_projection` の TRUNCATE 対象。
- **append_event**: 冪等追記。rebuild で消えない（truncate 対象外）。時系列監査の証跡（red→green 履歴 / hook / bypass / guardrail decision）。
- **config**: 静的設定（impact_rules / mcp_server_profiles 等）。rebuild 非対象 or seed のみ。

> clean harness は全 table を `rebuild_projection` で TRUNCATE する **projection-only** 実態（`test_result_events` 不在）。**V3 は append_event を独自差分で追加**（TL: 監査/red-first 履歴は時系列が証跡で projection-only では満たせない）。

### 56 table inventory（kind 付与は V3 確定、列/PK 完全仕様は capture §B3 を正本）

**core(27)**: `plan_registry`(proj) `artifact_registry`(proj) `model_runs`(event) `trace_edges`(proj) `coverage`(proj) `findings`(event) `gate_runs`(event) `drive_runs`(event) `hook_events`(event) `skill_invocations`(event) `skill_recommendations`(event) `feedback_events`(event) `quality_signals`(proj) `test_runs`(event) `test_cases`(proj) `test_results`(proj) **`test_result_events`(event, V3 新設)** `test_artifact_edges`(proj) `test_flake_events`(event) `search_index`(proj) `workflow_runs`(proj) `guardrail_decisions`(event) `issue_queue`(event) `trouble_events`(event) `retry_events`(event) `improvement_log`(event) `automation_assets`(proj)

**evaluation(10, 全 projection)**: `skill_evaluations` `poc_evaluations` `model_evaluations`(opt-in) `roadmap_rollups` `roadmap_band_coverage` `roadmap_gate_progress` `review_evidence_registry` `descent_obligations` `screens` `screen_trace`

**graph(20)**: `graph_nodes`(proj) `dependency_edges`(proj) `impact_rules`(config) `impact_results`(event) `artifact_progress`(proj) `artifact_progress_events`(event) `tool_runs`(event) `diagram_artifacts`(proj) `graph_snapshots`(proj) `mcp_server_profiles`(config) `mcp_profile_triggers`(config) `verification_profiles`(config) `verification_recommendations`(event) `mcp_server_runs`(event) `external_tool_findings`(event) `document_export_profiles`(config) `document_export_runs`(event) `document_export_datasets`(event) `document_export_artifacts`(proj) `document_export_triggers`(config)

> index = 41（capture §B3 一覧）。

## 6. enum SSoT（capture §B3 全列挙 → Python Enum）

`enums.py` を **enum 単一正本**にする（harness `src/schema/index.ts` = zod 相当）。drift を型 + 実行時検証で根絶。

- `Kind`(12): charter/impl/design/poc/reverse/add-design/add-impl/refactor/retrofit/recovery/troubleshoot/research
- `Layer`(16): L0-L14 + cross ／ `V_MODEL_PAIRS`(6): L1↔L14 / L2↔L10 / L3↔L12 / L4↔L9 / L5↔L8 / L6↔L7
- `VALID_SUB_DOCS`（層別 slug、L1:5/L2:4/L3:4/L4:9/L5:5/L6:4。FE slug = screen/screen-list/screen-flow/ui-element/wireframe/screen-functional/ui-standard/ui-detail/screen-spec）
- `Drive`(5) be/fe/fullstack/db/agent ／ `Status`(4) draft/confirmed/completed/archived ／ `Role`(7) po/tl/qa/aim/uiux/se/docs
- `WorkflowPhase`(10) S0-S4/R0-R4 ／ `DecisionOutcome`(3) ／ `ReverseType`(5) ／ `ForwardRouting`(5: L1/L3/L4/L5/gap-only) ／ `PromotionStrategy`(4)
- `ArtifactType`(19) ／ `OrchestrationMode`(5)

## 7. row identity（TL C-2）

各 `TableDef` に identity 契約: **logical_key**（冪等 upsert キー = PK or `(run_id,seq,kind)`）/ **stale_key**（source hash、値変化で stale 判定・行残置）/ **delete_scope**（projection=rebuild で消失 / append_event=消えない）。不変条件: 同一 input で `rebuild_projection` 2 回 bit-identical / append_event は rebuild 後残存 / source 消失=projection 行消失（deletion）/ source 内容変化=stale 更新（行残置）。

## 8. migration

`migrate(db)` は `PRAGMA user_version < SCHEMA_VERSION` のときだけ `CREATE TABLE/INDEX IF NOT EXISTS`（冪等）+ `ALTER TABLE ADD COLUMN`（追加列）を適用し `user_version=SCHEMA_VERSION` を set。table 追加は registry append + version bump のみ。

## 9. 検証 / 公開 API

- AT-V3-01: registry 外 `CREATE TABLE` → static check fail（invariant-1）。AT-V3-02: cross-DB FK 宣言 → schema check fail（invariant-3）。
- 単体: `schema_ddl()` 件数 == len(TABLES)+len(INDEXES) / 不正識別子で `assert_sql_identifier` raise / projection 2 回 rebuild bit-identical / append_event は truncate 非対象。
- **公開 API（破壊禁止）**: `VALID_SUB_DOCS` slug / gate ID(`G0.5-G14`) / rule 型 id / table 名 = 消費側依存。変更は breaking（shim + migration detector 必須）。
