# Whole-source coverage 単体テスト設計（UT-WSC-* / zero-omission B' Action4）

> L6 `whole-source-coverage-機能設計.md` の FN-WSC-* と 1:1 の単体テスト設計。
> 「既存テスト」列 = 実装済テストファイル（Reverse 由来で多くが実装済）。`なし/未確認` は UT 設計は完備だがテスト実装が carry。

| UT ID | 対象 FN | module | 検証観点（DbC 反証） | 既存テスト実装 |
|---|---|---|---|---|
| UT-WSC-01 | FN-WSC-01 | post-tool-use.sh | invariant/fail-close 方向を反証 |  |
| UT-WSC-02 | FN-WSC-02 | posttooluse-design-doc-web-search-revert.sh | invariant/fail-close 方向を反証 | あり (test_design_doc_web_search_guard.bats、test_helix_gate_design_doc_fail_close.py が pre-side をカバー。revert side は test_security_hardening.py で一部カバー) |
| UT-WSC-03 | FN-WSC-03 | posttooluse-helix-job-enqueue.sh | invariant/fail-close 方向を反証 |  |
| UT-WSC-04 | FN-WSC-04 | posttooluse-plan-auto-register.sh | invariant/fail-close 方向を反証 | あり (test_plan_parser.py が parser/upsert をカバー、test_plan_registry.py が registry をカバー。hook script の E2E は未確認) |
| UT-WSC-05 | FN-WSC-05 | posttooluse-skill-catalog-rebuild.sh | invariant/fail-close 方向を反証 |  |
| UT-WSC-06 | FN-WSC-06 | precompact-state-snapshot.sh | invariant/fail-close 方向を反証 | 未確認（test_security_hardening.py で断片カバーの可能性のみ、専用テストなし） |
| UT-WSC-07 | FN-WSC-07 | pretooluse-agent-fire.sh | invariant/fail-close 方向を反証 |  |
| UT-WSC-08 | FN-WSC-08 | pretooluse-agent-guard.sh | invariant/fail-close 方向を反証 | あり (tests/helix-agent-mandatory.bats / tests/helix-agent.bats が E2E カバー) |
| UT-WSC-09 | FN-WSC-09 | pretooluse-askuserquestion.sh | invariant/fail-close 方向を反証 | あり (test_pretooluse_askuserquestion.py が Python ロジックをカバー) |
| UT-WSC-10 | FN-WSC-10 | pretooluse-codex-slot-check.sh | invariant/fail-close 方向を反証 |  |
| UT-WSC-11 | FN-WSC-11 | pretooluse-design-doc-web-search-guard.sh | invariant/fail-close 方向を反証 | あり (tests/test_design_doc_web_search_guard.bats が E2E カバー、test_helix_gate_design_doc_fail_close.py が Python ロジックカバー) |
| UT-WSC-12 | FN-WSC-12 | pretooluse-opus-repo-block.sh | invariant/fail-close 方向を反証 | あり (tests/harness-hooks.bats で一部カバー、test_merge_settings.py / test_context_guard.py で設定側カバー) |
| UT-WSC-13 | FN-WSC-13 | sessionstart-harness-summary.sh | invariant/fail-close 方向を反証 |  |
| UT-WSC-14 | FN-WSC-14 | sessionstart-history-injection.sh | invariant/fail-close 方向を反証 | あり (test_session_start_helpers.py が extract_next_action 等の Python ロジックをカバー) |
| UT-WSC-15 | FN-WSC-15 | stop-recovery-update.sh | invariant/fail-close 方向を反証 | あり (test_helix_recovery.py が snapshot_on_stop をカバー) |
| UT-WSC-16 | FN-WSC-16 | stop.sh | invariant/fail-close 方向を反証 |  |
| UT-WSC-17 | FN-WSC-17 | userpromptsubmit-context-bundle.sh | invariant/fail-close 方向を反証 | 部分あり (test_session_start_helpers.py が関連 helper をカバー、hook script 直接テストなし) |
| UT-WSC-101 | FN-WSC-101 | allowed_files_estimator.py | invariant(エラー時/fail-close) + ensures を反証 | あり (`test_allowed_files_estimator.py`) |
| UT-WSC-102 | FN-WSC-102 | code_recommender.py | invariant(エラー時/fail-close) + ensures を反証 | あり (`test_code_recommender.py`) |
| UT-WSC-103 | FN-WSC-103 | codex_post_validation.py | invariant(エラー時/fail-close) + ensures を反証 | あり (`test_codex_post_validation.py`) |
| UT-WSC-104 | FN-WSC-104 | demotion_checker.py | invariant(エラー時/fail-close) + ensures を反証 | あり (`test_demotion_checker.py`) |
| UT-WSC-105 | FN-WSC-105 | doc_map_matcher.py | invariant(エラー時/fail-close) + ensures を反証 | …`/`COVERAGE_CHECK\ |
| UT-WSC-106 | FN-WSC-106 | doctor_plan_checks.py | invariant(エラー時/fail-close) + ensures を反証 | あり (`test_doctor_plan_checks.py`) |
| UT-WSC-107 | FN-WSC-107 | doctor_recovery_check.py | invariant(エラー時/fail-close) + ensures を反証 | あり (`test_doctor_recovery_check.py`) |
| UT-WSC-108 | FN-WSC-108 | drift_db_diff.py | invariant(エラー時/fail-close) + ensures を反証 | warn` + `WARN\ |
| UT-WSC-109 | FN-WSC-109 | dual_write_connection.py | invariant(エラー時/fail-close) + ensures を反証 | あり (`test_dual_write_connection_unit.py`) |
| UT-WSC-110 | FN-WSC-110 | dual_write_mismatch.py | invariant(エラー時/fail-close) + ensures を反証 | あり (`test_dual_write_mismatch_unit.py`) |
| UT-WSC-111 | FN-WSC-111 | effort_classifier.py | invariant(エラー時/fail-close) + ensures を反証 | あり (`test_effort_classifier.py`) |
| UT-WSC-112 | FN-WSC-112 | freeze_checker.py | invariant(エラー時/fail-close) + ensures を反証 | あり (`test_freeze_checker.py`) |
| UT-WSC-113 | FN-WSC-113 | gate_check_generator.py | invariant(エラー時/fail-close) + ensures を反証 | あり (`test_gate_check_generator.py`) |
| UT-WSC-114 | FN-WSC-114 | global_store.py | invariant(エラー時/fail-close) + ensures を反証 | あり (`test_global_store.py`) |
| UT-WSC-115 | FN-WSC-115 | job_p0_guard.py | invariant(エラー時/fail-close) + ensures を反証 | あり (`test_job_p0_guard.py`) |
| UT-WSC-116 | FN-WSC-116 | llm_classifier_base.py | invariant(エラー時/fail-close) + ensures を反証 | あり (`test_llm_classifier_base.py`) |
| UT-WSC-117 | FN-WSC-117 | phase_guard.py | invariant(エラー時/fail-close) + ensures を反証 | あり (`test_phase_guard.py`) |
| UT-WSC-118 | FN-WSC-118 | plan_lint.py | invariant(エラー時/fail-close) + ensures を反証 | あり (`test_plan_lint.py`) |
| UT-WSC-119 | FN-WSC-119 | plan_parser.py | invariant(エラー時/fail-close) + ensures を反証 | ファイル読み込み OSError→ `None` + `_warn()`; frontmatter ブロック不在→ `None` + `_warn()`; YAML 不正→ `None` + `_warn()`; required fields 欠落→ `loaded["_warnings"]` に追記した dict を返す（None にしない）; `upsert_plan` の SQLite エラーは `_warn()` のみで exit 0 |
| UT-WSC-201 | FN-WSC-201 | push_gate | invariant(エラー時/fail-close) + ensures を反証 | あり (test_push_gate.py) |
| UT-WSC-202 | FN-WSC-202 | recovery_plan_check | invariant(エラー時/fail-close) + ensures を反証 | あり (test_recovery_plan_check.py) |
| UT-WSC-203 | FN-WSC-203 | research_guard | invariant(エラー時/fail-close) + ensures を反証 | あり (test_research_guard.py) |
| UT-WSC-204 | FN-WSC-204 | research_tool_guard | invariant(エラー時/fail-close) + ensures を反証 | あり (test_research_tool_guard.py) |
| UT-WSC-205 | FN-WSC-205 | skill_classifier | invariant(エラー時/fail-close) + ensures を反証 | あり (test_skill_classifier.py) |
| UT-WSC-206 | FN-WSC-206 | skill_frontmatter_lint | invariant(エラー時/fail-close) + ensures を反証 | あり (test_skill_frontmatter_lint.py) |
| UT-WSC-207 | FN-WSC-207 | skill_recommender | invariant(エラー時/fail-close) + ensures を反証 | `task_text` が空なら `RecommenderError(2)` を raise。`candidates` は `top_n` 件以下。各 candidate の `score ∈ [0.0, 1.0]`。キャッシュ TTL 超過エントリは GC する。 |
| UT-WSC-208 | FN-WSC-208 | skip_annotation_linter | invariant(エラー時/fail-close) + ensures を反証 | あり (test_skip_annotation_linter.py) |
| UT-WSC-209 | FN-WSC-209 | sprint_auto_check | invariant(エラー時/fail-close) + ensures を反証 | あり (test_sprint_auto_check.py) |
| UT-WSC-210 | FN-WSC-210 | sprint_lint | invariant(エラー時/fail-close) + ensures を反証 | "fail", "target_files", "relevant_test_selector"}` を返す。 |
| UT-WSC-211 | FN-WSC-211 | task_type_inference | invariant(エラー時/fail-close) + ensures を反証 | あり (test_task_type_inference.py) |
| UT-WSC-212 | FN-WSC-212 | trace_symmetry | invariant(エラー時/fail-close) + ensures を反証 | あり (test_trace_symmetry.py) |
| UT-WSC-213 | FN-WSC-213 | uuid7_generator | invariant(エラー時/fail-close) + ensures を反証 | なし |
| UT-WSC-214 | FN-WSC-214 | vmodel_lint | invariant(エラー時/fail-close) + ensures を反証 | あり (test_vmodel_lint.py) |
| UT-WSC-215 | FN-WSC-215 | vmodel_pair_freeze | invariant(エラー時/fail-close) + ensures を反証 | "no_pair", ...}` を返す。 |
| UT-WSC-216 | FN-WSC-216 | workflow_dsl_parser | invariant(エラー時/fail-close) + ensures を反証 | あり (test_workflow_dsl_parser.py) |
| UT-WSC-217 | FN-WSC-217 | yaml_parser | invariant(エラー時/fail-close) + ensures を反証 | あり (test_yaml_parser.py) |
| UT-WSC-218 | FN-WSC-218 | zizmor_ignore_lint | invariant(エラー時/fail-close) + ensures を反証 | なし |

## 合格基準（G7 単体）

- UT-WSC-* が FN-WSC-* と 1:1（trace_symmetry L6↔L7 green）。
- 既存テスト実装済の FN は pytest/bats green を維持。
- テスト実装 carry（hooks E2E 6件 + uuid7_generator/zizmor_ignore_lint 等）は別 L7 sprint で実装（設計は本書で完備、抜け漏れではない）。
