from __future__ import annotations

import sqlite3

from cli.lib.v3.cutover.rollback import archive_db, restore_db, restore_dry_run


def _make_db(path: str) -> None:
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE t (a TEXT)")
    db.execute("INSERT INTO t VALUES ('hello')")
    db.commit()
    db.close()


def test_archive_then_restore_round_trip(tmp_path):
    db_path = str(tmp_path / "live.db")
    _make_db(db_path)
    record = archive_db(db_path, str(tmp_path / "archive"), "ts1")
    assert record.checksum
    # 元 DB は残る(copy であって move でない)
    import os

    assert os.path.isfile(db_path)
    target = str(tmp_path / "restored.db")
    assert restore_db(record, target) is True
    # restore された DB が中身を保持
    db = sqlite3.connect(target)
    assert db.execute("select a from t").fetchone() == ("hello",)
    db.close()


def test_restore_fails_on_corrupted_archive(tmp_path):
    db_path = str(tmp_path / "live.db")
    _make_db(db_path)
    record = archive_db(db_path, str(tmp_path / "archive"), "ts2")
    with open(record.archive_path, "ab") as handle:  # archive を破損
        handle.write(b"corruption")
    assert restore_db(record, str(tmp_path / "restored.db")) is False  # checksum mismatch


def test_restore_dry_run_is_nondestructive_and_true(tmp_path):
    db_path = str(tmp_path / "live.db")
    _make_db(db_path)
    import os

    before = os.path.getsize(db_path)
    assert restore_dry_run(db_path) is True
    assert os.path.getsize(db_path) == before  # 本物の DB に触れない


def test_restore_dry_run_missing_db_is_false(tmp_path):
    assert restore_dry_run(str(tmp_path / "nope.db")) is False
