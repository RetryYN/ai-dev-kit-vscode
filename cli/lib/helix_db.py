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
CURRENT_SCHEMA_VERSION = 7


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
