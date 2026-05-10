import json
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


def _write_agent(project_root: Path, agent_name: str, effort: str | None) -> None:
    agent_path = project_root / ".claude" / "agents" / f"{agent_name}.md"
    agent_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---", f"name: {agent_name}"]
    if effort is not None:
        lines.append(f"effort: {effort}")
    lines.extend(["---", ""])
    agent_path.write_text("\n".join(lines), encoding="utf-8")


def _dispatch_to_native_agent(
    monkeypatch,
    tmp_path: Path,
    *,
    agent_name: str,
    effort: str | None,
) -> dict:
    skills_root, catalog_path = _prepare_catalog(tmp_path)
    db_path = tmp_path / ".helix" / "helix.db"
    project_root = tmp_path / "project"
    _write_agent(project_root, agent_name, effort)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))

    return skill_dispatcher.dispatch(
        skill_id="common/testing",
        task_text="native task",
        recommended_agent=f"@{agent_name}",
        references=[],
        catalog_path=catalog_path,
        skills_root=skills_root,
        db_path=db_path,
        dry_run=False,
    )


def test_claude_native_hint_includes_high_effort_prefix_and_bundle(monkeypatch, tmp_path: Path) -> None:
    result = _dispatch_to_native_agent(
        monkeypatch,
        tmp_path,
        agent_name="be-api",
        effort="high",
    )

    assert result["outcome"] == "delegated_via_mention"
    assert "[effort=high]" in result["stdout"]
    assert "# Skill Context Bundle" in result["stdout"]
    assert "# test skill" in result["stdout"]


def test_claude_native_hint_includes_medium_effort_prefix(monkeypatch, tmp_path: Path) -> None:
    result = _dispatch_to_native_agent(
        monkeypatch,
        tmp_path,
        agent_name="ui-review",
        effort="medium",
    )

    assert "[effort=medium]" in result["stdout"]


def test_claude_native_hint_includes_low_effort_prefix(monkeypatch, tmp_path: Path) -> None:
    result = _dispatch_to_native_agent(
        monkeypatch,
        tmp_path,
        agent_name="quick-agent",
        effort="low",
    )

    assert "[effort=low]" in result["stdout"]


def test_claude_native_hint_omits_effort_prefix_when_effort_is_undefined(
    monkeypatch,
    tmp_path: Path,
) -> None:
    result = _dispatch_to_native_agent(
        monkeypatch,
        tmp_path,
        agent_name="unset-agent",
        effort=None,
    )

    assert "[effort=" not in result["stdout"]
    assert "# Skill Context Bundle" in result["stdout"]


def test_safe_reference_path_handles_repo_relative_no_double_concat(tmp_path: Path) -> None:
    repo_root = tmp_path
    skill_dir = repo_root / "skills" / "common" / "testing"
    skill_dir.mkdir(parents=True, exist_ok=True)

    resolved = skill_dispatcher._safe_reference_path(  # noqa: SLF001
        skill_dir,
        "skills/common/testing/SKILL.md",
    )

    expected = repo_root / "skills" / "common" / "testing" / "SKILL.md"
    assert resolved == expected


def test_safe_reference_path_rejects_traversal_outside_repo_root(tmp_path: Path) -> None:
    repo_root = tmp_path
    skill_dir = repo_root / "skills" / "common" / "testing"
    skill_dir.mkdir(parents=True, exist_ok=True)

    resolved = skill_dispatcher._safe_reference_path(  # noqa: SLF001
        skill_dir,
        "../../../../etc/passwd",
    )

    assert resolved is None
