from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
PLAN_LINT = REPO_ROOT / "cli" / "lib" / "plan_lint.py"
LIB_DIR = REPO_ROOT / "cli" / "lib"

if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import plan_lint


def _write_plan(path: Path, frontmatter: dict[str, object]) -> Path:
    content = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
    path.write_text(f"---\n{content}---\n\n# Plan\n", encoding="utf-8")
    return path


def _run_plan_lint(path: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(PLAN_LINT), *extra_args, str(path)],
        capture_output=True,
        text=True,
        check=False,
    )


def _base_process_frontmatter(created_at: str) -> dict[str, object]:
    return {
        "plan_id": "process-2026-06-01-strict-frontmatter-check",
        "title": "Process Sample Plan",
        "plan_scope": "process",
        "workflow_chain": "内部監査 -> Discovery -> Reverse",
        "kind": "research",
        "layer": "L1",
        "drive": "discovery",
        "status": "draft",
        "created": created_at,
        "contains_action_plans": [],
        "forward_return": "Forward L4",
        "agent_slots": [],
        "generates": [],
        "dependencies": {
            "parent": None,
            "requires": [],
            "blocks": [],
        },
    }


def test_strict_frontmatter_promotes_process_scope_required_fields_to_error(tmp_path: Path) -> None:
    frontmatter = _base_process_frontmatter(datetime.now(timezone.utc).date().isoformat())
    del frontmatter["workflow_chain"]
    del frontmatter["contains_action_plans"]
    del frontmatter["forward_return"]
    path = _write_plan(tmp_path / "process-2026-06-01-strict-frontmatter-check.md", frontmatter)

    result = _run_plan_lint(path, "--strict-frontmatter")

    assert result.returncode == 1
    assert "field=workflow_chain" in result.stderr
    assert "field=forward_return" in result.stderr
    assert "field=contains_action_plans" in result.stderr


def test_non_strict_frontmatter_fails_closed_when_process_forward_return_is_missing(tmp_path: Path) -> None:
    frontmatter = _base_process_frontmatter(datetime.now(timezone.utc).date().isoformat())
    del frontmatter["forward_return"]
    path = _write_plan(tmp_path / "process-2026-06-01-warning-frontmatter-check.md", frontmatter)

    result = _run_plan_lint(path)

    assert result.returncode == 1
    assert "field=forward_return" in result.stderr


def test_non_strict_frontmatter_passes_when_process_forward_return_is_present(tmp_path: Path) -> None:
    frontmatter = _base_process_frontmatter(datetime.now(timezone.utc).date().isoformat())
    path = _write_plan(tmp_path / "process-2026-06-01-forward-return-present.md", frontmatter)

    result = _run_plan_lint(path)

    assert result.returncode == 0
    assert "PASS: no contradictory status assertions" in result.stdout


def test_parse_args_accepts_strict_frontmatter_flag(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["plan_lint.py", "--strict-frontmatter", "docs/plans/process/process.md"],
    )

    args = plan_lint._parse_args()

    assert args.strict_frontmatter is True
