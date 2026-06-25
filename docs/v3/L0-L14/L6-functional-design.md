# HELIX V3 — L6 機能設計（detector 仕様・関数粒度 + DbC）

> **status: draft**（TL review → freeze 前）
> 入力: [L5 詳細設計](L5-detailed-design.md) / [engine/detector-wiring](../engine/detector-wiring.md) / [fork extract §4](../../research/2026-06-25-fork-engine-design-extract.md)
> 対の検証（V-model L6↔L7）: §4 単体テスト設計（関数 1 個 = UT 1 個の粒度）

本書は C3 detector を **関数粒度 + DbC（requires/ensures/invariant）** で確定する。clean harness の **~60 detector**（[capture §2](../audit/2026-06-26-new-base-comprehensive-capture.md) が全 inventory）を V3 の table 集合（L5 §1）へ写像し、**core 16（FN-DET-01〜16）を第 1 波**として下表に定める（残りは Phase 8 で baseline ratchet 昇格）。粒度原則: detector 関数 1 個 = 単体テスト対象 1 個。各 FN-DET は §1 の `source_kind` を宣言する（下表「query table」は db_projection 系の query 先、file_snapshot 系は loader が snapshot 化）。

---

## 1. detector 契約パターン（DbC template）

```python
# pure-function 3 層（TL C-3）: analyze（純関数）/ load（I/O 隔離）/ messages
def load_<name>_input(repo_root, db) -> Input:  ...   # source_kind ごとに DB query or file snapshot 化
def analyze_<name>(input: Input) -> Result:     ...   # 純関数（I/O なし）
def <name>_messages(result: Result) -> list[Finding]: ...
# source_kind: "db_projection" | "file_snapshot" | "hybrid"
```
```
requires:  source_kind に応じ DB row（C2 投影済）or file snapshot が load 済
ensures:   findings は (あるべき集合 − 実在集合) を全件 = もれを過不足なく返す
invariant: analyze は純関数（I/O は loader 隔離）/ source_kind 宣言 / absence(DB row/file 不在・空)=ok=false（scope-0 silent OK 禁止）/ severity 宣言
```
- 共通: `CheckResult{ok, messages:[Finding{id, severity, subject, missing}]}`。`ok=False` で doctor の AND に連動（hard）、advisory は ok 非連動（warning surface）。I/O 失敗=ok=false。

## 2. V3 core detector inventory（fork 61 → V3 写像）

| FN-ID | detector | query table | 欠落判定（あるべき−実在） | severity | fork 対応 | UT |
|---|---|---|---|---|---|---|
| FN-DET-01 | plan-artifact-existence | plan_registry, artifact_registry | PLAN.generates の artifact が未実在 | hard | plan-artifact-existence | UT-DET-01 |
| FN-DET-02 | plan-completion-drift | plan_registry, artifact_registry | artifact 在るのに PLAN status=draft 放置（逆向き drift） | hard | merged-plan-status/plan-completion-drift | UT-DET-02 |
| FN-DET-03 | trace-symmetry | trace_edges | req↔plan↔design↔test の片方向 edge（双方向非対称 orphan） | hard | g1-trace/propagation/backfill-pairing | UT-DET-03 |
| FN-DET-04 | descent-obligation | descent_obligations, test_cases | L6 active で L7 impl(test_cases) 未登録 traceKey | hard | descent-obligation | UT-DET-04 |
| FN-DET-05 | fn-ut-pair | functional_registry, test_cases | fn_id に対応する ut_id 不在（FN↔UT 1:1 違反） | hard | l6-fr-coverage/entity-coverage | UT-DET-05 |
| FN-DET-06 | oracle-test-trace | test_cases, trace_edges, baseline_registry | oracle 未 trace のうち baseline 外のみ | hard(ratchet) | oracle-test-trace(+baseline) | UT-DET-06 |
| FN-DET-07 | gate-confirm | gate_runs, plan_registry | PLAN の必須 gate 未通過 | hard | gate-confirm/right-arm-gate-planning | UT-DET-07 |
| FN-DET-08 | drive-passage | drive_runs, plan_registry | 駆動 workflow の forward_return 欠落/未通過 | hard | drive-model-passage/scrum-reverse | UT-DET-08 |
| FN-DET-09 | review-evidence | review_evidence_registry | 改ざん/未 anchor の定性 review（hash 不一致） | hard | review-evidence | UT-DET-09 |
| FN-DET-10 | lint-wiring | （detector registry + 到達集合） | registry − 到達 − DEFERRED = 死蔵 | hard | lint-wiring | UT-DET-10 |
| FN-DET-11 | db-projection-coverage | 全投影 table | 投影 row-count が期待下限未満（projection 健全性） | advisory→hard | db-projection-coverage/-ingestion | UT-DET-11 |
| FN-DET-12 | schema-ssot | （schema 定義静的） | registry 外 CREATE TABLE / cross-DB FK | hard | （V3 独自、schema-registry 由来） | UT-DET-12 |
| FN-DET-13 | fe-screen-pair | screens, screen_trace | drive=fe/fullstack で screen↔trace 片肺 | hard(drive-gated) | screen-impl-pair-freeze | UT-DET-13 |
| FN-DET-14 | dist-api-consistency | artifact_registry（manifest/loader） | core-manifest⇔setup.sh⇔loader 不一致（公開 API 回帰） | hard | runtime-portability/tracked-canonical | UT-DET-14 |
| FN-DET-15 | doc-contract | artifact_registry, findings | frontmatter/必須セクション/ID 規約違反 | hard | doc-consistency/sub-doc-section-structure | UT-DET-15 |
| FN-DET-16 | rule-drift | （rule registry） | coding/ddd rule registry と実態の drift | advisory | coding-rules/ddd-tdd-rules/rule-drift | UT-DET-16 |

> fork の残り lint（telemetry-closure / improvement-backlog / feedback-log / change-impact / module-drift / asset-drift / proposal-document-coverage / verification-profile / readability 等）は V3 の observability / advisory 層として **Phase 8（検出系強化）で段階追加**（baseline ratchet で advisory→hard 昇格）。core 16 を先に閉じる。

> **foundation P2（L7 着手前に決定・TL 2026-06-25）**: fork の relation-graph / `dependency_edges` / `graph_nodes` orphan 検出を V3 では FN-DET-03 trace-symmetry に圧縮した。依存漏れ・V-model 片肺をより強く検出するため、**`dependency_edges` を独立 table 化して FN-DET-03 を拡張するか、専用 detector（dependency-orphan）を足すか**を L7 着手前に決定する（圧縮のまま L7 に進まない）。

## 3. 代表 detector の full DbC（粒度 exemplar）

### FN-DET-02 plan-completion-drift
```
requires:  plan_registry と artifact_registry が C2 投影済（同一 rebuild 世代）
ensures:   {p ∈ plan_registry | p.generates が artifact_registry に全て実在
            ∧ p.status ∈ {draft,in_progress}} を findings に全件（artifact 完成済なのに未 close）
invariant: file を stat しない（artifact_registry の実在フラグを使う）/ severity=hard
UT-DET-02: artifact 全実在 + PLAN draft の fixture → 1 finding。PLAN completed → 0 finding。
```

### FN-DET-04 descent-obligation
```
requires:  descent_obligations（L6 active）と test_cases が投影済
ensures:   {o ∈ descent_obligations | o.status=active
            ∧ ¬∃ tc ∈ test_cases. tc.trace_key=o.trace_key} を findings に全件
invariant: trace_key の ID 規約（L5 §3）で突合 / severity=hard
UT-DET-04: active obligation + 対応 test_case 無し → 1 finding。test_case 追加 → 0。
```

### FN-DET-10 lint-wiring
```
requires:  detector registry のキー集合、RUNTIME_ENTRYPOINTS から到達する detector 集合、DEFERRED
ensures:   dead = registry − 到達 − DEFERRED、stale_deferred = DEFERRED ∩ 到達 を findings
invariant: dead=∅ ∧ stale_deferred=∅ で ok / severity=hard
UT-DET-10: 未配線 detector 追加 → dead に1件。DEFERRED 明示 → 0。到達可能を DEFERRED → stale 1件。
```

### FN-DET-06 oracle-test-trace（ratchet 連動）
```
requires:  test_cases, trace_edges, baseline_registry[oracle] が投影済
ensures:   missing = {未 trace oracle}、findings = missing − baseline（新規のみ hard）
invariant: baseline は縮小のみ（C5 ratchet）/ baseline 内は advisory surface
UT-DET-06: baseline 外 missing → hard fail。baseline 内 missing → advisory（ok 維持）。
```

## 4. 単体テスト設計（L6 ↔ L7 pair・対の検証）

- 各 FN-DET-NN に **UT-DET-NN を 1:1 対**で置く（粒度ペアリング原則: 関数 1 = UT 1）。
- UT は **DB fixture（in-memory SQLite に C1 schema + 既知行を投入）** で「あるべき集合 − 実在集合」の境界を突く（positive: もれ有→finding / negative: 充足→0 finding / boundary: baseline 境界）。
- L7 実装時に UT-DET-NN をテストコードに anchor（UT-ID をテストに紐付け + 実行 pass）。trace_symmetry だけで閉じない（exec_pass 必須＝pair_closure）。

## 5. wiring / baseline 注記

- 全 FN-DET は C4 lint-wiring の到達対象（RUNTIME_ENTRYPOINTS=helix doctor 経路）に配線必須。未配線は FN-DET-10 が検出。
- advisory→hard 昇格は C5 baseline ratchet 経由。昇格基準は 1 ADR に集約（detector ごとにバラさない）。

## 6. 次工程

→ **L7 実装**（テスト実装 UT-DET-* → detector 本体 → 3 点レビュー → 実行 pass → coverage closure）。実装コード（Python）は Codex 委譲。残り fork lint の段階追加は Phase 8。
