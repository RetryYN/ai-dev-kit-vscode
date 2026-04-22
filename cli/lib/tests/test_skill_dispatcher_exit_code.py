import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
DISPATCHER_PATH = LIB_DIR / "skill_dispatcher.py"


def _write_catalog(tmp_root: Path) -> tuple[Path, Path]:
    skills_root = tmp_root / "skills"
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
        "---\n",
        encoding="utf-8",
    )

    catalog_path = tmp_root / "skill-catalog.json"
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


def _write_mock_codex(tmp_root: Path, exit_code: int) -> Path:
    script = tmp_root / "mock-helix-codex.sh"
    script.write_text(f"#!/usr/bin/env bash\nexit {exit_code}\n", encoding="utf-8")
    script.chmod(0o755)
    return script


def _run_dispatch_with_exit_code(exit_code: int) -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp_root = Path(td)
        skills_root, catalog_path = _write_catalog(tmp_root)
        db_path = tmp_root / ".helix" / "helix.db"
        mock_codex = _write_mock_codex(tmp_root, exit_code=exit_code)

        env = {**os.environ, "HELIX_CODEX_BIN": str(mock_codex)}
        proc = subprocess.run(
            [
                sys.executable,
                str(DISPATCHER_PATH),
                "--mode",
                "dispatch",
                "--skill-id",
                "common/testing",
                "--task",
                "x",
                "--catalog-path",
                str(catalog_path),
                "--skills-root",
                str(skills_root),
                "--db-path",
                str(db_path),
            ],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        return proc.returncode


class SkillDispatcherExitCodeTest(unittest.TestCase):
    def test_failed_dispatch_returns_exit_code_1(self) -> None:
        self.assertEqual(_run_dispatch_with_exit_code(124), 1)

    def test_successful_dispatch_returns_exit_code_0(self) -> None:
        self.assertEqual(_run_dispatch_with_exit_code(0), 0)


if __name__ == "__main__":
    unittest.main()
