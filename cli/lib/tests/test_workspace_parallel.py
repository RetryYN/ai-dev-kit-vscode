import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "cli" / "lib"
TESTS_DIR = LIB_DIR / "tests"

if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from concurrent_lock import file_lock
from workspace_manager import WorkspaceManager
from test_workspace_manager import _commit_seed_state, _init_repo, _seed_helix


LOCK_ERROR_PATTERNS = ("database is locked", "lock not acquired")
STALE_LOCK_PATTERN = "stale_lock_released"
CREATE_SNIPPET = """
import sys
from pathlib import Path
from cli.lib.workspace_manager import WorkspaceManager

repo = Path(sys.argv[1])
home = Path(sys.argv[2])
task_id = sys.argv[3]
WorkspaceManager(project_root=repo, home=home).create(task_id=task_id)
"""
EXEC_SNIPPET = """
import sys
from pathlib import Path
from cli.lib.workspace_manager import WorkspaceManager

repo = Path(sys.argv[1])
home = Path(sys.argv[2])
task_id = sys.argv[3]
command = sys.argv[4]
raise SystemExit(WorkspaceManager(project_root=repo, home=home).exec_in_workspace(task_id, command))
"""
STRESS_COMMAND = r"""
python3 - <<'PY'
import os
from cli.lib import helix_db
from cli.lib.compatibility_adapter import write_connection

loops = int(os.environ.get("HELIX_WORKSPACE_STRESS_LOOPS", "30"))
for index in range(loops):
    with write_connection(helix_db.resolve_default_db_path()) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS workspace_stress "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL, iteration INTEGER NOT NULL)"
        )
        conn.execute(
            "INSERT INTO workspace_stress (task_id, iteration) VALUES (?, ?)",
            (os.environ["HELIX_WORKSPACE_TASK_ID"], index),
        )
print(f"stress-ok loops={loops}")
PY
"""


def _workspace_env(repo: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "PYTHONPATH": f"{REPO_ROOT}{os.pathsep}{LIB_DIR}{os.pathsep}{env.get('PYTHONPATH', '')}",
            "HELIX_PROJECT_ROOT": str(repo),
            "PROJECT_ROOT": str(repo),
            "HELIX_DIR": str(repo / ".helix"),
            "HELIX_DB_PATH": str(repo / ".helix" / "helix.db"),
        }
    )
    if extra:
        env.update(extra)
    return env


def _create_repo_with_helix(tmp_path: Path) -> tuple[Path, Path, WorkspaceManager]:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    _commit_seed_state(repo)
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    return repo, home, WorkspaceManager(project_root=repo, home=home)


def _run_parallel(processes: list[subprocess.Popen[str]], *, timeout: float) -> list[subprocess.CompletedProcess[str]]:
    results: list[subprocess.CompletedProcess[str]] = []
    for proc in processes:
        stdout, stderr = proc.communicate(timeout=timeout)
        results.append(
            subprocess.CompletedProcess(
                args=proc.args,
                returncode=proc.returncode,
                stdout=stdout,
                stderr=stderr,
            )
        )
    return results


def _assert_all_success(results: list[subprocess.CompletedProcess[str]]) -> None:
    for result in results:
        assert result.returncode == 0, (
            f"command failed rc={result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def _combined_output(results: list[subprocess.CompletedProcess[str]]) -> str:
    return "\n".join(f"{result.stdout}\n{result.stderr}" for result in results)


def _assert_no_lock_contention(results: list[subprocess.CompletedProcess[str]], *, max_stale_locks: int = 0) -> None:
    output = _combined_output(results)
    for pattern in LOCK_ERROR_PATTERNS:
        assert pattern not in output
    stale_count = output.count(STALE_LOCK_PATTERN)
    assert stale_count <= max_stale_locks, output


def test_parallel_workspace_create_no_lock_contention(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: PLAN-224 Sprint .3 D8 Layer 3 並列 create lock isolation."""
    repo, home, _manager = _create_repo_with_helix(tmp_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(repo))
    monkeypatch.setenv("HELIX_DB_PATH", str(repo / ".helix" / "helix.db"))
    env = _workspace_env(repo)

    processes = [
        subprocess.Popen(
            [sys.executable, "-c", CREATE_SNIPPET, str(repo), str(home), task_id],
            cwd=repo,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for task_id in ("PLAN-PAR-A", "PLAN-PAR-B")
    ]

    results = _run_parallel(processes, timeout=60)

    _assert_all_success(results)
    _assert_no_lock_contention(results, max_stale_locks=2)
    assert (home / ".helix" / "workspaces" / repo.name / "PLAN-PAR-A").exists()
    assert (home / ".helix" / "workspaces" / repo.name / "PLAN-PAR-B").exists()
    with file_lock("helix-db"):
        pass
    assert (repo / ".helix" / "locks" / "helix-db.lock").exists()


def test_parallel_workspace_exec_no_lock_contention(tmp_path: Path) -> None:
    """DoD 検証: PLAN-224 Sprint .3 D8 Layer 3 並列 exec lock isolation."""
    repo, home, manager = _create_repo_with_helix(tmp_path)
    manager.create(task_id="PLAN-EXEC-A")
    manager.create(task_id="PLAN-EXEC-B")
    env = _workspace_env(repo)
    command = (
        "python3 -c "
        "\"from pathlib import Path; "
        "from cli.lib import helix_db; "
        "path=Path(helix_db.resolve_default_db_path()); "
        "assert path.parent.name == '.helix'; print(path)\""
    )

    processes = [
        subprocess.Popen(
            [sys.executable, "-c", EXEC_SNIPPET, str(repo), str(home), task_id, command],
            cwd=repo,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for task_id in ("PLAN-EXEC-A", "PLAN-EXEC-B")
    ]

    results = _run_parallel(processes, timeout=60)

    _assert_all_success(results)
    _assert_no_lock_contention(results, max_stale_locks=2)


def test_parallel_workspace_db_write_stress_loop(tmp_path: Path) -> None:
    """DoD 検証: PLAN-224 Sprint .3 P1-3 DB write stress loop."""
    repo, home, manager = _create_repo_with_helix(tmp_path)
    manager.create(task_id="PLAN-STRESS-A")
    manager.create(task_id="PLAN-STRESS-B")
    loop_count = int(os.environ.get("HELIX_WORKSPACE_STRESS_LOOPS", "30"))
    loop_count = min(50, max(20, loop_count))
    env = _workspace_env(repo, {"HELIX_WORKSPACE_STRESS_LOOPS": str(loop_count)})

    processes = [
        subprocess.Popen(
            [sys.executable, "-c", EXEC_SNIPPET, str(repo), str(home), task_id, STRESS_COMMAND],
            cwd=repo,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for task_id in ("PLAN-STRESS-A", "PLAN-STRESS-B")
    ]

    results = _run_parallel(processes, timeout=90)

    _assert_all_success(results)
    _assert_no_lock_contention(results, max_stale_locks=0)
    assert _combined_output(results).count(f"stress-ok loops={loop_count}") == 2


def test_parallel_workspace_lock_path_isolation(tmp_path: Path) -> None:
    """DoD 検証: PLAN-224 Sprint .3 D8 Layer 3 lock_path workspace isolation."""
    repo, home, manager = _create_repo_with_helix(tmp_path)
    created = {
        task_id: Path(manager.create(task_id=task_id)["workspace_path"])
        for task_id in ("PLAN-LOCK-A", "PLAN-LOCK-B")
    }
    env = _workspace_env(repo)
    command = (
        "python3 -c "
        "\"from pathlib import Path; "
        "from concurrent_lock import _resolve_lock_dir; "
        "Path('lock-dir.txt').write_text(str(_resolve_lock_dir()), encoding='utf-8')\""
    )

    processes = [
        subprocess.Popen(
            [sys.executable, "-c", EXEC_SNIPPET, str(repo), str(home), task_id, command],
            cwd=repo,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for task_id in ("PLAN-LOCK-A", "PLAN-LOCK-B")
    ]

    results = _run_parallel(processes, timeout=60)

    _assert_all_success(results)
    _assert_no_lock_contention(results, max_stale_locks=0)
    lock_dirs = {
        task_id: (workspace_path / "lock-dir.txt").read_text(encoding="utf-8")
        for task_id, workspace_path in created.items()
    }
    main_lock_dir = str(repo / ".helix" / "locks")
    for task_id, workspace_path in created.items():
        assert lock_dirs[task_id] == str(workspace_path / ".helix" / "locks")
        assert lock_dirs[task_id] != main_lock_dir
    assert lock_dirs["PLAN-LOCK-A"] != lock_dirs["PLAN-LOCK-B"]
