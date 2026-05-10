import fcntl
import json
import os
import re
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


DEFAULT_LOCK_DIR = Path(".helix") / "locks"
LOCKFILE_METADATA_VERSION = 1
LOCK_RETRY_INTERVAL = 0.1
LOCK_TIMEOUT_SECONDS = 5.0
LOCK_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def _validate_name(name: str) -> str:
    if not LOCK_NAME_PATTERN.fullmatch(name):
        raise ValueError("lock name must use alphanumeric, dash, or underscore only")
    return name


def _lock_path(name: str, lock_dir: Path | None = None) -> Path:
    key = _validate_name(name)
    base_dir = Path(lock_dir) if lock_dir is not None else DEFAULT_LOCK_DIR
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / f"{key}.lock"


def _flock_with_timeout(fd: int, name: str, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except BlockingIOError as exc:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"lock not acquired within {timeout:.1f}s: {name}") from exc
            time.sleep(min(LOCK_RETRY_INTERVAL, max(0.0, deadline - time.monotonic())))


def _write_lockfile_metadata(fd: int, name: str) -> None:
    metadata = {
        "version": LOCKFILE_METADATA_VERSION,
        "pid": os.getpid(),
        "acquired_at": datetime.now(timezone.utc).isoformat(),
        "name": name,
    }
    os.lseek(fd, 0, os.SEEK_SET)
    os.ftruncate(fd, 0)
    os.write(fd, json.dumps(metadata).encode("utf-8") + b"\n")
    os.fsync(fd)


def acquire(name: str, timeout: float = LOCK_TIMEOUT_SECONDS, lock_dir: Path | None = None) -> int:
    if timeout < 0:
        raise ValueError("timeout must be non-negative")

    lock_path = _lock_path(name, lock_dir=lock_dir)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)

    try:
        _flock_with_timeout(fd, name, timeout)
        _write_lockfile_metadata(fd, name)
        return fd
    except Exception:
        os.close(fd)
        raise


def release(fd: int) -> None:
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


@contextmanager
def file_lock(name: str, timeout: float = LOCK_TIMEOUT_SECONDS, lock_dir: Path | None = None) -> Iterator[int]:
    fd = acquire(name, timeout=timeout, lock_dir=lock_dir)
    try:
        yield fd
    finally:
        release(fd)


def read_lockfile_metadata(name: str, lock_dir: Path | None = None) -> dict | None:
    lock_path = _lock_path(name, lock_dir=lock_dir)
    if not lock_path.exists():
        return None
    try:
        return json.loads(lock_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
