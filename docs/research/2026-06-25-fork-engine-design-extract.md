# Fork Engine Design Extract — UT-TDD Agent Harness（V3 起草の正本 reference）

> 抽出日: 2026-06-25 / 対象: `UT-TDD_AGENT-HARNESS-main`（HELIX の TypeScript/Bun フォーク、実運用済）
> 用途: HELIX **V3** の L4-L6 / engine keystone を Python で起草するための設計意図抽出。**コード写経でなく設計を盗む**。
> 根拠表記: 行番号付き = 実コード確認 / 「推測:」= 静的読解からの推定。

---

## 1. 設計ドキュメントの有無

- フォークの設計は **コード/schema/lint module の docstring に内在**（harness-db.ts 冒頭コメントが registry 規約を記述、各 lint module の冒頭に「何を violation にし doctor.ok にどう連動するか」を明記）。IMP-### / PLAN-L7-## の参照 ID がコメントに散在（例: lint-wiring の IMP-006、tool-adapter の IMP-033 / PLAN-L7-50 R8）。
- 含意: V3 では同等の「契約を doc 側に持つ」設計を**機械パース可能な形**で先に確定する（fork はコメント、V3 は frontmatter/registry へ昇格）。

## 2. schema 単一 registry SSoT（harness-db.ts, 1137L）

- **`SCHEMA_VERSION = 18`**（:18）。冒頭コメント: 「table 追加は registry への append + SCHEMA_VERSION」＝**追記式単一 registry**。
- **単一 DDL 生成**: `schemaDdl()`（:1135）= `[...HARNESS_DB_TABLES.map(createTableSql), ...HARNESS_DB_INDEXES.map(createIndexSql)]`。テーブルは `HARNESS_DB_TABLES`（`TableDef` 配列）、index は `HARNESS_DB_INDEXES`。`createTableSql(table)`（:1121）/ `createIndexSql(index)`（:1130）が唯一の DDL 文字列化口。
- **識別子 fail-close**: `assertSqlIdentifier(name)`（:46）が不正識別子を DDL 展開前に弾く（:1097 コメント）。
- **テーブル inventory（56 table）** ※機能群分類は V3 用に再編する前提:
  - **PLAN/artifact 系**: plan_registry, artifact_registry, artifact_progress, artifact_progress_events, improvement_log, issue_queue, outstanding(→ findings 経由)
  - **trace/relation 系**: trace_edges, graph_nodes, dependency_edges, graph_snapshots, relation-graph 由来 → coverage, descent_obligations
  - **test/oracle 系**: test_runs, test_cases, test_results, test_artifact_edges, test_flake_events
  - **gate/drive/workflow 系**: gate_runs, drive_runs, workflow_runs, guardrail_decisions
  - **model/run/telemetry 系**: model_runs, tool_runs, hook_events, retry_events, trouble_events, quality_signals, feedback_events
  - **skill 系**: skill_invocations, skill_recommendations, skill_evaluations
  - **impact/automation 系**: impact_rules, impact_results, automation_assets
  - **mcp/external/verification 系**: mcp_server_profiles, mcp_profile_triggers, mcp_server_runs, external_tool_findings, verification_profiles, verification_recommendations
  - **document export 系**: document_export_profiles/runs/datasets/artifacts/triggers
  - **roadmap/eval 系**: roadmap_rollups, roadmap_band_coverage, roadmap_gate_progress, poc_evaluations, model_evaluations
  - **review/FE/search 系**: review_evidence_registry, screens, screen_trace, search_index, diagram_artifacts, findings
  - + 41 index（idx_*）。
- 各テーブルが「あるべき集合」を持つ: 例 `plan_registry`=登録 PLAN 全件、`test_cases`/`test_results`=UT 全件と実行結果、`descent_obligations`=L6→L7 降下義務、`trace_edges`=縦断 trace、`review_evidence_registry`=定性 review 証跡。detector はこれらを query して欠落を出す。
- 推測: `TableDef`/`IndexDef` は Zod 等でなく TS interface（columns 配列）。型契約は schema 定義そのもの。V3 では Python の dataclass/TypedDict + 単一 DDL builder へ写像。

## 3. 単一 projection-writer（projection-writer.ts, 3019L）

- **入口**: `rebuildHarnessDb(input)`（:2952）→ `RebuildHarnessDbResult`。全 artifact を読み DB を再構築する単一口。
- **idempotent 機構**: 各テーブルを `DELETE FROM ${table.name}`（:1030）で**全消し → 再投影**。同一入力の再 rebuild は同一状態（重複行が原理的に出ない）。
- **deletion-aware**: rebuild が全消し再投影なので、消えた artifact は再投影されず DB から自然に消える（orphan 残らない）。
- **stale-aware**: 投影行に `stale_status`（:1159、`artifact.stale ? "stale" : "current"`）を持たせ、古い/失効 artifact を stale としてマークして残す（消すのでなく status で区別）。
- **artifact 種別 → table 投影**: 種別ごとに `project*()` 関数（例 `projectTokenUsage`→model_runs/tool_runs、`projectSkillEvaluations`→skill_evaluations、`projectPocEvaluations`→poc_evaluations、`projectModelEvaluations`→model_evaluations、`projectGuardrailInvariantAdvisories`→guardrail_decisions）。`recordProjectionEvent`（:314）で投影イベントを記録。
- **progress 判定**: `deriveArtifactProgressDecision`（:112）= artifact の進捗色/test 状態を導出 → artifact_progress(_events)。
- V3 含意: 「全消し→再投影」を **projection の基本契約**にする（差分更新でなく rebuild）。これが idempotent/deletion を同時に満たす最小設計。stale は status 列で表現。

## 4. DB 駆動 detector（src/lint/*.ts 61 module + doctor/index.ts 1985L）

- **集約**: doctor は各 check を呼び `{ messages, ok }` を受け、**runDoctor.ok に各 ok を連動（AND）で fail-close**（:347/369/385/404/424/442/458/480 …各 check が `ok: r.ok` を返す）。warning surface（handover/agent-slots/不在・stale）は `doctor.ok を落とさない`（:306/324 = exit 0 warning）。**hard 判定**は ok=false で全体 fail（例 review-evidence :470）。
- **DB query で「あるべき−実在=もれ」の代表**:
  - `plan-completion-drift` / `merged-plan-status`: plan_registry の status と artifact_registry の実在を突合し「artifact 在るのに PLAN draft 放置」等の逆向き drift を検出。
  - `descent-obligation`: descent_obligations（L6 active）に対し test_cases/artifact の実装行を query、未実装 traceKey を violation。
  - `oracle-test-trace`(+`-baseline`): test_cases の oracle と trace_edges を突合、baseline 外の欠落のみ fail-close（ratchet 連動）。
  - `relation-graph`: graph_nodes/dependency_edges/trace_edges で縦断（req→plan→design→test→source→db）の orphan/covered-by を検出。
  - `db-projection-coverage`/`-ingestion`: 投影テーブルの row-count と期待を突合（projection 自体の健全性）。
- **detector 61 の機能カテゴリ分類**（V3 移植マップの素材）:
  - PLAN: plan-artifact-existence, plan-body-substance, plan-completion-drift, plan-dod, plan-supersession, merged-plan-status, impl-plan-trace, outstanding, placeholder-deps
  - trace/relation: g1-trace, g3-trace, relation-graph, propagation, backfill-pairing, descent-obligation
  - FR/registry/coverage: fr-registry-audit, fr-roadmap-coverage, roadmap-registry, tracked-canonical, entity-coverage
  - L-completion: l6-completion, l6-fr-coverage, l7-completion
  - test/oracle: oracle-test-trace, oracle-test-trace-baseline, green-command-digest, cycle-p4-verification
  - DB projection: db-projection-coverage, db-projection-ingestion, drive-db-registration
  - rule/drift/doc: coding-rules, ddd-tdd-rules, rule-drift, rule-automation-closure, module-drift, dependency-drift, asset-drift, doc-consistency, sub-doc-catalog-drift, sub-doc-section-structure
  - gate/drive/branch: gate-confirm, right-arm-gate-planning, drive-model-passage, branch-kind
  - workflow/impact: scrum-reverse, change-impact
  - review/quality/telemetry: review-evidence, readability, telemetry-closure, improvement-backlog, feedback-log
  - wiring/meta/hook: lint-wiring, runtime-portability, project-hook, codex-hook-adapter, tool-adapter, skill-assignment
  - FE: screen-impl-pair-freeze
  - proposal/verification: proposal-document-coverage, verification-profile
  - shared（detector でなく共通 util）
- doctor の import 数 = 69（:`grep -c ^import`）。lint 61 中の大半が doctor 経由で配線（残りは lint-wiring が監視）。

## 5. lint-wiring メタゲート（lint-wiring.ts, 193L）

- **`RUNTIME_ENTRYPOINTS = ["src/cli.ts"]`**（:28）。ここから import グラフを **BFS して到達集合**を構築（:104,:123）。
- **三判定**（:49-51, :150）: ①到達不能 かつ DEFERRED 未登録 = **死蔵 violation** / ②DEFERRED 登録済みだが実は到達可能 = **stale 申告 violation** / ③到達 or DEFERRED = ok。
- **`DEFERRED_LINTS: Record<string,string>`**（:34）= 理由付き除外。現状 **1 件のみ**: `tool-adapter`（adapter-probe 純関数ライブラリ、`ut-tdd adapter` 統合は IMP-033/PLAN-L7-50 R8 で deferred = closed-as-library）。
- violation メッセージ（:191）: 「各 src/lint/<name>.ts は runtime 経路（cli→doctor/plan-lint 等）から到達するよう配線するか DEFERRED_LINTS に理由付き登録せよ（IMP-006）」。
- V3 含意: HELIX の axis-04/10/13 死蔵に効く。Python では「detector registry のキー集合 − cli から到達する detector 集合 − DEFERRED = 死蔵」を出す（AST import-graph or 明示 registry の集合差分）。

## 6. baseline ratchet

- 代表: `oracle-test-trace-baseline`（lint module として独立）= 既知 debt を baseline に持ち、**baseline 外の欠落だけ fail-close**。baseline は縮小のみ可（増加＝debt 追加を reject）。
- doctor の warning surface（exit 0 warning, :306）と hard 判定（ok=false, :470）の二段で、advisory→fail-close の段階を表現。
- V3 含意: detector ごとに `*_BASELINE`（既知 debt の id 集合）を持ち、「現 violation − baseline = 新規 violation のみ fail」。baseline 更新は縮小方向のみ許可する ratchet テストを置く。

## 7. ルール化 doc/workflow 契約

- PLAN/artifact は frontmatter + 規約セクションを持ち、projection-writer が読んで plan_registry / artifact_registry / artifact_progress へ投影（status/layer/drive/trace を列化）。
- workflow は workflow_runs / drive_runs / drive-model-passage で「駆動 model の通過（forward_return 相当）」を機械化（散文依存をやめ、通過を行で残す）。`drive-db-registration` が drive の DB 登録を検証。
- `gate_runs` / `gate-confirm` が gate 通過を行で持ち、`right-arm-gate-planning` が右腕 gate の計画を検証。
- V3 含意（最重要）: doc/workflow の **frontmatter/ID/必須セクション/forward_return を機械契約**にし、projection-writer が DB 行へ。これが「DB が *あるべき集合* を持つ」の供給源。HELIX 設定（workflow 群）はこの契約形式へ差し替える（charter Phase 4 = FR-CFG-01）。

---

## V3 への写像メモ（Python 化 / オリジナル化の指針）

| fork(TS) | V3(Python) 写像 |
|---|---|
| `HARNESS_DB_TABLES`(TableDef[]) + `schemaDdl()` | 単一 `TABLES` 定義（dataclass/TypedDict）+ `build_ddl()`。`assert_sql_identifier` を移植 |
| `rebuildHarnessDb` + `DELETE FROM` 全消し再投影 | `rebuild(db)` 全消し→`project_*` 群。idempotent/deletion を rebuild で同時担保、stale は status 列 |
| doctor の `{messages, ok}` AND 集約 | `run_doctor(db)->{ok, findings}`、ok=all(checks)。warning surface は ok 非連動 |
| `lint-wiring` BFS + DEFERRED | detector registry キー − cli 到達集合 − DEFERRED の集合差分 |
| `*-baseline` lint | detector ごと baseline id 集合、新規 violation のみ fail、縮小のみ許可 |
| frontmatter/コメント契約 | 機械パース可能 frontmatter（必須 field/ID/section/forward_return）+ projection rule |

**注意**: 物理 FK は同一 DB 内のみ（fork も単一 DB。HELIX の split-DB cutover FK 破綻を再発させない）。テーブル群は V3 の要求に合わせて**取捨選択**（fork の 56 を全移植せず、HELIX V-model + FE + 配布 + harness に必要な集合へ再編）。
