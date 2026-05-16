---
doc_id: D-DB-EXTENDED-draft-v0.1
plan_id: PLAN-070
sprint: SprintF / .6
status: draft
created: 2026-05-16
primary_drive: be
extends: D-DB-draft-v0.1
---

# PLAN-070 SprintF: L3 D-DB 拡張 draft v0.1

## §1 目的とスコープ

V-model 強化の運用系データを SQLite schema として追加する SprintF の D-DB draft である。  
`automation_runs` / `audit_log` / `session_telemetry` を v25/v26/v27 として追加し、Sprint B §2.0 (`docs/v2/L3-detailed-design/D-DB/D-DB-draft.md` §2.0.1 MigrationStep / §2.0.2 ColumnSpec) を再利用して additive / idempotent / non-destructive に固定する。本 draft では shape を再定義しない。  
push/pr/hook の実行種別を `run_kind` 列で分類し、1 テーブル `automation_runs` に統合することで FK 解決コストを削減する。3 テーブル分散より管理性が高く、statistical query / 横断レポートで利点がある。  
v24 (design_sprint_drive_decisions、Sprint B §5) は **未実装** であり、本 draft の v25 migration は v24 実装完了後に着手する。

### 1.1 対象

- v25: `automation_runs`
- v26: `audit_log`
- v27: `session_telemetry`
- 共通 primitive 再利用
- append-only trigger / index / view

### 1.2 Non-goals

- `cli/lib/helix_db.py` の内部実装詳細
- 既存 schema の rename / drop
- hook 実装ロジック本体
- API endpoint 実装本体
- JSON schema の正式凍結

### 1.3 参照正本

- `docs/plans/PLAN-070-l3-schema-and-contract-design.md` §3.F / §4.7
- `docs/v2/L3-detailed-design/D-DB/D-DB-draft.md` §2.0 / §5
- `cli/lib/helix_db.py` の `CURRENT_SCHEMA_VERSION=23`
- `docs/v2/B-design/vmodel-semantics-spine.yaml`
- `docs/v2/L1-REQUIREMENTS.md` AC-17, FR-VS01-06.4, FR-GR04, CON-06

## §2 migration matrix 拡張

Sprint B の v21-v24 草案に対して、SprintF は v25-v27 を追加する。  
各 step は additive で、既存行を破壊しない。SQLite 互換のため `ALTER TABLE ADD COLUMN` は使わず、new table + backfill を基本にする。

### 2.1 共通 primitive

```yaml
MigrationStep:
  type: object
  required: [step, version, kind, idempotent, rollback_path]
  additionalProperties: false
  properties:
    step: {type: integer}
    version:
      type: string
      pattern: '^v(\\d+)$'
    kind:
      type: string
      enum: [add_column, add_table, add_index, add_constraint, alter_check, backfill, add_trigger, add_view]
    idempotent: {type: boolean}
    rollback_path:
      oneOf: [{type: string}, {type: 'null'}]

ColumnSpec:
  type: object
  required: [name, type, null, default, check, fk, immutable]
  additionalProperties: false
  properties:
    name: {type: string}
    type: {type: string}
    null: {type: boolean}
    default:
      oneOf: [{type: string}, {type: integer}, {type: number}, {type: boolean}, {type: 'null'}]
    check:
      oneOf: [{type: string}, {type: 'null'}]
    fk:
      oneOf:
        - {type: 'null'}
        - type: object
          required: [table, column]
          properties:
            table: {type: string}
            column: {type: string}
    immutable: {type: boolean}
    unique: {type: boolean}

BaselinePolicyFamily:
  $ref: docs/v2/B-design/vmodel-semantics-spine.yaml#/baseline_policy_family
ScoreFormula:
  $ref: docs/v2/B-design/vmodel-semantics-spine.yaml#/score/formula
PromotionLinkRef:
  description: SprintC で正式化済みの参照型を流用
  type: object
  required: [promotion_kind, phase]
```

### 2.2 migration matrix

| version | kind | target | rollback |
|---|---|---|---|
| v25 | add_table | automation_runs | rollback_v25_to_v24.sql |
| v25 | add_index | automation_runs | rollback_v25_indexes.sql |
| v25 | add_trigger | automation_runs | rollback_v25_triggers.sql |
| v26 | add_table | audit_log | rollback_v26_to_v25.sql |
| v26 | add_index | audit_log | rollback_v26_indexes.sql |
| v26 | add_trigger | audit_log | rollback_v26_triggers.sql |
| v27 | add_table | session_telemetry | rollback_v27_to_v26.sql |
| v27 | add_index | session_telemetry | rollback_v27_indexes.sql |
| v27 (続き) | add_view | v_automation_recent_runs, v_audit_summary_by_plan, v_session_cost_summary | rollback_v27_views.sql |
| v27 | add_trigger | session_telemetry | rollback_v27_triggers.sql |

### 2.3 整合ルール

- enum と CHECK は YAML / SQL で同値
- nullable 列は既存レコードを壊さない
- trigger は `BEFORE UPDATE` / `BEFORE DELETE`
- immutable 比較は `IS NOT` を使う
- 既存 PK / FK の再作成は禁止

## §3 automation_runs テーブル定義（v25）

`automation_runs` は push/pr/pretool/posttool/stop/session_start の実行単位を 1 行で保持する。`precommit` は廃止し、`pretool` に統合する。  
このテーブルは **完全 append-only**（DELETE 禁止）かつ **terminal status lifecycle** を持つ。`status` は `running` から `passed/failed/blocked/cancelled` のいずれかへ 1 回だけ更新でき、それ以外の更新は不可とする。更新可能列の境界は `started_at` / `run_kind` / `plan_id` / `trigger_actor` が完全 immutable、`ended_at` / `status` / `exit_code` / `summary` が terminal 遷移時の 1 回のみ更新可、その後 immutable とする。

### 3.1 ColumnSpec

```yaml
automation_runs_columns:
  - {name: id, type: INTEGER, null: false, default: null, check: null, fk: null, immutable: true}
  - {name: run_kind, type: TEXT, null: false, default: null, check: "run_kind IN ('push','pr','pretool','posttool','stop','session_start')", fk: null, immutable: true}
  - {name: plan_id, type: TEXT, null: true, default: null, check: null, fk: null, immutable: true}
  - {name: trigger_actor, type: TEXT, null: false, default: null, check: "trigger_actor IN ('tl','se','pg','fe','qa','pm','system')", fk: null, immutable: true}
  - {name: started_at, type: TEXT, null: false, default: "datetime('now')", check: null, fk: null, immutable: true}
  - {name: ended_at, type: TEXT, null: true, default: null, check: null, fk: null, immutable: false}
  - {name: status, type: TEXT, null: false, default: 'running', check: "status IN ('running','passed','failed','blocked','cancelled')", fk: null, immutable: false}
  - {name: exit_code, type: INTEGER, null: true, default: null, check: null, fk: null, immutable: false}
  - {name: summary, type: TEXT, null: true, default: null, check: null, fk: null, immutable: false}
```

### 3.2 DDL

```sql
CREATE TABLE IF NOT EXISTS automation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_kind TEXT NOT NULL CHECK (run_kind IN ('push','pr','pretool','posttool','stop','session_start')),
    plan_id TEXT,
    trigger_actor TEXT NOT NULL CHECK (trigger_actor IN ('tl','se','pg','fe','qa','pm','system')),
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at TEXT,
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running','passed','failed','blocked','cancelled')),
    exit_code INTEGER,
    summary TEXT
);
```

### 3.3 Trigger

```sql
CREATE TRIGGER IF NOT EXISTS trg_automation_runs_no_delete
BEFORE DELETE ON automation_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'append-only: cannot delete from automation_runs');
END;

CREATE TRIGGER IF NOT EXISTS trg_automation_runs_no_mutate
BEFORE UPDATE ON automation_runs
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN OLD.id IS NOT NEW.id THEN RAISE(ABORT, 'id is immutable')
        WHEN OLD.run_kind IS NOT NEW.run_kind THEN RAISE(ABORT, 'run_kind is immutable')
        WHEN OLD.plan_id IS NOT NEW.plan_id THEN RAISE(ABORT, 'plan_id is immutable')
        WHEN OLD.trigger_actor IS NOT NEW.trigger_actor THEN RAISE(ABORT, 'trigger_actor is immutable')
        WHEN OLD.started_at IS NOT NEW.started_at THEN RAISE(ABORT, 'started_at is immutable')
        ELSE NULL
    END;
END;

CREATE TRIGGER IF NOT EXISTS trg_automation_runs_terminal_final
BEFORE UPDATE ON automation_runs
FOR EACH ROW
WHEN OLD.status IN ('passed', 'failed', 'blocked', 'cancelled')
     AND (
         NEW.status IS NOT OLD.status
         OR NEW.exit_code IS NOT OLD.exit_code
         OR NEW.summary IS NOT OLD.summary
         OR NEW.ended_at IS NOT OLD.ended_at
     )
BEGIN
    SELECT RAISE(ABORT, 'terminal status is final');
END;
```

<!-- P0-03 hybrid 判定確定 (Codex tl-advisor 2026-05-16):
     trigger 方式採用。`_transition_lifecycle_status` helper は app-layer check で
     terminal guard を実施し、trigger の一時 disable は使わない。
     正規遷移: pending → running → completed/failed/cancelled -->

<!-- _transition_lifecycle_status app-layer 要件:
     if OLD.status NOT IN ('completed','failed','cancelled') then UPDATE else RAISE
     trigger は lifecycle 遷移中も有効。helper が遷移 guard を持つ前提で trigger と二重防御を構成する -->

### 3.4 Index

```sql
CREATE INDEX IF NOT EXISTS idx_automation_runs_plan_id ON automation_runs(plan_id);
CREATE INDEX IF NOT EXISTS idx_automation_runs_kind_started_at ON automation_runs(run_kind, started_at);
CREATE INDEX IF NOT EXISTS idx_automation_runs_status ON automation_runs(status);
```

## §4 audit_log テーブル定義（v26）

`audit_log` は `automation_runs` に紐づく完全 append-only の監査記録である。

### 4.1 ColumnSpec

```yaml
audit_log_columns:
  - {name: id, type: INTEGER, null: false, default: null, check: null, fk: null, immutable: true}
  - {name: run_id, type: INTEGER, null: false, default: null, check: "run_id > 0", fk: {table: automation_runs, column: id}, immutable: true}
  - {name: audit_kind, type: TEXT, null: false, default: null, check: "audit_kind IN ('footer','summary','diff_lines','security_scan','qa_check')", fk: null, immutable: true}
  - {name: payload, type: TEXT, null: false, default: null, check: null, fk: null, immutable: true}
  - {name: created_at, type: TEXT, null: false, default: "datetime('now')", check: null, fk: null, immutable: true}
```

### 4.2 DDL

```sql
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES automation_runs(id),
    audit_kind TEXT NOT NULL CHECK (audit_kind IN ('footer','summary','diff_lines','security_scan','qa_check')),
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### 4.3 Trigger

```sql
CREATE TRIGGER IF NOT EXISTS trg_audit_log_no_delete
BEFORE DELETE ON audit_log
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'append-only: cannot delete from audit_log');
END;

CREATE TRIGGER IF NOT EXISTS trg_audit_log_no_mutate
BEFORE UPDATE ON audit_log
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN OLD.id IS NOT NEW.id THEN RAISE(ABORT, 'id is immutable')
        WHEN OLD.run_id IS NOT NEW.run_id THEN RAISE(ABORT, 'run_id is immutable')
        WHEN OLD.audit_kind IS NOT NEW.audit_kind THEN RAISE(ABORT, 'audit_kind is immutable')
        WHEN OLD.payload IS NOT NEW.payload THEN RAISE(ABORT, 'payload is immutable')
        WHEN OLD.created_at IS NOT NEW.created_at THEN RAISE(ABORT, 'created_at is immutable')
        ELSE NULL
    END;
END;
```

<!-- P0-03 hybrid 判定確定 (Codex tl-advisor 2026-05-16): trigger 方式採用。
     rollback SQL:
       DROP TRIGGER IF EXISTS trg_audit_log_no_mutate;
       DROP TRIGGER IF EXISTS trg_audit_log_no_delete; -->

### 4.4 Index

```sql
CREATE INDEX IF NOT EXISTS idx_audit_log_run_id ON audit_log(run_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_kind_created_at ON audit_log(audit_kind, created_at);
```

## §5 session_telemetry テーブル定義（v27）

`session_telemetry` は Stop hook 由来の終了情報を格納する。

### 5.1 ColumnSpec

```yaml
session_telemetry_columns:
  - {name: id, type: INTEGER, null: false, default: null, check: null, fk: null, immutable: true}
  - {name: session_id, type: TEXT, null: false, default: null, check: null, fk: null, immutable: true, unique: true}
  - {name: started_at, type: TEXT, null: false, default: "datetime('now')", check: null, fk: null, immutable: true}
  - {name: ended_at, type: TEXT, null: true, default: null, check: null, fk: null, immutable: false}
  - {name: tokens_used, type: INTEGER, null: true, default: null, check: "tokens_used IS NULL OR tokens_used >= 0", fk: null, immutable: false}
  - {name: cost_usd, type: REAL, null: true, default: null, check: "cost_usd IS NULL OR cost_usd >= 0", fk: null, immutable: false}
  - {name: model, type: TEXT, null: true, default: null, check: "model IN ('claude-opus-4-7','claude-sonnet-4-6','claude-haiku-4-5-20251001','gpt-5.5','gpt-5.4','gpt-5.4-mini','gpt-5.3-codex','gpt-5.3-codex-spark','gpt-5.2-codex') OR model IS NULL", fk: null, immutable: true}
  - {name: role, type: TEXT, null: true, default: null, check: "role IN ('pm','tl','se','pe','pmo','recommender','classifier','qa','docs','dba','devops','security') OR role IS NULL", fk: null, immutable: true}
  - {name: related_plan_id, type: TEXT, null: true, default: null, check: null, fk: null, immutable: false}
```

### 5.2 DDL

```sql
CREATE TABLE IF NOT EXISTS session_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at TEXT,
    tokens_used INTEGER,
    cost_usd REAL,
    model TEXT CHECK (model IN ('claude-opus-4-7','claude-sonnet-4-6','claude-haiku-4-5-20251001','gpt-5.5','gpt-5.4','gpt-5.4-mini','gpt-5.3-codex','gpt-5.3-codex-spark','gpt-5.2-codex') OR model IS NULL),
    role TEXT CHECK (role IN ('pm','tl','se','pe','pmo','recommender','classifier','qa','docs','dba','devops','security') OR role IS NULL),
    related_plan_id TEXT
);
```

### 5.3 Trigger

```sql
CREATE TRIGGER IF NOT EXISTS trg_session_telemetry_no_delete
BEFORE DELETE ON session_telemetry
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'append-only: cannot delete from session_telemetry');
END;

CREATE TRIGGER IF NOT EXISTS trg_session_telemetry_no_mutate
BEFORE UPDATE ON session_telemetry
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN OLD.id IS NOT NEW.id THEN RAISE(ABORT, 'id is immutable')
        WHEN OLD.session_id IS NOT NEW.session_id THEN RAISE(ABORT, 'session_id is immutable')
        WHEN OLD.started_at IS NOT NEW.started_at THEN RAISE(ABORT, 'started_at is immutable')
        WHEN OLD.model IS NOT NEW.model THEN RAISE(ABORT, 'model is immutable')
        WHEN OLD.role IS NOT NEW.role THEN RAISE(ABORT, 'role is immutable')
        ELSE NULL
    END;
END;
```

### 5.4 Index

```sql
CREATE INDEX IF NOT EXISTS idx_session_telemetry_session_id ON session_telemetry(session_id);
CREATE INDEX IF NOT EXISTS idx_session_telemetry_related_plan_id ON session_telemetry(related_plan_id);
CREATE INDEX IF NOT EXISTS idx_session_telemetry_started_at ON session_telemetry(started_at);
```

## §6 migration 実行戦略

### 6.1 原則

- additive / idempotent / non-destructive
- 既存 `helix.db` v23 までの完了 DB に追加入力可能
- `ALTER TABLE` は追加方向のみ
- 失敗時は 1 版ずつ戻せる rollback path を確保

### 6.2 実行順

1. v25: `automation_runs` 作成
2. v25: index / trigger 作成
3. v26: `audit_log` 作成
4. v26: index / trigger 作成
5. v27: `session_telemetry` 作成
6. v27: index / trigger 作成
7. v27: view 追加
8. `PRAGMA foreign_key_check`

### 6.3 rollback path

- v25 失敗: `automation_runs` / index / trigger を除去して v24 へ
- v26 失敗: `audit_log` / index / trigger を除去して v25 へ
- v27 失敗: `session_telemetry` / index / trigger / view を除去して v26 へ

### 6.4 検証 SQL

```sql
PRAGMA table_info(automation_runs);
PRAGMA table_info(audit_log);
PRAGMA table_info(session_telemetry);
PRAGMA foreign_key_check;
SELECT name, type
FROM sqlite_master
WHERE type IN ('table','view','trigger')
  AND name IN ('automation_runs','audit_log','session_telemetry');
```

## §7 集計 view 提案

### 7.1 v_automation_recent_runs

```sql
CREATE VIEW IF NOT EXISTS v_automation_recent_runs AS
SELECT id, run_kind, plan_id, trigger_actor, started_at, ended_at, status, exit_code, summary
FROM automation_runs
ORDER BY started_at DESC, id DESC;
```

### 7.2 v_audit_summary_by_plan

```sql
CREATE VIEW IF NOT EXISTS v_audit_summary_by_plan AS
SELECT ar.plan_id, al.audit_kind, COUNT(*) AS audit_count, MIN(al.created_at) AS first_seen_at, MAX(al.created_at) AS last_seen_at
FROM audit_log al
JOIN automation_runs ar ON ar.id = al.run_id
GROUP BY ar.plan_id, al.audit_kind;
```

### 7.3 v_session_cost_summary

```sql
CREATE VIEW IF NOT EXISTS v_session_cost_summary AS
SELECT session_id, related_plan_id, model, role, started_at, ended_at, tokens_used, cost_usd
FROM session_telemetry
ORDER BY started_at DESC, session_id;
```

## §8 既存実装との整合

`cli/lib/helix_db.py` の `CURRENT_SCHEMA_VERSION=23` は維持される。  
SprintF は新しい v25/v26/v27 を別系統で積み増すだけで、v23 freeze を崩さない。

### 8.1 整合ポイント

- v23 までの schema 互換を保持
- `PRAGMA table_info` で列存在を確認可能
- append-only は trigger で担保
- nullable 列の整合性は CHECK で担保

### 8.2 実装非依存メモ

- `summary` は JSON 文字列または自由テキストを許容
- `payload` は JSON を想定するが、厳密 schema は SprintC / 後続で正式化
- `session_telemetry` の `model` / `role` は現時点 model 9 値・role 12 値で CHECK 閉包、新 model/role 追加時は `ALTER TABLE CHECK` が必要になるため carry とする
- `ColumnSpec` の `unique` フィールドは Sprint B 原型に未定義のため、SprintD で Sprint B primitive 拡張を carry する
- `plans` テーブルの正本定義は現時点で未定義であり、確定後に FK 追加を検討する
- `automation_runs.summary` の formal schema は SprintC で確定する
- `audit_log.payload` の formal schema は SprintC で確定する

## §8.3 Phase 5 helper 仕様 (新規実装対象)

P0-03 trigger 方式確定に伴い、Phase 5 (L4) で新規実装する helper のシグネチャを以下に定義する。

```python
def _create_append_only_trigger(
    conn: sqlite3.Connection,
    table_name: str,
    immutable_columns: list[str] | None = None,
    terminal_status_column: str | None = None,
    terminal_values: list[str] | None = None,
) -> None:
    """
    table_name に対し append-only 強制 trigger を生成する。

    - immutable_columns: 指定した列の UPDATE を BEFORE UPDATE で拒否
    - terminal_status_column + terminal_values: terminal status の行への UPDATE 全般を拒否
    - 常に BEFORE DELETE を生成し、DELETE 拒否
    - すべて CREATE TRIGGER IF NOT EXISTS で idempotent 化
    """
```

- trigger 一時 disable (`PRAGMA`) は使わない。migration sandboxing 違反かつ HELIX append-only 不変条件に反する
- `_transition_lifecycle_status` 内で app-layer check (terminal guard) を持ち、trigger と二重防御を構成する

## §9 carry / open questions

- `session_telemetry` に `cost_currency` を追加するかは別途検討
- `cli/lib/helix_db.py` への migration 実装は L4 実装で扱う
- `v_automation_recent_runs` の LIMIT 付き派生 view は実装時に調整する
- 統合判断 ADR 起票は SprintD で確定する

### 9.1 受入チェック

- §1 で目的と scope が明示されている
- §2 migration matrix に v25 / v26 / v27 が揃っている
- §3-§5 で 3 テーブル DDL / trigger / index が揃っている
- §6 で additive / idempotent / rollback-safe が明記されている
- §7 で 3 つの集計 view が提案されている
- §8 で `CURRENT_SCHEMA_VERSION=23` の freeze 前提が記載されている

### 9.2 完了条件

- ファイルは新規作成済み
- 3 テーブル DDL が本文に含まれる
- append-only trigger が本文に含まれる
- `MigrationStep` と `ColumnSpec` が参照再利用されている
- 外部参照リンクのパスが整合している

## §10 agent_slots テーブル定義（v28）

### 10.1 概要

`agent_slots` は agent invocation 単位の slot 管理を行う追加 table である。  
目的は helix.db における並列実行の可視化であり、Codex / subagent / 将来の agent tool 実行を 1 行 1 invocation で記録する。  
PLAN-078 が schema 起源、PLAN-075 が V-model 4 artifact 原則、PLAN-074 が実装境界を提供する。  
migration ID は v27 → v28 であり、既存の automation_runs と session_telemetry を補完する。

#### 10.1.1 関連 table

- `automation_runs`: HTTP push / pr / hook 経由起動の run 単位
- `session_telemetry`: session 単位の累積 telemetry
- `agent_slots`: invocation 単位の slot 管理
- `audit_log`: fire / release イベントの監査補助に利用可能だが、本 §10 では必須化しない

### 10.2 schema (DDL)

```sql
CREATE TABLE IF NOT EXISTS agent_slots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_key        TEXT NOT NULL,           -- 'codex:{role}' or 'subagent:{subagent_type}'
    agent_kind      TEXT NOT NULL            -- 'codex' | 'claude_subagent'
                    CHECK(agent_kind IN ('codex', 'claude_subagent')),
    role            TEXT,                    -- helix-codex --role 値 (codex の場合)
    subagent_type   TEXT,                    -- Agent tool の subagent_type (subagent の場合)
    plan_id         TEXT,                    -- --plan-id 値 (任意)
    task_id         TEXT,                    -- --task-id 値 (任意)
    sprint          TEXT,                    -- --l4-sprint 値 (任意)
    session_id      TEXT,                    -- HELIX_SESSION_ID (任意、FK なし)
    automation_run_id INTEGER,               -- automation_runs.id FK (任意)
    fired_at        TEXT NOT NULL DEFAULT (datetime('now')),
    released_at     TEXT,                    -- NULL = 実行中
    status          TEXT NOT NULL DEFAULT 'running'
                    CHECK(status IN ('running', 'completed', 'failed', 'cancelled')),
    exit_code       INTEGER,                 -- codex exit code (任意)
    slot_source     TEXT NOT NULL DEFAULT 'helix_codex'
                    CHECK(slot_source IN ('helix_codex', 'pretooluse_hook')),
    FOREIGN KEY (automation_run_id) REFERENCES automation_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_agent_slots_status    ON agent_slots(status);
CREATE INDEX IF NOT EXISTS idx_agent_slots_plan      ON agent_slots(plan_id);
CREATE INDEX IF NOT EXISTS idx_agent_slots_fired_at  ON agent_slots(fired_at);
CREATE INDEX IF NOT EXISTS idx_agent_slots_kind      ON agent_slots(agent_kind);
```

### 10.3 列詳細仕様

| 列名 | 型 | NULL 許可 | default | CHECK 制約 | 用途 | 関連 helper 関数 |
|---|---|---|---|---|---|---|
| id | INTEGER | いいえ | なし | なし | slot の主キー | `fire_slot()` |
| slot_key | TEXT | いいえ | なし | なし | agent 種別と role/type の検索キー | `fire_slot()` |
| agent_kind | TEXT | いいえ | なし | `codex` / `claude_subagent` | invocation の分類 | `fire_slot()` |
| role | TEXT | はい | なし | なし | `helix-codex --role` 値 | `fire_slot()` |
| subagent_type | TEXT | はい | なし | なし | Agent tool の subagent_type | `fire_slot()` |
| plan_id | TEXT | はい | なし | なし | PLAN trace | `fire_slot()` / `get_stats()` |
| task_id | TEXT | はい | なし | なし | task trace | `fire_slot()` / `get_stats()` |
| sprint | TEXT | はい | なし | なし | L4 sprint trace | `fire_slot()` / `get_stats()` |
| session_id | TEXT | はい | なし | なし | HELIX session trace | `fire_slot()` / `get_stats()` |
| automation_run_id | INTEGER | はい | なし | FK `automation_runs(id)` | HTTP 起動との連携 | `fire_slot()` |
| fired_at | TEXT | いいえ | `datetime('now')` | なし | 起動時刻 | `fire_slot()` |
| released_at | TEXT | はい | なし | なし | 終了時刻 | `release_slot()` |
| status | TEXT | いいえ | `running` | `running` / `completed` / `failed` / `cancelled` | slot 状態 | `release_slot()` |
| exit_code | INTEGER | はい | なし | なし | Codex exit code | `release_slot()` |
| slot_source | TEXT | いいえ | `helix_codex` | `helix_codex` / `pretooluse_hook` | 記録起点 | `fire_slot()` |

### 10.4 trigger 設計

```sql
-- Phase 1 (本 §10 scope): no_delete trigger のみ
CREATE TRIGGER IF NOT EXISTS agent_slots_no_delete
BEFORE DELETE ON agent_slots
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'agent_slots is append-only (no delete allowed)');
END;
```

Phase 2 では `released_at` / `status` 遷移の append-only enforcement を追加する余地があるが、本 §10 では scope 外とする。

### 10.5 helper 関数

`cli/lib/agent_slots.py` で実装する helper は次の通りである。

- `fire_slot(agent_kind, role=None, subagent_type=None, plan_id=None, task_id=None, sprint=None, session_id=None, automation_run_id=None) -> int`
- `release_slot(slot_id, status='completed', exit_code=None)`
- `list_active_slots() -> list[dict]`
- `list_stale_slots(threshold_minutes=5) -> list[dict]`
- `get_stats(days=7, by='hour') -> dict`

### 10.6 状態遷移

```text
running ──┬─→ completed (正常終了、exit_code=0)
          ├─→ failed (exit_code != 0)
          ├─→ cancelled (trap SIGINT/SIGTERM)
          └─→ (Phase 2 で timed_out 自動遷移、本 §10 scope 外)
```

### 10.7 関連 table との連携

- **automation_runs**: HTTP push / pr / hook 経由起動の場合のみ FK 設定
- **audit_log**: fire / release イベントを監査記録へ複写可能だが、本 §10 では必須化しない
- **session_telemetry**: 粒度別軸として独立し、`session_id` 任意列で紐付け可能

### 10.8 V-model 4 artifact 双方向 trace

| Artifact | 担当層 | 想定パス |
|---|---|---|
| ① 設計 | L3 詳細設計 | `docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md` §10 agent_slots |
| ② 実装コード | L4 実装 | `cli/lib/agent_slots.py` + `cli/helix-agent` + `cli/helix-codex` 統合 |
| ③ テスト設計 | L4 設計 | `docs/v2/L4-test-design/PLAN-078-unit-test-design.md` / `docs/v2/L4-test-design/PLAN-078-integration-test-design.md` |
| ④ テストコード | L4 実装 | `cli/lib/tests/test_agent_slots*.py` |

### 10.9 migration 手順

```python
# CURRENT_SCHEMA_VERSION = 27 -> 28 に変更する。

AGENT_SLOTS_SCHEMA_V28 = """
CREATE TABLE IF NOT EXISTS agent_slots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_key        TEXT NOT NULL,
    agent_kind      TEXT NOT NULL CHECK(agent_kind IN ('codex', 'claude_subagent')),
    role            TEXT,
    subagent_type   TEXT,
    plan_id         TEXT,
    task_id         TEXT,
    sprint          TEXT,
    session_id      TEXT,
    automation_run_id INTEGER,
    fired_at        TEXT NOT NULL DEFAULT (datetime('now')),
    released_at     TEXT,
    status          TEXT NOT NULL DEFAULT 'running' CHECK(status IN ('running', 'completed', 'failed', 'cancelled')),
    exit_code       INTEGER,
    slot_source     TEXT NOT NULL DEFAULT 'helix_codex' CHECK(slot_source IN ('helix_codex', 'pretooluse_hook')),
    FOREIGN KEY (automation_run_id) REFERENCES automation_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_agent_slots_status   ON agent_slots(status);
CREATE INDEX IF NOT EXISTS idx_agent_slots_plan     ON agent_slots(plan_id);
CREATE INDEX IF NOT EXISTS idx_agent_slots_fired_at ON agent_slots(fired_at);
CREATE INDEX IF NOT EXISTS idx_agent_slots_kind     ON agent_slots(agent_kind);
"""

# @helix:index id=helix_db._migrate_v27_to_v28 domain=cli/lib summary=v28 で agent_slots table を追加 (PLAN-078)
def _migrate_v27_to_v28(conn: sqlite3.Connection) -> None:
    if not _has_table(conn, "agent_slots"):
        conn.executescript(AGENT_SLOTS_SCHEMA_V28)
    _create_append_only_trigger(conn, "agent_slots", immutable_columns=["id", "fired_at", "slot_key"])

# migrate() 内 if current < 28 ブロックとして追加する。
if current < 28:
    _migrate_v27_to_v28(conn)
    conn.execute("INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (28, datetime('now'))")
```

### 10.10 carry note

- Phase 2 で `released_at` / `status` 遷移の append-only enforcement を追加する余地がある
- `audit_log` への fire / release 自動記録は PLAN-078 では強制しない
- `session_telemetry` は session 単位の独立 table として維持する
- `automation_runs` との連携は HTTP 経路のみ FK を使う
