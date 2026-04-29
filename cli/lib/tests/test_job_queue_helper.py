import os
import sqlite3
import subprocess
import sys
import threading
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
import job_queue_helper as jobs


def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "project" / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))
    return db_path


def _fetch_job(db_path: Path, job_id: str) -> sqlite3.Row:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    finally:
        conn.close()


def test_enqueue_claim_and_completion(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    job_id = jobs.enqueue_job(
        str(db_path),
        "helix:command",
        "status",
        priority=7,
        job_id="job-1",
        now=1000,
    )
    claimed = jobs.claim_next_job(str(db_path), now=1001)
    completed = jobs.mark_completed(str(db_path), job_id, True)

    assert job_id == "job-1"
    assert claimed["id"] == "job-1"
    assert claimed["status"] == "running"
    assert claimed["started_at"] == 1001
    assert completed["status"] == "success"
    assert completed["last_error"] is None


def test_claim_orders_by_priority_then_fifo(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    jobs.enqueue_job(str(db_path), "helix:command", "status", priority=1, job_id="low", now=1000)
    jobs.enqueue_job(str(db_path), "helix:command", "status", priority=8, job_id="high-old", now=1001)
    jobs.enqueue_job(str(db_path), "helix:command", "status", priority=8, job_id="high-new", now=1002)

    assert jobs.claim_next_job(str(db_path), now=2000)["id"] == "high-old"
    assert jobs.claim_next_job(str(db_path), now=2000)["id"] == "high-new"
    assert jobs.claim_next_job(str(db_path), now=2000)["id"] == "low"


def test_failed_job_retries_until_max_retries(tmp_path: Path, monkeypatch, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    jobs.enqueue_job(
        str(db_path),
        "helix:command",
        "status",
        job_id="retry-me",
        max_retries=2,
        now=1000,
    )
    monkeypatch.setattr(jobs.task_dispatcher, "dispatch_task", lambda *_args: (False, "boom"))

    first = jobs.worker_loop(str(db_path), max_jobs=1, idle_sleep=0)[0]
    second = jobs.worker_loop(str(db_path), max_jobs=1, idle_sleep=0)[0]
    third = jobs.worker_loop(str(db_path), max_jobs=1, idle_sleep=0)[0]
    row = _fetch_job(db_path, "retry-me")

    assert first["status"] == "pending"
    assert first["retry_count"] == 1
    assert second["status"] == "pending"
    assert second["retry_count"] == 2
    assert third["status"] == "failed"
    assert row["retry_count"] == 2
    assert row["last_error"] == "boom"


def test_delay_until_blocks_claim_until_due(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    jobs.enqueue_job(str(db_path), "helix:command", "status", job_id="later", delay=60, now=1000)

    assert jobs.claim_next_job(str(db_path), now=1059) is None
    assert jobs.claim_next_job(str(db_path), now=1060)["id"] == "later"


def test_concurrent_claim_is_atomic(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    jobs.enqueue_job(str(db_path), "helix:command", "status", job_id="only-once", now=1000)
    barrier = threading.Barrier(8)
    claimed: list[str] = []
    lock = threading.Lock()

    def worker() -> None:
        barrier.wait()
        row = jobs.claim_next_job(str(db_path), now=1001)
        if row:
            with lock:
                claimed.append(row["id"])

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert claimed == ["only-once"]
    assert _fetch_job(db_path, "only-once")["status"] == "running"


def test_manual_retry_requeues_failed_job(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    jobs.enqueue_job(str(db_path), "helix:command", "status", job_id="manual", max_retries=0, now=1000)
    claimed = jobs.claim_next_job(str(db_path), now=1001)
    assert claimed["id"] == "manual"
    assert jobs.mark_completed(str(db_path), "manual", False, "failed")["status"] == "failed"
    assert jobs.retry_job(str(db_path), "manual") is True

    row = _fetch_job(db_path, "manual")
    assert row["status"] == "pending"
    assert row["last_error"] is None


def test_cli_enqueue_and_status(tmp_path: Path) -> None:
    project = tmp_path / "project"
    home = tmp_path / "home"
    (project / ".helix").mkdir(parents=True)
    home.mkdir()
    env = os.environ.copy()
    env["HELIX_HOME"] = str(REPO_ROOT)
    env["HELIX_PROJECT_ROOT"] = str(project)
    env["HOME"] = str(home)

    enqueue = subprocess.run(
        [
            str(REPO_ROOT / "cli" / "helix-job"),
            "enqueue",
            "--task-type",
            "helix:command",
            "--task-payload",
            "status",
            "--id",
            "cli-job",
        ],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert enqueue.returncode == 0

    status = subprocess.run(
        [str(REPO_ROOT / "cli" / "helix-job"), "status", "--id", "cli-job"],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert status.returncode == 0
    assert '"id": "cli-job"' in status.stdout
