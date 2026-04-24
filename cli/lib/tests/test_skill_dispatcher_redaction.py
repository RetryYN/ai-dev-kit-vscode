import json
import sqlite3
import subprocess
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import skill_dispatcher


def _prepare_catalog(tmp_path: Path) -> tuple[Path, Path]:
    skills_root = tmp_path / "skills"
    skill_md = skills_root / "common" / "testing" / "SKILL.md"
    skill_md.parent.mkdir(parents=True, exist_ok=True)
    skill_md.write_text(
        "---\n"
        "name: testing\n"
        "description: test skill\n"
        "metadata:\n"
        "  helix_layer: L4\n"
        "compatibility:\n"
        "  claude: true\n"
        "  codex: true\n"
        "---\n"
        "\n"
        "# test skill\n",
        encoding="utf-8",
    )

    catalog_path = tmp_path / "skill-catalog.json"
    catalog = {
        "version": "1.0",
        "generated_at": "2026-01-01T00:00:00Z",
        "skill_count": 1,
        "reference_count": 0,
        "skills": [
            {
                "id": "common/testing",
                "name": "testing",
                "category": "common",
                "path": "skills/common/testing/SKILL.md",
                "description": "test skill",
                "helix_layer": "L4",
                "triggers": [],
                "verification": [],
                "compatibility": {"claude": True, "codex": True},
                "references": [],
            }
        ],
    }
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
    return skills_root, catalog_path


def _fetch_usage(db_path: Path, usage_id: int) -> sqlite3.Row:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM skill_usage WHERE id = ?", (usage_id,)).fetchone()
        assert row is not None
        return row
    finally:
        conn.close()


def _dispatch_with_fake_runner(
    monkeypatch,
    tmp_path: Path,
    *,
    task_text: str,
    stdout: str,
    stderr: str = "",
) -> sqlite3.Row:
    skills_root, catalog_path = _prepare_catalog(tmp_path)
    db_path = tmp_path / ".helix" / "helix.db"

    def _fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=kwargs.get("args", []),
            returncode=0,
            stdout=stdout,
            stderr=stderr,
        )

    monkeypatch.setattr(skill_dispatcher.subprocess, "run", _fake_run)

    result = skill_dispatcher.dispatch(
        skill_id="common/testing",
        task_text=task_text,
        recommended_agent=None,
        references=[],
        catalog_path=catalog_path,
        skills_root=skills_root,
        db_path=db_path,
        dry_run=False,
    )
    usage_id = int(result["usage_id"])
    return _fetch_usage(db_path, usage_id)


def test_dispatch_redacts_task_text_before_insert(monkeypatch, tmp_path: Path) -> None:
    row = _dispatch_with_fake_runner(
        monkeypatch,
        tmp_path,
        task_text="run check api_key=sk-test-secret",
        stdout="ok",
    )

    assert row["task_text"] == "[REDACTED]"


def test_dispatch_redacts_result_stdout_before_update(monkeypatch, tmp_path: Path) -> None:
    row = _dispatch_with_fake_runner(
        monkeypatch,
        tmp_path,
        task_text="regular task",
        stdout="Bearer ABC123",
    )

    assert row["result_stdout"] == "[REDACTED]"


def test_dispatch_keeps_non_sensitive_text_as_is(monkeypatch, tmp_path: Path) -> None:
    row = _dispatch_with_fake_runner(
        monkeypatch,
        tmp_path,
        task_text="normal text only",
        stdout="normal output only",
        stderr="stderr no issue",
    )

    assert row["task_text"] == "normal text only"
    assert row["result_stdout"] == "normal output only"
    assert row["result_stderr"] == "stderr no issue"


def test_dispatch_warns_for_size_s_with_high_effort_subagent(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    skills_root, catalog_path = _prepare_catalog(tmp_path)
    db_path = tmp_path / ".helix" / "helix.db"

    project_root = tmp_path / "project"
    (project_root / ".helix").mkdir(parents=True, exist_ok=True)
    (project_root / ".claude" / "agents").mkdir(parents=True, exist_ok=True)
    (project_root / ".helix" / "matrix.yaml").write_text(
        'project:\n  size: "S"\n',
        encoding="utf-8",
    )
    (project_root / ".claude" / "agents" / "be-api.md").write_text(
        "---\nname: be-api\neffort: high\n---\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))

    result = skill_dispatcher.dispatch(
        skill_id="common/testing",
        task_text="normal task",
        recommended_agent="@be-api",
        references=[],
        catalog_path=catalog_path,
        skills_root=skills_root,
        db_path=db_path,
        dry_run=True,
    )

    captured = capsys.readouterr()
    assert result["agent"]["type"] == "subagent"
    assert "[helix] 警告: S タスクに effort=high のエージェントを使用" in captured.err
