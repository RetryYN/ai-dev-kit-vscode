from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_helix_discovery_script_exists() -> None:
    path = REPO_ROOT / "cli" / "helix-discovery"
    assert path.exists()
    assert path.read_text(encoding="utf-8").startswith("#!/bin/bash")


def test_helix_scrum_shim_points_to_discovery() -> None:
    text = (REPO_ROOT / "cli" / "helix-scrum").read_text(encoding="utf-8")
    assert "HELIX_SUPPRESS_LEGACY_WARN" in text
    assert "helix discovery" in text
    assert 'exec "$SCRIPT_DIR/helix-discovery" "$@"' in text


def test_helix_discovery_skill_exists() -> None:
    skill = REPO_ROOT / "skills" / "agent-skills" / "helix-discovery" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert "name: helix-discovery" in text
    assert "D0, D1, D2, D3, D4" in text


def test_helix_scrum_skill_has_legacy_note() -> None:
    text = (REPO_ROOT / "skills" / "agent-skills" / "helix-scrum" / "SKILL.md").read_text(encoding="utf-8")
    assert "[DEPRECATED]" in text
    assert "helix-discovery" in text
