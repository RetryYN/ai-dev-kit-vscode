from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "cli" / "lib" / "plan_validator.py"


def _run_validator(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(VALIDATOR), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )


def _write_plan(path: Path, frontmatter: dict[str, object]) -> Path:
    content = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
    path.write_text(f"---\n{content}---\n\n# Plan\n", encoding="utf-8")
    return path


def _warning_lines(stderr: str) -> list[str]:
    return [line for line in stderr.splitlines() if line.strip()]


def _assert_warns_on(stderr: str, field: str) -> None:
    assert any(f"field={field}" in line for line in _warning_lines(stderr)), stderr


def _assert_no_warn(stderr: str) -> None:
    assert _warning_lines(stderr) == [], stderr


def _base_frontmatter(created_at: str) -> dict[str, object]:
    return {
        "plan_id": "PLAN-123-valid",
        "title": "Valid Plan",
        "kind": "impl",
        "layer": "L4",
        "drive": "be",
        "status": "draft",
        "created": created_at,
        "agent_slots": [{"role": "se", "slot_label": "SE"}],
        "generates": [
            {
                "artifact_path": "cli/lib/plan_validator.py",
                "artifact_type": "python_module",
            }
        ],
        "dependencies": {
            "parent": None,
            "requires": [],
            "blocks": [],
        },
    }


def test_kind_enum_warn(tmp_path: Path) -> None:
    frontmatter = _base_frontmatter(datetime.now(timezone.utc).date().isoformat())
    frontmatter["kind"] = "invalid-kind"
    path = _write_plan(tmp_path / "PLAN-123-kind.md", frontmatter)

    result = _run_validator(path)

    assert result.returncode == 0
    _assert_warns_on(result.stderr, "kind")


def test_layer_enum_warn(tmp_path: Path) -> None:
    frontmatter = _base_frontmatter(datetime.now(timezone.utc).date().isoformat())
    frontmatter["layer"] = "R0"
    path = _write_plan(tmp_path / "PLAN-123-layer.md", frontmatter)

    result = _run_validator(path)

    assert result.returncode == 0
    _assert_warns_on(result.stderr, "layer")


def test_drive_enum_warn(tmp_path: Path) -> None:
    frontmatter = _base_frontmatter(datetime.now(timezone.utc).date().isoformat())
    frontmatter["drive"] = "mobile"
    path = _write_plan(tmp_path / "PLAN-123-drive.md", frontmatter)

    result = _run_validator(path)

    assert result.returncode == 0
    _assert_warns_on(result.stderr, "drive")


def test_role_enum_warn(tmp_path: Path) -> None:
    frontmatter = _base_frontmatter(datetime.now(timezone.utc).date().isoformat())
    frontmatter["agent_slots"] = [{"role": "codex-tl"}]
    path = _write_plan(tmp_path / "PLAN-123-role.md", frontmatter)

    result = _run_validator(path)

    assert result.returncode == 0
    _assert_warns_on(result.stderr, "agent_slots[0].role")


def test_artifact_type_enum_warn(tmp_path: Path) -> None:
    frontmatter = _base_frontmatter(datetime.now(timezone.utc).date().isoformat())
    frontmatter["generates"] = [{"artifact_path": "foo.txt", "artifact_type": "unknown"}]
    path = _write_plan(tmp_path / "PLAN-123-artifact.md", frontmatter)

    result = _run_validator(path)

    assert result.returncode == 0
    _assert_warns_on(result.stderr, "generates[0].artifact_type")


def test_workflow_phase_kind_mismatch_warn(tmp_path: Path) -> None:
    frontmatter = _base_frontmatter(datetime.now(timezone.utc).date().isoformat())
    frontmatter["layer"] = "cross"
    frontmatter["workflow_phase"] = "S2"
    path = _write_plan(tmp_path / "PLAN-123-phase.md", frontmatter)

    result = _run_validator(path)

    assert result.returncode == 0
    _assert_warns_on(result.stderr, "workflow_phase")


def test_plan_id_format_warn(tmp_path: Path) -> None:
    frontmatter = _base_frontmatter(datetime.now(timezone.utc).date().isoformat())
    frontmatter["plan_id"] = "PLAN-12"
    path = _write_plan(tmp_path / "PLAN-123-id.md", frontmatter)

    result = _run_validator(path)

    assert result.returncode == 0
    _assert_warns_on(result.stderr, "plan_id")


def test_required_field_missing_warn(tmp_path: Path) -> None:
    frontmatter = _base_frontmatter(datetime.now(timezone.utc).date().isoformat())
    del frontmatter["drive"]
    path = _write_plan(tmp_path / "PLAN-123-required.md", frontmatter)

    result = _run_validator(path)

    assert result.returncode == 0
    _assert_warns_on(result.stderr, "drive")


def test_reciprocal_dependency_warn(tmp_path: Path) -> None:
    created_at = datetime.now(timezone.utc).date().isoformat()
    plan_a = _base_frontmatter(created_at)
    plan_b = _base_frontmatter(created_at)
    plan_a["plan_id"] = "PLAN-199-a"
    plan_a["dependencies"] = {
        "parent": None,
        "requires": [],
        "blocks": ["PLAN-200-b"],
    }
    plan_b["plan_id"] = "PLAN-200-b"
    plan_b["dependencies"] = {
        "parent": None,
        "requires": [],
        "blocks": [],
    }

    path_a = _write_plan(tmp_path / "PLAN-199-a.md", plan_a)
    _write_plan(tmp_path / "PLAN-200-b.md", plan_b)

    result = _run_validator(path_a)

    assert result.returncode == 0
    _assert_warns_on(result.stderr, "dependencies.blocks")


def test_p1_exit_zero_with_warnings(tmp_path: Path) -> None:
    frontmatter = _base_frontmatter(datetime.now(timezone.utc).date().isoformat())
    frontmatter["kind"] = "wrong"
    frontmatter["layer"] = "S0"
    frontmatter["drive"] = "wrong"
    frontmatter["agent_slots"] = [{"role": "wrong"}]
    frontmatter["generates"] = [{"artifact_path": "foo", "artifact_type": "wrong"}]
    path = _write_plan(tmp_path / "PLAN-123-many.md", frontmatter)

    result = _run_validator(path)

    assert result.returncode == 0
    assert len(_warning_lines(result.stderr)) >= 5


def test_valid_plan_no_warn(tmp_path: Path) -> None:
    frontmatter = _base_frontmatter(datetime.now(timezone.utc).date().isoformat())
    path = _write_plan(tmp_path / "PLAN-123-valid.md", frontmatter)

    result = _run_validator(path)

    assert result.returncode == 0
    _assert_no_warn(result.stderr)
