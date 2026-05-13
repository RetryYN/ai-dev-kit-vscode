-- ============================================================
-- helix.db v20 -> v21 Additive Migration SQL Draft
-- Phase 3 / Design Spike
-- Inputs:
--   docs/v2/L1-REQUIREMENTS.md (FR-DB01..10, FR-V04)
--   docs/v2/B-design/vmodel-semantics-spine.yaml
--   docs/v2/A-audit/db-schema-current.md
--   cli/lib/helix_db.py (v20 schema)
-- ============================================================

-- ============================================================
-- §1 migration step (ordered)
-- additive only / no DROP in up path
-- ============================================================

-- Step 0: preflight (manual)
-- 1) backup db
-- 2) verify current version=20
-- 3) ensure exclusive write window

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;

BEGIN IMMEDIATE TRANSACTION;

-- ------------------------------------------------------------
-- Step 1: semantic columns for vmodel core tables
-- FR-V01 / FR-DB09 / FR-DB10
-- ------------------------------------------------------------

-- contract_entries.drive
ALTER TABLE contract_entries
  ADD COLUMN drive TEXT NOT NULL DEFAULT 'be'
  CHECK (drive IN ('be','fe','db','fullstack'));

-- test_design_entries.drive
ALTER TABLE test_design_entries
  ADD COLUMN drive TEXT NOT NULL DEFAULT 'be'
  CHECK (drive IN ('be','fe','db','fullstack'));

-- design_review.drive
ALTER TABLE design_review
  ADD COLUMN drive TEXT NOT NULL DEFAULT 'be'
  CHECK (drive IN ('be','fe','db','fullstack'));

-- contract_entries lifecycle columns
ALTER TABLE contract_entries
  ADD COLUMN origin_mode TEXT NOT NULL DEFAULT 'forward'
  CHECK (origin_mode IN ('forward','reverse','scrum'));

ALTER TABLE contract_entries
  ADD COLUMN evidence_status TEXT NOT NULL DEFAULT 'confirmed'
  CHECK (evidence_status IN ('observed','inferred','confirmed'));

-- design_review lifecycle columns
ALTER TABLE design_review
  ADD COLUMN direction TEXT NOT NULL DEFAULT 'forward'
  CHECK (direction IN ('forward','reverse'));

ALTER TABLE design_review
  ADD COLUMN source_phase TEXT;

-- ------------------------------------------------------------
-- Step 2: design sprint tables
-- FR-DB07 / FR-DB08
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS design_sprint_entries (
  id INTEGER PRIMARY KEY,
  plan_id TEXT NOT NULL,
  sprint_id TEXT,
  sprint_type TEXT NOT NULL
    CHECK (sprint_type IN ('architecture','detailed','functional','impl')),
  layer TEXT NOT NULL
    CHECK (layer IN ('architecture','detailed','functional')),
  drive TEXT NOT NULL
    CHECK (drive IN ('be','fe','db','fullstack')),
  track TEXT
    CHECK (track IN ('be','fe','db','contract','shared')),
  pair_status TEXT NOT NULL DEFAULT 'pending'
    CHECK (pair_status IN ('pending','design_only','test_only','paired','waived','failed')),
  freeze_gate TEXT,
  subgate TEXT,
  frozen_at TEXT,
  raw_meta TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS design_sprint_artifact_links (
  sprint_entry_id INTEGER NOT NULL,
  artifact_kind TEXT NOT NULL
    CHECK (artifact_kind IN ('design','test_design','review','baseline')),
  artifact_ref TEXT NOT NULL,
  link_kind TEXT NOT NULL
    CHECK (link_kind IN ('covers','derives_from','reviews','implements')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (sprint_entry_id, artifact_kind, artifact_ref, link_kind),
  FOREIGN KEY (sprint_entry_id) REFERENCES design_sprint_entries(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Step 3: v21 additional registries
-- FR-DB02 / FR-DB03 / FR-DB04 / FR-DB05
-- ------------------------------------------------------------

-- er_diagrams: D-DB diagram registry
CREATE TABLE IF NOT EXISTS er_diagrams (
  id INTEGER PRIMARY KEY,
  plan_id TEXT NOT NULL,
  design_level TEXT NOT NULL
    CHECK (design_level IN ('planning','requirement','architecture','detailed','functional')),
  drive TEXT NOT NULL
    CHECK (drive IN ('be','fe','db','fullstack')),
  diagram_path TEXT NOT NULL,
  mermaid_content TEXT,
  version TEXT,
  source_phase TEXT,
  author_role TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (plan_id, design_level, drive, diagram_path, version)
);

CREATE INDEX IF NOT EXISTS idx_er_diagrams_plan_level_drive
  ON er_diagrams(plan_id, design_level, drive);

-- process_maps: process/sequence/state map registry
CREATE TABLE IF NOT EXISTS process_maps (
  id INTEGER PRIMARY KEY,
  plan_id TEXT NOT NULL,
  design_level TEXT NOT NULL
    CHECK (design_level IN ('planning','requirement','architecture','detailed','functional')),
  drive TEXT NOT NULL
    CHECK (drive IN ('be','fe','db','fullstack')),
  map_kind TEXT NOT NULL
    CHECK (map_kind IN ('flow','sequence','state','swimlane')),
  map_path TEXT NOT NULL,
  mermaid_content TEXT,
  version TEXT,
  source_phase TEXT,
  author_role TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (plan_id, design_level, drive, map_kind, map_path, version)
);

CREATE INDEX IF NOT EXISTS idx_process_maps_plan_level_drive
  ON process_maps(plan_id, design_level, drive, map_kind);

-- managed_products: multi-product management metadata
CREATE TABLE IF NOT EXISTS managed_products (
  id INTEGER PRIMARY KEY,
  product_name TEXT NOT NULL,
  product_path TEXT NOT NULL,
  drive TEXT NOT NULL
    CHECK (drive IN ('be','fe','db','fullstack')),
  mode TEXT NOT NULL
    CHECK (mode IN ('forward','reverse','scrum')),
  helix_version TEXT,
  status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active','inactive','archived')),
  raw_meta TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (product_name, product_path)
);

CREATE INDEX IF NOT EXISTS idx_managed_products_drive_mode
  ON managed_products(drive, mode, status);

-- agent_registry: agent policy snapshot
CREATE TABLE IF NOT EXISTS agent_registry (
  id INTEGER PRIMARY KEY,
  agent_kind TEXT NOT NULL,
  role TEXT NOT NULL,
  model TEXT NOT NULL,
  thinking TEXT,
  allowed_paths TEXT,
  cost_budget REAL,
  status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active','inactive')),
  raw_meta TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (agent_kind, role, model)
);

CREATE INDEX IF NOT EXISTS idx_agent_registry_role_status
  ON agent_registry(role, status);

-- ------------------------------------------------------------
-- Step 4: performance indexes (TL recommendation)
-- ------------------------------------------------------------

-- rationale: plan + drive + level scoped contract lookup
CREATE INDEX IF NOT EXISTS idx_contract_plan_drive_level
  ON contract_entries(introduced_plan, drive, design_level);

-- rationale: plan + drive + contract scoped test-design lookup
CREATE INDEX IF NOT EXISTS idx_test_design_plan_drive_contract
  ON test_design_entries(plan_id, drive, contract_id, test_level);

-- rationale: plan + drive + layer + axis + verdict review scan
CREATE INDEX IF NOT EXISTS idx_design_review_plan_drive_layer_axis
  ON design_review(plan_id, drive, layer, review_axis, verdict);

-- rationale: plan + drive + layer sprint status scan
CREATE INDEX IF NOT EXISTS idx_design_sprint_plan_drive_layer
  ON design_sprint_entries(plan_id, drive, layer, sprint_type, pair_status);

-- ------------------------------------------------------------
-- Step 5: view_vmodel_integrity (FR-V04)
-- ------------------------------------------------------------

DROP VIEW IF EXISTS view_vmodel_integrity;

CREATE VIEW view_vmodel_integrity AS
SELECT
  c.id AS contract_id,
  c.introduced_plan AS plan_id,
  c.drive AS drive,
  c.design_level AS design_level,
  c.origin_mode AS origin_mode,
  c.evidence_status AS evidence_status,
  ce.to_entry_id AS code_entry_id,
  td.id AS test_design_id,
  td.test_level AS test_level,
  tb.id AS baseline_id,
  tb.status AS baseline_status,
  CASE WHEN ce.to_entry_id IS NULL THEN 1 ELSE 0 END AS missing_code_link,
  CASE WHEN td.id IS NULL THEN 1 ELSE 0 END AS missing_test_design,
  CASE WHEN tb.id IS NULL THEN 1 ELSE 0 END AS missing_baseline,
  CASE WHEN tb.status IS NOT NULL AND tb.status NOT IN ('passed','pass','ok') THEN 1 ELSE 0 END AS failing_baseline,
  (
    100
    - (15 * CASE WHEN td.id IS NULL THEN 1 ELSE 0 END)
    - (10 * CASE WHEN tb.id IS NULL THEN 1 ELSE 0 END)
    - (20 * CASE WHEN tb.status IS NOT NULL AND tb.status NOT IN ('passed','pass','ok') THEN 1 ELSE 0 END)
  ) AS vmodel_score
FROM contract_entries c
LEFT JOIN code_edges ce
  ON ce.from_entry_id = c.id
 AND ce.edge_type IN ('implements','derives_from','covers','reviews')
LEFT JOIN test_design_entries td
  ON td.contract_id = c.id
 AND td.plan_id = c.introduced_plan
 AND td.drive = c.drive
LEFT JOIN test_baseline tb
  ON tb.test_design_id = td.id;

-- ------------------------------------------------------------
-- Step 6: schema version update (FR-DB01)
-- ------------------------------------------------------------

INSERT OR IGNORE INTO schema_version(version, applied_at)
VALUES (21, datetime('now'));

COMMIT;

-- ============================================================
-- §2 default 値の設計根拠
-- ============================================================

-- drive='be'
--   v20 の既存運用は BE 起源で drive 非保持。後方互換上の保守値として be を採用。

-- origin_mode='forward'
--   v20 は reverse/scrum provenance 未保持のため、既存 record は forward 扱いとする。

-- evidence_status='confirmed'
--   v20 以前に evidence 粒度がないため、旧 record を confirmed とみなし fail-close 誤判定を避ける。

-- ============================================================
-- §3 後方互換 (NFR-01)
-- ============================================================

-- A) 既存 v20 record の migrate
--   NOT NULL + DEFAULT により既存行は自動補完される。

-- B) 既存 query 互換
--   drive 未指定 query は継続動作。追加 index は参照専用最適化。

-- C) pair-check 互換
--   helix gate --pair-check は drive 任意利用を想定（未指定時は互換ルート）。

-- D) additive guarantee
--   up migration で DROP/RENAME は行わない。

-- ============================================================
-- §4 rollback SQL (v21 -> v20 emergency)
-- ============================================================

-- WARNING:
-- 1) 本番では非推奨（データ消失リスク）
-- 2) SQLite では DROP COLUMN 非対応の可能性あり
-- 3) 必ず DB クローンで手順検証してから使用

/*
BEGIN IMMEDIATE TRANSACTION;

DROP VIEW IF EXISTS view_vmodel_integrity;

DROP TABLE IF EXISTS design_sprint_artifact_links;
DROP TABLE IF EXISTS design_sprint_entries;
DROP TABLE IF EXISTS er_diagrams;
DROP TABLE IF EXISTS process_maps;
DROP TABLE IF EXISTS managed_products;
DROP TABLE IF EXISTS agent_registry;

DROP INDEX IF EXISTS idx_contract_plan_drive_level;
DROP INDEX IF EXISTS idx_test_design_plan_drive_contract;
DROP INDEX IF EXISTS idx_design_review_plan_drive_layer_axis;
DROP INDEX IF EXISTS idx_design_sprint_plan_drive_layer;
DROP INDEX IF EXISTS idx_er_diagrams_plan_level_drive;
DROP INDEX IF EXISTS idx_process_maps_plan_level_drive;
DROP INDEX IF EXISTS idx_managed_products_drive_mode;
DROP INDEX IF EXISTS idx_agent_registry_role_status;

ALTER TABLE contract_entries DROP COLUMN drive;
ALTER TABLE contract_entries DROP COLUMN origin_mode;
ALTER TABLE contract_entries DROP COLUMN evidence_status;
ALTER TABLE test_design_entries DROP COLUMN drive;
ALTER TABLE design_review DROP COLUMN drive;
ALTER TABLE design_review DROP COLUMN direction;
ALTER TABLE design_review DROP COLUMN source_phase;

DELETE FROM schema_version WHERE version = 21;

COMMIT;
*/

-- ============================================================
-- §5 test fixture
-- apply / rollback / compatibility
-- ============================================================

-- 5.1 migration apply test
SELECT MAX(version) AS schema_version_max
FROM schema_version;

PRAGMA table_info(contract_entries);
PRAGMA table_info(test_design_entries);
PRAGMA table_info(design_review);

SELECT name AS table_name
FROM sqlite_master
WHERE type = 'table'
  AND name IN (
    'design_sprint_entries',
    'design_sprint_artifact_links',
    'er_diagrams',
    'process_maps',
    'managed_products',
    'agent_registry'
  )
ORDER BY name;

SELECT name AS index_name
FROM sqlite_master
WHERE type = 'index'
  AND name IN (
    'idx_contract_plan_drive_level',
    'idx_test_design_plan_drive_contract',
    'idx_design_review_plan_drive_layer_axis',
    'idx_design_sprint_plan_drive_layer',
    'idx_er_diagrams_plan_level_drive',
    'idx_process_maps_plan_level_drive',
    'idx_managed_products_drive_mode',
    'idx_agent_registry_role_status'
  )
ORDER BY name;

SELECT name AS view_name
FROM sqlite_master
WHERE type = 'view'
  AND name = 'view_vmodel_integrity';

-- 5.2 compatibility test for existing records
SELECT COUNT(*) AS contract_drive_null
FROM contract_entries
WHERE drive IS NULL;

SELECT drive, COUNT(*) AS cnt
FROM contract_entries
GROUP BY drive
ORDER BY drive;

SELECT origin_mode, evidence_status, COUNT(*) AS cnt
FROM contract_entries
GROUP BY origin_mode, evidence_status
ORDER BY origin_mode, evidence_status;

SELECT COUNT(*) AS test_design_drive_null
FROM test_design_entries
WHERE drive IS NULL;

SELECT drive, COUNT(*) AS cnt
FROM test_design_entries
GROUP BY drive
ORDER BY drive;

SELECT COUNT(*) AS design_review_drive_null
FROM design_review
WHERE drive IS NULL;

SELECT direction, COUNT(*) AS cnt
FROM design_review
GROUP BY direction
ORDER BY direction;

-- 5.3 view sanity
SELECT COUNT(*) AS integrity_row_count
FROM view_vmodel_integrity;

SELECT
  MIN(vmodel_score) AS min_score,
  MAX(vmodel_score) AS max_score
FROM view_vmodel_integrity;

-- 5.4 index behavior check (manual EXPLAIN)
EXPLAIN QUERY PLAN
SELECT id
FROM contract_entries
WHERE introduced_plan = 'PLAN-001'
  AND drive = 'be'
  AND design_level = 'detailed';

EXPLAIN QUERY PLAN
SELECT id
FROM test_design_entries
WHERE plan_id = 'PLAN-001'
  AND drive = 'be'
  AND contract_id = 1
  AND test_level = 'integration';

EXPLAIN QUERY PLAN
SELECT id
FROM design_review
WHERE plan_id = 'PLAN-001'
  AND drive = 'be'
  AND layer = 'detailed'
  AND review_axis = 'vertical'
  AND verdict = 'passed';

EXPLAIN QUERY PLAN
SELECT id
FROM design_sprint_entries
WHERE plan_id = 'PLAN-001'
  AND drive = 'db'
  AND layer = 'architecture'
  AND sprint_type = 'detailed'
  AND pair_status = 'pending';

-- 5.5 rollback test procedure (manual)
-- A) clone DB
-- B) apply up migration
-- C) execute rollback block on clone
-- D) compare objects with v20 baseline

SELECT name, type
FROM sqlite_master
WHERE type IN ('table','index','view')
ORDER BY type, name;

-- End of draft
