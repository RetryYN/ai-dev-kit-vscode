# Whole-source coverage 単体テスト設計（UT-WSC-* / zero-omission B' Action4）

> L6 `whole-source-coverage-機能設計.md` の FN-WSC-* と 1:1 の単体テスト設計（DbC 反証観点）。
> 詳細な requires/ensures/invariant は対の L6 FN-WSC-* 行を正本とする（本表は反証観点 + テスト実装 status）。
> 「テスト実装」列: 実装済 = 既存 test が DbC をカバー / 未整備・部分 = carry `WSC-TEST-IMPL`（設計は完備、実装が L7 sprint）。
> L7 は実装工程の谷であり、単体テストコード実装・本体実装・単体テスト実施を含む。L8 は L5 に対応する結合テスト工程であり、本表の対象外。

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
| UT-WSC-10 | FN-WSC-10 | pretooluse-codex-slot-check.sh | hook の fail-close/fail-open 方向 + ensures(verdict/副作用) を反証 | 実装済 |
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
| UT-WSC-219 | FN-WSC-219 | g7_subcheck.py | anchored/exec_pass 集計の ensures + missing/unanchored 部分黙殺しない invariant を反証 | 実装済 |
| UT-WSC-220 | FN-WSC-220 | vg_overview.py | required_clean 集約 + ratchet detector の skip/clean 反映 + overall_clean 判定(1項目 false→false) の invariant を反証 | 実装済 |
| UT-WSC-221 | FN-WSC-221 | fn_ut_pair_coverage_checks.py | missing_test_design/unanchored_ut(RD-UT除外)/orphan_ut/duplicate 検出 + waiver 抑制を反証 | 実装済 |
| UT-WSC-222 | FN-WSC-222 | design_id_existence_checks.py | missing_design_section 検出 + 実 doc 出現要求 + waiver 抑制を反証 | 実装済 |
| UT-WSC-223 | FN-WSC-223 | l7_worklist.py | anchored/waived/separate_inventory(RD-UT)/missing_ut 分類 + read-only(fail-close しない)を反証 | 実装済 |
| UT-WSC-224 | FN-WSC-224 | changed_files.py | env override 優先 + git diff fallback + `available_empty`/`unavailable` 分離を反証 | 実装済 |
| UT-WSC-225 | FN-WSC-225 | coding_rule_lint.py | baseline 内違反 pass / changed-files 新規違反 fail / optional linter 不在時 graceful skip を反証 | 実装済 |
| UT-WSC-226 | FN-WSC-226 | dependency_cycle_checks.py | baseline 内循環 pass / changed-files 新規循環 fail / `available_empty`/`unavailable` 境界を反証 | 実装済 |
| UT-WSC-227 | FN-WSC-227 | plan_dependency_gate.py | baseline 内 warning pass / new cycle・missing reciprocal fail / `available_empty`/`unavailable` 境界を反証 | 実装済 |
| UT-WSC-228 | FN-WSC-228 | fr_uses_checks.py | missing target fail-close / reverse reference warning-only / `available_empty`/`unavailable` 境界を反証 | 実装済 |
| UT-WSC-229 | FN-WSC-229 | anchor_quality.py | non-trivial assert / `pytest.raises` / Bats assertion だけを genuine anchor とし、trivial/skip/marker-only/run-only を weak 判定する invariant を反証 | 実装済 |
| UT-WSC-230 | FN-WSC-230 | g8_subcheck.py | IT inventory 限定集計 + markerless/needleless anchor reject + skip-exec 時 `anchored==exec_pass` の invariant を反証 | 実装済 |
| UT-WSC-231 | FN-WSC-231 | g9_subcheck.py | ST inventory 18 件のうち genuine 5 件だけを count し、markerless anchor を `unanchored_but_exists`、deferred gap を `missing/gap_count` に残す invariant を反証 | 実装済 |
| UT-WSC-232 | FN-WSC-232 | g12_subcheck.py | AT inventory 57 件のうち genuine 5 件だけを count し、markerless anchor を `unanchored_but_exists`、deferred gap を `missing/gap_count` に残す invariant を反証 | 実装済 |
| UT-WSC-233 | FN-WSC-233 | g14_subcheck.py | OT inventory 20 件のうち genuine 1 件だけを count し、markerless anchor を `unanchored_but_exists`、deferred gap を `missing/gap_count` に残す invariant を反証 | 実装済 |
| UT-WSC-234 | FN-WSC-234 | review_evidence_checks.py | clean payload no-findings / 必須 field 欠落 / reviewer=worker / review-before-tests / output tamper を正しく分岐し、`review_evidence` 不在を not-applicable に留める invariant を反証 | 実装済 |

## carry: WSC-TEST-IMPL（2026-06-07 closure、残 0 件）

> **設計の抜け漏れではない**。FN-WSC/UT-WSC 59 の設計は完備（trace_symmetry L6↔L7 green）。`WSC-TEST-IMPL` は verify-first で閉塞し、既存充足 1 件と新規/補助テスト 11 件へ実体是正した。

| 区分 | FN-WSC | 件数 |
|---|---|---|
| verify-first 既存充足 | 10 | 1 |
| 今回新規/補助テスト実装 | 02, 03, 04, 05, 06, 12, 13, 15, 17, 213(uuid7_generator), 218(zizmor_ignore_lint) | 11 |
| DF-G7-MISSING-001 closure | 07, 08, 10, 11 | 4 |
| **残 carry** | — | **0** |

## 合格基準（G7 単体）

- UT-WSC-* が FN-WSC-* と 1:1（trace_symmetry L6↔L7 balance≥1.0 / coverage100% / orphan0 / missing0）。
- 実装済 42 件は既存 pytest/bats green を維持。
- `WSC-TEST-IMPL` carry は closure 済（残 0 件、L1 verification-strategy §13 と件数一致）。
