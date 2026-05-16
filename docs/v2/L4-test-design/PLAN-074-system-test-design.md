---
plan_id: PLAN-074
doc_id: PLAN-074-system-test-design
title: "PLAN-074 総合テスト設計 (HTTP endpoint 層 / E2E)"
status: draft
artifact_role: "③ テスト設計 (V-model 4 artifact のうち)"
created: 2026-05-17
owner: PM
related_docs:
  - docs/plans/PLAN-075-vmodel-design-test-mapping.md (V-model 4 artifact 双方向 trace framework)
  - docs/v2/L2-design/CONCEPT.md (対象 ① 設計)
  - docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md (対象 ① 設計の詳細)
  - docs/v2/L4-test-design/PLAN-074-unit-test-design.md (同一 PLAN の別 artifact)
phases: L2, L6
gates: G2, G6
---

> **V-model 4 artifact 位置付け**:
> 本書は ③ テスト設計 artifact である。① 設計 (CONCEPT.md / D-API EXT §3.X) と
> ④ テストコード (cli/lib/tests/test_e2e_http_api_*.py) を双方向 trace で繋ぐ独立文書として保持する。
> 設計文書とテスト設計文書、テスト設計文書とテストコードを同一文書へ統合しない。

# PLAN-074 総合テスト設計 (③ D-TEST-DESIGN-SYS)

> 目的: PLAN-074 (HTTP endpoint 層) の E2E / system-level シナリオを定義し、5 endpoint
> (`push` / `pr` / `hook` / `audit` / `telemetry`) を跨ぐシステム全体動作を検証する。
> 本書は L2 全体設計に対応する ③ artifact であり、L6 統合検証のテストコード実装前提となる。

## §1 概要

### 1.1 目的

PLAN-074 の HTTP endpoint 群について、Flask test client を用いた単一 endpoint の挙動ではなく、
`actor -> HTTP request -> server -> route -> helix.db -> response -> audit_log / telemetry / side effect`
の一連の経路を E2E として検証する。

本書で扱う観点:

- endpoint 間の整合性
- 認証・入力・run_id 伝播
- 監査ログと telemetry の相互整合
- gate 失敗時の安全側挙動
- 冪等性 / 重複排除 / 競合検知

### 1.2 V-model 4 artifact 双方向 trace (PLAN-075)

- **対象設計 (①)**: `docs/v2/L2-design/CONCEPT.md` の HTTP automation layer 全体構想
- **対象設計 (①)**: `docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md` §3.1-3.5
- **対応実装 (②)**: `cli/lib/http_api/*` (全 module)
- **本文書 (③ D-TEST-DESIGN-SYS)**: `docs/v2/L4-test-design/PLAN-074-system-test-design.md`
- **対応テストコード (④ D-TEST-CODE-SYS)**: `cli/lib/tests/test_e2e_http_api_*.py`
- **検証 gate**: G6 (RC 判定)

Trace ルール:

- 設計 → 本書: ① 設計文書に「テスト設計ファイル: PLAN-074-system-test-design.md」を明示
- 本書 → 設計: 各 case に対象 D-API EXT 節を明示
- 本書 → テストコード: 各 case に対応する test file path を明示
- テストコード → 本書: テスト docstring に case ID を明示

### 1.3 case 命名規約

- `S-PUSH-001` ... `S-PUSH-NNN`: push endpoint E2E
- `S-PR-001` ... `S-PR-NNN`: pr endpoint E2E
- `S-HOOK-001` ... `S-HOOK-NNN`: hook endpoint E2E
- `S-AUDIT-001` ... `S-AUDIT-NNN`: audit endpoint E2E
- `S-TEL-001` ... `S-TEL-NNN`: telemetry endpoint E2E
- `S-CROSS-001` ... `S-CROSS-NNN`: 複数 endpoint を跨ぐ統合シナリオ

### 1.4 対象 endpoint と主要責務

| endpoint | 主責務 | 主要な観測点 |
|---|---|---|
| `push` | gate 実行と automation_runs 採番 | `run_id`, `status`, `push.attempted` |
| `pr` | pull request 起点の gate / pair_transition | `pair_transition`, `run_kind=pr` |
| `hook` | Claude / agent hook callback の受理 | `hook_kind`, `session_start`, `stop` |
| `audit` | footer / summary / diff / security / qa の監査蓄積 | `audit_kind`, `payload`, `endpoint_call` |
| `telemetry` | session 単位の上書き更新 | `session_id`, `tokens_total`, `cost_usd` |

### 1.5 テストコード配置

本文書に対応するテストコードは将来 L6 で以下へ実装する。

| case group | 予定ファイル |
|---|---|
| push | `cli/lib/tests/test_e2e_http_api_push.py` |
| pr | `cli/lib/tests/test_e2e_http_api_pr.py` |
| hook | `cli/lib/tests/test_e2e_http_api_hooks.py` |
| audit | `cli/lib/tests/test_e2e_http_api_audit.py` |
| telemetry | `cli/lib/tests/test_e2e_http_api_telemetry.py` |
| cross-endpoint | `cli/lib/tests/test_e2e_http_api_cross.py` |

## §2 E2E シナリオ設計

### §2.0 共通観測基準

各 case は最低でも次の 3 点を明示する。

- `expected_response_body`
- `expected_automation_runs`
- `expected_audit_log`

必要に応じて `expected_telemetry`, `expected_side_effect`, `expected_http_status`
も追加する。

### §2.1 push trigger E2E

push trigger は `D-API EXT §3.1` に対応する。`push_gate.run_all_gates()` の判定結果と、
`automation_runs` / `audit_log` の整合性を中心に検証する。

| case | シナリオ | 期待結果 | 検証項目 | テストコード |
|---|---|---|---|---|
| S-PUSH-001 | `execute=false` で全 gate PASS。HTTP request は正常 body を送り、DB への採番と audit 記録のみ確認する。 | `200`、`run_id` 採番、`automation_runs` に 1 行、`audit_log` に 1 行。 | `run_kind=push`、`push.attempted=false`、`response.body.run_id`、`expected_automation_runs`、`expected_audit_log`。 | `cli/lib/tests/test_e2e_http_api_push.py` |
| S-PUSH-002 | `execute=true` で全 gate PASS。push side effect を許可し、git push 実行まで通す。 | `200`、`push.attempted=true`、git push 成功、`automation_runs.status=succeeded`。 | side effect 確認、`git` 監査、`response.body.push.attempted`、`automation_runs.status`。 | `cli/lib/tests/test_e2e_http_api_push.py` |
| S-PUSH-003 | gate FAIL (例: `G-tests` 失敗) で `execute=true` を送る。 | `200` だが `push.attempted=false`、`automation_runs.status=failed`。 | gate fail 時の push 抑止、安全側挙動、`expected_response_body.gate_result`、`expected_audit_log.severity`。 | `cli/lib/tests/test_e2e_http_api_push.py` |
| S-PUSH-004 | 同一 `plan_id` + `commit_sha` で 2 回 trigger する。 | 1 回目 `200`、2 回目 `409`、重複検知。 | idempotency、`IntegrityError` 相当の防御、`response.body.error.code`、`automation_runs` 重複なし。 | `cli/lib/tests/test_e2e_http_api_push.py` |

#### S-PUSH-001 補足

- 前提: `helix.db` が fresh DB で初期化されている
- 入力: `plan_id`, `commit_sha`, `execute=false`, `actor`
- 期待結果: `automation_runs` に `run_kind=push` が 1 行だけ生成される
- 検証項目: `audit_log` の `event_type=endpoint_call`

#### S-PUSH-002 補足

- 前提: git side effect を許可するモック / sandbox
- 入力: `execute=true`
- 期待結果: gate PASS の場合のみ push 実施
- 検証項目: push 実行判定と `automation_runs` の `succeeded`

#### S-PUSH-003 補足

- 前提: gate 失敗を返す fixture
- 入力: `execute=true`
- 期待結果: `push.attempted=false`
- 検証項目: fail-close で副作用が起きないこと

#### S-PUSH-004 補足

- 前提: 先行トリガで同一 key を登録済み
- 入力: 同一 `plan_id` / `commit_sha`
- 期待結果: 2 回目は `409 Conflict`
- 検証項目: `automation_runs` 一意性、重複記録なし

### §2.2 pr trigger E2E

pr trigger は `D-API EXT §3.2` に対応する。push との共通 gate 群に加え、
`pair_transition` と既存 plan との整合を検証する。

| case | シナリオ | 期待結果 | 検証項目 | テストコード |
|---|---|---|---|---|
| S-PR-001 | 正常系 pr trigger。`execute=false` で gate PASS、pair 情報を含めて登録する。 | `200`、`run_id` 採番、`run_kind=pr`。 | `pair_transition` の初期値、`automation_runs.run_kind`、`audit_log` 登録。 | `cli/lib/tests/test_e2e_http_api_pr.py` |
| S-PR-002 | `pair_transition` が発生する条件で gate 移行を確認する。 | `200`、`pair_transition` が `open -> ready` 等へ遷移。 | 遷移前後の state、`response.body.pair_transition`、`audit_log` の整合。 | `cli/lib/tests/test_e2e_http_api_pr.py` |
| S-PR-003 | 既存 push 実行済み plan に対して pr trigger を送る。 | `200`、pair 整合性が保たれ、重複や矛盾がない。 | `push` と `pr` の `plan_id` 整合、`automation_runs` の関係、`expected_response_body.plan_binding`。 | `cli/lib/tests/test_e2e_http_api_pr.py` |

#### S-PR-001 補足

- 前提: `plan_id` が存在し、PR コンテキストが作成済み
- 入力: `pr_number`, `head_sha`, `execute=false`
- 期待結果: `run_kind=pr` が採番される
- 検証項目: `audit_log` に `endpoint_call` を記録

#### S-PR-002 補足

- 前提: pair transition を返す fixture
- 入力: `transition_hint`
- 期待結果: gate 遷移と DB 反映が一致
- 検証項目: `pair_transition.before` / `after`

#### S-PR-003 補足

- 前提: 同一 `plan_id` の push 実績あり
- 入力: PR trigger
- 期待結果: pair 整合性が崩れない
- 検証項目: push/pr の cross-reference

### §2.3 hook callback E2E

hook callback は `D-API EXT §3.3` に対応する。`PreToolUse`、`PostToolUse`、`Stop`、
`session_start` の 4 hook_kind を連続流入させたときの相互整合を検証する。

| case | シナリオ | 期待結果 | 検証項目 | テストコード |
|---|---|---|---|---|
| S-HOOK-001 | `PreToolUse -> session_start -> PostToolUse -> Stop` の 4 連続 hook を同一 session で流す。 | すべて `200`、`hook_kind` ごとの記録が 4 件揃う。 | `hook_kind` 別 route 到達、`audit_log` 4 件、`session_id` 維持。 | `cli/lib/tests/test_e2e_http_api_hooks.py` |
| S-HOOK-002 | `Stop` hook から telemetry 連動までを含めて session 終了を確認する。 | `200`、hook 記録後に telemetry 更新が観測される。 | `stop` 受理、`session_telemetry` 呼び出し、`expected_telemetry`。 | `cli/lib/tests/test_e2e_http_api_hooks.py` |
| S-HOOK-003 | `run_id` 不在で hook を送る。 | `404`、保存なし。 | `run_id` lookup 失敗時の拒否、`audit_log` 未作成。 | `cli/lib/tests/test_e2e_http_api_hooks.py` |
| S-HOOK-004 | `hook_kind` が path と body で不一致。 | `400`、不整合理由を返す。 | path/body 一致チェック、`expected_response_body.error.code`、拒否ログ。 | `cli/lib/tests/test_e2e_http_api_hooks.py` |

#### S-HOOK-001 補足

- 前提: 1 session の run context が準備されている
- 入力: 4 連続 hook request
- 期待結果: 各 hook_kind が 1 回ずつ記録される
- 検証項目: sequence order と `audit_log` の件数

#### S-HOOK-002 補足

- 前提: Stop hook が telemetry 更新を誘発する設定
- 入力: `Stop` 後の telemetry payload
- 期待結果: telemetry 更新が最後まで実施される
- 検証項目: hook と telemetry の連動性

#### S-HOOK-003 補足

- 前提: 不正な run lookup
- 入力: `run_id` なし
- 期待結果: `404`
- 検証項目: 保存系副作用が起きないこと

#### S-HOOK-004 補足

- 前提: path と body を意図的にずらす fixture
- 入力: 不一致 `hook_kind`
- 期待結果: `400`
- 検証項目: 不一致検出のメッセージ

### §2.4 audit log E2E

audit log は `D-API EXT §3.4` に対応する。footer / summary / diff / security / qa の
audit_kind を跨ぎ、payload の退避と endpoint_call の固定記録を検証する。

| case | シナリオ | 期待結果 | 検証項目 | テストコード |
|---|---|---|---|---|
| S-AUDIT-001 | footer audit kind 経由で payload を退避し、endpoint_call を記録する。 | `200`、payload が退避され、`endpoint_call` が保存される。 | `payload.http_audit_kind`、`audit_kind=endpoint_call`、`expected_audit_log`。 | `cli/lib/tests/test_e2e_http_api_audit.py` |
| S-AUDIT-002 | `summary / diff_lines / security_scan / qa_check` の 4 種 audit_kind を順次送る。 | 4 件すべて `200`、各 kind が独立に記録される。 | audit_kind 別の保存、`response.body.acknowledged`、kind ごとの分岐。 | `cli/lib/tests/test_e2e_http_api_audit.py` |
| S-AUDIT-003 | `run_id` 不在で audit を送る。 | `404`、保存なし。 | run lookup 失敗、`audit_log` 不生成、`expected_response_body.error.code`。 | `cli/lib/tests/test_e2e_http_api_audit.py` |
| S-AUDIT-004 | payload 内 `diff_lines` が schema 準拠であることを確認する。 | `200` か `400`、schema 準拠 / 不備が明確。 | `diff_lines` の型、範囲、`payload` 保持、`expected_response_body.validation`。 | `cli/lib/tests/test_e2e_http_api_audit.py` |

#### S-AUDIT-001 補足

- 前提: footer 由来 payload を受ける route
- 入力: `audit_kind=footer`, `payload`
- 期待結果: `payload.http_audit_kind` が退避される
- 検証項目: endpoint_call への正規化

#### S-AUDIT-002 補足

- 前提: 4 種 audit_kind を順次送れる fixture
- 入力: `summary`, `diff_lines`, `security_scan`, `qa_check`
- 期待結果: kind ごとに 1 件ずつ保存
- 検証項目: kind 別 row の独立性

#### S-AUDIT-003 補足

- 前提: run_id が DB に存在しない
- 入力: 404 を誘発する request
- 期待結果: 保存なし
- 検証項目: lookup 失敗の拒否

#### S-AUDIT-004 補足

- 前提: diff_lines schema の境界値 fixture
- 入力: 正常 / 異常の双方
- 期待結果: validation が schema に従う
- 検証項目: `diff_lines` の構造検証

### §2.5 telemetry E2E

telemetry は `D-API EXT §3.5` に対応する。`session_id` 単位の UPSERT、累積値、
actor の整合性を検証する。

| case | シナリオ | 期待結果 | 検証項目 | テストコード |
|---|---|---|---|---|
| S-TEL-001 | 単一 session の正常 UPSERT。初回送信で telemetry row を作成する。 | `200`、1 行 insert / upsert。 | `session_id`、`tokens_total`、`cost_usd`、`expected_telemetry`。 | `cli/lib/tests/test_e2e_http_api_telemetry.py` |
| S-TEL-002 | 同一 `session_id` で 5 回 UPSERT する。 | 5 回すべて `200`、最新値で上書きされる。 | idempotency、latest-wins、`automation_runs` との session binding。 | `cli/lib/tests/test_e2e_http_api_telemetry.py` |
| S-TEL-003 | `cost_usd` の累積を複数回更新して確認する。 | `200`、合計値が増分として反映される。 | `cost_usd` の加算、桁落ちなし、`expected_response_body.cost_usd_total`。 | `cli/lib/tests/test_e2e_http_api_telemetry.py` |
| S-TEL-004 | actor 形式 (`se/gpt-5.4`) の整合性を確認する。 | `200`、actor 表記が schema と一致。 | actor の形式、`session_id` との紐付け、`expected_telemetry.actor`. | `cli/lib/tests/test_e2e_http_api_telemetry.py` |

#### S-TEL-001 補足

- 前提: session_id が発行済み
- 入力: 単発 telemetry payload
- 期待結果: row が作成される
- 検証項目: UPSERT の初回経路

#### S-TEL-002 補足

- 前提: 同一 session_id を 5 回投げる
- 入力: 連続同値 / 変化値 mix
- 期待結果: 最新値が反映される
- 検証項目: latest-wins と冪等性

#### S-TEL-003 補足

- 前提: cost_usd の増分 fixture
- 入力: 数値 payload
- 期待結果: 累積が正しく増える
- 検証項目: sum 演算の正当性

#### S-TEL-004 補足

- 前提: actor 名の正規化規則を持つ
- 入力: `se/gpt-5.4`
- 期待結果: schema に一致
- 検証項目: actor 文字列形式

### §2.6 cross-endpoint シナリオ

複数 endpoint を組み合わせ、単一 endpoint では見えない整合性を検証する。

| case | シナリオ | 期待結果 | 検証項目 | テストコード |
|---|---|---|---|---|
| S-CROSS-001 | `push trigger -> audit log -> telemetry` の 1 セッションフロー。 | 全 request `200`、1 セッションの流れが完了する。 | `run_id` 伝播、`audit_log` 後の telemetry 更新、`expected_response_body.session_flow`。 | `cli/lib/tests/test_e2e_http_api_cross.py` |
| S-CROSS-002 | `pr trigger -> pair_transition -> audit log` の連動。 | `200`、pair 変化と audit が同一 run に紐づく。 | `pair_transition`、`audit_log.run_id`、`automation_runs.run_kind=pr`。 | `cli/lib/tests/test_e2e_http_api_cross.py` |
| S-CROSS-003 | `hook session_start -> tool 実行中の audit -> Stop hook -> telemetry` の full lifecycle。 | すべて `200`、session の開始から終了までを通しで確認。 | `session_id` 維持、hook/audit/telemetry の順序、`expected_audit_log`。 | `cli/lib/tests/test_e2e_http_api_cross.py` |
| S-CROSS-004 | 認証 (Bearer) 経路の 5 endpoint 一括検証。 | 5 endpoint すべて `401/403` または `200` を schema 通り返す。 | bearer validation、localhost 制約、endpoint ごとの差異なし。 | `cli/lib/tests/test_e2e_http_api_cross.py` |
| S-CROSS-005 | 異常系: `run_id` 中途切れで audit / telemetry が先行し、push 不在の状態を作る。 | `404` または `409`、不整合を保存しない。 | run chain の欠落検出、先行記録の拒否、`expected_response_body.error.code`。 | `cli/lib/tests/test_e2e_http_api_cross.py` |
| S-CROSS-006 | 同時多重 push を concurrency 付きで送る。 | 片方のみ成功し、もう片方は `409` か等価の重複拒否。 | race condition 耐性、`IntegrityError` 相当の防御、`automation_runs` 一意性。 | `cli/lib/tests/test_e2e_http_api_cross.py` |

#### S-CROSS-001 補足

- 前提: 単一 run のフローを直列で流せる fixture
- 入力: push -> audit -> telemetry
- 期待結果: run_id が全 endpoint で一致
- 検証項目: 伝播の欠落がないこと

#### S-CROSS-002 補足

- 前提: pr trigger 後に pair_transition を返せる fixture
- 入力: pr -> pair_transition -> audit
- 期待結果: 同一 run に紐づく
- 検証項目: pair と audit の join

#### S-CROSS-003 補足

- 前提: hook session_start が有効
- 入力: hook -> audit -> stop -> telemetry
- 期待結果: lifecycle 完了
- 検証項目: 時系列順と session_id

#### S-CROSS-004 補足

- 前提: bearer 認証を共通 fixture で注入
- 入力: 5 endpoint へ同条件 request
- 期待結果: 認証結果が一貫
- 検証項目: endpoint 間の認証差異なし

#### S-CROSS-005 補足

- 前提: push 不在の中間状態を模擬
- 入力: audit / telemetry 先行
- 期待結果: 不整合は保存されない
- 検証項目: 欠落 run の拒否

#### S-CROSS-006 補足

- 前提: concurrency を再現する test fixture
- 入力: 同時多重 push request
- 期待結果: 一方のみ採用
- 検証項目: race condition と重複拒否

## §3 共通 fixture / mock 戦略

### §3.1 基本方針

E2E 設計では「本物の HTTP 経路」を優先し、必要最小限のみを fixture 化する。

- `helix.db`: temp_dir + migrate_all で fresh DB 構築
- HTTP client: Flask test client を fixture 化
- bearer token: 既定の test token を fixture 化
- run_id 採番: 先行 insert で run context を固定
- git push side effect: 目的が side effect 確認の case のみ限定 mock / sandbox

### §3.2 mock / fixture の境界

| 対象 | 方針 | 理由 |
|---|---|---|
| Flask request / client | fixture | HTTP 経路の実測を残すため |
| helix.db | 実 DB で再現 | DB 整合を E2E として確認するため |
| git push side effect | case 限定で隔離 | 本番影響を避けつつ side effect を確認するため |
| `datetime` / `trace_id` | 固定化可 | 断続的な揺れを抑えるため |
| `push_gate` の判定 | 失敗系 case では mock | gate fail-close を明示するため |

### §3.3 標準セットアップ

1. fresh DB を作成する
2. `automation_runs` に必要な先行 row を入れる
3. Flask client を起動する
4. bearer token を注入する
5. case ごとの payload を送る
6. response / DB / side effect を三点照合する

## §4 case 数集計

| 区分 | case 数 |
|---|---|
| push | 4 |
| pr | 3 |
| hook | 4 |
| audit | 4 |
| telemetry | 4 |
| cross-endpoint | 6 |
| **合計** | **25** |

## §5 DoD (Definition of Done)

- 全 25 case の前提条件 / 入力 / 期待結果 / 検証項目が明示されている
- 各 case の対応テストコードファイルパスが §1.5 / §2 各表で確定している
- `expected_response_body` / `expected_automation_runs` / `expected_audit_log` が case ごとに定義されている
- 5 endpoint を跨ぐ cross-endpoint シナリオが 6 case 分ある
- G6 RC 判定 gate で本文書の case 充足率を確認できる

## §6 受入確認チェック

### §6.1 trace 整合

- ① 設計に `PLAN-074-system-test-design.md` への参照があること
- ③ 本文書に `CONCEPT.md` / `D-API EXT §3.X` の参照があること
- ④ テストコードに case ID が docstring で対応すること

### §6.2 coverage 確認観点

- `push` / `pr` / `hook` / `audit` / `telemetry` がそれぞれ最低 3 case 以上あること
- cross-endpoint が 5 endpoint 以上を跨ぐこと
- 失敗系 case が各 endpoint に含まれること

### §6.3 残存 TODO

- `cli/lib/tests/test_e2e_http_api_*.py` の実装は未着手
- `docs/v2/L2-design/CONCEPT.md` と `D-API EXT` 側への双方向 trace 追記は別 WBS で実施
- 実 DB を用いた E2E fixture の性能確認は L6 実装段階で確定

## §7 変更履歴

- 2026-05-17: 初版作成
- 2026-05-17: PLAN-075 の V-model 4 artifact 設計に合わせて system-level E2E 25 case を定義
