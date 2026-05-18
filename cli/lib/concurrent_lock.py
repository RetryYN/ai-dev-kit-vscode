import fcntl
import json
import os
import re
import sys
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


def _resolve_lock_dir(lock_dir: Path | None = None) -> Path:
    if lock_dir is not None:
        return Path(lock_dir)
    project_root = os.environ.get("HELIX_PROJECT_ROOT", "").strip()
    helix_home = os.environ.get("HELIX_HOME", "").strip()
    if project_root and helix_home:
        current_dir = Path.cwd().resolve()
        if current_dir == Path(helix_home).resolve():
            return Path(project_root) / DEFAULT_LOCK_DIR
    if project_root and Path.cwd().resolve() == Path(project_root).resolve():
        return Path(project_root) / DEFAULT_LOCK_DIR
    return DEFAULT_LOCK_DIR


def _lock_path(name: str, lock_dir: Path | None = None) -> Path:
    key = _validate_name(name)
    base_dir = _resolve_lock_dir(lock_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / f"{key}.lock"


def _lock_file_path(name: str, lock_dir: Path | None = None) -> Path:
    key = _validate_name(name)
    base_dir = _resolve_lock_dir(lock_dir)
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


def _is_valid_lockfile_metadata(metadata: object, name: str) -> bool:
    if not isinstance(metadata, dict):
        return False
    if metadata.get("version") != LOCKFILE_METADATA_VERSION:
        return False
    pid = metadata.get("pid")
    if type(pid) is not int or pid <= 0:
        return False
    acquired_at = metadata.get("acquired_at")
    if not isinstance(acquired_at, str):
        return False
    try:
        parsed = datetime.fromisoformat(acquired_at)
    except ValueError:
        return False
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return False
    return metadata.get("name") == name


def _parse_lockfile_metadata(raw: str, name: str) -> dict | None:
    try:
        metadata = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not _is_valid_lockfile_metadata(metadata, name):
        return None
    return metadata


def _read_lockfile_metadata_from_fd(fd: int, name: str) -> dict | None:
    os.lseek(fd, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    while True:
        chunk = os.read(fd, 4096)
        if not chunk:
            break
        chunks.append(chunk)
    return _parse_lockfile_metadata(b"".join(chunks).decode("utf-8"), name)


def _path_matches_fd(lock_path: Path, fd: int) -> bool:
    try:
        path_stat = lock_path.stat()
    except FileNotFoundError:
        return False
    fd_stat = os.fstat(fd)
    return (path_stat.st_dev, path_stat.st_ino) == (fd_stat.st_dev, fd_stat.st_ino)


def _pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _emit_stale_lock_released(lock_path: Path, previous_pid: int, current_pid: int) -> None:
    print(
        "level=warn "
        "event=stale_lock_released "
        f"lock_path={lock_path.resolve()} previous_pid={previous_pid} current_pid={current_pid}",
        file=sys.stderr,
        flush=True,
    )


def _release_stale_lock_if_needed(lock_path: Path, fd: int, name: str) -> bool:
    metadata = _read_lockfile_metadata_from_fd(fd, name)
    if metadata is None:
        return False
    previous_pid = metadata["pid"]
    if _pid_is_alive(previous_pid):
        return False
    _emit_stale_lock_released(lock_path, previous_pid, os.getpid())
    try:
        lock_path.unlink()
    except FileNotFoundError:
        pass
    return True


def acquire(name: str, timeout: float = LOCK_TIMEOUT_SECONDS, lock_dir: Path | None = None) -> int:
    if timeout < 0:
        raise ValueError("timeout must be non-negative")

    lock_path = _lock_path(name, lock_dir=lock_dir)
    deadline = time.monotonic() + timeout

    while True:
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        closed = False
        retry = False
        try:
            remaining = max(0.0, deadline - time.monotonic())
            _flock_with_timeout(fd, name, remaining)
            if _release_stale_lock_if_needed(lock_path, fd, name):
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
                closed = True
                retry = True
            elif _path_matches_fd(lock_path, fd):
                _write_lockfile_metadata(fd, name)
                return fd
            else:
                fcntl.flock(fd, fcntl.LOCK_UN)
        except Exception:
            if not closed:
                os.close(fd)
            raise

        if not closed:
            os.close(fd)
        if retry:
            continue
        if time.monotonic() >= deadline:
            raise TimeoutError(f"lock not acquired within {timeout:.1f}s: {name}")
        time.sleep(min(LOCK_RETRY_INTERVAL, max(0.0, deadline - time.monotonic())))


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
    lock_path = _lock_file_path(name, lock_dir=lock_dir)
    if not lock_path.exists():
        return None
    try:
        return _parse_lockfile_metadata(lock_path.read_text(encoding="utf-8"), name)
    except OSError:
        return None


def inspect_stale_locks(lock_dir: Path | None = None) -> dict[str, list[str]]:
    base_dir = _resolve_lock_dir(lock_dir)
    if not base_dir.exists():
        return {"stale": [], "alive_skipped": [], "errors": []}

    stale: list[str] = []
    alive_skipped: list[str] = []
    errors: list[str] = []

    for lock_file in sorted(base_dir.glob("*.lock")):
        try:
            metadata = read_lockfile_metadata(lock_file.stem, lock_dir=base_dir)
            if metadata is None:
                continue
            if _pid_is_alive(metadata["pid"]):
                alive_skipped.append(lock_file.name)
            else:
                stale.append(lock_file.name)
        except OSError as exc:
            errors.append(f"{lock_file.name}: {exc}")

    return {"stale": stale, "alive_skipped": alive_skipped, "errors": errors}


def cleanup_stale(lock_dir: Path | None = None) -> dict[str, list[str]]:
    base_dir = _resolve_lock_dir(lock_dir)
    if not base_dir.exists():
        return {"cleaned": [], "alive_skipped": [], "errors": []}

    cleaned: list[str] = []
    alive_skipped: list[str] = []
    errors: list[str] = []

    for lock_file in sorted(base_dir.glob("*.lock")):
        try:
            metadata = read_lockfile_metadata(lock_file.stem, lock_dir=base_dir)
            if metadata is None:
                continue
            if _pid_is_alive(metadata["pid"]):
                alive_skipped.append(lock_file.name)
                continue

            try:
                fd = os.open(lock_file, os.O_RDWR)
            except FileNotFoundError:
                continue

            try:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    continue
                if not _path_matches_fd(lock_file, fd):
                    continue
                current = _read_lockfile_metadata_from_fd(fd, lock_file.stem)
                if current != metadata:
                    continue
                if _pid_is_alive(current["pid"]):
                    alive_skipped.append(lock_file.name)
                    continue
                try:
                    lock_file.unlink()
                except FileNotFoundError:
                    continue
                cleaned.append(lock_file.name)
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
        except OSError as exc:
            errors.append(f"{lock_file.name}: {exc}")

    return {"cleaned": cleaned, "alive_skipped": alive_skipped, "errors": errors}
