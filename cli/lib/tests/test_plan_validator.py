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


def _assert_warn_contains(stderr: str, text: str) -> None:
    assert any(text in line for line in _warning_lines(stderr)), stderr


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


def test_cycle_detection_no_cycle(tmp_path: Path) -> None:
    created_at = datetime.now(timezone.utc).date().isoformat()
    plan_a = _base_frontmatter(created_at)
    plan_b = _base_frontmatter(created_at)
    plan_c = _base_frontmatter(created_at)
    plan_a["plan_id"] = "PLAN-301-a"
    plan_b["plan_id"] = "PLAN-302-b"
    plan_c["plan_id"] = "PLAN-303-c"
    plan_a["dependencies"] = {"parent": None, "requires": ["PLAN-302-b"], "blocks": []}
    plan_b["dependencies"] = {"parent": None, "requires": ["PLAN-303-c"], "blocks": []}
    plan_c["dependencies"] = {"parent": None, "requires": [], "blocks": []}

    path_a = _write_plan(tmp_path / "PLAN-301-a.md", plan_a)
    _write_plan(tmp_path / "PLAN-302-b.md", plan_b)
    _write_plan(tmp_path / "PLAN-303-c.md", plan_c)

    result = _run_validator(path_a)

    assert result.returncode == 0
    _assert_no_warn(result.stderr)


def test_cycle_detection_2node(tmp_path: Path) -> None:
    created_at = datetime.now(timezone.utc).date().isoformat()
    plan_a = _base_frontmatter(created_at)
    plan_b = _base_frontmatter(created_at)
    plan_a["plan_id"] = "PLAN-311-a"
    plan_b["plan_id"] = "PLAN-312-b"
    plan_a["dependencies"] = {"parent": None, "requires": ["PLAN-312-b"], "blocks": []}
    plan_b["dependencies"] = {"parent": None, "requires": ["PLAN-311-a"], "blocks": []}

    path_a = _write_plan(tmp_path / "PLAN-311-a.md", plan_a)
    _write_plan(tmp_path / "PLAN-312-b.md", plan_b)

    result = _run_validator(path_a)

    assert result.returncode == 0
    _assert_warns_on(result.stderr, "dependencies")
    _assert_warn_contains(result.stderr, "cycle detected: PLAN-311-a -> PLAN-312-b -> PLAN-311-a")


def test_cycle_detection_3node(tmp_path: Path) -> None:
    created_at = datetime.now(timezone.utc).date().isoformat()
    plan_a = _base_frontmatter(created_at)
    plan_b = _base_frontmatter(created_at)
    plan_c = _base_frontmatter(created_at)
    plan_a["plan_id"] = "PLAN-321-a"
    plan_b["plan_id"] = "PLAN-322-b"
    plan_c["plan_id"] = "PLAN-323-c"
    plan_a["dependencies"] = {"parent": None, "requires": ["PLAN-322-b"], "blocks": []}
    plan_b["dependencies"] = {"parent": None, "requires": ["PLAN-323-c"], "blocks": []}
    plan_c["dependencies"] = {"parent": None, "requires": ["PLAN-321-a"], "blocks": []}

    path_a = _write_plan(tmp_path / "PLAN-321-a.md", plan_a)
    _write_plan(tmp_path / "PLAN-322-b.md", plan_b)
    _write_plan(tmp_path / "PLAN-323-c.md", plan_c)

    result = _run_validator(path_a)

    assert result.returncode == 0
    _assert_warns_on(result.stderr, "dependencies")
    _assert_warn_contains(
        result.stderr,
        "cycle detected: PLAN-321-a -> PLAN-322-b -> PLAN-323-c -> PLAN-321-a",
    )


def test_cycle_detection_self_edge(tmp_path: Path) -> None:
    frontmatter = _base_frontmatter(datetime.now(timezone.utc).date().isoformat())
    frontmatter["dependencies"] = {"parent": None, "requires": ["PLAN-123-valid"], "blocks": []}
    path = _write_plan(tmp_path / "PLAN-123-self-edge.md", frontmatter)

    result = _run_validator(path)

    assert result.returncode == 0
    _assert_warns_on(result.stderr, "dependencies.requires")
    _assert_warn_contains(result.stderr, "self-edge in requires forbidden")


def test_reciprocal_blocks_nonexistent(tmp_path: Path) -> None:
    frontmatter = _base_frontmatter(datetime.now(timezone.utc).date().isoformat())
    frontmatter["dependencies"] = {
        "parent": None,
        "requires": [],
        "blocks": ["PLAN-999-never-exist"],
    }
    path = _write_plan(tmp_path / "PLAN-123-missing-block.md", frontmatter)

    result = _run_validator(path)

    assert result.returncode == 0
    _assert_warns_on(result.stderr, "dependencies.blocks")
    _assert_warn_contains(result.stderr, "PLAN-999-never-exist does not exist (referenced in blocks)")


def test_p2_exit_zero_with_warnings(tmp_path: Path) -> None:
    created_at = datetime.now(timezone.utc).date().isoformat()
    plan_a = _base_frontmatter(created_at)
    plan_b = _base_frontmatter(created_at)
    plan_a["plan_id"] = "PLAN-331-a"
    plan_b["plan_id"] = "PLAN-332-b"
    plan_a["dependencies"] = {"parent": None, "requires": ["PLAN-332-b"], "blocks": []}
    plan_b["dependencies"] = {"parent": None, "requires": ["PLAN-331-a"], "blocks": []}

    path_a = _write_plan(tmp_path / "PLAN-331-a.md", plan_a)
    _write_plan(tmp_path / "PLAN-332-b.md", plan_b)

    result = _run_validator(path_a)

    assert result.returncode == 0
    assert len(_warning_lines(result.stderr)) >= 1


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
