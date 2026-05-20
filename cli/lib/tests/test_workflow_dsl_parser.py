from __future__ import annotations

import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import workflow_dsl_parser


WORKFLOW_PATH = REPO_ROOT / "workflows" / "l4-sprint-workflow.yaml"
HARNESS_PATH = REPO_ROOT / "harness" / "g4-gate-harness.yaml"


def test_load_workflow_returns_mapping() -> None:
    loaded = workflow_dsl_parser.load_workflow(WORKFLOW_PATH)

    assert loaded["workflow_id"] == "l4-sprint-standard"
    assert isinstance(loaded["steps"], list)


def test_validate_workflow_schema_accepts_l4_sprint_workflow() -> None:
    loaded = workflow_dsl_parser.load_workflow(WORKFLOW_PATH)

    assert workflow_dsl_parser.validate_workflow_schema(loaded) == []


def test_validate_workflow_schema_accepts_g4_gate_harness() -> None:
    loaded = workflow_dsl_parser.load_workflow(HARNESS_PATH)

    assert workflow_dsl_parser.validate_workflow_schema(loaded) == []


def test_validate_workflow_schema_reports_invalid_step_fields() -> None:
    payload = workflow_dsl_parser.load_workflow(WORKFLOW_PATH)
    payload["steps"][0]["role"] = "not-a-role"
    payload["steps"][0]["escalation_level"] = "L9"

    errors = workflow_dsl_parser.validate_workflow_schema(payload)

    assert "steps[0].role must be one of ROLE_MAP agent roles" in errors
    assert "steps[0].escalation_level must be one of ['L0', 'L1', 'L2', 'L3']" in errors


def test_load_workflow_rejects_non_mapping_yaml(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("- not-a-mapping\n", encoding="utf-8")

    with pytest.raises(ValueError, match="top-level must be a mapping"):
        workflow_dsl_parser.load_workflow(invalid)
