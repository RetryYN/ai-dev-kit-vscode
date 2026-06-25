# C2 — 単一 projection-writer 契約（rebuild_projection ⊥ append_event）

> keystone C2。base SSoT = [capture §1 / §9.5](../audit/2026-06-26-new-base-comprehensive-capture.md) / 実体 = clean harness `src/state-db/{projection-writer,index,feedback-projections,refactor-candidates,artifact-progress-decision}.ts`。
> V3 = Python(stdlib `sqlite3`)。対応: REQ-PRJ-01〜05 / AT-V3-03/04/05/07 / NFR-V3-01。

## 1. 目的

doc/workflow/code/test/FR/設計 を rule で DB へ投影する**単一の口**。DB を artifact の SSoT にする供給側。DB 駆動 detector は writer が壊れると file scan より危険なので、**idempotent / deletion-aware / stale-aware / secret-safe を最優先契約**として固定する。

## 2. 二経路（TL C-1）

clean harness は全 table を rebuild で TRUNCATE する projection-only だが、V3 は **rebuild ⊥ append の二経路**を持つ:

```
rebuild_projection(db, sources) -> RebuildResult{counts, warnings, fails}
    BEGIN IMMEDIATE
      truncate_projection_tables(db)     # kind=="projection" の table のみ DELETE
      for project_fn in PROJECTORS: project_fn(db, sources)   # ~30 projector
    COMMIT   # 失敗時 ROLLBACK（原子・半端状態を作らない）

append_event(db, event) -> EventRowRef
    # kind=="append_event" の table へ冪等追記。logical_key で ON CONFLICT DO NOTHING/UPDATE
```

- **rebuild_projection**: projection table のみ全消し再投影。差分更新しない（idempotent/deletion の原理保証）。harness `rebuildHarnessDb` = `BEGIN IMMEDIATE → truncateProjectionTables → project* → COMMIT`。
- **append_event**: append_event table（`test_result_events`/`hook_events`/`guardrail_decisions`/`impact_results`/`artifact_progress_events`/`model_runs` 等）へ冪等追記。**rebuild の TRUNCATE 対象外**で履歴保持（red→green 遷移・hook 判定・bypass が証跡）。retention は run 単位（C5）。

## 3. 契約（DbC）

- **invariant-idempotent**: 同一 sources で `rebuild_projection` 2 回 → DB 状態 **bit-identical**（重複行ゼロ）。全消し再投影 + `upsert_row`（`INSERT ... ON CONFLICT(logical_key) DO UPDATE`）+ **stableId**（決定的 PK = `prefix:value` の安定ハッシュ）で担保。
- **invariant-deletion**: source 削除 → `rebuild_projection` → 対応 projection 行が再投影されず消える（orphan ゼロ）。
- **invariant-stale**: source 在 + 内容変化（`stale_key`/content hash 不一致）/ superseded → **`stale_status` 列**で current/stale を区別して残す（消すのでなく status）。
- **deletion / stale 排他（TL C-2）**: **source 消失 = deletion（行消失）** ⊥ **source 在 + 内容変化 = stale（行残置）**。source 消失を stale にしない。
- **invariant-secret（TL C-5）**: `assert_no_sensitive_payload(row, table)` が free-form 列への secret 様値（`SECRET_PATTERN`）/ raw transcript / PII を投影前に遮断（PK・`*_id` 参照列は除外）。secret/PII/raw transcript は DB 非保存（ID・理由・score・redacted summary のみ）。
- **invariant-unresolved-join**: 外部キー（`plan_id` 等）が参照先 registry に不在 → `findings` に `unresolved-join` 記録（SQLite FK 制約でなく projection 層の論理整合）。
- **invariant-fail-separation**: 壊れた frontmatter / 契約違反 artifact は **fail と warn を分離報告**（投影を黙って飛ばさない = REQ-PRJ-05）。投影できない artifact は `findings` へ。
- **requires**: artifact は C6（doc-workflow-rules）の機械契約を満たしてパース済。
- **ensures**: 投影先 table は artifact 種別ごとに一意（種別→table 対応が固定）。append_event は logical_key で冪等。

## 4. projector 群（capture §1）

`PROJECTORS` = ~30 の `project_<kind>(db, sources)`。主要: `project_plans` / `project_artifacts` / `project_trace_edges` / `project_test_evidence`(test_runs→cases→results→artifact_edges、`record_test_run_evidence` 経由) / `project_descent_obligations` / `project_gate_runs` / `project_review_evidence` / `project_screens`+`project_screen_trace` / `project_relation_graph`(graph_nodes/dependency_edges) / `project_artifact_progress`(red/yellow/green、純関数 `derive_artifact_progress_decision`) / **secondary projection**: `project_feedback_events`(findings+quality_signals+artifact_progress→feedback_events、PLAN 直読みせず DB 先行投影を読む) / `project_refactor_candidate_signals`(refactor-candidates→quality_signals)。

- **artifact_progress color**: red = `dependency_checked=0` or `open_dependency_impacts>0` / yellow = impl あり test 証跡なし / green = `passed_test_run_count>0 ∧ dependency_checked=1 ∧ open_dependency_impacts=0`（純関数 `derive_artifact_progress_decision`、DB I/O 非含有）。
- **refactor-candidate**（harness net-new）: `analyze_refactor_candidates` が split-module/extract-helper/deduplicate-function/externalize-literal/externalize-policy を静的検出 → `quality_signals`(confidence=high 上位 20 = warn) → `feedback_events` → doctor surface。閾値は policy 分離。

## 5. row identity / upsert 基盤

```python
def upsert_row(db, table, row):   # idempotent 基盤プリミティブ（全投影が経由）
    cols = ",".join(row); ph = ",".join("?"*len(row))
    upd = ",".join(f"{c}=excluded.{c}" for c in row if c != table.logical_key)
    db.execute(f"INSERT INTO {table.name} ({cols}) VALUES ({ph}) "
               f"ON CONFLICT({table.logical_key}) DO UPDATE SET {upd}", tuple(row.values()))
```

`stable_id(prefix, value)` で決定的 PK 生成（再投影で同一行が同一 PK = 重複防止）。`table.name`/column は schema registry の `assert_sql_identifier` 済識別子のみ。

## 6. 検証

- AT-V3-07: `rebuild_projection` 2 回 → DB diff 空（idempotent / bit-identical）。
- AT-V3-04: source 削除 → rebuild → 対応 projection 行消失（deletion）/ append_event 行は残存。
- AT-V3-05: source 更新 → 古い投影が残らない / `stale_status` マーク（stale）。
- 単体: 空 DB からの rebuild / 壊れた frontmatter の fail-warn 分離 / 種別→table 一意性 / secret 値投影で `assert_no_sensitive_payload` raise / append_event の冪等（同 logical_key 二重 append で 1 行）/ unresolved-join → findings。

## 7. 呼び出し

`rebuild_projection` は automation（Phase 6 hook / CI / `helix doctor`）から呼ばれ、detector（C3）は rebuild 済 DB を query する。`append_event` は hook（PostToolUse / SubagentStop）/ test runner / gate 実行から都度呼ばれる。物理 column 型は [L5 physical-data / capture §B3](../L0-L14/L5-detailed-design.md) を正本。
