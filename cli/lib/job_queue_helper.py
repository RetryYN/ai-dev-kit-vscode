#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import io
import json
import sqlite3
import sys
import time
import uuid

import helix_db
import task_dispatcher


STATUS_VALUES = ("pending", "running", "success", "failed", "cancelled")


def _conn(db_path: str) -> sqlite3.Connection:
    with contextlib.redirect_stdout(io.StringIO()):
        helix_db.init_db(db_path)
    conn = sqlite3.connect(db_path, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def enqueue_job(
    db_path: str,
    task_type: str,
    task_payload: str,
    *,
    priority: int = 5,
    delay: int | None = None,
    job_id: str | None = None,
    max_retries: int = 3,
    now: int | None = None,
) -> str:
    task_type = _validate_choice(task_type, task_dispatcher.TASK_TYPES, "task_type")
    task_payload = _require_text(task_payload, "task_payload")
    priority = _validate_int_range(priority, "priority", 1, 10)
    max_retries = _validate_int_range(max_retries, "max_retries", 0, 100)
    if delay is not None and int(delay) < 0:
        raise ValueError("delay must be >= 0")
    created_at = int(now or time.time())
    delay_until = created_at + int(delay) if delay is not None else None
    resolved_id = str(job_id or uuid.uuid4())

    conn = _conn(db_path)
    try:
        conn.execute(
            "INSERT INTO jobs "
            "(id, task_type, task_payload, priority, status, created_at, max_retries, delay_until) "
            "VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)",
            (resolved_id, task_type, task_payload, priority, created_at, max_retries, delay_until),
        )
    finally:
        conn.close()
    return resolved_id


def claim_next_job(db_path: str, *, now: int | None = None) -> dict | None:
    current_time = int(now or time.time())
    conn = _conn(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM jobs "
            "WHERE status = 'pending' AND (delay_until IS NULL OR delay_until <= ?) "
            "ORDER BY priority DESC, created_at ASC, id ASC "
            "LIMIT 1",
            (current_time,),
        ).fetchone()
        if not row:
            conn.execute("COMMIT")
            return None
        cur = conn.execute(
            "UPDATE jobs SET status = 'running', started_at = ? "
            "WHERE id = ? AND status = 'pending'",
            (current_time, row["id"]),
        )
        if cur.rowcount != 1:
            conn.execute("ROLLBACK")
            return None
        claimed = conn.execute("SELECT * FROM jobs WHERE id = ?", (row["id"],)).fetchone()
        conn.execute("COMMIT")
        return _row_to_dict(claimed)
    except Exception:
        with contextlib.suppress(sqlite3.Error):
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def mark_completed(db_path: str, job_id: str, success: bool, error_summary: str | None = None) -> dict | None:
    now = int(time.time())
    conn = _conn(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            conn.execute("COMMIT")
            return None
        if success:
            conn.execute(
                "UPDATE jobs SET status = 'success', completed_at = ?, last_error = NULL WHERE id = ?",
                (now, job_id),
            )
        elif should_retry(_row_to_dict(row)):
            conn.execute(
                "UPDATE jobs SET status = 'pending', retry_count = retry_count + 1, "
                "started_at = NULL, completed_at = NULL, last_error = ? WHERE id = ?",
                (_trim_error(error_summary), job_id),
            )
        else:
            conn.execute(
                "UPDATE jobs SET status = 'failed', completed_at = ?, last_error = ? WHERE id = ?",
                (now, _trim_error(error_summary), job_id),
            )
        updated = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        conn.execute("COMMIT")
        return _row_to_dict(updated)
    except Exception:
        with contextlib.suppress(sqlite3.Error):
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def should_retry(job_row: dict) -> bool:
    return int(job_row.get("retry_count") or 0) < int(job_row.get("max_retries") or 0)


def get_job(db_path: str, job_id: str) -> dict | None:
    conn = _conn(db_path)
    try:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def cancel_job(db_path: str, job_id: str) -> bool:
    now = int(time.time())
    conn = _conn(db_path)
    try:
        cur = conn.execute(
            "UPDATE jobs SET status = 'cancelled', completed_at = ? "
            "WHERE id = ? AND status IN ('pending', 'running')",
            (now, job_id),
        )
        return cur.rowcount == 1
    finally:
        conn.close()


def retry_job(db_path: str, job_id: str) -> bool:
    conn = _conn(db_path)
    try:
        cur = conn.execute(
            "UPDATE jobs SET status = 'pending', started_at = NULL, completed_at = NULL, last_error = NULL "
            "WHERE id = ? AND status = 'failed'",
            (job_id,),
        )
        return cur.rowcount == 1
    finally:
        conn.close()


def worker_loop(db_path: str, *, max_jobs: int | None = None, idle_sleep: float = 1.0) -> list[dict]:
    if max_jobs is not None and int(max_jobs) < 1:
        raise ValueError("max_jobs must be >= 1")
    if idle_sleep < 0:
        raise ValueError("idle_sleep must be >= 0")

    results: list[dict] = []
    processed = 0
    while max_jobs is None or processed < max_jobs:
        job = claim_next_job(db_path)
        if not job:
            if max_jobs is not None:
                break
            time.sleep(idle_sleep)
            continue
        ok, output = task_dispatcher.dispatch_task(job["task_type"], job["task_payload"])
        updated = mark_completed(db_path, job["id"], ok, None if ok else output)
        processed += 1
        results.append(
            {
                "id": job["id"],
                "ok": ok,
                "output": output,
                "status": updated["status"] if updated else None,
                "retry_count": updated["retry_count"] if updated else None,
            }
        )
    return results


def _validate_choice(value: str, choices: tuple[str, ...], name: str) -> str:
    if value not in choices:
        raise ValueError(f"{name} must be one of: {', '.join(choices)}")
    return value


def _validate_int_range(value: int, name: str, minimum: int, maximum: int) -> int:
    try:
        resolved = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if resolved < minimum or resolved > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return resolved


def _require_text(value: str, name: str) -> str:
    raw = (value or "").strip()
    if not raw:
        raise ValueError(f"{name} is required")
    return raw


def _trim_error(error_summary: str | None) -> str | None:
    if error_summary is None:
        return None
    return str(error_summary)[:2000]


def _print_json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="helix-job")
    parser.add_argument("--db-path", required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    enqueue = sub.add_parser("enqueue")
    enqueue.add_argument("--task-type", required=True, choices=task_dispatcher.TASK_TYPES)
    enqueue.add_argument("--task-payload", required=True)
    enqueue.add_argument("--priority", type=int, default=5)
    enqueue.add_argument("--delay", type=int)
    enqueue.add_argument("--id")
    enqueue.add_argument("--max-retries", type=int, default=3)

    worker = sub.add_parser("worker")
    worker.add_argument("--max-jobs", type=int)
    worker.add_argument("--idle-sleep", type=float, default=1.0)

    status = sub.add_parser("status")
    status.add_argument("--id", required=True)

    cancel = sub.add_parser("cancel")
    cancel.add_argument("--id", required=True)

    retry = sub.add_parser("retry")
    retry.add_argument("--id", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "enqueue":
            job_id = enqueue_job(
                args.db_path,
                args.task_type,
                args.task_payload,
                priority=args.priority,
                delay=args.delay,
                job_id=args.id,
                max_retries=args.max_retries,
            )
            _print_json({"id": job_id, "job": get_job(args.db_path, job_id)})
            return 0
        if args.command == "worker":
            _print_json(worker_loop(args.db_path, max_jobs=args.max_jobs, idle_sleep=args.idle_sleep))
            return 0
        if args.command == "status":
            row = get_job(args.db_path, args.id)
            if not row:
                print(f"job not found: {args.id}", file=sys.stderr)
                return 1
            _print_json(row)
            return 0
        if args.command == "cancel":
            ok = cancel_job(args.db_path, args.id)
            _print_json({"id": args.id, "cancelled": ok})
            return 0 if ok else 1
        if args.command == "retry":
            ok = retry_job(args.db_path, args.id)
            _print_json({"id": args.id, "retried": ok})
            return 0 if ok else 1
    except (sqlite3.Error, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
