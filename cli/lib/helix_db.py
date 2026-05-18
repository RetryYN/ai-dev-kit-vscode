#!/usr/bin/env python3
"""HELIX ログデータベース — SQLite ベースのタスク実行・評価・改善追跡

責務: HELIX の実行ログを SQLite に永続化し、集計/参照 API を提供する。

Usage:
  python3 helix_db.py init <db_path>
  python3 helix_db.py record-task <db> <json>
  python3 helix_db.py record-action <db> <json>
  python3 helix_db.py record-observation <db> <json>
  python3 helix_db.py record-feedback <db> <json>
  python3 helix_db.py record-invocation <db> <json>
  python3 helix_db.py record-feedback-argv <db> <task_run_id_or_0> <type> <category> <desc> [impact] [resolution]
  python3 helix_db.py latest-task-run <db> <task_id>
  python3 helix_db.py report <db> [summary|tasks|actions|feedback|quality|session] [date]
  python3 helix_db.py export-json <db> <output_path>
  python3 helix_db.py insert [<db_path>] <table> <json>
"""

import json
import os
import re
import sqlite3
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

try:
    from .concurrent_lock import file_lock
except ImportError:  # pragma: no cover
    from concurrent_lock import file_lock

try:
    from .migrations import (
        v31_db_separation,
        v32_design_doc_web_search_audit,
        v33_gate_audit_metrics,
    )
except ImportError:  # pragma: no cover
    from migrations import (
        v31_db_separation,
        v32_design_doc_web_search_audit,
        v33_gate_audit_metrics,
    )


SCHEMA = """
-- タスク実行ログ
CREATE TABLE IF NOT EXISTS task_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,           -- T001, T002, ...
    task_type TEXT NOT NULL,         -- research-library, review-security, ...
    plan_goal TEXT,                  -- タスクプランのゴール
    role TEXT NOT NULL,              -- tl, se, pg, security, ...
    status TEXT DEFAULT 'running',   -- running, completed, failed, skipped
    started_at TEXT NOT NULL,
    completed_at TEXT,
    output_log TEXT,                 -- 実行ログのパス or 内容
    created_at TEXT DEFAULT (datetime('now'))
);

-- アクション実行ログ
CREATE TABLE IF NOT EXISTS action_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_run_id INTEGER REFERENCES task_runs(id),
    action_index INTEGER NOT NULL,  -- アクション列内の順番
    action_type TEXT NOT NULL,      -- search-external, fact-check, ...
    action_desc TEXT,               -- アクションの説明
    status TEXT DEFAULT 'pending',  -- pending, passed, failed, skipped
    evidence TEXT,                  -- 作業の証跡
    created_at TEXT DEFAULT (datetime('now'))
);

-- オブザーバー結果
CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_run_id INTEGER REFERENCES task_runs(id),
    action_log_id INTEGER REFERENCES action_logs(id),
    action_type TEXT NOT NULL,
    expected_keywords TEXT,          -- JSON array
    matched_keywords TEXT,           -- JSON array (実際にマッチしたもの)
    passed INTEGER NOT NULL,        -- 1=pass, 0=fail
    reason TEXT,                    -- 失敗理由
    created_at TEXT DEFAULT (datetime('now'))
);

-- ユーザーフィードバック
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_run_id INTEGER REFERENCES task_runs(id),
    feedback_type TEXT NOT NULL,    -- correction, praise, suggestion, complaint
    category TEXT,                  -- task-selection, quality, missing-action, wrong-role, scope
    description TEXT NOT NULL,
    impact TEXT,                    -- high, medium, low
    resolution TEXT,                -- どう改善したか
    created_at TEXT DEFAULT (datetime('now'))
);

-- タスク選択評価（集計ビュー用）
CREATE TABLE IF NOT EXISTS task_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_goal TEXT,
    task_type TEXT NOT NULL,
    was_useful INTEGER,             -- 1=有用, 0=不要だった
    was_sufficient INTEGER,         -- 1=十分, 0=追加作業が必要だった
    quality_score REAL,             -- 0.0-1.0 (observation pass率)
    user_score REAL,                -- ユーザー評価 (1-5)
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- タスク選択ログ（PM が何を選び、何を選ばなかったか）
CREATE TABLE IF NOT EXISTS task_selections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL,              -- プランの識別子
    plan_goal TEXT NOT NULL,
    selected_tasks TEXT NOT NULL,        -- JSON array: 選択したタスクID
    available_tasks TEXT,                -- JSON array: カタログの全タスク（選択肢）
    selection_rationale TEXT,            -- PM がなぜこのタスクを選んだか
    review_status TEXT DEFAULT 'pending', -- pending, approved, rejected, revised
    review_result TEXT,                  -- TL レビュー結果
    review_suggestions TEXT,            -- TL からの追加/削除提案
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS gate_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_run_id INTEGER REFERENCES task_runs(id),
    gate TEXT NOT NULL,
    result TEXT NOT NULL,
    fail_reasons TEXT DEFAULT '',
    retry_count INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plan_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL,
    verdict TEXT NOT NULL,
    reviewer TEXT DEFAULT 'tl',
    findings_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS interrupts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_run_id INTEGER REFERENCES task_runs(id),
    interrupt_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    classification TEXT NOT NULL,
    scope TEXT DEFAULT '',
    status TEXT NOT NULL,
    duration_ms INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    resolved_at TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS retro_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gate TEXT NOT NULL,
    gate_name TEXT,
    gate_run_id INTEGER REFERENCES gate_runs(id),
    item_type TEXT NOT NULL,
    content TEXT NOT NULL,
    owner TEXT DEFAULT '',
    due TEXT DEFAULT '',
    done INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS debt_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    priority TEXT NOT NULL,
    source TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL,
    resolved_at TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS hook_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    file TEXT NOT NULL,
    result TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cost_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    model TEXT NOT NULL,
    thinking TEXT DEFAULT 'high',
    tokens_est INTEGER DEFAULT 0,
    cost_est REAL DEFAULT 0.0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bench_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skill_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_text TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    references_used TEXT,
    agent_used TEXT,
    match_score REAL,
    match_reason TEXT,
    outcome TEXT,
    user_feedback TEXT,
    result_stdout TEXT,
    result_stderr TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_task_runs_type ON task_runs(task_type);
CREATE INDEX IF NOT EXISTS idx_task_runs_role ON task_runs(role);
CREATE INDEX IF NOT EXISTS idx_task_runs_task_id_id_desc ON task_runs(task_id, id DESC);
CREATE INDEX IF NOT EXISTS idx_action_logs_type ON action_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_action_logs_task_run_status ON action_logs(action_type, status);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_feedback_category ON feedback(category);
CREATE INDEX IF NOT EXISTS idx_task_selections_plan ON task_selections(plan_id);
CREATE INDEX IF NOT EXISTS idx_gate_runs_task_run_id ON gate_runs(task_run_id);
CREATE INDEX IF NOT EXISTS idx_interrupts_task_run_id ON interrupts(task_run_id);
CREATE INDEX IF NOT EXISTS idx_retro_items_gate_run_id ON retro_items(gate_run_id);
CREATE INDEX IF NOT EXISTS idx_skill_usage_skill ON skill_usage(skill_id);
CREATE INDEX IF NOT EXISTS idx_skill_usage_outcome ON skill_usage(outcome);
"""


PRAGMA_JOURNAL_MODE = "WAL"
PRAGMA_BUSY_TIMEOUT_MS = 5000
DEFAULT_SQLITE_TIMEOUT_SEC = PRAGMA_BUSY_TIMEOUT_MS / 1000.0
CURRENT_SCHEMA_VERSION = 33
HELIX_DB_LOCK_NAME = "helix-db"


SCHEMA_VERSION_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
"""


REQUIREMENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    req_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    acceptance_criteria TEXT DEFAULT '[]',
    feature TEXT DEFAULT '',
    status TEXT DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS req_impl_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    req_id TEXT NOT NULL,
    impl_path TEXT NOT NULL,
    impl_type TEXT DEFAULT 'source',
    verified INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (req_id) REFERENCES requirements(req_id)
);

CREATE TABLE IF NOT EXISTS req_test_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    req_id TEXT NOT NULL,
    acc_index INTEGER DEFAULT 0,
    test_path TEXT NOT NULL,
    test_result TEXT DEFAULT 'pending',
    created_at TEXT NOT NULL,
    FOREIGN KEY (req_id) REFERENCES requirements(req_id)
);

CREATE TABLE IF NOT EXISTS req_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    req_id TEXT NOT NULL,
    change_type TEXT NOT NULL,
    reason TEXT NOT NULL,
    old_value TEXT DEFAULT '',
    new_value TEXT DEFAULT '',
    source TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (req_id) REFERENCES requirements(req_id)
);
"""


ACCURACY_SCORE_GATES = ("G2", "G3", "G4", "G5", "G6", "G7", "L8", "PLAN_REVIEW")
ACCURACY_SCORE_DIMENSIONS = ("density", "depth", "breadth", "accuracy", "maintainability")


ACCURACY_SCORE_SCHEMA = """
CREATE TABLE IF NOT EXISTS accuracy_score (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL,
    gate TEXT NOT NULL CHECK(gate IN ('G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'L8', 'PLAN_REVIEW')),
    dimension TEXT NOT NULL CHECK(dimension IN ('density', 'depth', 'breadth', 'accuracy', 'maintainability')),
    level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 5),
    comment TEXT DEFAULT '',
    evidence TEXT DEFAULT '',
    recorded_at TEXT NOT NULL,
    sprint TEXT DEFAULT NULL,
    reviewer TEXT DEFAULT 'codex-tl'
);

CREATE INDEX IF NOT EXISTS idx_accuracy_score_plan_gate
    ON accuracy_score(plan_id, gate);

CREATE INDEX IF NOT EXISTS idx_accuracy_score_recorded_at
    ON accuracy_score(recorded_at);
"""


INFRA_SCHEMA_V9 = """
-- automation/scheduler
CREATE TABLE IF NOT EXISTS schedules (
    id TEXT PRIMARY KEY,
    schedule_expr TEXT NOT NULL,
    task_type TEXT NOT NULL CHECK(task_type IN ('helix:command', 'shell:script', 'http:webhook')),
    task_payload TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'success', 'failed', 'cancelled')) DEFAULT 'pending',
    next_run_at INTEGER,
    last_run_at INTEGER,
    last_error TEXT DEFAULT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON schedules(next_run_at) WHERE status = 'pending';

-- automation/job-queue
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    task_type TEXT NOT NULL CHECK(task_type IN ('helix:command', 'shell:script', 'http:webhook')),
    task_payload TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 5 CHECK(priority BETWEEN 1 AND 10),
    status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'success', 'failed', 'cancelled')) DEFAULT 'pending',
    created_at INTEGER NOT NULL,
    started_at INTEGER,
    completed_at INTEGER,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    last_error TEXT DEFAULT NULL,
    delay_until INTEGER
);
CREATE INDEX IF NOT EXISTS idx_jobs_status_priority ON jobs(status, priority DESC, created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_delay ON jobs(delay_until) WHERE status = 'pending';

-- automation/lock (DB lock 用)
CREATE TABLE IF NOT EXISTS locks (
    name TEXT PRIMARY KEY,
    pid INTEGER NOT NULL,
    acquired_at INTEGER NOT NULL,
    expires_at INTEGER,
    scope TEXT NOT NULL CHECK(scope IN ('home', 'project')) DEFAULT 'project'
);
CREATE INDEX IF NOT EXISTS idx_locks_expires ON locks(expires_at) WHERE expires_at IS NOT NULL;

-- automation/observability (events)
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT NOT NULL,
    occurred_at INTEGER NOT NULL,
    data_json TEXT NOT NULL DEFAULT '{}',
    source TEXT DEFAULT NULL,
    severity TEXT CHECK(severity IN ('debug', 'info', 'warning', 'error', 'critical')) DEFAULT 'info'
);
CREATE INDEX IF NOT EXISTS idx_events_name_at ON events(event_name, occurred_at);
CREATE INDEX IF NOT EXISTS idx_events_severity ON events(severity, occurred_at) WHERE severity IN ('warning', 'error', 'critical');

-- automation/observability (metrics)
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    value REAL NOT NULL,
    tags_json TEXT DEFAULT '{}',
    recorded_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_metrics_name_at ON metrics(metric_name, recorded_at);

-- automation/init-setup
CREATE TABLE IF NOT EXISTS setup_checks (
    component TEXT PRIMARY KEY,
    verify_state TEXT NOT NULL CHECK(verify_state IN ('pending', 'running', 'success', 'failed', 'cancelled')),
    installed INTEGER NOT NULL DEFAULT 0,
    last_verify_at INTEGER,
    last_install_at INTEGER,
    last_repair_at INTEGER,
    verify_error TEXT,
    install_version TEXT,
    install_path TEXT,
    updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS setup_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component TEXT NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('verify','install','repair')),
    status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'success', 'failed', 'cancelled')),
    outcome TEXT,
    details_json TEXT,
    created_at INTEGER NOT NULL,
    FOREIGN KEY(component) REFERENCES setup_checks(component) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_setup_events_component_created ON setup_events(component, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_setup_events_status ON setup_events(status);
"""


AUDIT_DECISIONS_SCHEMA_V10 = """
CREATE TABLE IF NOT EXISTS import_runs (
    id TEXT PRIMARY KEY,
    started_at INTEGER NOT NULL,
    completed_at INTEGER,
    source_hash TEXT NOT NULL,
    scope_hash TEXT NOT NULL,
    imported_rows INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL CHECK(status IN ('started', 'success', 'failed')),
    error_summary TEXT
);

CREATE TABLE IF NOT EXISTS audit_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    scope_hash TEXT NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('keep', 'remove', 'merge', 'deprecate')),
    evidence TEXT NOT NULL DEFAULT '{}',
    rationale TEXT NOT NULL,
    fail_safe_action TEXT NOT NULL CHECK(fail_safe_action IN ('skip', 'quarantine', 'manual_review')),
    status TEXT NOT NULL CHECK(status IN ('active', 'historical')) DEFAULT 'active',
    import_run_id TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    decision_hash TEXT NOT NULL,
    imported_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (import_run_id) REFERENCES import_runs(id) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_audit_decisions_active_unique
    ON audit_decisions(candidate_id, schema_version)
    WHERE status = 'active';

CREATE UNIQUE INDEX IF NOT EXISTS idx_audit_decisions_event_unique
    ON audit_decisions(candidate_id, schema_version, scope_hash, decision_hash);

CREATE INDEX IF NOT EXISTS idx_audit_decisions_import_run_id
    ON audit_decisions(import_run_id);

CREATE INDEX IF NOT EXISTS idx_import_runs_status
    ON import_runs(status, started_at);
"""


TASK_TYPES_V9 = ("helix:command", "shell:script", "http:webhook")
AUTOMATION_STATUSES_V9 = ("pending", "running", "success", "failed", "cancelled")
LOCK_SCOPES_V9 = ("home", "project")
EVENT_SEVERITIES_V9 = ("debug", "info", "warning", "error", "critical")
IMPORT_RUN_STATUSES_V10 = ("started", "success", "failed")
AUDIT_DECISION_DECISIONS_V10 = ("keep", "remove", "merge", "deprecate")
AUDIT_DECISION_FAIL_SAFE_ACTIONS_V10 = ("skip", "quarantine", "manual_review")


SCRUM_TRIGGER_SCHEMA_V12 = """
CREATE TABLE IF NOT EXISTS scrum_trigger (
  trigger_id TEXT PRIMARY KEY,
  scrum_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  artifact_ref TEXT,
  event_type TEXT NOT NULL,
  plan_id TEXT,
  sprint_id TEXT,
  detected_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  ttl_at TEXT,
  resolved_at TEXT,
  uncertainty_score INTEGER,
  impact_score INTEGER,
  confidence REAL,
  evidence_count INTEGER DEFAULT 1,
  normalized_signature TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  status_owner TEXT,
  status_reason TEXT,
  reason_code TEXT,
  evidence_path_hint TEXT,
  source_path TEXT,
  source_line_start INTEGER,
  source_line_end INTEGER,
  created_by TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(scrum_type, source_id, normalized_signature)
);

CREATE INDEX IF NOT EXISTS idx_scrum_trigger_status ON scrum_trigger(status, detected_at);
CREATE INDEX IF NOT EXISTS idx_scrum_trigger_type ON scrum_trigger(scrum_type, status);
"""


VERIFY_RUNS_SCHEMA_V13 = """
CREATE TABLE IF NOT EXISTS verify_runs (
  run_id TEXT PRIMARY KEY,
  subcommand TEXT NOT NULL,
  plan_id TEXT,
  spec_plan_id TEXT,
  contract_path TEXT,
  inputs_hash TEXT NOT NULL,
  candidates_count INTEGER,
  drifts_count INTEGER,
  drift_severity_summary TEXT,
  has_fail_close BOOLEAN DEFAULT 0,
  output_summary TEXT,
  llm_suggest_used BOOLEAN DEFAULT 0,
  fallback_used BOOLEAN DEFAULT 0,
  created_at TEXT NOT NULL,
  created_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_verify_runs_subcommand ON verify_runs(subcommand, created_at);
CREATE INDEX IF NOT EXISTS idx_verify_runs_fail_close ON verify_runs(has_fail_close, created_at);
"""


CODE_INDEX_SCHEMA_V15 = """
CREATE TABLE IF NOT EXISTS code_index (
  id TEXT PRIMARY KEY,
  domain TEXT NOT NULL,
  summary TEXT NOT NULL,
  path TEXT NOT NULL,
  line_no INTEGER NOT NULL,
  symbol_line INTEGER NOT NULL DEFAULT 0,
  since TEXT,
  related TEXT,
  source_hash TEXT,
  bucket TEXT NOT NULL DEFAULT 'coverage_eligible',
  updated_at DATETIME
);

CREATE INDEX IF NOT EXISTS idx_code_index_domain ON code_index(domain);
CREATE INDEX IF NOT EXISTS idx_code_index_summary ON code_index(summary);
CREATE INDEX IF NOT EXISTS idx_code_index_path ON code_index(path);
CREATE INDEX IF NOT EXISTS idx_code_index_bucket ON code_index(bucket);
"""


ENTRIES_LINKS_SCHEMA_V17 = """
CREATE TABLE IF NOT EXISTS entries (
    id              TEXT PRIMARY KEY,
    axis            TEXT NOT NULL
                    CHECK(axis IN ('design','plan','code','schema','test','review','evidence')),
    stack           TEXT
                    CHECK(stack IS NULL OR stack IN ('front','back','contract','fullstack','infra','n/a')),
    lifecycle       TEXT NOT NULL
                    CHECK(lifecycle IN ('initial','addition','modification','migration','deprecation','removed')),
    parent_entry_id TEXT,
    sprint_id       TEXT,
    agent_actor     TEXT,
    ref             TEXT NOT NULL,
    version         TEXT,
    metadata        TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_entry_id) REFERENCES entries(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS links (
    from_id  TEXT NOT NULL,
    to_id    TEXT NOT NULL,
    kind     TEXT NOT NULL
             CHECK(kind IN ('uses','covers','reviews','implements','derives_from','supersedes')),
    metadata TEXT,
    PRIMARY KEY (from_id, to_id, kind),
    FOREIGN KEY (from_id) REFERENCES entries(id) ON DELETE CASCADE,
    FOREIGN KEY (to_id)   REFERENCES entries(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_entries_axis      ON entries(axis);
CREATE INDEX IF NOT EXISTS idx_entries_stack     ON entries(stack)       WHERE stack IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_entries_sprint    ON entries(sprint_id)   WHERE sprint_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_entries_agent     ON entries(agent_actor) WHERE agent_actor IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_entries_lifecycle ON entries(lifecycle);
CREATE INDEX IF NOT EXISTS idx_links_kind        ON links(kind);
"""


CONTRACT_REGISTRY_SCHEMA_V17 = """
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
        CHECK (design_level IN ('planning','requirement','architecture','detailed','functional'))
);
CREATE TABLE IF NOT EXISTS code_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_entry_id INTEGER NOT NULL,
    to_entry_id INTEGER,
    to_external_ref TEXT,
    edge_type TEXT NOT NULL,
    weight INTEGER DEFAULT 1,
    source_line INTEGER,
    raw_meta TEXT
);
CREATE INDEX IF NOT EXISTS idx_contract_type ON contract_entries(contract_type);
CREATE INDEX IF NOT EXISTS idx_contract_breaking ON contract_entries(breaking_change_flag);
CREATE INDEX IF NOT EXISTS idx_contract_design_level ON contract_entries(design_level);
CREATE INDEX IF NOT EXISTS idx_edges_from ON code_edges(from_entry_id, edge_type);
CREATE INDEX IF NOT EXISTS idx_edges_to ON code_edges(to_entry_id, edge_type);
"""


TEST_BASELINE_SCHEMA_V20 = """
CREATE TABLE IF NOT EXISTS test_baseline (
    id INTEGER PRIMARY KEY,
    commit_sha TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    suite TEXT NOT NULL,
    test_name TEXT NOT NULL,
    status TEXT NOT NULL,
    duration_ms INTEGER,
    skip_reason TEXT,
    code_entry_id INTEGER,
    test_design_id INTEGER,
    UNIQUE (commit_sha, suite, test_name)
);
CREATE INDEX IF NOT EXISTS idx_baseline_suite_name ON test_baseline(suite, test_name);
CREATE INDEX IF NOT EXISTS idx_baseline_commit ON test_baseline(commit_sha);
CREATE INDEX IF NOT EXISTS idx_baseline_code_entry ON test_baseline(code_entry_id);
CREATE INDEX IF NOT EXISTS idx_baseline_test_design ON test_baseline(test_design_id);
"""


TEST_DESIGN_ENTRIES_SCHEMA_V20 = """
CREATE TABLE IF NOT EXISTS test_design_entries (
    id INTEGER PRIMARY KEY,
    plan_id TEXT NOT NULL,
    acceptance_key TEXT NOT NULL,
    contract_id INTEGER,
    test_level TEXT NOT NULL CHECK (test_level IN
        ('operational','acceptance','system_integration','integration','unit')),
    paired_design_level TEXT NOT NULL CHECK (paired_design_level IN
        ('planning','requirement','architecture','detailed','functional')),
    pyramid_layer TEXT NOT NULL,
    test_target TEXT,
    expected_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (plan_id, acceptance_key, test_level)
);
CREATE INDEX IF NOT EXISTS idx_test_design_plan ON test_design_entries(plan_id);
CREATE INDEX IF NOT EXISTS idx_test_design_contract ON test_design_entries(contract_id);
CREATE INDEX IF NOT EXISTS idx_test_design_levels ON test_design_entries(test_level, paired_design_level);
"""


DESIGN_REVIEW_SCHEMA_V20 = """
CREATE TABLE IF NOT EXISTS design_review (
    id INTEGER PRIMARY KEY,
    plan_id TEXT NOT NULL,
    layer TEXT NOT NULL,
    review_axis TEXT NOT NULL,
    source_layer TEXT,
    target_id INTEGER,
    reviewed_at TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    verdict TEXT NOT NULL,
    raw_findings TEXT
);
CREATE INDEX IF NOT EXISTS idx_design_review_plan ON design_review(plan_id, layer, review_axis);
"""


DESIGN_SPRINT_ENTRIES_SCHEMA_V21 = """
CREATE TABLE IF NOT EXISTS design_sprint_entries (
    id INTEGER PRIMARY KEY,
    plan_id TEXT NOT NULL,
    sprint_id TEXT,
    sprint_type TEXT NOT NULL CHECK (sprint_type IN ('architecture','detailed','functional','impl')),
    layer TEXT NOT NULL CHECK (layer IN ('architecture','detailed','functional')),
    drive TEXT NOT NULL CHECK (drive IN ('be','fe','db','fullstack')),
    track TEXT CHECK (track IN ('be','fe','db','contract','shared')),
    pair_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (pair_status IN ('pending','design_only','test_only','paired','waived','failed')),
    freeze_gate TEXT,
    subgate TEXT,
    frozen_at TEXT,
    raw_meta TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (
        (sprint_type = 'architecture' AND layer = 'architecture') OR
        (sprint_type = 'detailed' AND layer = 'detailed') OR
        (sprint_type = 'functional' AND layer = 'functional') OR
        (sprint_type = 'impl' AND layer = 'functional')
    )
);
CREATE INDEX IF NOT EXISTS idx_design_sprint_plan_drive_layer
    ON design_sprint_entries(plan_id, drive, layer, sprint_type, pair_status);
"""


DESIGN_SPRINT_SWITCH_STATUSES = ("preserved", "waived", "failed")
DESIGN_SPRINT_TYPES = ("architecture", "detailed", "functional", "impl")
DESIGN_SPRINT_LAYERS = ("architecture", "detailed", "functional")
DESIGN_SPRINT_DRIVES = ("be", "fe", "db", "fullstack")
DESIGN_SPRINT_TRACKS = ("be", "fe", "db", "contract", "shared")
DESIGN_SPRINT_PAIR_STATUSES = ("pending", "design_only", "test_only", "paired", "waived", "failed")
DESIGN_SPRINT_ARTIFACT_KINDS = ("design", "test_design", "review", "baseline")
DESIGN_SPRINT_ARTIFACT_LINK_KINDS = ("covers", "derives_from", "reviews", "implements")


VIEW_VMODEL_INTEGRITY_V21 = """
CREATE VIEW IF NOT EXISTS view_vmodel_integrity AS
SELECT
    c.id AS contract_id,
    c.introduced_plan AS plan_id,
    c.drive AS drive,
    c.design_level AS design_level,
    c.origin_mode AS origin_mode,
    c.evidence_status AS evidence_status,
    ci.id AS code_index_id,
    td.id AS test_design_id,
    td.test_level AS test_level,
    tb.id AS baseline_id,
    tb.status AS baseline_status,
    CASE WHEN td.id IS NULL THEN 1 ELSE 0 END AS missing_test_design,
    CASE WHEN tb.id IS NULL THEN 1 ELSE 0 END AS missing_baseline,
    CASE WHEN tb.status IS NOT NULL AND tb.status NOT IN ('passed','pass','ok') THEN 1 ELSE 0 END AS failing_baseline,
    SUM(CASE WHEN td.id IS NULL THEN 1 ELSE 0 END) OVER (PARTITION BY c.introduced_plan) AS missing_test_design_count,
    SUM(CASE WHEN tb.id IS NULL THEN 1 ELSE 0 END) OVER (PARTITION BY c.introduced_plan) AS missing_baseline_count,
    SUM(CASE WHEN tb.status IS NOT NULL AND tb.status NOT IN ('passed','pass','ok') THEN 1 ELSE 0 END)
        OVER (PARTITION BY c.introduced_plan) AS failing_baseline_count,
    COUNT(*) OVER (PARTITION BY c.introduced_plan) AS plan_contract_count
FROM contract_entries c
LEFT JOIN code_edges ce
    ON ce.from_entry_id = c.id
   AND ce.edge_type IN ('implements','derives_from','covers','reviews')
LEFT JOIN code_index ci
    ON ci.id = CAST(ce.to_entry_id AS TEXT)
LEFT JOIN test_design_entries td
    ON td.contract_id = c.id
   AND td.plan_id = c.introduced_plan
LEFT JOIN test_baseline tb
    ON tb.test_design_id = td.id;
"""


DESIGN_SPRINT_ARTIFACT_LINKS_SCHEMA_V21 = """
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
"""


DESIGN_SPRINT_DRIVE_DECISIONS_SCHEMA_V24 = """
CREATE TABLE IF NOT EXISTS design_sprint_drive_decisions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    source_entry_id     INTEGER NOT NULL,
    target_entry_id     INTEGER NOT NULL,
    decision            TEXT NOT NULL CHECK(decision IN ('preserved','waived','failed')),
    decided_by          TEXT NOT NULL,
    reason              TEXT NOT NULL,
    reopen_condition    TEXT,
    lifecycle_status    TEXT NOT NULL DEFAULT 'observed'
        CHECK(lifecycle_status IN ('observed','inferred','confirmed')),
    direction           TEXT NOT NULL DEFAULT 'forward'
        CHECK(direction IN ('forward','reverse','forward_after_reverse')),
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (source_entry_id) REFERENCES design_sprint_entries(id),
    FOREIGN KEY (target_entry_id) REFERENCES design_sprint_entries(id)
);

CREATE INDEX IF NOT EXISTS idx_dsdd_source ON design_sprint_drive_decisions(source_entry_id);
CREATE INDEX IF NOT EXISTS idx_dsdd_target ON design_sprint_drive_decisions(target_entry_id);
CREATE INDEX IF NOT EXISTS idx_dsdd_decision ON design_sprint_drive_decisions(decision);
"""


AUTOMATION_RUNS_SCHEMA_V25 = """
CREATE TABLE IF NOT EXISTS automation_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_kind        TEXT NOT NULL,
    plan_id         TEXT,
    trigger_actor   TEXT NOT NULL,
    started_at      TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at        TEXT,
    status          TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','running','completed','failed','cancelled')),
    exit_code       INTEGER,
    summary         TEXT,
    retry_count     INTEGER NOT NULL DEFAULT 0,
    max_retries     INTEGER NOT NULL DEFAULT 0,
    last_error      TEXT
);

CREATE INDEX IF NOT EXISTS idx_automation_runs_kind ON automation_runs(run_kind);
CREATE INDEX IF NOT EXISTS idx_automation_runs_status ON automation_runs(status);
CREATE INDEX IF NOT EXISTS idx_automation_runs_started_at ON automation_runs(started_at);
"""


AUDIT_LOG_SCHEMA_V26 = """
CREATE TABLE IF NOT EXISTS audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_kind      TEXT NOT NULL,
    actor           TEXT NOT NULL,
    run_id          INTEGER,
    payload         TEXT NOT NULL,
    recorded_at     TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (run_id) REFERENCES automation_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_audit_log_kind ON audit_log(audit_kind);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor ON audit_log(actor);
CREATE INDEX IF NOT EXISTS idx_audit_log_run_id ON audit_log(run_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_recorded_at ON audit_log(recorded_at);
"""


SESSION_TELEMETRY_SCHEMA_V27 = """
CREATE TABLE IF NOT EXISTS session_telemetry (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id          TEXT NOT NULL UNIQUE,
    started_at          TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at            TEXT,
    actor               TEXT NOT NULL,
    related_plan_id     TEXT,
    tool_uses_count     INTEGER NOT NULL DEFAULT 0,
    tokens_total        INTEGER NOT NULL DEFAULT 0,
    cost_usd            REAL NOT NULL DEFAULT 0.0,
    last_updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_session_telemetry_actor ON session_telemetry(actor);
CREATE INDEX IF NOT EXISTS idx_session_telemetry_started_at ON session_telemetry(started_at);
CREATE INDEX IF NOT EXISTS idx_session_telemetry_related_plan ON session_telemetry(related_plan_id);
"""


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

CREATE INDEX IF NOT EXISTS idx_agent_slots_status ON agent_slots(status);
CREATE INDEX IF NOT EXISTS idx_agent_slots_plan ON agent_slots(plan_id);
CREATE INDEX IF NOT EXISTS idx_agent_slots_fired_at ON agent_slots(fired_at);
CREATE INDEX IF NOT EXISTS idx_agent_slots_kind ON agent_slots(agent_kind);

CREATE TRIGGER IF NOT EXISTS agent_slots_no_delete
BEFORE DELETE ON agent_slots
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'agent_slots is append-only (no delete allowed)');
END;
"""


SCRUM_LOCAL_LOOPS_SCHEMA_V29 = """
CREATE TABLE IF NOT EXISTS scrum_local_loops (
    loop_id              TEXT PRIMARY KEY,
    forward_layer        TEXT NOT NULL,
    forward_plan_id      TEXT,
    hypothesis           TEXT NOT NULL,
    acceptance           TEXT NOT NULL,
    state                TEXT NOT NULL DEFAULT 'S0'
                        CHECK(state IN ('S0', 'S1', 'S2', 'S3')),
    decide_result        TEXT
                        CHECK(decide_result IS NULL OR decide_result IN ('confirmed', 'rejected', 'pivot')),
    started_at           TEXT NOT NULL DEFAULT (datetime('now')),
    decided_at           TEXT,
    parent_loop_id       TEXT,
    related_agent_slot_id INTEGER,
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (parent_loop_id) REFERENCES scrum_local_loops(loop_id),
    FOREIGN KEY (related_agent_slot_id) REFERENCES agent_slots(id)
);

CREATE INDEX IF NOT EXISTS idx_scrum_local_state ON scrum_local_loops(state);
CREATE INDEX IF NOT EXISTS idx_scrum_local_layer ON scrum_local_loops(forward_layer);
CREATE INDEX IF NOT EXISTS idx_scrum_local_plan ON scrum_local_loops(forward_plan_id);

CREATE TRIGGER IF NOT EXISTS scrum_local_loops_no_delete
BEFORE DELETE ON scrum_local_loops
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'scrum_local_loops is append-only');
END;
"""


REVERSE_LOCAL_LOOPS_SCHEMA_V29 = """
CREATE TABLE IF NOT EXISTS reverse_local_loops (
    loop_id              TEXT PRIMARY KEY,
    parent_scrum_loop_id TEXT NOT NULL,
    reverse_type         TEXT NOT NULL DEFAULT 'scrum-to-forward'
                        CHECK(reverse_type IN ('scrum-to-forward')),
    state                TEXT NOT NULL DEFAULT 'R0'
                        CHECK(state IN ('R0', 'R1', 'R2', 'R3', 'R4')),
    target_forward_plan  TEXT,
    target_forward_layer TEXT,
    started_at           TEXT NOT NULL DEFAULT (datetime('now')),
    routed_at            TEXT,
    artifact_links       TEXT,
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (parent_scrum_loop_id) REFERENCES scrum_local_loops(loop_id)
);

CREATE INDEX IF NOT EXISTS idx_reverse_local_state ON reverse_local_loops(state);
CREATE INDEX IF NOT EXISTS idx_reverse_local_parent ON reverse_local_loops(parent_scrum_loop_id);
CREATE INDEX IF NOT EXISTS idx_reverse_local_plan ON reverse_local_loops(target_forward_plan);

CREATE TRIGGER IF NOT EXISTS reverse_local_loops_no_delete
BEFORE DELETE ON reverse_local_loops
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'reverse_local_loops is append-only');
END;
"""


HARNESS_CHECK_EVENTS_SCHEMA_V30 = """
CREATE TABLE IF NOT EXISTS harness_check_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_kind      TEXT NOT NULL
                    CHECK(event_kind IN ('pull', 'push', 'audit')),
    check_name      TEXT NOT NULL,
    triggered_at    TEXT NOT NULL DEFAULT (datetime('now')),
    session_id      TEXT,
    related_slot_id INTEGER,
    plan_id         TEXT,
    severity        TEXT NOT NULL DEFAULT 'info'
                    CHECK(severity IN ('info', 'warning', 'critical')),
    payload         TEXT,
    user_visible    INTEGER NOT NULL DEFAULT 0
                    CHECK(user_visible IN (0, 1)),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (related_slot_id) REFERENCES agent_slots(id)
);

CREATE INDEX IF NOT EXISTS idx_harness_check_kind ON harness_check_events(event_kind);
CREATE INDEX IF NOT EXISTS idx_harness_check_session ON harness_check_events(session_id);
CREATE INDEX IF NOT EXISTS idx_harness_check_at ON harness_check_events(triggered_at);
CREATE INDEX IF NOT EXISTS idx_harness_check_severity ON harness_check_events(severity);

CREATE TRIGGER IF NOT EXISTS harness_check_events_no_delete
BEFORE DELETE ON harness_check_events
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'harness_check_events is append-only');
END;
"""


INVOCATION_LOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS invocation_log (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    type TEXT NOT NULL,
    role TEXT,
    model TEXT,
    task_id TEXT,
    plan_id TEXT,
    sprint TEXT,
    input_bytes INTEGER,
    output_bytes INTEGER,
    duration_ms INTEGER,
    decision TEXT,
    cost_cents REAL,
    parent_invocation_id INTEGER,
    raw_meta TEXT
);
CREATE INDEX IF NOT EXISTS idx_invocation_plan ON invocation_log(plan_id, task_id);
CREATE INDEX IF NOT EXISTS idx_invocation_timestamp ON invocation_log(timestamp);
"""


INVOCATION_META_ALLOWLIST = (
    "role",
    "model",
    "task_id",
    "plan_id",
    "sprint",
    "decision",
    "cost_cents",
    "duration_ms",
)
INVOCATION_REDACTION_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"Bearer\s+\S+"),
    re.compile(r"token=\S+"),
)


def _prepare_db_path(db_path):
    parent_dir = os.path.dirname(os.path.abspath(db_path))
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)


# @helix:index id=helix-db.get-connection domain=cli/lib summary=connectionを取得する
def get_connection(db_path: str | Path | None = None, timeout: float = DEFAULT_SQLITE_TIMEOUT_SEC) -> sqlite3.Connection:
    """HELIX 統一 SQLite 接続。WAL + timeout + row_factory 設定済み。"""
    target_path = resolve_default_db_path() if db_path is None else str(db_path)
    conn = sqlite3.connect(target_path, timeout=timeout)
    conn.execute(f"PRAGMA journal_mode={PRAGMA_JOURNAL_MODE}")
    conn.execute(f"PRAGMA busy_timeout={int(timeout * 1000)}")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def _connect(db_path):
    return get_connection(db_path=db_path, timeout=DEFAULT_SQLITE_TIMEOUT_SEC)


def _resolve_db_path(db_path: str | Path | None) -> str:
    return resolve_default_db_path() if db_path is None else str(db_path)


@contextmanager
def _write_connection(db_path: str | Path | None, ensure_schema: bool = True):
    target_path = _resolve_db_path(db_path)
    _prepare_db_path(target_path)
    with file_lock(HELIX_DB_LOCK_NAME):
        conn = _connect(target_path)
        try:
            if ensure_schema:
                _ensure_schema(conn)
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def _create_requirements_tables(conn):
    conn.executescript(REQUIREMENTS_SCHEMA)


def _create_accuracy_score_table(conn):
    conn.executescript(ACCURACY_SCORE_SCHEMA)


def _create_infra_tables_v9(conn):
    conn.executescript(INFRA_SCHEMA_V9)


def _ensure_invocation_log_table(conn):
    conn.executescript(INVOCATION_LOG_SCHEMA)


def _redact_meta_value(value):
    if isinstance(value, str):
        redacted = value
        for pattern in INVOCATION_REDACTION_PATTERNS:
            redacted = pattern.sub("[REDACTED]", redacted)
        return redacted
    if isinstance(value, list):
        return [_redact_meta_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _redact_meta_value(item) for key, item in value.items()}
    return value


def _redact_meta(meta):
    if not isinstance(meta, dict):
        return {}

    redacted = {}
    for key in INVOCATION_META_ALLOWLIST:
        if key not in meta:
            continue
        value = meta[key]
        if value is None:
            continue
        redacted[key] = _redact_meta_value(value)
    return redacted


def _ensure_setup_tables(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS setup_checks (
            component TEXT PRIMARY KEY,
            verify_state TEXT NOT NULL CHECK(verify_state IN ('pending', 'running', 'success', 'failed', 'cancelled')),
            installed INTEGER NOT NULL DEFAULT 0,
            last_verify_at INTEGER,
            last_install_at INTEGER,
            last_repair_at INTEGER,
            verify_error TEXT,
            install_version TEXT,
            install_path TEXT,
            updated_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS setup_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            component TEXT NOT NULL,
            action TEXT NOT NULL CHECK(action IN ('verify','install','repair')),
            status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'success', 'failed', 'cancelled')),
            outcome TEXT,
            details_json TEXT,
            created_at INTEGER NOT NULL,
            FOREIGN KEY(component) REFERENCES setup_checks(component) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_setup_events_component_created
            ON setup_events(component, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_setup_events_status ON setup_events(status);
        """
    )


def _create_audit_decisions_v10(conn):
    conn.executescript(AUDIT_DECISIONS_SCHEMA_V10)


def _migrate_v10_to_v11(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS deferred_findings (
            id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL,
            origin_plan_id TEXT NOT NULL,
            origin_phase TEXT NOT NULL,
            current_plan_id TEXT NOT NULL,
            current_phase TEXT NOT NULL,
            target_plan_id TEXT,
            target_phase TEXT,
            level TEXT NOT NULL CHECK (level IN ('P0','P1','P2','P3')),
            carry_rule TEXT NOT NULL CHECK (carry_rule IN ('stop','carry-with-pm-approval','auto-carry','optional')),
            phase TEXT NOT NULL,
            source TEXT NOT NULL,
            severity TEXT NOT NULL CHECK (severity IN ('critical','high','medium','low')),
            status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','carried','resolved','abandoned')),
            weight REAL NOT NULL DEFAULT 0.0,
            created_at TEXT NOT NULL,
            resolved_at TEXT,
            pm_approved_by TEXT,
            pm_approved_at TEXT,
            pm_reason TEXT,
            yaml_synced_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_deferred_findings_plan ON deferred_findings(plan_id);
        CREATE INDEX IF NOT EXISTS idx_deferred_findings_status ON deferred_findings(status);
        CREATE INDEX IF NOT EXISTS idx_deferred_findings_level ON deferred_findings(level);
        CREATE INDEX IF NOT EXISTS idx_deferred_findings_phase ON deferred_findings(phase);

        CREATE TABLE IF NOT EXISTS accuracy_score_adjustments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            finding_id TEXT NOT NULL REFERENCES deferred_findings(id) ON DELETE CASCADE,
            plan_id TEXT NOT NULL,
            gate TEXT NOT NULL,
            dimension TEXT NOT NULL CHECK (dimension IN ('density','depth','breadth','accuracy','maintainability')),
            penalty REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_adjustments_finding ON accuracy_score_adjustments(finding_id);
        CREATE INDEX IF NOT EXISTS idx_adjustments_plan_gate ON accuracy_score_adjustments(plan_id, gate);

        DROP VIEW IF EXISTS accuracy_score_effective;
        CREATE VIEW IF NOT EXISTS accuracy_score_effective AS
        SELECT
            a.id AS accuracy_score_id,
            a.plan_id,
            a.gate,
            a.dimension,
            a.level AS raw_level,
            CAST(a.level AS REAL) AS raw_score,
            COALESCE(SUM(adj.penalty), 0.0) AS total_penalty,
            MAX(0.0, CAST(a.level AS REAL) - COALESCE(SUM(adj.penalty), 0.0)) AS effective_score,
            a.recorded_at AS evaluated_at
        FROM accuracy_score a
        LEFT JOIN accuracy_score_adjustments adj
            ON adj.plan_id = a.plan_id
            AND adj.gate = a.gate
            AND adj.dimension = a.dimension
        GROUP BY a.id;
        """
    )


def _migrate_v11_to_v12(conn):
    conn.executescript(SCRUM_TRIGGER_SCHEMA_V12)


def _migrate_v12_to_v13(conn):
    conn.executescript(VERIFY_RUNS_SCHEMA_V13)


def _migrate_v13_to_v14(conn):
    conn.executescript(CODE_INDEX_SCHEMA_V15)


def _migrate_v14_to_v15(conn):
    table_exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'code_index'"
    ).fetchone()
    if table_exists is None:
        conn.executescript(CODE_INDEX_SCHEMA_V15)
        return
    if not _has_column(conn, "code_index", "symbol_line"):
        conn.execute("ALTER TABLE code_index ADD COLUMN symbol_line INTEGER NOT NULL DEFAULT 0")
    if not _has_column(conn, "code_index", "bucket"):
        conn.execute("ALTER TABLE code_index ADD COLUMN bucket TEXT NOT NULL DEFAULT 'coverage_eligible'")
    conn.execute(
        """
        UPDATE code_index
        SET symbol_line = line_no
        WHERE symbol_line IS NULL OR symbol_line = 0
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_code_index_bucket ON code_index(bucket)")


def _migrate_v15_to_v16(conn):
    """v16: sessions テーブル新設 + skill_usage.session_id 追加 (PLAN-023 W-2a)"""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            cwd TEXT,
            claude_session_id TEXT,
            metadata TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions(started_at);
        """
    )
    _ensure_skill_usage_table(conn)
    if not _has_column(conn, "skill_usage", "session_id"):
        conn.execute("ALTER TABLE skill_usage ADD COLUMN session_id TEXT")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_skill_usage_session ON skill_usage(session_id) "
        "WHERE session_id IS NOT NULL"
    )
    _ensure_invocation_log_table(conn)


def _migrate_v16_to_v17(conn):
    """v17: entries/links + contract registry tables を追加する。"""
    conn.executescript(ENTRIES_LINKS_SCHEMA_V17)
    conn.executescript(CONTRACT_REGISTRY_SCHEMA_V17)


def _migrate_v17_to_v18(conn):
    """v18: code_index に 6 列追加 (PLAN-027 Sprint .3 W-3c) — entries 軸との対応"""
    for column, sql_type in [
        ("axis", "TEXT"),
        ("stack", "TEXT"),
        ("lifecycle", "TEXT"),
        ("parent_entry_id", "TEXT"),
        ("sprint_id", "TEXT"),
        ("agent_actor", "TEXT"),
    ]:
        if not _has_column(conn, "code_index", column):
            conn.execute(f"ALTER TABLE code_index ADD COLUMN {column} {sql_type}")


def _migrate_v18_to_v19(conn):
    """v19: entries に 3 列追加 + sprint_metrics / phase_gate_runs を追加する。"""
    for column, sql_type in [
        ("qa_result", "TEXT"),
        ("security_audit", "TEXT"),
        ("design_decision", "TEXT"),
    ]:
        if not _has_column(conn, "entries", column):
            conn.execute(f"ALTER TABLE entries ADD COLUMN {column} {sql_type}")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sprint_metrics (
            sprint_id TEXT PRIMARY KEY,
            test_pass_rate REAL,
            drift_count INTEGER,
            duration_minutes INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS phase_gate_runs (
            gate_id TEXT,
            phase TEXT,
            result TEXT CHECK(result IN ('passed','failed','blocked','interrupted')),
            ran_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (gate_id, ran_at)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_sprint_metrics_sprint ON sprint_metrics(sprint_id)"
    )


def _migrate_v19_to_v20(conn):
    """v20: QA baseline/V-model 用テーブル追加 + contract_entries.design_level 追加。"""
    if not _has_table(conn, "test_baseline"):
        conn.executescript(TEST_BASELINE_SCHEMA_V20)
    else:
        if not _has_column(conn, "test_baseline", "code_entry_id"):
            conn.execute("ALTER TABLE test_baseline ADD COLUMN code_entry_id INTEGER")
        if not _has_column(conn, "test_baseline", "test_design_id"):
            conn.execute("ALTER TABLE test_baseline ADD COLUMN test_design_id INTEGER")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_baseline_suite_name ON test_baseline(suite, test_name)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_baseline_commit ON test_baseline(commit_sha)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_baseline_code_entry ON test_baseline(code_entry_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_baseline_test_design ON test_baseline(test_design_id)"
        )

    if not _has_table(conn, "test_design_entries"):
        conn.executescript(TEST_DESIGN_ENTRIES_SCHEMA_V20)
    else:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_test_design_plan ON test_design_entries(plan_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_test_design_contract ON test_design_entries(contract_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_test_design_levels ON test_design_entries(test_level, paired_design_level)"
        )

    if not _has_table(conn, "design_review"):
        conn.executescript(DESIGN_REVIEW_SCHEMA_V20)
    else:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_design_review_plan ON design_review(plan_id, layer, review_axis)"
        )

    if not _has_table(conn, "contract_entries"):
        conn.executescript(CONTRACT_REGISTRY_SCHEMA_V17)
        return

    if not _has_column(conn, "contract_entries", "design_level"):
        conn.execute(
            "ALTER TABLE contract_entries ADD COLUMN design_level TEXT NOT NULL DEFAULT 'detailed'"
        )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_contract_design_level ON contract_entries(design_level)")


def _migrate_v20_to_v21(conn):
    """v21: contract_entries semantic columns + design_sprint_* tables (additive/idempotent)."""
    if not _has_table(conn, "contract_entries"):
        conn.executescript(CONTRACT_REGISTRY_SCHEMA_V17)

    # SQLite version compatibility: CHECK on ADD COLUMN can vary across runtimes,
    # so we use additive NOT NULL DEFAULT and rely on app-level semantic validation.
    if not _has_column(conn, "contract_entries", "drive"):
        conn.execute("ALTER TABLE contract_entries ADD COLUMN drive TEXT NOT NULL DEFAULT 'be'")
    if not _has_column(conn, "contract_entries", "origin_mode"):
        conn.execute("ALTER TABLE contract_entries ADD COLUMN origin_mode TEXT NOT NULL DEFAULT 'forward'")
    if not _has_column(conn, "contract_entries", "evidence_status"):
        conn.execute(
            "ALTER TABLE contract_entries ADD COLUMN evidence_status TEXT NOT NULL DEFAULT 'confirmed'"
        )

    if not _has_table(conn, "design_sprint_entries"):
        conn.executescript(DESIGN_SPRINT_ENTRIES_SCHEMA_V21)
    else:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_design_sprint_plan_drive_layer "
            "ON design_sprint_entries(plan_id, drive, layer, sprint_type, pair_status)"
        )

    if not _has_table(conn, "design_sprint_artifact_links"):
        conn.executescript(DESIGN_SPRINT_ARTIFACT_LINKS_SCHEMA_V21)
    conn.executescript(VIEW_VMODEL_INTEGRITY_V21)


def _migrate_v21_to_v22(conn):
    """v22: design_sprint_entries に drive switch 履歴列を追加する。"""
    if not _has_table(conn, "design_sprint_entries"):
        conn.executescript(DESIGN_SPRINT_ENTRIES_SCHEMA_V21)

    if not _has_column(conn, "design_sprint_entries", "previous_drive"):
        conn.execute("ALTER TABLE design_sprint_entries ADD COLUMN previous_drive TEXT")
    if not _has_column(conn, "design_sprint_entries", "drive_switch_reason"):
        conn.execute("ALTER TABLE design_sprint_entries ADD COLUMN drive_switch_reason TEXT")
    if not _has_column(conn, "design_sprint_entries", "status_on_switch"):
        conn.execute(
            "ALTER TABLE design_sprint_entries "
            "ADD COLUMN status_on_switch TEXT "
            "CHECK (status_on_switch IN ('preserved','waived','failed') OR status_on_switch IS NULL)"
        )


def _migrate_v22_to_v23(conn):
    """v23: append-only 訂正イベント列を追加する。"""
    if not _has_table(conn, "design_sprint_entries"):
        conn.executescript(DESIGN_SPRINT_ENTRIES_SCHEMA_V21)
        _migrate_v21_to_v22(conn)
    if not _has_table(conn, "design_sprint_artifact_links"):
        conn.executescript(DESIGN_SPRINT_ARTIFACT_LINKS_SCHEMA_V21)

    for table_name in ("design_sprint_entries", "design_sprint_artifact_links"):
        if not _has_column(conn, table_name, "supersedes_entry_id"):
            conn.execute(
                f"ALTER TABLE {table_name} "
                "ADD COLUMN supersedes_entry_id INTEGER REFERENCES design_sprint_entries(id)"
            )
        if not _has_column(conn, table_name, "correction_reason"):
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN correction_reason TEXT")
        if not _has_column(conn, table_name, "voided_at"):
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN voided_at TEXT")


# @helix:index id=helix-db.migrate-v23-to-v24 domain=cli/lib summary=v24 design_sprint_drive_decisions migration (drive switch policy + L1 P2-7 lifecycle + AC-17 direction)
def _migrate_v23_to_v24(conn: sqlite3.Connection) -> None:
    """v24: design_sprint_drive_decisions テーブル追加 (P0-03 hybrid + drive switch policy)"""
    if not _has_table(conn, "design_sprint_drive_decisions"):
        conn.executescript(DESIGN_SPRINT_DRIVE_DECISIONS_SCHEMA_V24)


# @helix:index id=helix-db.migrate-v24-to-v25 domain=cli/lib summary=v25 automation_runs migration (P0-03 hybrid + lifecycle helper + 限定 trigger)
def _migrate_v24_to_v25(conn: sqlite3.Connection) -> None:
    """v25: automation_runs テーブル + append-only 限定 trigger (P0-03 hybrid)"""
    if not _has_table(conn, "automation_runs"):
        conn.executescript(AUTOMATION_RUNS_SCHEMA_V25)
    _create_append_only_trigger(
        conn,
        "automation_runs",
        immutable_columns=["id", "run_kind", "started_at"],
        terminal_status_column="status",
        terminal_values=["completed", "failed", "cancelled"],
    )


# @helix:index id=helix-db.migrate-v25-to-v26 domain=cli/lib summary=v26 audit_log migration (P0-03 hybrid 方式 B + payload immutable + no_delete)
def _migrate_v25_to_v26(conn: sqlite3.Connection) -> None:
    """v26: audit_log + 物理改ざん拒否 trigger (P0-03 hybrid 方式 B)"""
    if not _has_table(conn, "audit_log"):
        conn.executescript(AUDIT_LOG_SCHEMA_V26)
    _create_append_only_trigger(
        conn,
        "audit_log",
        immutable_columns=["payload"],
    )


# @helix:index id=helix-db.migrate-v26-to-v27 domain=cli/lib summary=v27 session_telemetry migration (session_id UNIQUE + UPSERT 対応)
def _migrate_v26_to_v27(conn: sqlite3.Connection) -> None:
    """v27: session_telemetry テーブル (session_id UNIQUE, UPSERT 対応)"""
    if not _has_table(conn, "session_telemetry"):
        conn.executescript(SESSION_TELEMETRY_SCHEMA_V27)


# @helix:index id=helix-db.migrate-v27-to-v28 domain=cli/lib summary=v28 agent_slots migration (invocation 単位 slot 管理)
def _migrate_v27_to_v28(conn: sqlite3.Connection) -> None:
    """v28: agent_slots テーブル追加。"""
    if not _has_table(conn, "agent_slots"):
        conn.executescript(AGENT_SLOTS_SCHEMA_V28)


# @helix:index id=helix-db.migrate-v28-to-v29 domain=cli/lib summary=v29 scrum_local + reverse_local migration
def _migrate_v28_to_v29(conn: sqlite3.Connection) -> None:
    """v29: scrum_local_loops / reverse_local_loops テーブル追加。"""
    if not _has_table(conn, "scrum_local_loops"):
        conn.executescript(SCRUM_LOCAL_LOOPS_SCHEMA_V29)
    if not _has_table(conn, "reverse_local_loops"):
        conn.executescript(REVERSE_LOCAL_LOOPS_SCHEMA_V29)


# @helix:index id=helix-db.migrate-v29-to-v30 domain=cli/lib summary=v30 harness_check_events migration
def _migrate_v29_to_v30(conn: sqlite3.Connection) -> None:
    """v30: harness_check_events テーブル追加。"""
    conn.executescript(HARNESS_CHECK_EVENTS_SCHEMA_V30)


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _has_column(conn, table_name, column_name):
    if not _IDENTIFIER_RE.match(str(table_name)):
        raise ValueError(f"invalid table name: {table_name!r}")
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)


def _has_table(conn, table_name):
    if not _IDENTIFIER_RE.match(str(table_name)):
        raise ValueError(f"invalid table name: {table_name!r}")
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _migrate_gate_runs_v4(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS gate_runs_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_run_id INTEGER REFERENCES task_runs(id),
            gate TEXT NOT NULL,
            result TEXT NOT NULL,
            fail_reasons TEXT DEFAULT '',
            retry_count INTEGER DEFAULT 0,
            duration_ms INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        INSERT INTO gate_runs_new
            (id, task_run_id, gate, result, fail_reasons, retry_count, duration_ms, created_at)
        SELECT
            id, NULL, gate, result, fail_reasons, retry_count, duration_ms, created_at
        FROM gate_runs
        """
    )
    conn.execute("DROP TABLE gate_runs")
    conn.execute("ALTER TABLE gate_runs_new RENAME TO gate_runs")


def _migrate_interrupts_v4(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS interrupts_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_run_id INTEGER REFERENCES task_runs(id),
            interrupt_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            classification TEXT NOT NULL,
            scope TEXT DEFAULT '',
            status TEXT NOT NULL,
            duration_ms INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            resolved_at TEXT DEFAULT ''
        )
        """
    )
    conn.execute(
        """
        INSERT INTO interrupts_new
            (id, task_run_id, interrupt_id, kind, classification, scope, status, duration_ms, created_at, resolved_at)
        SELECT
            id, NULL, interrupt_id, kind, classification, scope, status, duration_ms, created_at, resolved_at
        FROM interrupts
        """
    )
    conn.execute("DROP TABLE interrupts")
    conn.execute("ALTER TABLE interrupts_new RENAME TO interrupts")


def _migrate_retro_items_v4(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS retro_items_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gate TEXT NOT NULL,
            gate_name TEXT,
            gate_run_id INTEGER REFERENCES gate_runs(id),
            item_type TEXT NOT NULL,
            content TEXT NOT NULL,
            owner TEXT DEFAULT '',
            due TEXT DEFAULT '',
            done INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        INSERT INTO retro_items_new
            (id, gate, gate_name, gate_run_id, item_type, content, owner, due, done, created_at)
        SELECT
            id, gate, gate, NULL, item_type, content, owner, due, done, created_at
        FROM retro_items
        """
    )
    conn.execute("DROP TABLE retro_items")
    conn.execute("ALTER TABLE retro_items_new RENAME TO retro_items")


def _migrate_skill_usage_v5(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS skill_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_text TEXT NOT NULL,
            skill_id TEXT NOT NULL,
            references_used TEXT,
            agent_used TEXT,
            match_score REAL,
            match_reason TEXT,
            outcome TEXT,
            user_feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_skill_usage_skill ON skill_usage(skill_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_skill_usage_outcome ON skill_usage(outcome)")


def _ensure_skill_usage_table(conn):
    # project-root tests cover catalog public behavior + migration end-to-end,
    # while cli/lib/tests keep helper-level unit coverage.
    if not _has_table(conn, "skill_usage"):
        _migrate_skill_usage_v5(conn)


def _migrate_skill_usage_stdout_v6(conn):
    _ensure_skill_usage_table(conn)
    if not _has_column(conn, "skill_usage", "result_stdout"):
        conn.execute("ALTER TABLE skill_usage ADD COLUMN result_stdout TEXT")
    if not _has_column(conn, "skill_usage", "result_stderr"):
        conn.execute("ALTER TABLE skill_usage ADD COLUMN result_stderr TEXT")


def _migrate_skill_usage_v7(conn):
    _ensure_skill_usage_table(conn)
    if not _has_column(conn, "skill_usage", "effort_estimated"):
        conn.execute("ALTER TABLE skill_usage ADD COLUMN effort_estimated TEXT")
    if not _has_column(conn, "skill_usage", "effort_actual"):
        conn.execute("ALTER TABLE skill_usage ADD COLUMN effort_actual TEXT")
    if not _has_column(conn, "skill_usage", "timeout_occurred"):
        conn.execute("ALTER TABLE skill_usage ADD COLUMN timeout_occurred INTEGER DEFAULT 0")
    if not _has_column(conn, "skill_usage", "tokens_used"):
        conn.execute("ALTER TABLE skill_usage ADD COLUMN tokens_used INTEGER")
    if not _has_column(conn, "skill_usage", "model_used"):
        conn.execute("ALTER TABLE skill_usage ADD COLUMN model_used TEXT")
    if not _has_column(conn, "skill_usage", "fallback_applied"):
        conn.execute("ALTER TABLE skill_usage ADD COLUMN fallback_applied INTEGER DEFAULT 0")


def _create_budget_events_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS budget_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occurred_at TEXT NOT NULL,
            event_type TEXT NOT NULL CHECK(event_type IN
                ('exhaustion', 'fallback', 'warning', 'forecast_miss', 'limit_observed')),
            model TEXT,
            pct_used REAL,
            details_json TEXT
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_budget_events_at ON budget_events(occurred_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_budget_events_type ON budget_events(event_type)")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_skill_usage_model ON skill_usage(model_used) "
        "WHERE model_used IS NOT NULL"
    )


# @helix:index id=helix-db.migrate domain=cli/lib summary=migrateを実行する
def migrate(conn):
    """スキーマをマイグレーション"""
    current = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] or 0
    if current < CURRENT_SCHEMA_VERSION:
        # v1→v2: requirements 系テーブル追加
        if current < 2:
            _create_requirements_tables(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (2, datetime('now'))"
            )
        # v2→v3: パフォーマンス改善インデックス追加
        if current < 3:
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_runs_task_id_id_desc ON task_runs(task_id, id DESC)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_action_logs_task_run_status ON action_logs(action_type, status)"
            )
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (3, datetime('now'))"
            )
        # v3→v4: gate_runs / interrupts / retro_items に FK カラム追加
        if current < 4:
            if not _has_column(conn, "gate_runs", "task_run_id"):
                _migrate_gate_runs_v4(conn)
            if not _has_column(conn, "interrupts", "task_run_id"):
                _migrate_interrupts_v4(conn)
            if not _has_column(conn, "retro_items", "gate_name") or not _has_column(conn, "retro_items", "gate_run_id"):
                _migrate_retro_items_v4(conn)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_gate_runs_task_run_id ON gate_runs(task_run_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_interrupts_task_run_id ON interrupts(task_run_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_retro_items_gate_run_id ON retro_items(gate_run_id)"
            )
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (4, datetime('now'))"
            )
        # v4→v5: skill_usage テーブル追加
        if current < 5:
            _migrate_skill_usage_v5(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (5, datetime('now'))"
            )
        # v5→v6: skill_usage に result_stdout / result_stderr カラム追加
        if current < 6:
            _migrate_skill_usage_stdout_v6(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (6, datetime('now'))"
            )
        # v6→v7: skill_usage に budget/autothinking 拡張カラム追加 + budget_events 作成
        if current < 7:
            _migrate_skill_usage_v7(conn)
            _create_budget_events_table(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (7, datetime('now'))"
            )
        # v7→v8: accuracy_score テーブル追加 (PLAN-004)
        if current < 8:
            _create_accuracy_score_table(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (8, datetime('now'))"
            )
        # v8→v9: automation infra テーブル追加 (PLAN-005 scheduler/job-queue/lock/setup/observability)
        if current < 9:
            _create_infra_tables_v9(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (9, datetime('now'))"
            )
        # v9→v10: audit_decisions + import_runs (PLAN-002 棚卸し基盤)
        if current < 10:
            _create_audit_decisions_v10(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (10, datetime('now'))"
            )
        # v10→v11: deferred_findings + adjustments + effective view (HELIX-V3-FOLLOWUP)
        if current < 11:
            _migrate_v10_to_v11(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (11, datetime('now'))"
            )
        # v11→v12: scrum_trigger table (PLAN-007 Scrum 5 種トリガー)
        if current < 12:
            _migrate_v11_to_v12(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (12, datetime('now'))"
            )
        # v12→v13: verify_runs table (PLAN-010 verify-agent persistence)
        if current < 13:
            _migrate_v12_to_v13(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (13, datetime('now'))"
            )
        # v13→v14: code_index table (PLAN-011 code catalog)
        if current < 14:
            _migrate_v13_to_v14(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (14, datetime('now'))"
            )
        # v14→v15: code_index bucket + symbol_line (PLAN-013)
        if current < 15:
            _migrate_v14_to_v15(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (15, datetime('now'))"
            )
        # v15→v16: sessions table + skill_usage.session_id (PLAN-023 W-2a)
        if current < 16:
            _migrate_v15_to_v16(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (16, datetime('now'))"
            )
        if current < 17:
            _migrate_v16_to_v17(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (17, datetime('now'))"
            )
        if current < 18:
            _migrate_v17_to_v18(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (18, datetime('now'))"
            )
        if current < 19:
            _migrate_v18_to_v19(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (19, datetime('now'))"
            )
        if current < 20:
            _migrate_v19_to_v20(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (20, datetime('now'))"
            )
        if current < 21:
            _migrate_v20_to_v21(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (21, datetime('now'))"
            )
        if current < 22:
            _migrate_v21_to_v22(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (22, datetime('now'))"
            )
        if current < 23:
            _migrate_v22_to_v23(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (23, datetime('now'))"
            )
        if current < 24:
            _migrate_v23_to_v24(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (24, datetime('now'))"
            )
        if current < 25:
            _migrate_v24_to_v25(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (25, datetime('now'))"
            )
        if current < 26:
            _migrate_v25_to_v26(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (26, datetime('now'))"
            )
        if current < 27:
            _migrate_v26_to_v27(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (27, datetime('now'))"
            )
        if current < 28:
            _migrate_v27_to_v28(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (28, datetime('now'))"
            )
        if current < 29:
            _migrate_v28_to_v29(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (29, datetime('now'))"
            )
        if current < 30:
            _migrate_v29_to_v30(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (30, datetime('now'))"
            )
        if current < 31:
            v31_db_separation.migrate_v30_to_v31(conn)
        if current < 32:
            v32_design_doc_web_search_audit.migrate_v31_to_v32(conn)
        v32_design_doc_web_search_audit.ensure_v32_additive_schema(conn)
        if current < 33:
            v33_gate_audit_metrics.migrate_v32_to_v33(conn)
        v33_gate_audit_metrics.ensure_v33_additive_schema(conn)
        conn.commit()


# @helix:index id=helix-db.migrate-all domain=cli/lib summary=全schema migration の互換 wrapper
def migrate_all(conn: sqlite3.Connection) -> None:
    """fresh DB / 既存 DB の両方で全 schema を揃える互換 wrapper。"""
    _ensure_schema(conn)


def _ensure_schema(conn):
    conn.executescript(SCHEMA)
    conn.executescript(SCHEMA_VERSION_SCHEMA)
    migrate(conn)
    _ensure_invocation_log_table(conn)
    _ensure_setup_tables(conn)


# @helix:index id=helix-db.init-db domain=cli/lib summary=dbを初期化する
def init_db(db_path):
    with _write_connection(db_path, ensure_schema=False) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        _ensure_schema(conn)
    print(f"DB initialized: {db_path}")


# @helix:index id=helix-db.insert-row domain=cli/lib summary=rowを挿入する
def insert_row(db_path, table, data):
    if not isinstance(data, dict):
        raise ValueError('insert payload must be a JSON object')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', table):
        raise ValueError(f'invalid table name: {table}')

    with _write_connection(db_path) as conn:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        if not rows:
            raise ValueError(f'unknown table: {table}')

        valid_columns = {row[1] for row in rows}
        payload = dict(data)
        if 'created_at' in valid_columns and 'created_at' not in payload:
            payload['created_at'] = datetime.now().isoformat()

        if not payload:
            raise ValueError('insert payload is empty')

        for key in payload:
            if key not in valid_columns:
                raise KeyError(f'unknown column: {table}.{key}')

        columns = list(payload.keys())
        values = [payload[col] for col in columns]
        placeholders = ', '.join(['?'] * len(columns))
        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        conn.execute(sql, values)
        row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    print(row_id)


# @helix:index id=helix-db.record-task domain=cli/lib summary=taskを記録する
def record_task(db_path, data):
    with _write_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO task_runs (task_id, task_type, plan_goal, role, status, started_at, output_log) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (data['task_id'], data['task_type'], data.get('plan_goal', ''),
             data['role'], data.get('status', 'running'),
             data.get('started_at', datetime.now().isoformat()),
             data.get('output_log', ''))
        )
        run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    print(run_id)


# @helix:index id=helix-db.record-action domain=cli/lib summary=actionを記録する
def record_action(db_path, data):
    with _write_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO action_logs (task_run_id, action_index, action_type, action_desc, status, evidence) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (data['task_run_id'], data['action_index'], data['action_type'],
             data.get('action_desc', ''), data.get('status', 'pending'),
             data.get('evidence', ''))
        )
        action_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    print(action_id)


# @helix:index id=helix-db.record-observation domain=cli/lib summary=observationを記録する
def record_observation(db_path, data):
    with _write_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO observations (task_run_id, action_log_id, action_type, "
            "expected_keywords, matched_keywords, passed, reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (data['task_run_id'], data.get('action_log_id'),
             data['action_type'], json.dumps(data.get('expected_keywords', [])),
             json.dumps(data.get('matched_keywords', [])),
             1 if data.get('passed') else 0, data.get('reason', ''))
        )


# @helix:index id=helix-db.record-feedback domain=cli/lib summary=feedbackを記録する
def record_feedback(db_path, data):
    with _write_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO feedback (task_run_id, feedback_type, category, description, impact, resolution) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (data.get('task_run_id'), data['feedback_type'],
             data.get('category', ''), data['description'],
             data.get('impact', 'medium'), data.get('resolution', ''))
        )
    print("Feedback recorded")


# @helix:index id=helix-db.record-feedback-argv domain=cli/lib summary=feedback argvを記録する
def record_feedback_argv(
    db_path,
    task_run_id,
    feedback_type,
    category,
    description,
    impact='medium',
    resolution='',
):
    run_id = None
    if isinstance(task_run_id, str):
        value = task_run_id.strip()
        if value.isdigit() and int(value) > 0:
            run_id = int(value)
    elif isinstance(task_run_id, int) and task_run_id > 0:
        run_id = task_run_id

    record_feedback(
        db_path,
        {
            'task_run_id': run_id,
            'feedback_type': feedback_type,
            'category': category,
            'description': description,
            'impact': impact,
            'resolution': resolution,
        },
    )


# @helix:index id=helix-db.record-invocation domain=cli/lib summary=invocation telemetryを記録する
def record_invocation(db_path, data):
    raw_meta = _redact_meta(data.get("raw_meta", {}))

    with _write_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO invocation_log "
            "(timestamp, type, role, model, task_id, plan_id, sprint, input_bytes, output_bytes, "
            "duration_ms, decision, cost_cents, parent_invocation_id, raw_meta) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                data.get("timestamp", datetime.now().isoformat()),
                data["type"],
                data.get("role"),
                data.get("model"),
                data.get("task_id"),
                data.get("plan_id"),
                data.get("sprint"),
                data.get("input_bytes"),
                data.get("output_bytes"),
                data.get("duration_ms"),
                data.get("decision"),
                data.get("cost_cents"),
                data.get("parent_invocation_id"),
                json.dumps(raw_meta, ensure_ascii=False),
            ),
        )
        row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    print(row_id)


# @helix:index id=helix-db.record-accuracy-score domain=cli/lib summary=accuracy scoreを記録する
def record_accuracy_score(
    db_path,
    plan_id,
    gate,
    dimension,
    level,
    comment="",
    evidence="",
    sprint=None,
    reviewer="codex-tl",
):
    """5 軸 Lv1-5 フィードバックを accuracy_score に記録。

    Args:
        plan_id: 対象 PLAN ID (e.g. "PLAN-002")
        gate: gate 名 (G2/G3/G4/G5/G6/G7/L8/PLAN_REVIEW)
        dimension: 評価軸 (density/depth/breadth/accuracy/maintainability)
        level: 1-5
        comment: 自由記述 (Sprint 3 までに redaction 適用必須)
        evidence: 根拠 (Sprint 3 までに redaction 適用必須)
        sprint: 任意 (e.g. "Sprint 2.3")
        reviewer: 評価者 (default: codex-tl)

    Returns:
        挿入された行 ID
    """
    if not plan_id:
        raise ValueError("plan_id is required")
    if gate not in ACCURACY_SCORE_GATES:
        raise ValueError(f"invalid gate: {gate}")
    if dimension not in ACCURACY_SCORE_DIMENSIONS:
        raise ValueError(f"invalid dimension: {dimension}")
    if type(level) is not int or not 1 <= level <= 5:
        raise ValueError("level must be an integer between 1 and 5")

    with _write_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO accuracy_score "
            "(plan_id, gate, dimension, level, comment, evidence, recorded_at, sprint, reviewer) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                plan_id,
                gate,
                dimension,
                level,
                comment,
                evidence,
                datetime.now().isoformat(),
                sprint,
                reviewer,
            ),
        )
        row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return row_id


# @helix:index id=helix-db.query-accuracy-history domain=cli/lib summary=query accuracy historyを実行する
def query_accuracy_history(db_path, plan_id=None, gate=None, dimension=None, since=None, limit=None):
    """accuracy_score の履歴クエリ。フィルタ条件で絞り込み。

    Args:
        plan_id: 任意 (絞り込み)
        gate: 任意
        dimension: 任意
        since: ISO8601 文字列、これ以降のレコードのみ
        limit: 任意 (LIMIT 句)

    Returns:
        list of dict (各行を dict 化)
    """
    if gate is not None and gate not in ACCURACY_SCORE_GATES:
        raise ValueError(f"invalid gate: {gate}")
    if dimension is not None and dimension not in ACCURACY_SCORE_DIMENSIONS:
        raise ValueError(f"invalid dimension: {dimension}")
    if limit is not None and (type(limit) is not int or limit < 1):
        raise ValueError("limit must be a positive integer")

    _prepare_db_path(db_path)
    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        where = []
        params = []
        if plan_id is not None:
            where.append("plan_id = ?")
            params.append(plan_id)
        if gate is not None:
            where.append("gate = ?")
            params.append(gate)
        if dimension is not None:
            where.append("dimension = ?")
            params.append(dimension)
        if since is not None:
            where.append("recorded_at >= ?")
            params.append(since)

        sql = "SELECT * FROM accuracy_score"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY recorded_at DESC, id DESC"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)

        return [dict(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def _epoch_now():
    return int(time.time())


def _json_text(value, default):
    if value is None:
        value = default
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _require_non_empty(value, field_name):
    if value is None or str(value).strip() == "":
        raise ValueError(f"{field_name} is required")
    return str(value)


def _validate_choice(value, field_name, allowed_values):
    if value not in allowed_values:
        raise ValueError(f"invalid {field_name}: {value}")
    return value


def _validate_observable_name(value, field_name):
    value = _require_non_empty(value, field_name)
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", value):
        raise ValueError(f"invalid {field_name}: {value}")
    return value


def _validate_positive_int(value, field_name):
    if type(value) is not int or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


# @helix:index id=helix-db.validate-positive-number domain=cli/lib summary=float/int 両対応の非負数 validator
def _validate_positive_number(value, field_name):
    import math

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    if number < 0:
        raise ValueError(f"{field_name} must be >= 0")
    return number


def _validate_identifier(value, field_name):
    value = _require_non_empty(value, field_name)
    if not _IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"invalid {field_name}: {value!r}")
    return value


def _validate_optional_choice(value, field_name, allowed_values):
    if value is None:
        return None
    return _validate_choice(value, field_name, allowed_values)


def _validate_dict_payload(value, field_name):
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a dict")
    return value


def _clean_optional_text(value, field_name):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if "\x00" in text:
        raise ValueError(f"{field_name} must not contain NUL")
    return text


def _table_columns(conn, table_name):
    table_name = _validate_identifier(table_name, "table_name")
    rows = conn.execute(f"PRAGMA table_info({_quote_identifier(table_name)})").fetchall()
    if not rows:
        raise ValueError(f"unknown table: {table_name}")
    return table_name, rows


# @helix:index id=helix-db.upsert-row domain=cli/lib summary=UPSERT helper for UNIQUE-constrained tables
def _upsert_row(conn, table, data, conflict_column):
    table_name, rows = _table_columns(conn, table)
    payload = _validate_dict_payload(data, "data").copy()
    conflict_column = _validate_identifier(conflict_column, "conflict_column")
    if conflict_column not in payload:
        raise ValueError(f"missing conflict column: {conflict_column}")
    if not payload:
        raise ValueError("upsert payload is empty")

    valid_columns = {row["name"] if isinstance(row, sqlite3.Row) else row[1] for row in rows}
    if conflict_column not in valid_columns:
        raise ValueError(f"unknown column: {table_name}.{conflict_column}")

    for key in payload:
        _validate_identifier(key, f"{table_name} column")
        if key not in valid_columns:
            raise KeyError(f"unknown column: {table_name}.{key}")

    columns = list(payload.keys())
    quoted_columns = [_quote_identifier(column) for column in columns]
    placeholders = ", ".join(["?"] * len(columns))
    update_targets = columns if len(columns) == 1 else [column for column in columns if column != conflict_column]
    if not update_targets:
        update_targets = [conflict_column]
    update_clause = ", ".join(
        f"{_quote_identifier(column)} = excluded.{_quote_identifier(column)}"
        for column in update_targets
    )
    sql = (
        f"INSERT INTO {_quote_identifier(table_name)} ({', '.join(quoted_columns)}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT({_quote_identifier(conflict_column)}) DO UPDATE SET {update_clause}"
    )
    values = [payload[column] for column in columns]
    conn.execute(sql, values)
    row = conn.execute(
        f"SELECT rowid FROM {_quote_identifier(table_name)} "
        f"WHERE {_quote_identifier(conflict_column)} = ?",
        (payload[conflict_column],),
    ).fetchone()
    if row is None:
        raise sqlite3.IntegrityError(f"upsert failed for {table_name}.{conflict_column}")
    return int(row[0])


# @helix:index id=helix-db.transition-lifecycle-status domain=cli/lib summary=lifecycle status transition helper
def _transition_lifecycle_status(conn, table, row_id, from_status, to_status, allowed_transitions):
    table_name, rows = _table_columns(conn, table)
    row_id = _validate_positive_int(row_id, "row_id")
    from_status = _require_non_empty(from_status, "from_status")
    to_status = _require_non_empty(to_status, "to_status")
    if not isinstance(allowed_transitions, dict):
        raise ValueError("allowed_transitions must be a dict")

    valid_columns = {row["name"] if isinstance(row, sqlite3.Row) else row[1] for row in rows}
    if "status" not in valid_columns:
        raise ValueError(f"unknown column: {table_name}.status")

    current_row = conn.execute(
        f"SELECT rowid, {_quote_identifier('status')} FROM {_quote_identifier(table_name)} WHERE rowid = ?",
        (row_id,),
    ).fetchone()
    if current_row is None:
        raise ValueError(f"row_id does not exist: {row_id}")

    current_status = current_row["status"] if isinstance(current_row, sqlite3.Row) else current_row[1]
    if current_status != from_status:
        raise sqlite3.IntegrityError(
            f"status mismatch: expected {from_status} got {current_status}"
        )

    next_statuses = allowed_transitions.get(from_status)
    if not next_statuses or to_status not in next_statuses:
        raise sqlite3.IntegrityError(
            f"invalid lifecycle transition: {from_status} -> {to_status}"
        )

    assignments = ['status = ?']
    params = [to_status]
    if "updated_at" in valid_columns:
        assignments.append("updated_at = ?")
        params.append(datetime.now().isoformat())
    params.append(row_id)
    conn.execute(
        f"UPDATE {_quote_identifier(table_name)} "
        f"SET {', '.join(assignments)} "
        f"WHERE rowid = ?",
        params,
    )
    return True


# @helix:index id=helix-db.resolve-default-db-path domain=cli/lib summary=hook と endpoint の DB_PATH 解決経路を統一する
def resolve_default_db_path():
    env_path = os.environ.get("HELIX_DB_PATH", "").strip()
    if env_path:
        return str(Path(env_path).expanduser())

    for env_name in ("HELIX_PROJECT_ROOT", "PROJECT_ROOT"):
        project_root = os.environ.get(env_name, "").strip()
        if project_root:
            return str(Path(project_root).expanduser() / ".helix" / "helix.db")

    helix_dir = os.environ.get("HELIX_DIR", "").strip()
    if helix_dir:
        return str(Path(helix_dir).expanduser() / "helix.db")

    return str(Path.cwd() / ".helix" / "helix.db")


# @helix:index id=helix-db.insert-audit-log domain=cli/lib summary=audit_log append-only writer for hooks endpoints and CLI
def insert_audit_log(
    conn,
    audit_kind: str,
    actor: str,
    run_id: int | None = None,
    payload: dict | None = None,
) -> int:
    _table_columns(conn, "audit_log")
    audit_kind = _validate_choice(
        audit_kind,
        "audit_kind",
        ("hook_exec", "gate_eval", "cli_invocation", "endpoint_call"),
    )
    actor = _require_non_empty(actor, "actor")
    if run_id is not None:
        run_id = _validate_positive_int(run_id, "run_id")
    payload_dict = {} if payload is None else _validate_dict_payload(payload, "payload")

    conn.execute(
        """
        INSERT INTO audit_log (audit_kind, actor, run_id, payload)
        VALUES (?, ?, ?, ?)
        """,
        (audit_kind, actor, run_id, json.dumps(payload_dict, ensure_ascii=False)),
    )
    row = conn.execute("SELECT last_insert_rowid()").fetchone()
    if row is None:
        raise sqlite3.IntegrityError("failed to insert audit_log row")
    return int(row[0])


# @helix:index id=helix-db.insert-design-doc-web-search-audit domain=cli/lib summary=設計 doc の WebSearch/OSS 探索 evidence を append-only で記録する
def insert_design_doc_web_search_audit(
    db_path,
    *,
    plan_id: str | None = None,
    adr_id: str | None = None,
    hook_session_id: str,
    web_search_executed: bool,
    oss_search_executed: bool,
    created_at: str | None = None,
):
    """Record design doc WebSearch/OSS exploration evidence."""
    plan_id = _clean_optional_text(plan_id, "plan_id")
    adr_id = _clean_optional_text(adr_id, "adr_id")
    if plan_id is None and adr_id is None:
        raise ValueError("plan_id or adr_id is required")

    hook_session_id = _require_non_empty(hook_session_id, "hook_session_id")
    created_at = _clean_optional_text(created_at, "created_at") or datetime.now().isoformat()

    with _write_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO design_doc_web_search_audit (
                plan_id,
                adr_id,
                hook_session_id,
                web_search_executed,
                oss_search_executed,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                plan_id,
                adr_id,
                hook_session_id,
                int(bool(web_search_executed)),
                int(bool(oss_search_executed)),
                created_at,
            ),
        )
        return _validate_positive_int(int(cursor.lastrowid), "row_id")


# @helix:index id=helix-db.insert-gate-audit-metric domain=cli/lib summary=design doc WebSearch gate の advisory/bypass 計測を記録する
def insert_gate_audit_metric(
    db_path,
    *,
    gate_name: str,
    plan_id: str,
    advisory_result: str,
    bypass_used: bool,
    created_at: str | None = None,
):
    """Record a gate-level design doc audit metric row."""
    gate_name = _validate_choice(_require_non_empty(gate_name, "gate_name"), "gate_name", ("G2", "G3"))
    plan_id = _require_non_empty(_clean_optional_text(plan_id, "plan_id"), "plan_id")
    advisory_result = _validate_choice(
        _require_non_empty(advisory_result, "advisory_result"),
        "advisory_result",
        ("pass", "warn", "skip"),
    )
    created_at = _clean_optional_text(created_at, "created_at") or datetime.now().isoformat()

    with _write_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO gate_audit_metrics (
                gate_name,
                plan_id,
                advisory_result,
                bypass_used,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                gate_name,
                plan_id,
                advisory_result,
                int(bool(bypass_used)),
                created_at,
            ),
        )
        return _validate_positive_int(int(cursor.lastrowid), "row_id")


# @helix:index id=helix-db.query-latest-design-doc-web-search-audit domain=cli/lib summary=設計 doc WebSearch/OSS 探索の最新 audit 行を取得する
def query_latest_design_doc_web_search_audit(
    db_path,
    *,
    plan_id: str | None = None,
    adr_id: str | None = None,
):
    """Return the latest design doc WebSearch/OSS evidence row for the target."""
    plan_id = _clean_optional_text(plan_id, "plan_id")
    adr_id = _clean_optional_text(adr_id, "adr_id")
    if plan_id is None and adr_id is None:
        raise ValueError("plan_id or adr_id is required")

    where = []
    params = []
    if plan_id is not None:
        where.append("plan_id = ?")
        params.append(plan_id)
    if adr_id is not None:
        where.append("adr_id = ?")
        params.append(adr_id)

    conn = _automation_conn(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM design_doc_web_search_audit WHERE "
            + " AND ".join(where)
            + " ORDER BY created_at DESC, id DESC LIMIT 1",
            params,
        ).fetchone()
        return None if row is None else dict(row)
    finally:
        conn.close()


# @helix:index id=helix-db.insert-automation-run domain=cli/lib summary=automation_runs rowを作成し pending から running へ遷移する
def insert_automation_run(
    conn,
    trigger_source: str,
    run_kind: str,
    metadata: dict | None = None,
) -> int:
    """automation_runs を登録し、開始時点で running へ進めた run_id を返す。"""
    trigger_source = _require_non_empty(trigger_source, "trigger_source")
    run_kind = _validate_choice(
        _require_non_empty(run_kind, "run_kind"),
        "run_kind",
        ("push", "pr", "pretool", "posttool", "stop", "session_start"),
    )
    if metadata is not None:
        metadata = _validate_dict_payload(metadata, "metadata")
    metadata_payload = dict(metadata or {})
    metadata_payload.setdefault("trigger_source", trigger_source)

    payload = {
        "run_kind": run_kind,
        "trigger_actor": "system",
        "started_at": datetime.now().isoformat(),
        "status": "pending",
    }
    plan_id = metadata_payload.get("plan_id")
    if isinstance(plan_id, str) and plan_id.strip():
        payload["plan_id"] = plan_id.strip()
    if metadata_payload:
        payload["summary"] = json.dumps(metadata_payload, ensure_ascii=False, sort_keys=True)

    columns = list(payload.keys())
    placeholders = ", ".join(["?"] * len(columns))
    cursor = conn.execute(
        f"INSERT INTO automation_runs ({', '.join(columns)}) VALUES ({placeholders})",
        [payload[column] for column in columns],
    )
    run_id = _validate_positive_int(int(cursor.lastrowid), "run_id")
    _transition_lifecycle_status(
        conn,
        "automation_runs",
        run_id,
        "pending",
        "running",
        {
            "pending": ["running", "cancelled"],
            "running": ["completed", "failed", "cancelled"],
        },
    )
    return run_id


# @helix:index id=helix-db.complete-automation-run domain=cli/lib summary=automation_runs rowを running から terminal status へ完了させる
def complete_automation_run(
    conn,
    run_id: int,
    status: str = "completed",
    error: str | None = None,
) -> None:
    """automation_runs を terminal status へ遷移し、終了メタデータを記録する。"""
    run_id = _validate_positive_int(run_id, "run_id")
    status = _validate_choice(
        _require_non_empty(status, "status"),
        "status",
        ("completed", "failed", "cancelled"),
    )
    error_text = None if error is None else str(error).strip() or None

    conn.execute(
        """
        UPDATE automation_runs
        SET ended_at = ?,
            exit_code = ?,
            last_error = ?
        WHERE id = ? AND status = 'running'
        """,
        (
            datetime.now().isoformat(),
            0 if status == "completed" else 1,
            error_text,
            run_id,
        ),
    )
    _transition_lifecycle_status(
        conn,
        "automation_runs",
        run_id,
        "running",
        status,
        {
            "pending": ["running", "cancelled"],
            "running": ["completed", "failed", "cancelled"],
        },
    )


# @helix:index id=helix-db.insert-drive-decision domain=cli/lib summary=drive switch decisionをappend-onlyで記録する
def insert_drive_decision(
    conn,
    plan_id: str,
    source_entry_id: int,
    target_entry_id: int,
    decision: str,
    reason: str | None = None,
    direction: str | None = None,
) -> int:
    """design_sprint_drive_decisions に drive switch 判定を追加する。"""
    plan_id = _require_non_empty(plan_id, "plan_id")
    source_entry_id = _validate_positive_int(source_entry_id, "source_entry_id")
    target_entry_id = _validate_positive_int(target_entry_id, "target_entry_id")
    decision = _validate_choice(
        _require_non_empty(decision, "decision"),
        "decision",
        DESIGN_SPRINT_SWITCH_STATUSES,
    )
    if source_entry_id == target_entry_id:
        raise ValueError("source_entry_id and target_entry_id must differ")

    source_entry = conn.execute(
        "SELECT id, plan_id FROM design_sprint_entries WHERE id = ?",
        (source_entry_id,),
    ).fetchone()
    if source_entry is None:
        raise ValueError("source_entry_id does not exist")
    if source_entry["plan_id"] != plan_id:
        raise ValueError("source_entry_id does not belong to plan_id")

    target_entry = conn.execute(
        "SELECT id, plan_id FROM design_sprint_entries WHERE id = ?",
        (target_entry_id,),
    ).fetchone()
    if target_entry is None:
        raise ValueError("target_entry_id does not exist")
    if target_entry["plan_id"] != plan_id:
        raise ValueError("target_entry_id does not belong to plan_id")

    reason_text = str(reason).strip() if reason is not None else ""
    if not reason_text:
        reason_text = f"drive switch decision recorded for {plan_id}"

    direction_value = None
    if direction not in (None, ""):
        direction_value = _validate_choice(
            _require_non_empty(direction, "direction"),
            "direction",
            ("forward", "reverse", "forward_after_reverse"),
        )

    _, rows = _table_columns(conn, "design_sprint_drive_decisions")
    valid_columns = {row["name"] if isinstance(row, sqlite3.Row) else row[1] for row in rows}

    payload = {
        "source_entry_id": source_entry_id,
        "target_entry_id": target_entry_id,
        "decision": decision,
        "reason": _require_non_empty(reason_text, "reason"),
    }
    if "plan_id" in valid_columns:
        payload["plan_id"] = plan_id
    if "decided_by" in valid_columns:
        payload["decided_by"] = "se"
    if "direction" in valid_columns and direction_value is not None:
        payload["direction"] = direction_value

    columns = list(payload.keys())
    placeholders = ", ".join(["?"] * len(columns))
    cursor = conn.execute(
        f"INSERT INTO design_sprint_drive_decisions ({', '.join(columns)}) VALUES ({placeholders})",
        [payload[column] for column in columns],
    )
    return _validate_positive_int(int(cursor.lastrowid), "decision_id")


# @helix:index id=helix-db.upsert-session-telemetry domain=cli/lib summary=session_telemetry を session_id 単位で UPSERT し start/stop hook から再利用する
def upsert_session_telemetry(
    conn,
    session_id: str,
    actor: str,
    *,
    related_plan_id: str | None = None,
    tool_uses_count: int = 0,
    tokens_total: int = 0,
    cost_usd: float = 0.0,
    ended: bool = False,
) -> int:
    session_id = _require_non_empty(session_id, "session_id")
    actor = _require_non_empty(actor, "actor")

    if type(tool_uses_count) is not int or tool_uses_count < 0:
        raise ValueError("tool_uses_count must be a non-negative integer")
    if type(tokens_total) is not int or tokens_total < 0:
        raise ValueError("tokens_total must be a non-negative integer")
    cost_usd = _validate_positive_number(cost_usd, "cost_usd")

    payload = {
        "session_id": session_id,
        "actor": actor,
        "tool_uses_count": tool_uses_count,
        "tokens_total": tokens_total,
        "cost_usd": cost_usd,
        "last_updated_at": datetime.now().isoformat(),
    }
    if related_plan_id is not None:
        plan_id = str(related_plan_id).strip()
        if plan_id:
            payload["related_plan_id"] = plan_id
    if ended:
        payload["ended_at"] = datetime.now().isoformat()

    telemetry_id = _upsert_row(
        conn,
        "session_telemetry",
        payload,
        conflict_column="session_id",
    )
    return _validate_positive_int(int(telemetry_id), "telemetry_id")


def _sql_string_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


# @helix:index id=helix-db.create-append-only-trigger domain=cli/lib summary=append-only trigger helper for SQLite tables
def _create_append_only_trigger(
    conn,
    table_name,
    immutable_columns=None,
    terminal_status_column=None,
    terminal_values=None,
):
    table_name, rows = _table_columns(conn, table_name)
    valid_columns = {row["name"] if isinstance(row, sqlite3.Row) else row[1] for row in rows}
    immutable_columns = list(immutable_columns) if immutable_columns is not None else None
    terminal_values = list(terminal_values) if terminal_values is not None else None

    if immutable_columns == []:
        raise ValueError("immutable_columns must not be empty")
    if terminal_values is not None and terminal_status_column is None:
        raise ValueError("terminal_status_column is required when terminal_values is set")
    if terminal_values == []:
        raise ValueError("terminal_values must not be empty")

    trigger_specs = [
        (
            f"{table_name}_no_delete",
            f"""
CREATE TRIGGER IF NOT EXISTS {_quote_identifier(f"{table_name}_no_delete")}
BEFORE DELETE ON {_quote_identifier(table_name)}
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, {_sql_string_literal(f"{table_name} is append-only")});
END
""".strip(),
        )
    ]

    if immutable_columns is not None:
        for column in immutable_columns:
            column = _validate_identifier(column, "immutable_column")
            if column not in valid_columns:
                raise ValueError(f"unknown column: {table_name}.{column}")
            trigger_name = f"{table_name}_{column}_immutable"
            trigger_specs.append(
                (
                    trigger_name,
                    f"""
CREATE TRIGGER IF NOT EXISTS {_quote_identifier(trigger_name)}
BEFORE UPDATE OF {_quote_identifier(column)} ON {_quote_identifier(table_name)}
FOR EACH ROW
WHEN OLD.{_quote_identifier(column)} IS NOT NEW.{_quote_identifier(column)}
BEGIN
    SELECT RAISE(ABORT, {_sql_string_literal(f"{table_name}.{column} is immutable")});
END
""".strip(),
                )
            )

    if terminal_status_column is not None and terminal_values is not None:
        terminal_status_column = _validate_identifier(terminal_status_column, "terminal_status_column")
        if terminal_status_column not in valid_columns:
            raise ValueError(f"unknown column: {table_name}.{terminal_status_column}")
        validated_values = [_require_non_empty(value, "terminal_value") for value in terminal_values]
        trigger_name = f"{table_name}_terminal_final"
        terminal_list = ", ".join(_sql_string_literal(value) for value in validated_values)
        trigger_specs.append(
            (
                trigger_name,
                f"""
CREATE TRIGGER IF NOT EXISTS {_quote_identifier(trigger_name)}
BEFORE UPDATE ON {_quote_identifier(table_name)}
FOR EACH ROW
WHEN OLD.{_quote_identifier(terminal_status_column)} IN ({terminal_list})
BEGIN
    SELECT RAISE(ABORT, {_sql_string_literal(f"{table_name} terminal status is final")});
END
""".strip(),
            )
        )

    for _, sql in trigger_specs:
        conn.execute(sql)


def _savepoint_name(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _insert_design_sprint_entry_row(conn, payload: dict) -> int:
    columns = (
        "plan_id",
        "sprint_id",
        "sprint_type",
        "layer",
        "drive",
        "track",
        "pair_status",
        "freeze_gate",
        "subgate",
        "frozen_at",
        "raw_meta",
        "previous_drive",
        "drive_switch_reason",
        "status_on_switch",
        "supersedes_entry_id",
        "correction_reason",
    )
    conn.execute(
        f"INSERT INTO design_sprint_entries ({', '.join(columns)}) "
        f"VALUES ({', '.join(['?'] * len(columns))})",
        tuple(payload.get(column) for column in columns),
    )
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def _insert_design_sprint_artifact_link_row(conn, payload: dict) -> int:
    columns = (
        "sprint_entry_id",
        "artifact_kind",
        "artifact_ref",
        "link_kind",
        "supersedes_entry_id",
        "correction_reason",
    )
    conn.execute(
        f"INSERT INTO design_sprint_artifact_links ({', '.join(columns)}) "
        f"VALUES ({', '.join(['?'] * len(columns))})",
        tuple(payload.get(column) for column in columns),
    )
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def _build_corrected_entry_payload(old_entry: sqlite3.Row, new_data: dict, correction_reason: str) -> dict:
    allowed_keys = {
        "plan_id",
        "sprint_id",
        "sprint_type",
        "layer",
        "drive",
        "track",
        "pair_status",
        "freeze_gate",
        "subgate",
        "frozen_at",
        "raw_meta",
        "previous_drive",
        "drive_switch_reason",
        "status_on_switch",
    }
    unknown_keys = set(new_data) - allowed_keys
    if unknown_keys:
        raise KeyError(f"unknown entry fields: {sorted(unknown_keys)!r}")

    payload = {
        "plan_id": _require_non_empty(new_data.get("plan_id", old_entry["plan_id"]), "plan_id"),
        "sprint_id": new_data.get("sprint_id", old_entry["sprint_id"]),
        "sprint_type": _validate_choice(
            _require_non_empty(new_data.get("sprint_type", old_entry["sprint_type"]), "sprint_type"),
            "sprint_type",
            DESIGN_SPRINT_TYPES,
        ),
        "layer": _validate_choice(
            _require_non_empty(new_data.get("layer", old_entry["layer"]), "layer"),
            "layer",
            DESIGN_SPRINT_LAYERS,
        ),
        "drive": _validate_choice(
            _require_non_empty(new_data.get("drive", old_entry["drive"]), "drive"),
            "drive",
            DESIGN_SPRINT_DRIVES,
        ),
        "track": _validate_optional_choice(new_data.get("track", old_entry["track"]), "track", DESIGN_SPRINT_TRACKS),
        "pair_status": _validate_choice(
            _require_non_empty(new_data.get("pair_status", old_entry["pair_status"]), "pair_status"),
            "pair_status",
            DESIGN_SPRINT_PAIR_STATUSES,
        ),
        "freeze_gate": new_data.get("freeze_gate", old_entry["freeze_gate"]),
        "subgate": new_data.get("subgate", old_entry["subgate"]),
        "frozen_at": new_data.get("frozen_at", old_entry["frozen_at"]),
        "raw_meta": new_data.get("raw_meta", old_entry["raw_meta"]),
        "previous_drive": new_data.get("previous_drive", old_entry["previous_drive"]),
        "drive_switch_reason": new_data.get("drive_switch_reason", old_entry["drive_switch_reason"]),
        "status_on_switch": _validate_optional_choice(
            new_data.get("status_on_switch", old_entry["status_on_switch"]),
            "status_on_switch",
            DESIGN_SPRINT_SWITCH_STATUSES,
        ),
        "supersedes_entry_id": int(old_entry["id"]),
        "correction_reason": correction_reason,
    }
    return payload


def _build_corrected_artifact_link_payload(
    old_link: sqlite3.Row,
    new_data: dict,
    correction_reason: str,
) -> dict:
    allowed_keys = {"sprint_entry_id", "artifact_kind", "artifact_ref", "link_kind"}
    unknown_keys = set(new_data) - allowed_keys
    if unknown_keys:
        raise KeyError(f"unknown artifact link fields: {sorted(unknown_keys)!r}")

    payload = {
        "sprint_entry_id": _validate_positive_int(
            new_data.get("sprint_entry_id", old_link["sprint_entry_id"]),
            "sprint_entry_id",
        ),
        "artifact_kind": _validate_choice(
            _require_non_empty(new_data.get("artifact_kind", old_link["artifact_kind"]), "artifact_kind"),
            "artifact_kind",
            DESIGN_SPRINT_ARTIFACT_KINDS,
        ),
        "artifact_ref": _require_non_empty(new_data.get("artifact_ref", old_link["artifact_ref"]), "artifact_ref"),
        "link_kind": _validate_choice(
            _require_non_empty(new_data.get("link_kind", old_link["link_kind"]), "link_kind"),
            "link_kind",
            DESIGN_SPRINT_ARTIFACT_LINK_KINDS,
        ),
        "supersedes_entry_id": int(old_link["sprint_entry_id"]),
        "correction_reason": correction_reason,
    }
    return payload


# @helix:index id=helix-db.insert-import-run domain=cli/lib summary=import runを挿入する
def insert_import_run(db_path, run_id, source_hash, scope_hash, status="started"):
    """import_run を新規 INSERT する。started_at は epoch seconds。"""
    run_id = _require_non_empty(run_id, "run_id")
    source_hash = _require_non_empty(source_hash, "source_hash")
    scope_hash = _require_non_empty(scope_hash, "scope_hash")
    status = _validate_choice(status, "status", IMPORT_RUN_STATUSES_V10)
    started_at = _epoch_now()

    with _write_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO import_runs (id, started_at, source_hash, scope_hash, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (run_id, started_at, source_hash, scope_hash, status),
        )
        return run_id


# @helix:index id=helix-db.update-import-run domain=cli/lib summary=import runを更新する
def update_import_run(db_path, run_id, status, completed_at=None, imported_rows=0, error_summary=None):
    """import_run を success/failed で更新する。"""
    run_id = _require_non_empty(run_id, "run_id")
    status = _validate_choice(status, "status", ("success", "failed"))
    if completed_at is None:
        completed_at = _epoch_now()
    completed_at = int(completed_at)
    imported_rows = int(imported_rows)
    if imported_rows < 0:
        raise ValueError("imported_rows must be non-negative")

    with _write_connection(db_path) as conn:
        cur = conn.execute(
            "UPDATE import_runs SET status = ?, completed_at = ?, imported_rows = ?, error_summary = ? "
            "WHERE id = ?",
            (status, completed_at, imported_rows, error_summary, run_id),
        )
        return cur.rowcount == 1


# @helix:index id=helix-db.insert-audit-decision domain=cli/lib summary=audit decisionを挿入する
def insert_audit_decision(
    db_path,
    candidate_id,
    schema_version,
    scope_hash,
    decision,
    evidence,
    rationale,
    fail_safe_action,
    import_run_id,
    source_hash,
    decision_hash,
    imported_at=None,
):
    """audit_decision を active 状態で INSERT する。Case A no-op 判定は呼び出し側で行う。"""
    candidate_id = _require_non_empty(candidate_id, "candidate_id")
    schema_version = _validate_positive_int(schema_version, "schema_version")
    scope_hash = _require_non_empty(scope_hash, "scope_hash")
    decision = _validate_choice(decision, "decision", AUDIT_DECISION_DECISIONS_V10)
    if evidence is not None and not isinstance(evidence, (dict, str)):
        raise ValueError("evidence must be a JSON object or JSON string")
    evidence_text = _json_text(evidence, {})
    rationale = _require_non_empty(rationale, "rationale")
    fail_safe_action = _validate_choice(
        fail_safe_action,
        "fail_safe_action",
        AUDIT_DECISION_FAIL_SAFE_ACTIONS_V10,
    )
    import_run_id = _require_non_empty(import_run_id, "import_run_id")
    source_hash = _require_non_empty(source_hash, "source_hash")
    decision_hash = _require_non_empty(decision_hash, "decision_hash")
    imported_at = int(imported_at or _epoch_now())

    with _write_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO audit_decisions "
            "(candidate_id, schema_version, scope_hash, decision, evidence, rationale, "
            "fail_safe_action, status, import_run_id, source_hash, decision_hash, "
            "imported_at, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?)",
            (
                candidate_id,
                schema_version,
                scope_hash,
                decision,
                evidence_text,
                rationale,
                fail_safe_action,
                import_run_id,
                source_hash,
                decision_hash,
                imported_at,
                imported_at,
                imported_at,
            ),
        )
        row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return row_id


# @helix:index id=helix-db.historical-to-active-audit-decision domain=cli/lib summary=historical to active audit decisionを実行する
def historical_to_active_audit_decision(db_path, candidate_id, schema_version, scope_hash):
    """既存 active 行を historical に降格する。"""
    candidate_id = _require_non_empty(candidate_id, "candidate_id")
    schema_version = _validate_positive_int(schema_version, "schema_version")
    _require_non_empty(scope_hash, "scope_hash")
    updated_at = _epoch_now()

    with _write_connection(db_path) as conn:
        cur = conn.execute(
            "UPDATE audit_decisions SET status = 'historical', updated_at = ? "
            "WHERE candidate_id = ? AND schema_version = ? AND status = 'active'",
            (updated_at, candidate_id, schema_version),
        )
        return cur.rowcount


# @helix:index id=helix-db.query-active-audit-decisions domain=cli/lib summary=query active audit decisionsを実行する
def query_active_audit_decisions(db_path, candidate_id=None, schema_version=None):
    """active な audit_decisions を取得する。"""
    where = ["status = 'active'"]
    params = []
    if candidate_id is not None:
        where.append("candidate_id = ?")
        params.append(_require_non_empty(candidate_id, "candidate_id"))
    if schema_version is not None:
        where.append("schema_version = ?")
        params.append(_validate_positive_int(schema_version, "schema_version"))

    conn = _automation_conn(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM audit_decisions WHERE "
            + " AND ".join(where)
            + " ORDER BY candidate_id, schema_version, id",
            params,
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def _automation_conn(db_path):
    _prepare_db_path(db_path)
    conn = _connect(db_path)
    _ensure_schema(conn)
    return conn


# @helix:index id=helix-db.insert-event domain=cli/lib summary=eventを挿入する
def insert_event(db_path, event_name, data, **kwargs):
    """PLAN-005 observability event insert API."""
    event_name = _validate_observable_name(event_name, "event_name")
    severity = _validate_choice(kwargs.get("severity", "info"), "severity", EVENT_SEVERITIES_V9)
    occurred_at = int(kwargs.get("occurred_at") or _epoch_now())
    if data is not None and not isinstance(data, (dict, str)):
        raise ValueError("data must be a JSON object or JSON string")
    data_json = _json_text(data, {})
    source = kwargs.get("source")
    if source is not None:
        source = _require_non_empty(source, "source")

    with _write_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO events (event_name, occurred_at, data_json, source, severity) "
            "VALUES (?, ?, ?, ?, ?)",
            (event_name, occurred_at, data_json, source, severity),
        )
        row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return row_id


# @helix:index id=helix-db.insert-metric domain=cli/lib summary=metricを挿入する
def insert_metric(db_path, metric_name, value, tags=None):
    """PLAN-005 observability metric insert API."""
    metric_name = _validate_observable_name(metric_name, "metric_name")
    metric_value = float(value)
    if tags is not None and not isinstance(tags, (dict, str)):
        raise ValueError("tags must be a JSON object or JSON string")
    recorded_at = int(_epoch_now())

    with _write_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO metrics (metric_name, value, tags_json, recorded_at) VALUES (?, ?, ?, ?)",
            (metric_name, metric_value, _json_text(tags, {}), recorded_at),
        )
        row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return row_id


# @helix:index id=helix-db.acquire-db-lock domain=cli/lib summary=lockを取得または更新する
def acquire_db_lock(
    db_path,
    name,
    pid,
    scope="project",
    timeout=None,
    ttl=None,
    acquired_at=None,
    expires_at=None,
):
    """Acquire or refresh PLAN-005 lock metadata.

    ``timeout`` is kept as a backwards-compatible TTL alias. The file lock
    remains the conflict source of truth.
    """
    name = _require_non_empty(name, "name")
    scope = _validate_choice(scope, "scope", LOCK_SCOPES_V9)
    acquired_at = int(acquired_at or _epoch_now())
    ttl_seconds = ttl if ttl is not None else timeout
    if expires_at is None and ttl_seconds is not None:
        expires_at = acquired_at + int(ttl_seconds)
    if expires_at is not None:
        expires_at = int(expires_at)

    with _write_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO locks (name, pid, acquired_at, expires_at, scope)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                pid = excluded.pid,
                acquired_at = excluded.acquired_at,
                expires_at = excluded.expires_at,
                scope = excluded.scope
            """,
            (name, int(pid), acquired_at, expires_at, scope),
        )
        return True


# @helix:index id=helix-db.release-db-lock domain=cli/lib summary=lockを解放する
def release_db_lock(db_path, name, pid):
    """PLAN-005 lock release API。pid 一致時のみ解放する。"""
    name = _require_non_empty(name, "name")

    with _write_connection(db_path) as conn:
        cur = conn.execute("DELETE FROM locks WHERE name = ? AND pid = ?", (name, int(pid)))
        return cur.rowcount == 1


# @helix:index id=helix-db.enqueue-job domain=cli/lib summary=jobをenqueueする
def enqueue_job(db_path, task_type, task_payload, priority=5, **kwargs):
    """PLAN-005 job-queue enqueue API。worker 実行は job_queue_helper が担当する。"""
    task_type = _validate_choice(task_type, "task_type", TASK_TYPES_V9)
    task_payload = _require_non_empty(task_payload, "task_payload")
    job_id = kwargs.get("job_id") or kwargs.get("id") or str(uuid.uuid4())
    created_at = int(kwargs.get("created_at") or _epoch_now())

    with _write_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO jobs "
            "(id, task_type, task_payload, priority, status, created_at, max_retries, delay_until) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                job_id,
                task_type,
                task_payload,
                int(priority),
                _validate_choice(kwargs.get("status", "pending"), "status", AUTOMATION_STATUSES_V9),
                created_at,
                int(kwargs.get("max_retries", 3)),
                kwargs.get("delay_until"),
            ),
        )
        return job_id


# @helix:index id=helix-db.add-schedule domain=cli/lib summary=scheduleを追加する
def add_schedule(db_path, schedule_expr, task_type, task_payload, **kwargs):
    """PLAN-005 scheduler add API。next_run_at 計算は scheduler_helper が担当する。"""
    schedule_expr = _require_non_empty(schedule_expr, "schedule_expr")
    task_type = _validate_choice(task_type, "task_type", TASK_TYPES_V9)
    task_payload = _require_non_empty(task_payload, "task_payload")
    schedule_id = kwargs.get("schedule_id") or kwargs.get("id") or str(uuid.uuid4())
    now = int(kwargs.get("created_at") or _epoch_now())

    with _write_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO schedules "
            "(id, schedule_expr, task_type, task_payload, status, next_run_at, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                schedule_id,
                schedule_expr,
                task_type,
                task_payload,
                _validate_choice(kwargs.get("status", "pending"), "status", AUTOMATION_STATUSES_V9),
                kwargs.get("next_run_at"),
                now,
                int(kwargs.get("updated_at") or now),
            ),
        )
        return schedule_id


def latest_task_run_id(db_path, task_id):
    conn = _connect(db_path)
    row = conn.execute(
        "SELECT id FROM task_runs WHERE task_id = ? ORDER BY id DESC LIMIT 1",
        (task_id,),
    ).fetchone()
    conn.close()
    print(row[0] if row else "")


def record_selection(db_path, data):
    with _write_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO task_selections (plan_id, plan_goal, selected_tasks, "
            "available_tasks, selection_rationale, review_status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (data['plan_id'], data['plan_goal'],
             json.dumps(data.get('selected_tasks', [])),
             json.dumps(data.get('available_tasks', [])),
             data.get('selection_rationale', ''),
             'pending')
        )
        sel_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    print(sel_id)


# @helix:index id=helix-db.update-review domain=cli/lib summary=reviewを更新する
def update_review(db_path, data):
    with _write_connection(db_path) as conn:
        conn.execute(
            "UPDATE task_selections SET review_status=?, review_result=?, review_suggestions=? "
            "WHERE id=?",
            (data['review_status'], data.get('review_result', ''),
             data.get('review_suggestions', ''), data['selection_id'])
        )


def report(db_path, report_type='summary', report_date=None):
    conn = _connect(db_path)
    conn.row_factory = sqlite3.Row

    if report_type == 'summary':
        print("=== HELIX Log Summary ===\n")

        # タスク実行統計
        row = conn.execute(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed, "
            "SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed "
            "FROM task_runs"
        ).fetchone()
        print(f"Tasks: {row['total']} total, {row['completed']} completed, {row['failed']} failed")

        # アクション統計
        row = conn.execute(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN status='passed' THEN 1 ELSE 0 END) as passed, "
            "SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed "
            "FROM action_logs"
        ).fetchone()
        print(f"Actions: {row['total']} total, {row['passed']} passed, {row['failed']} failed")

        # オブザーバー統計
        row = conn.execute(
            "SELECT COUNT(*) as total, "
            "SUM(passed) as passed "
            "FROM observations"
        ).fetchone()
        if row['total'] > 0:
            rate = (row['passed'] / row['total']) * 100
            print(f"Observations: {row['total']} checks, {rate:.0f}% pass rate")

        # フィードバック統計
        rows = conn.execute(
            "SELECT feedback_type, COUNT(*) as cnt FROM feedback GROUP BY feedback_type ORDER BY cnt DESC"
        ).fetchall()
        if rows:
            print(f"\nFeedback:")
            for r in rows:
                print(f"  {r['feedback_type']}: {r['cnt']}")

    elif report_type == 'tasks':
        print("=== Task History ===\n")
        rows = conn.execute(
            "SELECT task_id, task_type, role, status, started_at FROM task_runs ORDER BY id DESC LIMIT 20"
        ).fetchall()
        print(f"{'ID':<6} {'Task':<30} {'Role':<12} {'Status':<10} {'Date'}")
        for r in rows:
            print(f"{r['task_id']:<6} {r['task_type']:<30} {r['role']:<12} {r['status']:<10} {r['started_at'][:10]}")

    elif report_type == 'actions':
        print("=== Action Type Performance ===\n")
        rows = conn.execute(
            "SELECT action_type, COUNT(*) as total, "
            "SUM(CASE WHEN status='passed' THEN 1 ELSE 0 END) as passed, "
            "SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed "
            "FROM action_logs GROUP BY action_type ORDER BY failed DESC"
        ).fetchall()
        print(f"{'Action Type':<25} {'Total':>6} {'Pass':>6} {'Fail':>6} {'Rate':>8}")
        for r in rows:
            rate = (r['passed'] / r['total'] * 100) if r['total'] > 0 else 0
            print(f"{r['action_type']:<25} {r['total']:>6} {r['passed']:>6} {r['failed']:>6} {rate:>7.0f}%")

    elif report_type == 'feedback':
        print("=== Feedback Analysis ===\n")

        # カテゴリ別
        rows = conn.execute(
            "SELECT category, COUNT(*) as cnt, "
            "GROUP_CONCAT(description, ' | ') as descs "
            "FROM feedback WHERE category != '' "
            "GROUP BY category ORDER BY cnt DESC"
        ).fetchall()
        for r in rows:
            print(f"[{r['category']}] ({r['cnt']} 件)")
            for d in r['descs'].split(' | ')[:3]:
                print(f"  - {d[:80]}")
            print()

    elif report_type == 'quality':
        print("=== Task Selection Quality ===\n")

        # タスクタイプ別の observation pass 率
        rows = conn.execute(
            "SELECT t.task_type, COUNT(o.id) as checks, "
            "SUM(o.passed) as passed, "
            "ROUND(CAST(SUM(o.passed) AS REAL) / COUNT(o.id) * 100, 1) as rate "
            "FROM task_runs t JOIN observations o ON t.id = o.task_run_id "
            "GROUP BY t.task_type ORDER BY rate ASC"
        ).fetchall()
        print(f"{'Task Type':<30} {'Checks':>7} {'Pass':>6} {'Rate':>8}")
        for r in rows:
            flag = " ← LOW" if r['rate'] < 70 else ""
            print(f"{r['task_type']:<30} {r['checks']:>7} {r['passed']:>6} {r['rate']:>7.1f}%{flag}")

        # フィードバックが多いタスクタイプ
        print("\nMost corrected task types:")
        rows = conn.execute(
            "SELECT t.task_type, COUNT(f.id) as corrections "
            "FROM task_runs t JOIN feedback f ON t.id = f.task_run_id "
            "WHERE f.feedback_type = 'correction' "
            "GROUP BY t.task_type ORDER BY corrections DESC LIMIT 5"
        ).fetchall()
        for r in rows:
            print(f"  {r['task_type']}: {r['corrections']} corrections")

    elif report_type == 'selections':
        print("=== Task Selection History ===\n")
        rows = conn.execute(
            "SELECT id, plan_id, plan_goal, selected_tasks, review_status, "
            "review_result, review_suggestions, created_at "
            "FROM task_selections ORDER BY id DESC LIMIT 10"
        ).fetchall()
        for r in rows:
            status_icon = {'approved': '✓', 'rejected': '✗', 'revised': '↻', 'pending': '?'}.get(r['review_status'], '?')
            selected = json.loads(r['selected_tasks']) if r['selected_tasks'] else []
            print(f"{status_icon} Plan #{r['plan_id']} — {r['plan_goal']} ({r['created_at'][:10]})")
            print(f"  Selected: {len(selected)} tasks — {', '.join(selected[:5])}{'...' if len(selected) > 5 else ''}")
            print(f"  Review: {r['review_status']}")
            if r['review_result']:
                print(f"  Result: {r['review_result'][:100]}")
            if r['review_suggestions']:
                print(f"  Suggestions: {r['review_suggestions'][:100]}")
            print()

    elif report_type == 'session':
        target_date = report_date or datetime.now().date().isoformat()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", target_date):
            raise ValueError("session report date must be YYYY-MM-DD")

        print("=== Session Report ===\n")
        print(f"Date: {target_date}")

        finished = conn.execute(
            "SELECT COUNT(*) as cnt FROM cost_log "
            "WHERE role IN ('claude-code', 'opus-pm') AND date(created_at)=?",
            (target_date,),
        ).fetchone()["cnt"]
        print(f"終了 {finished} 回")

        print("\n[hook_events]")
        rows = conn.execute(
            "SELECT event_type, COUNT(*) as cnt FROM hook_events "
            "WHERE date(created_at)=? GROUP BY event_type ORDER BY event_type",
            (target_date,),
        ).fetchall()
        if rows:
            for r in rows:
                print(f"  {r['event_type']}: {r['cnt']}")
        else:
            print("  (なし)")

        print("\n[gate_runs]")
        rows = conn.execute(
            "SELECT gate, result, COUNT(*) as cnt FROM gate_runs "
            "WHERE date(created_at)=? GROUP BY gate, result ORDER BY gate, result",
            (target_date,),
        ).fetchall()
        if rows:
            for r in rows:
                print(f"  {r['gate']} {r['result']}: {r['cnt']}")
        else:
            print("  (なし)")

        print("\n[cost_log]")
        rows = conn.execute(
            "SELECT role, model, COUNT(*) as cnt FROM cost_log "
            "WHERE date(created_at)=? GROUP BY role, model ORDER BY role, model",
            (target_date,),
        ).fetchall()
        if rows:
            for r in rows:
                print(f"  {r['role']} / {r['model']}: {r['cnt']}")
        else:
            print("  (なし)")

    conn.close()


def _quote_identifier(name):
    return '"' + str(name).replace('"', '""') + '"'


# @helix:index id=helix-db.export-json domain=cli/lib summary=jsonを出力する
def export_json(db_path, output_path):
    """DB 全テーブルを JSON にエクスポート"""
    conn = get_connection(db_path=db_path, timeout=DEFAULT_SQLITE_TIMEOUT_SEC)
    tables = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    ]
    data = {}
    for table in tables:
        table_ident = _quote_identifier(table)
        rows = conn.execute(f"SELECT * FROM {table_ident}").fetchall()
        columns = [
            col[1]
            for col in conn.execute(f"PRAGMA table_info({table_ident})").fetchall()
        ]
        data[table] = [dict(zip(columns, row)) for row in rows]
    conn.close()

    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Exported: {output_path}")


def query_design_review_pair(db_path, plan_id: str, layer: str) -> dict:
    """Return dict with vertical_passed and horizontal_passed bools."""
    conn = get_connection(db_path)
    try:
        vertical_row = conn.execute(
            "SELECT 1 FROM design_review WHERE plan_id=? AND layer=? AND review_axis='vertical' AND verdict='passed' LIMIT 1",
            (plan_id, layer),
        ).fetchone()
        horizontal_row = conn.execute(
            "SELECT 1 FROM design_review WHERE plan_id=? AND layer=? AND review_axis='horizontal' AND verdict='passed' LIMIT 1",
            (plan_id, layer),
        ).fetchone()
        return {"vertical_passed": vertical_row is not None, "horizontal_passed": horizontal_row is not None}
    finally:
        conn.close()


# @helix:index id=helix-db.switch-drive-for-sprint domain=cli/lib summary=drive切替をappend-onlyで記録する
def switch_drive_for_sprint(
    db_path,
    plan_id,
    sprint_type,
    layer,
    old_drive,
    new_drive,
    reason,
    status_on_switch,
):
    """drive 切替を append-only で記録し、旧 entry に切替状態を残す。"""
    plan_id = _require_non_empty(plan_id, "plan_id")
    sprint_type = _validate_choice(
        _require_non_empty(sprint_type, "sprint_type"),
        "sprint_type",
        ("architecture", "detailed", "functional", "impl"),
    )
    layer = _validate_choice(
        _require_non_empty(layer, "layer"),
        "layer",
        ("architecture", "detailed", "functional"),
    )
    old_drive = _validate_choice(_require_non_empty(old_drive, "old_drive"), "old_drive", ("be", "fe", "db", "fullstack"))
    new_drive = _validate_choice(_require_non_empty(new_drive, "new_drive"), "new_drive", ("be", "fe", "db", "fullstack"))
    reason = _require_non_empty(reason, "reason")
    status_on_switch = _validate_choice(
        _require_non_empty(status_on_switch, "status_on_switch"),
        "status_on_switch",
        DESIGN_SPRINT_SWITCH_STATUSES,
    )
    if old_drive == new_drive:
        raise ValueError("old_drive and new_drive must differ")

    with _write_connection(db_path) as conn:
        duplicate_target = conn.execute(
            """
            SELECT id
            FROM design_sprint_entries
            WHERE plan_id = ? AND sprint_type = ? AND layer = ? AND drive = ? AND status_on_switch IS NULL
            ORDER BY id DESC
            LIMIT 1
            """,
            (plan_id, sprint_type, layer, new_drive),
        ).fetchone()
        if duplicate_target is not None:
            raise ValueError("active entry for new_drive already exists")

        old_entry = conn.execute(
            """
            SELECT *
            FROM design_sprint_entries
            WHERE plan_id = ? AND sprint_type = ? AND layer = ? AND drive = ? AND status_on_switch IS NULL
            ORDER BY id DESC
            LIMIT 1
            """,
            (plan_id, sprint_type, layer, old_drive),
        ).fetchone()
        if old_entry is None:
            raise ValueError("active entry for old_drive does not exist")

        conn.execute(
            "UPDATE design_sprint_entries SET status_on_switch = ?, updated_at = datetime('now') WHERE id = ?",
            (status_on_switch, old_entry["id"]),
        )
        conn.execute(
            """
            INSERT INTO design_sprint_entries (
                plan_id,
                sprint_id,
                sprint_type,
                layer,
                drive,
                previous_drive,
                drive_switch_reason,
                track,
                raw_meta
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                old_entry["plan_id"],
                old_entry["sprint_id"],
                old_entry["sprint_type"],
                old_entry["layer"],
                new_drive,
                old_drive,
                reason,
                old_entry["track"],
                old_entry["raw_meta"],
            ),
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


# @helix:index id=helix-db.void-entry-with-correction domain=cli/lib summary=design sprint entry訂正をappend-onlyで追加する
def void_entry_with_correction(conn, old_entry_id, new_data, correction_reason):
    """旧 entry を void し、訂正内容を append-only で追加する。"""
    old_entry_id = _validate_positive_int(old_entry_id, "old_entry_id")
    new_data = _validate_dict_payload(new_data, "new_data")
    correction_reason = _require_non_empty(correction_reason, "correction_reason")

    savepoint = _savepoint_name("void_entry")
    conn.execute(f"SAVEPOINT {savepoint}")
    try:
        old_entry = conn.execute(
            "SELECT * FROM design_sprint_entries WHERE id = ?",
            (old_entry_id,),
        ).fetchone()
        if old_entry is None:
            raise ValueError("old_entry_id does not exist")
        if old_entry["voided_at"] is not None:
            raise ValueError("old entry is already voided")

        payload = _build_corrected_entry_payload(old_entry, new_data, correction_reason)
        conn.execute(
            "UPDATE design_sprint_entries SET voided_at = datetime('now') WHERE id = ?",
            (old_entry_id,),
        )
        new_entry_id = _insert_design_sprint_entry_row(conn, payload)
        conn.execute(f"RELEASE SAVEPOINT {savepoint}")
        return new_entry_id
    except Exception:
        conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
        conn.execute(f"RELEASE SAVEPOINT {savepoint}")
        raise


# @helix:index id=helix-db.void-artifact-link-with-correction domain=cli/lib summary=artifact link訂正をappend-onlyで追加する
def void_artifact_link_with_correction(conn, old_link_rowid, new_data, correction_reason):
    """旧 artifact link を void し、訂正内容を append-only で追加する。"""
    old_link_rowid = _validate_positive_int(old_link_rowid, "old_link_rowid")
    new_data = _validate_dict_payload(new_data, "new_data")
    correction_reason = _require_non_empty(correction_reason, "correction_reason")

    savepoint = _savepoint_name("void_artifact_link")
    conn.execute(f"SAVEPOINT {savepoint}")
    try:
        old_link = conn.execute(
            "SELECT rowid AS link_rowid, * FROM design_sprint_artifact_links WHERE rowid = ?",
            (old_link_rowid,),
        ).fetchone()
        if old_link is None:
            raise ValueError("old_link_rowid does not exist")
        if old_link["voided_at"] is not None:
            raise ValueError("old artifact link is already voided")

        payload = _build_corrected_artifact_link_payload(old_link, new_data, correction_reason)
        conn.execute(
            "UPDATE design_sprint_artifact_links SET voided_at = datetime('now') WHERE rowid = ?",
            (old_link_rowid,),
        )
        new_link_rowid = _insert_design_sprint_artifact_link_row(conn, payload)
        conn.execute(f"RELEASE SAVEPOINT {savepoint}")
        return new_link_rowid
    except Exception:
        conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
        conn.execute(f"RELEASE SAVEPOINT {savepoint}")
        raise


# @helix:index id=helix-db.list-active-entries domain=cli/lib summary=active design sprint entryを一覧する
def list_active_entries(conn, plan_id, sprint_type, layer):
    """void されていない design sprint entry を返す。"""
    plan_id = _require_non_empty(plan_id, "plan_id")
    sprint_type = _validate_choice(
        _require_non_empty(sprint_type, "sprint_type"),
        "sprint_type",
        DESIGN_SPRINT_TYPES,
    )
    layer = _validate_choice(
        _require_non_empty(layer, "layer"),
        "layer",
        DESIGN_SPRINT_LAYERS,
    )
    return conn.execute(
        """
        SELECT *
        FROM design_sprint_entries
        WHERE plan_id = ? AND sprint_type = ? AND layer = ? AND voided_at IS NULL
        ORDER BY id
        """,
        (plan_id, sprint_type, layer),
    ).fetchall()


# @helix:index id=helix-db.query-functional-freeze-status domain=cli/lib summary=functional freeze状態を集計する
def query_functional_freeze_status(conn, plan_id: str, drive: str) -> dict:
    """指定 (plan_id, drive) の functional_freeze 状態を返す。"""
    rows = conn.execute(
        """
        SELECT pair_status, COUNT(*) AS cnt
        FROM design_sprint_entries
        WHERE plan_id = ? AND drive = ?
          AND sprint_type = 'functional' AND layer = 'functional'
        GROUP BY pair_status
        """,
        (plan_id, drive),
    ).fetchall()

    counts = {str(row["pair_status"]): int(row["cnt"]) for row in rows}
    total = sum(counts.values())
    paired = counts.get("paired", 0)
    pending = counts.get("pending", 0) + counts.get("design_only", 0) + counts.get("test_only", 0)
    failed = counts.get("failed", 0)

    if total == 0:
        verdict = "missing"
    elif failed > 0 or pending > 0:
        verdict = "failed"
    else:
        verdict = "passed"

    return {
        "plan_id": plan_id,
        "drive": drive,
        "functional_pair_count": total,
        "paired_count": paired,
        "pending_count": pending,
        "failed_count": failed,
        "verdict": verdict,
    }


# @helix:index id=helix-db.main domain=cli/lib summary=mainを実行する
def main():
    if len(sys.argv) < 2:
        print("Usage: helix_db.py <command> <db_path> [args]", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]

    try:
        if cmd == 'init':
            db_path = sys.argv[2] if len(sys.argv) > 2 else resolve_default_db_path()
            init_db(db_path)
        elif cmd == 'insert':
            if len(sys.argv) == 4:
                db_path = resolve_default_db_path()
                table = sys.argv[2]
                payload = json.loads(sys.argv[3])
            elif len(sys.argv) == 5:
                db_path = sys.argv[2]
                table = sys.argv[3]
                payload = json.loads(sys.argv[4])
            else:
                print("Usage: helix_db.py insert [<db_path>] <table> <json>", file=sys.stderr)
                sys.exit(1)
            insert_row(db_path, table, payload)
        elif len(sys.argv) < 3:
            print("Usage: helix_db.py <command> <db_path> [args]", file=sys.stderr)
            sys.exit(1)
        else:
            db_path = sys.argv[2]
            if cmd == 'record-task':
                record_task(db_path, json.loads(sys.argv[3]))
            elif cmd == 'record-action':
                record_action(db_path, json.loads(sys.argv[3]))
            elif cmd == 'record-observation':
                record_observation(db_path, json.loads(sys.argv[3]))
            elif cmd == 'record-feedback':
                record_feedback(db_path, json.loads(sys.argv[3]))
            elif cmd == 'record-invocation':
                record_invocation(db_path, json.loads(sys.argv[3]))
            elif cmd == 'record-feedback-argv':
                record_feedback_argv(
                    db_path,
                    sys.argv[3],
                    sys.argv[4],
                    sys.argv[5],
                    sys.argv[6],
                    sys.argv[7] if len(sys.argv) > 7 else 'medium',
                    sys.argv[8] if len(sys.argv) > 8 else '',
                )
            elif cmd == 'latest-task-run':
                latest_task_run_id(db_path, sys.argv[3])
            elif cmd == 'record-selection':
                record_selection(db_path, json.loads(sys.argv[3]))
            elif cmd == 'update-review':
                update_review(db_path, json.loads(sys.argv[3]))
            elif cmd == 'report':
                report_type = sys.argv[3] if len(sys.argv) > 3 else 'summary'
                report_date = sys.argv[4] if len(sys.argv) > 4 else None
                report(db_path, report_type, report_date)
            elif cmd == 'export-json':
                export_json(db_path, sys.argv[3])
            else:
                print(f"Unknown command: {cmd}", file=sys.stderr)
                sys.exit(1)
    except (json.JSONDecodeError, IndexError, KeyError, ValueError) as e:
        print(f"エラー: 入力形式が不正です — {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass  # Python < 3.7
    main()
