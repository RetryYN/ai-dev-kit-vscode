---
doc_id: l6-helix-workflows-edge-case-design
title: "HELIX-workflows V2 エッジケース設計 (境界値・例外・エラー処理)"
status: frozen
process_layer: L6
doc_type: edge_case_design
parent_plan: L6-helix-workflows-エッジケースplan
pairs_design: docs/v2/L5-internal-design/helix-workflows-internal-processing-design.md
pairs_test_design: docs/v2/L7-test-design/helix-workflows-unit-test-design.md
---

# HELIX-workflows V2 エッジケース設計 (境界値・例外・エラー処理)

## §0 概要

本書は `docs/v2/L6-functional-design/helix-workflows-function-spec-design.md` を入口契約の正本、`docs/v2/L5-internal-design/helix-workflows-internal-processing-design.md` を境界条件・失敗境界・回復経路の正本、`docs/v2/L5-internal-design/helix-workflows-interface-detailed-design.md` を exit code / timeout / retry / blocking の正本として、HELIX-workflows V2 の境界値・例外・エラー処理を L7 単体テストへ落とせる粒度で固定する。

### §0.1 分類

| 分類 | 意味 | 代表例 |
|---|---|---|
| 境界値 | 件数、サイズ、時間、スコア、閾値の端点 | 空 PLAN、10000 file 超、score NaN、timeout 上限 |
| 例外 | 入力破損、schema 不一致、権限、存在しない参照 | 不正 frontmatter、不正 mode、missing ADR、権限不足 |
| 並行 | lock、同時 write、debounce、重複 dispatch | helix.db lock、scheduler 競合、hook 同時発火 |
| リソース | ファイル数、DB サイズ、外部 process、メモリ | 巨大 graph、JSON 256KB 超、metrics 欠損 |

### §0.2 exit code 体系

| exit code | 意味 | テスト観点 |
|---:|---|---|
| 0 | success / warning-only success | fail-open で warning を `issues[]` に残す |
| 1 | user error / input invalid | 引数不足、unknown role、unsupported subcommand |
| 2 | fail-close / blocking failure | artifact 破損、DB write 失敗、deadlock risk |
| 1001 | routing / command not found | routing 不明、検証 route 不在 |
| 1010 | contract drift / plan mismatch | trace 欠損、artifact integrity、coexist policy |
| 1020 | artifact stale / policy age | planned 期限超過、budget pressure |
| 1030 | illegal transition | mode transition / state machine 不正 |
| 1040 | resource busy | lock 競合、blocking resource busy |
| 1050 | timeout | hook / command timeout |
| 1060 | fail-open allowed | 監査系 hook の遅延許容 |

### §0.3 fail-close / fail-open 方針

- fail-close: 契約・trace・状態遷移・migration integrity・DB write・権限境界・destructive 操作に関わるもの。`exit code=2` または domain code 10xx を返し、後続処理を止める。
- fail-open: 監査ログ、statusLine、任意 metrics、advisory output など本体実行を止めると可用性を損なうもの。`exit code=0` または `1060` とし、`issues[].severity=warning` を必ず残す。
- retry: read-only / 一時 FS 例外は 1〜3 回まで許容する。DB write / destructive / migration apply は原則 retry せず fail-close する。
- rollback: backup / dry-run / verify が定義された mutation のみ rollback 可能とする。rollback 不能な部分失敗は quarantine + manual recovery として扱う。

## §1 共通エラー処理パターン

| pattern ID | 対象 | 入力条件 | 期待動作 | implementation_status | source ref |
|---|---|---|---|---|---|
| EP-001 | CLI 全般 | `--timeout <=0` または上限超過 | user error。exit `1`、stderr に timeout validation error | implemented | L5 IF §1.4 |
| EP-002 | CLI 全般 | 処理 timeout | `ERROR CODE=1050`、exit `2`。hook は retry 後 2 回連続 timeout で fail-close | implemented | L5 IF §11 |
| EP-003 | read-only scan | 一時 FS lock / permission transient | 1〜3 回 retry。最終失敗で fail-close または warning 化 | implemented | L5 internal §1.1 |
| EP-004 | DB write | `sqlite3.OperationalError: database is locked` | retry しない。exit `2` / `1040` 相当、partial write を残さない | implemented | L5 IF §11 / A-88 |
| EP-005 | mutation | dry-run fail | apply を呼ばず fail-close。rollback 不要 | implemented | L5 internal §8.1 |
| EP-006 | mutation | apply 後 verify fail | backup から rollback、rollback 結果を audit log に残す | partial | L5 internal §8.1 |
| EP-007 | audit hook | audit write timeout | fail-open。warning issue を残し本体処理継続 | implemented | L5 IF §10 / §11 |
| EP-008 | schema validation | payload / frontmatter parse fail | fail-close。入力を破損扱いし downstream へ渡さない | implemented | L5 internal §2.1 |

### §1.1 retry / rollback の判断基準

retry してよいのは、読み取り専用であり、同一入力の再実行が重複副作用を生まない処理に限る。`scan_docs()`、`build_catalog()`、`check_pair_freeze()` は retry 可能である。一方、`record_invocation()`、`save_dependencies()`、`fire_slot()`、migration apply は重複 write や順序破壊の危険があるため retry しない。

rollback が許可されるのは、事前 backup と verify 手順が明示され、rollback 実行後に元状態の checksum または manifest を検証できる場合だけである。rollback が失敗した場合は `blocked` 状態へ遷移し、quarantine / manual recovery を必要条件として報告する。

## §2 F1 ドキュメント体系 / pair freeze 境界値・例外ケース

| edge case ID | 対象機能/関数 | 分類 | 入力条件 | 期待動作 (exit code/エラーメッセージ/rollback) | implementation_status | L7 単体テスト pointer | L5/関数仕様 source ref |
|---|---|---|---|---|---|---|---|
| EC-F1-001 | F1-1 `helix doctor <check-*>` | 境界値 | 対象 docs が 0 件 | exit `0`、empty payload。warning なし | implemented | → UT-F1-001 異常系 | L6 §1 F1-1 / L5 internal §1.1 |
| EC-F1-002 | F1-1 `helix doctor --json --summary` | 例外 | 相互排他 flag 同時指定 | exit `2`、usage error、side effect なし | implemented | → UT-F1-002 異常系 | L6 §1 境界 critical / L5 IF §1.3 |
| EC-F1-003 | F1-1 4 domain collect | リソース | scan が 3s 超過 | `collect_timeout`、retry 最大 3 回、最終 exit `1050` | implemented | → UT-F1-003 異常系 | L5 internal §1.1 |
| EC-F1-004 | F1-1 domain validation | 例外 | 4 domain 外 path が 1 件 | fail-close、exit `2`、後続 trace 計算停止 | implemented | → UT-F1-004 異常系 | L5 internal §1.1 |
| EC-F1-005 | F1-2 `vmodel_lint.main()` | 例外 | missing reference > 0 | exit `1010`、violation detail を stderr / JSON issues に出す | implemented | → UT-F1-005 異常系 | L6 §1 F1-2 / L5 internal §1.2 |
| EC-F1-006 | F1-2 SSoT sync | リソース | 300ms/file 超過 | throttle + retry 2 回、解消しなければ exit `1050` | implemented | → UT-F1-006 異常系 | L5 internal §1.2 |
| EC-F1-007 | F1-3 `check_pair_freeze()` | 例外 | `pairs_test_design` が空 path | missing edge。status を planned 扱いへ戻し fail-close | implemented | → UT-F1-007 異常系 | L6 §1 F1-3 / L5 internal §1.3 |
| EC-F1-008 | F1-3 pair freeze | 境界値 | `active_only=True` かつ active PLAN 0 件 | exit 相当なし、`missing=[]` の空結果 | implemented | → UT-F1-008 異常系 | L6 §1 F1-3 |
| EC-F1-009 | F1-4 `write_scaffold()` | 並行 | 既存 output file が存在 | 上書きしない。`status=skipped`、rollback 不要 | implemented | → UT-F1-009 異常系 | L6 §1 F1-4 |
| EC-F1-010 | F1-5 `build_doc_map()` | 例外 | `matrix.features` が dict でない | `ValueError`、file write なし、caller が exit `2` へ正規化 | implemented | → UT-F1-010 異常系 | L6 §1 F1-5 |

### §2.1 境界 critical: 4 artifact trace 欠損

4 artifact trace は L6↔L7-test pair freeze の安全境界であり、反対参照が 1 件でも不足すれば fail-close とする。欠損状態で `implemented` を維持すると、L7 側の test docstring reference が存在しないまま実装が進むため、trace 欠損は `implementation_status=planned` へ戻して扱う。回復経路は、参照 field 修正、対象 file 存在確認、逆参照追記、再 scan の順である。

## §3 F2 PLAN template / registry 境界値・例外ケース

| edge case ID | 対象機能/関数 | 分類 | 入力条件 | 期待動作 (exit code/エラーメッセージ/rollback) | implementation_status | L7 単体テスト pointer | L5/関数仕様 source ref |
|---|---|---|---|---|---|---|---|
| EC-F2-001 | F2-1 `helix plan create` | 境界値 | 空 title / 空 plan_id | exit `1`、input invalid、file write なし | implemented | → UT-F2-001 異常系 | L6 §2 F2-1 / L5 IF §4 |
| EC-F2-002 | F2-1 `helix plan validate` | リソース | 巨大 PLAN (1MB 超 markdown) | parse window 分割。timeout 時 exit `1050` | implemented | → UT-F2-002 異常系 | L5 IF §1.4 |
| EC-F2-003 | F2-2 `parse_frontmatter()` | 例外 | YAML parse 失敗 | `None`、caller は `INVALID_FRONTMATTER` として fail-close | implemented | → UT-F2-003 異常系 | L6 §2 F2-2 / L5 internal §2.1 |
| EC-F2-004 | F2-2 `upsert_plan()` | 例外 | `frontmatter` 空 | `failure_log` 追記。registry upsert しない | implemented | → UT-F2-004 異常系 | L6 §2 境界 critical |
| EC-F2-005 | F2-2 `detect_cycle()` | 例外 | requires graph に循環依存 | cycle list を返す。hook では exit `2` block | implemented | → UT-F2-005 異常系 | L6 §2 F2-2 / L5 IF A-11 |
| EC-F2-006 | F2-3 `validate_plan()` | 例外 | `process_layer=L99` | warning list に `process_layer_invalid`、CLI 層で fail-close | implemented | → UT-F2-006 異常系 | L5 internal §2.1 |
| EC-F2-007 | F2-3 dependency cycle | 境界値 | unknown dependency と known cycle が混在 | unknown は warning、known cycle は fail-close | implemented | → UT-F2-007 異常系 | L6 §2 F2-3 |
| EC-F2-008 | F2-4 `validate_plan_frontmatter()` | 例外 | required key 欠落 | errors に `missing_<key>`、exit `1010` 相当 | implemented | → UT-F2-008 異常系 | L6 §2 F2-4 |
| EC-F2-009 | F2-5 `save_dependencies()` | 並行 | helix.db lock 競合 | DB write retry なし、exit `1040` / `2`、partial write なし | implemented | → UT-F2-009 異常系 | L6 §2 F2-5 / L5 IF A-88 |
| EC-F2-010 | F2-6 plan auto-register hook | 並行 | 同一 PLAN に同時 Edit/Write | 片方のみ upsert 成功、cycle 検出時は hook exit `2` block | implemented | → UT-F2-010 異常系 | L6 §2 F2-6 / L5 IF §10.7 |
| EC-F2-011 | F2-6 hook | 例外 | hook 内 parser timeout 2 回連続 | fail-close、decision=`block`、exit `2` | implemented | → UT-F2-011 異常系 | L5 IF §11 |
| EC-F2-012 | F2-7 `plan_health.scan_all_plans()` | リソース | plans_root が存在しない | empty health payload。gate 強制化は L7 carry | partial | → UT-F2-012 異常系 | L6 §2 F2-7 / CARRY-L7-001 |

### §3.1 境界 critical: registry write の部分失敗

`upsert_plan()` は `plan_registry` を更新し、関連 row を削除して再挿入する。削除後に insert が失敗すると、registry と dependency が不整合になるため、L7 実装では transaction 境界を 1 つに閉じる必要がある。部分失敗時は rollback されること、rollback 不能時は `failure_log` と quarantine 記録に移ることを単体テストで固定する。

## §4 F3 skill catalog / recommender 境界値・例外ケース

| edge case ID | 対象機能/関数 | 分類 | 入力条件 | 期待動作 (exit code/エラーメッセージ/rollback) | implementation_status | L7 単体テスト pointer | L5/関数仕様 source ref |
|---|---|---|---|---|---|---|---|
| EC-F3-001 | F3-1 `helix skill show` | 例外 | unknown skill id | exit `1`、not found、cache 更新なし | implemented | → UT-F3-001 異常系 | L6 §3 F3-1 |
| EC-F3-002 | F3-1 `helix skill chain` | 境界値 | task text 空 | exit `1`、input invalid、dispatch しない | implemented | → UT-F3-002 異常系 | L5 IF A-93 |
| EC-F3-003 | F3-2 `build_catalog()` | 境界値 | skills_root 空 | empty catalog を返す。save は caller 判断 | implemented | → UT-F3-003 異常系 | L6 §3 F3-2 / L5 internal §3.1 |
| EC-F3-004 | F3-2 `load_catalog()` | 例外 | cache JSON 破損 | 1 回 rebuild、再失敗なら exit `2` 相当 | implemented | → UT-F3-004 異常系 | L5 internal §3.1 |
| EC-F3-005 | F3-3 `recommend()` | 境界値 | `top_n=0` | empty candidates、exit `0`、dispatch なし | implemented | → UT-F3-005 異常系 | L6 §3 F3-3 |
| EC-F3-006 | F3-3 embedding fallback | 例外 | embedding API / JSONL catalog unavailable | deterministic fallback。precision warning を issues に残す | implemented | → UT-F3-006 異常系 | L5 internal §3.2 |
| EC-F3-007 | F3-4 `dispatch()` | 例外 | unsupported agent role | `DispatcherError`、main は non-zero、task temp file cleanup | implemented | → UT-F3-007 異常系 | L6 §3 F3-4 |
| EC-F3-008 | F3-5 catalog rebuild hook | 並行 | 複数 SKILL.md 同時編集 | debounce file で 1 回に集約。hook は exit `0` fail-open | implemented | → UT-F3-008 異常系 | L6 §3 F3-5 / L5 IF §10.7 |

### §4.1 境界 critical: recommender fallback

skill 推挙は実行品質に影響するが、推挙失敗で本体タスクを停止し続けると運用不能になる。したがって catalog 読み取り失敗や embedding 不可は deterministic fallback へ降格する。ただし、role が決まらない dispatch は誤委譲に繋がるため fail-close とし、manual / TL 判断へ戻す。

## §5 F4 mode routing / local workflow 境界値・例外ケース

| edge case ID | 対象機能/関数 | 分類 | 入力条件 | 期待動作 (exit code/エラーメッセージ/rollback) | implementation_status | L7 単体テスト pointer | L5/関数仕様 source ref |
|---|---|---|---|---|---|---|---|
| EC-F4-001 | F4-1 `helix route` | 例外 | `--signal` file parse error | exit `1`、signal parse error、state write なし | implemented | → UT-F4-001 異常系 | L6 §4 F4-1 |
| EC-F4-002 | F4-1 `helix route --json` | 境界値 | signal が空 | forward suggestion + warning、exit `0` | implemented | → UT-F4-002 異常系 | L5 internal §4.1 |
| EC-F4-003 | F4-2 `RouteEngine.evaluate()` | 例外 | unknown explicit mode | fail-close または warning fallback。曖昧性 >2 は clarification_required | implemented | → UT-F4-003 異常系 | L6 §4 F4-2 / L5 internal §4.1 |
| EC-F4-004 | F4-2 `from_detect_output()` | 例外 | `detector/status/result` 欠落 | `ValueError`、exit `2` へ正規化 | implemented | → UT-F4-004 異常系 | L6 §4 境界 critical |
| EC-F4-005 | F4-2 transition table | 例外 | illegal transition | `ERROR(DOC-1030)`、exit `1030` / `2` | implemented | → UT-F4-005 異常系 | L5 IF A-07 / L5 internal §4.2 |
| EC-F4-006 | F4-3 `dispatch_task()` | 例外 | shell command unavailable | `(False, message)`、dependent tasks not started | implemented | → UT-F4-006 異常系 | L6 §4 F4-3 |
| EC-F4-007 | F4-3 `dispatch_task()` | 並行 | webhook / command timeout | fail-close for blocking dispatch、audit warning for advisory dispatch | implemented | → UT-F4-007 異常系 | L5 IF §11 |
| EC-F4-008 | F4-4 `load_workflow()` | 例外 | invalid YAML | validation errors、caller が exit `1/2` | partial | → UT-F4-008 異常系 | L6 §4 F4-4 / CARRY-L7-002 |
| EC-F4-009 | F4-5 `scrum_local.verify_loop()` | 例外 | loop_id 不存在 | `ValueError`、DB write なし | implemented | → UT-F4-009 異常系 | L6 §4 F4-5 |
| EC-F4-010 | F4-6 `route_to_forward()` | 境界値 | artifact_links 空配列 | forward 接続は許容。ただし trace warning を残す | implemented | → UT-F4-010 異常系 | L6 §4 F4-6 / L5 internal §11.1 |

### §5.1 境界 critical: illegal transition と recovery

mode transition は作業工程の安全境界である。存在しない遷移を forward fallback で飲み込むと、Incident / Recovery / Retrofit の停止条件をすり抜けるため、明示 mode が不正な場合は fail-close とする。自動判定だけが不明な場合は forward suggestion + warning を許容する。遷移ログ破損時の回復経路は、session state と直近 event から再構築し、再構築不能なら `clarification_required` として人間判断へ戻す。

## §6 F5 orchestration / audit / DB write 境界値・例外ケース

| edge case ID | 対象機能/関数 | 分類 | 入力条件 | 期待動作 (exit code/エラーメッセージ/rollback) | implementation_status | L7 単体テスト pointer | L5/関数仕様 source ref |
|---|---|---|---|---|---|---|---|
| EC-F5-001 | F5-1 `helix codex` | 例外 | `--task` と `--task-file` 両方欠落 | exit `1`、usage、Codex 起動なし | implemented | → UT-F5-001 異常系 | L6 §5 F5-1 |
| EC-F5-002 | F5-1 plan-only guard | 例外 | plan/review task で write sandbox requested | read-only に強制降格、warning log | implemented | → UT-F5-002 異常系 | L6 §5 F5-1 / AGENTS discipline |
| EC-F5-003 | F5-1 approved execution | 例外 | required approval evidence 欠落 | fail-close、exit `2`、task not executed | implemented | → UT-F5-003 異常系 | L5 internal §5.2 |
| EC-F5-004 | F5-2 `helix claude` | 例外 | `--execute` で role template missing | exit `2`、prompt file write なし | implemented | → UT-F5-004 異常系 | L6 §5 F5-2 |
| EC-F5-005 | F5-3 `helix agent fire-mandatory` | 例外 | mandatory slot definition missing | fail-close、exit `2`、audit finding | implemented | → UT-F5-005 異常系 | L6 §5 F5-3 |
| EC-F5-006 | F5-3 agent slots | 並行 | 同一 slot の二重 fire | idempotent guard、二重 audit を防ぐ | implemented | → UT-F5-006 異常系 | L5 internal §5.2 |
| EC-F5-007 | F5-4 `helix doctor --summary --json` | 境界値 | summary 対象 check 0 件 | empty summary JSON、exit `0` | implemented | → UT-F5-007 異常系 | L6 §5 F5-4 |
| EC-F5-008 | F5-5 `run_check_plan_cycle()` | 例外 | DB に循環 graph | finding list、doctor summary は fail-close | implemented | → UT-F5-008 異常系 | L6 §5 F5-5 |
| EC-F5-009 | F5-7 `pretooluse-agent-guard.sh` | 例外 | model family / subagent type 不一致 | exit `2` block、stderr に block reason | implemented | → UT-F5-009 異常系 | L6 §5 F5-7 |
| EC-F5-010 | F5-8 `pretooluse-agent-fire.sh` | 例外 | audit DB write failure | fail-open、stderr debug、main Agent 起動は継続 | implemented | → UT-F5-010 異常系 | L6 §5 F5-8 |
| EC-F5-011 | F5-10 `write_connection()` | 並行 | dual-write 中に split DB 側だけ失敗 | context manager exit で rollback / error。caller は exit `2` | implemented | → UT-F5-011 異常系 | L6 §5 F5-10 |
| EC-F5-012 | F5-11 `record_invocation()` | 並行 | same logical event retry | duplicate insert を上位 unique key で抑止。未実装なら L7 test fail | implemented | → UT-F5-012 異常系 | L6 §5 境界 critical |

### §6.1 境界 critical: DB write / lock / audit continuity

F5 は orchestration と audit の境界であり、部分 write が最も危険である。`write_connection()` の中で dual-write 片側だけが成功した場合、次回の summary / route / gate が異なる state を読むため、context manager は all-or-nothing に近い失敗表現を返す必要がある。rollback 不能な場合は split DB 側を quarantine し、次回 preflight で `contract drift` として fail-close する。

`record_invocation()` と `record_selection()` は insert 専用で非冪等である。retry が発生すると同一 logical event が重複するため、caller 側は event id / request id を固定し、重複時は no-op になる契約を持つべきである。現時点でこの wrapper が不足する場合、L7 carry で duplicate write test を必須化する。

## §7 F6-F10 planned

F6-F10 は governance 拡張領域であり、本書では L7 carry 前提の planned edge case contract として固定する。既存実体があるものは `implemented` / `partial` を正直に残すが、F6-F10 全体の完了判定は planned とする。

| edge case ID | 対象機能/関数 | 分類 | 入力条件 | 期待動作 (exit code/エラーメッセージ/rollback) | implementation_status | L7 単体テスト pointer | L5/関数仕様 source ref |
|---|---|---|---|---|---|---|---|
| EC-F6-001 | F6 homeostasis metrics | 境界値 | gate_pass_rate 分母 0 | 1 とみなさず 0 扱い、health score 保守寄り | planned | → UT-F6-001 異常系 | L6 §6.1 / L5 internal §6.1 |
| EC-F6-002 | F6 threshold state | 境界値 | health score NaN | RED 暫定遷移、status warning | planned | → UT-F6-002 異常系 | L5 internal §6.2 |
| EC-F6-003 | F6 statusLine | 並行 | 30s 未満の状態振動 | debounce suppress、audit metric 更新 | partial | → UT-F6-003 異常系 | L5 internal §6.3 |
| EC-F6-004 | F6 `scheduler_helper.run_due_schedules()` | 境界値 | `max_count < 0` | `ValueError`、schedule state write なし | implemented | → UT-F6-004 異常系 | L6 §6.1 F6-5 |
| EC-F7-001 | F7 evolution fork | 例外 | fork 失敗 | 親 PLAN は変更しない。state=`fail(fork_failed)` | planned | → UT-F7-001 異常系 | L5 internal §7.1 |
| EC-F7-002 | F7 evolution score | 境界値 | score NaN / DRIFT_MAX 超過 | HOLD。drift は 1 に飽和 | planned | → UT-F7-002 異常系 | L5 internal §7.2 |
| EC-F7-003 | F7 promote/deprecate | 並行 | promote 中に target locked | exit `2`、promotion table write なし | partial | → UT-F7-003 異常系 | L6 §6.2 F7-3 |
| EC-F7-004 | F7 `learning_engine.save_recipe()` | 例外 | recipe schema / source invalid | `ValueError`、`.helix/recipes` write なし | implemented | → UT-F7-004 異常系 | L6 §6.2 F7-4 |
| EC-F8-001 | F8 migration validate | 例外 | validate 失敗 | apply 進行不可。exit `2` | planned | → UT-F8-001 異常系 | L5 internal §8.1 |
| EC-F8-002 | F8 migration apply | 例外 | apply 後 verify 失敗 | backup から rollback、rollback_count increment | partial | → UT-F8-002 異常系 | L5 internal §8.1 |
| EC-F8-003 | F8 portable import | 例外 | checksum 不一致 | fail-close、staging しない | partial | → UT-F8-003 異常系 | L5 internal §8.2 |
| EC-F8-004 | F8 `rollback_execute()` | 例外 | confirm token 欠落 / backup path 不存在 | `ValueError` / `RuntimeError`、cutover env は変更しない | implemented | → UT-F8-004 異常系 | L6 §6.3 F8-6 |
| EC-F9-001 | F9 apoptosis | 境界値 | `last_modified` 欠損 | 候補除外。保守側 fail-safe | planned | → UT-F9-001 異常系 | L5 internal §9.1 |
| EC-F9-002 | F9 config | 境界値 | `recent_window_days < 0` | config invalid、即時修正要求、exit `1/2` | planned | → UT-F9-002 異常系 | L5 internal §9.2 |
| EC-F9-003 | F9 autophagy | 並行 | DB lock で retention scan 不能 | max 3 retry、最終 fail-close / quarantine | partial | → UT-F9-003 異常系 | L5 internal §9.3 |
| EC-F9-004 | F9 `recovery_plan_check` | 境界値 | `max_age_days < 0` または recovery plan missing | false / warning、destructive cleanup へ進まない | implemented | → UT-F9-004 異常系 | L6 §6.4 F9-2 |
| EC-F10-001 | F10 namespace conflict | 例外 | 同一 command / namespace 重複 | `reject_adopt`、conflict audit file 保存 | planned | → UT-F10-001 異常系 | L5 internal §10.1 |
| EC-F10-002 | F10 ACL adapter | 例外 | 権限昇格要求 | guard reject、HELIX core 継続 | partial | → UT-F10-002 異常系 | L5 internal §10.2 |
| EC-F10-003 | F10 heartbeat | リソース | heartbeat 3 回失敗 | stop and fallback、coexist status degraded | partial | → UT-F10-003 異常系 | L5 internal §10.2 |

### §7.1 planned 領域の未検出リスク

- F6-F10 は L7 実装前の contract であり、実測 fixture が未整備のため retry 回数、timeout 値、DB lock 復旧時間は実装時に再検証が必要である。
- F8/F10 の cutover / coexist は migration と rollback を伴うため、単体テストだけでは検出できない状態不整合が残る。L8 結合テストで shadow replay / dual-write mismatch を追加検証する。
- F10 ACL adapter は外部 framework ごとの権限モデル差分が残る。新規 adapter 追加時はライセンス・認証・PII を人間確認対象とする。

## §8 implementation_status 集計

### §8.1 edge case 件数

| section | scope | edge case count | implemented | partial | planned |
|---|---|---:|---:|---:|---:|
| §2 | F1 | 10 | 10 | 0 | 0 |
| §3 | F2 | 12 | 11 | 1 | 0 |
| §4 | F3 | 8 | 8 | 0 | 0 |
| §5 | F4 | 10 | 9 | 1 | 0 |
| §6 | F5 | 12 | 12 | 0 | 0 |
| §7 | F6-F10 | 19 | 4 | 7 | 8 |
| total | F1-F10 | 71 | 54 | 9 | 8 |

### §8.2 F1-F5 本体化判定

| feature | status | 根拠 |
|---|---|---|
| F1 | implemented | doctor / vmodel / scaffold / doc-map の fail-close 境界を L7 pointer 付きで固定 |
| F2 | partial included | registry / hook / cycle / lock を固定。F2-7 gate 強制化のみ partial として分離 |
| F3 | implemented | catalog / recommender / dispatcher / debounce hook の fallback と fail-close を固定 |
| F4 | partial included | route / transition / local loop を固定。workflow DSL 全域 schema は partial として分離 |
| F5 | implemented | codex / claude / agent / doctor / DB write / hook audit の異常系を固定 |

### §8.3 深掘り prose 対象リスト

1. §2.1 4 artifact trace 欠損
2. §3.1 registry write の部分失敗
3. §4.1 recommender fallback
4. §5.1 illegal transition と recovery
5. §6.1 DB write / lock / audit continuity
6. §7.1 planned 領域の未検出リスク

### §8.4 L6↔L7 trace 方針

本書の `→ UT-Fx-NNN 異常系` pointer は `docs/v2/L7-test-design/helix-workflows-unit-test-design.md` の異常系 test case ID として定義済 (2026-05-29 作成)。L6↔L7 双方向 trace は解決済で G6 freeze 可。fixture 実体・テストコードは L7 Sprint Step 2 carry。
