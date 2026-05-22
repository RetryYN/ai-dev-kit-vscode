---
plan_id: PLAN-143
title: "PLAN-143: helix.db v37 schema (event_log + telemetry table)"
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
    slot_label: "DBA — event_log / telemetry DDL 設計 + idempotent migration v36→v37 実装"
  - role: se
    slot_label: "SE — HelixEventLogger / TelemetryWriter helper + CLI 接続 + pytest"
  - role: pmo-sonnet
    slot_label: "PMO — 設計整合確認・PLAN-116/134 との依存整合チェック・helix log report 接続確認"
  - role: tl-advisor
    slot_label: "TL adversarial check — G4 凍結判定・table 設計 review・metric 粒度 P0 guard"
generates:
  - artifact_path: cli/lib/migrations/v37_event_telemetry.py
    artifact_type: schema_migration
  - artifact_path: cli/lib/helix_event_logger.py
    artifact_type: python_module
  - artifact_path: cli/lib/telemetry_writer.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_helix_db_v37.py
    artifact_type: test
  - artifact_path: docs/plans/PLAN-143-helix-db-v37-event-telemetry.md
    artifact_type: design_doc
  - artifact_path: docs/adr/ADR-050-helix-db-v37-event-telemetry-decision.md
    artifact_type: adr_snapshot
dependencies:
  parent: PLAN-116
  requires:
    - PLAN-116
  blocks: []
related_adr:
  - ADR-050-helix-db-v37-event-telemetry-decision (candidate)
related_plans:
  - PLAN-116 (親 PLAN、v36 schema 追加。plan_registry / task_queue が本 PLAN の前提)
  - PLAN-134 (helix metrics CLI。telemetry table を参照する。PLAN-134 は旧 frontmatter のため blocks に含めず related_plans で管理)
  - PLAN-086 (helix db rollback CLI、down() 呼び出し先)
  - PLAN-091 (frontmatter 語彙正本)
test_design: docs/v2/L4-test-design/PLAN-143-unit-test-design.md (別 session 起票予定)
---

# PLAN-143: helix.db v37 schema (event_log + telemetry table)

> **本 PLAN の位置付け**: PLAN-116 (v36 schema) の子 PLAN。  
> v36 で追加した plan_registry / task_queue を前提に、CLI 実行履歴・hook 発火履歴を記録する  
> `event_log` テーブルと、carry / budget / agent slot 利用率を蓄積する `telemetry` テーブルを  
> v36→v37 migration で追加する。

---

## 1. 目的

以下 2 table を helix.db に追加する:

1. `event_log` — CLI コマンド実行・hook 発火・gate 判定の履歴を記録する (可監査性)
2. `telemetry` — carry 消費数 / Opus budget 消費率 / agent slot 利用率 を蓄積する (運用改善)

これにより `helix log report` (既存コマンド) と PLAN-134 (`helix metrics`) が DB ベースの集計を得られる。

---

## 2. 背景

### 2.1 現状の問題

| 観点 | 現状 | 本 PLAN で解決 |
|---|---|---|
| CLI 実行履歴 | `helix log` はファイルログのみ | `event_log` で DB 集計可能に |
| hook 発火記録 | hook 側に個別ログなし | `event_log` で event_type=hook_fired として一元管理 |
| carry 消費 | CURRENT.json の瞬間値のみ | `telemetry` で session 別に蓄積 |
| budget 消費 | `helix budget status` で都度確認 | `telemetry` で時系列推移を追跡 |
| agent slot 利用率 | `helix agent stats` で件数のみ | `telemetry` で利用率 (使用/総枠) を蓄積 |

### 2.2 PLAN-116 との関係

```
PLAN-116 (v36 schema)
  ├── plan_registry     ← PLAN-092 が依存
  ├── task_queue        ← PLAN-088 が依存
  ├── plan_dependencies ← PLAN-093 が依存
  └── sprint_progress   ← Sprint 標準 8 ステップ追跡
           ↓
PLAN-143 (v37 schema、本 PLAN)
  ├── event_log         ← helix log report / PLAN-134 が依存
  └── telemetry         ← PLAN-134 (helix metrics) が依存
```

### 2.3 単一実行正本との整合

PLAN-091 §6.1 の単一実行正本決定に準拠:
- `event_log` = 実行の証跡 (append-only、削除禁止)
- `telemetry` = 集計メトリクス (session 単位で INSERT、重複 upsert 可)

---

## 3. L2 凍結 (ADR snapshot 必須)

本 PLAN は以下の L2 大局判断を含む:

1. **event_log / telemetry を helix.db に統合する採用決定**
   - 根拠: 既存 helix.db に plan_registry 等が集まる v36 に続く自然な拡張。外部 observability ツール不要
2. **event_log を append-only (UPDATE/DELETE 禁止) とする採用決定**
   - 根拠: 可監査性確保。post-mortem で発火順序を再現できることが必要
3. **telemetry の session 単位 upsert とする採用決定**
   - 根拠: 同一 session で複数回 update される指標は最新値で上書き、歴史推移はタイムスタンプで追跡

→ ADR-050-helix-db-v37-event-telemetry-decision.md を本 PLAN と同時起票すること。

> WebSearch は本 PLAN の scope 外 (内部 schema 設計、外部 standard 非適用)。

---

## 4. schema 詳細 (DDL)

### 4.1 event_log テーブル

```sql
CREATE TABLE IF NOT EXISTS event_log (
    event_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp     TEXT NOT NULL DEFAULT (datetime('now','utc')),
    event_type    TEXT NOT NULL,
                  -- cli_command | hook_fired | gate_judged | plan_status_changed
                  -- sprint_step_checked | agent_slot_used | error
    actor         TEXT NOT NULL,
                  -- "cli:<subcommand>" | "hook:<hook_name>" | "pmo-sonnet" | "codex-se" 等
    plan_id       TEXT,                    -- 関連 PLAN ID (任意)
    session_id    TEXT,                    -- Claude Code session_id (任意)
    result        TEXT,                    -- "pass" | "fail" | "blocked" | "skipped" (任意)
    message       TEXT,                    -- 1 行サマリ (任意)
    metadata_json TEXT                     -- JSON blob (追加情報、任意)
    -- append-only: UPDATE / DELETE 禁止
);
CREATE INDEX IF NOT EXISTS idx_event_log_timestamp  ON event_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_event_log_event_type ON event_log(event_type);
CREATE INDEX IF NOT EXISTS idx_event_log_plan_id    ON event_log(plan_id);
CREATE INDEX IF NOT EXISTS idx_event_log_session_id ON event_log(session_id);
```

### 4.2 telemetry テーブル

```sql
CREATE TABLE IF NOT EXISTS telemetry (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name    TEXT NOT NULL,
                   -- "carry_consumed" | "opus_budget_pct" | "agent_slot_utilization"
                   -- "session_duration_sec" | "sprint_mandatory_pass_rate"
    value          REAL NOT NULL,
    session_id     TEXT NOT NULL,
    timestamp      TEXT NOT NULL DEFAULT (datetime('now','utc')),
    dimensions_json TEXT,                  -- JSON blob {"phase": "L4", "role": "se"} 等
    UNIQUE (metric_name, session_id, timestamp)
                   -- 同一 session × 同一 timestamp の重複防止
);
CREATE INDEX IF NOT EXISTS idx_telemetry_metric_name ON telemetry(metric_name);
CREATE INDEX IF NOT EXISTS idx_telemetry_session_id  ON telemetry(session_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp   ON telemetry(timestamp);
```

---

## 5. migration 設計 (v36 → v37)

### 5.1 idempotent migration 原則

```python
# cli/lib/migrations/v37_event_telemetry.py

SCHEMA_VERSION = 37
DESCRIPTION = "Add event_log and telemetry tables"

def up(conn):
    """v36 → v37: 2 table 追加 (idempotent、複数回実行 OK)"""
    # CREATE TABLE IF NOT EXISTS で冪等性確保
    # INDEX も IF NOT EXISTS で冪等
    # schema_version table を v37 に更新

def down(conn):
    """v37 → v36: 2 table 削除 (helix db rollback v36 で呼ばれる)"""
    # DROP TABLE IF EXISTS で冪等
    # schema_version を v36 に戻す
```

### 5.2 rollback 対応

```bash
# PLAN-086 実装済み CLI を使用
helix db rollback v36   # down() を呼び v36 に戻す
# rollback 後は event_log / telemetry が DROP される
# plan_registry / task_queue 等 v36 tables は無影響
```

---

## 6. helper module 設計

### 6.1 HelixEventLogger (cli/lib/helix_event_logger.py)

```python
class HelixEventLogger:
    """event_log への append-only 書き込みを担当する helper"""

    def log(
        self,
        event_type: str,
        actor: str,
        plan_id: str | None = None,
        session_id: str | None = None,
        result: str | None = None,
        message: str | None = None,
        metadata: dict | None = None,
    ) -> int:
        """event_log に 1 件 INSERT し、event_id を返す"""
        ...

    def query(
        self,
        event_type: str | None = None,
        plan_id: str | None = None,
        since: str | None = None,   # ISO datetime 文字列
        limit: int = 100,
    ) -> list[dict]:
        """event_log を条件検索して dict list を返す"""
        ...
```

### 6.2 TelemetryWriter (cli/lib/telemetry_writer.py)

```python
class TelemetryWriter:
    """telemetry テーブルへの upsert を担当する helper"""

    def record(
        self,
        metric_name: str,
        value: float,
        session_id: str,
        dimensions: dict | None = None,
    ) -> None:
        """telemetry に INSERT OR REPLACE し、最新値を保持する"""
        ...

    def aggregate(
        self,
        metric_name: str,
        agg: str = "avg",           # "avg" | "sum" | "max" | "min" | "last"
        since: str | None = None,
    ) -> float | None:
        """時系列集計値を返す。PLAN-134 helix metrics が呼ぶ"""
        ...
```

---

## 7. `helix log report` / `helix metrics` との接続

```
helix log report
  → event_log WHERE event_type=gate_judged / hook_fired で最近 N 件を表示

helix metrics (PLAN-134 実装)
  → telemetry.aggregate("carry_consumed") で carry 推移
  → telemetry.aggregate("opus_budget_pct") で budget 推移
  → telemetry.aggregate("agent_slot_utilization") で slot 利用率
```

接続は PLAN-134 の Sprint .2 で実装する (本 PLAN は table 追加と helper module のみ担当)。

---

## 8. 実装 Sprint

### Sprint .1: DDL + migration 実装

**担当**: dba  
**scope**:
- `cli/lib/migrations/v37_event_telemetry.py` 新規作成
  - `up()`: event_log / telemetry CREATE IF NOT EXISTS + index + schema_version v37 更新
  - `down()`: 2 table DROP IF EXISTS + schema_version v36 に戻す
  - idempotent 確認: 2 回実行しても同一結果
- `python3 -m py_compile cli/lib/migrations/v37_event_telemetry.py` PASS

**Entry 条件**: helix.db v36 schema 適用済み (PLAN-116 Sprint .1 完遂)  
**Exit 条件**: `helix db migrate` で v37 適用 PASS + `helix db rollback v36` で v36 復元 PASS

### Sprint .2: helper module 実装

**担当**: se  
**scope**:
- `cli/lib/helix_event_logger.py` 新規作成 (HelixEventLogger: log / query)
- `cli/lib/telemetry_writer.py` 新規作成 (TelemetryWriter: record / aggregate)
- 既存 `helix log report` コマンドの event_log 参照への接続準備 (stub)
- `python3 -m py_compile` PASS (両ファイル)

**Entry 条件**: Sprint .1 完遂 (migration v37 適用 PASS)  
**Exit 条件**: py_compile PASS + 手動 smoke (log 1 件 INSERT → query で取得確認)

### Sprint .3: pytest + pmo-sonnet review

**担当**: se + pmo-sonnet  
**scope**:
- `cli/lib/tests/test_helix_db_v37.py` 新規作成
  - migration idempotent test (2 回適用 → 同一 schema)
  - rollback test (v37 → v36 → 2 table DROP 確認)
  - event_log CRUD test (append / query / 重複 actor test)
  - telemetry upsert + aggregate test (avg / last)
  - UNIQUE 制約テスト (同一 session × 同一 timestamp の重複)
- pmo-sonnet 設計整合確認
  - §4 DDL ↔ helper interface の一致確認
  - event_log append-only 制約の実装確認
- tl-advisor adversarial check (G4 凍結判定)
- V-model 4 artifact trace 確立

**Entry 条件**: Sprint .2 完遂  
**Exit 条件**: pytest test_helix_db_v37.py 全 PASS + 全回帰 PASS + pmo-sonnet review 承認 + tl-advisor G4 passed

---

## 9. DoD (Definition of Done)

- [ ] `cli/lib/migrations/v37_event_telemetry.py` 実装済み (up / down)
- [ ] idempotent 確認: `helix db migrate` を 2 回実行しても同一結果
- [ ] `helix db rollback v36` で 2 table DROP + v36 復元 PASS
- [ ] `cli/lib/helix_event_logger.py` 実装済み (log / query)
- [ ] `cli/lib/telemetry_writer.py` 実装済み (record / aggregate)
- [ ] `cli/lib/tests/test_helix_db_v37.py` で以下全 PASS:
  - migration idempotent test
  - rollback v37→v36 test
  - event_log append / query test
  - telemetry upsert + aggregate (avg / last) test
  - UNIQUE 制約 test
- [ ] `python3 -m py_compile` + 全回帰 PASS (`helix test`)
- [ ] ADR-050 起票済み + 双方向 reference 確立
- [ ] pmo-sonnet review 承認
- [ ] tl-advisor G4 passed

---

## 10. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 | docs/plans/PLAN-143-helix-db-v37-event-telemetry.md |
| ② 実装コード | 未着手 (Sprint .1-.2) | cli/lib/migrations/v37_event_telemetry.py / cli/lib/helix_event_logger.py / cli/lib/telemetry_writer.py |
| ③ テスト設計 | 未起票 (Sprint .3) | docs/v2/L4-test-design/PLAN-143-unit-test-design.md |
| ④ テストコード | 未着手 (Sprint .3) | cli/lib/tests/test_helix_db_v37.py |

双方向 reference:
- 本 PLAN → ADR-050: `related_adr: [ADR-050-helix-db-v37-event-telemetry-decision]`
- ADR-050 → 本 PLAN: `Related: PLAN-143 (実装 tree)`
- 本 PLAN → PLAN-116: `dependencies.parent: PLAN-116`
- PLAN-116 §1 → 本 PLAN: v37 拡張 (event_log / telemetry) は後続 PLAN に委譲
- 実装コード → 本 PLAN: docstring に `# 契約: PLAN-143 §4 DDL` を明示 (実装時)

---

## 11. 関連リンク

| 文書 | パス |
|---|---|
| PLAN-116 (親 PLAN、v36 schema) | docs/plans/PLAN-116-helix-db-v36-schema.md |
| ADR-050 (本 PLAN の L2 snapshot、candidate) | docs/adr/ADR-050-helix-db-v37-event-telemetry-decision.md |
| PLAN-134 (helix metrics CLI、telemetry 依存) | docs/plans/PLAN-134-helix-metrics-cli.md |
| PLAN-086 (helix db rollback CLI) | docs/plans/PLAN-086-helix-db-rollback-cli.md |
| PLAN-091 (frontmatter 語彙正本) | docs/plans/PLAN-091-v5-framework-core.md |
