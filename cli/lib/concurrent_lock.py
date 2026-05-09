import fcntl
import os
import re
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


LOCK_RETRY_INTERVAL = 0.1
LOCK_TIMEOUT_SECONDS = 5.0
LOCK_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def _validate_name(name: str) -> str:
    if not LOCK_NAME_PATTERN.fullmatch(name):
        raise ValueError("lock name must use alphanumeric, dash, or underscore only")
    return name


def _lock_path(name: str) -> Path:
    key = _validate_name(name)
    lock_dir = Path.cwd() / ".helix" / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    return lock_dir / f"{key}.lock"


def acquire(name: str, timeout: float = LOCK_TIMEOUT_SECONDS) -> int:
    if timeout < 0:
        raise ValueError("timeout must be non-negative")

    lock_path = _lock_path(name)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    deadline = time.monotonic() + timeout

    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return fd
            except BlockingIOError as exc:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"lock not acquired within {timeout:.1f}s: {name}") from exc
                time.sleep(min(LOCK_RETRY_INTERVAL, max(0.0, deadline - time.monotonic())))
    except Exception:
        os.close(fd)
        raise


def release(fd: int) -> None:
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


@contextmanager
def file_lock(name: str, timeout: float = LOCK_TIMEOUT_SECONDS) -> Iterator[int]:
    fd = acquire(name, timeout=timeout)
    try:
        yield fd
    finally:
        release(fd)
