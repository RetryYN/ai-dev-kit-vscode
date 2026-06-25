# V3 New Base 網羅 Capture（clean harness → V3 base SSoT）

> 作成: 2026-06-26 / 対象: 最新 clean `UT-TDD_AGENT-HARNESS-main.zip`（984 entries / 展開 906 files、旧版 = `-2026-06-25.zip` に退避）
> 方法: 8 領域並列 capture（pmo-helix-explorer ×8、最終構造化サマリ回収、keystone は file:line で spot-verify 可能）
> 方針（ユーザー 2026-06-25〜26）: **clean harness を丸ごと忠実に V3 base として capture（今）→ HELIX 独自強化は capture 後に別フェーズ（後）**。
> 位置づけ: 本 doc は V3 再構築の **base SSoT**。既存 `docs/v3/` 17-18 doc（旧 fork 由来・freeze-ready だった下書き）の前提と衝突する箇所は**本 capture が上書き**する（§9 参照）。**未コミット / 物理削除は cutover まで禁止**。

---

## 0. エグゼクティブサマリ

最新 harness は、旧 fork（V3 corpus の抽出元）から **refactoring で構造が clean 化**され、かつ **FE 設計ガバナンス・design 駆動モデル・refactor-candidate detector** が net-new で追加されていた。規模・完成度ともに V3 corpus の想定を上回り、**V3 base は本 harness の実態から作り直す**のが正しい（charter の一部凍結事項は実態と不一致 = §9）。

閉ループの背骨（fork で実証）:
**ルール化 doc/workflow 契約 → 単一 registry SSoT(schema) → projection-writer(rebuild) → detector(pure-function 3 層・ok=AND) → lint-wiring メタゲート(死蔵禁止) → baseline ratchet(非後退)**。

---

## 1. Schema & DB（keystone C1/C2）

- **単一 registry SSoT**: `SCHEMA_VERSION=18`。DDL 生成口は `schemaDdl()`/`createTableSql`/`createIndexSql` のみ（手書き分散ゼロ）。table 定義は `harness-db-tables-{core,evaluation,graph}.ts` → `harness-db-catalog.ts` で結合 → `harness-db.ts` が DDL 化。**識別子 fail-close**（`assertSqlIdentifier`、import 時に全 table/column/index 名を検証、injection 構造排除）。
- **table 実数 ≈ 56**（charter の「core 14 + Phase2」より遥かに多い）。分類: PLAN/artifact / trace / test / gate / model-telemetry / skill / feedback-ops / evaluation(skill/poc/model/roadmap/review_evidence/descent_obligations/**screens/screen_trace**) / graph-impact / MCP / verification / document_export。
- **projection-writer**: `rebuildHarnessDb()` = `BEGIN IMMEDIATE → truncateProjectionTables(全 DELETE) → ~30 の projectXxx() → COMMIT` の原子 rebuild。全投影は `upsertRow`（`INSERT ... ON CONFLICT(pk) DO UPDATE`）で冪等。`stableId`(決定的 PK) で再投影同一行保証。`assertNoSensitivePayload`(SECRET_PATTERN) で secret 投影遮断。dangling FK は SQLite 制約でなく projection 層で `findings` に `unresolved-join` 記録。
- **deletion/stale**: deletion = source 消失で次 rebuild 行消失 / stale = `stale_status` 列で source hash 差分判定（行残置）。
- **🆕 refactor-candidate detector**: `refactor-candidates.ts`（split-module/extract-helper/deduplicate-function/externalize-literal/externalize-policy の 5 種を静的検出、閾値は `-policy.ts` 分離）→ `quality_signals`(warn) → `feedback_events` → doctor surface。**= ユーザーの言う「refactoring フロー改善」の実体**。
- **⚠ 要 TL**: `test_result_events` は実在せず、rebuild が全 table TRUNCATE のため **event-append 履歴は現実装で永続しない**（§9-2）。

## 2. Detector / lint 層（keystone C3/C4）

- **約 60 lint module**。共通様式 = **3 層分離**: 純関数 `analyze<X>(input)→result` / I/O `load<X>Input(repoRoot)` / `<x>Messages(result)`。型は `*-types.ts`、policy 定数は `*-policy.ts` に分離（refactoring の核）。共通 helper は `shared.ts` 集約。
- **判定 source は混在**（charter C3「DB 駆動・file scan 禁止」は理想であって実態でない = §9-3）:
  - DB-projection 駆動: `db-projection-coverage` / `db-projection-ingestion`(14 table row>0 gate) / `relation-graph`(projection を書く)
  - file/artifact scan 駆動: `descent-obligation` / `screen-impl-pair-freeze` / `frontend-design-coverage` / `oracle-test-trace` / 大半の `plan-*`
- **普遍契約**: ①**ok=AND**（`runDoctor` が 60 checker を AND、1 つ false で全体 fail-close）②**absence-blindness 防止**（requirements=0 でも ok=false、無音 fallback 降格禁止、anchor 字句 marker で prose 改稿耐性）③ I/O 失敗 = ok=false（skip 禁止）。
- **lint-wiring メタゲート**（`lint-wiring.ts`, IMP-006）: 全 `src/lint/*.ts` が `src/cli.ts` から BFS 推移到達可能 **or** `DEFERRED_LINTS` に理由付き登録、のいずれか必須。死蔵=`unwired` violation、虚偽 defer=`staleDeferred` violation。現 DEFERRED=`tool-adapter` 1 件。
- **baseline ratchet**（`oracle-test-trace-baseline.ts`）: 未 citation 89 件を shrink-only `ReadonlySet`、件数増加禁止をレビュー規律 + CI monotone-decrease assert で担保。
- **FE detector**（charter D7 覆す = §9-4）: `frontend-design-coverage`（schema VALID_SUB_DOCS + §1c doc + 実ファイルの **3 者 AND**）/ `screen-impl-pair-freeze`（`next_pair_freeze` 未到達での `implemented_screens` 宣言を block）。
- **descent-obligation**: FR-L1-* trace key の L1→L3→…→L7(+L8/L9/L12) 降下義務を adjacency rule 駆動で全数計算、satisfied/deferred/unmet/impl-ahead 分類、`@ut-tdd-trace` explicit citation のみ採用（blanket range は provenance 区別）。

## 3. Workflow / 駆動モデル（keystone C6）

- **13 駆動モード**（`contracts-policy.ts` の `DRIVE_TDD_FITS`、HELIX/charter の 9-10 を超える）: design / add-feature / discovery / reverse / recovery / incident / refactor / retrofit / scrum / research / **screen-design** / **frontend-design** / **design-bottomup**。各々に red_triggers / green_requirements / forward_return / approval 要否（**recovery・incident のみ approval 強制**）。
- **routing**（`routing-contracts.ts`）: `ROUTE_SIGNAL_MAP`(13 entry) で signal→mode、最長一致優先。`evaluateRouteCommand` が route-config 違反(legacy-db/personal-path)を block、escalation 13 語(auth/payment/pii/prod/migration 等)で approval 強制、`ut-tdd` prefix 以外の command を `legacy-runtime-command` で排除。
- **🆕 design-bottomup**（`design-elicitation.ts`、第3の向き）: 確立 backend（data_entity/projection/cli_command）+ screen_trace → FE 要件 derive（各画面×L3/L5/L6 slot）→ gap 検出（has_body=false を SLOT_SIGNAL 発火、coverage≠substance）→ Discovery(entry=design_uncertain)へ合成（新 mode 作らず既存 routing に乗る）→ Forward L3-L6 降下。
- **C6→C2→C3 接続**: `recordTestRunEvidence`(唯一の test DB write 経路、plan_id/oracle_id 欠如は warn) → `readiness.ts`(findings/gate_runs/guardrail を live 集計 → workflow_runs 書戻し) → `enforceForwardOrder`(prior gate 未通過を error)。

## 4. Doctor / Gate / Baseline（keystone C5）

- **gate 体系 G0.5-G14**（`gate-design.md` 正本）。静的 gate（`evaluateStaticGate`、G7 = pair-freeze + impl-plan-trace + oracle-test-trace + coverage≥80% の AND）+ **judgment gate**（`JUDGMENT_GATES=G0.5/G2/G4/G5/G6/G7/R4`、review tier = **cross_agent**(worker≠reviewer model)/**intra_runtime_subagent**(checklist 7=DOC/TST/COD/XR/DEP/DUP/MOD)/**human**、naive self-review 常時 block）。
- **標準 4 軸**（A1 DoD / A2 上流 trace 孤児0 / A3 V-pair 実在+双方向 / A4 sub-doc 整合）。Critical=0 → CONDITIONAL PASS。
- **auto-enroll rule engine**（11 rule 型: pair-exists/ref-resolves/trace-bidir/upstream-coverage/count-matches/id-format/dup-id/glossary-delta/dependency-drift/asset-drift/backlog-format）: 新 doc が現れたら frontmatter 形状にマッチする全 rule が**自動適用**（lint 手書き不要）。`gate-checks.yaml` が G_N の rule id 集合を宣言。rule は純関数（LLM/外部 API 不使用）= 決定論。
- **構造 vs 意味の境界**: 構造的整合 → engine 自動 / 意味的整合 → review(subagent/cross-agent/human)。
- `runDoctor` = 60 checker ok=AND fail-close。`checkDbProjectionIngestion` は `:memory:` で rebuild → rowCounts 検査。

## 5. 設計 corpus（L0-L14 + FE）

- **V-pair map**（設計⇔検証、同一 test-design doc を pair_artifact で双方向 trace）: L1↔L14 / L2↔L10(wireframe self-pair) / L3↔L12 / L4↔L9 / L5↔L8 / **L6↔L7**。L4/L5 は集合 pair（sub-doc 群 → 1 test-design doc）。`vmodel-lint` が孤児0/ref-resolves/trace-bidir を検証。
- **L6 粒度**: 単一関数=1 DbC(pre/post/invariant)+1 U-* oracle。`function-spec.md`+18 専門 doc。`fr-unit-coverage.md` matrix が FR-L1（51 件）→ L6 spec path → unit contract → U-* oracle を 1:1 管理、`l6-fr-coverage.ts` が機械ガード。**L7 は matrix 内契約を実装するだけ（新 FR 発明禁止）**。
- **frontmatter 契約**: `layer / status(confirmed↔gate PASS 連動) / pair_artifact(self 特例あり) / next_pair_freeze / plan / sub_doc`。ID 体系: BR-/FR-L1-/NFR-/PM-HM-GD(画面)/U-<GROUP>-/IMP-/PLAN-/ADR-。
- **FE per-layer 降下**（`document-system-map §1c`）: L1 screen-requirements → L2(screen-list/flow/ui-element/wireframe) → L3 screen-functional → L4 **ui-standard + tokens.yaml(デザイントークン SSoT)** → L5 ui-detail → L6 screen-spec → **L7 src/web(未実装=唯一の greenfield)** → L10 visual-design。slot 登録≠body 完成（coverage≠substance）。

## 6. Process / Governance / Test-design / ADR

- **工程定義正本** = `document-system-map.md`(§1 L0-L14 master 表) + `gate-design.md`(§1 gate model)。専用 `docs/process/forward/` は無い。
- **document-system-map**: §1b 外部設計成果物カタログ（VALID_SUB_DOCS[L4]、①必須/②プロダクト選択）/ §1c FE per-layer 定義（上記）/ §2 国際標準クロスマップ(ISO 29148/arc42/IEEE 1016/ISO 29119-3/ISO 25010) / §3 DbC 配線 / §4 フロー改善(Z1-Z6/IMP)。
- **test-design 体系**: L1 OT-(47) / L3 AT- / L6→L7 U- / L5→L8 IT- / L4→L9 ST-。量閉じ=孤児0。`proposal-document-coverage-routing` が提案テキスト→coverage tier(G0-G5)→必要 design/test-design doc を union（LLM 縮小語で必要 doc を減らすのは `llm-shrinkage-ignored` で禁止）。
- **ADR 確定事項**: ADR-001(全面再実装/**TS/Bun**/zod 単一正本/単一バイナリ配布) / ADR-002(全依存→schema 一方向・循環禁止・pure+loader 分離) / ADR-003(runtime adapter ACL・**API key 非保持**) / ADR-004(内部資産 TS 制御境界) / ADR-005(**GitHub-pull 配布 + 中央 Web UI**・非 npm) / ADR-006(commander) / ADR-007(**harness.db=projection+feedback**・raw transcript/secret/PII 非保存)。

## 7. Harness / Runtime（D8）

- **AI 実行規律 8 層**: ①agent-guard allowlist fail-close（14 subagent allowlist、subagent_type/model 必須、frontmatter `model:` family 一致、bypass=`UT_TDD_ALLOW_RAW_AGENT=1`+evidence）②model family 一致強制 ③**tier-router**（T0=opus/gpt-5.5 は consult/verify のみ・FrontierAuth.explicit 必須、worker=se/docs は T1/T2 固定で上位帯到達不可）④**work-guard**（他 runtime uncommitted への盲目 Edit を block）⑤**review-guard**（tl/qa/reviewer 等 read-only role の working-tree 変更を violation）⑥**attempt-escalation**（同一 subject 3 連続失敗 → EscalationSignal、症状追いループを機械停止）⑦forced-stop（ESC/Ctrl+C 後追い記録 → pmo-haiku 分類 → high は Recovery 提示）⑧agent-slots（default 8 並列、5 分 stale 失効）。
- **hook**: `.claude/hooks/{agent-guard,work-guard,session-log}.ts` shim（stdin JSON → `src/cli.ts` dispatch、guard 系 exit 2 で block / log 系 fail-open exit 0）。session-log は tool/path/verb のみ記録（値・引数・secret はマスク）、commit から PLAN ID 推論で active plan 配線。
- **CI**: `.github/workflows/harness-check.yml` 単一集約 job（tsc → db rebuild → vitest → biome → doctor）。Branch Protection Required check = これ 1 本。
- **住所モデル 3 層**（`ai-agent-harness-directory-reference.md`）: Layer A 指示(CLAUDE.md/AGENTS.md) / B-local 決定論ゲート(.claude/settings.json+hooks) / B-remote 品質ゲート(.github) / C Branch Protection。runtime state = `.ut-tdd/`（state/logs/handover、gitignore）。
- **adapter**（ADR-003 実体）: `buildAdapterPlan()` が claude/codex を `AdapterIntent` 統一入力、provider 別 args + stdin プロンプト + context injection（required/optional paths）。API key 非保持、起動方式のみ吸収。

## 8. Skills / Templates / PLAN 体系

- **skill 52 件 + SKILL_MAP**（`schema_version: skill.v1` / name / skill_type(process/design-contract/verification/drive-reverse/orchestration/review/testing) / applies_to.layers / drive_models）。`ut-tdd skill suggest --plan` でスコア選抜・常時全件ロード禁止（HELIX と同思想）。
- **PLAN 体系**: 命名 `PLAN-<PREFIX>-<NN>-<slug>`（PREFIX=L1-L7/DISCOVERY/REVERSE/RECOVERY/**M(Milestone/master-hub)**）。**kind 11 enum**（impl/design/add-design/add-impl/poc/reverse/recovery/refactor/retrofit/troubleshoot/research）。status(draft/active/pair-freeze/trace-freeze/done/cancelled)。frontmatter: plan_id/kind/layer/drive(be/fe/fullstack/db/agent)/agent_slots/generates(artifact_path+type)/dependencies(parent/requires/blocks)/**review_evidence**(reviewer/review_kind/reviewed_at/tests_green_at/verdict/worker_model/reviewer_model)。Reverse 専用=`forward_routing`(=HELIX forward_return)/`promotion_strategy`(reuse-as-is/with-hardening/redesign、**HELIX 未実装**)/`confirmed_reverse_type`。親子=`dependencies.parent` 1 段 + master-hub PLAN。
- **template**: design/impl が §0-§7 強制（**§6 用語 delta / §7 FR delta を全 PLAN 強制 = doc anti-drift、HELIX 未実装で取り込み価値高**）。impl §3 = Sprint 標準 8 step、DoD=`tsc --noEmit`+`vitest` 全 PASS。`vmodel.json`=4 artifact(design/impl/test_design/test_code)+8 edge+3 freeze(pair/red/trace)。
- harness 自身が `docs/migration/helix-porting-map.md` を保有（HELIX→harness の porting map。統合フェーズで参照）。

---

## 9. Charter 前提の訂正（capture が無効化した凍結事項）

| # | charter/旧 V3 corpus の凍結 | clean harness 実態 | V3 での扱い |
|---|---|---|---|
| 1 | DB = core 14 + Phase2 拡張 | SCHEMA_VERSION=18 / 実 ~56 table（clean registry） | **harness の 56-table registry から作り直す** |
| 2 | `test_results`(current) ≠ `test_result_events`(履歴) を別 table 凍結 | `test_result_events` 不在・全 table rebuild TRUNCATE で event 永続せず | **(b) projection + append_event を V3 で分類凍結**（TL confirmed: 監査/red-first 履歴要求は時系列証跡 → projection-only 不可。§9.5） |
| 3 | C3 = DB 駆動 detector / file scan 禁止 | detector は file-scan + DB-projection の**混在**。普遍は pure-function 3 層 + ok=AND + lint-wiring + absence-blindness | **C3 文言を「pure-function 3 層・source は file/DB 両可」へ修正** |
| 4 | D7 FE = HELIX 最大の優位・新規 build（fork src/web 空） | FE ガバナンス（§1c/frontend-design-coverage/screen-impl-pair-freeze/screens table/tokens.yaml/design-bottomup）は **harness が機械契約済で保有**。空なのは実 UI 描画(src/web)のみ | **FE ガバナンスは harness から盗む / 描画だけ greenfield** |
| 5 | 駆動 9-10 mode | **13 mode**（+screen-design/frontend-design/design-bottomup） | **13 mode を採用** |
| 6 | ADR-001 = TS/Bun | 同左（harness 正本） | **V3 は Python へ反転**（公開 API/テスト資産保護、ユーザー方針） |

**HELIX/V3 が持たず harness から新規に盗む価値**: `promotion_strategy` / 全 PLAN §6・§7 delta(anti-drift) / auto-enroll rule engine(11 型) / tier-router(T0-T2) / attempt-escalation(3-strikes) / refactor-candidate detector / review-guard / 4-provider 住所モデル / vmodel.json。

## 9.5 TL 確定契約（freeze-blocking の解消、tl-advisor 2026-06-26 changes_required→go 条件）

freeze 前に **§9/§10 を以下の契約で固定する**こと（TL: これ無しの freeze は不可、契約反映後は go）。engine 実装前に最初に凍結すべき最小不変条件でもある。

**C-1 table 分類（projection ⊥ append_event）**: 全 table を `projection`（rebuild 全消し再投影）か `append_event`（冪等追記・truncate 対象外）に分類。`rebuild_projection(db, sources)` は projection table のみ TRUNCATE+再投影。`append_event(db, event)` は append table へ冪等追記、logical_key = `event_id` or `(run_id, seq, kind)`。**clean harness 実態は projection-only（全 TRUNCATE）だが、V3 は append_event を独自差分として追加**（red-first/green-digest/review-guard/hook-bypass 監査は時系列証跡）。`test_results`=current projection / `test_result_events`=red→green 履歴（用途分離）。event table 側に retention/PII/secret-mask/raw-transcript 非保存を必須契約化。

**C-2 row identity**: 各 table に `logical_key`（冪等 upsert キー）/ `stale_key`（source hash 差分で stale 判定）/ `delete_scope`（rebuild で消える対象か）を定義。同一 input で projection rebuild 2 回は bit-identical、append_event は rebuild 後も残存。

**C-3 detector 契約**: detector core は必ず pure function（I/O は loader 隔離）。各 detector に **`source_kind: db_projection | file_snapshot | hybrid`** を明示。file source は loader が snapshot 化し absence を `ok=false`（scope-0 silent OK 禁止）。`runDoctor.ok = AND` + lint-wiring 到達性維持。cutover 後の hard gate は可能なものから DB projection source へ昇格する方針を残す（「DB-only」でなく「source 宣言 + pure analyzer + fail-close aggregation + wiring」で厳格性を担保）。

**C-4 cutover gate**: C1/C2 だけでなく **cutover detector（pin inventory / dangling reference / rollback condition）が green になるまで cutover 禁止**。

**C-5 secret 境界**: secret / PII / raw provider transcript を DB に保存しない（ID・理由・score・redacted summary のみ）。

**doc 文言修正（P2）**: 既存 `docs/v3/engine/detector-wiring.md` / `V3-CHARTER.md` に残る「DB-only」表現を上記 C-3 に合わせて修正（capture と矛盾するため）。

## 10. V3 再構築プラン（capture 後）

**忠実に保持する核（言語非依存の設計意図）**: schema 単一 registry SSoT + 識別子 fail-close / projection rebuild 原子性 + 冪等 upsert + stableId / pure-function 3 層 detector + ok=AND + absence-blindness 防止 / lint-wiring メタゲート / baseline ratchet shrink-only / 13 駆動 mode 契約 + routing + design-bottomup / gate G0.5-G14 + judgment review tier + 標準 4 軸 + auto-enroll rule engine / V-pair + L6 粒度 + FE per-layer / agent-guard・tier-router・work/review-guard・attempt-escalation / PLAN/skill/template 体系 + §6/§7 delta。

**Python 化で変える表層**: zod→pydantic+Enum / bun:sqlite→stdlib sqlite3 / vitest→pytest / TS shim→Python(or Bash+py) hook / biome→ruff / `ut-tdd` CLI → `helix runtime` 系へ吸収 / BFS import graph → ast/importlib。公開 API `@~/.helix/core/<path>` 据え置き。物理 FK は同一 DB 内のみ。

**実行順（charter §6 を実態で更新）**: Phase 1-4(docs/v3 を本 capture から再構築・Python 化) → **Phase 6 engine 実装先行**(C1 schema-registry → C2 projection-writer、test-first・Codex 委譲・L7 PLAN 起票) → Phase 5 cutover(engine が rebuild 可能化後、破壊的・escalation) → Phase 7(DB 構築 + idempotent/deletion/stale 検証) → Phase 8(detector + lint-wiring + baseline) → HELIX 独自強化フェーズ(FE 描画/配布/HELIX W/既存 AI 規律 hook の上乗せ)。

## 11. 漏れ・未読（次フェーズで補完）

- Engine: `maintenance.ts`/`drive-registration.ts`/`schema/roadmap.ts`/`frontmatter.ts`、projection-writer 中間 projector 群、`upsertRow` 実装詳細。
- Detector: `coding-rules.ts`/`ddd-tdd-rules.ts`(AST rule 具体)、`g1/g3-trace`、`l6/l7-completion`、`plan/lint.ts` enum 全列、`verification-profile-safety` secret パターン、`vmodel/lint.ts` pair 判定式。
- Harness: `src/web`/`src/setup`/`src/cli.ts`(SubagentStop 実体)/`graph/loader.ts`/`.claude/commands/*`/shim/config 詳細、`team/run.ts` 直列化、`guardrail/ledger.ts` block 処理。
- Design corpus: L3 functional-requirements/business-detail/nfr-grade、L4 data/function 本文、L5 if-detail/internal-processing、L6 専門 doc 本文、`gate-design.md` PASS/park 表。
- Process: concept_v3.1.md / requirements_v1.2.md(FR registry SSoT) / ADR 本文 / audit-framework / ddd-tdd-rules / repository-structure。
- Skills: skill 本文（frontmatter のみ確認多数）、PLAN 331 件中代表 8 件のみ精読、`docs/process/modes/*`、`review-checklist.yaml`。
