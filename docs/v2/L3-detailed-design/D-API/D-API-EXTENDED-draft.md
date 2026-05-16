---
doc_id: D-API-EXTENDED-draft-v0.1
plan_id: PLAN-070
sprint: SprintE / .5
status: draft
created: 2026-05-16
primary_drive: be
secondary_drives: [fullstack, fe]
extends: D-API-draft-v0.1
---

# PLAN-070 / D-API Extended Draft

## §1 目的とスコープ

本稿は PLAN-070 SprintE（L3 D-API 拡張）の draft を起票し、運用機能の endpoint contract を固定する。
対象は push trigger / pr trigger / hook callback / audit / Stop hook telemetry の 5 endpoint であり、Sprint A §2.0 の共通 primitive を再利用する。

### スコープ

- `cli/helix-push` の起点となる push trigger contract
- `cli/helix-pr` の起点となる pr trigger contract
- `PreToolUse` / `PostToolUse` / `Stop` / `session_start` の hook callback contract
- `helix-codex audit/footer` の受領口となる audit contract
- Stop hook の session-summary 後継となる telemetry contract

### Non-goals

- hook 実行内部ロジック
- CLI parsing 内部ロジック
- Codex CLI exec wrapper の実装詳細
- D-DB migration 本文
- state-events.md の本文変更

## §2 共通 primitive の再利用

Sprint A §2.0 の primitive を再利用し、新規 primitive は追加しない。

- Sprint A §2.0 (`docs/v2/L3-detailed-design/D-API/D-API-draft.md` §2.0) で定義された `Envelope` / `ErrorModel` / `DetectorRef` / `PairStatusTransition` / `PromotionHookRef` を再利用し、本 draft では shape を再定義しない。
- `Envelope` は response 外枠に使う。
- `ErrorModel` は 400 / 401 / 404 / 409 / 500 の統一 error body に使う。
- `DetectorRef` は hook callback 由来の検知理由と gate 連動参照に使う。
- `PairStatusTransition` は pair / gate 遷移の状態表現に使う。
- `PromotionHookRef` は push / pr trigger の promotion trace に使う。
- path / query / header / body を分離し、`properties` は object として定義する。

## §3 endpoint contract

| # | method | path | 起源 | 役割 |
|---|---|---|---|---|
| 1 | POST | `/api/v1/automation/push/{plan_id}/trigger` | PLAN-067 | push 実行開始 |
| 2 | POST | `/api/v1/automation/pr/{plan_id}/trigger` | PLAN-067 | pr 実行開始 |
| 3 | POST | `/api/v1/automation/hooks/{hook_kind}/callback` | PLAN-043 / PLAN-014 / PLAN-015 / PLAN-016 | hook callback |
| 4 | POST | `/api/v1/automation/audit/log` | PLAN-034 / PLAN-048 | audit/footer 受領 |
| 5 | POST | `/api/v1/automation/session/telemetry` | PLAN-016 | Stop telemetry 受領 |

### 共通ルール

- 成功系 response は `success: true` と `data` を持つ。
- 失敗系 response は `success: false` と `error` を持つ。
- `trace.trace_id` は request と response をまたいで追跡可能とする。
- `trace.generated_at` は server generated の UTC timestamp とする。
- `X-Trace-Id` は補助キーとして `automation_runs.id` の解決に使い、推論不能な場合は 400 とする。
- push trigger / pr trigger は response.data.run_id を必須で返却し、新規 `automation_runs.id` を採番する。
- hook callback / audit / telemetry は request_schema.run_id を必須入力とし、既存 `automation_runs.id` を参照する。
- 追加 error code は原則認めず、400 / 401 / 404 / 409 / 500 に収束する。

### 3.1 push trigger endpoint

- path: `/api/v1/automation/push/{plan_id}/trigger`
- method: `POST`
- 起源: PLAN-067 helix-automation-layer
- 実装根拠: `cli/lib/push_gate.py` `run_all_gates()` L291-324 (Read 確認済み、2026-05-16 P0-04)
- **実装ファイル**: `cli/lib/http_api/routes/push_pr.py`
- **test ファイル**: `cli/lib/tests/test_http_api_push_pr.py` (5 cases)
- **担当 WBS**: PLAN-074 / WBS-074-L4-003 / Sprint .2 (commit 95cb7be)
- **テスト設計ファイル (③ D-TEST-DESIGN)**: 結合 `docs/v2/L4-test-design/PLAN-074-integration-test-design.md §3.1`、単体 `docs/v2/L4-test-design/PLAN-074-unit-test-design.md §2.7` (V-model 4 artifact 双方向 trace、PLAN-075)

**`run_all_gates()` シグネチャ (実測値)**:
- 引数: `execute: bool = False, remote: str = "origin", branch: str = "main"` (全オプション)
- 戻り値: `dict` — キー `ok / failed_count / gates / execute_requested / remote / branch / push`
- `gates`: `list[{id: str, passed: bool, detail: str, fix: str}]` — id は `G-tests / G-catalog / G-secret / G-ff / G-attr / G-nondestructive`
- `push`: `{attempted: bool, ok: bool, detail: str}`
- side effect: `execute=True` + 全 gate PASS 時のみ `git push` を実行。helix.db 書き込みなし

```yaml
path_schema:
  type: object
  required: [plan_id]
  properties: { plan_id: { type: string, minLength: 1, maxLength: 64 } }
  additionalProperties: false
query_schema:
  type: object
  properties:
    force: { type: boolean, default: false }
    dry_run: { type: boolean, default: false }
  additionalProperties: false
header_schema:
  type: object
  required: [Authorization, Content-Type, X-Trace-Id]
  properties:
    Authorization: { type: string }
    Content-Type: { type: string, enum: [application/json] }
    X-Trace-Id: { type: string, minLength: 8 }
  additionalProperties: false
request_schema:
  type: object
  required: [commit_sha, branch, trigger_actor, execute]
  properties:
    commit_sha: { type: string, minLength: 7, maxLength: 64 }
    branch: { type: string, minLength: 1, maxLength: 128 }
    trigger_actor: { type: string, minLength: 1, maxLength: 128 }
    execute: { type: boolean, default: false }
    remote: { type: string, default: "origin" }
    promotion_hook: { $ref: '#/components/schemas/PromotionHookRef' }
  additionalProperties: false
response_schema:
  allOf:
    - $ref: '#/components/schemas/Envelope'
    - type: object
      properties:
        data:
          type: object
          required: [run_id, ok, failed_count, gate_results, execute_requested, remote, branch, push, pair_transition]
          properties:
            run_id: { type: integer }
            ok: { type: boolean }
            failed_count: { type: integer, minimum: 0 }
            execute_requested: { type: boolean }
            remote: { type: string }
            branch: { type: string }
            gate_results:
              type: array
              description: "run_all_gates() gates キーの直接マッピング。id は G-tests/G-catalog/G-secret/G-ff/G-attr/G-nondestructive"
              items:
                type: object
                required: [id, passed, detail, fix]
                properties:
                  id: { type: string, enum: [G-tests, G-catalog, G-secret, G-ff, G-attr, G-nondestructive] }
                  passed: { type: boolean }
                  detail: { type: string }
                  fix: { type: string }
            push:
              type: object
              required: [attempted, ok, detail]
              properties:
                attempted: { type: boolean }
                ok: { type: boolean }
                detail: { type: string }
            pair_transition: { $ref: '#/components/schemas/PairStatusTransition' }
      additionalProperties: false
```

- `pair_transition` は push 実行で常時返却し、pair / gate 遷移を response data に明示する。
- `gate_results[].id` は `run_all_gates()` 戻り値の `gates[].id` と 1:1 対応する。HELIX フェーズゲート (G2/G3...) とは別体系であることに注意。
- error_codes: 400 / 401 / 404 / 409 / 500

### 3.2 pr trigger endpoint

- path: `/api/v1/automation/pr/{plan_id}/trigger`
- method: `POST`
- 起源: PLAN-067 helix-automation-layer
- 実装根拠: `cli/lib/push_gate.py` `run_all_gates()` L291-324 (Read 確認済み、2026-05-16 P0-04)。push/pr は同一 `run_all_gates()` を呼ぶ共通 gate 体系を持つ。
- **実装ファイル**: `cli/lib/http_api/routes/push_pr.py` (push と同一モジュール)
- **test ファイル**: `cli/lib/tests/test_http_api_push_pr.py` (5 cases、push と共有)
- **担当 WBS**: PLAN-074 / WBS-074-L4-003 / Sprint .2 (commit 95cb7be)
- **テスト設計ファイル (③ D-TEST-DESIGN)**: 結合 `docs/v2/L4-test-design/PLAN-074-integration-test-design.md §3.2`、単体 `docs/v2/L4-test-design/PLAN-074-unit-test-design.md §2.7` (push_pr 単体 module、PLAN-075)

```yaml
path_schema:
  type: object
  required: [plan_id]
  properties: { plan_id: { type: string, minLength: 1, maxLength: 64 } }
  additionalProperties: false
query_schema:
  type: object
  properties:
    force: { type: boolean, default: false }
    dry_run: { type: boolean, default: false }
    auto_merge: { type: boolean, default: false }
  additionalProperties: false
header_schema:
  type: object
  required: [Authorization, Content-Type, X-Trace-Id]
  properties:
    Authorization: { type: string }
    Content-Type: { type: string, enum: [application/json] }
    X-Trace-Id: { type: string, minLength: 8 }
  additionalProperties: false
request_schema:
  type: object
  required: [commit_sha, branch, trigger_actor, execute]
  properties:
    commit_sha: { type: string, minLength: 7, maxLength: 64 }
    branch: { type: string, minLength: 1, maxLength: 128 }
    trigger_actor: { type: string, minLength: 1, maxLength: 128 }
    execute: { type: boolean, default: false }
    remote: { type: string, default: "origin" }
    promotion_hook: { $ref: '#/components/schemas/PromotionHookRef' }
    pair_transition: { $ref: '#/components/schemas/PairStatusTransition' }
  additionalProperties: false
response_schema:
  allOf:
    - $ref: '#/components/schemas/Envelope'
    - type: object
      properties:
        data:
          type: object
          required: [run_id, ok, failed_count, gate_results, execute_requested, remote, branch, push]
          properties:
            run_id: { type: integer }
            ok: { type: boolean }
            failed_count: { type: integer, minimum: 0 }
            execute_requested: { type: boolean }
            remote: { type: string }
            branch: { type: string }
            gate_results:
              type: array
              description: "run_all_gates() gates キーの直接マッピング。id は G-tests/G-catalog/G-secret/G-ff/G-attr/G-nondestructive"
              items:
                type: object
                required: [id, passed, detail, fix]
                properties:
                  id: { type: string, enum: [G-tests, G-catalog, G-secret, G-ff, G-attr, G-nondestructive] }
                  passed: { type: boolean }
                  detail: { type: string }
                  fix: { type: string }
            push:
              type: object
              required: [attempted, ok, detail]
              properties:
                attempted: { type: boolean }
                ok: { type: boolean }
                detail: { type: string }
      additionalProperties: false
```

- pr trigger は query の `force` / `dry_run` / `auto_merge` と request body の `execute` / `remote` に分離し、`G8` は本 draft では扱わない。
- `gate_results[].id` は push trigger と同一の 6-gate 体系 (G-tests/G-catalog/G-secret/G-ff/G-attr/G-nondestructive) である。
- error_codes: 400 / 401 / 404 / 409 / 500

### 3.3 hook callback endpoint

- path: `/api/v1/automation/hooks/{hook_kind}/callback`
- method: `POST`
- 起源: PLAN-043 / PLAN-014 / PLAN-015 / PLAN-016
- **実装ファイル**: `cli/lib/http_api/routes/hooks.py`
- **test ファイル**: `cli/lib/tests/test_http_api_hooks.py` (5 cases)
- **担当 WBS**: PLAN-074 / WBS-074-L4-004 / Sprint .3 (commit a387f9c)
- **テスト設計ファイル (③ D-TEST-DESIGN)**: 結合 `docs/v2/L4-test-design/PLAN-074-integration-test-design.md §3.3`、単体 `docs/v2/L4-test-design/PLAN-074-unit-test-design.md §2.6` (PLAN-075)

```yaml
path_schema:
  type: object
  required: [hook_kind]
  properties: { hook_kind: { type: string, enum: [pretool, posttool, stop, session_start] } }
  additionalProperties: false
query_schema: { type: object, properties: {}, additionalProperties: false }
header_schema:
  type: object
  required: [Authorization, Content-Type, X-Trace-Id]
  properties:
    Authorization: { type: string }
    Content-Type: { type: string, enum: [application/json] }
    X-Trace-Id: { type: string, minLength: 8 }
  additionalProperties: false
request_schema:
  oneOf:
    - $ref: '#/components/schemas/HookPretool'
    - $ref: '#/components/schemas/HookPosttool'
    - $ref: '#/components/schemas/HookStop'
    - $ref: '#/components/schemas/HookSessionStart'
  discriminator:
    propertyName: hook_kind
response_schema:
  allOf:
    - $ref: '#/components/schemas/Envelope'
    - type: object
      properties:
        data:
          type: object
          required: [acknowledged, persisted_at]
          properties:
            acknowledged: { type: boolean }
            persisted_at: { type: string, format: date-time }
      additionalProperties: false
```

- hook_kind は `pretool` / `posttool` / `stop` / `session_start` に統一する。
- path_schema.hook_kind と request body.hook_kind は一致必須とし、不一致は 400 とする。
- error_codes: 400 / 401 / 404 / 409 / 500

### 3.4 audit endpoint

- path: `/api/v1/automation/audit/log`
- method: `POST`
- 起源: PLAN-034 / PLAN-048
- **実装ファイル**: `cli/lib/http_api/routes/audit.py`
- **test ファイル**: `cli/lib/tests/test_http_api_audit.py` (5 cases)
- **担当 WBS**: PLAN-074 / WBS-074-L4-005 / Sprint .4 (commit 2505c4a)
- **テスト設計ファイル (③ D-TEST-DESIGN)**: 結合 `docs/v2/L4-test-design/PLAN-074-integration-test-design.md §3.4`、単体 `docs/v2/L4-test-design/PLAN-074-unit-test-design.md §2.4 / §2.5` (audit + routes/audit、PLAN-075)
- **audit_kind enum drift 解決**: HTTP 側 kind (footer/summary/diff_lines/security_scan/qa_check) は `payload.http_audit_kind` に退避し、`helix_db.insert_audit_log` には `endpoint_call` 固定で記録

```yaml
path_schema: { type: object, properties: {}, additionalProperties: false }
query_schema: { type: object, properties: {}, additionalProperties: false }
header_schema:
  type: object
  required: [Authorization, Content-Type, X-Trace-Id]
  properties:
    Authorization: { type: string }
    Content-Type: { type: string, enum: [application/json] }
    X-Trace-Id: { type: string, minLength: 8 }
  additionalProperties: false
request_schema:
  type: object
  required: [audit_kind, payload, actor, run_id]
  properties:
    audit_kind: { type: string, enum: [footer, summary, diff_lines, security_scan, qa_check] }
    payload: { type: object, additionalProperties: true }
    run_id: { type: integer }
    actor: { type: string, minLength: 1, maxLength: 128 }
    related_plan_id: { type: string }
  additionalProperties: false
response_schema:
  allOf:
    - $ref: '#/components/schemas/Envelope'
    - type: object
      properties:
        data:
          type: object
          required: [acknowledged, persisted_at]
          properties:
            acknowledged: { type: boolean }
            persisted_at: { type: string, format: date-time }
      additionalProperties: false
```

- `payload` は object として受ける。
- `run_id` は必須で、`X-Trace-Id` から解決した `automation_runs.id` と一致する必要がある。
- `payload.diff_lines` は audit_kind=`diff_lines` のときに audit_log §4 payload schema に対応する。
- error_codes: 400 / 401 / 404 / 409 / 500

### 3.5 Stop hook telemetry endpoint

- path: `/api/v1/automation/session/telemetry`
- method: `POST`
- 起源: PLAN-016
- **実装ファイル**: `cli/lib/http_api/routes/telemetry.py`
- **test ファイル**: `cli/lib/tests/test_http_api_telemetry.py` (5 cases)
- **担当 WBS**: PLAN-074 / WBS-074-L4-006 / Sprint .5 (commit 1633202)
- **テスト設計ファイル (③ D-TEST-DESIGN)**: 結合 `docs/v2/L4-test-design/PLAN-074-integration-test-design.md §3.5`、単体 `docs/v2/L4-test-design/PLAN-074-unit-test-design.md §2.5` (telemetry 単体 module、PLAN-075)
- **UPSERT 動作**: session_id UNIQUE 制約による idempotent UPSERT (v27 schema、tool_uses_count / tokens_total / cost_usd 累積)

```yaml
path_schema: { type: object, properties: {}, additionalProperties: false }
query_schema: { type: object, properties: {}, additionalProperties: false }
header_schema:
  type: object
  required: [Authorization, Content-Type, X-Trace-Id]
  properties:
    Authorization: { type: string }
    Content-Type: { type: string, enum: [application/json] }
    X-Trace-Id: { type: string, minLength: 8 }
  additionalProperties: false
request_schema:
  type: object
  required: [run_id, session_id, started_at, ended_at, model, role]
  properties:
    run_id: { type: integer }
    session_id: { type: string, minLength: 1, maxLength: 128 }
    started_at: { type: string, format: date-time }
    ended_at: { type: string, format: date-time }
    tokens_used: { type: integer, minimum: 0, nullable: true }
    cost_usd: { type: number, minimum: 0, nullable: true }
    model: { type: string, minLength: 1, maxLength: 128 }
    role: { type: string, minLength: 1, maxLength: 128 }
    related_plan_id: { type: string }
    detector_refs:
      type: array
      items: { $ref: '#/components/schemas/DetectorRef' }
  additionalProperties: false
response_schema:
  allOf:
    - $ref: '#/components/schemas/Envelope'
    - type: object
      properties:
        data:
          type: object
          required: [acknowledged, persisted_at]
          properties:
            acknowledged: { type: boolean }
            persisted_at: { type: string, format: date-time }
      additionalProperties: false
```

- `related_plan_id` は nullable 相当の任意値として扱う。
- `run_id` は必須で、`automation_runs.id` を参照する。
- `detector_refs` は session 終了時に発火した detector の集約を表す。
- error_codes: 400 / 401 / 404 / 409 / 500

## §4 共通制約

- push / pr / hook / audit / telemetry は append-only を基本とする
- 同一 `X-Trace-Id` での重複送信は idempotent に扱う
- 既存行の破壊更新は避け、追記で整合を保つ
- Authorization header は必須とし、secret / credential は request body に載せない
- `X-Trace-Id` は CLI / hook / audit / telemetry の横断追跡に使う
- 全 endpoint で `run_id` の扱いを明示し、push / pr trigger は response.data.run_id を必須返却、hook / audit / telemetry は request_schema.run_id を必須入力とする。
- `X-Trace-Id` は補助的に `automation_runs.id` を解決するために使い、各 endpoint の run_id 参照を補強する。
- 本稿の endpoint は Sprint .6 で整備される `automation_runs` / `audit_log` / `session_telemetry` へ流し込む前提とする

## §5 RACI

| endpoint | decision | implementation | verification | approval | documentation |
|---|---|---|---|---|---|
| push trigger | tl | se | qa | pm | docs |
| pr trigger | tl | se | qa | pm | docs |
| hook callback | tl | se | qa | pm | docs |
| audit log | tl | se | qa | pm | docs |
| session telemetry | tl | se | qa | pm | docs |

## §6 receiving gates

| endpoint | 起動 gate / hook | 備考 |
|---|---|---|
| push trigger | G3 / G4 / G6 | push 実行前後の gate 連動 |
| pr trigger | G3 / G4 / G6 | PR 生成と受入の前提を含む |
| hook callback | PreToolUse / PostToolUse / Stop / session_start | FR-GR04 と連携 |
| audit log | PostToolUse / Stop | footer / summary / diff_lines を受領 |
| session telemetry | Stop | session 終了時に集約 |

- FR-INV01: capability 棚卸しの証跡として audit / telemetry を補強する。
- FR-GR04: PreToolUse hook による block を hook callback endpoint で受ける。
- CON-06: bypass 不可の前提を崩さない。
- hook callback が blocked を返した場合は API 側でも 409 で閉じる。
- push / pr trigger は gate 未通過時に blocked を返し、楽観的継続をしない。

## §7 D-DB 連携

- 参照テーブル: `automation_runs` / `audit_log` / `session_telemetry`
- flow: 1) push/pr trigger → `automation_runs` INSERT（`run_id` 採番）→ response の `run_id` 返却 2) hook callback / audit / telemetry → request の `run_id` で `automation_runs` 参照 → `audit_log` / `session_telemetry` INSERT
- insert が基本であり update は最小化する
- duplicate は trace / run / session 単位で検出する
- replay 時は同一 payload を再利用しても row 破壊を起こさない

## §8 open questions / carry

- hook 実行内部の詳細設計
- detector 実行時の具体的な blocking policy
- CLI parsing の詳細な argv map
- skill 推挙 / Reverse / Scrum / code-index の残 capability
- audit / telemetry の cross-plan 集約の可視化
- `automation_runs` の v25+ migration 本文
- queued status は将来の非同期 trigger 対応で再評価、本 sprint では同期作成のみのため status enum から除外。

未確定事項は contract ではなく carry として明示する。
ここでの未確定は実装の自由度ではなく、後続 PLAN の責務として扱う。

## §9 受入チェック

- 5 endpoint が draft として固定されている。
- path / query / header / body が分離されている。
- `Envelope` / `ErrorModel` / `DetectorRef` / `PairStatusTransition` / `PromotionHookRef` を再利用している。
- error code が 400 / 401 / 404 / 409 / 500 に統一されている。
- `docs/plans/PLAN-070-l3-schema-and-contract-design.md` §3.E / §4.6 と矛盾しない。
- `docs/v2/L3-detailed-design/D-API/D-API-draft.md` §2.0 の共通 primitive と矛盾しない。
- `docs/v2/L1-REQUIREMENTS.md` FR-INV01 / FR-GR04 / CON-06 と整合する。

本稿で明示した `$ref` は同一 file 内の alias のみであり、`.md` 形式の外部参照は使わない。

## §10 変更ログ

- 2026-05-16: PLAN-070 SprintE / .5 の draft を起票。
- 2026-05-16: Sprint A primitive を再利用する endpoint contract 5 本を固定。
- 2026-05-16: hook / audit / telemetry を append-only 前提で整理。
- 2026-05-16: H-1 push/pr trigger response.data.run_id を string → integer に修正 (D-DB §3 automation_runs.id INTEGER に統一)。H-2 push/pr trigger status enum を [queued, running, passed, failed, blocked] → [running, passed, failed, blocked, cancelled] に修正 (D-DB §3 CHECK と完全一致)。
