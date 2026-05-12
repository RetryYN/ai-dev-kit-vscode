from __future__ import annotations

from pathlib import Path

import pytest

from detectors.axis_07_doc_drift import Axis07DocDrift


def _write_project(root: Path) -> None:
    (root / "helix").mkdir(parents=True, exist_ok=True)
    (root / "skills").mkdir(parents=True, exist_ok=True)
    (root / "cli" / "config").mkdir(parents=True, exist_ok=True)
    (root / "cli").mkdir(parents=True, exist_ok=True)

    (root / "CLAUDE.md").write_text(
        "# CLAUDE\n\n"
        "model: gpt-5.5\n"
        "model-backup: gpt-5.4\n",
        encoding="utf-8",
    )
    (root / "AGENTS.md").write_text(
        "# AGENTS\n\n"
        "model: gpt-5.6\n"
        "phase: G8\n",
        encoding="utf-8",
    )
    (root / "helix" / "HELIX_CORE.md").write_text(
        "# HELIX CORE\n\n"
        "G2\n"
        "L4\n"
        "RGC\n",
        encoding="utf-8",
    )
    (root / "cli" / "ROLE_MAP.md").write_text(
        "# ROLE MAP\n\n"
        "| role | model | phase |\n"
        "| tl | gpt-5.5 | G2 |\n"
        "| se | gpt-5.4 | G4 |\n"
        "| pg | gpt-5.3-codex-spark | L4 |\n",
        encoding="utf-8",
    )
    (root / "skills" / "SKILL_MAP.md").write_text(
        "# SKILL MAP\n\n"
        "## Roles\n"
        "| tl | se | pe |\n",
        encoding="utf-8",
    )
    (root / "cli" / "config" / "models.yaml").write_text(
        "default_primary: gpt-5.5\n"
        "default_fallback: gpt-5.4\n"
        "roles:\n"
        "  tl: gpt-5.5\n"
        "  se: gpt-5.4\n"
        "  pg: gpt-5.3-codex-spark\n",
        encoding="utf-8",
    )


def test_axis_07_detects_model_role_and_phase_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path / "project"
    _write_project(project_root)
    db_path = project_root / ".helix" / "helix.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))

    result = Axis07DocDrift().run(db_path)

    assert result.verdict == "failed"
    kinds = {finding["kind"] for finding in result.findings}
    assert {"model_drift", "role_drift", "term_inconsistency"} <= kinds

    model_finding = next(finding for finding in result.findings if finding["kind"] == "model_drift")
    assert model_finding["source"] == "AGENTS.md"
    assert model_finding["observed"] == ["gpt-5.6"]

    role_finding = next(finding for finding in result.findings if finding["kind"] == "role_drift")
    assert role_finding["source"] == "skills/SKILL_MAP.md"
    assert "pg" in role_finding["expected"]
    assert "pe" in role_finding["observed"]

    phase_finding = next(finding for finding in result.findings if finding["kind"] == "term_inconsistency")
    assert phase_finding["source"] == "CLAUDE.md, AGENTS.md, skills/SKILL_MAP.md"
    assert phase_finding["observed"] == ["G8"]
