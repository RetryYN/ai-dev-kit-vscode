---
plan_id: PLAN-180
title: agent_slots SLA tracking (各 subagent の応答時間 SLA 計測・違反検出)
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-129-pmo-sonnet-stuck-recovery.md   # from dependencies.parent
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — agent_slot_sla_events テーブル + duration 計測 + SLA 違反判定ロジック実装"
  - role: qa
    slot_label: "QA — SLA 境界値テスト + auto-release 統合テスト"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-129 stuck recovery との責務境界確認・設計整合チェック"
generates:
  - artifact_type: schema_migration
    path: cli/lib/migrations/v37_agent_slot_sla_events.py
  - artifact_type: python_module
    path: cli/lib/agent_sla_tracker.py
  - artifact_type: cli_extension
    path: cli/helix-agent
  - artifact_type: test
    path: cli/lib/tests/test_agent_sla_tracker.py
  - artifact_type: doc_update
    path: docs/plans/PLAN-129-pmo-sonnet-stuck-recovery.md
dependencies:
  parent: PLAN-129
  requires:
    - PLAN-129
    - PLAN-146
  blocks: []
related_adr: []
related_docs:
  - docs/plans/PLAN-129-pmo-sonnet-stuck-recovery.md
  - docs/plans/PLAN-146-agent-slot-timeout-graduation.md
  - cli/lib/agent_mandatory.py
  - cli/helix-agent
  - cli/lib/helix_db.py
acceptance_criteria:
  - "agent_slot_sla_events テーブルが helix.db に存在し、invocation の開始・終了時刻と duration を記録できる"
  - "helix agent sla-report で weekly SLA compliance レポートが出力される"
  - "SLA 定義 (pmo-sonnet: p50=5min / p99=15min 他) が yaml_config で管理される"
  - "SLA 超過 30 分で auto-release が発動し PLAN-129 の release_slot に接続する"
  - "helix doctor check_agent_sla が SLA compliance < 80% で advisory WARN を出す"
  - "python3 -m py_compile cli/lib/agent_sla_tracker.py PASS"
  - "pytest test_agent_sla_tracker.py (8 case) 全 PASS"
  - "既存 helix agent slots / helix doctor pass 数に回帰なし"
---

# PLAN-180: agent_slots SLA tracking (各 subagent の応答時間 SLA 計測・違反検出)

## L2 凍結 (ADR snapshot)

helix.db schema 拡張 + advisory WARN パターンの繰り返し適用のため ADR snapshot は不要。
auto-release の fail-close 化判断は PLAN-129 で凍結済みの方針を踏襲する。

## 背景

2026-05-23 のセッションで pmo-sonnet が 30 分以上 stuck する事象が発生した。
PLAN-129 (pmo-sonnet stuck 検出 + auto-recovery hook) は stuck 後の回復を扱うが、
「各 subagent に SLA (Service Level Agreement) を定義し、超過を事前に可視化・自動介入する」
framework は存在しない。本 PLAN は以下を整備する:

1. 各 subagent role に SLA 目標値 (p50 / p99) を yaml_config で定義する
2. 全 invocation の duration を helix.db に記録し、SLA compliance を継続計測する
3. SLA 超過 30 分で PLAN-129 の auto-release に接続する
4. weekly SLA compliance レポートと helix doctor advisory WARN を提供する

## WebSearch 履歴 — skip

内部 helix.db 拡張 + Python 計測モジュールのみ。外部ライブラリ新規依存なし。

## SLA 定義 (初期値)

| role | p50s | p99s | auto-release s |
|---|---|---|---|
| pmo-sonnet | 300 | 900 | 1800 |
| pmo-haiku | 60 | 300 | 900 |
| pmo-{helix,project}-explorer | 120 | 600 | 1800 |
| pmo-tech-{docs,fork,news} | 180 | 900 | 1800 |
| pdm-* | 300 | 1800 | 3600 |

SLA 定義は `cli/config/agent_sla.yaml` で管理し、コードにハードコードしない。

## 設計方針

### helix.db テーブル設計

```sql
CREATE TABLE IF NOT EXISTS agent_slot_sla_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id INTEGER NOT NULL,           -- agent_slots.id への参照
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,                      -- NULL = 進行中
    duration_sec REAL,                  -- ended_at - started_at (秒)
    sla_p50_sec REAL NOT NULL,
    sla_p99_sec REAL NOT NULL,
    auto_release_threshold_sec REAL NOT NULL,
    sla_p50_met INTEGER,                -- 1=OK / 0=NG / NULL=進行中
    sla_p99_met INTEGER,
    auto_released INTEGER DEFAULT 0,    -- 1=auto-release 実行済
    metadata_json TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS ix_sla_events_role_started
  ON agent_slot_sla_events(role, started_at);

CREATE INDEX IF NOT EXISTS ix_sla_events_slot_id
  ON agent_slot_sla_events(slot_id);
```

- `ended_at` が NULL かつ `duration_sec` が auto-release 閾値を超えた行を SLA 超過として扱う
- `auto_released=1` は PLAN-129 の `release_slot(status='timeout')` 完了後にセット

### duration 計測ポイント

- **記録開始**: `helix agent fire` / `helix agent fire-mandatory` 実行時 (agent_slots への insert と同タイミング)
- **記録終了**: `helix agent slots release` / `release-stale` 実行時 (ended_at / duration_sec を UPDATE)
- SessionStart hook や Stop hook で進行中スロットを sweep し、終了未記録を補完する

### auto-release 統合 (PLAN-129 接続)

`agent_sla_tracker.check_auto_release_candidates()`:
- `ended_at IS NULL AND (strftime('%s','now') - strftime('%s', started_at)) > auto_release_threshold_sec` を検出
- PLAN-129 の `release_slot(slot_id, status='timeout')` を呼び出す
- `auto_released=1` に更新 + helix doctor 向け WARN ログ出力

呼び出しタイミング:
- `helix agent slots` (一覧表示) 実行時に副次チェック
- SessionStart hook での sweep
- 直接: `helix agent sla-check` サブコマンド

### helix doctor 統合

`helix doctor check_agent_sla`:
- 過去 7 日間の SLA events から role 別 p50 / p99 compliance 率を計算
- SLA compliance < 80% (p50) → advisory WARN
- auto_released > 0 件 → advisory WARN (stuck 発生の実績通知)
- サンプル 3 件未満の role → SKIP

## 実装計画

### Sprint .1: SLA 定義 yaml + schema migration + Python helper (Codex se、size S-M)

`cli/config/agent_sla.yaml` を新規作成 (初期値 10 role)。
`cli/lib/migrations/v37_agent_slot_sla_events.py` を新規作成。
`cli/lib/agent_sla_tracker.py` に以下の関数を実装:
- `start_event(slot_id, session_id, role) -> int` (event id を返す)
- `end_event(event_id, auto_released=False) -> None`
- `check_auto_release_candidates() -> list[int]` (対象 slot_id リスト)
- `weekly_sla_report() -> dict` (role 別 compliance 率)
- `check_sla_threshold(compliance_warn=0.80) -> list[str]` (helix doctor 向け)

`python3 -m py_compile` PASS + migration idempotent 確認が完了条件。

### Sprint .2: helix agent 統合 + PLAN-129 auto-release 接続 (Codex se、size S)

`cli/helix-agent` に以下を追加:
- `sla-report` — weekly compliance レポート表示
- `sla-check` — 即時 auto-release candidates 確認 + 実行オプション

`helix agent fire` / `helix agent slots release` / `helix agent slots release-stale` の各処理に
`start_event` / `end_event` 呼び出しを組み込む。
PLAN-129 の `release_slot` 呼び出し経路との二重 release 防止 (`auto_released` flag で排他)。

`bash -n cli/helix-agent` PASS + SLA event が DB 記録されることの手動確認が完了条件。

### Sprint .3: helix doctor 統合 + bats / pytest (Codex qa、size S)

`helix doctor check_agent_sla` 実装。
`cli/lib/tests/test_agent_sla_tracker.py` で 8 case:
- T1: start_event / end_event で duration_sec が正確に計算される
- T2: ended_at NULL + 閾値超過で check_auto_release_candidates に返る
- T3: ended_at あり (正常完了) は auto_release_candidates に含まれない
- T4: weekly_sla_report — p50 compliance 計算正確性
- T5: weekly_sla_report — サンプル不足 (< 3 件) で role を SKIP
- T6: check_sla_threshold — compliance=0.799 で WARN、0.800 で pass
- T7: auto_released=1 の重複 release 防止 (二重呼び出しで idempotent)
- T8: `datetime.now(timezone.utc)` ベースの動的 timestamp (固定値禁止)

pytest 8 PASS + helix doctor pass 数現行以上が完了条件。

### Sprint .4: PLAN-129 docs 双方向 trace 追記 + pmo-sonnet review (PMO、size S)

PLAN-129 に PLAN-180 連携注記を追加。pmo-sonnet で責務境界・二重 release 防止を確認。

## mandatory in sprint

- [ ] `python3 -m py_compile cli/lib/agent_sla_tracker.py` PASS
- [ ] migration idempotent 確認 / pytest 8 PASS / `bash -n cli/helix-agent` PASS
- [ ] 既存 `helix agent slots` / `helix doctor` 回帰なし
- [ ] pmo-sonnet review (Sprint .4)

## DoD

- [ ] `agent_slot_sla_events` テーブル migration 実装済み
- [ ] `cli/config/agent_sla.yaml` SLA 定義 10 role 分記載済み
- [ ] `agent_sla_tracker.py` duration 計測 + auto-release 接続 実装済み
- [ ] `helix agent sla-report` / `helix agent sla-check` 動作確認済み
- [ ] `helix doctor check_agent_sla` advisory WARN 実装済み
- [ ] PLAN-129 docs 双方向 trace 追記済み
- [ ] pytest 8 case 全 PASS
- [ ] helix doctor pass 数現行以上

## carry / 学び

- auto-release 閾値は `cli/config/agent_sla.yaml` に寄せ、ハードコード禁止。
- Sprint .2 着手前に PLAN-129 stuck 検出と duration 計測の重複処理を整理する。
- 全 timestamp は `datetime.now(timezone.utc)` で統一 (`datetime.utcnow()` 禁止、[[feedback_pytest_fixture_time_dependent_flake]])。
- SessionStart sweep は fail-open (hook 失敗で session を block しない)。

## 関連 reference

- PLAN-129 (parent) / PLAN-146 (依存) / cli/lib/agent_mandatory.py
