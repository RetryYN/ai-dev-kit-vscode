from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK = REPO_ROOT / ".claude" / "hooks" / "posttooluse-code-catalog-register.sh"


def _init_repo(project_root: Path) -> None:
    (project_root / "cli/lib").mkdir(parents=True, exist_ok=True)
    (project_root / "cli/config").mkdir(parents=True, exist_ok=True)
    (project_root / "cli/lib/alpha.py").write_text(
        "# @helix:index id=hook.alpha domain=cli/lib summary=hook alpha\n"
        "def alpha():\n"
        "    return 'ok'\n",
        encoding="utf-8",
    )
    (project_root / "cli/lib/beta.py").write_text(
        "# @helix:index id=hook.beta domain=cli/lib summary=hook beta\n"
        "def beta():\n"
        "    return 'ok'\n",
        encoding="utf-8",
    )
    (project_root / "cli/config/functional-registry.yaml").write_text("entries: []\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=project_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "qa@example.com"], cwd=project_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "QA"], cwd=project_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "add", "cli/lib/alpha.py", "cli/lib/beta.py", "cli/config/functional-registry.yaml"],
        cwd=project_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "commit", "-m", "init"], cwd=project_root, check=True, capture_output=True)


def _run_hook(project_root: Path, payload: dict[str, object]) -> dict[str, object]:
    proc = subprocess.run(
        ["/bin/bash", str(HOOK)],
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        cwd=project_root,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(project_root)},
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _catalog_entries(project_root: Path) -> list[dict[str, object]]:
    jsonl_path = project_root / ".helix" / "cache" / "code-catalog.jsonl"
    return [
        json.loads(line)
        for line in jsonl_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_hook_updates_catalog_and_warns_when_functional_registry_missing(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    _init_repo(project_root)

    payload = {"tool_name": "Write", "tool_input": {"file_path": "cli/lib/alpha.py"}}
    result = _run_hook(project_root, payload)

    assert result["decision"] == "continue"
    assert "functional-registry" in str(result["systemMessage"])

    entries = _catalog_entries(project_root)
    assert [entry["id"] for entry in entries] == ["hook.alpha"]
    assert entries[0]["path"] == "cli/lib/alpha.py"

    db_path = project_root / ".helix" / "helix.db"
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM code_index WHERE id = ? AND path = ?",
            ("hook.alpha", "cli/lib/alpha.py"),
        ).fetchone()
    assert row == (1,)


def test_hook_is_idempotent_for_same_path(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    _init_repo(project_root)

    payload = {"tool_name": "Write", "tool_input": {"file_path": "cli/lib/alpha.py"}}
    first = _run_hook(project_root, payload)
    second = _run_hook(project_root, payload)

    assert first["decision"] == "continue"
    assert second["decision"] == "continue"

    entries = _catalog_entries(project_root)
    assert [entry["id"] for entry in entries] == ["hook.alpha"]

    db_path = project_root / ".helix" / "helix.db"
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) FROM code_index WHERE id = ?", ("hook.alpha",)).fetchone()
    assert row == (1,)


def test_hook_only_upserts_target_path_without_rebuilding_other_entries(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    _init_repo(project_root)

    alpha_payload = {"tool_name": "Write", "tool_input": {"file_path": "cli/lib/alpha.py"}}
    beta_payload = {"tool_name": "Write", "tool_input": {"file_path": "cli/lib/beta.py"}}

    assert _run_hook(project_root, alpha_payload)["decision"] == "continue"
    assert _run_hook(project_root, beta_payload)["decision"] == "continue"

    before_beta = next(
        entry for entry in _catalog_entries(project_root) if entry["path"] == "cli/lib/beta.py"
    )

    (project_root / "cli/lib/alpha.py").write_text(
        "# @helix:index id=hook.alpha domain=cli/lib summary=hook alpha updated\n"
        "def alpha():\n"
        "    return 'updated'\n",
        encoding="utf-8",
    )

    assert _run_hook(project_root, alpha_payload)["decision"] == "continue"

    entries = _catalog_entries(project_root)
    after_beta = next(entry for entry in entries if entry["path"] == "cli/lib/beta.py")
    after_alpha = next(entry for entry in entries if entry["path"] == "cli/lib/alpha.py")

    assert before_beta == after_beta
    assert after_alpha["summary"] == "hook alpha updated"
