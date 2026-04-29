import io
import sqlite3
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import feedback_hook
import helix_db


SAMPLE_FEEDBACK_JSON = """{
  "feedback_message": "ここまでの整理は良い流れです。\\n次は根拠と差分を一段厚くして Lv4-5 を狙えます。",
  "scores": [
    {"dimension": "density", "level": 4, "comment": "必要な材料は揃っている"},
    {"dimension": "depth", "level": 3, "comment": "一部の根拠は追加できる"},
    {"dimension": "breadth", "level": 4, "comment": "関連領域に目配りできている"},
    {"dimension": "accuracy", "level": 5, "comment": "仕様との整合が高い"},
    {"dimension": "maintainability", "level": 4, "comment": "変更範囲が絞られている"}
  ]
}
"""


def _make_project(tmp_path: Path) -> tuple[Path, Path, Path]:
    project_root = tmp_path / "project"
    helix_dir = project_root / ".helix"
    helix_dir.mkdir(parents=True)
    (helix_dir / "phase.yaml").write_text("plan_id: PLAN-004\n", encoding="utf-8")
    db_path = helix_dir / "helix.db"
    helix_db.init_db(str(db_path))
    return project_root, helix_dir, db_path


def _fake_codex(tmp_path: Path, output: str, exit_code: int = 0) -> list[str]:
    script = tmp_path / "fake_codex.py"
    script.write_text(
        "import sys\n"
        f"sys.stdout.write({output!r})\n"
        f"raise SystemExit({exit_code})\n",
        encoding="utf-8",
    )
    return [sys.executable, str(script)]


def _rows(db_path: Path) -> list[sqlite3.Row]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute("SELECT * FROM accuracy_score ORDER BY dimension").fetchall()
    finally:
        conn.close()


def test_feedback_hook_records_5_dimensions(tmp_path: Path, capsys) -> None:
    project_root, helix_dir, db_path = _make_project(tmp_path)
    capsys.readouterr()

    emitted = feedback_hook.emit_feedback(
        project_root=project_root,
        helix_dir=helix_dir,
        gate="G2",
        gate_name="設計凍結ゲート",
        findings_summary="static_pass=2; static_fail=0",
        codex_cmd=_fake_codex(tmp_path, SAMPLE_FEEDBACK_JSON),
        env={},
        stdout=io.StringIO(),
    )

    rows = _rows(db_path)
    assert emitted is True
    assert len(rows) == 5
    assert {row["dimension"] for row in rows} == set(feedback_hook.DIMENSIONS)
    assert {row["plan_id"] for row in rows} == {"PLAN-004"}
    assert {row["gate"] for row in rows} == {"G2"}
    assert {row["reviewer"] for row in rows} == {"codex-tl"}


def test_feedback_hook_disabled_env(tmp_path: Path, capsys) -> None:
    project_root, helix_dir, db_path = _make_project(tmp_path)
    capsys.readouterr()
    stdout = io.StringIO()

    emitted = feedback_hook.emit_feedback(
        project_root=project_root,
        helix_dir=helix_dir,
        gate="G2",
        gate_name="設計凍結ゲート",
        findings_summary="static_pass=2",
        codex_cmd=[str(tmp_path / "missing-codex")],
        env={"HELIX_DISABLE_FEEDBACK": "1"},
        stdout=stdout,
    )

    assert emitted is False
    assert _rows(db_path) == []
    assert stdout.getvalue() == ""


def test_feedback_hook_fail_open_on_codex_error(tmp_path: Path, capsys) -> None:
    project_root, helix_dir, db_path = _make_project(tmp_path)
    capsys.readouterr()
    stderr = io.StringIO()

    emitted = feedback_hook.emit_feedback(
        project_root=project_root,
        helix_dir=helix_dir,
        gate="G2",
        gate_name="設計凍結ゲート",
        findings_summary="static_pass=2",
        codex_cmd=_fake_codex(tmp_path, "codex failed\n", exit_code=7),
        env={},
        stdout=io.StringIO(),
        stderr=stderr,
    )

    assert emitted is False
    assert _rows(db_path) == []
    assert "WARN: feedback hook skipped" in stderr.getvalue()


def test_feedback_message_displayed(tmp_path: Path, capsys) -> None:
    project_root, helix_dir, _ = _make_project(tmp_path)
    capsys.readouterr()
    stdout = io.StringIO()

    feedback_hook.emit_feedback(
        project_root=project_root,
        helix_dir=helix_dir,
        gate="G4",
        gate_name="実装凍結ゲート",
        findings_summary="mandatory=pass",
        codex_cmd=_fake_codex(tmp_path, SAMPLE_FEEDBACK_JSON),
        env={},
        stdout=stdout,
    )

    output = stdout.getvalue()
    assert "ここまでの整理は良い流れです" in output
    assert "accuracy: Lv5" in output
