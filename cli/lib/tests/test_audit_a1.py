"""Tests for audit_a1 (PLAN-002 Sprint 2b)。"""
import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from audit_a1 import A1ImportEngine
import audit_hash
import helix_db


SHA = "a" * 64
SHB = "b" * 64
SHC = "c" * 64


def _yaml_text(decisions: list[dict], scope_hash: str = SHA) -> str:
    body = textwrap.dedent(f"""\
        version: 1
        metadata:
          scope_hash: "{scope_hash}"
          source_hash: "{SHB}"
          schema_version: 1
        decisions:
        """)
    for d in decisions:
        body += textwrap.dedent(f"""\
              - candidate_id: {d.get('candidate_id', 'src/x.py')}
                schema_version: {d.get('schema_version', 1)}
                scope_hash: "{d.get('scope_hash', scope_hash)}"
                decision: {d.get('decision', 'keep')}
                rationale: "{d.get('rationale', 'r')}"
                evidence:
                  source: {d.get('candidate_id', 'src/x.py')}
                  hash: deadbeef
                  redacted: true
                fail_safe_action: {d.get('fail_safe_action', 'skip')}
        """)
    return body


def _make_yaml_file(text: str) -> Path:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    )
    f.write(text)
    f.close()
    return Path(f.name)


def _make_db() -> str:
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = f.name
    f.close()
    helix_db.init_db(db_path)
    return db_path


def test_dry_run_classifies_new_entry():
    db = _make_db()
    yaml_path = _make_yaml_file(_yaml_text([{"candidate_id": "src/a.py"}]))
    engine = A1ImportEngine(db, yaml_path)

    report = engine.dry_run()
    assert not report.has_errors
    assert len(report.classifications) == 1
    assert report.classifications[0].case == "new"
    assert report.case_counts == {"new": 1}


def test_dry_run_returns_validation_errors():
    db = _make_db()
    bad_yaml = _make_yaml_file(_yaml_text([{"decision": "unknown"}]))
    engine = A1ImportEngine(db, bad_yaml)

    report = engine.dry_run()
    assert report.has_errors
    assert any("decision must be" in e for e in report.validation_errors)


def test_import_sync_inserts_new_decision():
    db = _make_db()
    yaml_path = _make_yaml_file(_yaml_text([{"candidate_id": "src/a.py"}]))
    engine = A1ImportEngine(db, yaml_path)

    result = engine.import_sync()
    assert result.success
    assert result.imported_rows == 1
    assert result.case_counts == {"new": 1}

    # DB 状態確認
    rows = helix_db.query_active_audit_decisions(db)
    assert len(rows) == 1
    assert rows[0]["candidate_id"] == "src/a.py"
    assert rows[0]["status"] == "active"


def test_import_sync_case_a_noop():
    """同一 decision を再度 import → no-op (Case A)。"""
    db = _make_db()
    yaml_path = _make_yaml_file(_yaml_text([{"candidate_id": "src/a.py"}]))
    engine = A1ImportEngine(db, yaml_path)

    r1 = engine.import_sync()
    r2 = engine.import_sync()

    assert r1.success and r2.success
    assert r1.case_counts == {"new": 1}
    assert r2.case_counts == {"case_a": 1}
    assert r2.imported_rows == 0  # no-op

    rows = helix_db.query_active_audit_decisions(db)
    assert len(rows) == 1


def test_import_sync_case_b_demotes_old_active():
    """同一 (cand, sv, scope) で decision 変更 → 旧 active 行が historical 化。"""
    db = _make_db()

    # 初回 import
    yaml1 = _make_yaml_file(_yaml_text([{
        "candidate_id": "src/a.py", "decision": "keep"
    }]))
    A1ImportEngine(db, yaml1).import_sync()

    # decision 変更で再 import
    yaml2 = _make_yaml_file(_yaml_text([{
        "candidate_id": "src/a.py", "decision": "remove"
    }]))
    r2 = A1ImportEngine(db, yaml2).import_sync()

    assert r2.success
    assert r2.case_counts == {"case_b": 1}

    # active は 1 行 (新)、historical が 1 行 (旧) 残ること
    active = helix_db.query_active_audit_decisions(db)
    assert len(active) == 1
    assert active[0]["decision"] == "remove"

    import sqlite3
    conn = sqlite3.connect(db)
    try:
        rows = conn.execute(
            "SELECT decision, status FROM audit_decisions "
            "WHERE candidate_id='src/a.py' ORDER BY id"
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) == 2
    assert rows[0] == ("keep", "historical")
    assert rows[1] == ("remove", "active")


def test_import_sync_case_c_scope_hash_change():
    """scope_hash 変更 → 旧 active 行が historical 化、新 active INSERT。"""
    db = _make_db()

    yaml1 = _make_yaml_file(_yaml_text(
        [{"candidate_id": "src/a.py"}], scope_hash=SHA
    ))
    A1ImportEngine(db, yaml1).import_sync()

    yaml2 = _make_yaml_file(_yaml_text(
        [{"candidate_id": "src/a.py"}], scope_hash=SHC
    ))
    r2 = A1ImportEngine(db, yaml2).import_sync()

    assert r2.success
    assert r2.case_counts == {"case_c": 1}

    active = helix_db.query_active_audit_decisions(db)
    assert len(active) == 1
    assert active[0]["scope_hash"] == SHC


def test_import_sync_validation_error_no_db_run():
    """validation 失敗 → import_runs 行も作らない (早期 return)。"""
    db = _make_db()
    bad_yaml = _make_yaml_file(_yaml_text([{"decision": "unknown"}]))
    engine = A1ImportEngine(db, bad_yaml)

    result = engine.import_sync()
    assert not result.success
    assert "validation" in (result.error_summary or "")
    assert result.imported_rows == 0

    # import_runs に行が作られていないこと
    import sqlite3
    conn = sqlite3.connect(db)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM import_runs"
        ).fetchone()[0]
    finally:
        conn.close()
    assert count == 0


def test_verify_sync_in_sync():
    db = _make_db()
    yaml_path = _make_yaml_file(_yaml_text([{"candidate_id": "src/a.py"}]))
    engine = A1ImportEngine(db, yaml_path)
    engine.import_sync()

    result = engine.verify_sync()
    assert result.in_sync
    assert result.yaml_count == 1
    assert result.db_active_count == 1
    assert result.missing_in_db == []


def test_verify_sync_missing_in_db():
    db = _make_db()
    # import 1 件
    yaml1 = _make_yaml_file(_yaml_text([{"candidate_id": "src/a.py"}]))
    A1ImportEngine(db, yaml1).import_sync()

    # 別 yaml に 2 件 (1 件は DB に既にある、1 件は未 import)
    yaml2 = _make_yaml_file(_yaml_text([
        {"candidate_id": "src/a.py"},
        {"candidate_id": "src/b.py"},
    ]))
    result = A1ImportEngine(db, yaml2).verify_sync()

    assert not result.in_sync
    assert "src/b.py" in result.missing_in_db


def test_verify_sync_extra_in_db():
    db = _make_db()
    # import 2 件
    yaml1 = _make_yaml_file(_yaml_text([
        {"candidate_id": "src/a.py"},
        {"candidate_id": "src/b.py"},
    ]))
    A1ImportEngine(db, yaml1).import_sync()

    # 別 yaml に 1 件のみ
    yaml2 = _make_yaml_file(_yaml_text([{"candidate_id": "src/a.py"}]))
    result = A1ImportEngine(db, yaml2).verify_sync()

    assert not result.in_sync
    assert "src/b.py" in result.extra_in_db
