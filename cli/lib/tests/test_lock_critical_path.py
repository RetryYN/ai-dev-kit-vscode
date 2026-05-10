import sqlite3
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import concurrent_lock
import helix_db
import yaml_parser


def _instrument_lock(original_lock, hold_seconds: float = 0.1):
    state = {"active": 0, "max_active": 0, "calls": []}
    state_lock = threading.Lock()

    @contextmanager
    def wrapped(name, *args, **kwargs):
        with original_lock(name, *args, **kwargs):
            with state_lock:
                state["active"] += 1
                state["max_active"] = max(state["max_active"], state["active"])
                state["calls"].append(name)
            try:
                time.sleep(hold_seconds)
                yield
            finally:
                with state_lock:
                    state["active"] -= 1

    return wrapped, state


def test_helix_db_concurrent_writes_are_serialized_and_leave_metadata(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    db_path = tmp_path / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))

    wrapped_lock, state = _instrument_lock(concurrent_lock.file_lock)
    monkeypatch.setattr(helix_db, "file_lock", wrapped_lock)

    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def writer(index: int) -> None:
        try:
            barrier.wait(timeout=5)
            helix_db.record_task(
                str(db_path),
                {
                    "task_id": f"T{index}",
                    "task_type": "race-check",
                    "role": "qa",
                    "status": "completed",
                },
            )
        except BaseException as exc:  # pragma: no cover - assertion path
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(index,)) for index in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert all(not thread.is_alive() for thread in threads)
    assert not errors
    assert state["calls"] == [helix_db.HELIX_DB_LOCK_NAME, helix_db.HELIX_DB_LOCK_NAME]
    assert state["max_active"] == 1

    conn = sqlite3.connect(str(db_path))
    try:
        count = conn.execute("SELECT COUNT(*) FROM task_runs WHERE task_type = 'race-check'").fetchone()[0]
    finally:
        conn.close()
    assert count == 2

    metadata = concurrent_lock.read_lockfile_metadata(helix_db.HELIX_DB_LOCK_NAME)
    assert metadata is not None
    assert metadata["name"] == helix_db.HELIX_DB_LOCK_NAME


def test_yaml_parser_concurrent_writes_are_serialized_and_leave_valid_yaml(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    yaml_path = tmp_path / "phase.yaml"
    yaml_path.write_text("gates:\n  G2:\n    status: pending\n", encoding="utf-8")

    wrapped_lock, state = _instrument_lock(concurrent_lock.file_lock)
    monkeypatch.setattr(yaml_parser, "file_lock", wrapped_lock)

    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def writer(dotpath: str, value: str) -> None:
        try:
            barrier.wait(timeout=5)
            yaml_parser.write_yaml_safe(str(yaml_path), dotpath, value)
        except BaseException as exc:  # pragma: no cover - assertion path
            errors.append(exc)

    threads = [
        threading.Thread(target=writer, args=("gates.G2.status", "passed")),
        threading.Thread(target=writer, args=("gates.G3.status", "passed")),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert all(not thread.is_alive() for thread in threads)
    assert not errors
    assert state["calls"] == ["yaml-phase", "yaml-phase"]
    assert state["max_active"] == 1

    data = yaml_parser.parse_yaml(yaml_path.read_text(encoding="utf-8"))
    assert yaml_parser.get_nested(data, "gates.G2.status") == "passed"
    assert yaml_parser.get_nested(data, "gates.G3.status") == "passed"

    metadata = concurrent_lock.read_lockfile_metadata("yaml-phase")
    assert metadata is not None
    assert metadata["name"] == "yaml-phase"
