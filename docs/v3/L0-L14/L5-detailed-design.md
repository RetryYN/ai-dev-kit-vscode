# HELIX V3 — L5 詳細設計（内部設計）

> **status: draft**（TL review → freeze 前）
> 入力: [L4 基本設計](L4-basic-design.md) / [engine keystone](../engine/) / [fork extract](../../research/2026-06-25-fork-engine-design-extract.md)
> 対の検証（V-model L5↔L8）: §4 結合テスト設計

本書は C1 テーブル inventory・C2 projection rule・C6 workflow 契約 schema を**モジュール粒度**で確定する。detector の関数粒度は L6 機能設計。

---

## 0. 方針

clean harness の **56-table registry を忠実に採用**する（[capture §1](../audit/2026-06-26-new-base-comprehensive-capture.md) が harness 実体 / [C1 schema-registry §5](../engine/schema-registry.md) が **table 分類の唯一の SSoT** = projection⊥append_event⊥config）。V3 base は harness 56 に 2 table を明示追加し、HELIX 個人開発版はさらに 4 projection table を追加する = **62**（`test_result_events`=append 監査 / `functional_registry`=projection 機能一覧 SSoT / `template_catalog`・`doc_coverage`・`prompt_interpretations`・`learning_candidates`=AI 自走と設計資産化の projection）。個人開発版 4 table の列/PK/identity は [personal-edition-schema-contract](../engine/personal-edition-schema-contract.md) で freeze する。**`baseline_registry` は table でなく C5 baseline frozenset（code 定数、harness 同様）**。駆動 workflow の `forward_routing` は `drive_runs` 列。§1 は detector が query する V3-core（あるべき集合の供給源）の主要 table を抜粋し、全 62 の分類は C1 §5 を参照する（本書では再分類しない）。

## 1. C1 テーブル inventory（V3 core, 確定）

| table | あるべき集合 | 主要列（抜粋） | fork 対応 |
|---|---|---|---|
| `plan_registry` | 登録 PLAN 全件 | id, kind, status, layer, drive, forward_return | plan_registry |
| `artifact_registry` | doc/設計/code/test の実在 | path, kind, layer, stale_status, content_hash | artifact_registry |
| `functional_registry` | 機能一覧（V3-core, C1 §5 登録, projection） | fn_id, fr_id, layer, maps_to | （fork は FR を artifact 側で表現 → V3 が table 昇格） |
| `trace_edges` | 縦断 trace（req→plan→design→test→source→db） | from_id, to_id, edge_kind | trace_edges |
| `coverage` | design/test カバレッジ | subject_id, kind, covered_by | coverage |
| `test_cases` | UT/IT/ST/AT 全件 | ut_id, layer, oracle, anchor_path | test_cases |
| `test_results` | テスト実行結果（最新/current） | ut_id, status, run_id, digest | test_results |
| `descent_obligations` | L6→L7 降下義務 | trace_key, status | descent_obligations |
| `gate_runs` | gate 通過 | gate_id, plan_id, status | gate_runs |
| `drive_runs` / `workflow_runs` | 駆動 workflow 通過 + forward_return | drive, plan_id, forward_return, passage | drive_runs/workflow_runs |
| `findings` | detector 出力 | detector_id, severity, subject, missing | findings |
| `review_evidence_registry` | 定性 review 証跡 | plan_id, reviewer, verdict, evidence_hash | review_evidence_registry |
| `screens` / `screen_trace` | FE 画面と trace | screen_id, category / screen_id, trace | screens/screen_trace |

> 確定: 物理 FK は同一 DB 内のみ（trace_edges.from_id 等は logical reference、consistency は detector）。**冪等キー・stale 判定・削除スコープ・projector は §1.5 で凍結**（L5↔L8 結合テストが書ける粒度）。物理 column の型・補助列の細部だけ L7 実装へ残す（推測 schema を避ける＝CLAUDE.md「永続化要求が観測されてから schema 確定」）。

## 1.5 投影キー契約（凍結・L5↔L8 freeze 粒度）

projection-writer（C2）の idempotent / deletion / stale は **row identity が契約**。table 名だけでは結合テストが書けない（TL P1#1）ので、table ごとに次を凍結する（物理 column 型のみ L7）:

| table | logical_key（冪等単位） | stale_key（stale 判定） | delete_scope（source 消失で消える単位） | projector_owner |
|---|---|---|---|---|
| plan_registry | plan_id | —（current のみ） | plan_id | project_plan |
| artifact_registry | path | content_hash | path | project_artifact |
| functional_registry | fn_id | registry yaml hash | fn_id | project_fr |
| trace_edges | (from_id, to_id, edge_kind) | — | from_id の source artifact | （各 projector が emit） |
| coverage | (subject_id, kind) | — | subject_id の source | project_coverage |
| test_cases | ut_id | anchor_path hash | ut_id | project_test |
| test_results | (ut_id, run_id) | run digest | run_id | project_test_result |
| descent_obligations | trace_key | — | trace_key | project_descent |
| gate_runs | (gate_id, plan_id, run_id) | — | run_id | project_gate |
| workflow_runs / drive_runs | (drive, plan_id, run_id) | — | run_id | project_workflow |
| findings | (detector_id, subject) | —（毎 run 再生成） | detector run 全消し | C3 detector-runner |
| review_evidence_registry | (plan_id, reviewer, run_id) | evidence_hash | run_id | project_review |
| screens / screen_trace | screen_id | — | screen_id | project_screen |
| template_catalog | template_id | source_url + normalized_sections hash | template_id | project_template |
| doc_coverage | (layer, doc_kind, subject_id) | coverage digest | subject_id | project_doc_coverage |
| prompt_interpretations | (prompt_id, viewpoint) | interpretation_hash | prompt_id | project_prompt |
| learning_candidates | candidate_id | source_event_hash | candidate_id | project_learning |

- **deletion = source 消失** → rebuild 全消し再投影で当該 logical_key の行が再投影されず**消える**（行を残さない）。
- **stale = source は在るが stale_key（content_hash/digest）が前世代と不一致、または superseded（古い参照）** → `stale_status=stale` で**行は残す**。
- 両者は**排他**（TL P1#3）: source 消失は deletion（行消失）、内容変化/supersede は stale。

## 1.6 Phase 2 拡張 table（FE / harness / HELIX W、凍結）

FE（[fe](../fe/fe-ui-design.md)）/ harness（[harness](../harness/harness-design.md)）/ HELIX W（[helix-w](../helix-w-design.md)）/ HELIX personal extension 関連 table を §1 V3-core と同じ契約粒度（logical_key / stale_key / delete_scope / projection⊥append_event）で凍結する。これらは **62-table registry（[C1 §5](../engine/schema-registry.md) が分類 SSoT）の一部**であり、SSoT 外に置かない。

| table | logical_key | stale_key | delete_scope | projector_owner | 区分 |
|---|---|---|---|---|---|
| review_evidence_registry | (plan_id, reviewer, run_id) | evidence_hash | run_id | project_review | projection |
| hook_events | (hook_name, run_id, seq) | — | run_id | project_hook_events | append_event |
| guardrail_decisions | (guardrail, run_id, seq) | — | run_id | project_guardrail | append_event |
| test_result_events | (ut_id, run_id, seq) | — | run_id | project_test_result_events | append_event |
| impact_rules | rule_id | rule hash | rule_id | project_impact | config |
| impact_results | (rule_id, run_id) | — | run_id | project_impact | projection |
| template_catalog | template_id | normalized_sections hash | template_id | project_template | projection |
| doc_coverage | (layer, doc_kind, subject_id) | coverage digest | subject_id | project_doc_coverage | projection |
| prompt_interpretations | (prompt_id, viewpoint) | interpretation_hash | prompt_id | project_prompt | projection |
| learning_candidates | candidate_id | source_event_hash | candidate_id | project_learning | projection |

- **projection(53) 区分** = §1.5 と同じ全消し再投影（rebuild で TRUNCATE → idempotent/deletion/stale）。**`config`(6) は rebuild 非対象**＝ seed/migrate/init 管理で truncate されず rebuild 後も残存（[C1 §5](../engine/schema-registry.md)。config を truncate すると seed state 消失 = 禁止）。
- **append_event 区分**（C1 §5 = 3 件のみ: `test_result_events` / `hook_events` / `guardrail_decisions`）= immutable event table。rebuild 全消しの**対象外**（red→green 証跡・hook/bypass 判定・review-guard 決定は current source から再導出不能）。projection-writer は append のみ。delete_scope=run 単位の retention（保持期間は C5 ADR）。`impact_results` 等の `*_events` 名 table は projection（再導出可能）。
- **`test_results`（projection=最新/current）と `test_result_events`（append=red→green 履歴）は別 table・別用途**（P2 表記揺れ解消）: 「現在 green か」は `test_results` を query（current 判定）、red-first / green-command-digest は `test_result_events`（履歴）を query。
- **phase 次元（HELIX W、P1-5 確定）**: `plan_registry` / `artifact_registry` / `trace_edges` に `phase ∈ {general, agent}` を**属性列**で持つ（`phase_join` table は立てない＝1 DB・列方式）。default=`general`、single-V（agent system でない）は全行 general の degenerate。logical_key には含めない（plan は 1 phase 所属）。L10 合流 gate は C3 が「agent 行が存在するとき両 phase の pair_closure AND」を要求。

## 2. C2 projection rule（artifact 種別 → table, 確定）

| artifact 種別 | 入力 path（例） | 投影先 table | 冪等キー |
|---|---|---|---|
| PLAN | `docs/plans/L*/*.md` | plan_registry, artifact_registry | plan id |
| 設計 doc | `docs/v3/L*/*.md`, `docs/v3/engine/*.md` | artifact_registry, trace_edges | path |
| code | `cli/**/*.py`, `cli/helix*` | artifact_registry（code_catalog 相当） | path |
| test | pytest / bats | test_cases, test_results（current）, test_result_events（履歴・append）, trace_edges | ut_id |
| FR | `functional-registry.yaml` | functional_registry | fn_id |
| workflow 定義 | workflow doc / 設定 | workflow_runs, drive_runs | drive+plan |
| gate 結果 | gate 実行 | gate_runs | gate_id+plan |
| review 証跡 | review 出力 | review_evidence_registry | plan_id+reviewer |
| FE 画面 | screen 設計 / 状態遷移 trace | screens, screen_trace | screen_id |
| 設計テンプレート | 外部 URL / 社内テンプレート / 標準 doc map | template_catalog, doc_coverage | template_id / layer+doc_kind+subject_id |
| prompt 解釈 | user prompt / handover / PLAN 入力 | prompt_interpretations, findings | prompt_id+viewpoint |
| learning candidate | findings / review / postmortem / test_result_events | learning_candidates, trace_edges | candidate_id |
| harness append_event | test 実行(red→green) / hook capture / bypass / review-guard | test_result_events, hook_events, guardrail_decisions | run_id |

- **rebuild 方式**: テーブルごと全消し → 上表の rule で全 artifact を再投影（idempotent/deletion を同時担保）。
- **stale**: content_hash 不一致 or superseded（古い参照）で `stale_status=stale`（行は残す）。**source path 消失 = deletion（rebuild で行消失、stale ではない）**。§1.5 の deletion/stale 排他に従う。
- **3 経路を混同しない（[C1 §5](../engine/schema-registry.md) が分類 SSoT、本書で再分類しない）**: ①**rebuild TRUNCATE 対象 = projection 53 のみ**（上表「PLAN〜FE 画面」「設計テンプレート」「prompt 解釈」「learning candidate」行 = projection write）／②**config 6 = seed/migrate/init 管理**（truncate 対象外・rebuild 残存）／③**append_event 3 = append path**（上表「harness append_event」行のみ。truncate 対象外、`append_event(db,event)` 経由）。`rebuild_projection` は ① のみ全消し再投影する。`artifact_progress` は capture では独立 table（harness 実態）だが純関数 `derive_artifact_progress_decision` で color 導出。test↔artifact trace は `trace_edges` + `test_artifact_edges`。

## 3. C6 workflow/doc 契約 schema（frontmatter, 確定）

| kind | 必須 frontmatter field | 必須セクション |
|---|---|---|
| plan | id, kind, status, layer, drive, generates[], requires[], blocks[] | 目的 / 受入条件 / 工程 |
| design | id, layer, generates[], pairs_test_design, trace[] | 契約(DbC) / 検証 |
| workflow(駆動) | id, kind(driving), **forward_return**, workflow_chain[] | 起動条件 / 収束ループ / 戻し先 |
| fr | fn_id, fr_id, layer(L4/L5/L6), maps_to[] | （registry 行） |
| plan.review_evidence ブロック（P1-3） | review_kind(cross_agent\|intra_runtime_subagent), worker_model, reviewer_model, tests_green_at, reviewed_at, red_at?, green_at?, evidence_hash | （PLAN frontmatter の review_evidence ブロック） |
| template | template_id, source_url, source_kind(web\|internal\|standard), doc_kind, layer, required_sections[], pair_test_kind, provenance_hash, freshness_status, license_note | 目的 / 適用 layer / 必須項目 / 対応テスト設計 / 採用しない項目 |
| prompt_interpretation | prompt_id, viewpoint(scope\|acceptance\|risk\|test\|doc\|escalation), interpretation, conflicts[], generated_findings[] | 解釈 / 矛盾 / gate 影響 |
| learning_candidate | candidate_id, source_event, candidate_kind(plan\|rule\|template_gap\|debt), forward_return, discard_reason? | 根拠 / 昇格先 / 検証条件 |

- ID 規約（正規表現確定）: `FR-[A-Z]+-\d+` / `FN-[A-Z]+-\d+` / `UT-[A-Z]+-\d+` / `PLAN-L\d+-.+`。
- forward_return 値域: Forward の L（L0-L14）。駆動 workflow で欠落は violation（C3 detector）。
- review_evidence（P1-3）: `worker_model` 取得元 = agent guard の subagent_type→model family マップ、`reviewer_model` = review 実行 role。`cross_agent` は `reviewer_model ≠ worker_model` 必須。`tests_green_at ≤ reviewed_at` 必須。`red_at < green_at` は red-first 検証用（任意だが red-first 対象 UT は必須）。`evidence_hash` で改ざん検出。→ `review_evidence_registry`（C2 project_review）。

## 4. 結合テスト設計（L5 ↔ L8 pair・対の検証）

module 結合（C1↔C2↔C6 の境界）:

| IT-ID | 結合シナリオ | 対応 |
|---|---|---|
| IT-V3-01 | C6 parse → C2 project → C1 schema の列に valid 行が入る（種別→table 一意） | C6→C2→C1 |
| IT-V3-02 | content_hash 変更 → rebuild → stale_status 遷移（current→stale） | C2 stale |
| IT-V3-03 | C3 detector の query が C1 schema の実列と一致（存在しない列を引かない） | C3↔C1 |
| IT-V3-04 | 駆動 workflow doc（forward_return 付き）→ drive_runs に passage 行 | C6→C2 |
| IT-V3-05 | trace_edges の from/to が plan_registry/artifact_registry の id を logical 参照（cross-DB FK なし） | C1 FK 方針 |
| IT-V3-06 | functional_registry の fn_id ↔ test_cases の ut_id が 1:1（FN↔UT pair） | C1 整合 |
| IT-V3-07 | template_catalog → doc_coverage → findings の結合で、L3 受入テスト設計が欠落した subject を検出 | C7→C2→C3 |
| IT-V3-08 | prompt_interpretations の escalation viewpoint が auth/pii/prod を検出し、auto-run gate が停止 | C9→C3 |
| IT-V3-09 | learning_candidate が forward_return 付きなら PLAN draft candidate、欠落なら violation | C10→C6 |

## 5. 次工程

→ **L6 機能設計**（C3 detector を関数粒度 + DbC で確定。V3 detector inventory を fork 61 から V3 table 集合へ写像。単体テスト設計と対）。
