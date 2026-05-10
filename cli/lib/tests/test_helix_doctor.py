from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import concurrent_lock

from .test_role_config_consistency import REPO_ROOT


PYTHON = sys.executable
SEED_STALE_SCRIPT = textwrap.dedent(
    """
    import sys
    from pathlib import Path

    lib_dir = Path(sys.argv[1])
    project_dir = Path(sys.argv[2])
    name = sys.argv[3]

    sys.path.insert(0, str(lib_dir))
    import concurrent_lock

    os = __import__("os")
    os.chdir(project_dir)

    with concurrent_lock.file_lock(name, timeout=1.0):
        pass
    """
)

HOLDER_SCRIPT = textwrap.dedent(
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
        time.sleep(hold)
    """
)


def _prepare_project_root(project_root: Path) -> None:
    helix_dir = project_root / ".helix"
    helix_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / "cli/templates/phase.yaml", helix_dir / "phase.yaml")
    shutil.copy2(REPO_ROOT / "cli/templates/gate-checks.yaml", helix_dir / "gate-checks.yaml")
    shutil.copy2(REPO_ROOT / "cli/templates/doc-map.yaml", helix_dir / "doc-map.yaml")
    (helix_dir / "matrix.yaml").write_text("deliverables: []\n", encoding="utf-8")
    (project_root / "home").mkdir(exist_ok=True)


def _seed_stale_lock(project_root: Path, name: str) -> None:
    result = subprocess.run(
        [
            PYTHON,
            "-c",
            SEED_STALE_SCRIPT,
            str(LIB_DIR),
            str(project_root),
            name,
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def _run_holder(project_root: Path, name: str, hold: float) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            PYTHON,
            "-c",
            HOLDER_SCRIPT,
            str(LIB_DIR),
            str(project_root),
            name,
            str(hold),
        ],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _run_doctor(project_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HELIX_HOME"] = str(REPO_ROOT)
    env["HELIX_PROJECT_ROOT"] = str(project_root)
    env["HOME"] = str(project_root / "home")
    return subprocess.run(
        [str(REPO_ROOT / "cli/helix-doctor"), *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_doctor_shows_stale_lock_section(tmp_path: Path) -> None:
    _prepare_project_root(tmp_path)
    _seed_stale_lock(tmp_path, "doctor-dead")

    holder = _run_holder(tmp_path, "doctor-alive", hold=2.0)
    assert holder.stdout is not None
    assert holder.stdout.readline().strip() == "acquired"

    result = _run_doctor(tmp_path)
    _stdout, stderr = holder.communicate(timeout=5)

    assert holder.returncode == 0, stderr
    assert result.returncode == 0
    assert "[stale locks]" in result.stdout
    assert "  △ stale lock check" in result.stdout
    assert "dead: doctor-dead.lock" in result.stdout
    assert "alive skipped: doctor-alive.lock" in result.stdout


def test_doctor_cleanup_flag_removes_only_dead_locks(tmp_path: Path) -> None:
    _prepare_project_root(tmp_path)
    _seed_stale_lock(tmp_path, "doctor-dead")

    holder = _run_holder(tmp_path, "doctor-alive", hold=2.0)
    assert holder.stdout is not None
    assert holder.stdout.readline().strip() == "acquired"

    result = _run_doctor(tmp_path, "--cleanup-stale-locks")
    metadata = concurrent_lock.read_lockfile_metadata("doctor-alive", tmp_path / ".helix" / "locks")
    _stdout, stderr = holder.communicate(timeout=5)

    assert holder.returncode == 0, stderr
    assert result.returncode == 0
    assert "[stale locks]" in result.stdout
    assert "  △ stale lock cleanup" in result.stdout
    assert "cleaned: doctor-dead.lock" in result.stdout
    assert "alive skipped: doctor-alive.lock" in result.stdout
    assert not (tmp_path / ".helix" / "locks" / "doctor-dead.lock").exists()
    assert metadata is not None
