#!/usr/bin/env python3
"""HELIX ログデータベース — SQLite ベースのタスク実行・評価・改善追跡

責務: HELIX の実行ログを SQLite に永続化し、集計/参照 API を提供する。

Usage:
  python3 helix_db.py init <db_path>
  python3 helix_db.py record-task <db> <json>
  python3 helix_db.py record-action <db> <json>
  python3 helix_db.py record-observation <db> <json>
  python3 helix_db.py record-feedback <db> <json>
  python3 helix_db.py record-feedback-argv <db> <task_run_id_or_0> <type> <category> <desc> [impact] [resolution]
  python3 helix_db.py latest-task-run <db> <task_id>
  python3 helix_db.py report <db> [summary|tasks|actions|feedback|quality]
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
from datetime import datetime
from pathlib import Path


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
CURRENT_SCHEMA_VERSION = 11


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


def _prepare_db_path(db_path):
    parent_dir = os.path.dirname(os.path.abspath(db_path))
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)


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


def _create_requirements_tables(conn):
    conn.executescript(REQUIREMENTS_SCHEMA)


def _create_accuracy_score_table(conn):
    conn.executescript(ACCURACY_SCORE_SCHEMA)


def _create_infra_tables_v9(conn):
    conn.executescript(INFRA_SCHEMA_V9)


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


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _has_column(conn, table_name, column_name):
    if not _IDENTIFIER_RE.match(str(table_name)):
        raise ValueError(f"invalid table name: {table_name!r}")
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)


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


def _migrate_skill_usage_stdout_v6(conn):
    if not _has_column(conn, "skill_usage", "result_stdout"):
        conn.execute("ALTER TABLE skill_usage ADD COLUMN result_stdout TEXT")
    if not _has_column(conn, "skill_usage", "result_stderr"):
        conn.execute("ALTER TABLE skill_usage ADD COLUMN result_stderr TEXT")


def _migrate_skill_usage_v7(conn):
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
        # v8→v9: 5 infra テーブル追加 (PLAN-005 scheduler/job-queue/lock/observability)
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
        conn.commit()


def _ensure_schema(conn):
    conn.executescript(SCHEMA)
    conn.executescript(SCHEMA_VERSION_SCHEMA)
    migrate(conn)


def init_db(db_path):
    _prepare_db_path(db_path)
    conn = _connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    _ensure_schema(conn)
    conn.commit()
    conn.close()
    print(f"DB initialized: {db_path}")


def resolve_default_db_path():
    env_path = os.environ.get('HELIX_DB_PATH', '').strip()
    if env_path:
        return env_path
    project_root = os.environ.get('HELIX_PROJECT_ROOT', '').strip()
    if project_root:
        return os.path.join(project_root, '.helix', 'helix.db')
    return os.path.join(os.getcwd(), '.helix', 'helix.db')


def insert_row(db_path, table, data):
    if not isinstance(data, dict):
        raise ValueError('insert payload must be a JSON object')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', table):
        raise ValueError(f'invalid table name: {table}')

    _prepare_db_path(db_path)
    conn = _connect(db_path)
    _ensure_schema(conn)

    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    if not rows:
        conn.close()
        raise ValueError(f'unknown table: {table}')

    valid_columns = {row[1] for row in rows}
    payload = dict(data)
    if 'created_at' in valid_columns and 'created_at' not in payload:
        payload['created_at'] = datetime.now().isoformat()

    if not payload:
        conn.close()
        raise ValueError('insert payload is empty')

    for key in payload:
        if key not in valid_columns:
            conn.close()
            raise KeyError(f'unknown column: {table}.{key}')

    columns = list(payload.keys())
    values = [payload[col] for col in columns]
    placeholders = ', '.join(['?'] * len(columns))
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    conn.execute(sql, values)
    row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    print(row_id)


def record_task(db_path, data):
    conn = _connect(db_path)
    conn.execute(
        "INSERT INTO task_runs (task_id, task_type, plan_goal, role, status, started_at, output_log) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (data['task_id'], data['task_type'], data.get('plan_goal', ''),
         data['role'], data.get('status', 'running'),
         data.get('started_at', datetime.now().isoformat()),
         data.get('output_log', ''))
    )
    run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    print(run_id)


def record_action(db_path, data):
    conn = _connect(db_path)
    conn.execute(
        "INSERT INTO action_logs (task_run_id, action_index, action_type, action_desc, status, evidence) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (data['task_run_id'], data['action_index'], data['action_type'],
         data.get('action_desc', ''), data.get('status', 'pending'),
         data.get('evidence', ''))
    )
    action_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    print(action_id)


def record_observation(db_path, data):
    conn = _connect(db_path)
    conn.execute(
        "INSERT INTO observations (task_run_id, action_log_id, action_type, "
        "expected_keywords, matched_keywords, passed, reason) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (data['task_run_id'], data.get('action_log_id'),
         data['action_type'], json.dumps(data.get('expected_keywords', [])),
         json.dumps(data.get('matched_keywords', [])),
         1 if data.get('passed') else 0, data.get('reason', ''))
    )
    conn.commit()
    conn.close()


def record_feedback(db_path, data):
    conn = _connect(db_path)
    conn.execute(
        "INSERT INTO feedback (task_run_id, feedback_type, category, description, impact, resolution) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (data.get('task_run_id'), data['feedback_type'],
         data.get('category', ''), data['description'],
         data.get('impact', 'medium'), data.get('resolution', ''))
    )
    conn.commit()
    conn.close()
    print("Feedback recorded")


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

    _prepare_db_path(db_path)
    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
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
        conn.commit()
        return row_id
    finally:
        conn.close()


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


def insert_import_run(db_path, run_id, source_hash, scope_hash, status="started"):
    """import_run を新規 INSERT する。started_at は epoch seconds。"""
    run_id = _require_non_empty(run_id, "run_id")
    source_hash = _require_non_empty(source_hash, "source_hash")
    scope_hash = _require_non_empty(scope_hash, "scope_hash")
    status = _validate_choice(status, "status", IMPORT_RUN_STATUSES_V10)
    started_at = _epoch_now()

    conn = _automation_conn(db_path)
    try:
        conn.execute(
            "INSERT INTO import_runs (id, started_at, source_hash, scope_hash, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (run_id, started_at, source_hash, scope_hash, status),
        )
        conn.commit()
        return run_id
    finally:
        conn.close()


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

    conn = _automation_conn(db_path)
    try:
        cur = conn.execute(
            "UPDATE import_runs SET status = ?, completed_at = ?, imported_rows = ?, error_summary = ? "
            "WHERE id = ?",
            (status, completed_at, imported_rows, error_summary, run_id),
        )
        conn.commit()
        return cur.rowcount == 1
    finally:
        conn.close()


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

    conn = _automation_conn(db_path)
    try:
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
        conn.commit()
        return row_id
    finally:
        conn.close()


def historical_to_active_audit_decision(db_path, candidate_id, schema_version, scope_hash):
    """既存 active 行を historical に降格する。"""
    candidate_id = _require_non_empty(candidate_id, "candidate_id")
    schema_version = _validate_positive_int(schema_version, "schema_version")
    _require_non_empty(scope_hash, "scope_hash")
    updated_at = _epoch_now()

    conn = _automation_conn(db_path)
    try:
        cur = conn.execute(
            "UPDATE audit_decisions SET status = 'historical', updated_at = ? "
            "WHERE candidate_id = ? AND schema_version = ? AND status = 'active'",
            (updated_at, candidate_id, schema_version),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


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

    conn = _automation_conn(db_path)
    try:
        conn.execute(
            "INSERT INTO events (event_name, occurred_at, data_json, source, severity) "
            "VALUES (?, ?, ?, ?, ?)",
            (event_name, occurred_at, data_json, source, severity),
        )
        row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        return row_id
    finally:
        conn.close()


def insert_metric(db_path, metric_name, value, tags=None):
    """PLAN-005 observability metric insert API."""
    metric_name = _validate_observable_name(metric_name, "metric_name")
    metric_value = float(value)
    if tags is not None and not isinstance(tags, (dict, str)):
        raise ValueError("tags must be a JSON object or JSON string")
    recorded_at = int(_epoch_now())

    conn = _automation_conn(db_path)
    try:
        conn.execute(
            "INSERT INTO metrics (metric_name, value, tags_json, recorded_at) VALUES (?, ?, ?, ?)",
            (metric_name, metric_value, _json_text(tags, {}), recorded_at),
        )
        row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        return row_id
    finally:
        conn.close()


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

    ``timeout`` is kept as a backwards-compatible TTL alias for the Sprint 1
    skeleton. The file lock remains the conflict source of truth.
    """
    name = _require_non_empty(name, "name")
    scope = _validate_choice(scope, "scope", LOCK_SCOPES_V9)
    acquired_at = int(acquired_at or _epoch_now())
    ttl_seconds = ttl if ttl is not None else timeout
    if expires_at is None and ttl_seconds is not None:
        expires_at = acquired_at + int(ttl_seconds)
    if expires_at is not None:
        expires_at = int(expires_at)

    conn = _automation_conn(db_path)
    try:
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
        conn.commit()
        return True
    finally:
        conn.close()


def release_db_lock(db_path, name, pid):
    """PLAN-005 lock の最小 release API。pid 一致時のみ解放する。"""
    name = _require_non_empty(name, "name")

    conn = _automation_conn(db_path)
    try:
        cur = conn.execute("DELETE FROM locks WHERE name = ? AND pid = ?", (name, int(pid)))
        conn.commit()
        return cur.rowcount == 1
    finally:
        conn.close()


def enqueue_job(db_path, task_type, task_payload, priority=5, **kwargs):
    """PLAN-005 job-queue の最小 enqueue API。worker 実行は後続 Sprint で実装する。"""
    task_type = _validate_choice(task_type, "task_type", TASK_TYPES_V9)
    task_payload = _require_non_empty(task_payload, "task_payload")
    job_id = kwargs.get("job_id") or kwargs.get("id") or str(uuid.uuid4())
    created_at = int(kwargs.get("created_at") or _epoch_now())

    conn = _automation_conn(db_path)
    try:
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
        conn.commit()
        return job_id
    finally:
        conn.close()


def add_schedule(db_path, schedule_expr, task_type, task_payload, **kwargs):
    """PLAN-005 scheduler の最小 add API。next_run_at 計算は後続 Sprint で実装する。"""
    schedule_expr = _require_non_empty(schedule_expr, "schedule_expr")
    task_type = _validate_choice(task_type, "task_type", TASK_TYPES_V9)
    task_payload = _require_non_empty(task_payload, "task_payload")
    schedule_id = kwargs.get("schedule_id") or kwargs.get("id") or str(uuid.uuid4())
    now = int(kwargs.get("created_at") or _epoch_now())

    conn = _automation_conn(db_path)
    try:
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
        conn.commit()
        return schedule_id
    finally:
        conn.close()


def latest_task_run_id(db_path, task_id):
    conn = _connect(db_path)
    row = conn.execute(
        "SELECT id FROM task_runs WHERE task_id = ? ORDER BY id DESC LIMIT 1",
        (task_id,),
    ).fetchone()
    conn.close()
    print(row[0] if row else "")


def record_selection(db_path, data):
    conn = _connect(db_path)
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
    conn.commit()
    conn.close()
    print(sel_id)


def update_review(db_path, data):
    conn = _connect(db_path)
    conn.execute(
        "UPDATE task_selections SET review_status=?, review_result=?, review_suggestions=? "
        "WHERE id=?",
        (data['review_status'], data.get('review_result', ''),
         data.get('review_suggestions', ''), data['selection_id'])
    )
    conn.commit()
    conn.close()


def report(db_path, report_type='summary'):
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

    conn.close()


def _quote_identifier(name):
    return '"' + str(name).replace('"', '""') + '"'


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
                report(db_path, report_type)
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
