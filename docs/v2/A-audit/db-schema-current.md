# FR-INV07 helix.db v20 schema 現状棚卸し

最終更新: 2026-05-14

## 概要

本メモは `helix.db v20` の現行 schema を、`cli/lib/helix_db.py` と実 DB (`.helix/helix.db`) の両方から棚卸しした監査結果です。目的は、`docs/v2/L1-REQUIREMENTS.md` §3.1 `FR-VD01-09` と V2 Phase 3 `helix.db v21` 拡張の入力を固定することです。

結論:

- 現DBの実 table は **48 table**（`sqlite_sequence` 除外）
- 総 record 数は **433**
- `PLAN-065` で入った V-model 4 table のうち、`contract_entries / test_design_entries / design_review / test_baseline` は **現時点で全て 0 record**
- `detector_runs` は稼働しているが、`routing_decisions` は **本体 schema に未収載** で、現DBにも存在しない
- `managed_products / agent_registry / er_diagrams / process_maps / design_sprint_entries / design_sprint_artifact_links` は **v21 新規追加前提** で未実装

不確実性:

- この環境では `helix` コマンドが PATH 上に無く、`helix code find` や `helix handover status` の実行確認はできていない。そのため調査は **リポジトリ静的読解 + SQLite 実DB読取** ベースです。
- `cli/lib/migrations/*.py` と `cli/lib/_schema_v*.py` は現時点で存在しません。v1-v20 の導入版は、`cli/lib/helix_db.py` の `migrate()` と各 helper から復元しています。
- `detector_runs` は `cli/lib/helix_db.py` ではなく `cli/lib/detectors/base.py:69` の lazy create による導入です。`schema_version` と完全同期していない点は注記対象です。

## マイルストーン

| マイルストーン | 追加・変更の主眼 | 主な table |
|---|---|---|
| v1 | 基本ログ基盤 | `task_runs`, `action_logs`, `observations`, `feedback`, `gate_runs`, `hook_events`, `cost_log`, `skill_usage`, `invocation_log` |
| v5 | skill 利用記録の導入 | `skill_usage` |
| v10 | audit/import 基盤 | `import_runs`, `audit_decisions` |
| v15 | code catalog 強化 | `code_index` (`bucket`, `symbol_line`) |
| v20 | V-model / QA baseline | `test_baseline`, `test_design_entries`, `design_review`, `contract_entries.design_level` |

## table 棚卸し

記法:

- `record 件数` は `実数 (運用度)` 表記
- `V-model 強化での扱い` は `(a) drive列追加 / (b) origin_mode + evidence_status 追加 / (c) 新規 link / (d) 変更なし`
- `V2 変更計画` は `as-is / modify / extend / deprecate / new`

| table 名 | schema version / 起源 | 役割 | 主要列 | record 件数 (現状) | INSERT 元 | 読み取り元 | V-model 強化での扱い | V2 変更計画 | 修正理由・範囲 |
|---|---|---|---|---|---|---|---|---|---|
| `task_runs` (`cli/lib/helix_db.py:36`) | v1 | task 実行の親ログ | PK=`id`, `task_id`, `task_type`, `role`, `status` | 0 (未使用) | `cli/lib/helix_db.py:1459`, `cli/helix-task` | `cli/helix-gate`, `cli/lib/global_store.py` | d | as-is | V2 本筋ではなく task OS 既存基盤 |
| `action_logs` (`cli/lib/helix_db.py:50`) | v1 | task 内 action 単位ログ | PK=`id`, FK=`task_run_id`, `action_type`, `status` | 0 (未使用) | `cli/lib/helix_db.py:1474`, `cli/helix-test` | `cli/lib/learning_engine.py`, `helix_db report` | d | as-is | 旧学習系の証跡、V2 直接変更対象外 |
| `observations` (`cli/lib/helix_db.py:62`) | v1 | observation pass/fail 記録 | PK=`id`, FK=`task_run_id`,`action_log_id`, `passed` | 0 (未使用) | `cli/lib/helix_db.py:1488`, `cli/helix-test` | `cli/lib/learning_engine.py`, `helix_db report` | d | as-is | 旧学習系の補助観測 |
| `feedback` (`cli/lib/helix_db.py:75`) | v1 | ユーザーフィードバック蓄積 | PK=`id`, FK=`task_run_id`, `feedback_type`, `category` | 0 (未使用) | `cli/lib/helix_db.py:1499` | `helix_db report`, `helix-gate` 補助 | d | as-is | V2 では feedback loop 要件と間接関係のみ |
| `task_evaluations` (`cli/lib/helix_db.py:87`) | v1 | task 品質評価 | PK=`id`, `task_type`, `quality_score`, `user_score` | 0 (未使用) | `helix_db` insert helper 系 | `helix_db report` | d | as-is | 実運用薄く、当面監視のみ |
| `task_selections` (`cli/lib/helix_db.py:100`) | v1 | PM/TL の task 選択履歴 | PK=`id`, `plan_id`, `selected_tasks`, `review_status` | 0 (未使用) | `cli/lib/helix_db.py:2029`, `cli/helix-task` | `cli/helix-task`, `helix_db report` | d | as-is | V2 直結薄いが orchestration 監査には残す |
| `gate_runs` (`cli/lib/helix_db.py:113`) | v1, v4で `task_run_id` 追加 | gate 実行履歴 | PK=`id`, FK=`task_run_id`, `gate`, `result` | 0 (未使用) | `cli/helix-gate` | `helix_db report`, `cli/helix-gate` | d | as-is | 将来 detector auto-run と join 余地はあるが v21要件なし |
| `plan_reviews` (`cli/lib/helix_db.py:124`) | v1 | PLAN review の集約結果 | PK=`id`, `plan_id`, `verdict`, `reviewer` | 0 (未使用) | 明示的 runtime insert 未確認 | docs / report 想定 | d | as-is | 実装薄い。将来 review telemetry と統合候補 |
| `interrupts` (`cli/lib/helix_db.py:133`) | v1, v4で `task_run_id` 追加 | interrupt / incident 記録 | PK=`id`, `interrupt_id`, `kind`, `status` | 0 (未使用) | `helix_db` migration/test 由来、runtime write 薄い | `session_start_helpers` | d | as-is | handover/interrupt 連携は別実装が正本 |
| `retro_items` (`cli/lib/helix_db.py:146`) | v1, v4で `gate_name`,`gate_run_id` 追加 | retro action item | PK=`id`, `gate`, FK=`gate_run_id`, `done` | 0 (未使用) | `helix_db` 経由想定、runtime薄い | report / docs 想定 | d | as-is | 活用前段階 |
| `debt_items` (`cli/lib/helix_db.py:159`) | v1 | 技術負債台帳 | PK=`id`, `title`, `priority`, `status` | 0 (未使用) | YAML/CLI 側が主、本DB insert 薄い | `helix-dashboard` は YAML を参照 | d | deprecate | DBより YAML 正本が強く、整理余地あり |
| `hook_events` (`cli/lib/helix_db.py:169`) | v1 | hook 発火ログ | PK=`id`, `event_type`, `file`, `result` | 0 (未使用) | `cli/libexec/helix-hook`, `cli/helix-review`, `cli/helix-drift-check` | `helix_db report`, `session-summary` | d | as-is | 自動化レイヤの基礎。現DB未稼働のみ |
| `cost_log` (`cli/lib/helix_db.py:177`) | v1 | 実行コスト集計 | PK=`id`, `role`, `model`, `cost_est`, `created_at` | 114 (数百件未満) | `cli/helix-codex`, `cli/helix-session-summary` | `helix_db report session`, session summary系 | d | as-is | 既に運用中。v21追加対象ではない |
| `bench_snapshots` (`cli/lib/helix_db.py:187`) | v1 | benchmark snapshot | PK=`id`, `period`, `metrics_json` | 0 (未使用) | runtime write 未確認 | docs/report 想定 | d | as-is | 将来可観測性用の保留 table |
| `skill_usage` (`cli/lib/helix_db.py:194`) | v1, v5導入, v6/v7/v16列拡張 | skill 推挙/実行履歴 | PK=`id`, `task_text`, `skill_id`, `outcome`, `session_id` | 0 (未使用) | `skill_dispatcher` 系想定、tests あり | `axis_13`, `skill_dispatcher stats` | d | as-is | detector参照先だが現DB未投入 |
| `schema_version` (`cli/lib/helix_db.py:235`) | v1 | schema migration 管理 | PK=`version`, `applied_at` | 19 (v2-v20分) | `migrate()` | `migrate()`, tests, audit | d | modify | v21で `21` を追記。現DBは v20 到達を 19 行で保持 |
| `requirements` (`cli/lib/helix_db.py:243`) | v2 | 要件本体 | PK=`id`, UK=`req_id`, `status` | 0 (未使用) | 要件 import / test 想定 | `gate_check_generator`, templates | d | as-is | V2 でも要件正本は docs 側優勢 |
| `req_impl_map` (`cli/lib/helix_db.py:255`) | v2 | 要件→実装対応 | PK=`id`, FK=`req_id`, `impl_path`, `verified` | 0 (未使用) | 要件 mapping 補助 | `gate_check_generator` | d | as-is | traceability 用だが未運用 |
| `req_test_map` (`cli/lib/helix_db.py:265`) | v2 | 要件→テスト対応 | PK=`id`, FK=`req_id`, `test_path`, `test_result` | 0 (未使用) | 要件 mapping 補助 | gate/templates 想定 | d | as-is | traceability 用だが未運用 |
| `req_changes` (`cli/lib/helix_db.py:275`) | v2 | 要件変更履歴 | PK=`id`, FK=`req_id`, `change_type` | 0 (未使用) | 要件 change log 想定 | audit/report 想定 | d | as-is | docs 正本の補助 table に留まる |
| `accuracy_score` (`cli/lib/helix_db.py:294`) | v8 | gate 品質スコア | PK=`id`, `plan_id`, `gate`, `dimension`, `level` | 20 (数十件) | `cli/helix-gate`, `helix_db.record_accuracy_score` | `cli/helix-gate`, effective view | d | as-is | 稼働中。V-model score とは別軸 |
| `schedules` (`cli/lib/helix_db.py:317`) | v9 | scheduler 定義 | PK=`id`, `schedule_expr`, `task_type`, `status` | 0 (未使用) | `scheduler_helper` | `scheduler_helper` | d | as-is | 自動化基盤だが V2 schema拡張対象外 |
| `jobs` (`cli/lib/helix_db.py:332`) | v9 | 非同期 job queue | PK=`id`, `task_type`, `priority`, `status` | 0 (未使用) | `job_queue_helper`, `helix_db` | `job_queue_helper` | d | as-is | infra 補助 |
| `locks` (`cli/lib/helix_db.py:350`) | v9 | lock 管理 | PK=`name`, `pid`, `scope` | 0 (未使用) | `helix_db.acquire_lock`, `lock_helper` | `lock_helper` | d | as-is | infra 補助 |
| `events` (`cli/lib/helix_db.py:360`) | v9 | observability event | PK=`id`, `event_name`, `severity`, `occurred_at` | 0 (未使用) | `helix_db.record_event` | `observability_helper` | d | as-is | observability 基盤 |
| `metrics` (`cli/lib/helix_db.py:372`) | v9 | observability metric | PK=`id`, `metric_name`, `value`, `recorded_at` | 0 (未使用) | `helix_db.record_metric` | `observability_helper` | d | as-is | observability 基盤 |
| `setup_checks` (`cli/lib/helix_db.py:382`) | v9 | setup 状態 | PK=`component`, `verify_state`, `installed` | 0 (未使用) | `setup_helper` | `setup_helper` | d | as-is | setup subsystem 専用 |
| `setup_events` (`cli/lib/helix_db.py:395`) | v9 | setup 実行履歴 | PK=`id`, FK=`component`, `action`, `status` | 0 (未使用) | `setup_helper` | `setup_helper` | d | as-is | setup subsystem 専用 |
| `import_runs` (`cli/lib/helix_db.py:411`) | v10 | audit import 実行履歴 | PK=`id`, `source_hash`, `scope_hash`, `status` | 0 (未使用) | `cli/lib/helix_db.py:1731`, `audit_a1.py` | `audit_a1.py` | d | as-is | A1 audit 専用 |
| `audit_decisions` (`cli/lib/helix_db.py:422`) | v10 | audit keep/remove 判定履歴 | PK=`id`, `candidate_id`, `schema_version`, `decision`, `status` | 0 (未使用) | `audit_a1.py` | `audit_a1.py`, `query_active_audit_decisions` | d | as-is | A1 audit 専用 |
| `scrum_trigger` (`cli/lib/helix_db.py:466`) | v12 | scrum trigger persistence | PK=`trigger_id`, `scrum_type`, `status`, `normalized_signature` | 0 (未使用) | `cli/lib/scrum_trigger.py` | `scrum_trigger.py` | d | as-is | scrum mode 専用 |
| `verify_runs` (`cli/lib/helix_db.py:503`) | v13 | verify-agent 実行履歴 | PK=`run_id`, `subcommand`, `plan_id`, `has_fail_close` | 0 (未使用) | `cli/lib/verify_agent.py` | `verify_agent.py` | d | as-is | verify subsystem 専用 |
| `code_index` (`cli/lib/helix_db.py:527`) | v14, v15で `bucket/symbol_line`, v18で6列追加 | code catalog | PK=`id`, `path`, `symbol_line`, `bucket`, `axis/stack/lifecycle` | 59 (数十件) | `cli/lib/code_catalog.py` | `code_recommender`, `helix code stats/find`, gates | d | as-is | 4-layer chain の code 層。schema追加要求は現時点なし |
| `entries` (`cli/lib/helix_db.py:549`) | v17, v19で `qa_result/security_audit/design_decision` 追加 | entry DB の中心 | PK=`id`, `axis`, `stack`, `lifecycle`, `ref` | 69 (数十件) | `entry_helper.py` | `entry_helper.py`, `helix-gate` | c または d | as-is | link活用余地はあるが v21要件では追加列未定 |
| `links` (`cli/lib/helix_db.py:567`) | v17 | entry 間リンク | PK=`from_id,to_id,kind`, kind enum | 0 (未使用) | `entry_helper.py` | `entry_helper.py`, `helix-gate` | c | extend | 4-layer chain SQL/設計スプリント連携で link 活用拡大候補 |
| `contract_entries` (`cli/lib/helix_db.py:587`) | v17, v20で `design_level` 追加 | contract registry | PK=`id`, `contract_type`, `source_path`, `design_level`, `breaking_change_flag` | 0 (未使用) | `cli/lib/contract_registry.py:138` | `contract_registry.py`, detector/tests | a+b | modify | FR-V01, FR-DB06, FR-DB09 の中心対象 |
| `code_edges` (`cli/lib/helix_db.py:600`) | v17 | code/contract 関係エッジ | PK=`id`, `from_entry_id`, `to_entry_id`, `edge_type` | 0 (未使用) | `cli/lib/code_edges.py` | `axis_10_relation_graph`, tests | c | as-is | relation graph には必要だが v21列追加要件なし |
| `test_baseline` (`cli/lib/helix_db.py:619`) | v20 | test 実行 baseline | PK=`id`, UK=`commit_sha,suite,test_name`, `status`, `code_entry_id`, `test_design_id` | 0 (未使用) | 本番 insert 未確認、tests と `axis_11_regression` 前提 | `axis_11_regression.py` | d | extend | 4-layer chain view の右端。運用接続が必要 |
| `test_design_entries` (`cli/lib/helix_db.py:640`) | v20 | test 設計 registry | PK=`id`, `plan_id`, `acceptance_key`, FK=`contract_id`, `test_level`, `paired_design_level` | 0 (未使用) | 本番 insert 未確認。acceptance 抽出は要件のみ | pair-check / V-model query 想定 | a | modify | FR-V01 の対象。現状は schemaのみ |
| `design_review` (`cli/lib/helix_db.py:662`) | v20 | 縦/横 review 記録 | PK=`id`, `plan_id`, `layer`, `review_axis`, `verdict` | 0 (未使用) | tests の seed のみ確認 | `cli/helix-gate --pair-check`, `query_design_review_pair` | a | modify | FR-V01 + FR-DB10 の対象。現状は query先のみ |
| `invocation_log` (`cli/lib/helix_db.py:679`) | v1相当、v16移行時に保持保証 | agent/CLI invocation telemetry | PK=`id`, `timestamp`, `type`, `role`, `plan_id`, `task_id` | 106 (数百件未満) | `cli/lib/helix_db.py:1548`, invocation helper | `axis_13`, dashboard, report | d | as-is | 既稼働。自動化系の主要読取源 |
| `deferred_findings` (`cli/lib/helix_db.py:845`) | v11 | carry/deferred finding 台帳 | PK=`id`, `plan_id`, `level`, `status`, `severity` | 0 (未使用) | `cli/lib/deferred_findings.py` | `helix-gate`, `deferred_findings.py` | d | as-is | V2 監査補助、schema変更要求なし |
| `accuracy_score_adjustments` (`cli/lib/helix_db.py:873`) | v11 | finding 起因の score 補正 | PK=`id`, FK=`finding_id`, `plan_id`, `gate`, `penalty` | 0 (未使用) | `deferred_findings.py` | effective view | d | as-is | score 補正専用 |
| `sessions` (`cli/lib/helix_db.py:944`) | v16 | セッション開始記録 | PK=`id`, `started_at`, `cwd`, `claude_session_id` | 18 (数十件) | `cli/libexec/helix-session-start` | `skill_dispatcher stats`, session helpers | d | as-is | session-start telemetry として稼働中 |
| `sprint_metrics` (`cli/lib/helix_db.py:996`) | v19 | sprint KPI | PK=`sprint_id`, `test_pass_rate`, `drift_count` | 0 (未使用) | runtime write 未確認 | architecture/docs/tests 想定 | d | as-is | V2 Phase F の dashboard 候補だが現時点未投入 |
| `phase_gate_runs` (`cli/lib/helix_db.py:1007`) | v19 | phase/gate KPI | PK=`gate_id,ran_at`, `phase`, `result` | 0 (未使用) | runtime write 未確認 | docs/tests 想定 | d | as-is | dashboard 候補だが未投入 |
| `detector_runs` (`cli/lib/detectors/base.py:69`) | `schema_version`外、PLAN-063 detector 導入 | detector verdict 永続化 | PK=`run_id`, `axis_id`, `phase_gate`, `verdict`, `findings_json` | 28 (数十件) | `cli/lib/detectors/base.py:116` | `axis_02/05/10/11/14`, `detectors/registry.py` | d | as-is | 現在もっとも運用されている自動検知 table |

## 現DBに存在しないが、要件・周辺実装で参照される table

| table 名 | 現状 | 根拠 | 推奨扱い |
|---|---|---|---|
| `routing_decisions` | 未実装 / 現DBなし | detector tests と `docs/v2/L1-REQUIREMENTS.md`、`docs/v2/CONCEPT.md` で参照。`cli/lib/detectors/registry.py` は存在前提で集計分岐する | v21 までに `new` または、既存 `invocation_log` / `entries` へ吸収するかを早期確定 |
| `plans` | 未実装 / 現DBなし | `docs/v2/CONCEPT.md` が基盤 table として言及 | 本監査時点では構想のみ。v21 scope に入れるなら別要件化が必要 |
| `managed_products` | 未実装 / 現DBなし | `docs/v2/L1-REQUIREMENTS.md` FR-DB04 | v21 `new` |
| `agent_registry` | 未実装 / 現DBなし | `docs/v2/L1-REQUIREMENTS.md` FR-DB05 | v21 `new` |
| `er_diagrams` | 未実装 / 現DBなし | `docs/v2/L1-REQUIREMENTS.md` FR-DB02 | v21 `new` |
| `process_maps` | 未実装 / 現DBなし | `docs/v2/L1-REQUIREMENTS.md` FR-DB03 | v21 `new` |
| `design_sprint_entries` | 未実装 / 現DBなし | `docs/v2/L1-REQUIREMENTS.md` FR-DB07 / FR-VS01 | v21 `new` |
| `design_sprint_artifact_links` | 未実装 / 現DBなし | `docs/v2/L1-REQUIREMENTS.md` FR-DB08 / FR-VS02 | v21 `new` |

## 集計

- 全 table 数: **48**
- 総 record 件数: **433**
- 実際に record が入っている table:
  - `cost_log` 114
  - `invocation_log` 106
  - `entries` 69
  - `code_index` 59
  - `detector_runs` 28
  - `accuracy_score` 20
  - `schema_version` 19
  - `sessions` 18

### 空運用 table 一覧

`accuracy_score_adjustments`, `action_logs`, `audit_decisions`, `bench_snapshots`, `budget_events`, `code_edges`, `contract_entries`, `debt_items`, `deferred_findings`, `design_review`, `events`, `feedback`, `gate_runs`, `hook_events`, `import_runs`, `interrupts`, `jobs`, `links`, `locks`, `metrics`, `observations`, `phase_gate_runs`, `plan_reviews`, `req_changes`, `req_impl_map`, `req_test_map`, `requirements`, `retro_items`, `schedules`, `scrum_trigger`, `setup_checks`, `setup_events`, `skill_usage`, `sprint_metrics`, `task_evaluations`, `task_runs`, `task_selections`, `test_baseline`, `test_design_entries`, `verify_runs`

### V-model 強化で変更必須 table

- `contract_entries`
  - `drive` 追加
  - `design_level` 再分類 migration
  - `origin_mode` / `evidence_status` 追加
- `test_design_entries`
  - `drive` 追加
  - acceptance 抽出導線の本実装
- `design_review`
  - `drive` 追加
  - `direction` / `source_phase` 追加
- `links`
  - `contract -> code -> test_design -> baseline` の query を支える link 実運用が必要
- `test_baseline`
  - schema 追加よりも、test 実行完了時の自動投入導線が先

### v21 で新規追加する table 一覧

- `design_sprint_entries`
- `design_sprint_artifact_links`
- `er_diagrams`
- `process_maps`
- `managed_products`
- `agent_registry`

## v20 → v21 additive migration 概要

TL 推奨と現行要件を突き合わせると、v21 は **既存 table を壊さず additive に広げる** 方針が妥当です。

1. V-model 中核 3 table を拡張する
   - `contract_entries`: `drive`, `origin_mode`, `evidence_status`
   - `test_design_entries`: `drive`
   - `design_review`: `drive`, `direction`, `source_phase`
2. `contract_entries.design_level` の再分類 migration を別ステップに分離する
   - `dry-run` 必須
   - batch + transaction
   - 既存 0 record の今が最も安全
3. 設計成果物 table を追加する
   - `er_diagrams`
   - `process_maps`
4. 段 1 / 段 2 分離の基盤 table を追加する
   - `managed_products`
   - `agent_registry`
5. 工程転換 (V-model sprint) の table を追加する
   - `design_sprint_entries`
   - `design_sprint_artifact_links`
6. `detector_runs` と `routing_decisions` の扱いを揃える
   - 推奨は `_migrate_v20_to_v21` 側へ正式収載
   - 少なくとも `schema_version` 管理外 table を残したままにしない

## 推奨

1. `v21` の最初の migration は、**V-model 3 table の列追加 + 新規 6 table 追加** に限定し、`routing_decisions` や `plans` の整理は別 issue に切るのが安全です。
2. `contract_entries / test_design_entries / design_review / test_baseline` は、schema 追加より **record 自動投入導線の欠如** が本質的なボトルネックです。v21 では migration と同時に writer を実装しないと再び空運用になります。
3. `detector_runs` を本体 migration 管理外に置き続けるのは drift の温床です。`_migrate_v20_to_v21` に正式編入するか、少なくとも `schema inventory` 上は特殊扱いを明記すべきです。
4. `links` は現状 0 record ですが、V-model 4 layer chain と工程転換を SQL で解くなら重要度が上がります。v21 では `link writer` の設計を併走させるべきです。

## ソース

- `cli/lib/helix_db.py`
- `cli/lib/detectors/base.py`
- `cli/lib/contract_registry.py`
- `cli/lib/code_catalog.py`
- `cli/lib/code_edges.py`
- `cli/lib/entry_helper.py`
- `cli/lib/verify_agent.py`
- `cli/lib/scrum_trigger.py`
- `cli/lib/setup_helper.py`
- `cli/lib/job_queue_helper.py`
- `cli/lib/scheduler_helper.py`
- `cli/lib/observability_helper.py`
- `cli/lib/deferred_findings.py`
- `docs/plans/PLAN-065-qa-strictness.md`
- `docs/v2/L1-REQUIREMENTS.md`
- `docs/v2/CONCEPT.md`
