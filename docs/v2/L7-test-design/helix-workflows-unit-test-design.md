---
doc_id: l7-helix-workflows-unit-test-design
title: "HELIX-workflows V2 単体テスト設計 (unit test design)"
status: frozen
process_layer: L7
doc_type: unit_test_design
parent_plan: L7-helix-workflows-単体テストplan
pairs_design:
  - docs/v2/L6-functional-design/helix-workflows-function-spec-design.md
  - docs/v2/L6-functional-design/helix-workflows-class-module-command-design.md
  - docs/v2/L6-functional-design/helix-workflows-edge-case-design.md
test_execution_status: planned  # 設計凍結、実行は L7 Sprint Step 2 carry
---

# HELIX-workflows V2 単体テスト設計 (unit test design)

## §0 概要

本書は L6 機能設計 3 文書と L7 Sprint Step 2 の単体テスト実装を 1:1 に結ぶ ③ テスト設計 artifact である。対象は HELIX-workflows V2 dogfooding の F1-F10 で、F1-F5 は public 関数 / class / command / schema / hook の正常系・異常系・境界値を本体化し、F6-F10 は planned test contract として凍結する。

### §0.1 L6↔L7 pair 宣言

| artifact | path | 本書での扱い |
|---|---|---|
| ① L6 関数仕様 | `docs/v2/L6-functional-design/helix-workflows-function-spec-design.md` | public 関数 / CLI / hook signature の正本 |
| ① L6 class/module/command 設計 | `docs/v2/L6-functional-design/helix-workflows-class-module-command-design.md` | class / command / schema / hook 境界の正本 |
| ① L6 edge case 設計 | `docs/v2/L6-functional-design/helix-workflows-edge-case-design.md` | 異常系・境界値・fail-close 期待結果の正本 |
| ③ 本書 | `docs/v2/L7-test-design/helix-workflows-unit-test-design.md` | 単体テスト設計の正本 |
| ④ L7 テストコード | `cli/lib/tests/*`, `cli/lib/tests/bats/*`, hook smoke tests | L7 Sprint Step 2 carry。実体は本書では作成しない |

### §0.2 テスト方針

- F1-F5 は **feature 単位** で正常系・異常系・境界値を網羅する (各 feature 群として 3 分類を満たす。個々の public entry が 3 種すべてを持つとは限らず、§8 の feature-level trace で網羅性を判定する)。
- 異常系は `edge-case-design.md` の `EC-Fx-NNN` と対応させる。
- command / hook は単体境界で subprocess / payload fixture を使い、外部 LLM 実行や destructive write は mock / dry-run に閉じる。
- 全ケースの `implementation_status` は `planned` とし、fixture 実体とテストコードは L7 Sprint Step 2 の carry とする。

### §0.3 fixture 種別

| fixture 種別 | 構造 | 用途 |
|---|---|---|
| `tmp_docs_tree` | `docs/plans`, `docs/v2`, pair frontmatter を持つ一時 markdown tree | F1 trace / pair freeze / scaffold |
| `tmp_plan_tree` | PLAN markdown、frontmatter、requires/generates、巨大 file variant | F2 plan parser / validator / hook |
| `tmp_skill_tree` | `skills/**/SKILL.md`, catalog JSON, broken JSON variant | F3 catalog / recommender |
| `route_signal_payload` | dict/list JSON、missing key variant、illegal mode variant | F4 route engine / dispatcher |
| `tmp_helix_db` | fresh SQLite、必要 table と lock / split write variant | F5 audit / DB write / plan registry |
| `hook_payload_json` | PreToolUse / PostToolUse / SessionStart payload | F2/F3/F5 hook |
| `cli_runner` | subprocess wrapper または monkeypatch した argv/main 呼び出し | bash CLI / Python main |
| `clock_fixture` | now 固定、timeout / stale / debounce 境界 | retry / resource / debounce |

## §1 テスト全体方針

### §1.1 unit test framework

| 対象 | framework | 実装予定ファイル |
|---|---|---|
| Python module / class | pytest | `cli/lib/tests/test_helix_workflows_v2_unit.py` などへ分割 |
| bash CLI / hook | bats + shell subprocess smoke | `cli/lib/tests/bats/helix_workflows_v2_unit.bats` などへ分割 |
| schema / config | pytest + yaml/json parser | Python unit test に同梱 |
| hook payload | pytest subprocess + JSON payload fixture | hook 単体 smoke |

### §1.2 coverage 方針

| 指標 | 目標 | 判定 |
|---|---:|---|
| F1-F5 public entry case coverage | 100% | 本書の UT case が各 public entry を参照していること |
| Unit statement coverage | 80% 以上 | L7 Sprint Step 2 実装時に計測 |
| Branch / error branch coverage | 60% 以上 | fail-close / fail-open branch を優先 |
| Critical path | 100% | trace, plan registry, mode route, harness guard, DB write |

### §1.3 fixture pattern

- Arrange は fixture builder に寄せる。ただしテスト対象本体は mock しない。
- File system は temp dir へ閉じ、repository 実ファイルを破壊しない。
- DB は fresh SQLite を使い、lock / split write / duplicate logical event は最小 fixture で再現する。
- LLM / Codex / Claude 実行は単体テストでは起動せず、command construction と guard decision を検証する。

## §2 F1 ドキュメント体系 / pair freeze 単体テスト設計

| ケース ID | 対象設計 (関数/class/edge case ID) | 分類(正常/異常/境界) | 入力 (fixture種別・構造) | 期待結果 (戻り値/exit code/例外) | implementation_status | L6 source pointer |
|---|---|---|---|---|---|---|
| UT-F1-001 | F1-1 / CMD-F1-01 / EC-F1-001 | 境界 | `tmp_docs_tree`: 対象 docs 0 件、`cli_runner`: `helix doctor check-vmodel --json` | exit `0`、empty JSON payload、warning なし | planned | function §1 F1-1; class §2 CMD-F1-01; edge §2 EC-F1-001 |
| UT-F1-002 | F1-1 / PY-F1-01 / SCM-F1-01 / EC-F1-002 | 異常 | `cli_runner`: `helix doctor --json --summary` | exit `2`、usage error、file write なし | planned | function §1 F1-1; class §1.1 PY-F1-01; edge §2 EC-F1-002 |
| UT-F1-003 | F1-1 / EC-F1-003 | 異常 | `tmp_docs_tree`: slow scan、`clock_fixture`: 3s 超過を 3 回 | collect timeout、最終 exit `1050` | planned | function §1 F1-1; edge §2 EC-F1-003 |
| UT-F1-004 | F1-2 / PY-F1-01 / EC-F1-005 | 異常 | `tmp_docs_tree`: missing reference 1 件、`vmodel_lint.main(argv)` | exit `1010`、stderr または JSON issues に violation detail | planned | function §1 F1-2; class §1.1 PY-F1-01; edge §2 EC-F1-005 |
| UT-F1-005 | F1-2 / PY-F1-01 | 正常 | `tmp_docs_tree`: 4 artifact trace 完備、`argv=['--json']` | exit `0`、lint summary pass | planned | function §1 F1-2; class §1.1 PY-F1-01 |
| UT-F1-006 | F1-3 / PY-F1-02 / EC-F1-007 | 異常 | `tmp_docs_tree`: `pairs_test_design` 空 path | dict に missing edge、fail-close 相当 status、planned 扱いへ戻す | planned | function §1 F1-3; class §1.1 PY-F1-02; edge §2 EC-F1-007 |
| UT-F1-007 | F1-3 / PY-F1-02 / EC-F1-008 | 境界 | `tmp_docs_tree`: active PLAN 0 件、`active_only=True` | `missing=[]` の空結果、例外なし | planned | function §1 F1-3; edge §2 EC-F1-008 |
| UT-F1-008 | F1-4 / PY-F1-03 | 正常 | `tmp_docs_tree`: paired L6 doc、`dry_run=True`, `extract_functions=True` | `status=dry_run`、content に対象関数 section が含まれる、file write なし | planned | function §1 F1-4; class §1.1 PY-F1-03 |
| UT-F1-009 | F1-4 / PY-F1-03 / EC-F1-009 | 境界 | `tmp_docs_tree`: output file 既存、`dry_run=False`, `output_path` 指定 | `status=skipped`、既存 file を上書きしない | planned | function §1 F1-4; edge §2 EC-F1-009 |
| UT-F1-010 | F1-5 / PY-F1-04 / EC-F1-010 | 異常 | `matrix` fixture: `features` が list、resolver は spy | `ValueError`、resolver 未呼出、file write なし | planned | function §1 F1-5; class §1.1 PY-F1-04; edge §2 EC-F1-010 |
| UT-F1-011 | F1-5 / PY-F1-04 | 正常 | valid matrix、deliverables rules、deterministic resolver | 同一入力で同一 doc-map dict を返す | planned | function §1 F1-5; class §1.1 PY-F1-04 |
| UT-F1-012 | F1-6 / template artifact | 正常 | PLAN template render fixture、minimal plan metadata | frontmatter と 4 artifact trace skeleton を含む | planned | function §1 F1-6; class §1.6 境界 critical |
| UT-F1-013 | F1-6 / EC-F1-004 | 異常 | `tmp_docs_tree`: 4 domain 外 path を含む generated trace | fail-close、exit `2` 相当、後続 trace 計算停止 | planned | function §1 境界 critical; edge §2 EC-F1-004 |

## §3 F2 PLAN template / registry 単体テスト設計

| ケース ID | 対象設計 (関数/class/edge case ID) | 分類(正常/異常/境界) | 入力 (fixture種別・構造) | 期待結果 (戻り値/exit code/例外) | implementation_status | L6 source pointer |
|---|---|---|---|---|---|---|
| UT-F2-001 | F2-1 / CMD-F2-01 / EC-F2-001 | 境界 | `cli_runner`: `helix plan create --title '' --plan-id ''` | exit `1`、input invalid、file write なし | planned | function §2 F2-1; class §2 CMD-F2-01; edge §3 EC-F2-001 |
| UT-F2-002 | F2-2 / PY-F2-01 / SCM-F5-02 / EC-F2-003 | 異常 | `tmp_plan_tree`: broken YAML frontmatter | `parse_frontmatter()` は `None`、caller は `INVALID_FRONTMATTER` | planned | function §2 F2-2; class §1.2 PY-F2-01; edge §3 EC-F2-003 |
| UT-F2-003 | F2-2 / PY-F2-01 | 正常 | valid PLAN frontmatter + `tmp_helix_db` | `upsert_plan()` が `plan_registry` と related rows を更新 | planned | function §2 F2-2; class §1.2 PY-F2-01; schema §3 SCM-F5-02 |
| UT-F2-004 | F2-2 / EC-F2-004 | 異常 | `frontmatter={}`、`doc_path` 有効 | `failure_log` 追記、registry upsert なし | planned | function §2 境界 critical; edge §3 EC-F2-004 |
| UT-F2-005 | F2-2 / EC-F2-005 | 異常 | `tmp_helix_db`: requires graph に循環依存 | cycle list を返す、hook caller は exit `2` block | planned | function §2 F2-2; edge §3 EC-F2-005 |
| UT-F2-006 | F2-3 / PY-F2-02 / SCM-F2-01 / EC-F2-006 | 異常 | PLAN frontmatter: `process_layer=L99` | warning list に `process_layer_invalid`、CLI 層で fail-close | planned | function §2 F2-3; class §1.2 PY-F2-02; edge §3 EC-F2-006 |
| UT-F2-007 | F2-3 / EC-F2-007 | 境界 | requires graph: unknown dependency + known cycle 混在 | unknown は warning、known cycle は fail-close | planned | function §2 F2-3; edge §3 EC-F2-007 |
| UT-F2-008 | F2-4 / PY-F2-03 / EC-F2-008 | 異常 | frontmatter から required key 1 件欠落 | errors に `missing_<key>`、exit `1010` 相当 | planned | function §2 F2-4; class §1.2 PY-F2-03; edge §3 EC-F2-008 |
| UT-F2-009 | F2-4 / PY-F2-03 | 正常 | complete V2 PLAN frontmatter | empty error list、validator policy を再実装しない | planned | function §2 F2-4; class §1.2 PY-F2-03 |
| UT-F2-010 | F2-5 / PY-F2-04 / EC-F2-009 | 異常 | `tmp_helix_db`: lock 競合、`save_dependencies()` | retry なし、exit `1040` / `2` 相当、partial write なし | planned | function §2 F2-5; class §1.2 PY-F2-04; edge §3 EC-F2-009 |
| UT-F2-011 | F2-5 / CMD-F2-02 | 正常 | saved dependency graph + `load_dependencies()` | graph dict が保存内容と一致 | planned | function §2 F2-5; class §2 CMD-F2-02 |
| UT-F2-012 | F2-6 / HOOK-F2-01 / EC-F2-010 | 異常 | `hook_payload_json`: 同一 PLAN に同時 Edit/Write | 片方のみ upsert、cycle 検出時は decision=`block` | planned | function §2 F2-6; class §4 HOOK-F2-01; edge §3 EC-F2-010 |
| UT-F2-013 | F2-6 / EC-F2-011 | 異常 | hook 内 parser timeout 2 回連続 | exit `2`、decision=`block`、systemMessage に理由 | planned | function §2 F2-6; edge §3 EC-F2-011 |
| UT-F2-014 | F2-7 / PY-F2-05 / EC-F2-012 | 境界 | `plans_root` が存在しない | empty health payload、gate 強制化は carry として残る | planned | function §2 F2-7; class §1.2 PY-F2-05; edge §3 EC-F2-012 |
| UT-F2-015 | F2-7 / PY-F2-05 | 正常 | `tmp_plan_tree`: valid / warning / blocked PLAN 混在 | health summary が件数と status を分類 | planned | function §2 F2-7; class §1.2 PY-F2-05 |

## §4 F3 skill catalog / recommender 単体テスト設計

| ケース ID | 対象設計 (関数/class/edge case ID) | 分類(正常/異常/境界) | 入力 (fixture種別・構造) | 期待結果 (戻り値/exit code/例外) | implementation_status | L6 source pointer |
|---|---|---|---|---|---|---|
| UT-F3-001 | F3-1 / CMD-F3-01 / EC-F3-001 | 異常 | `cli_runner`: `helix skill show unknown-skill` | exit `1`、not found、cache 更新なし | planned | function §3 F3-1; class §2 CMD-F3-01; edge §4 EC-F3-001 |
| UT-F3-002 | F3-1 / EC-F3-002 | 境界 | `cli_runner`: `helix skill chain ''` | exit `1`、input invalid、dispatch なし | planned | function §3 F3-1; edge §4 EC-F3-002 |
| UT-F3-003 | F3-2 / PY-F3-01 / EC-F3-003 | 境界 | `tmp_skill_tree`: skills_root 空 | empty catalog を返す、save は caller 判断 | planned | function §3 F3-2; class §1.3 PY-F3-01; edge §4 EC-F3-003 |
| UT-F3-004 | F3-2 / PY-F3-01 / EC-F3-004 | 異常 | broken catalog JSON cache | 1 回 rebuild、再失敗なら exit `2` 相当 | planned | function §3 F3-2; edge §4 EC-F3-004 |
| UT-F3-005 | F3-3 / PY-F3-02 / EC-F3-005 | 境界 | `recommend(task_text='x', top_n=0)` | empty candidates、exit `0`、dispatch なし | planned | function §3 F3-3; class §1.3 PY-F3-02; edge §4 EC-F3-005 |
| UT-F3-006 | F3-3 / EC-F3-006 | 異常 | JSONL catalog unavailable + embedding unavailable | deterministic fallback、precision warning を issues に記録 | planned | function §3 F3-3; edge §4 EC-F3-006 |
| UT-F3-007 | F3-3 / PY-F3-02 | 正常 | `tmp_skill_tree`: testing / verification skill、task text="単体テスト設計" | top candidates に QA/testing 系 skill が含まれる | planned | function §3 F3-3; class §1.3 PY-F3-02 |
| UT-F3-008 | F3-4 / PY-F3-03 / SCM-F3-01 / EC-F3-007 | 異常 | unsupported agent role を持つ skill dispatch | `DispatcherError`、main は non-zero、temp file cleanup | planned | function §3 F3-4; class §1.3 PY-F3-03; edge §4 EC-F3-007 |
| UT-F3-009 | F3-4 / PY-F3-03 | 正常 | supported skill + dry_run dispatch | plan_only/delegated payload、`skill_usage` dry-run shape を返す | planned | function §3 F3-4; class §1.3 PY-F3-03; schema §3 SCM-F3-01 |
| UT-F3-010 | F3-5 / HOOK-F3-01 / EC-F3-008 | 異常 | `hook_payload_json`: 複数 SKILL.md 同時編集 | debounce file で 1 回に集約、hook exit `0` fail-open | planned | function §3 F3-5; class §4 HOOK-F3-01; edge §4 EC-F3-008 |

## §5 F4 mode routing / local workflow 単体テスト設計

| ケース ID | 対象設計 (関数/class/edge case ID) | 分類(正常/異常/境界) | 入力 (fixture種別・構造) | 期待結果 (戻り値/exit code/例外) | implementation_status | L6 source pointer |
|---|---|---|---|---|---|---|
| UT-F4-001 | F4-1 / CMD-F4-01 / EC-F4-001 | 異常 | `cli_runner`: `helix route --signal broken.json` | exit `1`、signal parse error、state write なし | planned | function §4 F4-1; class §2 CMD-F4-01; edge §5 EC-F4-001 |
| UT-F4-002 | F4-1 / EC-F4-002 | 境界 | `route_signal_payload`: 空 signal、`--json` | forward suggestion + warning、exit `0` | planned | function §4 F4-1; edge §5 EC-F4-002 |
| UT-F4-003 | F4-2 / PY-F4-01 / SCM-F4-01 / EC-F4-003 | 異常 | `RouteEngine.evaluate(signal='x', drift_type='unknown-explicit')` | fail-close または warning fallback、曖昧性 >2 は `clarification_required` | planned | function §4 F4-2; class §1.4 PY-F4-01; edge §5 EC-F4-003 |
| UT-F4-004 | F4-2 / PY-F4-01 / EC-F4-004 | 異常 | `from_detect_output()` に `detector/status/result` 欠落 | `ValueError`、exit `2` へ正規化 | planned | function §4 F4-2; edge §5 EC-F4-004 |
| UT-F4-005 | F4-2 / EC-F4-005 | 異常 | illegal transition table input | `ERROR(DOC-1030)`、exit `1030` / `2` | planned | function §4 F4-2; edge §5 EC-F4-005 |
| UT-F4-006 | F4-2 / PY-F4-01 | 正常 | 同一 signal / uncertainty / impact / env を 2 回評価 | 同一 `RouteResult` と command hint を返す | planned | function §4 F4-2; class §1.4 PY-F4-01 |
| UT-F4-007 | F4-3 / PY-F4-02 / EC-F4-006 | 異常 | unavailable shell command payload | `(False, message)`、dependent tasks not started | planned | function §4 F4-3; class §1.4 PY-F4-02; edge §5 EC-F4-006 |
| UT-F4-008 | F4-3 / EC-F4-007 | 異常 | webhook / command timeout | blocking dispatch は fail-close、advisory dispatch は audit warning | planned | function §4 F4-3; edge §5 EC-F4-007 |
| UT-F4-009 | F4-4 / PY-F4-03 / EC-F4-008 | 異常 | invalid YAML workflow file | validation errors、caller が exit `1/2` | planned | function §4 F4-4; class §1.4 PY-F4-03; edge §5 EC-F4-008 |
| UT-F4-010 | F4-4 / PY-F4-03 | 正常 | valid recovery/escalation workflow YAML | parsed dict + empty validation errors | planned | function §4 F4-4; class §1.4 PY-F4-03 |
| UT-F4-011 | F4-5 / PY-F4-04 / EC-F4-009 | 異常 | `verify_loop(loop_id='missing')` | `ValueError`、DB write なし | planned | function §4 F4-5; class §1.4 PY-F4-04; edge §5 EC-F4-009 |
| UT-F4-012 | F4-5 / CMD-F4-02 | 正常 | `init_local_loop()` with forward layer / hypothesis / acceptance | loop_id を返し、local state と audit event を保存 | planned | function §4 F4-5; class §2 CMD-F4-02 |
| UT-F4-013 | F4-6 / PY-F4-05 / CMD-F4-03 / EC-F4-010 | 境界 | `route_to_forward(..., artifact_links=[])` | forward 接続は許容、trace warning を残す | planned | function §4 F4-6; class §1.4 PY-F4-05; edge §5 EC-F4-010 |

## §6 F5 orchestration / audit / DB write 単体テスト設計

| ケース ID | 対象設計 (関数/class/edge case ID) | 分類(正常/異常/境界) | 入力 (fixture種別・構造) | 期待結果 (戻り値/exit code/例外) | implementation_status | L6 source pointer |
|---|---|---|---|---|---|---|
| UT-F5-001 | F5-1 / CMD-F5-01 / EC-F5-001 | 異常 | `cli_runner`: `helix codex --role qa` without task/task-file | exit `1`、usage、Codex 起動なし | planned | function §5 F5-1; class §2 CMD-F5-01; edge §6 EC-F5-001 |
| UT-F5-002 | F5-1 / EC-F5-002 | 異常 | plan/review task + write sandbox requested | read-only に強制降格、warning log | planned | function §5 F5-1; edge §6 EC-F5-002 |
| UT-F5-003 | F5-1 / CMD-F5-01 / EC-F5-003 | 異常 | approved execution + required approval evidence 欠落 | fail-close、exit `2`、task not executed | planned | function §5 F5-1; class §2 CMD-F5-01; edge §6 EC-F5-003 |
| UT-F5-004 | F5-2 / CMD-F5-02 / EC-F5-004 | 異常 | `helix claude --execute` with missing role template | exit `2`、prompt file write なし | planned | function §5 F5-2; class §2 CMD-F5-02; edge §6 EC-F5-004 |
| UT-F5-005 | F5-2 / CMD-F5-02 | 正常 | `helix claude --dry-run --role docs --task-file valid` | prompt text を生成、外部実行なし | planned | function §5 F5-2; class §2 CMD-F5-02 |
| UT-F5-006 | F5-3 / CMD-F5-03 / SCM-F5-04 / EC-F5-005 | 異常 | mandatory slot definition missing | fail-close、exit `2`、audit finding | planned | function §5 F5-3; class §2 CMD-F5-03; edge §6 EC-F5-005 |
| UT-F5-007 | F5-3 / EC-F5-006 | 境界 | 同一 slot の二重 fire | idempotent guard、二重 audit を防ぐ | planned | function §5 F5-3; edge §6 EC-F5-006 |
| UT-F5-008 | F5-4 / CMD-F1-01 / EC-F5-007 | 境界 | `helix doctor --summary --json` with summary 対象 0 件 | empty summary JSON、exit `0` | planned | function §5 F5-4; class §2 CMD-F1-01; edge §6 EC-F5-007 |
| UT-F5-009 | F5-5 / PY-F5-01 / EC-F5-008 | 異常 | DB に循環 graph | finding list、doctor summary は fail-close | planned | function §5 F5-5; class §1.5 PY-F5-01; edge §6 EC-F5-008 |
| UT-F5-010 | F5-6 / PY-F5-02 | 正常 | valid matrix fixture for doc-map generation | deterministic doc-map dict、file write なし | planned | function §5 F5-6; class §1.5 PY-F5-02 |
| UT-F5-011 | F5-7 / HOOK-F5-01 / EC-F5-009 | 異常 | subagent type / model family 不一致 payload | exit `2` block、stderr に block reason | planned | function §5 F5-7; class §4 HOOK-F5-01; edge §6 EC-F5-009 |
| UT-F5-012 | F5-8 / HOOK-F5-02 / EC-F5-010 | 異常 | audit DB write failure in auto fire hook | fail-open、stderr debug、main Agent 起動継続 | planned | function §5 F5-8; class §4 HOOK-F5-02; edge §6 EC-F5-010 |
| UT-F5-013 | F5-9 / HOOK-F5-03 | 正常 | PostToolUse dispatcher payload with 2 hook targets | fan-out し、個別 hook business rule は再実装しない | planned | function §5 F5-9; class §4 HOOK-F5-03 |
| UT-F5-014 | F5-10 / PY-F5-03 / EC-F5-011 | 異常 | dual-write 中に split DB 側だけ失敗 | context manager exit で rollback / error、caller は exit `2` | planned | function §5 F5-10; class §1.5 PY-F5-03; edge §6 EC-F5-011 |
| UT-F5-015 | F5-11 / PY-F5-04 / SCM-F5-01 / EC-F5-012 | 境界 | same logical event retry | duplicate insert を unique key で抑止、未実装なら L7 test fail | planned | function §5 F5-11; class §1.5 PY-F5-04; edge §6 EC-F5-012 |
| UT-F5-016 | F5-11 / PY-F5-04 | 正常 | valid invocation / selection payload | `invocation_log` / `task_selections` に insert、required keys 欠落なし | planned | function §5 F5-11; class §1.5 PY-F5-04; schema §3 SCM-F5-01 |

## §7 F6-F10 planned test contract

F6-F10 は governance 拡張領域であり、本書では test contract を先行凍結する。実装・fixture・テストコードは L7 carry とし、必要に応じて L8 結合テストで shadow replay / dual-write mismatch / migration rollback を補強する。

| ケース ID | 対象設計 (関数/class/edge case ID) | 分類(正常/異常/境界) | 入力 (fixture種別・構造) | 期待結果 (戻り値/exit code/例外) | implementation_status | L6 source pointer |
|---|---|---|---|---|---|---|
| UT-F6-001 | F6-1 / PLN-F6-01 / EC-F6-001 | 境界 | homeostasis metrics: gate_pass_rate 分母 0 | 分母を 1 とみなさず 0 扱い、health score 保守寄り | planned | function §6.1 F6-1; class §5 PLN-F6-01; edge §7 EC-F6-001 |
| UT-F6-002 | F6-2 / PLN-F6-02 / EC-F6-002 | 境界 | health score NaN | RED 暫定遷移、status warning | planned | function §6.1 F6-2; edge §7 EC-F6-002 |
| UT-F6-003 | F6 statusLine / EC-F6-003 | 異常 | 30s 未満の状態振動 | debounce suppress、audit metric 更新 | planned | function §6.1 F6-7; edge §7 EC-F6-003 |
| UT-F6-004 | F6-5 / EC-F6-004 | 境界 | `run_due_schedules(max_count=-1)` | `ValueError`、schedule state write なし | planned | function §6.1 F6-5; edge §7 EC-F6-004 |
| UT-F6-005 | F6-6 / PLN-F6-04 | 異常 | PreCompact high pressure payload | saturation 前 snapshot、fail-close 条件なら exit `2` | planned | function §6.1 F6-6; class §5 PLN-F6-04 |
| UT-F7-001 | F7-1 / PLN-F7-01 / PLN-F7-02 / EC-F7-001 | 異常 | evolution fork 失敗 | 親 PLAN は変更しない、state=`fail(fork_failed)` | planned | function §6.2 F7-1; class §5 PLN-F7-01; edge §7 EC-F7-001 |
| UT-F7-002 | F7-1 / EC-F7-002 | 境界 | score NaN / DRIFT_MAX 超過 | HOLD、drift は 1 に飽和 | planned | function §6.2 F7-1; edge §7 EC-F7-002 |
| UT-F7-003 | F7-3 / EC-F7-003 | 異常 | promote 中に target locked | exit `2`、promotion table write なし | planned | function §6.2 F7-3; edge §7 EC-F7-003 |
| UT-F7-004 | F7-4 / EC-F7-004 | 異常 | recipe schema / source invalid | `ValueError`、`.helix/recipes` write なし | planned | function §6.2 F7-4; edge §7 EC-F7-004 |
| UT-F8-001 | F8-1 / PLN-F8-01 / PLN-F8-02 / EC-F8-001 | 異常 | migration validate 失敗 | apply 進行不可、exit `2` | planned | function §6.3 F8-1; class §5 PLN-F8-01; edge §7 EC-F8-001 |
| UT-F8-002 | F8-2 / PLN-F8-03 / EC-F8-002 | 異常 | apply 後 verify 失敗 | backup から rollback、rollback_count increment | planned | function §6.3 F8-2; class §5 PLN-F8-03; edge §7 EC-F8-002 |
| UT-F8-003 | F8-3 / PLN-F8-04 / EC-F8-003 | 異常 | portable import checksum 不一致 | fail-close、staging しない | planned | function §6.3 F8-3; class §5 PLN-F8-04; edge §7 EC-F8-003 |
| UT-F8-004 | F8-6 / EC-F8-004 | 異常 | rollback confirm token 欠落 / backup path 不存在 | `ValueError` / `RuntimeError`、cutover env は変更しない | planned | function §6.3 F8-6; edge §7 EC-F8-004 |
| UT-F9-001 | F9-1 / PLN-F9-01 / EC-F9-001 | 境界 | apoptosis candidate with `last_modified` 欠損 | 候補除外、保守側 fail-safe | planned | function §6.4 F9-1; class §5 PLN-F9-01; edge §7 EC-F9-001 |
| UT-F9-002 | F9 config / EC-F9-002 | 境界 | `recent_window_days < 0` | config invalid、即時修正要求、exit `1/2` | planned | function §6.4 F9-1; edge §7 EC-F9-002 |
| UT-F9-003 | F9 autophagy / PLN-F9-03 / EC-F9-003 | 異常 | DB lock で retention scan 不能 | max 3 retry、最終 fail-close / quarantine | planned | function §6.4 F9-3; class §5 PLN-F9-03; edge §7 EC-F9-003 |
| UT-F9-004 | F9-2 / EC-F9-004 | 境界 | `max_age_days < 0` または recovery plan missing | false / warning、destructive cleanup へ進まない | planned | function §6.4 F9-2; edge §7 EC-F9-004 |
| UT-F10-001 | F10-1 / PLN-F10-01 / PLN-F10-02 / EC-F10-001 | 異常 | 同一 command / namespace 重複 | `reject_adopt`、conflict audit file 保存 | planned | function §6.5 F10-1; class §5 PLN-F10-01; edge §7 EC-F10-001 |
| UT-F10-002 | F10-2 / EC-F10-002 | 異常 | ACL adapter が権限昇格要求 | guard reject、HELIX core 継続 | planned | function §6.5 F10-2; edge §7 EC-F10-002 |
| UT-F10-003 | F10 heartbeat / EC-F10-003 | 異常 | heartbeat 3 回失敗 | stop and fallback、coexist status degraded | planned | function §6.5 F10-4; edge §7 EC-F10-003 |
| UT-F10-004 | F10-4 / PLN-F10-04 | 正常 | shadow replay dry-run, no mismatch | `ReplayResult` ready、state write なし | planned | function §6.5 F10-4; class §5 PLN-F10-04 |
| UT-F6-006 | F6 PreCompact / PLN-F6-04 | 異常 | precompact-state-snapshot.sh 高圧 payload | saturation 前 snapshot 保存、高圧時 fail-close (exit 2)、通常 fail-open | planned | function §6.1 PreCompact; class §5 PLN-F6-04 |
| UT-F6-007 | F6-7 / session_start_helpers.build_progress_block | 境界 | project_root に state 不在 | 空/最小 progress block を返し例外を出さない | planned | function §6.1 F6-7 |
| UT-F7-005 | PLN-F7-04 / posttooluse-mutation-event.sh | 異常 | scheduler audit write 遅延/失敗 | fail-open、warning issue 残置、本体継続 | planned | class §5 PLN-F7-04 |
| UT-F7-006 | F7-6 / demotion_checker.check_demotion_eligibility/demote | 境界 | violation_history 空 / days<0 | demotion 非適用、保守側 false | planned | function §6.2 F7-6 |
| UT-F8-005 | F8-5 / recovery_workflow_engine.main/snapshot_on_stop | 異常 | recovery state 不整合 / stop 中 snapshot | exit 1010、state quarantine、部分 write 残さない | planned | function §6.3 F8-5 |
| UT-F8-006 | F8-6 / rollback_orchestrator.rollback_preflight/rollback_execute | 異常 | confirm_token 欠落 / backup_path 不存在 | ValueError/RuntimeError、cutover env 不変 | planned | function §6.3 F8-6 |
| UT-F9-005 | F9-5 / rollback_orchestrator (apoptosis 連携) | 異常 | rollback 不能な部分失敗 | blocked へ遷移、quarantine + manual recovery 要求 | planned | function §6.4 F9-5 |
| UT-F9-006 | F9-6 / compatibility_adapter.write_connection (obsolete cleanup) | 境界 | obsolete record cleanup 中 DB lock | retry せず fail-close、二重 insert 回避は主キー依存 | planned | function §6.4 F9-6 |
| UT-F10-005 | F10-5 / cutover_orchestrator.cutover_preflight/cutover_execute | 異常 | confirm_token 不正 / preflight fail | cutover 実行せず exit 2、state 不変 | planned | function §6.5 F10-5 |
| UT-F10-006 | F10-6 / rollback_orchestrator (coexist 連携) | 異常 | coexist rollback verify fail | backup から rollback、rollback_count increment、audit 記録 | planned | function §6.5 F10-6 |

## §8 L6↔L7-test 双方向 trace 表 + implementation_status 集計

> **trace 粒度モデル (2026-05-29 doc-reviewer 反映)**: L6↔L7 の双方向 trace は **feature-level (Fx 設計群 ↔ UT-Fx-NNN 群)** を正本とする。本 §8 の feature 別 trace 表が SSoT。L6 doc 各 row の `→ UT-Fx-NNN` pointer は同一 feature 群内の代表 case を指すものであり、関数/class/edge と UT case の **厳密な row-level 1:1 binding は L7 Sprint Step 2 (テスト実装時) で test docstring の `DoD 検証: UT-Fx-NNN` により確定する** (それまでは feature-level trace で閉じる)。複数 L6 設計要素 (function/class/edge) が同一 feature の UT 群を多対多で共有するため、row 単位の ID 一致ではなく feature 単位の網羅性で freeze を判定する。

### §8.1 F1-F5 trace

| feature | L6 function IDs | L6 class/command/schema/hook IDs | L6 edge case IDs | L7 test case IDs | reverse pointer 方針 |
|---|---|---|---|---|---|
| F1 | F1-1..F1-6 | CMD-F1-01, PY-F1-01..04, SCM-F1-01 | EC-F1-001..010 | UT-F1-001..013 | L6 各 `→ UT-F1-NNN` と本書 case ID を一致させる |
| F2 | F2-1..F2-7 | CMD-F2-01..02, PY-F2-01..05, SCM-F2-01, SCM-F5-02, HOOK-F2-01 | EC-F2-001..012 | UT-F2-001..015 | plan registry / hook / dependency case は edge ID へ逆参照 |
| F3 | F3-1..F3-5 | CMD-F3-01, PY-F3-01..03, SCM-F3-01..02, HOOK-F3-01 | EC-F3-001..008 | UT-F3-001..010 | recommender fallback と debounce は edge ID へ逆参照 |
| F4 | F4-1..F4-6 | CMD-F4-01..03, PY-F4-01..05, SCM-F4-01 | EC-F4-001..010 | UT-F4-001..013 | illegal transition / detect schema は fail-close case として逆参照 |
| F5 | F5-1..F5-11 | CMD-F5-01..04, PY-F5-01..04, SCM-F5-01..05, HOOK-F5-01..06 | EC-F5-001..012 | UT-F5-001..016 | harness guard / DB write / audit duplicate は edge ID へ逆参照 |

### §8.2 F6-F10 planned contract trace

| feature | L6 function IDs | L6 planned design IDs | L6 edge case IDs | L7 test case IDs | reverse pointer 方針 |
|---|---|---|---|---|---|
| F6 | F6-1..F6-7 | PLN-F6-01..04 | EC-F6-001..004 | UT-F6-001..007 | homeostasis / PreCompact / session_start は L7 carry で実装後に docstring 参照 |
| F7 | F7-1..F7-6 | PLN-F7-01..04 | EC-F7-001..004 | UT-F7-001..006 | evolution planned CLI / demotion_checker と existing learn/promote を分けて参照 |
| F8 | F8-1..F8-6 | PLN-F8-01..05 | EC-F8-001..004 | UT-F8-001..006 | migration / recovery / rollback は L8 結合にも carry |
| F9 | F9-1..F9-6 | PLN-F9-01..03 | EC-F9-001..004 | UT-F9-001..006 | destructive cleanup / rollback / obsolete cleanup は単体では進めず guard を固定 |
| F10 | F10-1..F10-6 | PLN-F10-01..04 | EC-F10-001..003 | UT-F10-001..006 | coexist / ACL / heartbeat / cutover / rollback は adapter 差分を L8 へ carry |

### §8.3 implementation_status 集計

| 範囲 | planned case count | 正常 | 異常 | 境界 | 実行 status |
|---|---:|---:|---:|---:|---|
| §2 F1 | 13 | 4 | 6 | 3 | planned |
| §3 F2 | 15 | 4 | 8 | 3 | planned |
| §4 F3 | 10 | 2 | 5 | 3 | planned |
| §5 F4 | 13 | 3 | 8 | 2 | planned |
| §6 F5 | 16 | 4 | 9 | 3 | planned |
| F1-F5 subtotal | 67 | 17 | 36 | 14 | planned |
| §7 F6-F10 | 31 | 1 | 20 | 10 | planned |
| total | 98 | 18 | 56 | 24 | planned |

### §8.4 品質レベル / 未検出リスク / ゲート判定

| 項目 | 判定 |
|---|---|
| テスト設計品質 Lv | T3.5 相当。F1-F5 は正常・異常・境界を網羅し T3 を超えるが、実行 fixture / coverage 実測が未実施のため T4 は L7 Step 2 後に判定する |
| G4 (非対象・参考) | 本書の正対 pair は L6↔L7 単体テストであり、G4 (L4↔L9 総合テスト) は対象外。参考として、本書の trace 設計は L4 側 evidence と矛盾しない |
| G6 判定 | pass。L6 function / class / edge case から本書の UT case へ双方向 trace 可能 |
| カバレッジ | 設計 coverage: F1-F5 public entry 100%。実測 statement / branch coverage は未実行 |
| 未検出リスク | F6-F10 planned 領域、DB lock 復旧時間、migration rollback、external framework ACL 差分は単体テストだけでは検出不能。L8 結合テストへ carry |

### §8.5 L7 carry

| carry ID | 内容 | 受入条件 |
|---|---|---|
| CARRY-L7-UNIT-001 | 本書 98 case を pytest / bats / hook smoke に分割実装 | 各 test docstring / test name に `DoD 検証: helix-workflows-unit-test-design.md UT-Fx-NNN` を記載 |
| CARRY-L7-UNIT-002 | fixture 実体作成 | `tmp_docs_tree`, `tmp_plan_tree`, `tmp_skill_tree`, `tmp_helix_db`, `hook_payload_json` が再利用可能 |
| CARRY-L7-UNIT-003 | coverage gate 接続 | F1-F5 unit statement 80% 以上、branch 60% 以上、critical path 100% |
| CARRY-L8-INT-001 | F8/F10 migration / coexist の結合検証 | shadow replay / dual-write mismatch / rollback を integration test で検証 |
