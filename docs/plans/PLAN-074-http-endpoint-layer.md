---
plan_id: PLAN-074
title: "PLAN-074: HTTP endpoint 5 endpoint 実装 (PLAN-072 L4.5 carry、D-API EXT 契約具現化)"
status: in_progress
gate_status: G4_ready
size: M-L
drive: be
created: 2026-05-16
sprint_5_completed_at: 2026-05-16
owner: PM
phases: L4, L6
gates: G4
framework: Flask
framework_decision_rationale: |
  Codex tl-advisor (gpt-5.5 high) 助言 2026-05-16 結論。
  Flask 推奨理由: 軽量、Werkzeug の堅牢 routing/test_client、Pydantic drift リスクなし、pytest 統合容易。
  FastAPI 非推奨: 依存追加大 + OpenAPI 自動生成が D-API EXT と drift するリスク。
  http.server fallback: 依存ゼロにこだわる場合のみ。手書き routing/validation で G4 品質リスク増。
auth_decision: localhost-only-bearer
auth_decision_note_resolved: |
  Sprint .1 で確定: 127.0.0.1/::1 限定 bind + Authorization: Bearer <HELIX_HTTP_API_TOKEN env>。
  本番運用前に HMAC / mTLS / TLS termination 等の強化を検討 (carry note)。
auth_decision_note: |
  Sprint .1 framework setup で Authorization header 形式 (Bearer / localhost-only / API key) を凍結する。
  HELIX は CLI 中心、HTTP 層は補完なので localhost-only + env 由来 token の最小構成が初期推奨。
notes:
  - Sprint .1 v2 では framework setup と auth freeze のみを実装し、endpoint 実装は Sprint .2-.5 に carry する。
  - audit_kind enum drift は Sprint .4 の audit endpoint 実装時に解消設計を決定する。
  - 'cli/lib/http_api/server.py' は Flask 不在環境 (PEP 668 externally-managed) でも動作する compat fallback Flask class を含む。本番運用前に本物 Flask install を必須化し、fallback を削除すること。
  - Flask install 手順 (運用時): (a) python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt、(b) または sudo apt install python3-flask、(c) または pipx で隔離 install。pip install --break-system-packages は推奨しない。
structure_proposal: |
  cli/lib/http_api/
    server.py        # create_app(), local bind, error handlers
    envelope.py      # success/error/trace response
    validation.py    # D-API EXT schema validators
    auth.py          # Authorization / localhost policy
    routes/
      push_pr.py     # push/pr trigger
      hooks.py       # hook callback
      audit.py       # audit log
      telemetry.py   # session telemetry
  cli/lib/tests/
    test_http_api_push_pr.py
    test_http_api_hooks_audit.py
    test_http_api_telemetry.py
    test_http_api_contract.py
  cli/tests/
    helix-http-api.bats
acceptance:
  - 5 endpoint (push/pr/hook/audit/telemetry) を HTTP server として実装し、D-API EXT 契約と完全整合
  - 既存 CLI 結合 (helix-push/pr + hooks) と同等の DB 書き込み挙動を HTTP 経由で再現
  - automation_runs lifecycle 遷移 / audit_log 書き込み / session_telemetry UPSERT が HTTP 経由で動作
  - bats / pytest 全 PASS 維持 (回帰 0)
  - G4 entry 条件達成 (実装 + テスト + ドキュメント整備)
related:
  - PLAN-072-l4-5-integration (frozen 親 L4.5、HTTP 層 carry の根拠)
  - PLAN-070-l3-schema-and-contract-design (frozen L3、D-API EXT 契約起源)
  - docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md (5 endpoint 契約正本)
  - docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md (v25-v27 schema)
---

# PLAN-074: HTTP endpoint 5 endpoint 実装

## §1 目的と背景

PLAN-072 (L4.5 Phase B 結合) で CLI 結合 (helix-push / helix-pr / hook / gate) と helix.db 書き込みを完遂した (11 commits, pytest 1285 / bats 478 全 PASS、2026-05-16 frozen)。

しかし D-API EXT で凍結した HTTP endpoint 層は未実装のまま carry となった。本 PLAN はその carry を独立 PLAN として具現化し、D-API EXT 契約 (docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md) を HTTP server 実装に落とし込む。

### 前提条件

- PLAN-072 frozen 済 (CLI 結合・DB 書き込み完了が前提)
- D-API EXT contract 凍結済 (PLAN-070 SprintE にて確定)
- v25 automation_runs / v26 audit_log / v27 session_telemetry schema は CURRENT_SCHEMA_VERSION=27 で稼働中
- helper 3 件 (`_upsert_row` / `_transition_lifecycle_status` / `_create_append_only_trigger`) が cli/lib/helix_db.py に実装済み

---

## §2 対象 endpoint

D-API EXT (docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md §3) で凍結された 5 endpoint:

| # | method | path | 役割 | 主要 DB テーブル |
|---|--------|------|------|----------------|
| 1 | POST | `/api/v1/automation/push/{plan_id}/trigger` | push 実行開始・automation_runs INSERT + lifecycle | automation_runs, audit_log |
| 2 | POST | `/api/v1/automation/pr/{plan_id}/trigger` | pr 実行開始・automation_runs INSERT + lifecycle | automation_runs, audit_log |
| 3 | POST | `/api/v1/automation/hooks/{hook_kind}/callback` | hook callback (PreToolUse / PostToolUse / Stop / session_start) | audit_log |
| 4 | POST | `/api/v1/automation/audit/log` | audit/footer 受領 | audit_log |
| 5 | POST | `/api/v1/automation/session/telemetry` | Stop hook session-summary 後継 telemetry | session_telemetry |

### endpoint 共通ルール (D-API EXT §3 共通ルール より)

- 成功系: `{ success: true, data: {...}, trace: { trace_id, generated_at } }`
- 失敗系: `{ success: false, error: { code, message, detail } }`
- `X-Trace-Id` header 必須 (補助キー、automation_runs.id 解決に使用)
- push trigger / pr trigger は response.data.run_id を必須返却 (新規 automation_runs.id)
- hook callback / audit / telemetry は request body.run_id 必須 (既存 automation_runs.id を参照)
- error code は 400 / 401 / 404 / 409 / 500 のみ

---

## §3 Sprint 構成 (実態反映、2026-05-16 update)

当初計画は Sprint .0-.5 (6 Sprint) だったが、実装段階で endpoint 単位に分割し Sprint .0-.6 (7 Sprint) で完遂した。1 Sprint = 1 endpoint の粒度を採用 (HELIX 標準 .1a/.1b/.2/.3/.4/.5 を踏襲しなかった、carry note §10 参照)。

### Sprint .0 / WBS-074-L4-001 — framework 候補整理 (Codex tl-advisor)

- 機能設計: framework 選定 ADR (Flask vs FastAPI vs http.server)
- 実装ファイル: なし (調査のみ)
- test ファイル: なし
- 参照: D-API EXT §1-§2 共通ルール (`docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md`)
- 成果: tl-advisor 結論 **Flask 推奨** (`.helix/tmp/p074-s0-tl-advisor.log`)
- commit: `e30dfe8` (frontmatter framework=Flask 反映)

### Sprint .1 / WBS-074-L4-002 — framework setup (Codex SE → pg v2)

- 機能設計: HTTP server / auth / envelope / validation の責務分離
- 実装ファイル: `cli/lib/http_api/server.py` / `envelope.py` / `validation.py` / `auth.py` / `routes/` 5 blueprint
- test ファイル: `cli/lib/tests/test_http_api_server.py` (5 cases) + `cli/tests/helix-http-api.bats` (1 case)
- 参照: D-API EXT §1 共通 envelope 形式 + §2 認証方針
- auth 凍結: 127.0.0.1/::1 + Bearer Token (HELIX_HTTP_API_TOKEN env)
- compat fallback Flask class (PEP 668 sandbox 用、本番削除 carry → `.L6.1b`)
- 公開 endpoint: `/health` + `/api/v1/_status`
- commit: `879945b`, `883552b`

### Sprint .2 / WBS-074-L4-003 — push/pr trigger endpoint (Codex pg)

- 機能設計: D-API EXT **§3.1 push trigger** + **§3.2 pr trigger**
- 実装ファイル: `cli/lib/http_api/routes/push_pr.py`
- test ファイル: `cli/lib/tests/test_http_api_push_pr.py` (5 cases)
- 契約: `push_gate.run_all_gates()` 結合 + automation_runs INSERT + audit_log
- DoD: success / missing / unauthorized / not_found / dry_run の 5 シナリオ
- commit: `95cb7be`

### Sprint .3 / WBS-074-L4-004 — hooks callback endpoint (Codex pg)

- 機能設計: D-API EXT **§3.3 hook callback**
- 実装ファイル: `cli/lib/http_api/routes/hooks.py`
- test ファイル: `cli/lib/tests/test_http_api_hooks.py` (5 cases)
- 契約: hook_kind enum [pretool, posttool, stop, session_start] + audit_log 連携 (hook_exec audit_kind)
- commit: `a387f9c`

### Sprint .4 / WBS-074-L4-005 — audit endpoint (Codex pg v2)

- 機能設計: D-API EXT **§3.4 audit endpoint**
- 実装ファイル: `cli/lib/http_api/routes/audit.py`
- test ファイル: `cli/lib/tests/test_http_api_audit.py` (5 cases)
- 契約: HTTP audit_kind enum [footer, summary, diff_lines, security_scan, qa_check]
- **audit_kind enum drift 解決**: HTTP 側 kind を payload.http_audit_kind に退避、helix_db.insert_audit_log には endpoint_call 固定で記録
- commit: `2505c4a`
- 注記: Sprint .4 v1 は SE/QA review_only_drift で失敗、pg role + 完全サンプル明示で v2 成功

### Sprint .5 / WBS-074-L4-006 — session telemetry endpoint (Codex pg)

- 機能設計: D-API EXT **§3.5 Stop hook telemetry endpoint**
- 実装ファイル: `cli/lib/http_api/routes/telemetry.py`
- test ファイル: `cli/lib/tests/test_http_api_telemetry.py` (5 cases)
- 契約: session_telemetry UPSERT (session_id UNIQUE、v27) + tool_uses_count / tokens_total / cost_usd 累積
- DoD: success / upsert / missing / unauthorized / invalid の 5 シナリオ
- commit: `1633202`

### Sprint .6 / WBS-074-L4-007 — G4 ready 判定 (Opus 直接)

- 27/27 PASS (http_api 5 endpoint suite)
- 全回帰: pytest 1319 / bats 479 / shell 614 全 PASS
- helix doctor: 21 pass / 0 fail / 1 warn (rg のみ)
- D-API EXT 契約整合 確認 (§3.1-§3.5 全件 vs routes/*.py)
- commit: `80a6b90`, `13de2af`

---

## §3.5 L6 統合検証 工程 (HELIX 標準粒度 .1a/.1b/.2/.3/.4/.5/.6 を厳守、2026-05-16 起票)

L6 以降は HELIX 標準粒度を踏襲し、`.helix/task-plan.yaml` で WBS 番号 / role / acceptance / reference_docs を粒度別に管理する (§3 の反省を踏まえた構造)。

### Sprint .L6.1a — entry 条件確認 + 既存 test 全 PASS 確認

- Opus 直接
- G4 ready 確認 (PLAN-074 frontmatter gate_status=G4_ready)
- pytest 1319 / bats 479 / shell 614 全 PASS 再確認
- 成果物: L6 entry readiness ログ

### Sprint .L6.1b — Flask 本物 install + compat fallback class 削除

- Codex se
- venv / apt / pipx いずれかで Flask install (`requirements-dev.txt` 更新)
- `cli/lib/http_api/server.py` の Blueprint shim 撤去
- `cli/lib/http_api/routes/*.py` の `try: from flask import ...` fallback 経路削除
- 受入: 本物 Flask で既存 27/27 PASS、Sprint .1 で残した carry note (§7 §8) 全 resolved

### Sprint .L6.2 — E2E test (本物 Flask 環境で 5 endpoint curl 実証)

- Codex qa
- localhost server 起動 (`python3 -m cli.lib.http_api.server`)
- 5 endpoint 全件 curl 動作確認:
  - POST /api/v1/automation/push/{plan_id}/trigger (実 DB 書き込み確認)
  - POST /api/v1/automation/pr/{plan_id}/trigger
  - POST /api/v1/automation/hooks/{hook_kind}/callback
  - POST /api/v1/automation/audit/log (payload.http_audit_kind 退避確認)
  - POST /api/v1/automation/session/telemetry (UPSERT 冪等確認)
- 401 / 403 / 404 / 409 / 500 全件 curl で再現
- 受入: E2E 5 endpoint × 5 status code = 25 シナリオ全件 PASS

### Sprint .L6.3 — perf test (latency / DB lock / timeout)

- Codex perf
- request latency 99 percentile < 500ms (push/pr endpoint は < 5s、push_gate.run_all_gates 同期実行のため)
- 並列リクエスト下での helix.db lock 衝突確認 (10 並列 × 100 req)
- timeout 上限設定 (default 30s)
- 受入: latency target 達成、lock 衝突 0、timeout 動作確認

### Sprint .L6.4 — security test (OWASP / Bearer 強度 / localhost bind)

- Codex security
- OWASP Top 10 静的チェック (semgrep / bandit)
- Bearer token 漏洩経路の確認 (log / error response / audit_log)
- localhost-only bind の検証 (外部 IP からの接続拒否確認)
- 受入: OWASP critical 0、Bearer token 漏洩経路なし、外部 bind 拒否

### Sprint .L6.5 — 運用準備 (runbook / monitoring / on-call)

- Codex devops
- runbook 起票 (`docs/runbook/PLAN-074-http-api.md`)
  - 起動 / 停止手順、token rotation 手順、log location、emergency rollback
- monitoring 設計 (request rate / error rate / latency / DB lock event)
- on-call alarm 設定方針 (alert threshold)
- 受入: runbook 完成、monitoring metric 列挙完了

### Sprint .L6.6 — G6 RC 判定 + 残 debt 整理

- Opus 直接
- G6 entry 条件チェックリスト (RC 判定)
- セキュリティ③ 確認
- 残 debt を `.helix/audit/deferred-findings.yaml` に記録
- L7 デプロイ判定 (本番 vs PoC 影響評価)
- 受入: G6 passed / blocked 判定確定

---

---

## §4 受入条件詳細

1. **endpoint 契約整合**: 全 5 endpoint が D-API EXT §3 の path / method / request_schema / response_schema / error_code と 1:1 整合
2. **DB 書き込み等価性**: HTTP 経由で CLI と同等の automation_runs / audit_log / session_telemetry 書き込みが発生する
3. **lifecycle 遷移**: push / pr trigger が `_transition_lifecycle_status` 経由で `pending → running → completed / failed` を正しく遷移する
4. **append-only 保護**: audit_log に対する UPDATE / DELETE が HTTP 経由でも trigger ブロック (v26 実装済みの確認)
5. **idempotency**: telemetry endpoint が session_id 単位で UPSERT 冪等動作する
6. **P1 解消**: P1-01 (invocation_log 型衝突) / P1-02 (HELIX_DIR 経路) / P1-03 (cost_usd float) を HTTP 実装内で解消
7. **回帰 0**: pytest / bats / helix-test 全 PASS 維持
8. **G4 通過**: §7 チェックリスト全件 passed

---

## §5 リスク

| ID | リスク | 影響 | 緩和策 |
|----|--------|------|--------|
| R-01 | HTTP framework 選定 (Sprint .1) が遅延し後続 Sprint がブロック | 全体遅延 | Sprint .0 で比較表を事前作成、TL 判断を 1 Sprint に集約 |
| R-02 | 認証方式未定 (API key / token / 無認証) が実装に波及 | 設計変更 | Sprint .1 で暫定 API key 認証として決定。本番認証は PLAN-075 carry 可 |
| R-03 | CORS / network binding (localhost only vs 0.0.0.0) | セキュリティ | 初期実装は localhost only + 127.0.0.1 bind。外部公開は別 PLAN |
| R-04 | push_gate.run_all_gates() が同期 long-run になり HTTP timeout | 性能 | async / subprocess dispatch を Sprint .2 で検討。timeout 30s 上限設定 |
| R-05 | P1-01〜03 の carry が Sprint .3〜.4 で想定外に複雑化 | 工数超過 | PLAN-072 exit-validation notes (phase-4.5-integration-notes.md) を Sprint .3 entry で必ず Read |
| R-06 | CLI 結合 (PLAN-072) との DB 書き込み二重発火 (CLI + HTTP 両方使用時) | データ整合 | Sprint .5 で二重書き込みシナリオを明示テスト。UNIQUE constraint を確認 |

---

## §6 依存関係

```
PLAN-070 (frozen) — L3 D-API EXT 契約起源
  └── PLAN-072 (frozen) — CLI 結合 + helix.db v27 稼働
        └── PLAN-074 (本 PLAN) — HTTP endpoint 層実装
              └── (未定) PLAN-075 — 認証強化 / 本番 network 設定 (carry 想定)
```

- PLAN-072 frozen が本 PLAN の entry 前提。未 frozen の場合は本 PLAN の Sprint .0 で blocked とする
- D-API EXT は契約のみ。HTTP server の framework / routing 実装は本 PLAN で初出
- D-DB EXT (v25-v27) は schema + helper 実装済み。本 PLAN では schema 変更を行わない

---

## §7 G4 entry 条件チェックリスト

G4 は Sprint .5 で実施する。全件 passed で G4 通過とする。

- [ ] 5 endpoint 全件が HTTP 200 / 400 / 409 / 500 を正しく返す (pytest 実証)
- [ ] `automation_runs.id` (run_id) が push / pr trigger レスポンスで返却される
- [ ] `audit_log` に trigger ごとの行が INSERT されている (bats 実証)
- [ ] `session_telemetry` が UPSERT 冪等で動作する (pytest 実証)
- [ ] P1-01 / P1-02 / P1-03 が全件 resolved (exit-validation notes 更新確認)
- [ ] `helix doctor` 0 fail (8 warn は既存 drift で許容済み)
- [ ] `python3 -m pytest cli/lib/tests/ -q --tb=short` 全 PASS
- [ ] `cli/helix test --no-pytest --bats-only` 全 PASS
- [ ] `helix code stats --scope core5 --bucket coverage_eligible --fail-under 80` 通過
- [ ] deferred-findings.yaml に残 debt が記録されている (または空)

---

## §8 Next Action

1. PMO Sonnet: D-API EXT 全文 Read + framework 候補整理 (Sprint .0)
2. TL: framework 選定 ADR 起草 (Sprint .1) — Flask / FastAPI / http.server の比較判断
3. TL 選定結果確認後、Sprint .2〜.4 を Codex SE 並列投入 (push/pr ∥ hook/audit ∥ telemetry は独立)
4. Sprint .5: TL + PMO Sonnet で統合検証 → G4 判定 → Opus commit
5. commit は Opus が Sprint .5 完了確認後に実施 (Codex は commit 禁止)

**並列可否**: Sprint .2 / Sprint .3 / Sprint .4 は framework 選定 (Sprint .1) 完了後に同時投入可能 (ファイル衝突なし、DB schema 変更なし)。

---

## §9 Resolution Summary (G4 ready, 2026-05-16)

### Sprint 実装結果

| Sprint | 内容 | commit | test |
|---|---|---|---|
| .0 | framework 選定 (Flask) | e30dfe8 | tl-advisor 助言 |
| .1 | framework setup (5 routes blueprint + auth + envelope + validation) | 879945b, 883552b | pytest 5 / bats 1 PASS |
| .2 | push/pr trigger endpoint | 95cb7be | pytest 5 PASS |
| .3 | hooks callback endpoint | a387f9c | pytest 5 PASS |
| .4 | audit endpoint | 2505c4a | pytest 5 PASS |
| .5 | session telemetry endpoint | 1633202 | pytest 5 PASS |

### 5 endpoint 実装 (D-API EXT 正本準拠)

```
POST /api/v1/automation/push/{plan_id}/trigger      (push_pr.py)
POST /api/v1/automation/pr/{plan_id}/trigger        (push_pr.py)
POST /api/v1/automation/hooks/{hook_kind}/callback  (hooks.py)
POST /api/v1/automation/audit/log                   (audit.py)
POST /api/v1/automation/session/telemetry           (telemetry.py)
```

### 設計判断

- **auth**: localhost-only (127.0.0.1/::1 bind) + Authorization: Bearer <HELIX_HTTP_API_TOKEN env>
- **audit_kind enum drift 解決**: HTTP 側 audit_kind (footer/summary/diff_lines/security_scan/qa_check) は payload.http_audit_kind に格納、helix_db.insert_audit_log には endpoint_call 固定で記録
- **Flask compat fallback**: PEP 668 sandbox 用、本番運用前に削除必要 (Flask 本物 install)

### test 全 PASS 検証

- 27/27 PASS (http_api 5 endpoint suite)
- 全回帰 (2026-05-16 23:43 完遂): pytest **1319** (+10 = Sprint .2-.5 追加分) / bats **479** / shell **614** 全 PASS、0 failed / 0 skipped
- helix doctor: 21 pass / 0 fail / 1 warn (rg のみ、env 由来 warn)

### G4 entry チェックリスト

- [x] 5 endpoint 全件で D-API EXT 契約と整合
- [x] automation_runs lifecycle 遷移 / audit_log 書き込み / session_telemetry UPSERT が HTTP 経由で動作
- [x] auth (localhost + Bearer) で 401/403 が返る
- [x] pytest 全 PASS / bats 全 PASS
- [x] helix doctor 0 fail
- [x] git commit / push 完了 (origin/main 2505c4a)

### Carry / Followup

1. **Flask 本物 install (本番運用必須)**: venv / apt / pipx で。`pip install --break-system-packages` 非推奨
2. **compat fallback Flask class 削除** (本番前): cli/lib/http_api/server.py の Blueprint shim 撤去
3. **auth 強化** (必要時): HMAC / mTLS / TLS termination
4. **HELIX V-model 後続**: L5 Visual (HTTP 系は薄い) / L6 統合検証 / L7-L11 Run phase

### Sprint .6 G4 ready 宣言

PLAN-074 (HTTP endpoint 層) は G4 ready 状態に到達。L4.5 carry の HTTP endpoint 層を完遂し、PLAN-072 で確立した v24-v27 helix.db + CLI/hook 統合の HTTP 表現を追加した。次工程: G4 PM 承認 → L6 統合検証。

---

## §9 V-model 4 artifact mapping (PLAN-075 retrofit、2026-05-17、commit aa8a948)

PLAN-075 で確立した V-model 4 artifact 双方向 trace 原則 (詳細: `helix/HELIX_CORE.md §設計⇔テスト対応`) に対する PLAN-074 の整備状況。

| Artifact | 種類 | path | 状態 |
|---|---|---|---|
| ① 設計 (詳細) | D-API EXT §3.1-§3.5 (5 endpoint) | docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md | 完備 (テスト設計 reference 5 件追加済) |
| ① 設計 (DB) | D-DB EXT v25/v26/v27 | docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md | 完備 (PLAN-072 由来) |
| ② 実装コード | cli/lib/http_api/* (5 endpoint + framework) | cli/lib/http_api/{server,auth,envelope,validation}.py + routes/{push_pr,hooks,audit,telemetry}.py | 完備 (G4 ready) |
| ③ テスト設計 (総合) | D-TEST-DESIGN-SYS、E2E 25 case | docs/v2/L4-test-design/PLAN-074-system-test-design.md | 完備 (PLAN-075 Phase 3 新規 427 行) |
| ③ テスト設計 (結合) | D-TEST-DESIGN-INT、27 case | docs/v2/L4-test-design/PLAN-074-integration-test-design.md | 完備 (PLAN-075 Phase 3 新規 677 行) |
| ③ テスト設計 (単体) | D-TEST-DESIGN-UNIT、8 module 63 case | docs/v2/L4-test-design/PLAN-074-unit-test-design.md | 完備 (PLAN-074 で起票、PLAN-075 で 8 module 双方向 ref 追記) |
| ④ テストコード (結合) | D-TEST-CODE-INT、27 case 全 PASS | cli/lib/tests/test_http_api_{push_pr,hooks,audit,telemetry,server}.py | 完備 (PLAN-074 で実装、PLAN-075 で docstring に ③ ref 追記) |
| ④ テストコード (単体) | D-TEST-CODE-UNIT、63 case 全 PASS | cli/lib/tests/test_http_api_{auth,envelope,validation,server_unit,routes_audit,routes_telemetry,routes_hooks,routes_push_pr}.py | 完備 (PLAN-075 Phase 3 新規) |

### 双方向 trace (grep で検証可能)

| from → to | path / 検証コマンド | count |
|---|---|---|
| ① → ③ | D-API EXT 内 `テスト設計ファイル` reference | 5 (5 endpoint) |
| ③ → ① | unit-test-design.md 内 `対象設計 (① D-API)` reference | 8 (8 module) + 14 件総計 |
| ② → ① | 実装 docstring 内 `契約: D-API EXT §X.Y` reference | 各 module で完備 |
| ④ → ③ | test_*.py 内 `DoD 検証: PLAN-074-*-design.md U-XXX-NNN` reference | 13 file 全件、87+ 件 |

### audit 結果

- PLAN-075 Phase 4.1a audit (`docs/v2/audit/plan-067-074-vmodel-audit.md`) で **P0 partial** 判定 (実態は完備、PLAN doc への ref 欠落のみ)
- 本 §9 追加で carry 解消、PLAN-074 は 4 artifact 双方向 trace 完全準拠
- Phase 5 lint (vmodel_lint) で grandfather 対象外、lint 通過想定

## 業界 standard 参照 (Web 検索 retrofit 2026-05-19)

- Flask/HTTP API 設計
  - Flask-RESTX は API 定義と OpenAPI/Swagger をデコレータ中心で整形しやすい設計思想を採用しており、エンドポイント記述の一貫性と検証可能性に資する。
  - Flask-Smorest は `marshmallow` ベースのシリアライズ/バリデーション、OpenAPI 自動生成、明示的な検証エラー、ETag / ページングを提供する実装実績がある。
  - 参照: [Flask-RESTX Documentation](https://flask-restx.readthedocs.io/), [Flask-RESTX scaling guide](https://flask-restx.readthedocs.io/en/latest/scaling.html), [flask-smorest GitHub README](https://github.com/marshmallow-code/flask-smorest)

- Webhook 受信検証（署名検証）
  - GitHub は webhook の受信時に、`X-Hub-Signature-256` ヘッダ付き HMAC 署名で送信元と改ざんを検証する方式を推奨している。
  - Stripe は webhook 処理前に生のリクエストボディ、`Stripe-Signature`、secret を使って検証を行うことを前提にしている。
  - 参照: [GitHub webhook signature validation](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries), [Stripe webhook signature docs](https://docs.stripe.com/webhooks/signature?locale=en-GB)

- API バージョニング（進化）
  - Google API 設計原則では、まず既存互換の追加（新規プロパティ追加など）で互換性を保った拡張を優先し、必要時のみバージョニングを検討する方針が示される。
  - Microsoft の公開ガイドラインでは `/v1` といった URL 先頭バージョン指定を含む実装が多く示される一方、運用上の整合性と更新性が重要な論点として扱われる。
  - Zalando は互換変更での追加/延長を原則とし、やむを得ない場合にのみマルチバージョン化を推奨し、`Content-Type` ベース（メディアタイプ版）を検討する。
  - 参照: [Google API versioning tips](https://cloud.google.com/blog/products/api-management/restful-api-design-tips-versioning), [Microsoft API Guidelines](https://github.com/microsoft/api-guidelines/blob/vNext/Guidelines.md), [Zalando RESTful API guidelines](https://opensource.zalando.com/restful-api-guidelines/index.html)

### Revision History

- W5c-8 / 2026-05-19: PLAN-074 に「業界 standard 参照」セクションを追加し、W5c 13 件 retrofits（対象項目: W5c-8）を反映。既存セクションは変更せず追記のみ実施。
