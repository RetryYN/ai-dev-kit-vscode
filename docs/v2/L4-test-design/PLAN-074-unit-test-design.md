---
plan_id: PLAN-074
doc_id: PLAN-074-unit-test-design
title: "PLAN-074 単体テスト設計 (HTTP API framework + routes)"
status: maintained
artifact_role: "③ テスト設計 (V-model 4 artifact のうち)"
created: 2026-05-17
status_history:
  - 2026-05-17: 初期作成 (誤って Phase 3 で削除予定とした)
  - 2026-05-17: V-model 4 artifact 正解として保持決定 (PLAN-075 訂正)
owner: PM
related_docs:
  - docs/plans/PLAN-074-http-endpoint-layer.md
  - docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md (対象 ① 設計)
phases: L4
gates: G4
---

> **V-model 4 artifact 位置付け** (2026-05-17 訂正):
> 本書は ③ テスト設計 artifact。① 設計 (D-API EXT §3.X) と ④ テストコード (test_http_api_*.py) と
> 双方向 trace で繋がる独立 artifact として **保持する** (Phase 3 で削除しない)。
> PLAN-075 当初の誤解「同じ文書に統合」は訂正済。

# PLAN-074 単体テスト設計 (HTTP API framework + routes)

> 目的: PLAN-074 で実装した HTTP API 層 (framework + 5 endpoint) の単体テストを設計する。既存 27 cases (Flask test_client + 実 DB) は結合テストとして維持し、本設計では handler / helper level の独立挙動を **モック分離** で検証する単体テストを追加する。

## §1 位置付け (HELIX V-model テストピラミッド)

```
        E2E (L6 .L6.2 予定、25 シナリオ curl)
       /          \
      / Integration \  ← 既存 27 cases (test_http_api_*.py)
     /______________\
    /                \
   /   Unit tests     \  ← 本設計の対象 (約 62 cases)
  /____________________\
```

PLAN-074 §3 (Sprint .1-.5) で実装が先行し、単体テストが欠落した状態 (= 逆ピラミッド)。本設計で基礎を補強する。

**HELIX V-model 整合性**:

- L3 詳細設計 (D-API EXT §3.1-3.5): 機能設計、変更不要
- L4 実装: cli/lib/http_api/* (実装済)
- **L4 テスト設計 (本ドキュメント、現フェーズ)**: 単体テスト設計
- L4 テスト実装: 単体テスト Codex qa 委譲 (8 task 並列)
- L4 G4: 単体 + 結合 + coverage 80% 確認
- L6 E2E: 本物 Flask 環境で curl × 25 シナリオ

## §2 対象モジュール × 関数 × case 設計

### §2.1 auth.py

**対象設計 (① D-API)**: D-API EXT §3.1〜§3.5 共通 framework 層 (require_localhost_and_bearer 認証契約、全 5 endpoint で適用)。V-model 4 artifact 双方向 trace (PLAN-075)。
**実装ファイル (② D-IMPL)**: `cli/lib/http_api/auth.py`
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_http_api_auth.py` (新規、Phase 3.4a で実装)

| 関数 | case | 入力 | 期待出力 | mock |
|---|---|---|---|---|
| `require_localhost_and_bearer` | U-AUTH-001 | remote_addr=127.0.0.1, Bearer=valid | None (pass through) | request |
| | U-AUTH-002 | remote_addr=::1, Bearer=valid | None | request |
| | U-AUTH-003 | remote_addr=192.168.1.1 | Forbidden (403) | request |
| | U-AUTH-004 | remote_addr=127.0.0.1, Bearer なし | Unauthorized (401) | request |
| | U-AUTH-005 | remote_addr=127.0.0.1, Bearer=invalid_token | Unauthorized (401) | request, env |
| | U-AUTH-006 | HELIX_HTTP_API_TOKEN env 未設定 | 500 (config error) | request, env |

**case 数**: 6

### §2.2 envelope.py

**対象設計 (① D-API)**: D-API EXT §共通 Envelope schema (success / error response 構造、全 5 endpoint で適用)。V-model 4 artifact 双方向 trace (PLAN-075)。
**実装ファイル (② D-IMPL)**: `cli/lib/http_api/envelope.py`
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_http_api_envelope.py` (新規、Phase 3.4a で実装)

| 関数 | case | 入力 | 期待出力 |
|---|---|---|---|
| `success_response` | U-ENV-001 | data={"x": 1}, trace_id="abc12345" | dict {success: True, data: {x:1}, trace: {trace_id, generated_at}} |
| | U-ENV-002 | data=None | dict (data 不在 OK) |
| | U-ENV-003 | trace_id="" | trace_id 空文字 OK |
| `error_response` | U-ENV-004 | code="BAD_REQUEST", msg="x", trace_id="t" | dict {success: False, error: {code, message}, trace: ...}, status=400 |
| | U-ENV-005 | code="NOT_FOUND" | status=404 |
| | U-ENV-006 | code="INTERNAL" | status=500 |
| (helper) | U-ENV-007 | timestamp 生成 | ISO8601 形式 |
| | U-ENV-008 | timestamp 含有確認 | trace.generated_at が UTC |

**case 数**: 8 (純粋関数、mock なし)

### §2.3 validation.py

**対象設計 (① D-API)**: D-API EXT §3.1〜§3.5 各 request_schema (必須フィールド / 型 / 境界値の validation helper、全 5 endpoint 共通)。V-model 4 artifact 双方向 trace (PLAN-075)。
**実装ファイル (② D-IMPL)**: `cli/lib/http_api/validation.py`
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_http_api_validation.py` (新規、Phase 3.4a で実装)

| 関数 | case | 入力 | 期待出力 |
|---|---|---|---|
| validation helper | U-VAL-001 | 正常 dict | dict 返却 |
| | U-VAL-002 | 必須フィールド欠落 | ValueError |
| | U-VAL-003 | 型不正 (string 期待で int) | ValueError |
| | U-VAL-004 | 境界 (length 0 / max) | ValueError or pass |

**case 数**: 4

### §2.4 server.py

**対象設計 (① D-API)**: D-API EXT §framework (Flask app 構築、blueprint 登録、error handler、全 5 endpoint の組立て層)。V-model 4 artifact 双方向 trace (PLAN-075)。
**実装ファイル (② D-IMPL)**: `cli/lib/http_api/server.py`
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_http_api_server_unit.py` (新規、Phase 3.4a で実装。既存 `test_http_api_server.py` は結合 test として継続)

| 関数 | case | 入力 | 期待出力 | mock |
|---|---|---|---|---|
| `create_app` | U-SRV-001 | 引数なし | Flask app instance | Flask |
| | U-SRV-002 | blueprint 登録確認 | 5 blueprint 登録 | Flask |
| error handler | U-SRV-003 | 404 trigger | error_response 形式 | request |
| | U-SRV-004 | 500 trigger | error_response 形式 | request |
| | U-SRV-005 | カスタム例外 | 適切な status code | request |

**case 数**: 5

### §2.5 routes/audit.py

**対象設計 (① D-API)**: D-API EXT §3.4 audit endpoint (audit_kind enum drift 解決、payload.http_audit_kind 退避、helix_db.insert_audit_log の endpoint_call 固定)。V-model 4 artifact 双方向 trace (PLAN-075)。
**実装ファイル (② D-IMPL)**: `cli/lib/http_api/routes/audit.py`
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_http_api_routes_audit.py` (新規、Phase 3.4b で実装)

| 関数 | case | 入力 | 期待出力 | mock |
|---|---|---|---|---|
| `_request_json` | U-AUD-H-001 | request.get_json() = {"x": 1} | {"x": 1} | request |
| | U-AUD-H-002 | request.get_json() raises | {} (空 dict) | request |
| | U-AUD-H-003 | get_json() = None | {} | request |
| `HTTP_AUDIT_KINDS` validation | U-AUD-V-001 | "footer" | pass | - |
| | U-AUD-V-002 | "summary" | pass | - |
| | U-AUD-V-003 | "hook_exec" (internal) | reject (400) | - |
| | U-AUD-V-004 | "" | reject | - |
| | U-AUD-V-005 | None | reject | - |
| `audit_log` handler | U-AUD-001 | 正常 body | 200 + acknowledged | helix_db, sqlite3 |
| | U-AUD-002 | 必須欠落 | 400 | helix_db, sqlite3 |
| | U-AUD-003 | run_id 未存在 | 404 | helix_db (fetchone=None) |
| | U-AUD-004 | sqlite IntegrityError | 409 | sqlite3 (raise) |
| | U-AUD-005 | sqlite Error | 500 | sqlite3 (raise) |
| | U-AUD-006 | payload.http_audit_kind 退避確認 | helix_db.insert_audit_log called with audit_kind="endpoint_call" | helix_db.insert_audit_log (mock + spy) |

**case 数**: 14

### §2.6 routes/telemetry.py

**対象設計 (① D-API)**: D-API EXT §3.5 Stop hook telemetry endpoint (session_id UNIQUE 制約による idempotent UPSERT、tool_uses_count/tokens_total/cost_usd 累積)。V-model 4 artifact 双方向 trace (PLAN-075)。
**実装ファイル (② D-IMPL)**: `cli/lib/http_api/routes/telemetry.py`
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_http_api_routes_telemetry.py` (新規、Phase 3.4b で実装)

| 関数 | case | 入力 | 期待出力 |
|---|---|---|---|
| `_require_non_empty_string` | U-TEL-H-001 | "abc" | "abc" |
| | U-TEL-H-002 | None | None |
| | U-TEL-H-003 | "" | ValueError |
| | U-TEL-H-004 | "a" * 129 | ValueError (max 128) |
| `_require_timestamp_string` | U-TEL-T-001 | "2026-05-17T00:00:00Z" | string |
| | U-TEL-T-002 | "" | ValueError |
| | U-TEL-T-003 | None | ValueError |
| `session_telemetry` handler | U-TEL-001 | 正常 body | 200 + UPSERT | helix_db, sqlite3 |
| | U-TEL-002 | 必須欠落 | 400 | helix_db |
| | U-TEL-003 | UNIQUE 違反で UPSERT | 200 (idempotent) | sqlite3 |
| | U-TEL-004 | sqlite Error | 500 | sqlite3 |
| | U-TEL-005 | cost_usd 型不正 | 400 | helix_db |

**case 数**: 12

### §2.7 routes/hooks.py

**対象設計 (① D-API)**: D-API EXT §3.3 hook callback endpoint (hook_kind = pretool/posttool/stop/session_start、path と body の hook_kind 一致必須)。V-model 4 artifact 双方向 trace (PLAN-075)。
**実装ファイル (② D-IMPL)**: `cli/lib/http_api/routes/hooks.py`
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_http_api_routes_hooks.py` (新規、Phase 3.4c で実装)

| 関数 | case | 入力 | 期待出力 | mock |
|---|---|---|---|---|
| `hook_callback` handler | U-HK-001 | hook_kind=pretool, 正常 | 200 | helix_db |
| | U-HK-002 | hook_kind=posttool | 200 | helix_db |
| | U-HK-003 | hook_kind=stop | 200 | helix_db |
| | U-HK-004 | hook_kind=session_start | 200 | helix_db |
| | U-HK-005 | hook_kind=invalid | 400 | helix_db |
| | U-HK-006 | path と body の hook_kind 不一致 | 400 | helix_db |

**case 数**: 6

### §2.8 routes/push_pr.py

**対象設計 (① D-API)**: D-API EXT §3.1 push trigger endpoint + §3.2 pr trigger endpoint (push_gate.run_all_gates() 共通 gate 体系、run_kind=push/pr の automation_runs 登録)。V-model 4 artifact 双方向 trace (PLAN-075)。
**実装ファイル (② D-IMPL)**: `cli/lib/http_api/routes/push_pr.py`
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_http_api_routes_push_pr.py` (新規、Phase 3.4c で実装)

| 関数 | case | 入力 | 期待出力 | mock |
|---|---|---|---|---|
| `push_trigger` handler | U-PUSH-001 | execute=False, gate PASS | 200 + run_id | push_gate, helix_db |
| | U-PUSH-002 | execute=False, gate FAIL | 200 + failed gate | push_gate |
| | U-PUSH-003 | 必須欠落 | 400 | - |
| | U-PUSH-004 | plan_id 不正 (空) | 400 | - |
| `pr_trigger` handler | U-PR-001 | execute=False, gate PASS | 200 + run_id | push_gate, helix_db |
| | U-PR-002 | execute=False, gate FAIL | 200 + failed gate | push_gate |
| | U-PR-003 | 必須欠落 | 400 | - |
| | U-PR-004 | plan_id 不正 | 400 | - |

**case 数**: 8

## §3 case 数集計

| Module | case |
|---|---|
| auth.py | 6 |
| envelope.py | 8 |
| validation.py | 4 |
| server.py | 5 |
| routes/audit.py | 14 |
| routes/telemetry.py | 12 |
| routes/hooks.py | 6 |
| routes/push_pr.py | 8 |
| **合計** | **63 cases** |

## §4 モック戦略

### §4.1 mock 対象判断基準

- **外部 I/O** (DB / HTTP / file system): 必ず mock
- **同モジュール内 helper**: 原則 mock せず (combo test)
- **datetime.now / random**: 必要に応じて freezegun / patch
- **flask.request**: pytest fixture + MagicMock

### §4.2 標準パターン

```python
# pattern A: request mock
@pytest.fixture
def mock_request(monkeypatch):
    req = MagicMock()
    req.headers = {"Authorization": "Bearer test-token", "X-Trace-Id": "abc12345"}
    req.remote_addr = "127.0.0.1"
    req.get_json.return_value = {"x": 1}
    monkeypatch.setattr("cli.lib.http_api.routes.audit.request", req)
    return req

# pattern B: helix_db mock
@pytest.fixture
def mock_helix_db(monkeypatch):
    fake = MagicMock()
    fake.insert_audit_log = MagicMock(return_value=42)
    fake.get_helix_db_path = MagicMock(return_value="/tmp/test.db")
    monkeypatch.setattr("cli.lib.http_api.routes.audit.helix_db", fake)
    return fake

# pattern C: sqlite3 mock
@pytest.fixture
def mock_sqlite(monkeypatch):
    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = (1,)  # 正常時 run_id 存在
    monkeypatch.setattr("sqlite3.connect", lambda *a, **kw: conn)
    return conn
```

### §4.3 アンチパターン

- **既存 integration test を mock 化して unit に転換**: NG。integration は維持
- **mock で全部置き換え (handler 自体の logic を mock)**: NG。テストの意味がない
- **mock の戻り値だけ確認 (spy なし)**: NG。call 引数も assert する

## §5 ファイル構造規約

```
cli/lib/tests/
  unit/
    __init__.py
    test_http_api_auth_unit.py        (U-AUTH-001〜006)
    test_http_api_envelope_unit.py    (U-ENV-001〜008)
    test_http_api_validation_unit.py  (U-VAL-001〜004)
    test_http_api_server_unit.py      (U-SRV-001〜005)
    test_routes_audit_unit.py         (U-AUD-* 14 cases)
    test_routes_telemetry_unit.py     (U-TEL-* 12 cases)
    test_routes_hooks_unit.py         (U-HK-* 6 cases)
    test_routes_push_pr_unit.py       (U-PUSH-*, U-PR-* 8 cases)
```

- `unit/` サブディレクトリで結合テストと分離
- ファイル名 suffix `_unit.py` で `pytest cli/lib/tests/unit/` 単独実行可能
- 各 case 名は `test_<case_id>_<description>` 規約 (例: `test_U_AUTH_001_localhost_valid_bearer`)

## §6 受入条件 (G4 entry 単体テスト追加分)

- [ ] §2 の 63 cases を全件実装
- [ ] `pytest cli/lib/tests/unit/ -v` で 63/63 PASS
- [ ] 既存 `pytest cli/lib/tests/test_http_api_*.py` 27/27 維持 (回帰 0)
- [ ] coverage: cli/lib/http_api/ 80% 以上 (`helix code stats --scope cli-lib --bucket coverage_eligible --fail-under 80`)
- [ ] D-API EXT §3.X 各 endpoint に「単体テストファイル: test_routes_<endpoint>_unit.py」追記
- [ ] PLAN-074 §3 に Sprint .7 単体テスト実装 を追記 (WBS-074-L4-008)

## §7 Sprint 構成 (HELIX 標準粒度を厳守)

`.helix/task-plan.yaml` に以下を追加。

### Sprint .7 / WBS-074-L4-008 — 単体テスト 63 cases 実装

並列 4 task で投入 (HELIX 標準粒度 .1a/.1b/.2/.3/.4/.5):

| sub-sprint | 内容 | role | 並列性 |
|---|---|---|---|
| .7.1a | 本設計レビュー (Codex tl-advisor、任意) | tl-advisor | 単独 |
| .7.1b | unit/ dir 作成 + 共通 conftest.py + fixture | qa | 単独 |
| .7.2 | auth.py + envelope.py + validation.py + server.py の unit test (23 cases) | qa | task-A |
| .7.3 | routes/audit.py + telemetry.py の unit test (26 cases) | qa | task-B |
| .7.4 | routes/hooks.py + push_pr.py の unit test (14 cases) | qa | task-C |
| .7.5 | coverage 確認 + 回帰確認 + carry 整理 | Opus | 単独 |

**並列構造**:
- .7.1b → .7.2 / .7.3 / .7.4 を 3 並列投入 (異なる test ファイル、ファイル衝突なし)
- .7.5 で集約

estimate: 90 分 (3 並列 + 集約)

## §8 PLAN-074 §3 への組み込み

実装後、PLAN-074 §3 に Sprint .7 を追加:

```markdown
### Sprint .7 / WBS-074-L4-008 — 単体テスト 63 cases (Codex qa 並列)

- 機能設計: 本書 (PLAN-074-unit-test-design.md)
- 実装ファイル: cli/lib/tests/unit/test_*_unit.py (8 files)
- 担当 WBS: WBS-074-L4-008
- DoD: 63/63 PASS + 既存 27/27 維持 + coverage 80%
```

D-API EXT §3.X 各 endpoint には「**単体テストファイル**: test_routes_<endpoint>_unit.py」を追記する。

## §9 4 ノード trace の整合性

```
PLAN-074 §3 Sprint .7 / WBS-074-L4-008 ─┐
                                         │
PLAN-074-unit-test-design.md (本書) ────┤
                                         │
D-API EXT §3.X (機能設計参照、変更なし) ┤
                                         │
cli/lib/http_api/routes/*.py (実装) ────┤
                                         │
cli/lib/tests/unit/test_*_unit.py ──────┘ (本設計の case を実装)
```

5 ノード双方向 trace に拡張 (PLAN ⇔ test 設計 ⇔ 仕様 ⇔ 実装 ⇔ unit test)。

## §10 Next Action

1. 本設計のユーザー承認待ち
2. 承認後、`.helix/task-plan.yaml` に WBS-074-L4-008 (4 sub-sprint) を追加
3. Sprint .7.1b → .7.2 / .7.3 / .7.4 を 3 並列 Codex qa 委譲
4. Sprint .7.5 で coverage / 回帰確認 → commit + push
5. PLAN-074 §3 に Sprint .7 を追記
6. D-API EXT §3.1-3.5 に「単体テストファイル」を追記
