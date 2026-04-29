import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

LIB_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
import lock_helper

CLI = REPO_ROOT / "cli" / "helix-lock"


def _prepare_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, dict[str, str]]:
    project = tmp_path / "project"
    project.mkdir()
    (project / ".helix").mkdir()
    home = tmp_path / "home"
    home.mkdir()
    env = os.environ.copy()
    env["HELIX_HOME"] = str(REPO_ROOT)
    env["HELIX_PROJECT_ROOT"] = str(project)
    env["HOME"] = str(home)
    env["HELIX_LOCK_OWNER_PID"] = str(os.getpid())
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project))
    monkeypatch.setenv("HOME", str(home))
    return project, env


def _run_lock(project: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(CLI), *args], cwd=project, env=env, capture_output=True, text=True, check=False)


def _db_row(project: Path, name: str) -> sqlite3.Row | None:
    conn = sqlite3.connect(str(project / ".helix" / "helix.db"))
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute("SELECT * FROM locks WHERE name = ?", (name,)).fetchone()
    finally:
        conn.close()


def _write_lock(project: Path, name: str, pid: int, acquired_at: int, expires_at: int | None = None) -> None:
    lock_dir = project / ".helix" / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    expires = "" if expires_at is None else str(expires_at)
    (lock_dir / f"{name}.lock").write_text(f"{pid}:{acquired_at}:{expires}\n", encoding="utf-8")


def _seed_db_lock(project: Path, name: str, pid: int, acquired_at: int, expires_at: int | None = None) -> None:
    helix_db.acquire_db_lock(
        str(project / ".helix" / "helix.db"),
        name,
        pid,
        scope="project",
        acquired_at=acquired_at,
        expires_at=expires_at,
    )


def test_acquire_release_basic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, env = _prepare_project(tmp_path, monkeypatch)
    assert _run_lock(project, env, "acquire", "--name", "basic").returncode == 0
    assert (project / ".helix" / "locks" / "basic.lock").exists()
    assert _db_row(project, "basic") is not None
    assert _run_lock(project, env, "release", "--name", "basic").returncode == 0
    assert not (project / ".helix" / "locks" / "basic.lock").exists()
    assert _db_row(project, "basic") is None


def test_acquire_blocks_when_held(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, env = _prepare_project(tmp_path, monkeypatch)
    assert _run_lock(project, env, "acquire", "--name", "held").returncode == 0
    conflict = _run_lock(project, env, "acquire", "--name", "held", "--timeout", "0")
    assert conflict.returncode == 1
    assert "lock not acquired" in conflict.stderr


def test_acquire_with_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, env = _prepare_project(tmp_path, monkeypatch)
    assert _run_lock(project, env, "acquire", "--name", "waited").returncode == 0
    waiter = subprocess.Popen(
        [str(CLI), "acquire", "--name", "waited", "--timeout", "2"],
        cwd=project,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(0.3)
    assert _run_lock(project, env, "release", "--name", "waited").returncode == 0
    stdout, stderr = waiter.communicate(timeout=5)
    assert waiter.returncode == 0, stderr
    assert "acquired name=waited" in stdout
    assert _run_lock(project, env, "release", "--name", "waited").returncode == 0


def test_stale_lock_detected_and_cleaned(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, env = _prepare_project(tmp_path, monkeypatch)
    now = int(time.time())
    _write_lock(project, "stale", 99999999, now)
    _seed_db_lock(project, "stale", 99999999, now)
    acquired = _run_lock(project, env, "acquire", "--name", "stale")
    assert acquired.returncode == 2, acquired.stderr
    assert "stale_cleaned=true" in acquired.stdout
    assert lock_helper.read_lock_file(project / ".helix" / "locks" / "stale.lock").pid == os.getpid()
    assert _db_row(project, "stale")["pid"] == os.getpid()


def test_ttl_expired_lock_cleaned(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, env = _prepare_project(tmp_path, monkeypatch)
    now = int(time.time())
    _write_lock(project, "expired", os.getpid(), now - 20, now - 10)
    _seed_db_lock(project, "expired", os.getpid(), now - 20, now - 10)
    acquired = _run_lock(project, env, "acquire", "--name", "expired")
    assert acquired.returncode == 2, acquired.stderr
    assert "reason=ttl_expired" in acquired.stdout


def test_release_validates_pid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, env = _prepare_project(tmp_path, monkeypatch)
    assert _run_lock(project, env, "acquire", "--name", "owner").returncode == 0
    other_env = dict(env)
    other_env["HELIX_LOCK_OWNER_PID"] = str(os.getpid() + 100000)
    rejected = _run_lock(project, other_env, "release", "--name", "owner")
    assert rejected.returncode == 3
    assert "owner mismatch" in rejected.stderr


def test_list_shows_all_locks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, env = _prepare_project(tmp_path, monkeypatch)
    assert _run_lock(project, env, "acquire", "--name", "listed").returncode == 0
    listed = _run_lock(project, env, "list", "--scope", "all")
    assert listed.returncode == 0
    assert "name\tpid\tacquired_at\texpires_at\tscope\tpid_alive" in listed.stdout
    assert "listed" in listed.stdout
    assert "\tproject\ttrue" in listed.stdout


def test_status_shows_stale_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, env = _prepare_project(tmp_path, monkeypatch)
    now = int(time.time())
    _write_lock(project, "status-stale", 99999999, now)
    _seed_db_lock(project, "status-stale", 99999999, now)
    status = _run_lock(project, env, "status", "--name", "status-stale")
    assert status.returncode == 0
    assert "stale: true" in status.stdout
    assert "reason: pid_dead" in status.stdout


def test_scope_home_uses_home_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, env = _prepare_project(tmp_path, monkeypatch)
    assert _run_lock(project, env, "acquire", "--name", "home-lock", "--scope", "home").returncode == 0
    lock_file = Path(env["HOME"]) / ".helix" / "locks" / "home-lock.lock"
    assert lock_file.exists()
    assert oct(lock_file.stat().st_mode & 0o777) == "0o600"
    assert oct(lock_file.parent.stat().st_mode & 0o777) == "0o700"
    assert _db_row(project, "home-lock")["scope"] == "home"


def test_scope_project_uses_project_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, env = _prepare_project(tmp_path, monkeypatch)
    assert _run_lock(project, env, "acquire", "--name", "project-lock", "--scope", "project").returncode == 0
    lock_file = project / ".helix" / "locks" / "project-lock.lock"
    assert lock_file.exists()
    assert oct(lock_file.stat().st_mode & 0o777) == "0o644"
    assert _db_row(project, "project-lock")["scope"] == "project"
