#!/usr/bin/env python3
"""HELIX ログデータベース — SQLite ベースのタスク実行・評価・改善追跡

Usage:
  python3 helix_db.py init <db_path>
  python3 helix_db.py record-task <db> <json>
  python3 helix_db.py record-action <db> <json>
  python3 helix_db.py record-observation <db> <json>
  python3 helix_db.py record-feedback <db> <json>
  python3 helix_db.py report <db> [summary|tasks|actions|feedback|quality]
"""

import sqlite3
import json
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

-- インデックス
CREATE INDEX IF NOT EXISTS idx_task_runs_type ON task_runs(task_type);
CREATE INDEX IF NOT EXISTS idx_task_runs_role ON task_runs(role);
CREATE INDEX IF NOT EXISTS idx_action_logs_type ON action_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_feedback_category ON feedback(category);
CREATE INDEX IF NOT EXISTS idx_task_selections_plan ON task_selections(plan_id);
"""


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"DB initialized: {db_path}")


def record_task(db_path, data):
    conn = sqlite3.connect(db_path)
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
    conn = sqlite3.connect(db_path)
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
    conn = sqlite3.connect(db_path)
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
    conn = sqlite3.connect(db_path)
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


def record_selection(db_path, data):
    conn = sqlite3.connect(db_path)
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
    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE task_selections SET review_status=?, review_result=?, review_suggestions=? "
        "WHERE id=?",
        (data['review_status'], data.get('review_result', ''),
         data.get('review_suggestions', ''), data['selection_id'])
    )
    conn.commit()
    conn.close()


def report(db_path, report_type='summary'):
    conn = sqlite3.connect(db_path)
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


def main():
    if len(sys.argv) < 3:
        print("Usage: helix_db.py <command> <db_path> [args]", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    db_path = sys.argv[2]

    if cmd == 'init':
        init_db(db_path)
    elif cmd == 'record-task':
        record_task(db_path, json.loads(sys.argv[3]))
    elif cmd == 'record-action':
        record_action(db_path, json.loads(sys.argv[3]))
    elif cmd == 'record-observation':
        record_observation(db_path, json.loads(sys.argv[3]))
    elif cmd == 'record-feedback':
        record_feedback(db_path, json.loads(sys.argv[3]))
    elif cmd == 'record-selection':
        record_selection(db_path, json.loads(sys.argv[3]))
    elif cmd == 'update-review':
        update_review(db_path, json.loads(sys.argv[3]))
    elif cmd == 'report':
        report_type = sys.argv[3] if len(sys.argv) > 3 else 'summary'
        report(db_path, report_type)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
