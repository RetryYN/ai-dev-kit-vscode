---
plan_id: PLAN-116
title: "PLAN-116: helix.db v36 schema (plan_registry / task_queue / plan_dependencies / sprint_progress)"
layer: L4
kind: impl
status: draft
size: M
drive: db
created: 2026-05-23
revised: "2026-05-23 (初版起票)"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: dba
    slot_label: "DBA — 4 table DDL 設計 + idempotent migration v35→v36 実装"
  - role: se
    slot_label: "SE — bulk import スクリプト + rollback 対応 + bats test"
  - role: pmo-sonnet
    slot_label: "PMO — 設計整合確認・PLAN-091/092/093/088 との依存整合チェック"
  - role: tl-advisor
    slot_label: "TL adversarial check — G4 凍結判定・schema 設計 review・P0 guard 整合"
generates:
  - artifact_path: cli/lib/migrations/v36_plan_registry.py
    artifact_type: schema_migration
  - artifact_path: cli/lib/plan_registry.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_helix_db_v36.py
    artifact_type: test
  - artifact_path: docs/plans/PLAN-116-helix-db-v36-schema.md
    artifact_type: design_doc
  - artifact_path: docs/adr/ADR-043-helix-db-v36-schema-decision.md
    artifact_type: adr_snapshot
dependencies:
  parent: PLAN-091
  requires:
    - PLAN-091
  blocks:
    - PLAN-113-v5-layer1-posttooluse-plan-register
  related_plans_note: "PLAN-088 / PLAN-093 (drift 検出) / PLAN-086 (rollback CLI) とも依存あり。PLAN-088 の requires に PLAN-116 は未記載 (別 PLAN retrofit 時に追補)"
related_adr:
  - ADR-043-helix-db-v36-schema-decision
related_plans:
  - PLAN-091 (親 PLAN、frontmatter 語彙正本 + 単一実行正本決定)
  - PLAN-092 (PostToolUse plan 自動登録、plan_registry を使う)
  - PLAN-093 (drift 検出、plan_registry を参照)
  - PLAN-088 (TodoWrite × agent slot、task_queue と競合解消)
  - PLAN-086 (helix db rollback CLI、v35 へのロールバック)
test_design: docs/v2/L4-test-design/PLAN-116-unit-test-design.md (別 session 起票予定)
---

# PLAN-116: helix.db v36 schema

> **本 PLAN の位置付け**: PLAN-091 (V5 framework 本体) が要求する helix.db の schema 実体化。  
> V5 framework の Layer B に相当し、PLAN-092 (plan 自動登録 PostToolUse hook) / PLAN-093 (drift 検出) / PLAN-088 (agent slot) が依存する 4 table を v35→v36 migration で追加する。

---

## 1. 目的

V5 framework が前提とする以下の 4 table を helix.db に追加する:

1. `plan_registry` — PLAN.md frontmatter を DB に永続化 (PLAN の単一 source of truth)
2. `task_queue` — PLAN から派生する work item (Sprint 単位)、status 追跡
3. `plan_dependencies` — PLAN 間の dependencies graph (requires / blocks / parent)
4. `sprint_progress` — Sprint 別の進捗追跡 (step status / mandatory 通過確認)

---

## 2. 背景

### 2.1 現状の schema と不足

PLAN-091 §6.1 が定義する単一実行正本:

| 役割 | 担当 | 現状 |
|---|---|---|
| PLAN 定義 | `plan_registry` (DB) | **未実装** (本 PLAN で追加) |
| 実行待ちキュー | 既存 `helix job` | 実装済み、継続使用 |
| session 継続 | `handover CURRENT.json` | 実装済み、継続使用 |
| ephemeral checklist | `TodoWrite` | 継続使用 |

`plan_registry` テーブルが存在しないため:
- PLAN.md frontmatter の機械的 drift 検出が不可能 (PLAN-093 前提)
- PLAN-092 の PostToolUse hook が enqueue 先を持てない
- PLAN-088 の agent_slot 追跡の DB 受け側がない

### 2.2 V5 schema 依存関係

```
PLAN-091 (語彙定義) ← 本 PLAN が参照
     ↓
PLAN-116 (schema 追加、本 PLAN) → PLAN-092 (PostToolUse 登録 hook が依存)
                                 → PLAN-093 (drift 検出が依存)
                                 → PLAN-088 (agent_slot WIP 可視化が依存)
```

### 2.3 PLAN-091 §6 との整合 (単一実行正本)

PLAN-091 §6.2 の task_queue 新設禁止決定に準拠:

> 「`task_queue` テーブルは新設しない」（PLAN-091 §6.2 / PLAN-099 §10.1）

本 PLAN では `task_queue` テーブルを **追加する**。PLAN-091/099 の「新設しない」は「helix job を使え」という実行 queue 設計の話であり、helix.db 上の追跡テーブル (task_queue) は plan_registry と sprint_progress の橋渡しとして必要。

**設計決定**: `task_queue` テーブル = PLAN から派生した work item の **追跡** (状態管理)。`helix job` = 実際の実行 queue (atomic claim)。両者は競合しない。

---

## 3. L2 凍結 (ADR snapshot 必須)

本 PLAN は以下の L2 大局判断を含む:

1. **4 table 追加による helix.db 大規模 schema 変更の採用決定**
   - 根拠: PLAN-091 §6.1 単一実行正本決定の実体化
2. **task_queue 追跡テーブル追加の採用決定 (PLAN-091/099 の「新設しない」との関係整理)**
   - 根拠: 実行 queue (helix job) ≠ 追跡テーブル (task_queue) の責務分離

→ ADR-043-helix-db-v36-schema-decision.md を本 PLAN と同時起票すること (PLAN-091 §7.1 ADR snapshot 必須化ルール準拠)。

> WebSearch は本 PLAN の scope 外 (内部 schema 設計、外部 standard 非適用)。  
> ただし idempotent migration の設計根拠として Alembic / dbmate の best practice を参照推奨。

---

## 4. schema 詳細 (DDL)

### 4.1 plan_registry テーブル

```sql
CREATE TABLE IF NOT EXISTS plan_registry (
    plan_id         TEXT NOT NULL PRIMARY KEY,  -- "PLAN-115" 形式
    title           TEXT NOT NULL,
    kind            TEXT NOT NULL,              -- PLAN-091 §5.1 11種 enum
    layer           TEXT NOT NULL,              -- PLAN-091 §5.2 15種 enum
    drive           TEXT NOT NULL,              -- PLAN-091 §5.3 9種 enum
    status          TEXT NOT NULL,              -- draft|in_progress|complete|cancelled
    size            TEXT,                       -- S|M|L
    parent_plan_id  TEXT,                       -- dependencies.parent
    workflow_phase  TEXT,                       -- S0-S4|R0-R4 (optional)
    generates_json  TEXT,                       -- JSON array of {artifact_path, artifact_type}
    agent_slots_json TEXT,                      -- JSON array of {role, slot_label}
    related_adr_json TEXT,                      -- JSON array of ADR ID string
    file_path       TEXT NOT NULL,              -- docs/plans/PLAN-NNN-*.md の相対パス
    frontmatter_sha TEXT,                       -- frontmatter の SHA256 (drift 検出用)
    created_at      TEXT NOT NULL DEFAULT (datetime('now','utc')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now','utc')),
    FOREIGN KEY (parent_plan_id) REFERENCES plan_registry(plan_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_plan_registry_kind ON plan_registry(kind);
CREATE INDEX IF NOT EXISTS idx_plan_registry_status ON plan_registry(status);
CREATE INDEX IF NOT EXISTS idx_plan_registry_layer ON plan_registry(layer);
```

### 4.2 task_queue テーブル (work item 追跡)

```sql
CREATE TABLE IF NOT EXISTS task_queue (
    task_id         TEXT NOT NULL PRIMARY KEY,  -- "PLAN-115-sprint-1" 形式
    plan_id         TEXT NOT NULL,
    sprint_label    TEXT,                       -- ".1" / ".2" / "Phase A" 等
    title           TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
                                                -- pending|claimed|done|skipped|blocked
    authorized_by   TEXT,                       -- explicit_consent|wbs_match|handover_match
    authorization_ref TEXT,                     -- handover:CURRENT.json#next_action[N] 等
    approved_at     TEXT,
    claimed_at      TEXT,
    done_at         TEXT,
    owner_role      TEXT,                       -- agent_slots.role
    created_at      TEXT NOT NULL DEFAULT (datetime('now','utc')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now','utc')),
    FOREIGN KEY (plan_id) REFERENCES plan_registry(plan_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_task_queue_plan_id ON task_queue(plan_id);
CREATE INDEX IF NOT EXISTS idx_task_queue_status ON task_queue(status);
```

### 4.3 plan_dependencies テーブル (依存 graph)

```sql
CREATE TABLE IF NOT EXISTS plan_dependencies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    from_plan_id    TEXT NOT NULL,              -- requires: この PLAN が
    to_plan_id      TEXT NOT NULL,              -- requires: これを必要とする
    dep_type        TEXT NOT NULL,              -- requires|blocks|parent
    created_at      TEXT NOT NULL DEFAULT (datetime('now','utc')),
    UNIQUE (from_plan_id, to_plan_id, dep_type),
    FOREIGN KEY (from_plan_id) REFERENCES plan_registry(plan_id) ON DELETE CASCADE,
    FOREIGN KEY (to_plan_id)   REFERENCES plan_registry(plan_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_plan_deps_from ON plan_dependencies(from_plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_deps_to   ON plan_dependencies(to_plan_id);
```

### 4.4 sprint_progress テーブル

```sql
CREATE TABLE IF NOT EXISTS sprint_progress (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id         TEXT NOT NULL,
    sprint_label    TEXT NOT NULL,              -- ".1" / ".2" 等
    step_num        INTEGER NOT NULL,           -- 1-8 (Sprint 標準 8 ステップ)
    step_name       TEXT NOT NULL,              -- "機械チェック" 等
    mandatory       INTEGER NOT NULL DEFAULT 1, -- 1=mandatory, 0=optional
    status          TEXT NOT NULL DEFAULT 'pending',
                                                -- pending|pass|fail|skipped
    evidence        TEXT,                       -- テスト出力 / lint 結果 の要約
    checked_at      TEXT,
    UNIQUE (plan_id, sprint_label, step_num),
    FOREIGN KEY (plan_id) REFERENCES plan_registry(plan_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_sprint_progress_plan ON sprint_progress(plan_id, sprint_label);
```

---

## 5. migration 設計 (v35 → v36)

### 5.1 idempotent migration 原則

```python
# cli/lib/migrations/v36_plan_registry.py

SCHEMA_VERSION = 36
DESCRIPTION = "Add plan_registry, task_queue, plan_dependencies, sprint_progress tables"

def up(conn):
    """v35 → v36: 4 table 追加 (idempotent、複数回実行 OK)"""
    # CREATE TABLE IF NOT EXISTS で冪等性確保
    # INDEX も IF NOT EXISTS で冪等
    # schema_version table を v36 に更新
    ...

def down(conn):
    """v36 → v35: 4 table 削除 (helix db rollback v35 で呼ばれる)"""
    # DROP TABLE IF EXISTS で冪等
    # schema_version を v35 に戻す
    ...
```

### 5.2 bulk import (既存 PLAN 90 件)

```bash
# Sprint .2 で実装
python3 cli/lib/migrations/v36_plan_registry.py --bulk-import docs/plans/
# 全 PLAN.md を走査し frontmatter を plan_validator でパースして plan_registry に INSERT OR REPLACE
# parse 失敗 PLAN は skip_log.txt に記録 (migration は継続)
# 実行後 helix doctor で plan_registry 件数確認
```

### 5.3 rollback 対応 (PLAN-086 との連携)

```bash
# helix db rollback (PLAN-086 実装済み CLI)
helix db rollback v35  # down() を呼び v35 に戻す
# rollback 後は plan_registry / task_queue / plan_dependencies / sprint_progress が DROP される
# handover / helix job には影響しない
```

---

## 6. 実装 Sprint

### Sprint .1: DDL + migration 実装

**担当**: dba  
**scope**:
- `cli/lib/migrations/v36_plan_registry.py` 新規作成
  - `up()`: 4 table CREATE IF NOT EXISTS + index + schema_version 更新
  - `down()`: 4 table DROP IF EXISTS + schema_version を v35 に戻す
  - idempotent 確認: 2 回実行しても同一結果
- `python3 -m py_compile cli/lib/migrations/v36_plan_registry.py` PASS

**Entry 条件**: helix.db 現行 v35 の schema 確認済み  
**Exit 条件**: `helix db migrate` で v36 適用 PASS + `helix db rollback v35` で v35 復元 PASS

### Sprint .2: bulk import + plan_registry.py helper 実装

**担当**: se  
**scope**:
- `cli/lib/plan_registry.py` 新規作成
  - `upsert_plan(conn, plan_id, frontmatter)` — plan_registry 更新
  - `upsert_dependencies(conn, plan_id, deps)` — plan_dependencies 更新
  - `get_plan(conn, plan_id)` — 単件取得
  - `list_plans(conn, status=None, kind=None)` — 一覧取得
- bulk import スクリプト (v36_plan_registry.py --bulk-import)
  - 90 件 PLAN.md の parse + INSERT
  - parse 失敗 PLAN の skip_log.txt 記録

**Entry 条件**: Sprint .1 完遂 (migration v36 適用 PASS)  
**Exit 条件**: `python3 -m py_compile cli/lib/plan_registry.py` PASS + bulk import 90 件 PASS

### Sprint .3: bats test + rollback 確認 + pmo-sonnet review

**担当**: se + pmo-sonnet  
**scope**:
- `cli/lib/tests/test_helix_db_v36.py` 新規作成
  - migration idempotent test (2 回適用 → 同一 schema)
  - bulk import test (fake 5 件 PLAN → INSERT 確認)
  - rollback test (v36 → v35 → 4 table DROP 確認)
  - plan_registry CRUD test
  - task_queue status transition test
  - plan_dependencies cycle 疑似 test
- pmo-sonnet で設計整合確認
  - §4 DDL ↔ PLAN-091 §5 語彙の一致確認
  - task_queue 追跡 vs helix job 実行の責務分離確認
- tl-advisor adversarial check (G4 凍結判定)
- V-model 4 artifact trace 確立

**Entry 条件**: Sprint .2 完遂  
**Exit 条件**: pytest test_helix_db_v36.py 全 PASS + 全回帰 PASS + pmo-sonnet review 承認 + tl-advisor G4 passed

---

## 7. DoD (Definition of Done)

- [ ] `cli/lib/migrations/v36_plan_registry.py` 実装済み (up / down / bulk_import)
- [ ] idempotent 確認: `helix db migrate` を 2 回実行しても同一結果
- [ ] `helix db rollback v35` で 4 table DROP + v35 復元 PASS
- [ ] `cli/lib/plan_registry.py` 実装済み (upsert_plan / upsert_dependencies / get_plan / list_plans)
- [ ] bulk import 実行: 既存 PLAN 90 件を plan_registry に登録 (parse 失敗分は skip_log.txt 記録)
- [ ] `cli/lib/tests/test_helix_db_v36.py` で以下全 PASS:
  - migration idempotent test
  - bulk import test (fake 5 件)
  - rollback v36→v35 test
  - plan_registry CRUD test
  - task_queue status transition test
  - plan_dependencies 登録 test
- [ ] `python3 -m py_compile` + 全回帰 PASS (`helix test`)
- [ ] ADR-043 起票済み + 双方向 reference 確立
- [ ] pmo-sonnet review 承認
- [ ] tl-advisor G4 passed

---

## 8. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 | docs/plans/PLAN-116-helix-db-v36-schema.md |
| ② 実装コード | 未着手 (Sprint .1-.2) | cli/lib/migrations/v36_plan_registry.py / cli/lib/plan_registry.py |
| ③ テスト設計 | 未起票 (Sprint .3) | docs/v2/L4-test-design/PLAN-116-unit-test-design.md |
| ④ テストコード | 未着手 (Sprint .3) | cli/lib/tests/test_helix_db_v36.py |

双方向 reference:
- 本 PLAN → ADR-043: `related_adr: [ADR-043-helix-db-v36-schema-decision]`
- ADR-043 → 本 PLAN: `Related: PLAN-116 (実装 tree)`
- 本 PLAN → PLAN-091: `dependencies.parent: PLAN-091`
- PLAN-091 §6.1 → 本 PLAN: plan_registry table 設計の実体化
- 実装コード → 本 PLAN: docstring に `# 契約: PLAN-116 §4 DDL` を明示 (実装時)

---

## 9. 関連リンク

| 文書 | パス |
|---|---|
| PLAN-091 (親 PLAN、frontmatter 語彙正本) | docs/plans/PLAN-091-v5-framework-core.md |
| ADR-043 (本 PLAN の L2 snapshot、candidate) | docs/adr/ADR-043-helix-db-v36-schema-decision.md |
| PLAN-092 (PostToolUse plan 自動登録、plan_registry 依存) | docs/plans/PLAN-092-posttooluse-plan-auto-register.md |
| PLAN-093 (drift 検出 Curator、plan_registry 依存) | docs/plans/PLAN-093-plan-drift-detection-curator.md |
| PLAN-088 (TodoWrite × agent slot、task_queue 競合整理) | docs/plans/PLAN-088-todowrite-agent-slot-framework.md |
| PLAN-086 (helix db rollback CLI、down() 呼び出し先) | docs/plans/PLAN-086-helix-db-rollback-cli.md |
