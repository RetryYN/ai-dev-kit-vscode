# FR-INV13: テスト coverage / 品質監査

最終更新: 2026-05-14  
監査者: Research (Codex)  
不確実性: `pyramid` 比率と一部の `状態` 判定は、ファイル名・配置・代表サンプル読解からの推定を含む。特に `unit / integration / E2E` の境界は実装側で厳密ラベル管理されていないため、ここでは監査用の近似値として扱う。

## 1. 概要

Verify 層は量としては十分に大きく、`cli/tests` の Bats、`cli/lib/tests` の pytest、`verify/*.sh` の長経路検証、`helix gate` と 14 axis detector による fail-close 入口が揃っている。  
一方で、coverage は `overall 7.9%` と薄く、手厚いのは `core5 86.4%` に限られる。V2 Phase 4 の guardrail 入力としては、「core5 を守りつつ、advanced / automation layer / hook / plan command 群へ coverage を拡張する」方針が妥当。

特に強いのは以下。

- detector 14 軸に対する pytest が一通り存在する
- `PLAN-051` 起点で bats-lite hidden failure 対策が自己テスト化されている
- `verify/h401-full-flow-integration.sh` まで含めた end-to-end 経路が残っている
- GitHub Actions CI が `helix-test`、Bats、`helix-verify-all`、pytest をすべて起動する

弱いのは以下。

- overall uncovered が大きく、`cli/helix-plan-cmds/*`、hook、automation 補助関数の直接 coverage が薄い
- fixture / mock 主体で、実 DB・実 Git・実 hook を跨ぐ統合ケースは限定的
- capability inventory 上の V-model schema、contract auto-record、automation layer 連動に対する検証は部分実装
- 手動 shell check が 2 本残っており、CI 線に乗らない hidden knowledge がある

## 2. 監査方法とソース

### 直接集計

- `./cli/helix code stats --uncovered`  
  注記: 環境で `HOME` 未設定だったため `HOME=/home/tenni ./cli/helix ...` で代替実行
- `find cli/tests cli/lib/tests verify -type f`
- Python 集計で `@test` / `def test_` / `wc -l` を算出
- `.github/workflows/ci.yml`

### 確認した代表実装

- `cli/tests/test-bats-lite-runner.bats`
- `cli/tests/helix-gate-detector.bats`
- `cli/tests/test-helix-readiness-e2e.bats`
- `cli/lib/tests/test_gate_detector_integration.py`
- `cli/lib/tests/test_design_review_pair_check.py`
- `cli/lib/tests/test_axis_11_regression.py`
- `cli/lib/tests/test_verify_agent.py`
- `verify/h401-full-flow-integration.sh`
- `docs/v2/A-audit/capability-inventory.md`
- `docs/plans/PLAN-051-bats-lite-and-hidden-failures.md`

### 工程表 / handover

- `.helix/handover/CURRENT.json`: なし
- `.helix/task-plan.yaml`: あり。ただし `PLAN-013` 完了済みで、今回の `FR-INV13` を直接拘束する行はなし

## 3. 全体サマリ

| 指標 | 値 |
|---|---:|
| 総 test group file 数 | 221 |
| 総 test case 数 | 1504 |
| 総行数 | 34340 |
| Bats | 67 files / 439 cases / 8920 lines |
| manual shell | 2 files / 2 cases / 259 lines |
| pytest | 120 files / 1031 cases / 23741 lines |
| verify | 32 files / 32 cases / 1420 lines |
| overall coverage | 51 / 642 = 7.9% |
| core5 coverage | 51 / 59 = 86.4% |

## 4. coverage

### 4.1 overall / core5

- overall uncovered: `covered=51`, `eligible=642`, `coverage=7.9%`
- core5 uncovered: `covered=51`, `eligible=59`, `coverage=86.4%`

解釈:

- core5 はかなり守られている
- ただし advanced / support layer を含む全体では coverage が急落する
- したがって V2 では「core5 gate は維持」「advanced 層は detector / hook / automation を軸に優先拡張」が現実的

### 4.2 uncovered top-10

`helix code stats --uncovered` の先頭 10 件:

1. `.claude/hooks/post-tool-use.sh:10` `record_invocation_telemetry`
2. `.claude/hooks/pretooluse-opus-repo-block.sh:11` `read_json_field`
3. `.claude/hooks/stop.sh:10` `record_invocation_telemetry`
4. `cli/helix-plan-cmds/_shared.sh:9` `ensure_dirs`
5. `cli/helix-plan-cmds/_shared.sh:13` `validate_plan_id`
6. `cli/helix-plan-cmds/_shared.sh:21` `validate_mini_plan_id`
7. `cli/helix-plan-cmds/_shared.sh:29` `validate_parent_plan_id`
8. `cli/helix-plan-cmds/_shared.sh:37` `plan_file_path`
9. `cli/helix-plan-cmds/_shared.sh:42` `ensure_plan_exists`
10. `cli/helix-plan-cmds/_shared.sh:52` `yaml_read`

所見:

- uncovered の先頭は plan command 共通部と Claude hook 系に偏る
- ここは detector よりも「薄い shell contract test」を増やす方が費用対効果が高い

### 4.3 core5 uncovered 先頭

`core5` では `cli/lib/code_catalog.py` の内部 helper が主な未網羅。

- `_strip_quotes`
- `_parse_key_values`
- `_source_hash`
- `_parse_marker_payload`
- `_comment_lines`
- `_comment_marker_lines`
- `_is_index_marker_valid`
- `_project_root_for`
- `_is_non_indexable_path`
- `_is_excluded_path`

所見:

- core5 の不足は外側 API ではなく parser/helper 層に集中
- したがって V2 では property-style unit test を足せば短期で 90% 台に届く可能性が高い

## 5. test pyramid

注記: 厳密ラベルがないため、以下で近似分類した。

- `unit`: ほとんどの pytest
- `integration`: Bats、manual shell、pytest 内の `integration/e2e/handover/verify_agent/gate_detector` 系
- `E2E`: `verify/*.sh` と `readiness-e2e` などの長経路ケース

### 推定件数

| 層 | 件数 | 比率 |
|---|---:|---:|
| unit | 974 | 64.8% |
| integration | 494 | 32.8% |
| E2E | 36 | 2.4% |

### 評価

- 形としては unit 優勢で、pyramid 自体は大きく崩れていない
- ただし integration がかなり厚く、shell/Bats 側に仕様知識が寄っている
- E2E は最低限あるが、本番 guardrail としては「Phase 4 運用経路」「drive × layer semantic」「sprint pair-check」の追加余地が大きい

## 6. test グループ一覧

| path | 件数 | 行数 | 対応 capability | coverage 寄与 | 状態 | V2 変更計画 | V2 Phase 紐付け |
|---|---:|---:|---|---|---|---|---|
| `cli/tests/test-bats-lite-runner.bats` | 7 | 46 | bats-lite runner、`PLAN-051` hidden failure 対策、skip/errexit | advanced | 健全 | as-is | Phase 4 |
| `cli/tests/helix-budget-*.bats` | 14 | 246 | budget guard、status/forecast migration | advanced | 健全 | modify | Phase 5 |
| `cli/tests/test-helix-plan*.bats` | 40 | 912 | plan draft/finalize/lint/mini/reset | advanced | coverage 薄い本体あり | extend | Phase 2 |
| `cli/tests/helix-gate-*.bats`, `cli/tests/test-helix-gate-*.bats` | 33 | 895 | G2/G4/G6/G9/G10/G11、detector auto-run、pair-check | detector | 健全 | extend | Phase 4 |
| `cli/tests/test-helix-readiness*.bats` | 9 | 443 | readiness exit、deferred finding、gate enforce | detector | 健全 | extend | Phase 4 |
| `cli/tests/test-handover.bats` | 37 | 446 | handover protocol、resume/update/status | advanced | 健全 | as-is | Phase 1, Phase 5 |
| `cli/tests/test-helix-audit*.bats` | 9 | 182 | audit A0/A1 preflight | advanced | 健全 | modify | Phase 1 |
| `cli/tests/test-helix-code.bats`, `cli/tests/test-helix-entry.bats` | 57 | 941 | code-index、entry/link inventory | core5 | 健全 | as-is | Phase 1, Phase 3 |
| `cli/tests/test-helix-codex*.bats`, `test_codex_role_intent.bats`, `test-codex-review-prompt.bats` | 37 | 676 | `helix codex` harness、allowed-files、footer discipline | advanced | 健全 | extend | Phase 5 |
| `cli/tests/test-helix-claude-pmo.bats`, `test-helix-doctor-pmo.bats` | 6 | 155 | PMO / Claude harness | advanced | 健全 | modify | Phase 5 |
| `cli/tests/test-helix-reverse-*.bats` | 25 | 339 | Reverse HELIX | advanced | 健全 | as-is | Phase 2 |
| `cli/tests/test-helix-scrum*.bats` | 13 | 327 | Scrum HELIX、trigger persistence | advanced | 健全 | as-is | Phase 2 |
| `cli/tests/test-helix-setup.bats`, `test-helix-asset.bats`, `test-helix-size-agent.bats`, `helix-size-drive-auto.bats` | 31 | 421 | setup、asset、size/drive classification | advanced | 健全 | modify | Phase 1 |
| `cli/tests/test-helix-routing.bats`, `test-helix-meta-phase.bats`, `test-helix-dashboard.bats`, `test-helix-phase-*.bats` | 29 | 620 | routing、meta-phase、dashboard、deploy phase | advanced | 健全 | extend | Phase 4, Phase 5 |
| `cli/tests/test-helix-lock.bats`, `test-helix-job.bats`, `test-helix-observe.bats`, `test-helix-scheduler.bats`, `test-helix-interrupt-history.bats` | 14 | 327 | job/scheduler/observe/interrupt | advanced | 健全 | modify | Phase 5 |
| `cli/tests/test-pretooluse-opus-repo-block.bats`, `test-retro-auto-enqueue.bats`, `test-helix-review-internal-skip.bats`, `test-helix-flexibility.bats`, `test-helix-skill.bats`, `test-helix-session-summary.bats`, `test-helix-sprint-strict.bats`, `test_helix_gate_g5_design_md.bats` | 34 | 878 | governance、review skip、skill dispatch、G5 | advanced | 混在。守備範囲が広く回帰の温床 | split/extend | Phase 4, Phase 5 |
| `cli/tests/*manual.sh` | 2 | 259 | drift-check / auto-enqueue の手動確認 | advanced | outdated | deprecate | Phase 4 |
| `cli/lib/tests/test_audit_*.py` | 42 | 752 | A1 import/hash/validator/inventory | advanced | 健全 | extend | Phase 1 |
| `cli/lib/tests/test_axis_01_dead.py` | 1 | 76 | detector axis-01 dead code drift | detector | 薄いが存在 | extend | Phase 4 |
| `cli/lib/tests/test_axis_02_coverage.py` | 2 | 121 | detector axis-02 coverage erosion | detector | 薄いが存在 | extend | Phase 4 |
| `cli/lib/tests/test_axis_03_dup.py` | 1 | 72 | detector axis-03 duplicate | detector | 薄いが存在 | extend | Phase 4 |
| `cli/lib/tests/test_axis_04_skill_decay.py` | 1 | 95 | detector axis-04 skill decay | detector | 薄いが存在 | extend | Phase 4 |
| `cli/lib/tests/test_axis_05_plan_debt.py` | 2 | 161 | detector axis-05 plan debt loop | detector | 薄いが存在 | extend | Phase 4 |
| `cli/lib/tests/test_axis_06_naming.py` | 1 | 87 | detector axis-06 naming confusion | detector | 薄いが存在 | extend | Phase 4 |
| `cli/lib/tests/test_axis_07_doc_drift.py` | 1 | 84 | detector axis-07 doc drift | detector | 薄いが存在 | extend | Phase 4 |
| `cli/lib/tests/test_axis_08_plan_integrity.py` | 2 | 65 | detector axis-08 plan integrity | detector | 薄いが存在 | extend | Phase 4 |
| `cli/lib/tests/test_axis_09_refactor.py` | 1 | 102 | detector axis-09 refactor opportunity | detector | 薄いが存在 | extend | Phase 4 |
| `cli/lib/tests/test_axis_10_relation_graph.py` | 1 | 166 | detector axis-10 relation graph | detector | 薄いが存在 | extend | Phase 4 |
| `cli/lib/tests/test_axis_11_regression.py` | 3 | 222 | detector axis-11 regression、flaky 判定 | detector | 健全 | extend | Phase 4 |
| `cli/lib/tests/test_axis_12_connection.py` | 1 | 87 | detector axis-12 connection deficiency | detector | 薄いが存在 | extend | Phase 4 |
| `cli/lib/tests/test_axis_13_model_skill.py` | 1 | 199 | detector axis-13 model-skill analytics | detector | 薄いが存在 | extend | Phase 4 |
| `cli/lib/tests/test_axis_14_orchestration.py` | 5 | 296 | detector axis-14 orchestration integrity | detector | 比較的健全 | as-is | Phase 4, Phase 5 |
| `cli/lib/tests/test_gate_detector_integration.py`, `test_deliverable_gate*.py`, `test_design_review_pair_check.py`, `test_gate_policy_helper.py`, `test_gate_check_generator.py` | 41 | 916 | gate × detector 接続、deliverable gate、pair-check | detector | 健全 | extend | Phase 4 |
| `cli/lib/tests/test_handover.py`, `test_helix_db*.py`, `test_session_start_helpers.py` | 90 | 2517 | handover DB、runtime schema、resume logic | core5 | 健全 | as-is | Phase 1, Phase 5 |
| `cli/lib/tests/test_agent_policy_guard.py`, `test_context_guard.py`, `test_codex_post_*.py`, `test_hook_*.py`, `test_llm_guard.py`, `test_security_hardening.py`, `test_research_guard.py`, `test_research_tool_guard.py` | 162 | 2342 | hook / guard / security / research gate | advanced | 健全。ただし hook 本体未網羅あり | extend | Phase 4, Phase 5 |
| `cli/lib/tests/test_code_*.py`, `test_build_jsonl_catalog.py`, `test_bash_trace.py` | 72 | 1342 | code catalog、code edges、recommender | core5 | 健全 | as-is | Phase 1, Phase 3 |
| `cli/lib/tests/test_skill_*.py` | 92 | 2697 | skill catalog / recommender / dispatcher / review | advanced | 健全 | modify | Phase 5 |
| `cli/lib/tests/test_builders*.py`, `test_matrix_*.py`, `test_meta_phase*.py` | 83 | 1647 | builder、matrix compile、meta-phase | advanced | 健全 | extend | Phase 2, Phase 5 |
| `cli/lib/tests/test_budget*.py`, `test_model_fallback.py`, `test_effort_classifier.py`, `test_role_config_consistency.py` | 30 | 768 | model / budget / effort routing | advanced | 健全 | modify | Phase 1, Phase 5 |
| `cli/lib/tests/test_scheduler_helper.py`, `test_job_queue_helper.py`, `test_lock_*.py`, `test_concurrent_lock.py`, `test_stale_lock_cleanup.py` | 52 | 1356 | scheduler / job / lock / stale cleanup | advanced | 健全 | as-is | Phase 5 |
| `cli/lib/tests/test_plan_*.py`, `test_task_*.py`, `test_command_*.py`, `test_cli_regressions.py`, `test_defaults_loader.py`, `test_init_helpers.py`, `test_invocation_*.py`, `test_merge_settings.py`, `test_migrate.py`, `test_legacy_plan_migration.py`, `test_phase_guard.py` | 102 | 2077 | plan/task/command/runtime migration | advanced | 健全だが uncovered 上位とズレあり | extend | Phase 1, Phase 2 |
| `cli/lib/tests/test_verify_agent.py`, `test_contract_registry.py`, `test_drift_db_diff.py`, `test_doc_map_matcher.py` | 29 | 714 | verify-agent、contract registry、drift DB | advanced | 部分機能 | extend | Phase 3, Phase 4 |
| `cli/lib/tests/test_entries_links.py`, `test_learning_*.py`, `test_global_store.py`, `test_feedback_hook.py`, `test_observability_skill.py`, `test_helix_debt.py` | 74 | 1540 | entries/links、learning、feedback、debt | advanced | 健全 | modify | Phase 5 |
| `cli/lib/tests/test_helix_claude_execute.py`, `test_helix_common_sh.py`, `test_helix_doctor*.py`, `test_yaml_parser.py`, `test_scrum_trigger.py`, `test_setup_skill.py`, `test_team_runner.py` | 61 | 1572 | misc runtime、doctor、yaml、team runner | advanced | 混在。責務が広い | split/extend | Phase 5 |
| `verify/001-010*.sh` | 10 | 465 | smoke verify、基本 CLI flow | advanced | 健全 | as-is | Phase 4 |
| `verify/h101-h105*.sh` | 5 | 198 | forward flow、freeze recovery、status | E2E | 健全 | extend | Phase 4 |
| `verify/h201-h206*.sh` | 6 | 266 | codex/claude harness、gate cascade、安全性 | E2E | 健全 | extend | Phase 5 |
| `verify/h301-h310*.sh` | 10 | 352 | skill validation、hook trigger、reverse/scrum edge | E2E | 健全 | extend | Phase 4, Phase 5 |
| `verify/h401-full-flow-integration.sh` | 1 | 139 | init→scrum→gate→sprint→api-check→freeze-break→status→pr の長経路 | E2E | 健全 | as-is | Phase 4 |

## 7. flaky / hidden failure 監査

### 現状

- `PLAN-051` で `bats-lite` の `errexit` 伝播 bug と hidden failure が修正済み
- `cli/tests/test-bats-lite-runner.bats` に以下の自己テストがある
  - pass
  - fail が `not ok` になる
  - `skip` が reason 付きで通る
  - `errexit` 後に後続行が実行されない
- `cli/lib/tests/test_axis_11_regression.py` に flaky 判定ロジックのテストがある
  - 非 flaky PASS→FAIL は critical
  - flaky 履歴あり PASS→FAIL は warning

### 評価

- hidden failure の再発防止は「存在する」
- ただし flaky 判定は detector / baseline ロジック側に寄っており、Bats 側の retry / quarantine 戦略はまだ弱い
- manual shell check が 2 本残っているため、「人手でしか確かめていない failure mode」は残存

## 8. capability coverage と INV01 突合

| capability | テストの有無 | 所見 |
|---|---|---|
| V-model schema / QA baseline schema | あり | `test_axis_11_regression.py`、`test_design_review_pair_check.py`、`test_helix_db_v20.py` で部分的に担保。schema 全体の contract test は不足。 |
| 14 detector system | あり | axis-01〜14 すべて pytest あり。接続も `test_gate_detector_integration.py`、`helix-gate-detector.bats` で確認。 |
| contract extractor / contract registry | あり | `test_contract_registry.py` はあるが auto-record / FE 契約までは未到達。 |
| handover protocol | あり | Bats と pytest の両線で手厚い。 |
| skill 推挙 / skill chain | あり | `test_skill_*` 群で厚い。 |
| Reverse HELIX | あり | Bats と verify で存在。 |
| Scrum HELIX | あり | Bats と verify で存在。 |
| Agent transformation / codex-claude harness | あり | Bats、pytest、verify が三重にある。 |
| PMO / advisor role system | あり | Claude/Codex harness テストに部分包含。role-level capability test は追加余地あり。 |
| Stop hook / session summary shim | あり | `test-helix-session-summary.bats` と hook 系 pytest がある。 |
| code-index | あり | `test-helix-code.bats`、`test_code_catalog.py` 群で厚い。 |
| budget guard / auto-thinking | あり | budget Bats / pytest がある。 |
| gate runner | あり | Bats・pytest・verify の三層で存在。 |

結論:

- INV01 capability に対して「テストが全くない」領域は見当たらない
- ただし「部分実装 capability に対する追試不足」は明確で、V-model schema、contract auto-record、automation layer 連動が次の重点

## 9. fixture / mock 戦略

### as-is

- pytest は `tmp_path`、一時 repo、SQLite、`patch()`、fake runner を多用
- handover / gate / verify-agent は一時 project を組んで擬似統合するパターンが多い
- Bats は `mktemp -d` + `.helix` fixture + fake project 構築
- `verify/*.sh` はより実フロー寄りだが、依然として temporary project が中心

### 評価

- 単体 / 擬似統合には強い
- 実 DB は SQLite 実体を使っており、この点は mock 偏重ではない
- 一方で GitHub Actions、hook install 済み repo、実 `bats` / `bats-lite` 切替、外部 connector 連動などは mock/fixture 前提が多い

### 推奨

- DB は現状の「SQLite 実体」方針を維持
- hook / plan-cmds / automation layer は shell contract test を追加
- verify-agent / contract / V-model schema は fake runner に加え schema fixture の golden test を増やす

## 10. CI 連動度

`.github/workflows/ci.yml` では以下を実行している。

1. `bash cli/helix-test`
2. `bats cli/tests/*.bats`
3. `bash cli/helix-verify-all`
4. `python3 -m pytest cli/lib/tests/ -v`
5. PR 時のみ drift-check

### 評価

- CI は Bats / verify / pytest を一通り回しており、範囲は広い
- `pre-commit` は hook template として存在するが、GitHub Actions から直接は実行していない
- manual shell check 2 本は CI 直接対象外

## 11. V2 で新規追加すべきテスト top-10

1. V-model schema の end-to-end contract test  
   `test_baseline`、`design_review`、`contract_entries`、`accuracy_score_effective` を 1 本の scenario でつなぐ
2. sprint pair-check test  
   `helix gate --pair-check` と設計 review pair を跨ぐ長経路検証
3. drive × layer semantic test  
   `be / fe / db / fullstack / scrum / agent` ごとに expected gate/phase 遷移を固定
4. `cli/helix-plan-cmds/_shared.sh` helper contract test  
   uncovered top-10 の集中解消
5. Claude hook shell test  
   `.claude/hooks/post-tool-use.sh`、`pretooluse-opus-repo-block.sh`、`stop.sh` を shell contract 化
6. contract auto-record schema test  
   `D-API` 更新から `contract_entries` 反映までの自動記録を固定
7. detector × pre-commit auto-run test  
   `PLAN-067` 系の staged diff 連動検証
8. flaky baseline replay test  
   `PASS→FAIL→PASS`、`3連続FAIL`、warning/fail-close をまとめて再生
9. verify-agent multi-tool harvest / design / cross-check integrated test  
   `research` / `tl` runner stub を跨ぐ長経路
10. full-flow Phase 4 guardrail test  
   `readiness`、`detector`、`handover ready_for_review`、`session-summary` を 1 本化

## 12. 推奨

### 選択肢

| 選択肢 | メリット | デメリット | 推奨度 |
|---|---|---|---|
| A. core5 維持のみ | 低コスト、既存 gate を壊しにくい | advanced 層の事故を拾えない | 低 |
| B. uncovered top-10 + V-model schema 追補 | 少ない投資で coverage の説明責任が改善 | automation layer の体系化までは届かない | 中 |
| C. detector / V-model / plan-cmd / hook を Phase 4 guardrail として再編 | V2 入力として最も筋がよい。品質監査が設計に直結する | グループ再編と新規 scenario 設計が必要 | 高 |

### 推奨方針

- 推奨は `C`。理由は、現状の問題は「テストが少ない」ことよりも「guardrail と coverage の焦点が分散している」ことだから。
- まずは `overall uncovered top-10` と `V-model schema / pair-check / drive semantic` の 3 本柱を Phase 4 入力として固定するべき。
- core5 coverage はすでに 86.4% あるため、そこを大きく崩さず、advanced 層を detector 主導で増やすのが最も費用対効果が高い。
