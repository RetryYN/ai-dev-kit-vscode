---
plan_id: PLAN-080
doc_id: PLAN-080-integration-test-design
title: "PLAN-080 結合テスト設計 (harness 3 軸 Pull/Push/Audit)"
status: draft
artifact_role: "③ テスト設計 (V-model 4 artifact のうち)"
created: 2026-05-17
status_history:
  - 2026-05-17: 初期作成 (PLAN-080 Sprint .2b)
owner: PM
related_docs:
  - docs/plans/PLAN-080-harness-dynamic-monitoring.md
  - docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md (§13 対象 ① 設計)
  - docs/v2/L4-test-design/PLAN-078-integration-test-design.md (姉妹 ③)
phases: L4
gates: G4
---

> **V-model 4 artifact 位置付け** (PLAN-075):
> 本書は ③ テスト設計 artifact。① 設計 (D-DB EXT §13 + PLAN-080 §3.1-§3.3) と
> ④ テストコード (`cli/lib/tests/test_harness_monitor_integration.py` + `tests/harness-hooks.bats`)
> を双方向 trace で繋ぐ独立文書である。

# PLAN-080 結合テスト設計 (③ D-TEST-DESIGN-INT)

## §1 概要

### 1.1 目的

PLAN-080 (Harness Dynamic Monitoring) の **結合テスト** を設計する。

本書の対象は、`helix harness status` による Pull、`.claude/hooks/pretooluse-codex-slot-check.sh`
による Push、`.claude/hooks/sessionstart-harness-summary.sh` による Audit、
および `harness_check_events` ↔ `agent_slots` の FK 連携と payload JSON の保存・復元である。
結合層として「CLI / hook / DB の 1 本の起動経路が、監視イベントの記録と可視化を正しく引き回すか」を検証する。

### 1.2 スコープ

対象は以下の 5 領域である。

1. `helix harness status` CLI / `helix harness status --json`
2. `.claude/hooks/pretooluse-codex-slot-check.sh` の hook 動作
3. `.claude/hooks/sessionstart-harness-summary.sh` の hook 動作
4. `harness_check_events` ↔ `agent_slots` FK 連携
5. payload JSON のロード / 保存

対象外は以下である。

- `harness_monitor.py` の純粋関数単体整合
- D-DB migration の個別 SQL 文の構文差分
- 実際の Claude Code / Codex 外部呼び出し
- 既存 PLAN 群の業務ロジック検証

### 1.3 V-model 4 artifact 双方向 trace

- **対象設計 (①)**: `docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md` §13
- **対応実装 (②)**: `cli/lib/harness_monitor.py` / `cli/helix-harness` / `.claude/hooks/pretooluse-codex-slot-check.sh` / `.claude/hooks/sessionstart-harness-summary.sh`
- **本文書 (③ D-TEST-DESIGN-INT)**: `docs/v2/L4-test-design/PLAN-080-integration-test-design.md`
- **対応テストコード (④ D-TEST-CODE-INT)**: `cli/lib/tests/test_harness_monitor_integration.py` / `tests/harness-hooks.bats`
- **検証 gate**: G4 (実装凍結)

### 1.4 case 命名規約

結合テスト case は次の接頭辞で管理する。

- `I-PULL-001` 〜: `helix harness status` / `--json`
- `I-PUSH-001` 〜: `pretooluse` hook
- `I-AUDIT-001` 〜: `sessionstart` hook
- `I-FK-001` 〜: `harness_check_events` ↔ `agent_slots`
- `I-PAYLOAD-001` 〜: payload JSON serialize / deserialize

### 1.5 mock 戦略

結合テストでは、実 DB と外部副作用の境界を明確に分ける。

- `helix.db`: temp dir に生成し、`migrate_all` で v30 まで適用する
- `agent_slots`: PLAN-078 前提の fixture を用意し、事前 INSERT する
- `hook`: 直接実行で stdin / stdout / stderr をシミュレートする
- `system-reminder`: stderr 出力を grep で検証する
- `payload`: JSON を文字列として保存し、復元側で構造一致を確認する

### 1.6 本書の読み方

- §2 は case 一覧
- §3 は領域別の詳細設計
- §4 は共通 fixture
- §5 は case 数集計
- §6 は DoD
- §7 は 4 artifact 双方向 trace 表

## §2 case 一覧

### 2.1 全 case 一覧

| case ID | 既存 / 予定 test 関数 | 検証内容サマリ | 対象 |
|---|---|---|---|
| I-PULL-001 | `test_harness_status_table_includes_active_slots` | status table に active slot を表示 | Pull |
| I-PULL-002 | `test_harness_status_table_includes_running_tasks` | running task 一覧を表示 | Pull |
| I-PULL-003 | `test_harness_status_table_includes_deferred_findings` | 未消化 deferred-findings を表示 | Pull |
| I-PULL-004 | `test_harness_status_table_includes_skipped_skill_chain` | skip した skill chain を表示 | Pull |
| I-PULL-005 | `test_harness_status_json_exposes_active_slot_count` | `--json` で active_slot_count を返す | Pull |
| I-PULL-006 | `test_harness_status_json_exposes_parallel_ratio` | `--json` で parallel_ratio を返す | Pull |
| I-PULL-007 | `test_harness_status_json_exposes_recent_events` | `--json` で recent_events を返す | Pull |
| I-PULL-008 | `test_harness_status_json_stable_schema` | JSON schema の key 順と型を固定 | Pull |
| I-PUSH-001 | `test_pretooluse_emits_system_reminder_for_helix_codex` | `helix codex` 起動を捕捉して reminder 出力 | Push |
| I-PUSH-002 | `test_pretooluse_emits_warning_when_active_slot_threshold_reached` | active slot 閾値到達時 warning | Push |
| I-PUSH-003 | `test_pretooluse_emits_reference_doc_reminder_for_wbs_id` | `--wbs-id` + `--reference-doc` 不足 warning | Push |
| I-PUSH-004 | `test_pretooluse_does_not_emit_for_non_helix_commands` | 非対象 command では無出力 | Push |
| I-PUSH-005 | `test_pretooluse_handles_json_status_lookup_failure` | status lookup 失敗時 fallback | Push |
| I-PUSH-006 | `test_pretooluse_records_push_event_into_harness_check_events` | Push event を DB に記録 | Push |
| I-AUDIT-001 | `test_sessionstart_emits_previous_session_summary` | 前 session summary を表示 | Audit |
| I-AUDIT-002 | `test_sessionstart_includes_release_miss_count` | release 漏れ件数を含める | Audit |
| I-AUDIT-003 | `test_sessionstart_includes_carry_findings_summary` | carry findings summary を含める | Audit |
| I-AUDIT-004 | `test_sessionstart_records_audit_event_into_harness_check_events` | Audit event を DB に記録 | Audit |
| I-FK-001 | `test_record_event_links_to_agent_slot_when_slot_exists` | `related_slot_id` FK 接続 | FK |
| I-FK-002 | `test_record_event_rejects_missing_agent_slot_when_fk_required` | FK 必須経路で欠落拒否 | FK |
| I-FK-003 | `test_record_event_allows_nullable_related_slot_for_pull_only` | nullable 経路を保持 | FK |
| I-PAYLOAD-001 | `test_record_event_preserves_payload_json_text` | payload JSON を文字列保存 | payload |
| I-PAYLOAD-002 | `test_record_event_round_trips_payload_structure` | payload の復元構造一致 | payload |
| I-PAYLOAD-003 | `test_list_recent_events_parses_payload_json` | recent event 取得時に JSON を parse | payload |
| I-PAYLOAD-004 | `test_get_active_status_merges_payload_fields` | active status に payload をマージ | payload |

### 2.2 総 case 数

本書は 24 case を設計する。
Pull を 8 case、Push を 6 case、Audit を 4 case、FK を 3 case、payload を 4 case で分担し、
3 軸の可視化と保存系を厚く確認する。

## §3 シナリオ別詳細設計

### 3.1 Pull: `helix harness status` CLI

**対象設計**: D-DB EXT §13.1 / §13.5 / §13.7  
**対象実装**: `cli/lib/harness_monitor.py` / `cli/helix-harness`  
**対象テストコード**: `cli/lib/tests/test_harness_monitor_integration.py`

#### I-PULL-001 `test_harness_status_table_includes_active_slots`

- 前提:
  - `harness_check_events` と `agent_slots` が v30 / v28 まで migrate 済みである
  - active slot fixture が 2 件以上ある
- 入力:
  - `helix harness status`
- 期待出力:
  - `Active Slots` セクションに slot が表示される
- 検証ポイント:
  - `slot_count` が active 件数と一致する
  - `plan_id` / `related_slot_id` の trace が壊れない
- DoD:
  - status table が active 起点で読める

#### I-PULL-002 `test_harness_status_table_includes_running_tasks`

- 前提:
  - running task fixture がある
- 入力:
  - `helix harness status`
- 期待出力:
  - `Running Background Tasks` セクションが出る
- 検証ポイント:
  - `task_name` / `started_at` が表示される
- DoD:
  - 実行中 task の可視化が崩れない

#### I-PULL-003 `test_harness_status_table_includes_deferred_findings`

- 前提:
  - open deferred finding fixture がある
- 入力:
  - `helix harness status`
- 期待出力:
  - `未消化 Deferred Findings` セクションが出る
- 検証ポイント:
  - `severity` と `finding_id` が出力される
- DoD:
  - carry 対象の確認漏れを抑止できる

#### I-PULL-004 `test_harness_status_table_includes_skipped_skill_chain`

- 前提:
  - skip された skill chain の記録がある
- 入力:
  - `helix harness status`
- 期待出力:
  - `skip した Skill Chain` セクションが出る
- 検証ポイント:
  - skip 回数が 0 でないときのみ表示される
- DoD:
  - 取りこぼしの可視化が安定する

#### I-PULL-005 `test_harness_status_json_exposes_active_slot_count`

- 前提:
  - active slot fixture がある
- 入力:
  - `helix harness status --json`
- 期待出力:
  - `active_slot_count` が JSON に含まれる
- 検証ポイント:
  - 数値型で返る
- DoD:
  - Push / Audit が参照できる

#### I-PULL-006 `test_harness_status_json_exposes_parallel_ratio`

- 前提:
  - 複数 slot / serial 並行の混在 fixture がある
- 入力:
  - `helix harness status --json`
- 期待出力:
  - `parallel_ratio` と `peak_parallel` が返る
- 検証ポイント:
  - 0.0〜1.0 の範囲が保たれる
- DoD:
  - 並列遵守率を機械可読で扱える

#### I-PULL-007 `test_harness_status_json_exposes_recent_events`

- 前提:
  - recent events が存在する
- 入力:
  - `helix harness status --json`
- 期待出力:
  - `recent_events` が JSON 配列で返る
- 検証ポイント:
  - pull / push / audit を区別できる
- DoD:
  - 最近の逸脱を 1 回の pull で把握できる

#### I-PULL-008 `test_harness_status_json_stable_schema`

- 前提:
  - 3 軸の情報が一通り存在する
- 入力:
  - `helix harness status --json`
- 期待出力:
  - schema の top-level key が固定される
- 検証ポイント:
  - key 追加 / 削除が意図せず起きない
- DoD:
  - downstream hook で壊れにくい

### 3.2 Push: `.claude/hooks/pretooluse-codex-slot-check.sh`

**対象設計**: D-DB EXT §13.2 / §13.4 / PLAN-080 §3.2  
**対象実装**: `.claude/hooks/pretooluse-codex-slot-check.sh`  
**対象テストコード**: `tests/harness-hooks.bats`

#### I-PUSH-001 `test_pretooluse_emits_system_reminder_for_helix_codex`

- 前提:
  - `helix codex` を含む tool input がある
  - `helix harness status --json` が成功する
- 入力:
  - hook を stdin / env 付きで直接実行する
- 期待出力:
  - stderr に `system-reminder` が出る
- 検証ポイント:
  - `helix codex` 起動を捕捉する
- DoD:
  - Push の最小経路が通る

#### I-PUSH-002 `test_pretooluse_emits_warning_when_active_slot_threshold_reached`

- 前提:
  - active slot 数が閾値以上である
- 入力:
  - hook を直接実行する
- 期待出力:
  - `8 並列` に関する warning が stderr に出る
- 検証ポイント:
  - threshold 到達時のみ出力される
- DoD:
  - 過剰な警告を避けつつ抑止できる

#### I-PUSH-003 `test_pretooluse_emits_reference_doc_reminder_for_wbs_id`

- 前提:
  - tool input に `--wbs-id` が含まれる
  - `--reference-doc` が含まれない
- 入力:
  - hook を直接実行する
- 期待出力:
  - `system-reminder` で `--reference-doc` 推奨が出る
- 検証ポイント:
  - `wbs-id` 単独を機械的に警告できる
- DoD:
  - PLAN 運用の抜けを減らせる

#### I-PUSH-004 `test_pretooluse_does_not_emit_for_non_helix_commands`

- 前提:
  - hook 対象外 command である
- 入力:
  - `npm test` 等の非対象 input
- 期待出力:
  - stderr に reminder が出ない
- 検証ポイント:
  - 誤検知がない
- DoD:
  - ノイズが増えない

#### I-PUSH-005 `test_pretooluse_handles_json_status_lookup_failure`

- 前提:
  - `helix harness status --json` が失敗する stub である
- 入力:
  - hook を直接実行する
- 期待出力:
  - hook 全体は落ちず、限定的 warning で継続する
- 検証ポイント:
  - failure fallback がある
- DoD:
  - hook 失敗で全体操作を止めない

#### I-PUSH-006 `test_pretooluse_records_push_event_into_harness_check_events`

- 前提:
  - `harness_check_events` が空である
- 入力:
  - Push 該当 input を hook に与える
- 期待出力:
  - `event_kind='push'` の record が追加される
- 検証ポイント:
  - `user_visible=1` が保存される
- DoD:
  - warning の監査 trace が残る

### 3.3 Audit: `.claude/hooks/sessionstart-harness-summary.sh`

**対象設計**: D-DB EXT §13.3 / §13.6 / §13.7  
**対象実装**: `.claude/hooks/sessionstart-harness-summary.sh`  
**対象テストコード**: `tests/harness-hooks.bats`

#### I-AUDIT-001 `test_sessionstart_emits_previous_session_summary`

- 前提:
  - 前 session の summary 対象イベントが存在する
- 入力:
  - session start hook を直接実行する
- 期待出力:
  - previous session summary が stdout または stderr に出る
- 検証ポイント:
  - summary が 1 回だけ表示される
- DoD:
  - セッション跨ぎの可視化ができる

#### I-AUDIT-002 `test_sessionstart_includes_release_miss_count`

- 前提:
  - release 漏れ相当の event がある
- 入力:
  - session start hook を直接実行する
- 期待出力:
  - release miss count が含まれる
- 検証ポイント:
  - 件数が 0 のときは抑制できる
- DoD:
  - 放置 slot の残数が分かる

#### I-AUDIT-003 `test_sessionstart_includes_carry_findings_summary`

- 前提:
  - carry findings が存在する
- 入力:
  - session start hook を直接実行する
- 期待出力:
  - carry findings summary が表示される
- 検証ポイント:
  - `severity` ごとにまとめられる
- DoD:
  - 次 session での着手判断に使える

#### I-AUDIT-004 `test_sessionstart_records_audit_event_into_harness_check_events`

- 前提:
  - `harness_check_events` が空である
- 入力:
  - session start hook を直接実行する
- 期待出力:
  - `event_kind='audit'` の record が追加される
- 検証ポイント:
  - `session_id` と `payload` が保存される
- DoD:
  - Audit の履歴が残る

### 3.4 `harness_check_events` ↔ `agent_slots` FK 連携

**対象設計**: D-DB EXT §13.1.1 / §13.2 / §13.7  
**対象実装**: `cli/lib/harness_monitor.py`
**対象テストコード**: `cli/lib/tests/test_harness_monitor_integration.py`

#### I-FK-001 `test_record_event_links_to_agent_slot_when_slot_exists`

- 前提:
  - `agent_slots` に対象 slot が存在する
- 入力:
  - `record_event(..., related_slot_id=<id>)`
- 期待出力:
  - `related_slot_id` が保存される
- 検証ポイント:
  - FK が存在する slot に接続される
- DoD:
  - fire 由来 event の trace が切れない

#### I-FK-002 `test_record_event_rejects_missing_agent_slot_when_fk_required`

- 前提:
  - FK 必須の経路である
- 入力:
  - `related_slot_id` が存在しない id
- 期待出力:
  - validation error もしくは DB error
- 検証ポイント:
  - orphan event が残らない
- DoD:
  - 監査 trace の整合性が保たれる

#### I-FK-003 `test_record_event_allows_nullable_related_slot_for_pull_only`

- 前提:
  - Pull のみの event である
- 入力:
  - `related_slot_id=None`
- 期待出力:
  - event が保存される
- 検証ポイント:
  - nullable 経路が許容される
- DoD:
  - Pull 単体の status 取得が壊れない

### 3.5 payload JSON serialize / deserialize

**対象設計**: D-DB EXT §13.2 / §13.5 / §13.6  
**対象実装**: `cli/lib/harness_monitor.py`  
**対象テストコード**: `cli/lib/tests/test_harness_monitor_integration.py`

#### I-PAYLOAD-001 `test_record_event_preserves_payload_json_text`

- 前提:
  - dict payload fixture がある
- 入力:
  - `record_event(..., payload=<dict>)`
- 期待出力:
  - DB 上では JSON 文字列として保存される
- 検証ポイント:
  - key / value が壊れない
- DoD:
  - audit payload が再利用できる

#### I-PAYLOAD-002 `test_record_event_round_trips_payload_structure`

- 前提:
  - ネストした payload fixture がある
- 入力:
  - 保存後に read back する
- 期待出力:
  - 元の構造と一致する
- 検証ポイント:
  - list / nested object の型が保持される
- DoD:
  - hook ごとの詳細 context を保持できる

#### I-PAYLOAD-003 `test_list_recent_events_parses_payload_json`

- 前提:
  - recent event に JSON payload がある
- 入力:
  - `list_recent_events(days=1)`
- 期待出力:
  - `payload` が dict として返る
- 検証ポイント:
  - parse 失敗時の例外が明確
- DoD:
  - CLI / hook で直読できる

#### I-PAYLOAD-004 `test_get_active_status_merges_payload_fields`

- 前提:
  - active status に payload 由来の補助項目がある
- 入力:
  - `get_active_status(session_id=...)`
- 期待出力:
  - status dict に payload fields が反映される
- 検証ポイント:
  - `slot_count` / `parallel_ratio` と payload が共存する
- DoD:
  - Pull 出力の summary が豊かになる

## §4 共通 fixture

### 4.1 DB fixture

- `temp dir` 配下に `helix.db` を作成する
- `migrate_all` で v30 まで適用する
- `agent_slots` は PLAN-078 前提で事前 INSERT する
- `harness_check_events` は空状態から開始する

### 4.2 hook fixture

- `stdin` で tool input を渡す
- `stdout` は table / summary 表示を検証する
- `stderr` は `system-reminder` と warning を grep する
- `env` は `HELIX_SESSION_ID` / `HELIX_PLAN_ID` を固定する

### 4.3 payload fixture

- 1 層 JSON: `{ "slot_count": 3, "parallel_ratio": 0.5 }`
- 2 層 JSON: `{ "current": { "slot_count": 3 }, "recent": [ ... ] }`
- 文字列化後の key 順は保存層で不定とし、parse 後の構造一致で確認する

## §5 case 数集計

### 5.1 軸別内訳

| 軸 | case 数 | 主対象 |
|---|---:|---|
| Pull | 8 | `helix harness status` / `--json` |
| Push | 6 | `pretooluse-codex-slot-check.sh` |
| Audit | 4 | `sessionstart-harness-summary.sh` |
| FK | 3 | `harness_check_events` ↔ `agent_slots` |
| payload | 4 | JSON serialize / deserialize |

### 5.2 規模判定

本書は合計 24 case であり、L4 の結合テスト設計として中規模である。
3 軸 CLI/hook と DB 連携を跨ぐため、単体設計よりも fixture 設計の重みが大きい。

## §6 DoD

- [ ] `I-PULL-001` 〜 `I-PULL-008` が Pull 経路の期待を網羅する
- [ ] `I-PUSH-001` 〜 `I-PUSH-006` が Push 経路の reminder / warning / event 記録を網羅する
- [ ] `I-AUDIT-001` 〜 `I-AUDIT-004` が Audit 経路の summary / event 記録を網羅する
- [ ] `I-FK-001` 〜 `I-FK-003` が `harness_check_events` ↔ `agent_slots` の FK 連携を網羅する
- [ ] `I-PAYLOAD-001` 〜 `I-PAYLOAD-004` が payload JSON の保存 / 復元を網羅する
- [ ] ③ テスト設計と ④ テストコードの双方向 trace が明記されている
- [ ] 参照先に対するリンク整合が保たれている

## §7 4 artifact 双方向 trace

| Artifact | 担当層 | 想定パス |
|---|---|---|
| ① 設計 | L3 詳細設計 | `docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md` §13 harness_check_events |
| ② 実装コード | L4 実装 | `cli/lib/harness_monitor.py` + `cli/helix-harness` + `.claude/hooks/pretooluse-codex-slot-check.sh` + `.claude/hooks/sessionstart-harness-summary.sh` |
| ③ テスト設計 | L4 設計 | `docs/v2/L4-test-design/PLAN-080-integration-test-design.md` |
| ④ テストコード | L4 実装 | `cli/lib/tests/test_harness_monitor_integration.py` + `tests/harness-hooks.bats` |
