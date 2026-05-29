---
doc_id: l6-helix-workflows-function-spec-design
title: "HELIX-workflows V2 関数仕様設計 (function spec design)"
status: frozen
process_layer: L6
doc_type: function_spec_design
parent_plan: L6-helix-workflows-関数仕様plan
pairs_design: docs/v2/L5-internal-design/helix-workflows-module-decomposition-design.md
pairs_test_design: docs/v2/L7-test-design/helix-workflows-unit-test-design.md
---

# HELIX-workflows V2 関数仕様設計 (function spec design)

## §0 概要

本書は L5 詳細設計 3 文書を入力に、L7 実装へ直接落とせる public 関数 / CLI / hook の入口契約を凍結する L6 関数仕様設計である。関数 inventory の正本は `docs/v2/L5-internal-design/helix-workflows-module-decomposition-design.md` §2.1、CLI と hook の入出力正本は `docs/v2/L5-internal-design/helix-workflows-interface-detailed-design.md`、振る舞い正本は `docs/v2/L5-internal-design/helix-workflows-internal-processing-design.md` とする。

### §0.1 目的

- F1-F5 の中核機能について、実装入口契約を `signature / args / returns / exit code / stdout-stderr / side effect` まで確定する
- F6-F10 の拡張 governance 機能について、L7 carry 前提の planned contract を固定する
- `implemented / partial / planned` を混在させず、現状実装との差分を L7 carry として明示する
- L6↔L7-test の pair freeze 前提で、全 public 入口に `→ UT-Fx-NNN` を配線する

### §0.2 入力

1. `docs/v2/L5-internal-design/helix-workflows-module-decomposition-design.md` §2.1
2. `docs/v2/L5-internal-design/helix-workflows-interface-detailed-design.md`
3. `docs/v2/L5-internal-design/helix-workflows-internal-processing-design.md`

### §0.3 scope

- F1-F5: 完全本体化
- F6-F10: planned contract。既存 partial 実装がある場合は partial のまま明示し、統合不足は L7 carry に送る

### §0.4 implementation_status 定義

| 値 | 意味 |
|---|---|
| `implemented` | 実体が存在し、現時点で public 入口として利用可能 |
| `partial` | 実体は存在するが、L5/L6 契約の一部しか閉じていない |
| `planned` | 契約だけ先行確定し、実体は未作成または CLI/hook 連携未着手 |

## §1 F1 ドキュメント体系 / pair freeze 関数仕様

| function ID | owner module / file path | signature (引数 / 戻り値) | exit code / stdout / stderr | side effect | implementation_status | L7 単体テスト pointer | L5 source ref |
|---|---|---|---|---|---|---|---|
| F1-1 | `cli/helix-doctor` | `helix doctor <check-*> [--json] [--summary] [--timeout N] [--verbose]` | `0/1/2/1001/1010/1020/1030`; stdout=`text or JSON doctor payload`; stderr=`ERROR/WARN(...)` | read-only。`--apply*` 系指定時のみ PLAN revision / patch 反映 | `implemented` | `→ UT-F1-001` | `→ L5 IF §2 A-01..A-14`; `→ L5 §2.1 F1-1` |
| F1-2 | `cli/lib/vmodel_lint.py` | `def main(argv: list[str] | None = None) -> int` | `0/1/2/1030`; stdout=`lint summary`; stderr=`violation detail` | `docs/plans` / `docs/v2` の pair / trace 監査のみ | `implemented` | `→ UT-F1-002` | `→ L5 IF §2`; `→ L5 §2.1 F1-2`; `→ L5 internal §1` |
| F1-3 | `cli/lib/vmodel_pair_freeze.py` | `def check_pair_freeze(layer: str, *, project_root: Path | None = None, active_only: bool = False, since_days: int | None = None) -> dict[str, Any]` | `n/a`; stdout=`none`; stderr=`none` | none (pure read of `docs/plans`) | `implemented` | `→ UT-F1-003` | `→ L5 §2.1 F1-3`; `→ L5 internal §1.3` |
| F1-4 | `cli/lib/test_design_scaffold.py` | `def generate_skeleton(layer: str, paired_design_doc: str, *, title: str | None = None, extract_sections: bool = False, extract_functions: bool = False, extract_endpoints: bool = False, openapi_spec_path: Path | str | None = None) -> str`<br>`def write_scaffold(layer: str, paired_design_doc: str, *, project_root: Path, dry_run: bool = True, output_path: Path | None = None, output_dir: Path | str | None = None, as_json: bool = False, extract_sections: bool = False, extract_functions: bool = False, extract_endpoints: bool = False) -> dict[str, Any]` | `generate_skeleton`: `n/a` / no stdio<br>`write_scaffold`: `status=dry_run|applied|skipped` payload | pair test design 雛形生成。`dry_run=False` のみ file write | `implemented` | `→ UT-F1-004` | `→ L5 §2.1 F1-4`; `→ L5 internal §1.3` |
| F1-5 | `cli/lib/gate_check_generator.py` | `def build_doc_map(matrix: dict[str, Any], deliverables_rules: dict[str, Any], structure: dict[str, Any], *, catalog_index: Callable[[dict[str, Any]], dict[str, dict[str, Any]]], resolve_paths: Callable[[str, dict[str, Any], str, dict[str, Any]], Any], d_contract_doc_pattern: Callable[[str, dict[str, Any], dict[str, Any]], str]) -> dict[str, Any]` | `n/a`; stdout=`none`; stderr=`ValueError on invalid matrix` | none (deterministic doc-map generation) | `implemented` | `→ UT-F1-005` | `→ L5 §2.1 F1-5`; `→ L5 internal §1.1` |
| F1-6 | `cli/templates/docs/PLAN.md.template` | `template artifact: PLAN frontmatter + 4-artifact trace skeleton` | `n/a`; stdout/stderr=`none` | none。`helix plan` 生成時の source template | `implemented` | `→ UT-F1-006` | `→ L5 §2.1 F1-6`; `→ L5 internal §1.1` |

### 境界 critical 補足

`helix_doctor` は CLI 集約入口であり、`--json` と `--summary` は同時指定不可、usage 不正は exit `2` で fail-close する。F1 としては read-only が基本だが、`--apply-stale-revisions` / `--apply-patches` / `--rollback-stale-revisions` に `--apply` を併用した場合だけ副作用を持つ。

`gate_check_generator.build_doc_map()` は `matrix.features` が辞書であることを事前条件とし、崩れた場合は `ValueError` を返す。入力が同一なら出力も同一であり冪等、file write は呼び出し側に委譲される。

`test_design_scaffold.write_scaffold()` は `dry_run=True` なら純関数的に content を返し、`dry_run=False` でも既存 file があれば `status="skipped"` を返して上書きしないため、同一 output path に対して収束的である。

## §2 F2 PLAN template / registry 関数仕様

| function ID | owner module / file path | signature (引数 / 戻り値) | exit code / stdout / stderr | side effect | implementation_status | L7 単体テスト pointer | L5 source ref |
|---|---|---|---|---|---|---|---|
| F2-1 | `cli/helix-plan` | `helix plan <create|view|fork|status|apoptosis|validate> [--json] [--plan-id <id>]` | `0/1/2/1010`; stdout=`text or plan payload`; stderr=`ERROR(DOC-1010)` | plan file / registry 更新（fork, apoptosis） | `implemented` | `→ UT-F2-001` | `→ L5 IF §4 A-18..A-22`; `→ L5 §2.1 F2-1` |
| F2-2 | `cli/lib/plan_parser.py` | `def parse_frontmatter(filepath: str) -> dict | None`<br>`def upsert_plan(conn, frontmatter: dict | None, doc_path: str) -> dict`<br>`def detect_cycle(conn, plan_id: str) -> list[str]` | `n/a`; stdout=`none`; stderr=`_warn(...)` on parse/read failure | `plan_registry` / `plan_dependencies` / `plan_agent_slots` / `plan_references` / `plan_generates` 更新、失敗時 `failure_log` 追記 | `implemented` | `→ UT-F2-002` | `→ L5 §2.1 F2-2`; `→ L5 internal §2.1` |
| F2-3 | `cli/lib/plan_validator.py` | `def validate_plan(path: Path) -> list[str]`<br>`def detect_dependency_cycle(path: Path, plan_id: str) -> list[str] | None` | `n/a`; stdout=`none`; stderr=`none` | none (semantic validation only) | `implemented` | `→ UT-F2-003` | `→ L5 §2.1 F2-3`; `→ L5 internal §2.1-§2.3` |
| F2-4 | `cli/lib/plan_lint.py` | `def validate_plan_frontmatter(frontmatter: dict) -> list[dict[str, str]]` | `n/a`; stdout=`none`; stderr=`none` | none (static lint only) | `implemented` | `→ UT-F2-004` | `→ L5 §2.1 F2-4`; `→ L5 internal §2.1` |
| F2-5 | `cli/lib/plan_dependencies.py` | `def load_dependencies(plan_id: str, project_root: str | Path | None = None) -> dict[str, Any]`<br>`def save_dependencies(plan_id: str, deps: dict[str, Any], db_path: str | None = None) -> None` | `n/a`; stdout=`none`; stderr=`none` | `helix.db.plan_dependencies` update | `implemented` | `→ UT-F2-005` | `→ L5 §2.1 F2-5`; `→ L5 internal §2.1` |
| F2-6 | `.claude/hooks/posttooluse-plan-auto-register.sh` | `PostToolUse(Edit/Write on PLAN*.md or ADR-*.md) -> {"decision":"continue|block","systemMessage":str}` | hook exit=`0` pass/fail-open, `2` on cycle block; stdout=`decision JSON`; stderr=`warning only` | `plan_parser.py --mode upsert` 実行、`helix.db` / `failure_log` 更新 | `implemented` | `→ UT-F2-006` | `→ L5 §2.1 F2-6`; `→ L5 IF §10.7`; `→ L5 internal §2.1` |
| F2-7 | `cli/lib/plan_health.py` | `def scan_all_plans(plans_root: Path) -> dict[str, object]` | `n/a`; stdout=`none`; stderr=`none` | none (tree scan only) | `partial` | `→ UT-F2-007` | `→ L5 §2.1 F2-7`; `→ L5 IF §4 A-18..A-22` |

### 境界 critical 補足

`plan_parser.parse_frontmatter()` の事前条件は「対象が PLAN/ADR 系の markdown で、frontmatter が YAML mapping であること」である。非対象 file は `{}`、読込失敗や YAML 破損は `None` を返し、呼び出し側は parse error として扱う。

`plan_parser.upsert_plan()` は `plan_id` を主キーに `ON CONFLICT ... DO UPDATE` を行い、関連 row を削除して再挿入するため、同一 frontmatter の再投入は収束的である。一方 `frontmatter` が空のときは `failure_log` を 1 件追加するので、失敗パスは非冪等である。

`plan_validator.validate_plan()` は例外を外へ投げず warning list に正規化する方針で、fail-close 判定は CLI 層が担当する。`detect_dependency_cycle()` は path 解決できない依存を許容しつつ既知 graph 内の cycle のみ返す pure function である。

## §3 F3 skill catalog / recommender 関数仕様

| function ID | owner module / file path | signature (引数 / 戻り値) | exit code / stdout / stderr | side effect | implementation_status | L7 単体テスト pointer | L5 source ref |
|---|---|---|---|---|---|---|---|
| F3-1 | `cli/helix-skill` | `helix skill <list|show|lint|catalog rebuild|classify|search|use|chain|stats|review-pending|approve> ...` | `0/1/2`; stdout=`text or JSON`; stderr=`usage / not found / validation error` | cache rebuild、skill_usage 記録、dispatch 実行時の task artifact 生成 | `implemented` | `→ UT-F3-001` | `→ L5 IF §12.5 A-93`; `→ L5 §2.1 F3-1` |
| F3-2 | `cli/lib/skill_catalog.py` | `def build_catalog(skills_root: Path) -> dict[str, Any]`<br>`def load_catalog(cache_path: Path) -> dict[str, Any]` | `n/a`; stdout=`none`; stderr=`none` | `save_catalog()` 呼び出し側で cache file を更新 | `implemented` | `→ UT-F3-002` | `→ L5 §2.1 F3-2`; `→ L5 internal §3.1` |
| F3-3 | `cli/lib/skill_recommender.py` | `def recommend(task_text: str, top_n: int = 5, layer_filter: str | None = None, category_filter: str | None = None, catalog_path: Path | None = None, cache_dir: Path | None = None, jsonl_catalog_path: Path | None = None, phase_filter: list[str] | None = None, use_no_jsonl: bool = False, force_refresh: bool = False) -> dict[str, Any]` | `main()`: `0/2/4`; stdout=`candidate JSON or text`; stderr=`エラー:` | recommendation cache 更新 | `implemented` | `→ UT-F3-003` | `→ L5 §2.1 F3-3`; `→ L5 internal §3.2` |
| F3-4 | `cli/lib/skill_dispatcher.py` | `def determine_agent(skill: dict, recommended_agent: str | None = None) -> dict`<br>`def dispatch(skill_id: str, task_text: str, recommended_agent: str | None, references: list[str], catalog_path: Path | None = None, skills_root: Path | None = None, db_path: Path | None = None, dry_run: bool = False) -> dict` | `main()`: `0/7/...`; stdout=`plan_only/delegated result`; stderr=`DispatcherError text` | `skill_usage` insert/update、task temp file 作成、Codex/Claude dispatch | `implemented` | `→ UT-F3-004` | `→ L5 §2.1 F3-4`; `→ L5 internal §3.2` |
| F3-5 | `.claude/hooks/posttooluse-skill-catalog-rebuild.sh` | `PostToolUse(Edit/Write/MultiEdit on skills/**/SKILL.md) -> background rebuild trigger` | hook exit=`0`; stdout=`none`; stderr=`none` | debounce file / cache delete / `helix skill catalog rebuild` 非同期起動 | `implemented` | `→ UT-F3-005` | `→ L5 §2.1 F3-5`; `→ L5 IF §10.7` |

## §4 F4 mode routing / local workflow 関数仕様

| function ID | owner module / file path | signature (引数 / 戻り値) | exit code / stdout / stderr | side effect | implementation_status | L7 単体テスト pointer | L5 source ref |
|---|---|---|---|---|---|---|---|
| F4-1 | `cli/helix-route` | `helix route [--signal <file>] [--json] [--dry-run]` | `0/1/2`; stdout=`route suggestion text/payload`; stderr=`signal parse error` | routing suggestion のみ。state write なし | `implemented` | `→ UT-F4-001` | `→ L5 IF §12.5 A-62`; `→ L5 §2.1 F4-1` |
| F4-2 | `cli/lib/route_engine.py` | `class RouteEngine`<br>`def evaluate(self, signal: str, uncertainty: Severity = "low", impact: Severity = "low", env: Env | None = None, reopen_point: str = "HEAD", drift_type: str | None = None) -> RouteResult`<br>`def from_detect_output(self, detect_run_json: dict[str, Any] | list[dict[str, Any]]) -> list[RouteResult]` | `main()`: `0/1/2`; stdout=`RouteResult JSON/text`; stderr=`deprecation warning / unknown signal` | none (pure routing) | `implemented` | `→ UT-F4-002` | `→ L5 §2.1 F4-2`; `→ L5 internal §4.1-§4.2` |
| F4-3 | `cli/lib/task_dispatcher.py` | `def dispatch_task(task_type: str, task_payload: str) -> tuple[bool, str]` | `n/a`; stdout=`none`; stderr=`returned in tuple message` | shell / webhook / helix command 実行 | `implemented` | `→ UT-F4-003` | `→ L5 §2.1 F4-3`; `→ L5 internal §4.2` |
| F4-4 | `cli/lib/workflow_dsl_parser.py` | `def load_workflow(filepath: str | Path) -> dict[str, Any]`<br>`def validate_workflow_schema(payload: dict[str, Any]) -> list[str]` | `n/a`; stdout=`none`; stderr=`none` | none (YAML load / schema validation only) | `partial` | `→ UT-F4-004` | `→ L5 §2.1 F4-4`; `→ L5 internal §4.2` |
| F4-5 | `cli/lib/scrum_local.py` | `def init_local_loop(forward_layer: str, hypothesis: str, acceptance: str, forward_plan_id: str | None = None, parent_loop_id: str | None = None) -> str`<br>`def verify_loop(loop_id: str, observation: str | None = None) -> None`<br>`def decide_loop(loop_id: str, result: str, note: str | None = None) -> None` | `n/a`; stdout=`none`; stderr=`ValueError on bad state/input` | `scrum_local_loops` / audit event write | `implemented` | `→ UT-F4-005` | `→ L5 §2.1 F4-5`; `→ L5 internal §4.2` |
| F4-6 | `cli/lib/reverse_local.py` | `def route_to_forward(loop_id: str, target_plan: str, target_layer: str, artifact_links: list[dict] | None = None) -> None` | `n/a`; stdout=`none`; stderr=`ValueError on bad state/input` | `reverse_local_loops` update、audit event write | `implemented` | `→ UT-F4-006` | `→ L5 §2.1 F4-6`; `→ L5 internal §11.1` |

### 境界 critical 補足

`RouteEngine.evaluate()` は `signal / uncertainty / impact / env / drift_type` の正規化に失敗した場合のみ例外を返し、それ以外は副作用なしで `RouteResult` を返す。lookup table が同じなら完全に冪等であり、L7 では「同一入力で command hint が不変であること」を固定する。

`RouteEngine.from_detect_output()` は detect schema を厳密に要求し、`detector/status/result` のどれかが欠けると `ValueError` で fail-close する。cross-detection や dashboard schema は adapter 必須として明示拒否するため、呼び出し境界での schema 混線を防ぐ。

## §5 F5 orchestration / audit / DB write 関数仕様

| function ID | owner module / file path | signature (引数 / 戻り値) | exit code / stdout / stderr | side effect | implementation_status | L7 単体テスト pointer | L5 source ref |
|---|---|---|---|---|---|---|---|
| F5-1 | `cli/helix-codex` | `helix codex --role <role> (--task <text> | --task-file <path>) [--approved|--plan-only] [--plan-id <id>] [--wbs-id <id>] [--reference-doc <path>] ...` | `0/1/2`; stdout=`summary block / task output`; stderr=`guard / retry / model fallback logs` | task file 読込、approval/evidence 検証、Codex 実行、telemetry 記録 | `implemented` | `→ UT-F5-001` | `→ L5 IF §12.5 A-89`; `→ L5 §2.1 F5-1` |
| F5-2 | `cli/helix-claude` | `helix claude --role <role> (--task <text> | --task-file <path>) [--dry-run|--execute] [--plan-id <id>] [--handover] ...` | `0/1/2`; stdout=`prompt or execute result`; stderr=`input/role/template error` | prompt file write、PMO execute 時の invocation telemetry | `implemented` | `→ UT-F5-002` | `→ L5 IF §12.5 A-90`; `→ L5 §2.1 F5-2` |
| F5-3 | `cli/helix-agent` | `helix agent <init|stage1|stage2|merge|phase|layer|route|fire|release|slots|stats|fire-mandatory|suggest|audit>` | `0/1/2`; stdout=`table or JSON`; stderr=`input/schema error` | `agent_slots` / phase state / audit write | `implemented` | `→ UT-F5-003` | `→ L5 §2.1 F5-3`; `→ L5 internal §5.2` |
| F5-4 | `cli/helix-doctor` | `helix doctor --summary [--json]` | `0/1/2`; stdout=`summary JSON`; stderr=`doctor text->summary conversion failure` | read-only summary aggregation | `implemented` | `→ UT-F5-004` | `→ L5 IF §2`; `→ L5 §2.1 F5-4` |
| F5-5 | `cli/lib/doctor_plan_checks.py` | `def run_check_plan_drift(conn: sqlite3.Connection) -> list[dict[str, Any]]`<br>`def run_check_plan_cycle(conn: sqlite3.Connection) -> list[dict[str, Any]]` | `n/a`; stdout=`none`; stderr=`none` | none (DB read only) | `implemented` | `→ UT-F5-005` | `→ L5 §2.1 F5-5`; `→ L5 internal §5.2` |
| F5-6 | `cli/lib/gate_check_generator.py` | `def build_doc_map(...) -> dict[str, Any]` | `n/a`; stdout=`none`; stderr=`ValueError on invalid matrix` | none | `implemented` | `→ UT-F5-006` | `→ L5 §2.1 F5-6`; `→ L5 internal §5.1` |
| F5-7 | `.claude/hooks/pretooluse-agent-guard.sh` | `PreToolUse(Agent) -> exit 0|2` | `0` pass / `2` block; stdout=`none`; stderr=`block reason` | none。policy guard のみ | `implemented` | `→ UT-F5-007` | `→ L5 §2.1 F5-7`; `→ L5 IF §10.3` |
| F5-8 | `.claude/hooks/pretooluse-agent-fire.sh` | `PreToolUse(Agent auto fire) -> exit 0` | `0`; stdout=`none`; stderr=`debug only` | `agent_slots.fire_slot()` 記録 | `implemented` | `→ UT-F5-008` | `→ L5 §2.1 F5-8`; `→ L5 IF §10.3` |
| F5-9 | `.claude/hooks/post-tool-use.sh` | `PostToolUse dispatcher -> exit 0` | `0`; stdout=`none`; stderr=`suppressed warn only` | audit log write、fan-out dispatch | `implemented` | `→ UT-F5-009` | `→ L5 §2.1 F5-9`; `→ L5 IF §10.7-§10.11` |
| F5-10 | `cli/lib/compatibility_adapter.py` | `@contextmanager def write_connection(db_path: str | Path | None = None, ensure_schema: bool = True) -> Iterator[Connection | _DualWriteConnection]` | `n/a`; stdout=`none`; stderr=`logger warning/debug` | `helix.db` / split db への write routing | `implemented` | `→ UT-F5-010` | `→ L5 §2.1 F5-10`; `→ L5 internal §5.1` |
| F5-11 | `cli/lib/helix_db.py` | `def record_invocation(db_path, data) -> None`<br>`def record_selection(db_path, data) -> None` | `n/a`; stdout=`last_insert_rowid()`; stderr=`KeyError / sqlite error by exception` | `invocation_log` / `task_selections` insert | `implemented` | `→ UT-F5-011` | `→ L5 §2.1 F5-11`; `→ L5 internal §5.1` |

### 境界 critical 補足

`compatibility_adapter.write_connection()` は `db_path` 明示時は legacy 互換、`db_path=None` かつ `HELIX_DB_CUTOVER=1` なら routed DB 単独書込、cutover 無効なら dual-write に落ちる。呼び出し側は context manager を正常終了させることが前提で、同一 write を再試行した場合の二重 insert 回避は上位側の主キー / unique 制約に依存する。

`helix_db.record_invocation()` と `record_selection()` は insert 専用であり、本質的に非冪等である。呼び出し側が retry を行う場合は「同一 logical event を再送しない」設計が必要で、L7 では duplicate write を防ぐ wrapper test を持つ。

`pretooluse-agent-guard.sh` は subagent type / model family / definition file を満たさない場合に exit `2` で block する fail-close 境界である。`pretooluse-agent-fire.sh` と `post-tool-use.sh` は監査記録系なので fail-open で進み、実行停止は原則起こさない。

## §6 F6-F10 planned contract

### §6.1 F6 homeostasis

| function ID | owner module / file path | signature (引数 / 戻り値) | exit code / stdout / stderr | side effect | implementation_status | L7 単体テスト pointer | L5 source ref |
|---|---|---|---|---|---|---|---|
| F6-1 | `cli/lib/homeostasis.py` | `planned CLI: helix budget status --homeostasis [--json] [--days <N>] [--project <name>]` | `0/1/2/1020`; stdout=`pressure payload`; stderr=`WARN(DOC-1020)` | none | `planned` | `→ UT-F6-001` | `→ L5 IF §3 A-16`; `→ L5 §2.1 F6-1` |
| F6-2 | `cli/lib/budget.py` | `def collect_status(use_cache: bool = True) -> dict[str, Any]` | `n/a`; stdout=`none`; stderr=`none` | budget cache 更新 | `partial` | `→ UT-F6-002` | `→ L5 §2.1 F6-2`; `→ L5 internal §6.1` |
| F6-3 | `cli/lib/budget_cli.py` | `def cmd_status(args) -> int`<br>`def cmd_forecast(args) -> int`<br>`def main(argv: list[str] | None = None) -> int` | `0/1/2/1020`; stdout=`status/forecast text or JSON`; stderr=`usage/input error` | none | `partial` | `→ UT-F6-003` | `→ L5 IF §3 A-15..A-17`; `→ L5 §2.1 F6-3` |
| F6-4 | `cli/lib/plan_health.py` | `def scan_all_plans(plans_root: Path) -> dict[str, object]` | `n/a`; stdout=`none`; stderr=`none` | none | `implemented` | `→ UT-F6-004` | `→ L5 §2.1 F6-4`; `→ L5 internal §6.1` |
| F6-5 | `cli/lib/scheduler_helper.py` | `def run_due_schedules(db_path: str, dry_run: bool = False, max_count: int | None = None, *, requeue_stale_older_than: int | None = None) -> list[dict]`<br>`def requeue_stale_schedules(db_path: str, *, older_than: int = 3600, now: int | None = None) -> list[dict]` | `n/a`; stdout=`none`; stderr=`ValueError on invalid max_count` | `schedules` table state transition / task dispatch | `implemented` | `→ UT-F6-005` | `→ L5 §2.1 F6-5`; `→ L5 internal §6.2` |
| F6-6 | `.claude/hooks/precompact-state-snapshot.sh` | `PreCompact -> exit 0|2` | `0` pass / `2` fail-close; stdout=`state snapshot message`; stderr=`reason` | blocked session snapshot / backup write | `implemented` | `→ UT-F6-006` | `→ L5 §2.1 F6-6`; `→ L5 IF §10.2` |
| F6-7 | `cli/lib/session_start_helpers.py` | `def build_progress_block(project_root: Path) -> str` | `n/a`; stdout=`none`; stderr=`none` | none | `partial` | `→ UT-F6-007` | `→ L5 §2.1 F6-7`; `→ L5 internal §6.3` |

### §6.2 F7 evolution

| function ID | owner module / file path | signature (引数 / 戻り値) | exit code / stdout / stderr | side effect | implementation_status | L7 単体テスト pointer | L5 source ref |
|---|---|---|---|---|---|---|---|
| F7-1 | `cli/lib/evolution.py` | `planned CLI: helix evolution <score|promote|deprecate> [--json] [--window <days>]` | `0/1/2`; stdout=`evolution payload`; stderr=`policy error` | recipe lifecycle write | `planned` | `→ UT-F7-001` | `→ L5 IF §5 A-23..A-25`; `→ L5 §2.1 F7-1` |
| F7-2 | `cli/helix-learn` | `helix learn [--json] [--source <path>] [--dry-run]` | `0/1/2`; stdout=`recipe candidate`; stderr=`source invalid` | learning store update | `implemented` | `→ UT-F7-002` | `→ L5 IF §12.5 A-78`; `→ L5 §2.1 F7-2` |
| F7-3 | `cli/helix-promote` | `helix promote [--json] [--id <artifact-id>] [--target <stable|legacy>]` | `0/1/2`; stdout=`promotion payload`; stderr=`target locked` | promotion table write | `implemented` | `→ UT-F7-003` | `→ L5 IF §12.5 A-79`; `→ L5 §2.1 F7-3` |
| F7-4 | `cli/lib/learning_engine.py` | `def analyze_success(task_run_id: int, db_path: str) -> dict[str, Any] | None`<br>`def save_recipe(recipe: dict[str, Any], project_root: str) -> str`<br>`def find_recipe(recipe_id: str, project_root: str) -> dict[str, Any] | None` | `n/a`; stdout=`none`; stderr=`ValueError on invalid run/recipe` | `.helix/recipes/*.json` write/read | `implemented` | `→ UT-F7-004` | `→ L5 §2.1 F7-4`; `→ L5 internal §7.1-§7.2` |
| F7-5 | `cli/lib/matrix_advisor.py` | `def run_advisory(index_path: Path, state_path: Path, rel_path: str, project_root: Path) -> None` | `n/a`; stdout=`warning only`; stderr=`warning only` | none (advisory output only) | `partial` | `→ UT-F7-005` | `→ L5 §2.1 F7-5`; `→ L5 internal §7.2` |
| F7-6 | `cli/lib/demotion_checker.py` | `def check_demotion_eligibility(rule_id: str, days: int, violation_history: Iterable[object]) -> bool`<br>`def demote(current_level: EscalationLevel) -> EscalationLevel` | `n/a`; stdout=`none`; stderr=`none` | none | `implemented` | `→ UT-F7-006` | `→ L5 §2.1 F7-6`; `→ L5 internal §7.1` |

### §6.3 F8 migration / version coevolution

| function ID | owner module / file path | signature (引数 / 戻り値) | exit code / stdout / stderr | side effect | implementation_status | L7 単体テスト pointer | L5 source ref |
|---|---|---|---|---|---|---|---|
| F8-1 | `cli/lib/migration.py` | `planned CLI: helix version bump (--major|--minor) [--compatibility-adr <path>] [--json]` | `0/1/2`; stdout=`version bump payload`; stderr=`migration policy error` | version metadata write | `planned` | `→ UT-F8-001` | `→ L5 §2.1 F8-1`; `→ L5 internal §8.1` |
| F8-2 | `cli/lib/migrate.py` | `def merge_yaml(existing_text: str, template_text: str, file_kind: str) -> str`<br>`def main(argv: list[str] | None = None) -> int` | `0/1/2`; stdout=`operations/changed_files`; stderr=`safety abort` | file merge / backup 作成 | `implemented` | `→ UT-F8-002` | `→ L5 IF §6 A-27`; `→ L5 §2.1 F8-2` |
| F8-3 | `cli/lib/compatibility_adapter.py` | `def write_connection(...) -> Iterator[Connection | _DualWriteConnection]` | `n/a`; stdout=`none`; stderr=`logger output` | dual-write / cutover routing | `implemented` | `→ UT-F8-003` | `→ L5 §2.1 F8-3`; `→ L5 internal §8.1` |
| F8-4 | `cli/lib/recovery_engine.py` | `def main(argv: list[str] | None = None) -> int` | `0/1/2`; stdout=`diagnostics`; stderr=`recover failure` | optional recovery plan draft | `implemented` | `→ UT-F8-004` | `→ L5 IF §9 A-36`; `→ L5 §2.1 F8-4` |
| F8-5 | `cli/lib/recovery_workflow_engine.py` | `def main(argv: list[str] | None = None) -> int`<br>`def snapshot_on_stop() -> None` | `0/1/2/1010`; stdout=`recovery state`; stderr=`state/transition error` | recovery workflow state / snapshot write | `implemented` | `→ UT-F8-005` | `→ L5 IF §9 A-35`; `→ L5 §2.1 F8-5` |
| F8-6 | `cli/lib/rollback_orchestrator.py` | `def rollback_preflight() -> dict[str, Any]`<br>`def rollback_execute(*, confirm_token: str, backup_path: str) -> RollbackResult` | `n/a`; stdout=`none`; stderr=`exception text` | env `HELIX_DB_CUTOVER` 切替、rollback result 生成 | `implemented` | `→ UT-F8-006` | `→ L5 §2.1 F8-6`; `→ L5 internal §8.1` |

### §6.4 F9 apoptosis / autophagy

| function ID | owner module / file path | signature (引数 / 戻り値) | exit code / stdout / stderr | side effect | implementation_status | L7 単体テスト pointer | L5 source ref |
|---|---|---|---|---|---|---|---|
| F9-1 | `cli/lib/apoptosis.py` | `planned CLI: helix plan apoptosis --plan-id <id> --mode <archive|close|retire> [--json] [--force]` | `0/1/2`; stdout=`archive payload`; stderr=`apoptosis failed` | plan metadata / audit write | `planned` | `→ UT-F9-001` | `→ L5 IF §4 A-20`; `→ L5 §2.1 F9-1` |
| F9-2 | `cli/lib/recovery_plan_check.py` | `def check_recovery_plan_freshness(filepath: str | Path, max_age_days: int = 30) -> bool`<br>`def check_session_exit_4items(carry_count: int, recovery_plan_exists: bool, handover_updated: bool, memory_updated: bool) -> list[str]` | `n/a`; stdout=`none`; stderr=`none` | none | `implemented` | `→ UT-F9-002` | `→ L5 §2.1 F9-2`; `→ L5 internal §9.1-§9.2` |
| F9-3 | `cli/lib/doctor_recovery_check.py` | `def run_check_recovery_freshness(max_age_days: int = 30) -> list[dict[str, Any]]` | `n/a`; stdout=`none`; stderr=`none` | none | `implemented` | `→ UT-F9-003` | `→ L5 §2.1 F9-3`; `→ L5 internal §9.2` |
| F9-4 | `cli/lib/demotion_checker.py` | `def check_demotion_eligibility(...) -> bool`<br>`def demote(...) -> EscalationLevel` | `n/a`; stdout=`none`; stderr=`none` | none | `implemented` | `→ UT-F9-004` | `→ L5 §2.1 F9-4`; `→ L5 internal §9.1` |
| F9-5 | `cli/lib/rollback_orchestrator.py` | `def rollback_preflight() -> dict[str, Any]`<br>`def rollback_execute(*, confirm_token: str, backup_path: str) -> RollbackResult` | `n/a`; stdout=`none`; stderr=`exception text` | rollback readiness / cutover retreat | `partial` | `→ UT-F9-005` | `→ L5 §2.1 F9-5`; `→ L5 internal §9.3` |
| F9-6 | `cli/lib/compatibility_adapter.py` | `def write_connection(...) -> Iterator[Connection | _DualWriteConnection]` | `n/a`; stdout=`none`; stderr=`logger output` | obsolete cleanup 時の DB write gateway 候補 | `partial` | `→ UT-F9-006` | `→ L5 §2.1 F9-6`; `→ L5 internal §9.3` |

### §6.5 F10 coexist

| function ID | owner module / file path | signature (引数 / 戻り値) | exit code / stdout / stderr | side effect | implementation_status | L7 単体テスト pointer | L5 source ref |
|---|---|---|---|---|---|---|---|
| F10-1 | `cli/lib/coexist.py` | `planned CLI: helix coexist <status|adopt|validate> [--compatibility-adr <path>] [--json]` | `0/1/2/1010`; stdout=`coexist payload`; stderr=`compatibility error` | config / coexist manifest write | `planned` | `→ UT-F10-001` | `→ L5 IF §8 A-32..A-34`; `→ L5 §2.1 F10-1` |
| F10-2 | `cli/lib/compatibility_adapter.py` | `def write_connection(...) -> Iterator[Connection | _DualWriteConnection]` | `n/a`; stdout=`none`; stderr=`logger output` | dual-write / cutover routing | `partial` | `→ UT-F10-002` | `→ L5 §2.1 F10-2`; `→ L5 internal §10.2` |
| F10-3 | `cli/lib/merge_settings.py` | `def merge(settings) -> bool`<br>`def merge_settings_for_migrate(current, hooks_to_install) -> bool` | `main()`: `0/1/2`; stdout=`changed summary`; stderr=`usage / JSON error` | settings merge / hook insertion | `partial` | `→ UT-F10-003` | `→ L5 §2.1 F10-3`; `→ L5 internal §10.2` |
| F10-4 | `cli/lib/shadow_replay.py` | `def replay_to_shadow_db(legacy_conn: sqlite3.Connection, shadow_db_path: str, *, since_event_id: str | None = None, dry_run: bool = False) -> ReplayResult` | `n/a`; stdout=`none`; stderr=`exception text` | shadow DB replay / compare | `partial` | `→ UT-F10-004` | `→ L5 §2.1 F10-4`; `→ L5 internal §10.1` |
| F10-5 | `cli/lib/cutover_orchestrator.py` | `def cutover_preflight() -> CutoverPreflightResult`<br>`def cutover_execute(*, confirm_token: str) -> dict[str, Any]` | `n/a`; stdout=`none`; stderr=`RuntimeError on blocker` | preflight evaluation、optional execute hook invocation | `partial` | `→ UT-F10-005` | `→ L5 §2.1 F10-5`; `→ L5 internal §10.2` |
| F10-6 | `cli/lib/rollback_orchestrator.py` | `def rollback_preflight() -> dict[str, Any]`<br>`def rollback_execute(*, confirm_token: str, backup_path: str) -> RollbackResult` | `n/a`; stdout=`none`; stderr=`exception text` | coexist failure 時の rollback path | `partial` | `→ UT-F10-006` | `→ L5 §2.1 F10-6`; `→ L5 internal §10.2` |

### 境界 critical 補足

`rollback_preflight()` は `HELIX_DB_CUTOVER=1`、backup / manifest 存在、sha256 一致、rollback window 内であることを前提に read-only 判定を返す。ここまでは冪等であり、同一 backup と manifest に対して結果は安定する。

`rollback_execute()` は confirm token と preflight 成功が必須で、失敗時は `RuntimeError` / `ValueError` / `PermissionError` を返す。成功時は `HELIX_DB_CUTOVER=0` へ戻すため副作用を持ち、再実行は同一 state を前提にしない。

`recovery_workflow_engine.main()` / `snapshot_on_stop()` は recovery state machine の入口であり、active session がない場合の `snapshot_on_stop()` は no-op になる。したがって停止処理自体は収束的だが、active session への repeated snapshot は同一 file 更新を起こしうる。

`shadow_replay.replay_to_shadow_db()` と `cutover_preflight()` は migration / coexist 境界の監査面を担う。前者は legacy event を shadow DB に replay して mismatch を返し、後者は `dual_write` / `shadow_replay` / mismatch count が全て満たされた場合だけ ready を返す。

## §7 implementation_status 集計 + L7 carry 一覧

### §7.1 集計

| 範囲 | rows | implemented | partial | planned |
|---|---:|---:|---:|---:|
| F1-F5 | 35 | 33 | 2 | 0 |
| F6-F10 | 31 | 15 | 11 | 5 |
| total | 66 | 48 | 13 | 5 |

### §7.2 F1-F5 section row count

| section | function rows |
|---|---:|
| §1 F1 | 6 |
| §2 F2 | 7 |
| §3 F3 | 5 |
| §4 F4 | 6 |
| §5 F5 | 11 |

### §7.3 L7 carry

| carry ID | 対象 | carry 内容 | 理由 |
|---|---|---|---|
| CARRY-L7-001 | F2-7 | `plan_health.scan_all_plans()` を fail-close gate へ接続 | health 集計はあるが gate 強制化が未完 |
| CARRY-L7-002 | F4-4 | `workflow_dsl_parser` の 9 mode 全域 schema 化 | 現状 recovery/escalation 中心の partial |
| CARRY-L7-003 | F6-1/F6-2/F6-3/F6-7 | homeostasis CLI と metric 統合 | budget/status はあるが threshold / statusLine 統合未完 |
| CARRY-L7-004 | F7-1/F7-5 | evolution CLI 本体化と auto promote/deprecate | recipe 周辺は existing、governance 自動化は未接続 |
| CARRY-L7-005 | F8-1 | `helix version bump` public CLI 追加 | migrate は existing、version mutation public contract は planned |
| CARRY-L7-006 | F9-1/F9-5/F9-6 | apoptosis / autophagy を plan lifecycle と DB cleanup に統合 | rollback / adapter はあるが cleanup orchestration が未完 |
| CARRY-L7-007 | F10-1..F10-6 | coexist CLI、namespace/ACL、cutover metadata の閉じ込み | adapter / replay / cutover は partial で contract 完結に未達 |

### §7.4 L6↔L7-test pair 宣言

- 本書の全 `UT-Fx-NNN` pointer は `docs/v2/L7-test-design/helix-workflows-unit-test-design.md` に対応する
- L7 側では同一 pointer を test case ID の最小単位とし、実装 code docstring では `DoD 検証: helix-workflows-unit-test-design.md UT-Fx-NNN` を必須とする
- planned / partial の入口も pointer を先行確保し、L7 で仕様 drift を起こさない
