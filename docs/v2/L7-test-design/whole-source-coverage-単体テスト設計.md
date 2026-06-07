# Whole-source coverage 単体テスト設計（UT-WSC-* / zero-omission B' Action4）

> L6 `whole-source-coverage-機能設計.md` の FN-WSC-* と 1:1 の単体テスト設計（DbC 反証観点）。
> 詳細な requires/ensures/invariant は対の L6 FN-WSC-* 行を正本とする（本表は反証観点 + テスト実装 status）。
> 「テスト実装」列: 実装済 = 既存 test が DbC をカバー / 未整備・部分 = carry `WSC-TEST-IMPL`（設計は完備、実装が L7 sprint）。

| UT ID | 対象 FN | module | 検証観点（DbC 反証） | テスト実装 |
|---|---|---|---|---|
| UT-WSC-01 | FN-WSC-01 | post-tool-use.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 |
| UT-WSC-02 | FN-WSC-02 | posttooluse-design-doc-web-search-revert.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 |
| UT-WSC-03 | FN-WSC-03 | posttooluse-helix-job-enqueue.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 |
| UT-WSC-04 | FN-WSC-04 | posttooluse-plan-auto-register.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 |
| UT-WSC-05 | FN-WSC-05 | posttooluse-skill-catalog-rebuild.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 |
| UT-WSC-06 | FN-WSC-06 | precompact-state-snapshot.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 |
| UT-WSC-07 | FN-WSC-07 | pretooluse-agent-fire.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 |
| UT-WSC-08 | FN-WSC-08 | pretooluse-agent-guard.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 |
| UT-WSC-09 | FN-WSC-09 | pretooluse-askuserquestion.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 |
| UT-WSC-10 | FN-WSC-10 | pretooluse-codex-slot-check.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 (verify-first: 既存充足) |
| UT-WSC-11 | FN-WSC-11 | pretooluse-design-doc-web-search-guard.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 |
| UT-WSC-12 | FN-WSC-12 | pretooluse-opus-repo-block.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 |
| UT-WSC-13 | FN-WSC-13 | sessionstart-harness-summary.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 |
| UT-WSC-14 | FN-WSC-14 | sessionstart-history-injection.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 |
| UT-WSC-15 | FN-WSC-15 | stop-recovery-update.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 |
| UT-WSC-16 | FN-WSC-16 | stop.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 |
| UT-WSC-17 | FN-WSC-17 | userpromptsubmit-context-bundle.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 |
| UT-WSC-101 | FN-WSC-101 | allowed_files_estimator.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-102 | FN-WSC-102 | code_recommender.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-103 | FN-WSC-103 | codex_post_validation.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-104 | FN-WSC-104 | demotion_checker.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-105 | FN-WSC-105 | doc_map_matcher.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-106 | FN-WSC-106 | doctor_plan_checks.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-107 | FN-WSC-107 | doctor_recovery_check.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-108 | FN-WSC-108 | drift_db_diff.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-109 | FN-WSC-109 | dual_write_connection.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-110 | FN-WSC-110 | dual_write_mismatch.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-111 | FN-WSC-111 | effort_classifier.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-112 | FN-WSC-112 | freeze_checker.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-113 | FN-WSC-113 | gate_check_generator.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-114 | FN-WSC-114 | global_store.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-115 | FN-WSC-115 | job_p0_guard.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-116 | FN-WSC-116 | llm_classifier_base.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-117 | FN-WSC-117 | phase_guard.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-118 | FN-WSC-118 | plan_lint.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-119 | FN-WSC-119 | plan_parser.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-201 | FN-WSC-201 | push_gate.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-202 | FN-WSC-202 | recovery_plan_check.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-203 | FN-WSC-203 | research_guard.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-204 | FN-WSC-204 | research_tool_guard.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-205 | FN-WSC-205 | skill_classifier.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-206 | FN-WSC-206 | skill_frontmatter_lint.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-207 | FN-WSC-207 | skill_recommender.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-208 | FN-WSC-208 | skip_annotation_linter.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-209 | FN-WSC-209 | sprint_auto_check.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-210 | FN-WSC-210 | sprint_lint.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-211 | FN-WSC-211 | task_type_inference.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-212 | FN-WSC-212 | trace_symmetry.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-213 | FN-WSC-213 | uuid7_generator.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 (補助1ケース追加) |
| UT-WSC-214 | FN-WSC-214 | vmodel_lint.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-215 | FN-WSC-215 | vmodel_pair_freeze.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-216 | FN-WSC-216 | workflow_dsl_parser.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-217 | FN-WSC-217 | yaml_parser.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |
| UT-WSC-218 | FN-WSC-218 | zizmor_ignore_lint.py | 主関数の invariant(エラー時/fail-close) + ensures(戻り値/出力) を反証 | 実装済 |

## carry: WSC-TEST-IMPL（2026-06-07 closure、残 0 件）

> **設計の抜け漏れではない**。FN-WSC/UT-WSC 54 の設計は完備（trace_symmetry L6↔L7 green）。`WSC-TEST-IMPL` は verify-first で閉塞し、既存充足 1 件と新規/補助テスト 11 件へ実体是正した。

| 区分 | FN-WSC | 件数 |
|---|---|---|
| verify-first 既存充足 | 10 | 1 |
| 今回新規/補助テスト実装 | 02, 03, 04, 05, 06, 12, 13, 15, 17, 213(uuid7_generator), 218(zizmor_ignore_lint) | 11 |
| **残 carry** | — | **0** |

## 合格基準（G7 単体）

- UT-WSC-* が FN-WSC-* と 1:1（trace_symmetry L6↔L7 balance≥1.0 / coverage100% / orphan0 / missing0）。
- 実装済 42 件は既存 pytest/bats green を維持。
- `WSC-TEST-IMPL` carry は closure 済（残 0 件、L1 verification-strategy §13 と件数一致）。
