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

## 5. table 分類 SSoT（TL C-1 — projection ⊥ append_event ⊥ config）

**本節が V3 全 table の唯一の分類 SSoT。** L5/L6/C2 は本表を参照し、再分類しない（C1 = 単一 table SSoT、TL P1）。各 `TableDef` に `kind ∈ {projection, append_event, config}` を必須属性で持つ。

- **projection**: rebuild で全消し再投影。現在状態 = 最新 rebuild 結果。`rebuild_projection` の TRUNCATE 対象。**default**。
- **append_event**: 冪等追記。rebuild で消えない（truncate 対象外）。**rebuild が破壊する＝current source から再導出不能な監査履歴のみ**（capture §1/§103: red-first / review-guard / hook-bypass）。
- **config**: 静的設定（seed のみ、runtime 由来でない）。rebuild 非対象。

> **分類原則**: clean harness は全 table を `rebuild_projection` で TRUNCATE する **projection-only** 実態。V3 は「rebuild で復元不能な監査証跡」だけを append_event へ昇格する（最小 delta）。再導出可能な `*_events` 名 table（`model_runs` / `impact_results` / `artifact_progress_events` / `retry_events` / `trouble_events` / `test_flake_events` / `mcp_server_runs` 等）は **projection のまま**（"event" は harness の命名であって append 意味論ではない）。

### V3 table inventory（58 = harness 56 + V3 追加 2）

harness = **56**（core 26 + evaluation 10 + graph 20、`SCHEMA_VERSION=18`、index 41）。V3 は次の 2 table を明示追加し **58** とする（推測増設はしない）:

- `test_result_events`（**append_event**, V3 新設）: red→green 履歴。`test_results`(current projection) と用途分離。
- `functional_registry`（**projection**, V3-core）: 機能一覧 SSoT（fn_id↔ut_id の FN↔UT 1:1 供給、FR-FNREG）。harness は FR を artifact 側で表現 → V3 は queryable table へ昇格（C1 登録 = SSoT 準拠）。

分類別の全件（58）:

- **append_event(3)**: `test_result_events` / `guardrail_decisions` / `hook_events`
- **config(6)**: `impact_rules` / `mcp_server_profiles` / `mcp_profile_triggers` / `verification_profiles` / `document_export_profiles` / `document_export_triggers`
- **projection(49)**: 下記の append_event/config を除く全 table

module 別（kind は上の 3 分類が正、ここは配置）:

**core(28)**: `plan_registry` `artifact_registry` **`functional_registry`(V3)** `trace_edges` `coverage` `findings` `gate_runs` `drive_runs` `model_runs` `skill_invocations` `skill_recommendations` `feedback_events` `quality_signals` `test_runs` `test_cases` `test_results` **`test_result_events`(V3, append)** `test_artifact_edges` `test_flake_events` `search_index` `workflow_runs` `guardrail_decisions`(append) `hook_events`(append) `issue_queue` `trouble_events` `retry_events` `improvement_log` `automation_assets` — projection 25 + append 3

**evaluation(10, 全 projection)**: `skill_evaluations` `poc_evaluations` `model_evaluations` `roadmap_rollups` `roadmap_band_coverage` `roadmap_gate_progress` `review_evidence_registry` `descent_obligations` `screens` `screen_trace`

**graph(20)**: `graph_nodes` `dependency_edges` `impact_rules`(config) `impact_results` `artifact_progress` `artifact_progress_events` `tool_runs` `diagram_artifacts` `graph_snapshots` `mcp_server_profiles`(config) `mcp_profile_triggers`(config) `verification_profiles`(config) `verification_recommendations` `mcp_server_runs` `external_tool_findings` `document_export_profiles`(config) `document_export_runs` `document_export_datasets` `document_export_artifacts` `document_export_triggers`(config) — projection 14 + config 6

> 列/PK 完全仕様は **L7 で確定**（推測 schema を避ける＝CLAUDE.md「永続化要求が観測されてから schema 確定」）。harness 実体 = capture §1 / `src/schema/harness-db-tables-{core,evaluation,graph}.ts`。index = 41（harness `harness-db-indexes.ts`）。

## 6. enum SSoT（capture §1 全列挙 → Python Enum）

`enums.py` を **enum 単一正本**にする（harness `src/schema/index.ts` = zod 相当）。drift を型 + 実行時検証で根絶。

- `PlanKind`(11): impl/design/poc/reverse/add-design/add-impl/refactor/retrofit/recovery/troubleshoot/research（C6 PLAN kind と一致。**`charter` は PLAN でなく top-level doc artifact = `ArtifactType` 側**。`PlanKind` と `ArtifactType` を混同しない）
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
