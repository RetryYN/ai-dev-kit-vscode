---
doc_id: l6-helix-workflows-class-module-command-design
title: "HELIX-workflows V2 Class/Module/Command 設計"
status: frozen
process_layer: L6
doc_type: class_module_command_design
parent_plan: L6-helix-workflows-クラス設計plan
pairs_design: docs/v2/L5-internal-design/helix-workflows-module-decomposition-design.md
pairs_test_design: docs/v2/L7-test-design/helix-workflows-unit-test-design.md
---

# HELIX-workflows V2 Class/Module/Command 設計

## §0 概要

本書は L5 詳細設計 4 文書と L6 関数仕様設計を入力に、L7 実装スプリントが直接参照できる粒度まで Class / Module / Command / Schema / Hook の入口契約を凍結する L6 機能設計である。TL 助言に従い「クラス設計」は Python class / dataclass / module API、bash CLI subcommand、config/schema、hook/agent contract を一体で扱う。

### §0.1 4 種の設計対象

1. Python lib: class / dataclass / module API。責務、公開メソッド、属性、不変条件を固定する。
2. bash CLI: `helix-*` subcommand。引数、exit code、stdout/stderr、side effect を固定する。
3. config/schema: `cli/config/*.yaml` と `helix.db` table。validation、default、互換性を固定する。
4. hook/agent: `.claude/hooks` と `.claude/agents`。event contract、envelope、失敗時動作を固定する。

### §0.2 scope

- F1-F5: 設計本体化。実装の有無とは分けて、入口契約を complete に記述する。
- F6-F10: planned contract。signature / 責務 / schema / hook contract を固定し、実体の carry は `implementation_status` で正直に残す。
- `implementation_status` は `implemented / partial / planned` の 3 値で統一する。

### §0.3 pair freeze 注記

- L7 pair 先は `docs/v2/L7-test-design/helix-workflows-unit-test-design.md` として pointer を先行確保する。
- L7 単体テスト設計 doc (helix-workflows-unit-test-design.md) は 2026-05-29 に作成済。本書の `→ UT-Fx-NNN` pointer は L7 doc 内の UT-Fx-NNN として定義済で双方向 trace が解決する。fixture 実体・テストコードは L7 Sprint Step 2 carry。

## §1 Python lib class/module 設計

### §1.1 F1 document lifecycle / pair freeze

| 設計対象 ID | 種別(class/command/schema/hook) | owner module/file | 責務 / 公開 API | 依存方向 | implementation_status | L7 単体テスト pointer (→UT-Fx-NNN) | L5/関数仕様 source ref |
|---|---|---|---|---|---|---|---|
| PY-F1-01 | class | `cli/lib/vmodel_lint.py` | `main(argv=None) -> int`。4 artifact 双方向 trace を lint し、CLI へ domain exit code を返す。invariant: file write を持たない。 | `helix-doctor -> vmodel_lint -> vmodel_pair_freeze/docs` | implemented | `→ UT-F1-002` | `→ L5 module §2.1 F1-2`; `→ L5 IF A-01..A-14`; `→ L6 function §1 F1-2` |
| PY-F1-02 | class | `cli/lib/vmodel_pair_freeze.py` | `check_pair_freeze(layer, ...) -> dict[str, Any]`。L6↔L7 を含む pair freeze の read-only 監査。invariant: 同一 docs tree に対して決定的。 | `vmodel_pair_freeze -> docs/plans + docs/v2` | implemented | `→ UT-F1-003` | `→ L5 module §2.1 F1-3`; `→ L6 function §1 F1-3` |
| PY-F1-03 | class | `cli/lib/test_design_scaffold.py` | `generate_skeleton()` / `write_scaffold()`。pair design doc から unit/integration/system test 雛形を抽出。invariant: `dry_run=True` では純関数。 | `test_design_scaffold -> paired design docs` | implemented | `→ UT-F1-004` | `→ L5 module §2.1 F1-4`; `→ L6 function §1 F1-4` |
| PY-F1-04 | class | `cli/lib/gate_check_generator.py` | `build_doc_map(...) -> dict[str, Any]`。gate / doc-map 生成。invariant: malformed matrix は `ValueError` で fail-close。 | `gate_check_generator -> matrix compiler -> gate files/hooks` | implemented | `→ UT-F1-005` | `→ L5 module §2.1 F1-5`; `→ L6 function §1 F1-5` |

### §1.2 F2 PLAN registry / parser

| 設計対象 ID | 種別(class/command/schema/hook) | owner module/file | 責務 / 公開 API | 依存方向 | implementation_status | L7 単体テスト pointer (→UT-Fx-NNN) | L5/関数仕様 source ref |
|---|---|---|---|---|---|---|---|
| PY-F2-01 | class | `cli/lib/plan_parser.py` | `parse_frontmatter()` / `upsert_plan()`。frontmatter parse と registry 更新だけを担当。invariant: semantic validation を抱え込まない。 | `plan_parser -> plan_dependencies + helix.db` | implemented | `→ UT-F2-002` | `→ L5 module §2.1 F2-2`; `→ L6 function §2 F2-2` |
| PY-F2-02 | class | `cli/lib/plan_validator.py` | `validate_plan()` / `detect_dependency_cycle()`。path / role / dependency cycle を静的検査。invariant: write を持たず warning list に正規化。 | `plan_validator -> parsed frontmatter + role config` | implemented | `→ UT-F2-003` | `→ L5 module §2.1 F2-3`; `→ L6 function §2 F2-3` |
| PY-F2-03 | class | `cli/lib/plan_lint.py` | `validate_plan_frontmatter()`。文面 lint と duplicate 候補検出。invariant: validator の policy を再実装しない。 | `plan_lint -> plan_validator.VALID_KINDS` | implemented | `→ UT-F2-004` | `→ L5 module §2.1 F2-4`; `→ L6 function §2 F2-4` |
| PY-F2-04 | class | `cli/lib/plan_dependencies.py` | `load_dependencies()` / `save_dependencies()`。dependency graph の保存・読取専用。 | `plan_dependencies -> plan_registry / helix.db` | implemented | `→ UT-F2-005` | `→ L5 module §2.1 F2-5`; `→ L6 function §2 F2-5` |
| PY-F2-05 | class | `cli/lib/plan_health.py` | `scan_all_plans()`。plan tree の健康度集計。invariant: fail-close 判定そのものは CLI/gate 側が担当。 | `plan_health -> docs/plans tree` | partial | `→ UT-F2-007` | `→ L5 module §2.1 F2-7`; `→ L6 function §2 F2-7` |

### §1.3 F3 skill catalog / recommender

| 設計対象 ID | 種別(class/command/schema/hook) | owner module/file | 責務 / 公開 API | 依存方向 | implementation_status | L7 単体テスト pointer (→UT-Fx-NNN) | L5/関数仕様 source ref |
|---|---|---|---|---|---|---|---|
| PY-F3-01 | class | `cli/lib/skill_catalog.py` | `build_catalog()` / `load_catalog()`。`SKILL.md` を catalog へ正規化。invariant: catalog の source of truth は skills tree。 | `skill_catalog -> skills/**/SKILL.md` | implemented | `→ UT-F3-002` | `→ L5 module §2.1 F3-2`; `→ L6 function §3 F3-2` |
| PY-F3-02 | class | `cli/lib/skill_recommender.py` | `recommend(...) -> dict[str, Any]`。task text を skill 候補へ写像し TTL cache を持つ。 | `skill_recommender -> skill_catalog + cache` | implemented | `→ UT-F3-003` | `→ L5 module §2.1 F3-3`; `→ L6 function §3 F3-3` |
| PY-F3-03 | class | `cli/lib/skill_dispatcher.py` | `determine_agent()` / `dispatch()`。推挙結果を Codex / Claude dispatch に変換。invariant: skill score の再計算をしない。 | `skill_dispatcher -> helix codex/claude + skill_usage` | implemented | `→ UT-F3-004` | `→ L5 module §2.1 F3-4`; `→ L6 function §3 F3-4` |

### §1.4 F4 mode routing / local workflow

| 設計対象 ID | 種別(class/command/schema/hook) | owner module/file | 責務 / 公開 API | 依存方向 | implementation_status | L7 単体テスト pointer (→UT-Fx-NNN) | L5/関数仕様 source ref |
|---|---|---|---|---|---|---|---|
| PY-F4-01 | class | `cli/lib/route_engine.py` | `RouteEngine.evaluate()` / `from_detect_output()`。mode 判定と alias 正規化のみ。invariant: side effect を持たない。 | `route_engine -> route result only` | implemented | `→ UT-F4-002` | `→ L5 module §2.1 F4-2`; `→ L6 function §4 F4-2` |
| PY-F4-02 | class | `cli/lib/task_dispatcher.py` | `dispatch_task()`。承認済み task を shell / helix command / webhook に変換。invariant: route 判定を再実行しない。 | `task_dispatcher -> command adapters` | implemented | `→ UT-F4-003` | `→ L5 module §2.1 F4-3`; `→ L6 function §4 F4-3` |
| PY-F4-03 | class | `cli/lib/workflow_dsl_parser.py` | `load_workflow()` / `validate_workflow_schema()`。workflow YAML を parse し schema を検証。 | `workflow_dsl_parser -> recovery/escalation workflow yaml` | partial | `→ UT-F4-004` | `→ L5 module §2.1 F4-4`; `→ L6 function §4 F4-4` |
| PY-F4-04 | class | `cli/lib/scrum_local.py` | `init_local_loop()` / `verify_loop()` / `decide_loop()`。Discovery/Scrum local state 管理。 | `scrum_local -> compatibility_adapter.write_connection()` | implemented | `→ UT-F4-005` | `→ L5 module §2.1 F4-5`; `→ L6 function §4 F4-5` |
| PY-F4-05 | class | `cli/lib/reverse_local.py` | `route_to_forward()`。Reverse から Forward への handoff を単責務で保持。 | `reverse_local -> reverse state -> Forward handoff` | implemented | `→ UT-F4-006` | `→ L5 module §2.1 F4-6`; `→ L6 function §4 F4-6` |

### §1.5 F5 orchestration / audit / DB write

| 設計対象 ID | 種別(class/command/schema/hook) | owner module/file | 責務 / 公開 API | 依存方向 | implementation_status | L7 単体テスト pointer (→UT-Fx-NNN) | L5/関数仕様 source ref |
|---|---|---|---|---|---|---|---|
| PY-F5-01 | class | `cli/lib/doctor_plan_checks.py` | `run_check_plan_drift()` / `run_check_plan_cycle()`。doctor finding 生成専用。invariant: artifact 生成を行わない。 | `doctor_plan_checks -> plan_parser / plan_validator` | implemented | `→ UT-F5-005` | `→ L5 module §2.1 F5-5`; `→ L6 function §5 F5-5` |
| PY-F5-02 | class | `cli/lib/gate_check_generator.py` | `build_doc_map()`。gate / doc-map の deterministic generator。 | `gate_check_generator -> matrix compiler -> gate files` | implemented | `→ UT-F5-006` | `→ L5 module §2.1 F5-6`; `→ L6 function §5 F5-6` |
| PY-F5-03 | class | `cli/lib/compatibility_adapter.py` | `write_connection()`。helix.db dual-write / cutover / rollback の唯一の物理境界。invariant: 上位からの direct SQLite write を許可しない。 | `hook/CLI -> compatibility_adapter -> sqlite` | implemented | `→ UT-F5-010` | `→ L5 module §2.1 F5-10`; `→ L6 function §5 F5-10` |
| PY-F5-04 | class | `cli/lib/helix_db.py` | `record_invocation()` / `record_selection()`。監査 event / selection の persistence façade。 | `helix_db -> sqlite persistence` | implemented | `→ UT-F5-011` | `→ L5 module §2.1 F5-11`; `→ L6 function §5 F5-11` |

### §1.6 境界 critical

#### routing

`route_engine.py` は recommendation / normalization に限定し、`task_dispatcher.py` が execution を持つ。`RouteEngine.evaluate()` の返り値をそのまま `dispatch_task()` へ渡す一方向依存に固定し、route 側で shell 実行や DB write を始めない。失敗時は `DispatchError` か blocked payload で止め、route 再計算による fail-open を避ける。

#### plan parser

`plan_parser.py` は YAML frontmatter を読み、registry へ upsert するだけである。意味検証、role 解決、cycle 検出は `plan_validator.py` と `plan_lint.py` に分離する。不変条件は「parse failure と policy failure を同じ層で扱わない」ことで、これを崩すと hook 失敗の attribution ができなくなる。

#### doctor / gate

`cli/helix-doctor` は shell entry の集約器で、doctor 本体は `vmodel_lint.py` と `doctor_plan_checks.py` が持つ。逆に `gate_check_generator.py` は finding を作らず artifact 生成だけを持つ。この分離により「read-only 監査」と「生成系 mutation」の責務が交差しない。

#### DB write

`compatibility_adapter.write_connection()` を helix.db write の唯一境界に固定する。hook、CLI、local workflow が SQLite を直接開き始めると dual-write / cutover / rollback の対称性が壊れるため、上位層は connection acquisition を adapter に委譲し、`helix_db.py` は persistence API に徹する。

## §2 bash CLI subcommand 設計

| 設計対象 ID | 種別(class/command/schema/hook) | owner module/file | 責務 / 公開 API | 依存方向 | implementation_status | L7 単体テスト pointer (→UT-Fx-NNN) | L5/関数仕様 source ref |
|---|---|---|---|---|---|---|---|
| CMD-F1-01 | command | `cli/helix-doctor` | `helix doctor check-* [--json] [--timeout N]`。read-only doctor family。exit `0/1/2/10xx`、stdout は text/JSON、stderr は `ERROR(DOC-10xx)`。 | `doctor CLI -> vmodel_lint / doctor_plan_checks` | implemented | `→ UT-F1-001` | `→ L5 IF §2 A-01..A-14`; `→ L6 function §1 F1-1` |
| CMD-F2-01 | command | `cli/helix-plan` | `helix plan <create|view|fork|status|apoptosis|validate> [--json]`。plan lifecycle を公開。fork/apoptosis のみ mutation。 | `helix-plan -> plan_parser / validator / health` | implemented | `→ UT-F2-001` | `→ L5 IF §4 A-18..A-22`; `→ L6 function §2 F2-1` |
| CMD-F2-02 | command | `cli/helix-matrix` | `helix matrix --plan-id <id> [--json] [--diff <other-id>]`。coverage 行列の read-mostly 出口。 | `matrix -> gate_check_generator` | partial | `→ UT-F2-005` | `→ L5 IF A-21`; `→ L5 module §2.1 F2-5` |
| CMD-F3-01 | command | `cli/helix-skill` | `helix skill <search|chain|use|catalog rebuild|stats|review-pending|approve>`。catalog / recommender / dispatcher の公開入口。 | `helix-skill -> catalog / recommender / dispatcher` | implemented | `→ UT-F3-001` | `→ L5 IF §12.5 A-93`; `→ L6 function §3 F3-1` |
| CMD-F4-01 | command | `cli/helix-route` | `helix route`。9 mode 入口の推奨判定のみ。dry-run 的に使え、直接 mutation を起こさない。 | `helix-route -> route_engine` | implemented | `→ UT-F4-001` | `→ L5 module §2.1 F4-1`; `→ L6 function §4 F4-1` |
| CMD-F4-02 | command | `cli/helix-discovery` | `helix discovery <init|backlog|plan|poc|verify|decide>`。local state machine の公開入口。 | `discovery CLI -> scrum_local` | implemented | `→ UT-F4-005` | `→ L5 module §2.1 F4-5`; `→ L5 IF A-73`; `→ L6 function §4 F4-5` |
| CMD-F4-03 | command | `cli/helix-reverse` | `helix reverse <type> <phase>`。Reverse から Forward への handoff を含む。 | `reverse CLI -> reverse_local` | implemented | `→ UT-F4-006` | `→ L5 module §2.1 F4-6`; `→ L5 IF A-70`; `→ L6 function §4 F4-6` |
| CMD-F5-01 | command | `cli/helix-codex` | `helix codex --role <role> --task ... [--plan-only|--approved]`。Codex 実行 harness。allowed-files / diff_lines 監査を後段に接続。 | `helix-codex -> codex post validation/hook` | implemented | `→ UT-F5-001` | `→ L5 module §2.1 F5-1`; `→ L5 IF A-89`; `→ L6 function §5 F5-1` |
| CMD-F5-02 | command | `cli/helix-claude` | `helix claude --role <role> --task ... --dry-run`。Claude task-file/prompt 生成。 | `helix-claude -> prompt/task-file generation` | implemented | `→ UT-F5-002` | `→ L5 module §2.1 F5-2`; `→ L5 IF A-90`; `→ L6 function §5 F5-2` |
| CMD-F5-03 | command | `cli/helix-agent` | `helix agent {fire-mandatory|suggest|audit}`。mandatory/on-demand agent を統制。 | `helix-agent -> agent slots / role_audit` | implemented | `→ UT-F5-003` | `→ L5 module §2.1 F5-3`; `→ L5 IF A-65`; `→ L6 function §5 F5-3` |
| CMD-F5-04 | command | `cli/helix-review` | `helix review --uncommitted`。差分 review を read-only で返す。 | `review CLI -> codex review harness` | implemented | `→ UT-F5-003` | `→ L5 IF A-92`; `→ L5 module §2.1 F5-3` |

### §2.1 境界 critical

#### doctor

`helix doctor check-*` は read-only family とし、`--fix` のような mutation を持つ場合でも別 flag を明示して default では無効にする。stdout は summary/JSON、stderr は error template、exit code は `0/1/2/10xx` に正規化し、doctor の分岐で独自コードを増殖させない。

#### command orchestration

`helix plan` は lifecycle mutation を持つが、`helix route` は持たない。この差を崩して route 側に実行責務を混ぜると、mode recommendation と irreversible mutation が同じ entry に閉じ込められるため禁止する。`helix codex` / `helix claude` / `helix agent` も同様で、dispatch command が business rule を独自実装せず、下位 module に委譲する。

## §3 config/schema 設計

| 設計対象 ID | 種別(class/command/schema/hook) | owner module/file | 責務 / 公開 API | 依存方向 | implementation_status | L7 単体テスト pointer (→UT-Fx-NNN) | L5/関数仕様 source ref |
|---|---|---|---|---|---|---|---|
| SCM-F1-01 | schema | `cli/config/vmodel-semantics.yaml` | V-model layer pair / trace ルールを定義。default は L1↔L14 ... L6↔L7。validation: unknown layer pair は fail-close。 | `doctor/gate -> vmodel semantics` | implemented | `→ UT-F1-002` | `→ L5 module §5.1`; `→ L5 IF §1`; `→ L6 function §1 F1-2` |
| SCM-F2-01 | schema | `cli/config/plan-limits.yaml` | plan size / age / lint 上限を定義。default は policy-driven、missing key は conservative default を採用。 | `plan_validator / doctor -> plan-limits` | implemented | `→ UT-F2-003` | `→ L5 module §5.1`; `→ L5 IF A-03,A-13`; `→ L6 function §2 F2-3` |
| SCM-F3-01 | schema | `cli/config/models.yaml` | role→model/thinking map。validation: role key 必須、unknown model family は warning ではなく fail-close。 | `helix-codex/claude -> role config` | implemented | `→ UT-F3-004` | `→ L5 module §5.1`; `→ L5 IF A-06`; `→ L6 function §3 F3-4` |
| SCM-F3-02 | schema | `cli/config/model-fallback.yaml` | fallback chain を定義。default は primary role model のみ、fallback は opt-in。 | `budget/dispatcher -> model fallback` | implemented | `→ UT-F3-004` | `→ L5 module §5.1`; `→ L6 function §3 F3-4` |
| SCM-F4-01 | schema | `helix.db.mode_transition` | mode handoff の永続 record。validation: `(plan_id, mode_from, mode_to, started_at)` uniqueness。 | `route/recovery -> mode_transition` | partial | `→ UT-F4-002` | `→ L5 physical §2.4`; `→ L5 module §2.1 F4-2`; `→ L6 function §4 F4-2` |
| SCM-F5-01 | schema | `helix.db.event_log` | hook / CLI / gate の append-only audit。default `schema_version=36`、`metadata_json='{}'`。 | `hooks/CLI -> event_log` | implemented | `→ UT-F5-011` | `→ L5 physical §2.1`; `→ L5 module §2.1 F5-11`; `→ L6 function §5 F5-11` |
| SCM-F5-02 | schema | `helix.db.plan_registry` | plan frontmatter registry。validation: `plan_id` PK、`frontmatter_json` 必須。 | `plan_parser -> plan_registry` | implemented | `→ UT-F2-002` | `→ L5 physical §2.2`; `→ L5 module §2.1 F2-2`; `→ L6 function §2 F2-2` |
| SCM-F5-03 | schema | `helix.db.skill_usage` | skill dispatch / Task hook の usage 監査。compatibility: 既存列名維持で migrate safe。 | `skill_dispatcher / Task hook -> skill_usage` | implemented | `→ UT-F3-004` | `→ L5 physical §2.3`; `→ L5 module §2.1 F3-4`; `→ L6 function §3 F3-4` |
| SCM-F5-04 | schema | `helix.db.role_audit` | agent / handover / delegation 監査。default `risk_level='medium'`。 | `helix-agent / hooks -> role_audit` | partial | `→ UT-F5-003` | `→ L5 physical §2.5`; `→ L5 IF §10`; `→ L6 function §5 F5-3` |
| SCM-F5-05 | schema | `helix.db.audit_link` | artifact 間 trace link。validation: `(from,to,link_type)` unique。 | `doctor/gate/hook -> audit_link` | partial | `→ UT-F5-011` | `→ L5 physical §2.6`; `→ L5 IF §12`; `→ L6 function §5 F5-11` |

### §3.1 schema 境界

config file は「policy / default / compatibility」を持ち、runtime state を持たない。逆に `helix.db` table は runtime state / audit を持つが、policy source of truth にはならない。この境界を守ることで migration 時に「設定の意味論」と「実行履歴」が混ざらない。

## §4 hook/agent contract 設計

| 設計対象 ID | 種別(class/command/schema/hook) | owner module/file | 責務 / 公開 API | 依存方向 | implementation_status | L7 単体テスト pointer (→UT-Fx-NNN) | L5/関数仕様 source ref |
|---|---|---|---|---|---|---|---|
| HOOK-F2-01 | hook | `.claude/hooks/posttooluse-plan-auto-register.sh` | `PostToolUse(Edit/Write on PLAN*.md)`。payload `{decision, systemMessage}` を返し、plan auto-register を実行。fail-close on cycle block。 | `PostToolUse -> plan_parser -> plan_registry` | implemented | `→ UT-F2-006` | `→ L5 module §2.1 F2-6`; `→ L5 module §6.2`; `→ L5 IF §10.7`; `→ L6 function §2 F2-6` |
| HOOK-F3-01 | hook | `.claude/hooks/posttooluse-skill-catalog-rebuild.sh` | `PostToolUse(SKILL.md Write/Edit)`。catalog/jsonl rebuild を debounce し、fail-open で usage を止めない。 | `PostToolUse -> skill_catalog -> cache` | implemented | `→ UT-F3-005` | `→ L5 module §2.1 F3-5`; `→ L5 module §6.2`; `→ L6 function §3 F3-5` |
| HOOK-F5-01 | hook | `.claude/hooks/pretooluse-agent-guard.sh` | `PreToolUse(agent-guard)`。payload 必須キー `tool_name, agent_name, risk_level, policy_id`。違反は exit `2` で fail-close。 | `PreToolUse -> policy check -> role_audit/event_log` | implemented | `→ UT-F5-007` | `→ L5 module §2.1 F5-7`; `→ L5 IF §10.3`; `→ L6 function §5 F5-7` |
| HOOK-F5-02 | hook | `.claude/hooks/pretooluse-agent-fire.sh` | `PreToolUse(agent auto fire)`。slot 記録と mandatory agent fire の準備。 | `PreToolUse -> session helper / role_audit` | implemented | `→ UT-F5-008` | `→ L5 module §2.1 F5-8`; `→ L5 IF §10.3`; `→ L6 function §5 F5-8` |
| HOOK-F5-03 | hook | `.claude/hooks/post-tool-use.sh` | `PostToolUse dispatcher`。posttooluse-* fan-out の集約器。invariant: 個別 hook の business rule を再実装しない。 | `PostToolUse -> posttooluse-*` | implemented | `→ UT-F5-009` | `→ L5 module §2.1 F5-9`; `→ L5 module §6.2`; `→ L6 function §5 F5-9` |
| HOOK-F5-04 | hook | `.claude/hooks/sessionstart-harness-summary.sh` | `SessionStart`。payload `{session_id,cwd,user_context,compact_state}`。初期 context 注入。 | `SessionStart -> context bundle / role_audit` | implemented | `→ UT-F5-003` | `→ L5 module §6.2`; `→ L5 IF §10.4` |
| HOOK-F5-05 | hook | `.claude/hooks/userpromptsubmit-context-bundle.sh` | `UserPromptSubmit`。prompt intent を context bundle として増補。fail-open。 | `UserPromptSubmit -> context bundle` | implemented | `→ UT-F5-003` | `→ L5 module §6.2`; `→ L5 IF §10.5` |
| HOOK-F5-06 | hook | `.claude/agents/*.md` | subagent envelope。最低 `{role, slot_label, plan_id?, handover_id?, task}` を持ち、禁止 7 種は起動禁止。 | `helix-agent -> allowed agent set -> role_audit` | implemented | `→ UT-F5-003` | `→ L5 module §7`; `→ L5 IF §10`; `→ L5 IF A-65` |

### §4.1 hook orchestration 境界

PreToolUse、PostToolUse、SessionStart、UserPromptSubmit は混線させない。PreToolUse は block/allow のみ、PostToolUse は fan-out と audit、SessionStart は context injection、UserPromptSubmit は prompt augmentation に固定する。失敗時動作は interface 詳細設計の `fail-close / fail-open` をそのまま継承し、hook 同士が相互に state machine を再実装しない。

## §5 F6-F10 planned contract

| 設計対象 ID | 種別(class/command/schema/hook) | owner module/file | 責務 / 公開 API | 依存方向 | implementation_status | L7 単体テスト pointer (→UT-Fx-NNN) | L5/関数仕様 source ref |
|---|---|---|---|---|---|---|---|
| PLN-F6-01 | class | `cli/lib/homeostasis.py` | planned module API。`collect_pressure()` / `evaluate_saturation()` / `emit_homeostasis_status()` を持ち、F6 signals を統合する。 | `homeostasis -> budget/plan_health/metrics_log` | planned | `→ UT-F6-001` | `→ L5 module §2.1 F6-1`; `→ L6 function §6.1 F6-1` |
| PLN-F6-02 | command | `cli/helix-budget` | `helix budget status --homeostasis [--days N] [--project <name>]`。pressure index を返す read-only command。 | `budget CLI -> homeostasis.py` | partial | `→ UT-F6-002` | `→ L5 IF A-16`; `→ L6 function §6.1 F6-2/F6-3` |
| PLN-F6-03 | schema | `helix.db.metrics_log` | homeostasis metrics table。default `metric_scope='global'`、derived metrics を区別。 | `collectors -> metrics_log` | planned | `→ UT-F6-004` | `→ L5 physical §3.1`; `→ L6 function §6.1 F6-4..F6-7` |
| PLN-F6-04 | hook | `.claude/hooks/precompact-state-snapshot.sh` | `PreCompact` 時に saturation 前の snapshot を残す。高圧時は fail-close、通常は fail-open しない。 | `PreCompact -> metrics/backup` | implemented | `→ UT-F6-006` | `→ L5 IF §10.2`; `→ L5 module §6.2`; `→ L6 function §6.1 F6-6` |
| PLN-F7-01 | class | `cli/lib/evolution.py` | planned module API。`score_plan()`, `promote_artifact()`, `deprecate_artifact()` を façade として提供。 | `evolution -> learning_engine / demotion_checker / plan_history` | planned | `→ UT-F7-001` | `→ L5 module §2.1 F7-1`; `→ L6 function §6.2 F7-1` |
| PLN-F7-02 | command | `planned cli/helix-evolution` | `helix evolution <score|promote|deprecate> [--json]`。F7 public entry。 | `evolution CLI -> evolution.py` | planned | `→ UT-F7-001` | `→ L5 IF §5 A-23..A-25`; `→ L6 function §6.2 F7-1` |
| PLN-F7-03 | schema | `helix.db.plan_history` | plan mutation / promote / deprecate 履歴。compatibility: `status` で active/superseded/deprecated を保持。 | `evolution -> plan_history` | planned | `→ UT-F7-004` | `→ L5 physical §3.2`; `→ L6 function §6.2 F7-4/F7-5` |
| PLN-F7-04 | hook | `planned .claude/hooks/posttooluse-mutation-event.sh` | `PostToolUse + scheduler`。payload `{operation_type,target_plan_id,metadata,dry_run}`。audit 遅延時は fail-open。 | `Mutation hook -> plan_history / audit_link` | planned | `→ UT-F7-005` | `→ L5 IF §10.9`; `→ L6 function §6.2 F7-5` |
| PLN-F8-01 | class | `cli/lib/migration.py` | planned orchestration API。`prepare_version_bump()`, `apply_version_bump()`, `verify_compatibility_adr()` を持つ。 | `migration.py -> migrate.py / version_tag / compatibility_adapter` | planned | `→ UT-F8-001` | `→ L5 module §2.1 F8-1`; `→ L6 function §6.3 F8-1` |
| PLN-F8-02 | command | `planned cli/helix-version` | `helix version bump (--major|--minor) [--compatibility-adr <path>] [--json]`。breaking / non-breaking を分岐する。 | `version CLI -> migration.py` | planned | `→ UT-F8-001` | `→ L5 IF A-26..A-29`; `→ L6 function §6.3 F8-1/F8-2` |
| PLN-F8-03 | schema | `helix.db.version_tag` | version / migration / rollback manifest を保持。default `migration_status='planned'`。 | `migration/recovery -> version_tag` | planned | `→ UT-F8-002` | `→ L5 physical §3.3`; `→ L6 function §6.3 F8-2..F8-6` |
| PLN-F8-04 | schema | `helix.db.version_coevolution` | upstream/downstream version の共進化監査。 | `coexist/cutover -> version_coevolution` | planned | `→ UT-F8-003` | `→ L5 physical §3.6`; `→ L6 function §6.3 F8-3` |
| PLN-F8-05 | hook | `planned .claude/hooks/posttooluse-migration-event.sh` | payload `{operation_type,target_plan_id,metadata{from,to,compatibility_adr},duration_ms}`。migration integrity は fail-close。 | `Migration hook -> version_tag / event_log` | planned | `→ UT-F8-004` | `→ L5 IF §10.10`; `→ L6 function §6.3 F8-4/F8-5` |
| PLN-F9-01 | class | `cli/lib/apoptosis.py` | planned cleanup façade。`plan_cleanup()`, `approve_cleanup()`, `execute_cleanup()` を持つ。 | `apoptosis -> obsolete_record / rollback_orchestrator` | planned | `→ UT-F9-001` | `→ L5 module §2.1 F9-1`; `→ L6 function §6.4 F9-1` |
| PLN-F9-02 | command | `cli/helix-plan` / `cli/helix-db` | `helix plan apoptosis ...` と `helix db autophagy` を分離し、metadata archive と physical cleanup を別 command に保つ。 | `plan/db CLI -> apoptosis.py / recovery_plan_check` | planned | `→ UT-F9-001` | `→ L5 IF A-20,A-30,A-31`; `→ L6 function §6.4 F9-1..F9-3` |
| PLN-F9-03 | schema | `helix.db.obsolete_record` | obsolete artifact / approval / rollback manifest の監査 table。 | `apoptosis/autophagy -> obsolete_record` | planned | `→ UT-F9-003` | `→ L5 physical §3.4`; `→ L6 function §6.4 F9-2..F9-6` |
| PLN-F10-01 | class | `cli/lib/coexist.py` | planned coexist façade。`adopt_framework()`, `validate_boundary()`, `report_status()` を持つ。 | `coexist.py -> compatibility_adapter / merge_settings / cutover` | planned | `→ UT-F10-001` | `→ L5 module §2.1 F10-1`; `→ L6 function §6.5 F10-1` |
| PLN-F10-02 | command | `planned cli/helix-coexist` | `helix coexist <status|adopt|validate> [--compatibility-adr <path>] [--json]`。portable adopt と語彙を分離。 | `coexist CLI -> coexist.py` | planned | `→ UT-F10-001` | `→ L5 IF A-32..A-34`; `→ L6 function §6.5 F10-1` |
| PLN-F10-03 | schema | `helix.db.coexist_config` | namespace / ACL / boundary contract / schema JSON を保持。default `compatibility_level='low'`, `acl_enabled=1`。 | `coexist -> coexist_config` | planned | `→ UT-F10-003` | `→ L5 physical §3.5`; `→ L6 function §6.5 F10-2..F10-4` |
| PLN-F10-04 | hook | `planned .claude/hooks/posttooluse-coexist-event.sh` | payload `{operation_type,target_plan_id,metadata{framework,compatibility_mode},status}`。最終監査で収束するため fail-open。 | `Coexist hook -> coexist_config / event_log` | planned | `→ UT-F10-004` | `→ L5 IF §10.11`; `→ L6 function §6.5 F10-4..F10-6` |

### §5.1 境界 critical

#### migration

`migration.py` は version bump の意図決定を持ち、実ファイル merge は `migrate.py` が持つ。version orchestration と file merge を同じ module に混ぜると、dry-run と rollback 証跡が壊れるため禁止する。`Migration event hook` は integrity failure を fail-close とし、`version_tag` 書き込みより先に safety check を完了させる。

#### recovery

`recovery_engine.py`、`recovery_workflow_engine.py`、`rollback_orchestrator.py` は三層分離する。triage、state progression、rollback execute を別責務に固定し、active session の snapshot と destructive rollback を同一 entry で扱わない。失敗時は rollback path を 1 本に収束させ、partial apply の監査窓を閉じる。

#### apoptosis / coexist

`helix plan apoptosis` は metadata lifecycle、`helix db autophagy` は physical cleanup、`helix coexist` は boundary adoption を扱う。obsolete cleanup と coexist adoption の両方が `compatibility_adapter.write_connection()` を経由する設計にすることで、dual-write / shadow replay / rollback の対称性を保つ。

## §6 implementation_status 集計 + L7 carry

### §6.1 集計

| section | design items | implemented | partial | planned |
|---|---:|---:|---:|---:|
| §1 Python lib class/module | 21 | 19 | 2 | 0 |
| §2 bash CLI subcommand | 11 | 10 | 1 | 0 |
| §3 config/schema | 10 | 7 | 3 | 0 |
| §4 hook/agent contract | 8 | 8 | 0 | 0 |
| §5 F6-F10 planned contract | 20 | 1 | 1 | 18 |
| total | 70 | 45 | 7 | 18 |

### §6.2 L7 carry

| carry ID | 対象 | carry 内容 | 理由 |
|---|---|---|---|
| CARRY-L7-CMC-001 (resolved 2026-05-29) | pair freeze | L7 単体テスト設計 doc 作成済、`UT-Fx-NNN` 定義済で双方向 trace 解決。残る carry は fixture/テストコード実体化 (L7 Sprint Step 2) | pair doc 起票完了、テスト実装は L7 carry |
| CARRY-L7-CMC-002 | F2 | `plan_health.scan_all_plans()` を gate fail-close と接続 | health 集計はあるが gate 強制化未完 |
| CARRY-L7-CMC-003 | F4 | `workflow_dsl_parser.py` を 9 mode 全域 schema に拡張 | 現状は recovery/escalation 中心 |
| CARRY-L7-CMC-004 | F6 | `homeostasis.py` と `metrics_log` を `helix budget status --homeostasis` へ統合 | signal は分散し unified façade がない |
| CARRY-L7-CMC-005 | F7 | `helix evolution` と `plan_history` の mutation flow を本体化 | recipe 周辺の既存実装と governance 自動化が未結線 |
| CARRY-L7-CMC-006 | F8 | `helix version bump`、`version_tag`、`Migration event hook` を閉じる | migration orchestration は planned contract 止まり |
| CARRY-L7-CMC-007 | F9 | `apoptosis.py` と `obsolete_record` に approval/execute path を実装 | lifecycle archive と physical cleanup が未統合 |
| CARRY-L7-CMC-008 | F10 | `helix coexist`、`coexist_config`、`Coexist event hook` を実装 | boundary contract は定義済みだが public CLI 不在 |

### §6.3 freeze evidence (2026-05-29)

- L7 単体テスト pointer (`→ UT-F`): 72 件。
- §1-§5 各 section の設計項目数: `21 / 11 / 10 / 8 / 20`。
- L6↔L7 trace は §8 (L7 doc) の feature-level 表を正本とし、row 単位 `→ UT-Fx-NNN` は同一 feature 群内の代表 pointer。厳密 1:1 binding は L7 Sprint Step 2 (テスト実装時) で確定する。
4. 未確定 marker / 同一行繰り返し: `0` を目標とし、frontmatter と table row に一時語を残さない。
5. 深掘り prose 対象: `routing`, `plan parser`, `doctor/gate`, `DB write`, `migration`, `recovery`, `apoptosis/coexist`。
