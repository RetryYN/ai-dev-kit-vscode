#!/usr/bin/env python3
"""Single-host HELIX lock helper."""

from __future__ import annotations

import argparse
import fcntl
import os
import re
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import helix_db

EXIT_SUCCESS = 0
EXIT_NOT_ACQUIRED = 1
EXIT_STALE_CLEANED = 2
EXIT_ERROR = 3
LOCK_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
LOCK_SCOPES = ("home", "project")
LIST_SCOPES = ("home", "project", "all")


class LockError(Exception):
    pass


class LockArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(EXIT_ERROR, f"{self.prog}: error: {message}\n")


@dataclass(frozen=True)
class LockPaths:
    lock_file: Path
    db_path: Path
    scope: str


@dataclass(frozen=True)
class LockRecord:
    pid: int
    acquired_at: int
    expires_at: int | None


def epoch_now() -> int:
    return int(time.time())


def validate_lock_name(name: str) -> str:
    if not name or not LOCK_NAME_RE.fullmatch(name):
        raise LockError("LOCK_01: invalid lock name")
    return name


def validate_scope(scope: str, *, allow_all: bool = False) -> str:
    allowed = LIST_SCOPES if allow_all else LOCK_SCOPES
    if scope not in allowed:
        raise LockError(f"invalid scope: {scope}")
    return scope


def owner_pid() -> int:
    raw = os.environ.get("HELIX_LOCK_OWNER_PID", "").strip()
    try:
        pid = int(raw) if raw else os.getppid()
    except ValueError as exc:
        raise LockError("invalid HELIX_LOCK_OWNER_PID") from exc
    if pid <= 0:
        raise LockError("invalid owner pid")
    return pid


def is_pid_alive(pid: int) -> bool:
    """Return whether a PID appears to be alive on Linux/macOS."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def resolve_paths(name: str, scope: str, project_root: str | None, db_path: str | None) -> LockPaths:
    validate_lock_name(name)
    validate_scope(scope)
    root = Path(project_root or os.environ.get("HELIX_PROJECT_ROOT") or os.getcwd()).resolve()
    lock_file = (
        Path.home() / ".helix" / "locks" / f"{name}.lock"
        if scope == "home"
        else root / ".helix" / "locks" / f"{name}.lock"
    )
    resolved_db = Path(db_path or os.environ.get("HELIX_DB_PATH", "") or root / ".helix" / "helix.db").resolve()
    return LockPaths(lock_file=lock_file, db_path=resolved_db, scope=scope)


def ensure_lock_parent(paths: LockPaths) -> None:
    paths.lock_file.parent.mkdir(parents=True, exist_ok=True)
    if paths.scope == "home":
        os.chmod(paths.lock_file.parent, 0o700)


def lock_file_mode(scope: str) -> int:
    return 0o600 if scope == "home" else 0o644


def parse_lock_text(text: str) -> LockRecord:
    parts = text.strip().split(":")
    if len(parts) != 3:
        raise ValueError("expected pid:acquired_at:expires_at")
    return LockRecord(
        pid=int(parts[0]),
        acquired_at=int(parts[1]),
        expires_at=int(parts[2]) if parts[2] else None,
    )


def read_lock_file(lock_file_path: str | Path) -> LockRecord:
    return parse_lock_text(Path(lock_file_path).read_text(encoding="utf-8"))


def format_lock_record(record: LockRecord) -> str:
    expires = "" if record.expires_at is None else str(record.expires_at)
    return f"{record.pid}:{record.acquired_at}:{expires}\n"


def _reject_symlink(path: Path) -> None:
    if path.is_symlink():
        raise LockError(f"refusing symlink lock file: {path}")


def _fetch_db_row(db_path: Path, name: str, scope: str | None = None) -> sqlite3.Row | None:
    conn = helix_db._automation_conn(str(db_path))
    try:
        if scope is None:
            return conn.execute("SELECT * FROM locks WHERE name = ?", (name,)).fetchone()
        return conn.execute("SELECT * FROM locks WHERE name = ? AND scope = ?", (name, scope)).fetchone()
    finally:
        conn.close()


def _delete_db_row(db_path: Path, name: str) -> None:
    conn = helix_db._automation_conn(str(db_path))
    try:
        conn.execute("DELETE FROM locks WHERE name = ?", (name,))
        conn.commit()
    finally:
        conn.close()


def is_stale(lock_file_path: str | Path, db_row: Any = None) -> tuple[bool, str]:
    """Return stale state and reason for a lock file plus optional DB row."""
    now = epoch_now()
    try:
        record = read_lock_file(lock_file_path)
    except FileNotFoundError:
        return (db_row is not None, "file_missing" if db_row is not None else "")
    except (OSError, ValueError):
        return True, "lock_file_unreadable"
    if record.expires_at is not None and record.expires_at <= now:
        return True, "ttl_expired"
    if not is_pid_alive(record.pid):
        return True, "pid_dead"
    if db_row is not None:
        db_expires = db_row["expires_at"]
        db_pid = int(db_row["pid"])
        if db_expires is not None and int(db_expires) <= now:
            return True, "db_ttl_expired"
        if not is_pid_alive(db_pid):
            return True, "db_pid_dead"
    return False, ""


def _read_from_fd(fd: int) -> str:
    os.lseek(fd, 0, os.SEEK_SET)
    return os.read(fd, 4096).decode("utf-8")


def _write_to_fd(fd: int, text: str) -> None:
    os.lseek(fd, 0, os.SEEK_SET)
    os.ftruncate(fd, 0)
    os.write(fd, text.encode("utf-8"))
    os.fsync(fd)


def _try_acquire_once(paths: LockPaths, name: str, pid: int, ttl: int | None) -> tuple[bool, bool, str]:
    ensure_lock_parent(paths)
    _reject_symlink(paths.lock_file)
    mode = lock_file_mode(paths.scope)
    fd = os.open(paths.lock_file, os.O_RDWR | os.O_CREAT, mode)
    try:
        os.chmod(paths.lock_file, mode)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False, False, "flock_busy"
        raw = _read_from_fd(fd).strip()
        stale_cleaned = False
        stale_reason = ""
        if raw:
            try:
                parse_lock_text(raw)
            except ValueError:
                stale_cleaned = True
                stale_reason = "lock_file_unreadable"
                _delete_db_row(paths.db_path, name)
            else:
                stale, reason = is_stale(paths.lock_file, _fetch_db_row(paths.db_path, name, paths.scope))
                if not stale:
                    return False, False, "held"
                stale_cleaned = True
                stale_reason = reason
                _delete_db_row(paths.db_path, name)
        now = epoch_now()
        expires_at = now + ttl if ttl is not None else None
        record = LockRecord(pid=pid, acquired_at=now, expires_at=expires_at)
        _write_to_fd(fd, format_lock_record(record))
        helix_db.acquire_db_lock(
            str(paths.db_path),
            name,
            pid,
            scope=paths.scope,
            acquired_at=now,
            expires_at=expires_at,
        )
        return True, stale_cleaned, stale_reason
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def acquire(name: str, scope: str, timeout: int, ttl: int | None, project_root: str | None, db_path: str | None) -> int:
    name = validate_lock_name(name)
    scope = validate_scope(scope)
    if timeout < 0:
        raise LockError("timeout must be >= 0")
    if ttl is not None and ttl <= 0:
        raise LockError("ttl must be > 0")
    paths = resolve_paths(name, scope, project_root, db_path)
    pid = owner_pid()
    deadline = time.monotonic() + timeout
    last_reason = "held"
    while True:
        acquired, stale_cleaned, reason = _try_acquire_once(paths, name, pid, ttl)
        if acquired:
            record = read_lock_file(paths.lock_file)
            print(
                "acquired "
                f"name={name} scope={scope} pid={record.pid} "
                f"acquired_at={record.acquired_at} expires_at={record.expires_at or ''} "
                f"path={paths.lock_file}"
            )
            if stale_cleaned:
                print(f"stale_cleaned=true reason={reason}")
                return EXIT_STALE_CLEANED
            return EXIT_SUCCESS
        last_reason = reason
        if timeout == 0 or time.monotonic() >= deadline:
            print(f"lock not acquired: name={name} scope={scope} reason={last_reason}", file=sys.stderr)
            return EXIT_NOT_ACQUIRED
        time.sleep(0.1)


def release(name: str, scope: str, project_root: str | None, db_path: str | None) -> int:
    name = validate_lock_name(name)
    scope = validate_scope(scope)
    paths = resolve_paths(name, scope, project_root, db_path)
    if not paths.lock_file.exists():
        print(f"lock not found: name={name} scope={scope}", file=sys.stderr)
        return EXIT_NOT_ACQUIRED
    _reject_symlink(paths.lock_file)
    pid = owner_pid()
    fd = os.open(paths.lock_file, os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            record = parse_lock_text(_read_from_fd(fd))
        except ValueError as exc:
            raise LockError("lock file is unreadable") from exc
        if record.pid != pid:
            print(f"lock owner mismatch: name={name} expected_pid={record.pid} current_pid={pid}", file=sys.stderr)
            return EXIT_ERROR
        helix_db.release_db_lock(str(paths.db_path), name, pid)
        try:
            paths.lock_file.unlink()
        except FileNotFoundError:
            pass
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
    print(f"released name={name} scope={scope} pid={pid}")
    return EXIT_SUCCESS


def list_locks(scope: str, project_root: str | None, db_path: str | None) -> int:
    scope = validate_scope(scope, allow_all=True)
    root = Path(project_root or os.environ.get("HELIX_PROJECT_ROOT") or os.getcwd()).resolve()
    resolved_db = Path(db_path or os.environ.get("HELIX_DB_PATH", "") or root / ".helix" / "helix.db")
    conn = helix_db._automation_conn(str(resolved_db))
    try:
        params: tuple[str, ...] = ()
        sql = "SELECT name, pid, acquired_at, expires_at, scope FROM locks"
        if scope != "all":
            sql += " WHERE scope = ?"
            params = (scope,)
        sql += " ORDER BY scope, name"
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    print("name\tpid\tacquired_at\texpires_at\tscope\tpid_alive")
    for row in rows:
        alive = "true" if is_pid_alive(int(row["pid"])) else "false"
        expires = "" if row["expires_at"] is None else str(row["expires_at"])
        print(f"{row['name']}\t{row['pid']}\t{row['acquired_at']}\t{expires}\t{row['scope']}\t{alive}")
    return EXIT_SUCCESS


def status(name: str, scope: str, project_root: str | None, db_path: str | None) -> int:
    name = validate_lock_name(name)
    scope = validate_scope(scope)
    paths = resolve_paths(name, scope, project_root, db_path)
    db_row = _fetch_db_row(paths.db_path, name, scope)
    file_record: LockRecord | None = None
    file_error = ""
    try:
        _reject_symlink(paths.lock_file)
        file_record = read_lock_file(paths.lock_file)
    except FileNotFoundError:
        file_error = "file_missing"
    except (OSError, ValueError):
        file_error = "lock_file_unreadable"
    if db_row is None and file_record is None:
        print(f"lock not found: name={name} scope={scope}", file=sys.stderr)
        return EXIT_NOT_ACQUIRED
    stale, reason = is_stale(paths.lock_file, db_row)
    if not reason:
        reason = file_error
    pid = file_record.pid if file_record is not None else int(db_row["pid"])
    acquired_at = file_record.acquired_at if file_record is not None else int(db_row["acquired_at"])
    expires_at = file_record.expires_at if file_record is not None else db_row["expires_at"]
    ttl_remaining = str(max(0, int(expires_at) - epoch_now())) if expires_at is not None else ""
    print(f"name: {name}")
    print(f"scope: {scope}")
    print("held: true")
    print(f"pid: {pid}")
    print(f"pid_alive: {'true' if is_pid_alive(pid) else 'false'}")
    print(f"acquired_at: {acquired_at}")
    print(f"expires_at: {expires_at or ''}")
    print(f"ttl_remaining: {ttl_remaining}")
    print(f"stale: {'true' if stale else 'false'}")
    print(f"reason: {reason}")
    print(f"path: {paths.lock_file}")
    return EXIT_SUCCESS


def build_parser() -> argparse.ArgumentParser:
    parser = LockArgumentParser(prog="helix-lock")
    parser.add_argument("--db-path", default=None)
    parser.add_argument("--project-root", default=None)
    sub = parser.add_subparsers(dest="command", required=True, parser_class=LockArgumentParser)
    acquire_p = sub.add_parser("acquire")
    acquire_p.add_argument("--name", required=True)
    acquire_p.add_argument("--timeout", type=int, default=0)
    acquire_p.add_argument("--scope", choices=LOCK_SCOPES, default="project")
    acquire_p.add_argument("--ttl", type=int, default=None)
    release_p = sub.add_parser("release")
    release_p.add_argument("--name", required=True)
    release_p.add_argument("--scope", choices=LOCK_SCOPES, default="project")
    list_p = sub.add_parser("list")
    list_p.add_argument("--scope", choices=LIST_SCOPES, default="all")
    status_p = sub.add_parser("status")
    status_p.add_argument("--name", required=True)
    status_p.add_argument("--scope", choices=LOCK_SCOPES, default="project")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "acquire":
            return acquire(args.name, args.scope, args.timeout, args.ttl, args.project_root, args.db_path)
        if args.command == "release":
            return release(args.name, args.scope, args.project_root, args.db_path)
        if args.command == "list":
            return list_locks(args.scope, args.project_root, args.db_path)
        if args.command == "status":
            return status(args.name, args.scope, args.project_root, args.db_path)
    except LockError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
