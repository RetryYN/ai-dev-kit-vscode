from __future__ import annotations

import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import schema_validator


def test_validate_phase_schema_accepts_minimal_valid_data() -> None:
    data = {
        "project": "demo",
        "current_phase": "L4",
        "gates": {
            "G0.5": {"status": "pending", "date": None},
            "G1": {"status": "passed", "date": "2026-04-04"},
            "G1.5": {"status": "skipped", "date": None},
            "G1R": {"status": "skipped", "date": None},
            "G2": {"status": "pending", "date": None},
            "G3": {"status": "pending", "date": None},
            "G4": {"status": "pending", "date": None},
            "G5": {"status": "pending", "date": None},
            "G6": {"status": "pending", "date": None},
            "G7": {"status": "pending", "date": None},
        },
        "sprint": {
            "current_step": None,
            "status": "active",
            "drive": None,
            "tracks": None,
            "phase": None,
            "steps": {".1a": {"status": "pending"}},
        },
        "reverse_gates": {
            "RG0": {"status": "pending", "date": None},
            "RG1": {"status": "pending", "date": None},
            "RG2": {"status": "pending", "date": None},
            "RG3": {"status": "pending", "date": None},
        },
        "reverse": {"status": None, "completed_at": None},
    }

    assert schema_validator.validate(data, "phase") == []


def test_validate_phase_schema_reports_missing_required() -> None:
    data = {"current_phase": "L2"}

    errors = schema_validator.validate(data, "phase.schema.json")

    assert any("missing required property 'project'" in e for e in errors)
    assert any("missing required property 'gates'" in e for e in errors)


def test_validate_gate_checks_schema_rejects_invalid_static_item() -> None:
    base_gate = {
        "name": "gate",
        "static": [{"name": "check-only-name"}],
        "ai": [{"role": "tl", "task": "check"}],
    }
    data = {
        "G0.5": base_gate,
        "G1": base_gate,
        "G1.5": base_gate,
        "G1R": base_gate,
        "G2": base_gate,
        "G3": base_gate,
        "G4": base_gate,
        "G5": base_gate,
        "G6": base_gate,
        "G7": base_gate,
    }

    errors = schema_validator.validate(data, "gate-checks")

    assert any("missing required property 'cmd'" in e for e in errors)


def test_validate_returns_schema_not_found() -> None:
    errors = schema_validator.validate({}, "missing-schema")

    assert len(errors) == 1
    assert "schema not found" in errors[0]
