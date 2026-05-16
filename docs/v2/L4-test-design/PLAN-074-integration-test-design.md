---
plan_id: PLAN-074
doc_id: PLAN-074-integration-test-design
title: "PLAN-074 結合テスト設計 (HTTP endpoint layer)"
status: maintained
artifact_role: "③ テスト設計 (V-model 4 artifact のうち)"
created: 2026-05-17
status_history:
  - 2026-05-17: 初期作成 (PLAN-075 Phase 3.3b)
owner: PM
related_docs:
  - docs/plans/PLAN-075-vmodel-design-test-mapping.md
  - docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md
  - docs/v2/L4-test-design/PLAN-074-unit-test-design.md
phases: L4
gates: G4
---

> **V-model 4 artifact 位置付け**:
> 本書は ③ テスト設計 artifact。① 設計 (D-API EXT §3.1〜§3.5) と ④ テストコード
> (`cli/lib/tests/test_http_api_*.py`) を双方向 trace で繋ぐ、HTTP endpoint 層の結合テスト設計である。
> 既存 27 cases を本文書で parent 化し、結合テストの期待値・前提条件・mock 方針を固定する。

# PLAN-074 結合テスト設計 (③ D-TEST-DESIGN-INT)

## §1 概要

### 1.1 目的

PLAN-074 (HTTP endpoint 層) の **結合テスト** を設計する。
既存の 27 結合 test cases を本書で網羅し、各 case の前提条件 / 入力 / mock / 期待結果 /
検証項目 / DoD を明確化する。

本書の役割は、実装済みの HTTP API endpoint 群に対して「Flask test client + 実 DB + 主要外部
gate の mock」を用いた結合検証の親文書を提供することである。

### 1.2 V-model 4 artifact 双方向 trace (PLAN-075)

- **対象設計 (①)**: `docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md` §3.1〜§3.5
- **対応実装 (②)**: `cli/lib/http_api/routes/*` / `cli/lib/http_api/server.py`
- **本文書 (③ D-TEST-DESIGN-INT)**: `docs/v2/L4-test-design/PLAN-074-integration-test-design.md`
- **対応テストコード (④ D-TEST-CODE-INT)**: `cli/lib/tests/test_http_api_*.py`
- **検証 gate**: G4 (実装凍結)

### 1.3 case 命名規約

- `I-PUSH-001` ... `I-PUSH-006`: push endpoint 結合
- `I-PR-001`: pr endpoint 結合
- `I-HOOK-001` ... `I-HOOK-005`: hook callback 結合
- `I-AUDIT-001` ... `I-AUDIT-005`: audit endpoint 結合
- `I-TEL-001` ... `I-TEL-005`: telemetry endpoint 結合
- `I-SRV-001` ... `I-SRV-005`: server/framework 層結合

### 1.4 mock 戦略

- `helix.db`: temp dir + `migrate_all` で fresh DB
- `push_gate`: pytest fixture で mock (実 git 操作を行わない)
- `flask test client`: Bearer token + `X-Trace-Id` を fixture から注入
- `sqlite3`: 実 DB を基本にしつつ、異常系で必要な箇所のみ fixture で差し替える
- `request`: header / JSON body / remote_addr の注入は client fixture で統一する

### 1.5 本書の読み方

- §2 は 27 case の全体一覧
- §3 は endpoint 別の詳細設計
- §4 は共通 fixture / 環境前提
- §5 は case 数集計
- §6 は DoD
- §7 は G6 との関係

## §2 case 一覧と既存 test 関数 mapping

### 2.1 全 case 一覧

| case ID | 既存 test 関数 | 検証内容サマリ | gate |
|---|---|---|---|
| I-PUSH-001 | `test_push_trigger_success_records_run_and_audit` | 正常 push 成功 + `automation_runs` INSERT + `audit_log` | G4 |
| I-PUSH-002 | `test_push_trigger_failure_records_failed_run_and_audit` | push gate FAIL 時の failed run 記録 | G4 |
| I-PUSH-003 | `test_push_trigger_requires_bearer_and_trace_id` | 認証 / trace 必須 | G4 |
| I-PUSH-004 | `test_push_trigger_rejects_invalid_plan_id` | plan_id 形式不正拒否 | G4 |
| I-PUSH-005 | `test_push_trigger_rejects_missing_execute_flag` | execute 欠落拒否 | G4 |
| I-PUSH-006 | `test_push_trigger_rejects_non_json_body` | JSON 以外拒否 | G4 |
| I-PR-001 | `test_pr_trigger_success_records_pr_actor` | 正常 pr 成功 + pr actor 記録 | G4 |
| I-HOOK-001 | `test_hook_callback_accepts_pretool_event` | pretool hook 受付 | G4 |
| I-HOOK-002 | `test_hook_callback_accepts_posttool_event` | posttool hook 受付 | G4 |
| I-HOOK-003 | `test_hook_callback_accepts_stop_event` | stop hook 受付 | G4 |
| I-HOOK-004 | `test_hook_callback_accepts_session_start_event` | session_start hook 受付 | G4 |
| I-HOOK-005 | `test_hook_callback_rejects_invalid_hook_kind` | 不正 hook_kind 拒否 | G4 |
| I-AUDIT-001 | `test_audit_log_records_footer_audit` | footer audit 正常登録 | G4 |
| I-AUDIT-002 | `test_audit_log_records_summary_audit` | summary audit 正常登録 | G4 |
| I-AUDIT-003 | `test_audit_log_rejects_missing_run_id` | run_id 欠落拒否 | G4 |
| I-AUDIT-004 | `test_audit_log_rejects_unknown_run_id` | run_id 未存在拒否 | G4 |
| I-AUDIT-005 | `test_audit_log_handles_sqlite_errors` | sqlite 異常時の error mapping | G4 |
| I-TEL-001 | `test_session_telemetry_records_new_session` | telemetry 初回登録 | G4 |
| I-TEL-002 | `test_session_telemetry_is_idempotent_on_conflict` | UNIQUE 衝突時 UPSERT | G4 |
| I-TEL-003 | `test_session_telemetry_rejects_missing_session_id` | session_id 欠落拒否 | G4 |
| I-TEL-004 | `test_session_telemetry_rejects_invalid_cost_type` | cost_usd 型不正拒否 | G4 |
| I-TEL-005 | `test_session_telemetry_handles_sqlite_error` | sqlite 異常時の error mapping | G4 |
| I-SRV-001 | `test_health_endpoint_is_public` | `/health` は公開 | G4 |
| I-SRV-002 | `test_status_endpoint_requires_bearer` | `/api/v1/_status` は認証必須 | G4 |
| I-SRV-003 | `test_status_endpoint_accepts_valid_bearer` | 正 token で status 200 | G4 |
| I-SRV-004 | `test_status_endpoint_rejects_invalid_bearer` | 誤 token 403 | G4 |
| I-SRV-005 | `test_unknown_route_returns_404_envelope` | 未定義 URL の 404 envelope | G4 |

### 2.2 mapping の確認方針

- 各 `I-XXX-YYY` は 1 件の既存 test 関数に 1:1 で対応する
- `test_http_api_*.py` の関数名は、既存 27 case の関係を固定するための参照点である
- 本書では「結合テストとしての目的」を固定し、テストコード側での実装揺れを抑制する

## §3 endpoint 別 結合テスト設計

### §3.1 push trigger 結合テスト (D-API EXT §3.1 対応)

**対象設計**: D-API EXT §3.1 push trigger endpoint  
**対象実装**: `cli/lib/http_api/routes/push_pr.py` (push 部分)  
**対象テストコード**: `cli/lib/tests/test_http_api_push_pr.py` (push 6 cases)

push endpoint の結合テストは、`push_gate.run_all_gates()` の結果と `automation_runs` / `audit_log`
への永続化の整合を確認する。

#### I-PUSH-001 (test_push_trigger_success_records_run_and_audit)

- 前提条件:
  - helix.db が fresh migrate 済み
  - Bearer token が valid
  - `X-Trace-Id` が fixture から注入済み
  - `plan_id` が既存 plan と整合
- 入力:
  - `POST /api/v1/automation/push/{plan_id}/trigger`
  - body = `{ "execute": false, "reason": "integration-check" }`
- mock:
  - `push_gate.run_all_gates()` → 全 gate PASS
  - git 系副作用は発生しない
- 期待結果:
  - 200
  - Envelope `{ success: true, data: { run_id, ok, ... } }`
- 検証項目:
  - `response.data.run_id` が採番されている
  - `automation_runs` テーブルに 1 行 INSERT
  - `audit_log` テーブルに 1 行 INSERT
  - `audit_log.actor` が `"http-push"`
  - `trace_id` が request header と一致
- DoD:
  - G4 で本 case が PASS
  - D-API EXT §3.1 の成功系契約と一致

#### I-PUSH-002 (test_push_trigger_failure_records_failed_run_and_audit)

- 前提条件:
  - fresh migrate 済み
  - valid token / `X-Trace-Id` あり
- 入力:
  - `POST /api/v1/automation/push/{plan_id}/trigger`
  - body = `{ "execute": false, "reason": "force-fail" }`
- mock:
  - `push_gate.run_all_gates()` → 1 つ以上 FAIL
  - 失敗 gate 名は fixture で安定化
- 期待結果:
  - 200
  - Envelope `{ success: true, data: { ok: false, failed_gates: [...] } }`
- 検証項目:
  - `automation_runs` に failed status の行が 1 行 INSERT
  - `audit_log` に 1 行 INSERT
  - failed gate 名が response と DB の双方で一致
- DoD:
  - failed run が観測可能
  - gate FAIL が 500 に化けない

#### I-PUSH-003 (test_push_trigger_requires_bearer_and_trace_id)

- 前提条件:
  - fresh migrate 済み
- 入力:
  - Bearer なし、または `X-Trace-Id` なしで trigger
- mock:
  - `push_gate` は呼ばれない
- 期待結果:
  - Bearer なし: 401 / 403 の契約に従う
  - trace なし: 400 もしくは明示的 error envelope
- 検証項目:
  - endpoint へ到達する前に拒否される
  - DB 書き込みがない
  - audit log が増えない
- DoD:
  - 認証と trace 注入の前提が守られる

#### I-PUSH-004 (test_push_trigger_rejects_invalid_plan_id)

- 前提条件:
  - fresh migrate 済み
- 入力:
  - plan_id が空文字、または不正形式
- mock:
  - なし
- 期待結果:
  - 400
  - validation error envelope
- 検証項目:
  - route で reject される
  - `push_gate.run_all_gates()` が呼ばれない
  - DB 変更なし
- DoD:
  - path parameter validation が維持される

#### I-PUSH-005 (test_push_trigger_rejects_missing_execute_flag)

- 前提条件:
  - fresh migrate 済み
- 入力:
  - body から `execute` 欠落
- mock:
  - なし
- 期待結果:
  - 400
- 検証項目:
  - request validation error
  - gate 実行なし
- DoD:
  - request schema が維持される

#### I-PUSH-006 (test_push_trigger_rejects_non_json_body)

- 前提条件:
  - fresh migrate 済み
- 入力:
  - JSON 以外の body
- mock:
  - なし
- 期待結果:
  - 400
- 検証項目:
  - parser error が envelope へ正規化される
  - DB 書き込みなし
- DoD:
  - content-type 前提が固定される

### §3.2 pr trigger 結合テスト (D-API EXT §3.2)

**対象設計**: D-API EXT §3.2 pr trigger endpoint  
**対象実装**: `cli/lib/http_api/routes/push_pr.py` (pr 部分)  
**対象テストコード**: `cli/lib/tests/test_http_api_push_pr.py` (pr 1 case)

#### I-PR-001 (test_pr_trigger_success_records_pr_actor)

- 前提条件:
  - fresh migrate 済み
  - valid token / `X-Trace-Id` あり
  - pull request 由来の `actor` が fixture で設定済み
- 入力:
  - `POST /api/v1/automation/pr/{plan_id}/trigger`
  - body = `{ "execute": false, "reason": "integration-check" }`
- mock:
  - `push_gate.run_all_gates()` → PASS
  - PR 固有 actor 解決は fixture で安定化
- 期待結果:
  - 200
  - Envelope `{ success: true, data: { run_id, ok, ... } }`
- 検証項目:
  - `automation_runs` に 1 行 INSERT
  - `audit_log.actor` が `"http-pr"`
  - `trace_id` が request header と一致
- DoD:
  - pr の成功系結合が PASS
  - pr 固有の異常系 (400/404/409) は単体設計に委譲済み

### §3.3 hook callback 結合テスト (D-API EXT §3.3、5 case)

**対象設計**: D-API EXT §3.3 hook callback endpoint  
**対象実装**: `cli/lib/http_api/routes/hooks.py`  
**対象テストコード**: `cli/lib/tests/test_http_api_hooks.py` (5 cases)

hook callback の結合テストは、hook_kind ごとの受理と、DB への hook event 記録の整合を確認する。

#### I-HOOK-001 (test_hook_callback_accepts_pretool_event)

- 前提条件:
  - fresh migrate 済み
  - valid token / trace あり
- 入力:
  - `POST /api/v1/hook/pretool`
  - body に `hook_kind=pretool`
- mock:
  - `helix_db` の記録先は実 DB
- 期待結果:
  - 200
  - success envelope
- 検証項目:
  - hook event が 1 件 INSERT
  - path と body の kind が一致
- DoD:
  - pretool hook が受理される

#### I-HOOK-002 (test_hook_callback_accepts_posttool_event)

- 前提条件:
  - fresh migrate 済み
- 入力:
  - `POST /api/v1/hook/posttool`
- mock:
  - なし
- 期待結果:
  - 200
- 検証項目:
  - hook event 1 件 INSERT
  - kind が `posttool`
- DoD:
  - posttool hook が受理される

#### I-HOOK-003 (test_hook_callback_accepts_stop_event)

- 前提条件:
  - fresh migrate 済み
- 入力:
  - `POST /api/v1/hook/stop`
- mock:
  - なし
- 期待結果:
  - 200
- 検証項目:
  - stop hook が記録される
  - trace が保存される
- DoD:
  - stop hook が受理される

#### I-HOOK-004 (test_hook_callback_accepts_session_start_event)

- 前提条件:
  - fresh migrate 済み
- 入力:
  - `POST /api/v1/hook/session_start`
- mock:
  - なし
- 期待結果:
  - 200
- 検証項目:
  - session_start が 1 件 INSERT
  - session meta が保持される
- DoD:
  - session_start hook が受理される

#### I-HOOK-005 (test_hook_callback_rejects_invalid_hook_kind)

- 前提条件:
  - fresh migrate 済み
- 入力:
  - invalid hook_kind
- mock:
  - なし
- 期待結果:
  - 400
- 検証項目:
  - DB 書き込みなし
  - error envelope 正規化
- DoD:
  - 不正 hook_kind が拒否される

### §3.4 audit endpoint 結合テスト (D-API EXT §3.4、5 case)

**対象設計**: D-API EXT §3.4 audit endpoint  
**対象実装**: `cli/lib/http_api/routes/audit.py`  
**対象テストコード**: `cli/lib/tests/test_http_api_audit.py` (5 cases)

audit endpoint の結合テストは、audit log の永続化と error mapping を確認する。

#### I-AUDIT-001 (test_audit_log_records_footer_audit)

- 前提条件:
  - fresh migrate 済み
  - valid token / trace あり
- 入力:
  - `POST /api/v1/audit/footer`
  - footer audit payload
- mock:
  - 実 DB で記録
- 期待結果:
  - 200
  - acknowledged response
- 検証項目:
  - `audit_log` に 1 行 INSERT
  - `audit_kind` が `footer`
- DoD:
  - footer audit が記録できる

#### I-AUDIT-002 (test_audit_log_records_summary_audit)

- 前提条件:
  - fresh migrate 済み
- 入力:
  - `POST /api/v1/audit/summary`
- mock:
  - なし
- 期待結果:
  - 200
- 検証項目:
  - summary audit が 1 行 INSERT
  - `trace_id` が保存される
- DoD:
  - summary audit が記録できる

#### I-AUDIT-003 (test_audit_log_rejects_missing_run_id)

- 前提条件:
  - fresh migrate 済み
- 入力:
  - run_id 欠落 body
- mock:
  - なし
- 期待結果:
  - 400
- 検証項目:
  - DB 書き込みなし
  - request validation error
- DoD:
  - 必須入力の欠落が拒否される

#### I-AUDIT-004 (test_audit_log_rejects_unknown_run_id)

- 前提条件:
  - fresh migrate 済み
- 入力:
  - 存在しない run_id
- mock:
  - `helix_db` の参照は実 DB
- 期待結果:
  - 404
- 検証項目:
  - run が存在しないことを検証
  - audit row は増えない
- DoD:
  - run 存在性チェックが有効

#### I-AUDIT-005 (test_audit_log_handles_sqlite_errors)

- 前提条件:
  - fresh migrate 済み
- 入力:
  - 正常な request body
- mock:
  - `sqlite3.Error` / `IntegrityError` を fixture で発生
- 期待結果:
  - 500 もしくは契約上の error envelope
- 検証項目:
  - 例外が leak しない
  - error envelope が返る
- DoD:
  - sqlite 異常時の契約が固定される

### §3.5 telemetry endpoint 結合テスト (D-API EXT §3.5、5 case)

**対象設計**: D-API EXT §3.5 telemetry endpoint  
**対象実装**: `cli/lib/http_api/routes/telemetry.py`  
**対象テストコード**: `cli/lib/tests/test_http_api_telemetry.py` (5 cases)

telemetry endpoint の結合テストは、session ごとの UPSERT と idempotency を確認する。

#### I-TEL-001 (test_session_telemetry_records_new_session)

- 前提条件:
  - fresh migrate 済み
  - valid token / trace あり
- 入力:
  - `POST /api/v1/telemetry/session`
  - 正常 body
- mock:
  - 実 DB
- 期待結果:
  - 200
  - UPSERT の初回 INSERT
- 検証項目:
  - telemetry row が 1 件作成される
  - `session_id` が保存される
- DoD:
  - 新規 telemetry が記録される

#### I-TEL-002 (test_session_telemetry_is_idempotent_on_conflict)

- 前提条件:
  - fresh migrate 済み
  - 同一 `session_id` を 2 回送る
- 入力:
  - 同じ session payload を再送
- mock:
  - UNIQUE conflict を実 DB で再現
- 期待結果:
  - 200
  - idempotent UPSERT
- 検証項目:
  - row が重複しない
  - 累積値が期待通り更新される
- DoD:
  - telemetry が冪等である

#### I-TEL-003 (test_session_telemetry_rejects_missing_session_id)

- 前提条件:
  - fresh migrate 済み
- 入力:
  - session_id 欠落
- mock:
  - なし
- 期待結果:
  - 400
- 検証項目:
  - request validation error
  - DB 書き込みなし
- DoD:
  - session_id 必須が守られる

#### I-TEL-004 (test_session_telemetry_rejects_invalid_cost_type)

- 前提条件:
  - fresh migrate 済み
- 入力:
  - cost_usd に string 等の不正型
- mock:
  - なし
- 期待結果:
  - 400
- 検証項目:
  - 型検証が生きている
  - telemetry row が作成されない
- DoD:
  - cost 型の契約が固定される

#### I-TEL-005 (test_session_telemetry_handles_sqlite_error)

- 前提条件:
  - fresh migrate 済み
- 入力:
  - 正常 body
- mock:
  - sqlite3 error を fixture で発生
- 期待結果:
  - 500 もしくは契約上の error envelope
- 検証項目:
  - 例外が leak しない
  - error envelope が返る
- DoD:
  - sqlite 異常時の契約が固定される

### §3.6 server/framework 結合テスト (5 case)

**対象設計**: D-API EXT §共通 framework  
**対象実装**: `cli/lib/http_api/server.py`  
**対象テストコード**: `cli/lib/tests/test_http_api_server.py` (5 cases)

server/framework の結合テストは、公開 endpoint と認証 endpoint の境界、および 404 / envelope
の一貫性を確認する。

#### I-SRV-001 (test_health_endpoint_is_public)

- 前提条件:
  - app factory 起動済み
  - Bearer なし
- 入力:
  - `GET /health`
- mock:
  - なし
- 期待結果:
  - 200
- 検証項目:
  - health が公開 endpoint として到達する
  - auth middleware を通らない
- DoD:
  - health は無認証で利用できる

#### I-SRV-002 (test_status_endpoint_requires_bearer)

- 前提条件:
  - app factory 起動済み
- 入力:
  - `GET /api/v1/_status` with Bearer なし
- mock:
  - なし
- 期待結果:
  - 403
- 検証項目:
  - 認証なしで拒否される
  - status body は漏れない
- DoD:
  - _status に認証が要求される

#### I-SRV-003 (test_status_endpoint_accepts_valid_bearer)

- 前提条件:
  - app factory 起動済み
  - valid token fixture あり
- 入力:
  - `GET /api/v1/_status`
- mock:
  - なし
- 期待結果:
  - 200
- 検証項目:
  - status envelope が返る
  - 監視用途の metadata が含まれる
- DoD:
  - 正 token で status 到達

#### I-SRV-004 (test_status_endpoint_rejects_invalid_bearer)

- 前提条件:
  - app factory 起動済み
- 入力:
  - 誤 token で `_status`
- mock:
  - なし
- 期待結果:
  - 403
- 検証項目:
  - invalid token が拒否される
  - DB 書き込みなし
- DoD:
  - 認証失敗が正しく拒否される

#### I-SRV-005 (test_unknown_route_returns_404_envelope)

- 前提条件:
  - app factory 起動済み
- 入力:
  - 未定義 URL
- mock:
  - なし
- 期待結果:
  - 404
- 検証項目:
  - error envelope が返る
  - framework 例外が露出しない
- DoD:
  - 404 が統一形式で返る

## §4 共通 fixture / 環境前提

- `helix.db`: temp dir + `migrate_all v27` まで
- token: pytest fixture (`HELIX_HTTP_API_TOKEN=test_token`)
- Flask test client: `server.create_app()` + `test_client()`
- `X-Trace-Id`: すべての endpoint で fixture から注入
- database lifecycle: 各 case で fresh DB を作成し、case 間の状態共有を避ける
- error envelope: 例外は endpoint 層で正規化し、stack trace を response に出さない
- logging: audit / telemetry は response と DB の双方で traceable にする

## §5 case 数集計

| 区分 | 既存 case 数 | 新規追加 (もしあれば) |
|---|---|---|
| push | 6 | 0 |
| pr | 1 | 0 |
| hook | 5 | 0 |
| audit | 5 | 0 |
| telemetry | 5 | 0 |
| server | 5 | 0 |
| **合計** | **27** | **0** |

## §6 DoD (Definition of Done)

- 全 27 case が D-API EXT §3.X への双方向 reference を持つ
- 各 case に対する ④ テストコード (`test_http_api_*.py`) の関数名 mapping が §2 表で確定
- push / pr / hook / audit / telemetry / server の 6 区分が case 数集計で一致
- G4 実装凍結 gate で本文書記載の 27 case 全 PASS が必須条件
- 実 DB + fixture mock の責務分離が本書どおり維持される

## §7 G6 (RC 判定) との関係

総合テスト (E2E) は `PLAN-074-system-test-design.md` で扱う。
本書 (結合) は G4 までを対象とし、G6 では総合設計が主となる。

結合テスト設計としての責務は、HTTP endpoint 層の契約を固定し、E2E へ渡す前提条件を
明示することにある。

## §8 trace check list

- [ ] ① 設計 → ③ テスト設計 の reference を保持
- [ ] ③ テスト設計 → ④ テストコード の mapping を保持
- [ ] 27 case の総数が §2 と §5 で一致
- [ ] 各 endpoint の case 数が T301 報告と一致
- [ ] 未完了注記が残っていない
