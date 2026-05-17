---
doc_id: D-DB-SEP-draft-v0.1
plan_id: PLAN-084
sprint: Phase 3 / L3 詳細設計
status: draft
created: 2026-05-17
primary_drive: be
extends: D-DB-EXTENDED-draft-v0.1
related_adrs:
  - ADR-018-db-separation-and-event-sourcing
  - ADR-019-double-helix-naming-principle
related_plans:
  - PLAN-070 (D-DB-EXTENDED v25-v27 既存基盤)
  - PLAN-084 (本 PLAN、L2 ADR + L1 要件)
sibling_docs:
  - D-API-SEP-draft-v0.1 (Phase 3.2 起票、adapter API 正本、本 doc schema を adapter 経由で routing)
  - D-CONTRACT-EVENT-draft-v0.1 (Phase 3.3 起票、event class 正本、本 doc §3 event_envelope schema を Python class 化)
related_test_designs:
  - PLAN-084-unit-test-design.md §2 (Phase 3.4 起票、U-ADAPTER-* / U-EVT-* で本 doc の table CRUD をカバー)
  - PLAN-084-integration-test-design.md §2-§4 (Phase 3.4 起票、I-MIGRATION-* / I-DUALWRITE-* / I-REPLAY-* で本 doc §6 migration step をカバー)
---

# PLAN-084 Phase 3: L3 D-DB 6 分離詳細設計 v0.1

## §1 目的とスコープ

### 1.1 本文書の位置づけ

本文書は ADR-018 §Decision.1/2/3/5 を schema レベルに展開し、Phase 4.A/4.B/4.C 実装の正本契約とする L3 詳細設計書である。

ADR-018 で凍結された 5 事項のうち、以下を本文書でスキーマ定義まで落とし込む:

- Decision §1: 6 db 物理分離 + entity ownership + cross-db 規約
- Decision §2: Event Sourcing ハイブリッド採用 (plan.db hybrid の具体 schema)
- Decision §3: projector 境界 (projection_state table)
- Decision §5: migration gate 6 段階 (v30 → v31 の SQL step)

Decision §4 (frontend/backend state-store 再判定条件) は schema の変更を伴わないため本文書では参照に留める。

### 1.2 スコープ

**In-scope**:

- 6 db (orchestration / vmodel / scrum / plan / backend / frontend) の table 定義 (shape 確定)
- event_envelope table (event-sourced 3 db 共通)
- projection_state table (projector read model)
- plan_change_log table (plan.db hybrid の change log 側)
- migration script v30 → v31 の SQL step 順序
- cross-db 規約 + ATTACH allowlist の design contract
- carry 項目の Phase 4 割当

**Non-goals**:

- compatibility_adapter.py の Python 実装詳細 (D-API-SEP-draft で扱う)
- event envelope の Python class 設計 (D-CONTRACT-EVENT-draft で扱う、本 doc は schema のみ)
- 完全な CREATE TABLE SQL (table shape を確定、完全 SQL は Phase 4.A 実装で確定)
- HTTP endpoint 実装 (本 PLAN scope 外。`cli/lib/http_api/routes/*.py` 既存実装は D-API-SEP-draft compatibility adapter 経由で 6 db へ routing される、新規 HTTP endpoint は本 PLAN では扱わない)
- projector の Python 実装詳細 (Phase 4.B)

### 1.3 前段文書との接続

| 前段文書 | 接続箇所 |
|---|---|
| ADR-018 §Decision.1-5 | 本文書全体の根拠。decision → schema の展開 |
| L1-REQUIREMENTS.md §3.9 FR-DB-SEP-01〜09 | 受入条件の原点。各 §2.X で対応 FR を明示 |
| PLAN-084 §2.2-2.6 | matrix の正本 (entity ownership / 6 軸判定 / projector 境界 / migration gate / adapter file) |
| D-DB-EXTENDED-draft.md (PLAN-070) | 前段 v25-v27 schema (automation_runs / audit_log / session_telemetry)。本 doc の §2.5 backend.db はこれを参照 |
| D-DB-MIGRATION.md | HELIX 既存 migration 戦略 v1-v4。本 doc の §6 migration step pattern の参考 |

### 1.4 migration 起点

本文書が扱う migration 番号の起点は **v30** (CURRENT_SCHEMA_VERSION = 30 想定、Phase 4.A 着手時に実環境確認必須)。v31 が dual-write start gate (gate 1) の通過条件となる。

---

## §2 6 db 物理分離 schema (ADR-018 §Decision.1 / FR-DB-SEP-01)

### 設計原則

全 6 db は以下の共通原則を持つ:

- 独立した SQLite file として存在 (`.helix/<db_name>.db`)
- cross-db FK 禁止 (SQLite ATTACH 下でも foreign key 制約は db 内に閉じる)
- ATTACH 許可: migration script (`cli/lib/migrations/*.py`) + projector 内部 (`cli/lib/projectors/*.py`) のみ
- アプリ層 (`cli/helix-*` / `cli/lib/http_api/*`) からの ATTACH 禁止
- 各 db 単独での schema migration 可能 (db 間の migration 依存を持たない、NFR-43)

### §2.1 orchestration.db (event-sourced)

canonical entity: phase / gate / agent_slot / harness_event / harness_check_event

6 軸判定: audit ◎ / temporal ◎ / event ordering ◎ → **event-sourced**

```sql
-- phase 遷移の最新状態 (snapshot)
CREATE TABLE IF NOT EXISTS phases (
    phase_id   TEXT PRIMARY KEY,
    phase_name TEXT NOT NULL,
    status     TEXT NOT NULL CHECK(status IN ('pending','active','passed','failed','skipped')),
    plan_id    TEXT,
    entered_at TEXT NOT NULL,
    exited_at  TEXT,
    metadata   JSON
);

-- gate 通過状況の最新状態 (snapshot)
CREATE TABLE IF NOT EXISTS gates (
    gate_id    TEXT PRIMARY KEY,
    gate_name  TEXT NOT NULL CHECK(gate_name IN ('G1','G1.5','G1R','G2','G3','G4','G5','G6','G7','G8','G9','G10','G11')),
    status     TEXT NOT NULL CHECK(status IN ('open','passed','failed','blocked')),
    plan_id    TEXT,
    evaluated_at TEXT NOT NULL,
    metadata   JSON
);

-- agent_slot の最新状態 (snapshot)
CREATE TABLE IF NOT EXISTS agent_slots (
    slot_id    TEXT PRIMARY KEY,
    role       TEXT NOT NULL,
    status     TEXT NOT NULL CHECK(status IN ('idle','active','error')),
    session_id TEXT,
    fired_at   TEXT,
    released_at TEXT,
    metadata   JSON
);

-- harness monitor events
CREATE TABLE IF NOT EXISTS harness_monitor_events (
    event_id   TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    slot_id    TEXT,
    payload    JSON NOT NULL,
    occurred_at TEXT NOT NULL
);
```

主要 index:
- `phases`: (plan_id, status), (entered_at)
- `gates`: (plan_id, gate_name), (evaluated_at)
- `agent_slots`: (status, role), (session_id)

### §2.2 vmodel.db (event-sourced)

canonical entity: artifact / artifact_link / cross_drive_integrity / drive_decision

6 軸判定: audit ◎ / temporal ◎ / event ordering ◎ → **event-sourced**

```sql
-- V-model 4 artifact の snapshot
CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id   TEXT PRIMARY KEY,
    artifact_type TEXT NOT NULL CHECK(artifact_type IN ('design','impl','test_design','test_impl')),
    plan_id       TEXT NOT NULL,
    layer         TEXT NOT NULL CHECK(layer IN ('L1','L2','L3','L4')),
    file_path     TEXT NOT NULL,
    status        TEXT NOT NULL CHECK(status IN ('draft','frozen','deprecated')),
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    metadata      JSON
);

-- artifact 間の双方向 trace link
CREATE TABLE IF NOT EXISTS artifact_links (
    link_id      TEXT PRIMARY KEY,
    src_artifact TEXT NOT NULL REFERENCES artifacts(artifact_id),
    dst_artifact TEXT NOT NULL REFERENCES artifacts(artifact_id),
    link_type    TEXT NOT NULL CHECK(link_type IN ('design_to_impl','design_to_test_design','test_design_to_test_impl')),
    created_at   TEXT NOT NULL
);

-- cross-drive integrity check 結果
CREATE TABLE IF NOT EXISTS cross_drive_integrity (
    check_id     TEXT PRIMARY KEY,
    plan_id      TEXT NOT NULL,
    drive        TEXT NOT NULL,
    check_type   TEXT NOT NULL,
    status       TEXT NOT NULL CHECK(status IN ('ok','warning','fail')),
    detail       JSON,
    checked_at   TEXT NOT NULL
);
```

主要 index:
- `artifacts`: (plan_id, artifact_type), (layer, status), (file_path)
- `artifact_links`: (src_artifact), (dst_artifact), (link_type)

### §2.3 scrum.db (event-sourced)

canonical entity: hypothesis / scrum_loop / srf_chain / scrum_local_loop / reverse_local_loop

6 軸判定: audit ◎ / temporal ◎ / event ordering ◎ → **event-sourced**

```sql
-- Scrum 仮説 (S0 backlog エントリ)
CREATE TABLE IF NOT EXISTS hypotheses (
    hypothesis_id TEXT PRIMARY KEY,
    plan_id       TEXT NOT NULL,
    title         TEXT NOT NULL,
    status        TEXT NOT NULL CHECK(status IN ('pending','confirmed','rejected','pivot')),
    created_at    TEXT NOT NULL,
    decided_at    TEXT,
    metadata      JSON
);

-- Scrum ループ (S1-S4 の 1 周)
CREATE TABLE IF NOT EXISTS scrum_loops (
    loop_id       TEXT PRIMARY KEY,
    hypothesis_id TEXT NOT NULL REFERENCES hypotheses(hypothesis_id),
    sprint_goal   TEXT NOT NULL,
    status        TEXT NOT NULL CHECK(status IN ('planning','poc','verify','deciding','done')),
    started_at    TEXT NOT NULL,
    completed_at  TEXT,
    metadata      JSON
);

-- scrum_local / reverse_local ループ (UPS/SRF)
CREATE TABLE IF NOT EXISTS scrum_local_loops (
    local_loop_id TEXT PRIMARY KEY,
    parent_loop_id TEXT,
    loop_type     TEXT NOT NULL CHECK(loop_type IN ('scrum_local','reverse_local','srf_chain')),
    status        TEXT NOT NULL,
    started_at    TEXT NOT NULL,
    completed_at  TEXT,
    metadata      JSON
);
```

主要 index:
- `hypotheses`: (plan_id, status), (decided_at)
- `scrum_loops`: (hypothesis_id, status)

### §2.4 plan.db (hybrid: state snapshot + change log)

canonical entity: plan / sprint / task / wbs / design_sprint_drive_decision

6 軸判定: audit ◎ / temporal △ / event ordering ○ → **hybrid**

projector 不要: plan.db 内で state と change log が両方持つため外部 projector 不要。

```sql
-- plan 最新状態 (state 部分)
CREATE TABLE IF NOT EXISTS plans (
    plan_id     TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    status      TEXT NOT NULL CHECK(status IN ('draft','active','completed','abandoned')),
    size        TEXT CHECK(size IN ('S','M','L')),
    drive       TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    metadata    JSON
);

-- sprint 最新状態 (state 部分)
CREATE TABLE IF NOT EXISTS sprints (
    sprint_id   TEXT PRIMARY KEY,
    plan_id     TEXT NOT NULL REFERENCES plans(plan_id),
    sprint_name TEXT NOT NULL,
    status      TEXT NOT NULL CHECK(status IN ('pending','active','completed','blocked')),
    started_at  TEXT,
    completed_at TEXT,
    metadata    JSON
);

-- task 最新状態 (state 部分)
CREATE TABLE IF NOT EXISTS tasks (
    task_id     TEXT PRIMARY KEY,
    sprint_id   TEXT NOT NULL REFERENCES sprints(sprint_id),
    plan_id     TEXT NOT NULL,
    title       TEXT NOT NULL,
    status      TEXT NOT NULL CHECK(status IN ('pending','active','completed','blocked','skipped')),
    owner       TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    metadata    JSON
);

-- plan change log (change log 部分、append-only)
-- state update と同一 transaction で append (tl-advisor Round 2 助言反映)
CREATE TABLE IF NOT EXISTS plan_change_log (
    change_id   TEXT PRIMARY KEY,
    plan_id     TEXT NOT NULL,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('plan','sprint','task','wbs')),
    entity_id   TEXT NOT NULL,
    change_type TEXT NOT NULL CHECK(change_type IN ('status_transition','create','complete','block','skip','wbs_add','wbs_remove')),
    old_value   JSON,
    new_value   JSON NOT NULL,
    occurred_at TEXT NOT NULL
);
```

主要 index:
- `plans`: (status), (drive)
- `sprints`: (plan_id, status)
- `tasks`: (sprint_id, status), (plan_id, status)
- `plan_change_log`: (plan_id, occurred_at), (entity_type, entity_id)

### §2.5 backend.db (state-store)

canonical entity: api_endpoint / contract / impl_module / automation_run / audit_log / session_telemetry

6 軸判定: audit △ / temporal × / event ordering × → **state-store**

前段 schema: PLAN-070 D-DB-EXTENDED-draft.md v25-v27 (automation_runs / audit_log / session_telemetry) が既存。v30 時点でこれらが backend.db に移動される前提。

```sql
-- automation_runs (PLAN-070 v25 由来、backend.db に物理移動)
-- 既存 shape 維持、6 db 分離後の所属確定のみ
CREATE TABLE IF NOT EXISTS automation_runs (
    run_id       TEXT PRIMARY KEY,
    run_kind     TEXT NOT NULL CHECK(run_kind IN ('push','pr','hook')),
    plan_id      TEXT,
    status       TEXT NOT NULL CHECK(status IN ('pending','running','passed','failed')),
    started_at   TEXT NOT NULL,
    completed_at TEXT,
    metadata     JSON
);

-- audit_log (PLAN-070 v26 由来、append-only trigger 付き)
CREATE TABLE IF NOT EXISTS audit_log (
    log_id      TEXT PRIMARY KEY,
    event_type  TEXT NOT NULL,
    actor       TEXT,
    target_id   TEXT,
    detail      JSON NOT NULL,
    occurred_at TEXT NOT NULL
);

-- session_telemetry (PLAN-070 v27 由来)
CREATE TABLE IF NOT EXISTS session_telemetry (
    session_id  TEXT PRIMARY KEY,
    model       TEXT,
    role        TEXT,
    started_at  TEXT NOT NULL,
    ended_at    TEXT,
    token_input  INTEGER DEFAULT 0,
    token_output INTEGER DEFAULT 0,
    metadata    JSON
);
```

主要 index:
- `automation_runs`: (run_kind, status), (plan_id)
- `audit_log`: (event_type, occurred_at), (target_id)
- `session_telemetry`: (model, role), (started_at)

### §2.6 frontend.db (state-store)

canonical entity: ui_component / mock / design_token / mock_promotion

6 軸判定: audit △ / temporal × / event ordering × → **state-store**

Phase 4.A 時点では空 schema (table なし) として初期化のみ。PLAN-085 等で table 詳細を起票する。

```sql
-- (空 schema、ファイル存在のみ確保)
-- 将来の ui_component / mock / design_token / mock_promotion は
-- PLAN-085 以降で table 定義を追加する
```

---

## §3 event envelope schema (ADR-018 §Decision.1 / FR-DB-SEP-01)

### §3.1 event_envelope table 定義

event-sourced 3 db (orchestration / vmodel / scrum) 共通の event envelope。各 db に物理的に存在する。

```sql
CREATE TABLE IF NOT EXISTS event_envelope (
    event_id        TEXT NOT NULL UNIQUE,           -- UUID v7 (global unique)
    aggregate_id    TEXT NOT NULL CHECK(length(aggregate_id) > 0),
    aggregate_type  TEXT NOT NULL CHECK(length(aggregate_type) > 0),
    db_name         TEXT NOT NULL CHECK (db_name IN ('orchestration','vmodel','scrum')),
    event_type      TEXT NOT NULL CHECK(length(event_type) > 0),
    payload         JSON NOT NULL,                  -- application-specific (event_type 別の JSON schema は Phase 4.B で確定)
    correlation_id  TEXT NOT NULL CHECK(length(correlation_id) > 0),  -- cross-db trace、空文字拒否 (tl-advisor L3 review P2 #6 反映)
    occurred_at     TEXT NOT NULL CHECK(length(occurred_at) > 0),    -- ISO8601 (UTC)
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,      -- SQLite INSERT 時刻 (occurred_at と別物、D-CONTRACT-EVENT §6.3 と整合、tl-advisor L3 review P2 #5 反映)
    PRIMARY KEY (db_name, event_id)
);
```

制約:
- `event_id` は global unique を保証 (UUID v7 推奨)
- `(db_name, event_id)` composite PRIMARY KEY で identity 保証
- `payload` は event_type 別の JSON schema で管理 (carry: Phase 4.B で JSON schema 確定)

### §3.2 aggregate key composite

aggregate の identity は `{db_name, aggregate_type, aggregate_id}` の composite key で保証する。

- `aggregate_id` 単体での global uniqueness は要求しない (db 内 uniqueness のみ)
- cross-db での aggregate 参照は `correlation_id` で行う
- tl-advisor Round 2 important #3 反映: L3 契約で composite key を確定

### §3.3 UUID v7 generator 責務 (carry → Phase 4.A)

UUID v7 の生成方式は Phase 4.A 実装時に確定する。選択肢:

1. `uuid7-py` package (`pip install uuid7`)
2. 自前実装 (Python `time.time_ns()` + random bits で UUID v7 フォーマット生成)

選定基準: package 管理コスト vs 依存追加のトレードオフ。Phase 4.A の Codex se が判断・実装する。

### §3.4 correlation_id 規約

- orchestration.db で新規 correlation_id を発行 (UUID v4 または UUID v7)
- 他 db (vmodel / scrum) の event は orchestration の correlation_id を継承
- cross-db trace の必須フィールド: correlation_id が空の event は event-sourced 3 db で拒否される (CHECK constraint)
- 同一ビジネスフロー内で発生する全 event は同一 correlation_id を持つ

### §3.5 index 必須

event_envelope に対して以下の index を各 db に作成する:

```sql
CREATE INDEX IF NOT EXISTS idx_event_envelope_occurred
    ON event_envelope (db_name, occurred_at);

CREATE INDEX IF NOT EXISTS idx_event_envelope_correlation
    ON event_envelope (correlation_id);

CREATE INDEX IF NOT EXISTS idx_event_envelope_aggregate
    ON event_envelope (aggregate_type, aggregate_id);
```

---

## §4 projection_state table (ADR-018 §Decision.3 / FR-DB-SEP-03)

### §4.1 projection_state table 定義

projector が event log から構築した read model のスナップショットを保持する。

```sql
CREATE TABLE IF NOT EXISTS projection_state (
    projector_id          TEXT NOT NULL,             -- 'phase_projector' / 'gate_projector' / 'agent_slot_projector'
    db_name               TEXT NOT NULL,             -- 配置先 db ('orchestration' / 'vmodel' / 'scrum')
    last_processed_event_id TEXT NOT NULL,           -- 最後に処理した event_id
    snapshot              JSON,                      -- read model の最新状態
    updated_at            TEXT NOT NULL,             -- 最終更新時刻 (ISO8601)
    PRIMARY KEY (projector_id, db_name)
);
```

### §4.2 同期許可 projector 3 件の projection_state 配置

ADR-018 §Decision.3 で確定した同期許可リスト 3 件はすべて orchestration.db に配置する:

| projector_id | db_name | 同期理由 | timeout |
|---|---|---|---|
| `phase_projector` | orchestration | phase.yaml 更新は全体の同期ポイント | 200ms |
| `gate_projector` | orchestration | gate 通過判定は次 phase 遷移の前提 | 200ms |
| `agent_slot_projector` | orchestration | fire/release は real-time harness 監視に必要 | 200ms |

上記 3 件以外は async enqueue とし、projection_state 更新は非同期で行う。caller は 200 OK + `X-Projector-Warning: fallback-to-async` header を受け取った後に自身の処理を継続する。

### §4.3 lag 監視設計

projector lag の算定式:

```
lag = count(*) FROM event_envelope
      WHERE db_name = <対象 db>
        AND event_id > <last_processed_event_id>
```

lag 境界:

| lag event 数 | 挙動 |
|---|---|
| < 100 | 正常 (平常稼働定義、NFR-17) |
| 100 〜 999 | WARN log + harness_monitor_events に record |
| 1000 以上 | **Phase 4.B 以降**: G2/G3/G4 gate 通過判定 block (fail-close) |

Phase 4.A 完成までは fail-close 不適用 (projector 未稼働のため)。Phase 4.B で harness_monitor 統合と同時実装する (carry: §7 carry 項目 #6)。

### §4.4 cross-db 参照規則

- 他 db からの projection_state 参照: read のみ許可 (FK 禁止)
- ATTACH 経由での projection_state read: projector 内部のみ許可
- アプリ層からの projection_state 直接 read: **禁止** (Python helper `read_cross_db_projection(projector_id, db_name)` 経由を必須とする)
- `read_cross_db_projection` の定義は D-API-SEP-draft で確定 (carry)

---

## §5 cross-db 規約 + ATTACH allowlist (ADR-018 §Decision.1 / FR-DB-SEP-01)

### §5.1 cross-db FK 禁止

SQLite ATTACH 下でも foreign key 制約は db 内に閉じる。cross-db FK は全面禁止。

違反例 (してはいけない):
```sql
-- NG: orchestration.db の phases を参照する FK を vmodel.db に書く
CREATE TABLE artifacts (
    ...
    phase_id TEXT REFERENCES phases(phase_id)  -- phases は orchestration.db に存在 → 禁止
);
```

正しい参照:
```sql
-- OK: correlation_id 経由で cross-db trace (FK なし)
-- OK: projection_state を read して orchestration の状態を参照
```

### §5.2 ATTACH allowlist

ATTACH DATABASE の使用が許可されるコンテキスト:

| 許可コンテキスト | ファイルパス | 用途 |
|---|---|---|
| migration script | `cli/lib/migrations/*.py` | v30 → v31 の schema 変更・初期化 |
| projector 内部 | `cli/lib/projectors/*.py` | cross-db projection_state の read |

**禁止コンテキスト**:

| 禁止コンテキスト | ファイルパス |
|---|---|
| アプリ層 CLI | `cli/helix-*` |
| HTTP API routes | `cli/lib/http_api/*` |
| 通常の lib helper | `cli/lib/*.py` (migrations / projectors 以外) |

### §5.3 ATTACH 禁止 grep/CI gate

CI で以下の grep を実行し、0 件であることを確認する (carry: Phase 4.A で実装):

```bash
# アプリ層での ATTACH 禁止チェック
grep -rn "ATTACH DATABASE" cli/helix-* cli/lib/http_api/
# 期待: マッチ 0 件

# lib 全体 (migration / projector 以外)
grep -rn "ATTACH DATABASE" cli/lib/ \
  --exclude-dir=migrations \
  --exclude-dir=projectors
# 期待: マッチ 0 件
```

この CI gate は Phase 4.A の Sprint Exit 条件に組み込む (PLAN-084 §3.1 Phase 4.A 受入条件参照)。

### §5.4 cross-db 参照 pattern (正規経路)

cross-db 参照が必要な場合の正規経路:

1. **event subscribe 経由**: orchestration.db の event_envelope を vmodel / scrum が correlation_id で参照
2. **projection_state 経由**: plan.db / backend.db / frontend.db が orchestration の projection_state snapshot を read
3. **Python helper 経由**: `read_cross_db_projection(projector_id, db_name)` (D-API-SEP-draft で定義)

禁止:
- ATTACH + direct cross-db JOIN (アプリ層)
- cross-db FK 制約

---

## §6 migration v30 → v31 step (ADR-018 §Decision.5 / FR-DB-SEP-06)

### §6.1 migration script 配置

```
cli/lib/migrations/
    v31_db_separation.py    # 本 §6 の実装対象 (Phase 4.A)
```

既存パターン (`D-DB-MIGRATION.md` §2.2 / `cli/lib/helix_db.py` migrate() 関数) に準拠し、idempotent + additive で実装する。

### §6.2 dual-write start step (gate 1 対応)

**目的**: v30 (単一 helix.db) に event_envelope / projection_state table を追加し、dual-write の準備を整える。既存 v30 table は破壊しない (additive only)。

```sql
-- 既存 helix.db (v30) に追加する table (gate 1 通過条件)
-- idempotent: CREATE TABLE IF NOT EXISTS で複数回実行安全

CREATE TABLE IF NOT EXISTS event_envelope (
    event_id        TEXT NOT NULL UNIQUE,
    aggregate_id    TEXT NOT NULL CHECK(length(aggregate_id) > 0),
    aggregate_type  TEXT NOT NULL CHECK(length(aggregate_type) > 0),
    db_name         TEXT NOT NULL CHECK (db_name IN ('orchestration','vmodel','scrum')),
    event_type      TEXT NOT NULL CHECK(length(event_type) > 0),
    payload         JSON NOT NULL,
    correlation_id  TEXT NOT NULL CHECK(length(correlation_id) > 0),
    occurred_at     TEXT NOT NULL CHECK(length(occurred_at) > 0),
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (db_name, event_id)
);
-- §3.1 と byte-level 一致 (tl-advisor L3 review Round 2 P1 #3 反映)

CREATE TABLE IF NOT EXISTS projection_state (
    projector_id            TEXT NOT NULL,
    db_name                 TEXT NOT NULL,
    last_processed_event_id TEXT NOT NULL,
    snapshot                JSON,
    updated_at              TEXT NOT NULL,
    PRIMARY KEY (projector_id, db_name)
);

-- schema_version を v31 に更新
INSERT OR IGNORE INTO schema_version (version, applied_at)
    VALUES (31, datetime('now'));
```

### §6.3 6 db file 分離 step (gate 1 続き)

migration script が ATTACH で各 db file を初期化する:

```python
# cli/lib/migrations/v31_db_separation.py (疑似コード、完全実装は Phase 4.A)
DB_FILES = {
    'orchestration': '.helix/orchestration.db',
    'vmodel':        '.helix/vmodel.db',
    'scrum':         '.helix/scrum.db',
    'plan':          '.helix/plan.db',
    'backend':       '.helix/backend.db',
    'frontend':      '.helix/frontend.db',
}

def step_create_6_dbs(legacy_conn):
    """各 db file を作成し、本 doc §2.X の table shape を CREATE TABLE IF NOT EXISTS で初期化"""
    for db_name, db_path in DB_FILES.items():
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        _init_schema(conn, db_name)   # §2.X の table 定義を適用
        conn.commit()
        conn.close()
```

### §6.4 dual-write trigger (gate 2 前提)

compatibility_adapter.py が旧 helix.db と新 6 db の両方に write する dual-write を開始する。

- 旧 helix.db への write は継続 (既存テスト PASS 維持)
- 新 6 db への write は compatibility_adapter.py が routing
- mismatch gate (gate 2) が divergence 0 件 (10000 write 連続) を確認するまで dual-write を継続

### §6.5 shadow replay step (gate 3 対応)

```python
# Phase 4.C 実装対象 (carry: §7 carry 項目 #7)
def step_shadow_replay(legacy_conn, orchestration_conn, replay_limit=1000):
    """
    過去 replay_limit 件の event を新 projector で replay し、
    derived state が旧 helix.db の state と byte-level 一致するか確認する。
    不一致 → fail-close (cutover 不可)
    """
```

### §6.6 cutover step (gate 5 対応)

- 上記 gate 1-4 の全 PASS + ユーザー (PO) 承認後に実行
- 旧 helix.db への write 停止
- 6 db のみへの write に移行
- 旧 helix.db の state table を tombstone → drop (event log は保持)

### §6.7 rollback step (gate 6: cutover 後 7d 以内)

- cutover 後 7d 以内に重大 anomaly (data loss / projector down > 1h) が発生した場合に実行
- 旧 helix.db への切り戻し (event log は保持、新 projection は drop)
- PM 推奨 + PO 承認後に実行

---

## §7 carry to Phase 4

L4 実装時に確定する事項:

| # | carry 項目 | 確定 phase | 担当 |
|---|---|---|---|
| 1 | UUID v7 generator 実装 (Python library or 自前) | Phase 4.A | Codex se |
| 2 | event_envelope payload schema (event_type ごとの JSON schema) | Phase 4.B | Codex se |
| 3 | plan.db state/change_log atomicity test (SQLite transaction 制約) | Phase 4.A | Codex qa |
| 4 | cli/libexec/helix-session-start を adapter 対象外にする根拠明記 | Phase 4.A | Codex se |
| 5 | ATTACH 禁止 CI gate (grep + lint integration) | Phase 4.A | Codex se |
| 6 | projector lag 監視 = harness_monitor 統合 (lag > 1000 event → G2/G3/G4 block、Phase 4.B 以降適用) | Phase 4.B | Codex se |
| 7 | shadow replay test (過去 1000 event replay → byte-level 一致) | Phase 4.C | Codex qa |
| 8 | cutover gate 5 PO 承認手順 (runbook 起票) | Phase 4.C | PM |
| 9 | ADR-020 (cutover 判断 ADR) 起票 = gate 5 pass 後 - gate 6 前 | Phase 4.C 末 | PM/TL |

carry 項目の優先度:

- **Phase 4.A 必須**: #1 (UUID v7), #3 (atomicity test), #4 (session-start 除外根拠), #5 (CI gate)
- **Phase 4.B 必須**: #2 (payload schema), #6 (lag 監視)
- **Phase 4.C 必須**: #7 (shadow replay), #8 (runbook), #9 (ADR-020)

---

## §8 V-model trace

本文書の 4 artifact 双方向 trace (HELIX_CORE.md §V-model 4 artifact 双方向 trace / PLAN-075 準拠):

| artifact | 本文書との関係 |
|---|---|
| **① 設計** (本文書) | D-DB-SEP-draft-v0.1。L3 詳細設計 / 結合テスト設計レイヤー |
| **② 実装コード** | `cli/lib/migrations/v31_db_separation.py` + `cli/lib/projectors/*.py` (Phase 4.A/4.B 起票) |
| **③ テスト設計** | `docs/v2/L4-test-design/PLAN-084-integration-test-design.md` §2 (I-MIGRATION) + §3 (I-DUALWRITE) + §4 (I-REPLAY) (Phase 3.4 起票済、commit ff04129) + `docs/v2/L4-test-design/PLAN-084-unit-test-design.md` §2 (U-ADAPTER)
| **④ テストコード** | `cli/lib/tests/test_db_separation_integration.py` (Phase 4.B) + `cli/lib/tests/test_shadow_replay.py` (Phase 4.C) |

双方向 trace:

- **本 doc → ③ テスト設計**: `docs/v2/L4-test-design/PLAN-084-integration-test-design.md` §2 (I-MIGRATION) + §3 (I-DUALWRITE) + §4 (I-REPLAY) + `PLAN-084-unit-test-design.md` §2 (U-ADAPTER) (Phase 3.4 起票済、commit ff04129)
- **本 doc → ② 実装コード**: `cli/lib/migrations/v31_db_separation.py` (Phase 4.A)
- **③ テスト設計 → 本 doc**: PLAN-084-unit-test-design.md / PLAN-084-integration-test-design.md frontmatter `related_designs` に「D-DB-SEP-draft-v0.1」明示済 (Phase 3.4 反映済)
- **④ テストコード → ③ テスト設計**: Phase 4.B 着手時に test 実装 docstring に「DoD 検証: PLAN-084-integration-test-design.md I-MIGRATION-XXX / I-DUALWRITE-XXX / I-REPLAY-XXX」を記載 (Phase 4.B carry)

---

## §9 References

| 文書 | 参照箇所 |
|---|---|
| `docs/adr/ADR-018-db-separation-and-event-sourcing.md` §Decision.1-5 | 本文書全体の根拠。entity ownership / Event Sourcing / projector / migration gate / ATTACH 規約 |
| `docs/adr/ADR-019-double-helix-naming-principle.md` §Decision.1-4 | HELIX 命名 + 3 軸 + strand mapping |
| `docs/plans/PLAN-084-helix-db-separation-and-event-sourcing.md` §2.2-2.6 + §3.1 Phase 4 工程 | matrix の正本 (entity ownership / 6 軸判定 / projector 境界 / migration gate / adapter file 一覧) |
| `docs/v2/L1-REQUIREMENTS.md` §3.9 FR-DB-SEP-01〜09 + AC-DB-SEP-01〜07 | 受入条件の原点。各 §2.X / §3 / §4 / §5 / §6 と対応 |
| `docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md` (PLAN-070 v25-27) | 前段 v25-v27 schema (automation_runs / audit_log / session_telemetry)。§2.5 backend.db の前段 |
| `docs/design/D-DB-MIGRATION.md` (HELIX 既存 migration 戦略 v1-v4) | §6 migration step pattern の参考 (additive / idempotent / rollback_path 規約) |
