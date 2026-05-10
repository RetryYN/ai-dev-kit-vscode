import os
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import concurrent_lock


PYTHON = sys.executable
WORKER_SCRIPT = textwrap.dedent(
    """
    import sys
    import time
    from pathlib import Path

    lib_dir = Path(sys.argv[1])
    project_dir = Path(sys.argv[2])
    mode = sys.argv[3]
    name = sys.argv[4]
    timeout = float(sys.argv[5])
    hold = float(sys.argv[6])

    sys.path.insert(0, str(lib_dir))
    import concurrent_lock

    os = __import__("os")
    os.chdir(project_dir)

    try:
        with concurrent_lock.file_lock(name, timeout=timeout):
            print("acquired", flush=True)
            if hold:
                time.sleep(hold)
    except TimeoutError as exc:
        print(f"timeout:{exc}", file=sys.stderr, flush=True)
        raise
    """
)


def _run_worker(project_dir: Path, name: str, timeout: float, hold: float) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            PYTHON,
            "-c",
            WORKER_SCRIPT,
            str(LIB_DIR),
            str(project_dir),
            "lock",
            name,
            str(timeout),
            str(hold),
        ],
        cwd=project_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _seed_stale_lock(project_dir: Path, name: str) -> None:
    result = subprocess.run(
        [
            PYTHON,
            "-c",
            WORKER_SCRIPT,
            str(LIB_DIR),
            str(project_dir),
            "lock",
            name,
            "1.0",
            "0.0",
        ],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_acquire_release_basic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    fd = concurrent_lock.acquire("basic")
    lock_file = tmp_path / ".helix" / "locks" / "basic.lock"

    assert fd >= 0
    assert lock_file.exists()

    concurrent_lock.release(fd)

    reopened = concurrent_lock.acquire("basic", timeout=0)
    concurrent_lock.release(reopened)


def test_context_manager(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    with concurrent_lock.file_lock("context") as fd:
        assert fd >= 0
        assert (tmp_path / ".helix" / "locks" / "context.lock").exists()

    reopened = concurrent_lock.acquire("context", timeout=0)
    concurrent_lock.release(reopened)


def test_lockfile_metadata_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    with concurrent_lock.file_lock("metadata") as fd:
        assert fd >= 0
        metadata = concurrent_lock.read_lockfile_metadata("metadata")

    assert metadata is not None
    assert metadata["version"] == concurrent_lock.LOCKFILE_METADATA_VERSION
    assert metadata["pid"] == os.getpid()
    assert metadata["name"] == "metadata"
    acquired_at = datetime.fromisoformat(metadata["acquired_at"])
    assert acquired_at.tzinfo == timezone.utc


def test_race_condition(tmp_path: Path) -> None:
    holder = _run_worker(tmp_path, "race", timeout=1.0, hold=0.8)
    assert holder.stdout is not None
    assert holder.stdout.readline().strip() == "acquired"

    waiter = _run_worker(tmp_path, "race", timeout=0.2, hold=0.0)
    waiter_stdout, waiter_stderr = waiter.communicate(timeout=5)
    holder_stdout, holder_stderr = holder.communicate(timeout=5)

    assert waiter.returncode != 0
    assert "timeout:" in waiter_stderr
    assert holder.returncode == 0, holder_stderr
    assert waiter_stdout == ""
    assert holder_stdout == ""


def test_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    fd = concurrent_lock.acquire("timeout-case")

    waiter = _run_worker(tmp_path, "timeout-case", timeout=0.0, hold=0.0)
    _stdout, stderr = waiter.communicate(timeout=5)

    concurrent_lock.release(fd)

    assert waiter.returncode != 0
    assert "timeout:" in stderr


def test_invalid_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError):
        concurrent_lock.acquire("../escape")


def test_cleanup_stale_skips_alive_pid(tmp_path: Path) -> None:
    holder = _run_worker(tmp_path, "alive-cleanup", timeout=1.0, hold=1.0)
    assert holder.stdout is not None
    assert holder.stdout.readline().strip() == "acquired"

    result = concurrent_lock.cleanup_stale(tmp_path / ".helix" / "locks")

    _stdout, stderr = holder.communicate(timeout=5)
    assert holder.returncode == 0, stderr
    assert result == {
        "cleaned": [],
        "alive_skipped": ["alive-cleanup.lock"],
        "errors": [],
    }


def test_cleanup_stale_removes_dead_pid_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_stale_lock(tmp_path, "dead-cleanup")

    result = concurrent_lock.cleanup_stale(tmp_path / ".helix" / "locks")

    assert result == {
        "cleaned": ["dead-cleanup.lock"],
        "alive_skipped": [],
        "errors": [],
    }
    assert concurrent_lock.read_lockfile_metadata("dead-cleanup") is None
