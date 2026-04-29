#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import sqlite3
import sys
import time
import uuid
from dataclasses import dataclass

import helix_db
from task_dispatcher import TASK_TYPES, dispatch_task


STATUS_VALUES = ("pending", "running", "success", "failed", "cancelled")
RELATIVE_RE = re.compile(r"^\+(\d+)([smhd])$")
UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


@dataclass(frozen=True)
class CronSpec:
    minutes: set[int]
    hours: set[int]
    days: set[int]
    months: set[int]
    weekdays: set[int]


def _conn(db_path: str) -> sqlite3.Connection:
    with contextlib.redirect_stdout(io.StringIO()):
        helix_db.init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def parse_schedule(schedule_expr: str, base_time: int) -> int:
    expr = (schedule_expr or "").strip()
    if not expr:
        raise ValueError("schedule_expr is required")
    relative = RELATIVE_RE.fullmatch(expr)
    if relative:
        amount = int(relative.group(1))
        if amount <= 0:
            raise ValueError("relative schedule amount must be positive")
        return int(base_time) + amount * UNIT_SECONDS[relative.group(2)]
    spec = _parse_cron(expr)
    return _next_cron_run(spec, int(base_time))


def compute_next_run(schedule_expr: str, last_run: int | None, current_time: int) -> int:
    base_time = max(int(current_time), int(last_run or 0))
    return parse_schedule(schedule_expr, base_time)


def _parse_cron(expr: str) -> CronSpec:
    fields = expr.split()
    if len(fields) != 5:
        raise ValueError("cron schedule must contain 5 fields")
    return CronSpec(
        minutes=_parse_cron_field(fields[0], 0, 59, "minute"),
        hours=_parse_cron_field(fields[1], 0, 23, "hour"),
        days=_parse_cron_field(fields[2], 1, 31, "day"),
        months=_parse_cron_field(fields[3], 1, 12, "month"),
        weekdays=_parse_cron_field(fields[4], 0, 7, "weekday"),
    )


def _parse_cron_field(raw: str, minimum: int, maximum: int, name: str) -> set[int]:
    values: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            raise ValueError(f"empty cron {name} segment")
        if part == "*":
            values.update(range(minimum, maximum + 1))
            continue
        if part.startswith("*/"):
            step = int(part[2:])
            if step <= 0:
                raise ValueError(f"cron {name} step must be positive")
            values.update(range(minimum, maximum + 1, step))
            continue
        if "-" in part:
            start_raw, end_raw = part.split("-", 1)
            start, end = int(start_raw), int(end_raw)
            if start > end:
                raise ValueError(f"cron {name} range start must be <= end")
            _validate_range(start, minimum, maximum, name)
            _validate_range(end, minimum, maximum, name)
            values.update(range(start, end + 1))
            continue
        value = int(part)
        _validate_range(value, minimum, maximum, name)
        values.add(value)
    if name == "weekday" and 7 in values:
        values.add(0)
        values.discard(7)
    return values


def _validate_range(value: int, minimum: int, maximum: int, name: str) -> None:
    if value < minimum or value > maximum:
        raise ValueError(f"cron {name} value out of range: {value}")


def _next_cron_run(spec: CronSpec, base_time: int) -> int:
    # Cron is minute-granular: start at the next full minute after base_time.
    candidate = base_time - (base_time % 60) + 60
    end = base_time + 366 * 24 * 3600 * 5
    while candidate <= end:
        tm = time.gmtime(candidate)
        cron_weekday = (tm.tm_wday + 1) % 7
        if (
            tm.tm_min in spec.minutes
            and tm.tm_hour in spec.hours
            and tm.tm_mday in spec.days
            and tm.tm_mon in spec.months
            and cron_weekday in spec.weekdays
        ):
            return candidate
        candidate += 60
    raise ValueError("cron schedule has no run within 5 years")


def add_schedule(db_path: str, schedule_expr: str, task_type: str, task_payload: str, **kwargs) -> str:
    task_type = _validate_choice(task_type, TASK_TYPES, "task_type")
    task_payload = _require_text(task_payload, "task_payload")
    schedule_expr = _require_text(schedule_expr, "schedule_expr")
    now = int(kwargs.get("now") or time.time())
    schedule_id = str(kwargs.get("id") or kwargs.get("schedule_id") or uuid.uuid4())
    next_run_at = int(kwargs.get("next_run_at") or parse_schedule(schedule_expr, now))
    conn = _conn(db_path)
    try:
        conn.execute(
            "INSERT INTO schedules "
            "(id, schedule_expr, task_type, task_payload, status, next_run_at, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)",
            (schedule_id, schedule_expr, task_type, task_payload, next_run_at, now, now),
        )
        conn.commit()
    finally:
        conn.close()
    return schedule_id


def list_schedules(db_path: str, status_filter: str | None = None) -> list[dict]:
    params: list[str] = []
    query = "SELECT * FROM schedules"
    if status_filter:
        query += " WHERE status = ?"
        params.append(_validate_choice(status_filter, STATUS_VALUES, "status"))
    query += " ORDER BY next_run_at IS NULL, next_run_at, created_at, id"
    conn = _conn(db_path)
    try:
        return [_row_to_dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def get_schedule(db_path: str, schedule_id: str) -> dict | None:
    conn = _conn(db_path)
    try:
        row = conn.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def cancel_schedule(db_path: str, schedule_id: str) -> bool:
    now = int(time.time())
    conn = _conn(db_path)
    try:
        cur = conn.execute(
            "UPDATE schedules SET status = 'cancelled', updated_at = ? "
            "WHERE id = ? AND status != 'cancelled'",
            (now, schedule_id),
        )
        conn.commit()
        return cur.rowcount == 1
    finally:
        conn.close()


def run_due_schedules(db_path: str, dry_run: bool = False) -> list[dict]:
    now = int(time.time())
    conn = _conn(db_path)
    try:
        rows = [
            _row_to_dict(row)
            for row in conn.execute(
                "SELECT * FROM schedules WHERE status = 'pending' AND next_run_at <= ? "
                "ORDER BY next_run_at, created_at, id",
                (now,),
            ).fetchall()
        ]
        results: list[dict] = []
        for row in rows:
            if dry_run:
                results.append({"id": row["id"], "dry_run": True, "would_run": True, "ok": None, "output": ""})
                continue
            conn.execute(
                "UPDATE schedules SET status = 'running', updated_at = ? WHERE id = ?",
                (now, row["id"]),
            )
            conn.commit()
            ok, output = dispatch_task(row["task_type"], row["task_payload"])
            finished_at = int(time.time())
            if ok:
                next_run_at = compute_next_run(row["schedule_expr"], finished_at, finished_at)
                conn.execute(
                    "UPDATE schedules SET status = 'pending', last_run_at = ?, next_run_at = ?, "
                    "last_error = NULL, updated_at = ? WHERE id = ?",
                    (finished_at, next_run_at, finished_at, row["id"]),
                )
            else:
                conn.execute(
                    "UPDATE schedules SET status = 'failed', last_run_at = ?, last_error = ?, "
                    "updated_at = ? WHERE id = ?",
                    (finished_at, output[:2000], finished_at, row["id"]),
                )
            conn.commit()
            results.append({"id": row["id"], "dry_run": False, "ok": ok, "output": output})
        return results
    finally:
        conn.close()


def _validate_choice(value: str, choices: tuple[str, ...], name: str) -> str:
    if value not in choices:
        raise ValueError(f"{name} must be one of: {', '.join(choices)}")
    return value


def _require_text(value: str, name: str) -> str:
    raw = (value or "").strip()
    if not raw:
        raise ValueError(f"{name} is required")
    return raw


def _print_json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="helix-scheduler")
    parser.add_argument("--db-path", required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add")
    add.add_argument("--schedule", required=True)
    add.add_argument("--task-type", required=True, choices=TASK_TYPES)
    add.add_argument("--task-payload", required=True)
    add.add_argument("--id")

    list_cmd = sub.add_parser("list")
    list_cmd.add_argument("--status", choices=STATUS_VALUES)

    cancel = sub.add_parser("cancel")
    cancel.add_argument("--id", required=True)

    status = sub.add_parser("status")
    status.add_argument("--id", required=True)

    run_due = sub.add_parser("run-due")
    run_due.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.command == "add":
            schedule_id = add_schedule(args.db_path, args.schedule, args.task_type, args.task_payload, id=args.id)
            row = get_schedule(args.db_path, schedule_id)
            _print_json({"id": schedule_id, "schedule": row})
            return 0
        if args.command == "list":
            _print_json(list_schedules(args.db_path, args.status))
            return 0
        if args.command == "cancel":
            ok = cancel_schedule(args.db_path, args.id)
            _print_json({"id": args.id, "cancelled": ok})
            return 0 if ok else 1
        if args.command == "status":
            row = get_schedule(args.db_path, args.id)
            if not row:
                print(f"schedule not found: {args.id}", file=sys.stderr)
                return 1
            _print_json(row)
            return 0
        if args.command == "run-due":
            _print_json(run_due_schedules(args.db_path, dry_run=args.dry_run))
            return 0
    except (sqlite3.Error, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
