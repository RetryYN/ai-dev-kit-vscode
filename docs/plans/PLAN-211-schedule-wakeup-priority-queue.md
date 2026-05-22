---
plan_id: PLAN-211
title: ScheduleWakeup priority queue (urgent vs background wake-up event 管理)
status: draft
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
    slot_label: "SE — wake_queue テーブル + WakeupScheduler クラス + next-event 計算ロジック実装"
  - role: qa
    slot_label: "QA — priority 別 fire time 境界値テスト + carry count 閾値テスト"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-099 ScheduleWakeup 既存設計との責務境界・衝突リスク確認・G4 review"
generates:
  - artifact_type: schema_migration
    path: cli/lib/migrations/v38_wake_queue.py
  - artifact_type: python_module
    path: cli/lib/wakeup_scheduler.py
  - artifact_type: cli_extension
    path: cli/helix-schedule
  - artifact_type: test
    path: cli/lib/tests/test_wakeup_scheduler.py
dependencies:
  parent: PLAN-114
  requires:
    - PLAN-114
  blocks: []
related_docs:
  - docs/plans/PLAN-114-session-wakeup-scheduler.md
  - docs/plans/PLAN-099-auto-run-framework.md
  - cli/lib/helix_db.py
  - helix/HELIX_CORE.md
acceptance_criteria:
  - "helix.db に wake_queue テーブルが存在し、priority / fire_at / carry_count を記録できる"
  - "helix schedule wake --priority urgent が 5 分後に ScheduleWakeup を投入する"
  - "helix schedule wake --priority background が 30 分後に ScheduleWakeup を投入する"
  - "helix schedule next が最短 fire_at の event を表示し、重複 ScheduleWakeup 投入を防ぐ"
  - "carry_count > 5 時に priority が urgent へ自動昇格する"
  - "python3 -m py_compile cli/lib/wakeup_scheduler.py PASS"
  - "pytest test_wakeup_scheduler.py (9 case) 全 PASS"
  - "既存 helix doctor pass 数に回帰なし"
---

# PLAN-211: ScheduleWakeup priority queue

## L2 凍結 (ADR snapshot)

PLAN-114 の ScheduleWakeup 実装を queue 管理へ拡張する。
helix.db schema 追加 + Python helper 追加のみで、新 framework 採用ではないため
ADR snapshot 不要。PLAN-099 §ScheduleWakeup 運用ルールとの責務分離は
pmo-sonnet review (Sprint .4) で確認する。

## 背景

PLAN-114 / PLAN-182 で実装した ScheduleWakeup は **単一 timer** として動作する。
複数の carry / 異なる priority の wake-up 要求が競合した場合:

- 新しい ScheduleWakeup 投入が古い timer を上書きする
- urgent (carry > 5) も background (定期 sweep) も同じ間隔で扱われる
- 「次に起きるべき最短 fire_at」を算出する仕組みがない

本 PLAN は wake-up event を helix.db の `wake_queue` テーブルで管理し、
priority に応じた fire_at を計算して **最短 event 1 件のみ** ScheduleWakeup に投入する
queue framework を実装する。

## WebSearch skip 理由 (PLAN-087 ガードレール)

HELIX 内部 helix.db 拡張 + Python helper 追加のみ。外部ライブラリ新規依存なし。

## 設計方針

### wake_queue テーブル設計

カラム: `id` / `event_type` (carry_check|heartbeat|custom) / `priority` (urgent|normal|background) /
`carry_count` / `fire_at` (ISO8601 UTC) / `scheduled_at` / `consumed_at` (NULL=未消費) / `metadata_json`。

`consumed_at IS NULL` の行が未消費イベント。`ix_wake_queue_fire_at` でフィルタ済みインデックス。
同一 event_type で未消費が存在する場合 upsert で fire_at を更新 (重複追加防止)。

### priority 別 fire time matrix

| priority | fire_at (投入から) | 昇格条件 |
|---|---|---|
| urgent | +5 分 | carry_count > 5、または budget 消費率 > 90% |
| normal | +15 分 | carry_count 1〜5 (default) |
| background | +30 分 | carry_count == 0、または定期 heartbeat |

- 昇格は `WakeupScheduler.enqueue()` 呼び出し時に carry_count を見て自動判定
- budget 消費率チェックは PLAN-210 の `BudgetAllocator.check_warn()` に委譲 (利用可能な場合)

### WakeupScheduler クラス (cli/lib/wakeup_scheduler.py)

主要 public メソッド:

- `enqueue(event_type, carry_count=0, priority=None) -> int`: wake_queue に event 追加。priority 未指定時は carry_count から自動判定。同一 event_type 未消費があれば upsert (fire_at 更新)。
- `next_event() -> dict | None`: 最短 fire_at の未消費 event。なければ None。
- `consume(event_id) -> None`: consumed_at をセット。
- `schedule_next_wakeup() -> None`: next_event() を取得し ScheduleWakeup に投入。未消費 0 件なら何もしない。

内部定数: `FIRE_MINUTES = {"urgent": 5, "normal": 15, "background": 30}`、`URGENT_CARRY_THRESHOLD = 5`。
全 timestamp は `datetime.now(timezone.utc)` で統一。

### helix schedule CLI

```
helix schedule wake [--priority urgent|normal|background] [--carry-count N]
helix schedule next                  # 次に fire する event を表示
helix schedule list [--pending]      # 未消費 queue 一覧
helix schedule consume <event_id>    # 手動消費 (テスト・デバッグ用)
```

- `wake` はデフォルト carry_count=0 (background)、`--carry-count` でオーバーライド
- `next` は `schedule_next_wakeup()` を呼び出し、ScheduleWakeup 投入後に event_id を表示
- `list --pending` は未消費 event を fire_at 昇順で表示

### PLAN-099 との責務分離

PLAN-099 の ScheduleWakeup 運用ルールは「harness 追跡外の外部状態 polling 専用」を明記する。
本 PLAN の wake_queue は **helix 内部 carry check / heartbeat** に限定し、
外部 CI / GitHub Actions 監視は PLAN-099 の既存ルールを継続する。

SessionStart hook での `schedule_next_wakeup()` 呼び出しは fail-open で実装する
(hook 失敗で session を block しない)。

## 実装計画

### Sprint .1: schema migration + WakeupScheduler コア (Codex se、size S-M)

`cli/lib/migrations/v38_wake_queue.py` を新規作成 (idempotent)。
`cli/lib/wakeup_scheduler.py` に enqueue / next_event / consume / _resolve_priority /
_fire_at を実装。`python3 -m py_compile` PASS + migration idempotent 確認が完了条件。

### Sprint .2: schedule_next_wakeup + helix schedule CLI (Codex se、size S)

`schedule_next_wakeup()` を実装 (ScheduleWakeup 投入モック付き)。
`cli/helix-schedule` に wake / next / list / consume サブコマンドを追加。
`bash -n cli/helix-schedule` PASS が完了条件。

### Sprint .3: pytest (Codex qa、size S)

`cli/lib/tests/test_wakeup_scheduler.py` で 9 case:
T1: carry=0→background(+30min) / T2: carry=3→normal(+15min) / T3: carry=6→urgent(+5min)
T4: 同一 event_type 重複 upsert で行 1 件 / T5: next_event は fire_at 昇順最小を返す
T6: consume 後に next_event から消える / T7: 未消費 0 件で ScheduleWakeup 呼び出し 0 回
T8: 未消費 1 件で ScheduleWakeup 呼び出し 1 回 / T9: fire_at が動的 (+N 分) で生成される

### Sprint .4: pmo-sonnet review + PLAN-099 docs 整合確認 (PMO、size S)

PLAN-099 §ScheduleWakeup 運用ルールに wake_queue 委譲の注記を追加。
pmo-sonnet で PLAN-099 / PLAN-114 との責務衝突がないことを確認。

## mandatory in sprint

- [ ] `python3 -m py_compile cli/lib/wakeup_scheduler.py` PASS
- [ ] migration idempotent 確認
- [ ] `bash -n cli/helix-schedule` PASS
- [ ] pytest 9 PASS / `helix doctor` pass 数現行以上
- [ ] pmo-sonnet review (Sprint .4)

## DoD

- [ ] `wake_queue` テーブル migration 実装済み
- [ ] `WakeupScheduler` が enqueue / next_event / consume / schedule_next_wakeup を実装している
- [ ] carry_count > 5 で priority が urgent に自動昇格する
- [ ] `helix schedule wake` / `next` / `list` / `consume` が動作する
- [ ] `schedule_next_wakeup()` が未消費 0 件の時に ScheduleWakeup を呼ばない
- [ ] PLAN-099 docs に wake_queue 委譲の注記が追加されている
- [ ] pytest 9 case 全 PASS
- [ ] helix doctor pass 数現行以上

## carry / 学び

- upsert は `INSERT ... ON CONFLICT DO UPDATE` で id を保持 (`INSERT OR REPLACE` は id が変わり外部参照が壊れる)。
- SessionStart hook は fail-open (try/except silent fail)。全 timestamp は `datetime.now(timezone.utc)` で統一。
- ScheduleWakeup 投入コードは PLAN-114 実装を wrap し mock しやすい設計を維持する。

## 関連 reference

- PLAN-114 (parent) / PLAN-099 (ScheduleWakeup 運用ルール)
- PLAN-210 (BudgetAllocator — urgent 昇格の budget check 候補)
- cli/lib/helix_db.py / helix/HELIX_CORE.md §ScheduleWakeup 運用ルール
