# C3 detector + C4 lint-wiring 契約（pure-function 3 層・source_kind 宣言）

> keystone C3/C4。base SSoT = [capture §2 / §9-3 / §9.5](../audit/2026-06-26-new-base-comprehensive-capture.md) / 実体 = clean harness `src/lint/*`（~60 module）/ `src/doctor/index.ts` / `src/lint/lint-wiring.ts`。
> V3 = Python。対応: REQ-DET-01/02/03, REQ-WIR-01/02 / AT-V3-06/07/08。
> **訂正（capture §9-3, TL 2026-06-26）**: 旧 charter の「detector は DB 駆動・file scan 禁止」は実態と不一致。clean harness の detector は **file-scan と DB-projection の混在**。普遍は「DB-only」でなく **pure-function 3 層 + source_kind 宣言 + ok=AND + lint-wiring + absence-blindness 防止**。

## C3 detector

### 1. 目的

detector は「**あるべき集合 − 実在集合 = もれ**」を返す。doctor が全 detector を集約し **ok=AND で fail-close**。clean harness は ~60 detector を `runDoctor` が AND 連鎖（1 つでも false → 全体 fail-close）。

### 2. 共通様式（3 層分離、capture §2 — 全 detector が遵守）

```python
def analyze_<x>(input: XInput) -> XResult: ...    # 純関数（I/O なし。引数の型付き struct から result を計算）
def load_<x>_input(repo_root: str, db) -> XInput:  # I/O 端点（fs 読取 / DB query / snapshot 化をここに隔離）
def <x>_messages(result: XResult) -> list[Finding]: # ok/violation を機械可読 Finding へ
```

- detector core（`analyze_*`）は**必ず pure function**（テストは input を直接構築して呼ぶだけ、fs/DB 不要）。
- 型は `*_types.py`、policy 定数（catalog/allowlist/scenario）は `*_policy.py` に分離（harness refactoring の核）。共通 helper は `shared.py`。

### 3. source_kind 契約（TL C-3）

各 detector は **`source_kind: "db_projection" | "file_snapshot" | "hybrid"`** を宣言する。

- **db_projection**: `load_*` が DB を query（例: `db-projection-ingestion`=14 table row>0 / `db-projection-coverage`=physical-data×schema / `relation-graph`=projection 書込）。
- **file_snapshot**: `load_*` が doc/source を読み **snapshot 化**（例: `descent-obligation` / `screen-impl-pair-freeze` / `frontend-design-coverage` / `oracle-test-trace` / 大半の `plan-*`）。
- **hybrid**: 両方。
- **absence は ok=false**: source（DB row / file）不在・空でも `ok=false`（scope-0 silent OK 禁止）。「読めなかったから skip」「requirements=0 で空振り pass」「弱い fallback へ無音降格」は全て禁止（absence-blindness 防止）。
- **source-completeness（loader 不完全 = fail-close。upstream bug #3 予防）**: `file_snapshot` loader は**意図する file 集合を完全に**列挙する。単一供給源（`git ls-files`）が使えない環境（zip/tarball 展開・`.git` 不在）で**対象が縮小したら silent narrow-OK は禁止＝fail-close**。供給は二段 = ①git（`git ls-files --cached --others --exclude-standard`）→ ②**失敗時 filesystem-walk fallback**（同一 filter で `src/`・`.claude/hooks/`・`scripts/`・config を走査）。loader が完全集合を保証できなければ `ok=false`。これは upstream `runtime-portability` lint が `.git` 不在で対象を `package.json`/`tsconfig.json` のみに縮小し `src/`/`scripts/` を**無音で検査漏れ**した穴を、absence-blindness の具体 failure-mode として契約で塞ぐもの。
- **方針**: cutover 後の hard gate は可能なものから db_projection source へ昇格（file scan を漸減）。db_projection 側も C2 の artifact 列挙が git 非依存で完全であることに依存する（[projection-writer §4](projection-writer.md)）。

### 4. 契約（DbC）

```
Detector = {analyze, load, messages, source_kind, severity: "hard"|"soft"}
CheckResult = {ok: bool, messages: list[Finding]}   # Finding: {id, severity, subject, missing}
run_doctor(db, detectors) -> DoctorResult{ok: bool, findings: list[Finding]}
```

- **invariant-AND**: `run_doctor.ok = all(d.ok for d in hard_detectors)`（fail-close）。short-circuit せず全 detector 実行（messages 全件収集）。
- **invariant-fail-close-io**: I/O 失敗 = `ok=false`（`{messages:["... could not be read"], ok:false}`）。
- **warning surface 分離**: soft/advisory は message のみ surface し `doctor.ok` を落とさない（harness: handover/agent-slots/green-digest = warn-only）。hard/soft は detector が宣言。
- **ensures**: findings は機械可読（id/severity/subject/missing）で push gate / CI が exit code 判定可能。

### 5. detector inventory（capture §2 — ~60、V3 で再構築）

FE: `frontend-design-coverage`(schema VALID_SUB_DOCS+§1c+実ファイルの 3 者 AND) / `screen-impl-pair-freeze` ／ descent/trace: `descent-obligation`(adjacency rule 駆動 9 rule、satisfied/deferred/unmet/impl-ahead) / `oracle-test-trace`(baseline 連動) ／ graph: `relation-graph`(orphan/stale-edge/missing-projection) / `change-impact` ／ verification: `verification-profile`(allowlist 実行) ／ DB: `db-projection-coverage` / `db-projection-ingestion` ／ plan: `plan-artifact-existence`/`plan-body-substance`/`plan-completion-drift`/`plan-dod`/`plan-supersession` ／ gate/trace: `g1-trace`/`g3-trace`/`gate-confirm`/`impl-plan-trace`/`l6-fr-coverage`/`l6-completion`/`l7-completion` ／ governance: `backfill-pairing`/`scrum-reverse`/`propagation`/`review-evidence`/`cross-review`(via test-before-review)/`module-drift`/`asset-drift`/`dependency-drift`/`coding-rules`/`ddd-tdd-rules`/`rule-drift`/`right-arm-gate-planning`/`codex-hook-adapter` 他。完全一覧 = capture §2 inventory。

## C4 lint-wiring（死蔵禁止メタゲート）

### 6. 目的 / 契約

配線されない死蔵 detector を禁止する（HELIX の死蔵 detector 放置を構造的に潰す）。

```
RUNTIME_ENTRYPOINTS: list[str]    # 実行口（V3: helix doctor 経路の CLI entrypoint）
DEFERRED: dict[str, str]          # 理由付き除外（理由必須）
check_wiring(detector_keys, reachable, deferred) -> WiringResult{dead, stale_deferred}
```

- **三判定**（harness `lint-wiring.ts`）: ①到達不能 かつ DEFERRED 未登録 = **死蔵 violation**（unwired）/ ②DEFERRED 登録済だが到達可能 = **stale 申告 violation** / ③到達 or DEFERRED = ok。
- **invariant**: `dead == ∅ ∧ stale_deferred == ∅`。`ok = not dead and not stale_deferred`。
- **到達集合**: `RUNTIME_ENTRYPOINTS` から import グラフを BFS（Python = `ast`/`importlib` で import 抽出、コメントアウト import は除外）。あるいは「detector registry キー − doctor から明示 import される集合 − DEFERRED」の集合差分。tests/ は実行経路でないので BFS 対象外。
- harness 現 DEFERRED = `tool-adapter` 1 件（adapter-probe 純関数ライブラリ、理由付き）。

### 7. RUNTIME_ENTRYPOINTS 凍結（TL P2）

lint-wiring（C4）実装前に **`helix doctor` 経路を CLI entrypoint registry として実体パスで凍結**する（到達集合の基準点）。実体未凍結のまま lint-wiring を実装しない。

## 検証

- AT-V3-06: DB/file から「あるべき」1 件を抜く → detector がもれ検出（source_kind 別 loader）。
- AT-V3-07: 1 detector を fail → doctor 全体 fail（ok=AND）。
- AT-V3-08: 配線していない detector を追加 → lint-wiring fail。新 detector に source_kind 宣言なし → 登録 fail。
- AT-V3-09（source-completeness、bug #3 予防）: `.git` を外した展開状態で `file_snapshot` detector が scope 縮小せず（filesystem-walk fallback で）同一 finding を返す / fallback でも完全集合を保証できなければ fail-close（silent pass しない）。
- **L7 精緻化（TL re-review #3 2026-06-26 P2、freeze block でない）**: fallback の走査 root catalog（`src/` / `.claude/hooks/` / `scripts/` / config 等）を **detector 別に明示**し、`docs/plans` 系など file_snapshot の対象集合の解釈余地を消す（loader ごとに intended root を凍結）。
- 単体: 各 detector の `analyze_*` を pure に呼ぶ / loader failure・missing source・empty requirements が全て ok=false（absence-blindness）/ git 不在で loader が fs-walk fallback し対象集合が縮小しない。
