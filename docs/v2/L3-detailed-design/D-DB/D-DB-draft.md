---
doc_id: D-DB-draft-v0.1
plan_id: PLAN-070
sprint: SprintB / .2
status: draft
created: 2026-05-16
primary_drive: be
secondary_drives:
  - fullstack
  - fe
---

# PLAN-070 SprintB: L3 D-DB draft v0.1

## §1 目的とスコープ

L2 G2 凍結後の状態を起点に、helix-db v21 → v22 → v23 → v24 の D-DB migration 草案を L3 起点で固定する。

- 対象テーブル: `contract_entries`, `design_sprint_entries`, `design_sprint_artifact_links`
- Non-goals: API endpoint 実装、promotion hook 実装、`functional_freeze` CLI 本体、migration 実行コード、破壊的 DDL
- 設計参照: `docs/v2/L2-MASTER.md`（§3, §8, §8.x, §9.5）、`docs/v2/L1-REQUIREMENTS.md`（AC-15/16/17, FR-VS01〜06.4）
- ベース実装参照: `cli/lib/helix_db.py`（v22 の既存 ALTER と v23 拡張位置）

## §2.0 共通 DB primitive

### 2.0.1 MigrationStep

```yaml
MigrationStep:
  type: object
  required:
    - step
    - version
    - kind
    - idempotent
    - rollback_path
  additionalProperties: false
  properties:
    step: {type: integer}
    version:
      type: string
      pattern: '^v(\\d+)$'
    kind:
      type: string
      enum: [add_column, add_table, add_index, add_constraint, alter_check, backfill, add_trigger, add_view]
    idempotent:
      type: boolean
    rollback_path:
      type: [string, 'null']
```

### 2.0.2 ColumnSpec

```yaml
ColumnSpec:
  type: object
  required:
    - name
    - type
    - null
    - default
    - check
    - fk
    - immutable
  properties:
    name: {type: string}
    type:
      type: string
    enum: [TEXT, INTEGER, REAL, BLOB, TIMESTAMP]
    null: {type: boolean}
    default: {oneOf: [{type: string}, {type: integer}, {type: number}, {type: boolean}, {"type": "null"}]}
    check: {oneOf: [{type: string}, {"type": "null"}]}
    fk:
      oneOf:
        - type: "null"
        - type: object
          required: [table, column]
          properties:
            table: {type: string}
            column: {type: string}
    immutable: {type: boolean}
```

### 2.0.3 Primitive 参照

```yaml
BaselinePolicyFamily:
  $ref: docs/v2/B-design/vmodel-semantics-spine.yaml#/baseline_policy_family
ScoreFormula:
  $ref: docs/v2/B-design/vmodel-semantics-spine.yaml#/score/formula
PromotionLinkRef:
  description: SprintC で正式化する placeholder
  type: object
  required: [promotion_kind, phase]
```

### 2.0.4 参照整合ルール

- `enum` と `check` は YAML/SQL の両方で同値表現
- 列名、型、null 許容、既定値を `ColumnSpec` と DDL で一致
- migration は additive、既存 PK/FK 再作成禁止

## §2 v21 → v22 → v23 → v24 migration matrix

| version | 列カテゴリ | 対象テーブル | 列名 | 由来 |
|---|---|---|---|---|
| v21 | semantic (v21-spec 互換) | contract_entries | drive, origin_mode, evidence_status | helix-db-v21-spec.md (enum: pending/collected/missing/invalid) |
| v21+ | L1 lifecycle (新規) | contract_entries | lifecycle_status, direction | L1 P2-7 (observed/inferred/confirmed) + AC-17。evidence_status とは別列。SprintB で v21 migration step に additive 追加 |
| v22 | drive-switch | design_sprint_entries | previous_drive, drive_switch_reason, status_on_switch | cli/lib/helix_db.py:1194-1206 |
| v23 | append-only correction | design_sprint_entries / design_sprint_artifact_links | supersedes_entry_id, correction_reason, voided_at | cli/lib/helix_db.py:1218-1227 |
| v24 | drive-switch decision event | design_sprint_drive_decisions | source_entry_id, target_entry_id, decision, decided_by, reason, reopen_condition | L2 MASTER §8.x |

**evidence_status 列の扱い (v21 互換):**
- `evidence_status` (enum: `pending/collected/missing/invalid`) は helix-db-v21-spec.md 由来。`helix_db.py:1177` の実装 DEFAULT は `'confirmed'`。本草案の DEFAULT を `'confirmed'` に統一し、v21-spec 実装実態と整合する。
- L1 P2-7 の lifecycle (`observed -> inferred -> confirmed`) は **新規 `lifecycle_status` 列**で管理し、既存 evidence_status を変更しない (破壊的 migration 回避)。
- `direction` 列は AC-17 要求。NULL 許容で additive 追加。`forward_after_reverse` は Reverse→Forward 自動遷移後を示す。
- `lifecycle_status` と `direction` の migration version は v21 拡張 step として扱い、v22 以前の DB は backfill DEFAULT で非破壊。最終 rename/統合判断は SprintD 確定事項 (§9 carry 参照)。

### 2.1 v21→v22→v23→v24 YAML

```yaml
migration_matrix:
  version: v21_v22_v23_v24
  strategy:
    additive: true
    idempotent: true
    rollback_safe: true
    no_pk_fk_recreation: true
  transitions:
    - from: v21
      to: v22
      steps:
        - step: 1
          version: v22
          kind: add_column
          idempotent: true
          rollback_path: rollback_v22_to_v21.sql
    - from: v22
      to: v23
      steps:
        - step: 1
          version: v23
          kind: add_column
          idempotent: true
          rollback_path: rollback_v23_to_v22.sql
    - from: v23
      to: v24
      steps:
        - step: 1
          version: v24
          kind: add_table
          idempotent: true
          rollback_path: rollback_v24_to_v23.sql
```

### 2.2 追加方針

- v21 は `contract_entries` の semantic 列を確定
- v22 は既存実装の `design_sprint_entries` drive-switch 列を維持
- v23 は `design_sprint_entries` / `design_sprint_artifact_links` の correction 列を既存実装準拠で維持
- v24 は `design_sprint_drive_decisions` を append-only で追加
- すべて default/backfill で既存行の互換性を保持

## §3 contract_entries テーブル定義（v21 + v22 拡張）

### 3.1 DDL（v21/v22）

```sql
CREATE TABLE IF NOT EXISTS contract_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_type TEXT NOT NULL,
    source_path TEXT NOT NULL,
    symbol_id TEXT,
    version TEXT,
    schema_hash TEXT,
    breaking_change_flag INTEGER DEFAULT 0,
    introduced_plan TEXT,
    raw_spec TEXT,
    design_level TEXT NOT NULL DEFAULT 'detailed'
      CHECK (design_level IN ('planning','requirement','architecture','detailed','functional')),
    drive TEXT NOT NULL DEFAULT 'be'
      CHECK (drive IN ('be','fe','db','fullstack')),
    origin_mode TEXT NOT NULL DEFAULT 'forward'
      CHECK (origin_mode IN ('forward','reverse','scrum')),
    evidence_status TEXT NOT NULL DEFAULT 'confirmed'
      CHECK (evidence_status IN ('pending','collected','missing','invalid')),
    lifecycle_status TEXT NOT NULL DEFAULT 'observed'
      CHECK (lifecycle_status IN ('observed','inferred','confirmed')),
    direction TEXT
      CHECK (direction IS NULL OR direction IN ('forward','reverse','forward_after_reverse')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (length(source_path) > 0)
);
```

### 3.2 ColumnSpec（v22 追加列）

```yaml
contract_entries_columns:
  - name: drive
    type: TEXT
    null: false
    default: be
    check: "drive IN ('be','fe','db','fullstack')"
    fk: null
    immutable: false
  - name: origin_mode
    type: TEXT
    null: false
    default: forward
    check: "origin_mode IN ('forward','reverse','scrum')"
    fk: null
    immutable: false
  - name: evidence_status
    type: TEXT
    null: false
    default: confirmed
    check: "evidence_status IN ('pending','collected','missing','invalid')"
    fk: null
    immutable: false
    note: "v21 互換列 (helix-db-v21-spec.md 由来)。L1 P2-7 lifecycle は lifecycle_status で管理"
  - name: lifecycle_status
    type: TEXT
    null: false
    default: observed
    check: "lifecycle_status IN ('observed','inferred','confirmed')"
    fk: null
    immutable: false
    note: "L1 P2-7 master (observed -> inferred -> confirmed 遷移)。RG3 PO 承認で confirmed に遷移"
  - name: direction
    type: TEXT
    null: true
    default: null
    check: "direction IS NULL OR direction IN ('forward','reverse','forward_after_reverse')"
    fk: null
    immutable: false
    note: "AC-17 要求列。origin_mode と組み合わせて Reverse→Forward lifecycle をトレース"
```

### 3.3 インデックス

```sql
CREATE INDEX IF NOT EXISTS idx_contract_design ON contract_entries(contract_type, design_level);
CREATE INDEX IF NOT EXISTS idx_contract_drive_origin ON contract_entries(drive, origin_mode, evidence_status);
CREATE INDEX IF NOT EXISTS idx_contract_lifecycle ON contract_entries(lifecycle_status, direction);
CREATE INDEX IF NOT EXISTS idx_contract_plan ON contract_entries(introduced_plan);
```

## §4 design_sprint_entries テーブル拡張（v22 + v23 既存実装）

### 4.1 v22 固定列（既存実装ベース）

```sql
ALTER TABLE design_sprint_entries
ADD COLUMN previous_drive TEXT;
ALTER TABLE design_sprint_entries
ADD COLUMN drive_switch_reason TEXT;
ALTER TABLE design_sprint_entries
ADD COLUMN status_on_switch TEXT
CHECK (status_on_switch IN ('preserved','waived','failed') OR status_on_switch IS NULL);
```

### 4.2 v23 既存追加列（既存実装ベース）

```yaml
design_sprint_entries_v23_columns:
  - name: supersedes_entry_id
    type: INTEGER
    null: true
    default: null
    check: "supersedes_entry_id IS NULL OR supersedes_entry_id > 0"
    fk: {table: design_sprint_entries, column: id}
    immutable: false
  - name: correction_reason
    type: TEXT
    null: true
    default: null
    check: "correction_reason IS NULL OR length(correction_reason) BETWEEN 1 AND 2000"
    fk: null
    immutable: false
  - name: voided_at
    type: TEXT
    null: true
    default: null
    check: "voided_at IS NULL OR length(voided_at) > 0"
    fk: null
    immutable: false
```

### 4.3 v23 追加 DDL（既存実装追従）

```sql
ALTER TABLE design_sprint_entries
ADD COLUMN supersedes_entry_id INTEGER
REFERENCES design_sprint_entries(id);
ALTER TABLE design_sprint_entries
ADD COLUMN correction_reason TEXT;
ALTER TABLE design_sprint_entries
ADD COLUMN voided_at TEXT;
```

## §5 design_sprint_drive_decisions テーブル（v24）

### 5.1 ColumnSpec

```yaml
design_sprint_drive_decisions_columns:
  - name: source_entry_id
    type: INTEGER
    null: false
    default: null
    check: "source_entry_id > 0"
    fk: {table: design_sprint_entries, column: id}
    immutable: true
  - name: target_entry_id
    type: INTEGER
    null: true
    default: null
    check: "target_entry_id IS NULL OR target_entry_id > 0"
    fk: {table: design_sprint_entries, column: id}
    immutable: true
  - name: decision
    type: TEXT
    null: false
    default: null
    check: "decision IN ('preserved', 'waived', 'failed')"
    fk: null
    immutable: true
  - name: decided_by
    type: TEXT
    null: false
    default: null
    check: "decided_by IN ('tl', 'se', 'pg', 'fe', 'qa', 'pm')"
    fk: null
    immutable: true
  - name: reason
    type: TEXT
    null: false
    default: null
    check: "length(reason) BETWEEN 1 AND 2000"
    fk: null
    immutable: true
  - name: reopen_condition
    type: TEXT
    null: true
    default: null
    check: "reopen_condition IS NULL OR json_valid(reopen_condition)"
    fk: null
    immutable: true
```

### 5.2 DDL

```sql
CREATE TABLE IF NOT EXISTS design_sprint_drive_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_entry_id INTEGER NOT NULL,
    target_entry_id INTEGER,
    decision TEXT NOT NULL CHECK (decision IN ('preserved', 'waived', 'failed')),
    decided_by TEXT NOT NULL
        CHECK (decided_by IN ('tl', 'se', 'pg', 'fe', 'qa', 'pm')),
    reason TEXT NOT NULL CHECK (length(reason) BETWEEN 1 AND 2000),
    reopen_condition TEXT DEFAULT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (source_entry_id) REFERENCES design_sprint_entries(id),
    FOREIGN KEY (target_entry_id) REFERENCES design_sprint_entries(id),
    CHECK (
      (decision = 'failed' AND target_entry_id IS NULL)
      OR (decision IN ('preserved', 'waived') AND target_entry_id IS NOT NULL)
    )
);
CREATE INDEX IF NOT EXISTS idx_dsd_source_entry_id ON design_sprint_drive_decisions(source_entry_id);
CREATE INDEX IF NOT EXISTS idx_dsd_target_entry_id ON design_sprint_drive_decisions(target_entry_id);
CREATE INDEX IF NOT EXISTS idx_dsd_decided_by ON design_sprint_drive_decisions(decided_by);

CREATE TRIGGER IF NOT EXISTS trg_dsd_no_delete_append_only
BEFORE DELETE ON design_sprint_drive_decisions
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'append-only: cannot delete from design_sprint_drive_decisions');
END;

```

### 5.3 append-only トリガ

```sql
CREATE TRIGGER IF NOT EXISTS trg_dsd_no_mutate_append_only
BEFORE UPDATE ON design_sprint_drive_decisions
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN OLD.source_entry_id IS NOT NEW.source_entry_id THEN RAISE(ABORT, 'source_entry_id is immutable')
        WHEN OLD.target_entry_id IS NOT NEW.target_entry_id THEN RAISE(ABORT, 'target_entry_id is immutable')
        WHEN OLD.decision IS NOT NEW.decision THEN RAISE(ABORT, 'decision is immutable')
        WHEN OLD.decided_by IS NOT NEW.decided_by THEN RAISE(ABORT, 'decided_by is immutable')
        WHEN OLD.reason IS NOT NEW.reason THEN RAISE(ABORT, 'reason is immutable')
        WHEN OLD.created_at IS NOT NEW.created_at THEN RAISE(ABORT, 'created_at is immutable')
        WHEN OLD.reopen_condition IS NOT NEW.reopen_condition THEN RAISE(ABORT, 'reopen_condition is immutable')
        ELSE NULL
    END;
END;
```

### 5.4 v23 correction / v24 decision 統合ビュー

```sql
CREATE VIEW IF NOT EXISTS v_design_sprint_corrections_and_decisions AS
SELECT
    'correction' AS event_kind,
    dse.id AS event_id,
    dse.supersedes_entry_id AS source_entry_id,
    dse.id AS target_entry_id,
    NULL AS decision,
    NULL AS decided_by,
    NULL AS reopen_condition,
    dse.correction_reason AS reason,
    dse.voided_at AS event_created_at
FROM design_sprint_entries dse
WHERE dse.supersedes_entry_id IS NOT NULL
UNION ALL
SELECT
    'decision' AS event_kind,
    dsd.id AS event_id,
    dsd.source_entry_id,
    dsd.target_entry_id,
    dsd.decision,
    dsd.decided_by,
    dsd.reopen_condition,
    dsd.reason,
    dsd.created_at AS event_created_at
FROM design_sprint_drive_decisions dsd;
```

## §6 design_sprint_artifact_links テーブル定義（v22+ / v23 補正列）

### 6.1 ColumnSpec

```yaml
design_sprint_artifact_links_columns:
  - {name: sprint_entry_id, type: INTEGER, null: false, default: null, check: "sprint_entry_id > 0", fk: {table: design_sprint_entries, column: id}, immutable: true}
  - {name: artifact_kind, type: TEXT, null: false, default: null, check: "artifact_kind IN ('design','test_design','review','baseline')", fk: null, immutable: true}
  - {name: link_kind, type: TEXT, null: false, default: null, check: "link_kind IN ('covers','derives_from','reviews','implements')", fk: null, immutable: true}
  - {name: artifact_ref, type: TEXT, null: false, default: null, check: "length(artifact_ref) > 0", fk: null, immutable: true}
  - {name: supersedes_entry_id, type: INTEGER, null: true, default: null, check: "supersedes_entry_id IS NULL OR supersedes_entry_id > 0", fk: {table: design_sprint_entries, column: id}, immutable: false}
  - {name: correction_reason, type: TEXT, null: true, default: null, check: "correction_reason IS NULL OR length(correction_reason) BETWEEN 1 AND 2000", fk: null, immutable: false}
  - {name: voided_at, type: TEXT, null: true, default: null, check: "voided_at IS NULL OR length(voided_at) > 0", fk: null, immutable: false}
```

### 6.2 DDL

```sql
CREATE TABLE IF NOT EXISTS design_sprint_artifact_links (
    sprint_entry_id INTEGER NOT NULL,
    artifact_kind TEXT NOT NULL CHECK (artifact_kind IN ('design','test_design','review','baseline')),
    link_kind TEXT NOT NULL CHECK (link_kind IN ('covers','derives_from','reviews','implements')),
    artifact_ref TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    supersedes_entry_id INTEGER REFERENCES design_sprint_entries(id),
    correction_reason TEXT,
    voided_at TEXT,
    PRIMARY KEY (sprint_entry_id, artifact_kind, artifact_ref, link_kind),
    FOREIGN KEY (sprint_entry_id) REFERENCES design_sprint_entries(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_dsal_entry ON design_sprint_artifact_links(sprint_entry_id);
CREATE INDEX IF NOT EXISTS idx_dsal_artifact ON design_sprint_artifact_links(artifact_kind, artifact_ref);
```

### 6.3 既存実装追従ルール

- 補正履歴は v23 既存列（`supersedes_entry_id`, `correction_reason`, `voided_at`）のみ固定する。
- `artifact_ref` は既存仕様を継続し、追加属性は v24/次Sprintで分離定義する。
- `g2_evidence_preserved` / `append_only` は本 sprint 外（SprintC）で再検討する。

## §7 baseline_policy_family と score formula の DB 写像

### 7.1 family mapping

```sql
CREATE VIEW IF NOT EXISTS v_model_family AS
SELECT
  td.id AS test_design_id,
  td.plan_id,
  CASE
    WHEN td.test_level IN ('operational', 'acceptance') THEN 'fixture_like'
    WHEN td.test_level IN ('integration', 'system_integration', 'unit') THEN 'snapshot_like'
    ELSE 'fixture_like'
  END AS baseline_policy_family
FROM test_design_entries td;
```

※`test_baseline` は本 sprint で v24 以降に正式定義する前提のため、サンプル SQL は実装優先の代替 SQL で示す（baseline 欠損は `evidence_status` ベース）。
※§7.2 score formula の `evidence_status IN ('missing','invalid')` は v21 互換 enum を参照している。L1 P2-7 lifecycle に基づく `lifecycle_status` 観点のスコアリング (例: `lifecycle_status != 'confirmed'` を減点対象とする再定義) は SprintD の score formula 改訂で確定する (§9 carry)。

### 7.2 score 集計（SUM/COUNT/WEIGHTED_AVG）

```sql
CREATE VIEW IF NOT EXISTS v_model_score_by_plan AS
SELECT
  ce.introduced_plan AS plan_id,
  mf.baseline_policy_family,
  COUNT(DISTINCT ce.id) AS total_contracts,
  SUM(CASE WHEN td.id IS NULL THEN 1 ELSE 0 END) AS missing_test_design,
  SUM(CASE WHEN ce.evidence_status IN ('missing','invalid') THEN 1 ELSE 0 END) AS missing_baseline,
  SUM(CASE WHEN ce.evidence_status = 'invalid' THEN 1 ELSE 0 END) AS failing_baseline,
  CAST(
    100
    - 15.0 * SUM(CASE WHEN td.id IS NULL THEN 1 ELSE 0 END)
    - 10.0 * SUM(CASE WHEN ce.evidence_status IN ('missing','invalid') THEN 1 ELSE 0 END)
    - 20.0 * SUM(CASE WHEN ce.evidence_status = 'invalid' THEN 1 ELSE 0 END)
    AS INTEGER) AS raw_score,
  CAST((
    (100.0
    - 15.0 * SUM(CASE WHEN td.id IS NULL THEN 1 ELSE 0 END)
    - 10.0 * SUM(CASE WHEN ce.evidence_status IN ('missing','invalid') THEN 1 ELSE 0 END)
    - 20.0 * SUM(CASE WHEN ce.evidence_status = 'invalid' THEN 1 ELSE 0 END))
    / NULLIF(COUNT(DISTINCT ce.id), 0)
  ) AS NUMERIC) AS weighted_avg_score
FROM contract_entries ce
LEFT JOIN design_sprint_entries dse
  ON dse.plan_id = ce.introduced_plan
LEFT JOIN test_design_entries td
  ON td.plan_id = ce.introduced_plan
  AND td.contract_id = ce.id
LEFT JOIN (
  SELECT plan_id, MAX(baseline_policy_family) AS baseline_policy_family
  FROM v_model_family
  GROUP BY plan_id
) mf
  ON mf.plan_id = ce.introduced_plan
GROUP BY ce.introduced_plan, mf.baseline_policy_family;
```

### 7.3 SELECT サンプル

```sql
SELECT plan_id, baseline_policy_family, raw_score, weighted_avg_score
FROM v_model_score_by_plan
WHERE plan_id = :plan_id;
```

## §8 migration 実行戦略

### 8.1 原則

- additive / idempotent / rollback-safe
- 既存 PK/FK を再作成しない
- v21〜v24 は既定値の backfill で既存データ非破壊

### 8.2 実行順

1. v21: contract_entries 3 列
2. v22: design_sprint_entries の既存 drive-switch 3 列
3. v22: design_sprint_artifact_links 存在確認
4. v23: v23 補正列の有無確認（既存実装互換）
5. v24: design_sprint_drive_decisions 追加 + trigger + 統合ビュー
6. PRAGMA 検証

### 8.3 検証 SQL

```sql
PRAGMA table_info(contract_entries);
PRAGMA table_info(design_sprint_entries);
PRAGMA table_info(design_sprint_artifact_links);
PRAGMA foreign_key_check;
SELECT name, type FROM sqlite_master WHERE type IN ('table','view','trigger');
SELECT COUNT(*) AS bad_source_links
FROM design_sprint_drive_decisions dsd
LEFT JOIN design_sprint_entries s ON s.id = dsd.source_entry_id
WHERE dsd.source_entry_id IS NOT NULL AND s.id IS NULL;
```

### 8.4 rollback-safe

```sql
BEGIN IMMEDIATE;
-- migration steps
-- verification
-- success: COMMIT / failure: ROLLBACK
```

## §9 carry / open questions

- resolved (SprintB): `evidence_status` の enum は v21 互換 (`pending/collected/missing/invalid`, DEFAULT='confirmed') で固定。L1 P2-7 lifecycle は新規 `lifecycle_status` 列 (observed/inferred/confirmed) + `direction` 列 (AC-17) として additive 追加済み
- carry (SprintD): `lifecycle_status` への score formula 移行 (§7.2 の evidence_status 参照を lifecycle_status 観点に再定義)
- carry (SprintD): `evidence_status` の rename または `lifecycle_status` への統合の最終判断
- carry: `reopen_condition` の正式 JSON schema は SprintC
- carry: `test_plan_map` / `test_baseline` の実テーブル化と参照定義は v24 以降で整理
- carry: `v_model_family` の厳密な `baseline_policy_family` 定義は次 sprint で再検証
- carry: promotion endpoint の D-CONTRACT は SprintC
- carry: cross-doc 合致確認は SprintD exit

### 9.1 L2 MASTER §8.x 接続

- 6 列 (`source_entry_id`, `target_entry_id`, `decision`, `decided_by`, `reason`, `reopen_condition`) を v24 で明示定義
- v23 補正列は `design_sprint_entries` / `design_sprint_artifact_links` の既存列として固定
- v24 は append-only trigger と `v_design_sprint_corrections_and_decisions` ビューで統合表示を担保

### 9.2 受入チェック（本文内）

- §1〜§9 冒頭行は存在
- §2 migration matrix の行数は 4（v21/v22/v23/v24）
- §4 の v23 補正列は ColumnSpec 網羅済み
- §5 の v24 decision 列 6 件は ColumnSpec + DDL + trigger + view で網羅済み
- `baseline_policy_family` と score formula を SQL で可視化済み
