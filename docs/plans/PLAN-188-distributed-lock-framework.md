---
plan_id: PLAN-188
title: "HELIX runtime distributed lock (multi-session 衝突防止)"
kind: impl
layer: L4
drive: be
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
size: M
created: "2026-05-23"
owner: PM
phases: L3, L4
gates: G3, G4
agent_slots:
  - role: se
    slot_label: "SE — cli/lib/distributed_lock.py 新規 + granularity 3 種 (DB/file/logical) 実装"
  - role: pmo-sonnet
    slot_label: "PMO — 既存 helix.db lock / handover write 競合の既存 PLAN drift チェック"
  - role: tl-advisor
    slot_label: "TL adversarial check — flock vs SQLite WAL の設計選択・デッドロックリスクレビュー"
  - role: qa
    slot_label: "QA — 並行アクセス fixture テスト (同 session 多重 OK / 異 session block / timeout 解放)"
generates:
  - artifact_path: docs/plans/PLAN-188-distributed-lock-framework.md
    artifact_type: design_doc
  - artifact_path: cli/lib/distributed_lock.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_distributed_lock.py
    artifact_type: test
dependencies:
  parent: null
  requires:
    - PLAN-088
    - PLAN-129
  blocks: []
related_plans:
  - PLAN-088 (TodoWrite × agent slot framework — agent_slots テーブルと handover の正本)
  - PLAN-129 (pmo-sonnet stuck 検出 + auto-recovery — stuck slot release と lock 解放の協調)
  - PLAN-092 (helix.db schema + PostToolUse 自動登録 — DB 書き込み競合の発生源)
---

# PLAN-188: HELIX runtime distributed lock framework

## L2 凍結 (ADR snapshot)

本 PLAN は **multi-session 競合防止のための distributed lock 新設** という新規大局判断を含む。

設計選択 (TL adversarial check で確定):
- **採用**: POSIX `flock` + Python `fcntl.flock` (依存ゼロ、Linux/macOS 共通)
- **採用**: SQLite WAL mode + `busy_timeout=3000ms` を helix.db に適用
- **不採用**: Redis / etcd 系 (外部依存、HELIX self-contained 原則に違反)

根拠:
- 8 並列上限 (CLAUDE.md) の並列操作で helix.db / handover / agent_slots が競合するリスクがある
- session_id 別 namespace により同一 session の再帰 lock は許可 (deadlock 回避)
- WebSearch 3 query 実施: fcntl.flock POSIX 標準確認 / SQLite WAL BEGIN IMMEDIATE / reentrant lock file パターン

## 背景

HELIX は 8 並列まで同時セッション (Opus / Codex / pmo-sonnet) を許容する。複数セッションが
同一 runtime state に同時アクセスする競合シナリオが構造的に存在する。

問題:
1. **helix.db 並行 write**: PostToolUse hook (PLAN-092) が並発すると `SQLITE_BUSY` で silent fail
2. **handover CURRENT.json 競合**: read-modify-write 中に他セッションが read すると古い状態を取得
3. **agent_slots 多重更新**: PLAN-129 auto-recovery と手動 release が同一 slot_id を同時 UPDATE

## 設計方針

### lock granularity 3 種

| granularity | 対象 | lock 方式 | 競合時アクション |
|---|---|---|---|
| **db** | helix.db write | SQLite `BEGIN IMMEDIATE` + busy_timeout 3000ms | 自動 retry (3s 上限) |
| **file** | handover/CURRENT.json | POSIX `flock(LOCK_EX)` | タイムアウト付き待機 (10s) |
| **logical** | agent_slots.slot_id | lock file `/tmp/helix-slot-{slot_id}.lock` | 競合時 skip + WARN log |

### distributed_lock.py API

```python
from cli.lib.distributed_lock import HelixLock, LockGranularity

with HelixLock(granularity=LockGranularity.FILE,
               resource_id="handover/CURRENT.json",
               session_id=SESSION_ID,
               timeout_sec=10) as lock:
    update_handover(...)
# lock 競合時は HelixLockTimeout を raise
```

- **同 session_id** の再帰 lock: reentrant で通過 (deadlock 回避)
- **異 session_id**: 既存 lock 解放まで待機、timeout で `HelixLockTimeout`
- session_id 取得: `os.environ.get("CLAUDE_SESSION_ID", "unknown")`

### helix.db WAL 設定 (helix_db.py 追加)

```python
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA busy_timeout=3000")
```

## 実装計画

### Sprint .1: distributed_lock.py 実装 (Codex se 委譲)

Entry 条件: PLAN-088 + PLAN-129 Sprint .1 (migration v36) 完了

1. `cli/lib/distributed_lock.py` 新規 (`LockGranularity` enum + `HelixLock` context manager)
2. `HelixLockTimeout` exception + `is_locked()` helper
3. `python3 -m py_compile cli/lib/distributed_lock.py` PASS (mandatory in sprint)

受入条件: lock/unlock 正常 / 異 session_id 競合で HelixLockTimeout / 同 session_id 再帰 OK

### Sprint .2: helix.db WAL 統合 (Codex se 委譲)

Entry 条件: Sprint .1 PASS

1. `cli/lib/helix_db.py` 接続初期化に WAL + busy_timeout 追加
2. 既存テスト `test_helix_db*.py` 全 PASS 確認 (mandatory in sprint)

### Sprint .3: handover file lock 統合 (Codex se 委譲)

Entry 条件: Sprint .2 PASS

1. handover read-modify-write パスに `HelixLock(FILE, "handover/CURRENT.json")` 適用
2. lock timeout 時は fail-open (WARN log のみ)

### Sprint .4: fixture テスト (Codex qa 委譲)

Entry 条件: Sprint .1〜.3 PASS

`cli/lib/tests/test_distributed_lock.py` に 6 シナリオ:

| T ID | シナリオ | 期待結果 |
|---|---|---|
| T188-001 | 通常 lock/unlock | lock file 生成 → 削除 |
| T188-002 | 同 session_id 再帰 | deadlock なし、両方通過 |
| T188-003 | 異 session_id 競合 | HelixLockTimeout raise |
| T188-004 | timeout 後の自動解放 | 解放後に次 session が lock 取得 |
| T188-005 | helix.db WAL 並行 INSERT | SQLITE_BUSY なし、両方成功 |
| T188-006 | logical lock slot 競合 | 先着 1 件のみ release、後続 WARN |

全 PASS 必須。`datetime.now(timezone.utc)` ベースで動的 timestamp 生成 (固定値 flake 防止)。

## DoD

- [ ] `python3 -m py_compile cli/lib/distributed_lock.py` PASS
- [ ] granularity 3 種 (db / file / logical) が動作する
- [ ] session_id 別 reentrant lock で deadlock しない
- [ ] helix.db に WAL + busy_timeout=3000 が適用済み
- [ ] T188-001〜T188-006 全 PASS
- [ ] 既存 test_helix_db*.py 全 PASS (regression なし)
- [ ] `helix doctor` warn 増加なし

## risks

| リスク | 影響 | 緩和策 |
|---|---|---|
| `flock` が NFS / WSL で非動作 | file lock 機能しない | `HelixLockUnavailable` で catch し fail-open |
| deadlock (A→B / B→A 相互待機) | CLI フリーズ | 全 HelixLock に timeout_sec 必須化 (上限 60s) |
| lock file 残留 (プロセス crash) | 永久待機 | `flock` は fd close 時に OS が自動回収 |
| helix.db WAL ファイル増大 | git 汚染 | .gitignore に `*.db-wal` / `*.db-shm` 追加 (P1) |
