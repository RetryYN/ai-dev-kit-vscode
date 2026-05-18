from __future__ import annotations

import os
import signal
import subprocess
import sys
import textwrap
import threading
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
    name = sys.argv[3]
    hold = float(sys.argv[4])

    sys.path.insert(0, str(lib_dir))
    import concurrent_lock

    os = __import__("os")
    os.chdir(project_dir)

    with concurrent_lock.file_lock(name, timeout=1.0):
        print("acquired", flush=True)
        if hold:
            time.sleep(hold)
    """
)


def _seed_stale_lock(project_dir: Path, name: str) -> None:
    result = subprocess.run(
        [
            PYTHON,
            "-c",
            WORKER_SCRIPT,
            str(LIB_DIR),
            str(project_dir),
            name,
            "0.0",
        ],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "acquired"


def _spawn_holder(project_dir: Path, name: str, hold: float = 5.0) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            PYTHON,
            "-c",
            WORKER_SCRIPT,
            str(LIB_DIR),
            str(project_dir),
            name,
            str(hold),
        ],
        cwd=project_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_cleanup_skips_live_holder_while_waiter_blocks_then_acquires(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    holder_started = threading.Event()
    release_holder = threading.Event()
    waiter_acquired = threading.Event()
    cleanup_result: dict[str, list[str]] = {}
    errors: list[BaseException] = []

    def holder() -> None:
        try:
            with concurrent_lock.file_lock("live-race", timeout=1.0):
                holder_started.set()
                assert release_holder.wait(timeout=5)
        except BaseException as exc:  # pragma: no cover - assertion path
            errors.append(exc)

    def waiter() -> None:
        try:
            assert holder_started.wait(timeout=5)
            fd = concurrent_lock.acquire("live-race", timeout=2.0)
            waiter_acquired.set()
            concurrent_lock.release(fd)
        except BaseException as exc:  # pragma: no cover - assertion path
            errors.append(exc)

    def cleanup() -> None:
        try:
            assert holder_started.wait(timeout=5)
            cleanup_result.update(concurrent_lock.cleanup_stale())
        except BaseException as exc:  # pragma: no cover - assertion path
            errors.append(exc)

    threads = [
        threading.Thread(target=holder, name="holder-thread"),
        threading.Thread(target=waiter, name="waiter-thread"),
        threading.Thread(target=cleanup, name="cleanup-thread"),
    ]
    for thread in threads:
        thread.start()

    threads[2].join(timeout=5)
    assert not threads[2].is_alive()
    release_holder.set()

    for thread in threads[:2]:
        thread.join(timeout=5)
        assert not thread.is_alive()

    assert not errors
    assert waiter_acquired.is_set()
    assert cleanup_result == {
        "cleaned": [],
        "alive_skipped": ["live-race.lock"],
        "errors": [],
    }


def test_cleanup_cleans_dead_lock_before_waiter_acquires(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_stale_lock(tmp_path, "dead-before-waiter")

    result = concurrent_lock.cleanup_stale()

    assert result == {
        "cleaned": ["dead-before-waiter.lock"],
        "alive_skipped": [],
        "errors": [],
    }

    with concurrent_lock.file_lock("dead-before-waiter", timeout=0.0):
        metadata = concurrent_lock.read_lockfile_metadata("dead-before-waiter")

    assert metadata is not None
    assert metadata["name"] == "dead-before-waiter"


def test_waiter_retries_after_cleanup_unlinks_stale_inode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_stale_lock(tmp_path, "split-race")

    waiter_acquired = threading.Event()
    release_waiter = threading.Event()
    waiter_fd: list[int] = []
    cleanup_result: dict[str, list[str]] = {}
    errors: list[BaseException] = []

    def waiter() -> None:
        try:
            fd = concurrent_lock.acquire("split-race", timeout=2.0)
            waiter_fd.append(fd)
            waiter_acquired.set()
            assert release_waiter.wait(timeout=5)
            concurrent_lock.release(fd)
        except BaseException as exc:  # pragma: no cover - assertion path
            errors.append(exc)

    def cleanup() -> None:
        try:
            cleanup_result.update(concurrent_lock.cleanup_stale())
        except BaseException as exc:  # pragma: no cover - assertion path
            errors.append(exc)

    waiter_thread = threading.Thread(target=waiter, name="waiter-thread")
    cleanup_thread = threading.Thread(target=cleanup, name="cleanup-thread")

    waiter_thread.start()
    cleanup_thread.start()

    cleanup_thread.join(timeout=5)
    assert not cleanup_thread.is_alive()
    assert waiter_acquired.wait(timeout=5)

    with pytest.raises(TimeoutError):
        contender_fd = concurrent_lock.acquire("split-race", timeout=0.0)
        concurrent_lock.release(contender_fd)

    release_waiter.set()
    waiter_thread.join(timeout=5)
    assert not waiter_thread.is_alive()

    assert not errors
    assert cleanup_result in (
        {"cleaned": ["split-race.lock"], "alive_skipped": [], "errors": []},
        {"cleaned": [], "alive_skipped": ["split-race.lock"], "errors": []},
        {"cleaned": [], "alive_skipped": [], "errors": []},
    )
    assert waiter_fd


def test_stale_lock_auto_release_on_dead_pid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_stale_lock(tmp_path, "auto-dead")

    lock_path = tmp_path / ".helix" / "locks" / "auto-dead.lock"
    unlinked: list[Path] = []
    original_unlink = Path.unlink

    def tracking_unlink(self: Path, *args, **kwargs):
        unlinked.append(self)
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", tracking_unlink)

    fd = concurrent_lock.acquire("auto-dead", timeout=0.0)
    metadata = concurrent_lock.read_lockfile_metadata("auto-dead")
    stderr = capsys.readouterr().err
    concurrent_lock.release(fd)

    assert metadata is not None
    assert metadata["pid"] == os.getpid()
    assert any(path.resolve() == lock_path.resolve() for path in unlinked)
    assert "level=warn event=stale_lock_released" in stderr
    assert f"lock_path={lock_path}" in stderr
    assert "previous_pid=" in stderr
    assert f"current_pid={os.getpid()}" in stderr


def test_stale_lock_not_released_on_live_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    holder = _spawn_holder(tmp_path, "auto-live", hold=1.0)
    assert holder.stdout is not None
    assert holder.stdout.readline().strip() == "acquired"

    lock_path = tmp_path / ".helix" / "locks" / "auto-live.lock"
    unlinked: list[Path] = []
    original_unlink = Path.unlink

    def tracking_unlink(self: Path, *args, **kwargs):
        unlinked.append(self)
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", tracking_unlink)

    with pytest.raises(TimeoutError):
        concurrent_lock.acquire("auto-live", timeout=0.0)

    _stdout, stderr_worker = holder.communicate(timeout=5)
    stderr = capsys.readouterr().err

    assert holder.returncode == 0, stderr_worker
    assert all(path.resolve() != lock_path.resolve() for path in unlinked)
    assert "stale_lock_released" not in stderr


def test_stale_lock_auto_release_after_sigkill(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    holder = _spawn_holder(tmp_path, "auto-killed", hold=5.0)
    assert holder.stdout is not None
    assert holder.stdout.readline().strip() == "acquired"

    lock_path = tmp_path / ".helix" / "locks" / "auto-killed.lock"
    unlinked: list[Path] = []
    original_unlink = Path.unlink

    def tracking_unlink(self: Path, *args, **kwargs):
        unlinked.append(self)
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", tracking_unlink)
    previous_pid = holder.pid
    assert previous_pid is not None

    os.kill(previous_pid, signal.SIGKILL)
    _stdout, stderr_worker = holder.communicate(timeout=5)

    fd = concurrent_lock.acquire("auto-killed", timeout=1.0)
    metadata = concurrent_lock.read_lockfile_metadata("auto-killed")
    stderr = capsys.readouterr().err
    concurrent_lock.release(fd)

    assert holder.returncode == -signal.SIGKILL, stderr_worker
    assert metadata is not None
    assert metadata["pid"] == os.getpid()
    assert any(path.resolve() == lock_path.resolve() for path in unlinked)
    assert "level=warn event=stale_lock_released" in stderr
    assert f"previous_pid={previous_pid}" in stderr
    assert f"current_pid={os.getpid()}" in stderr
