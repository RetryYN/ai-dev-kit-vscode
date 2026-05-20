#!/usr/bin/env python3
"""契約: PLAN-097 §6 §7

workflow / harness DSL YAML を parse し、最小 schema を validate する。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ALLOWED_AGENT_ROLES = {
    "tl",
    "se",
    "pg",
    "fe",
    "qa",
    "security",
    "dba",
    "devops",
    "docs",
    "research",
    "legacy",
    "perf",
    "classifier",
    "recommender",
    "effort-classifier",
    "pmo-sonnet",
    "pmo-haiku",
    "pdm-tech-innovation",
    "pdm-marketing-innovation",
    "pdm-innovation-manager",
    "impl-sonnet",
    "pm-advisor",
    "tl-advisor",
    "pmo-helix-explorer",
    "pmo-helix-scout",
    "pmo-project-explorer",
    "pmo-project-scout",
    "pmo-tech-docs",
    "pmo-tech-fork",
    "pmo-tech-news",
}
ALLOWED_ESCALATION_LEVELS = {"L0", "L1", "L2", "L3"}
ALLOWED_ON_FAIL = {"reject", "review_inject", "escalate", "warn"}
ALLOWED_REVIEWER_TYPES = {"agent", "council", "human"}


def load_workflow(filepath: str | Path) -> dict[str, Any]:
    """Load workflow or harness DSL YAML and return the parsed mapping."""
    path = Path(filepath)
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if loaded is None:
        raise ValueError(f"workflow DSL is empty: {path}")
    if not isinstance(loaded, dict):
        raise ValueError(f"workflow DSL top-level must be a mapping: {path}")
    return loaded


def validate_workflow_schema(payload: dict[str, Any]) -> list[str]:
    """Return schema violations for workflow or harness DSL payloads."""
    if not isinstance(payload, dict):
        return ["top-level must be a mapping"]
    if "workflow_id" in payload:
        return _validate_workflow(payload)
    if "harness_id" in payload:
        return _validate_harness(payload)
    return ["expected workflow_id or harness_id at top-level"]


def _validate_workflow(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _require_string(payload, "workflow_id", errors)
    _require_int(payload, "schema_version", errors)
    _require_string(payload, "version", errors)
    _require_string(payload, "description", errors)
    _require_string_list(payload.get("drive"), "drive", errors, allow_empty=False)

    steps = payload.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append("steps must be a non-empty list")
        return errors

    seen_ids: set[str] = set()
    for index, step in enumerate(steps):
        label = f"steps[{index}]"
        if not isinstance(step, dict):
            errors.append(f"{label} must be a mapping")
            continue
        step_id = _require_string(step, "id", errors, prefix=label)
        _require_string(step, "name", errors, prefix=label)
        role = _require_string(step, "role", errors, prefix=label)
        _require_string(step, "condition", errors, prefix=label)
        escalation_level = _require_string(step, "escalation_level", errors, prefix=label)
        _require_bool(step, "mandatory", errors, prefix=label)
        _require_string_list(step.get("depends_on"), f"{label}.depends_on", errors, allow_empty=True)

        if step_id:
            if step_id in seen_ids:
                errors.append(f"{label}.id must be unique")
            seen_ids.add(step_id)
        if role and role not in ALLOWED_AGENT_ROLES:
            errors.append(f"{label}.role must be one of ROLE_MAP agent roles")
        if escalation_level and escalation_level not in ALLOWED_ESCALATION_LEVELS:
            errors.append(f"{label}.escalation_level must be one of {sorted(ALLOWED_ESCALATION_LEVELS)}")
    return errors


def _validate_harness(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _require_string(payload, "harness_id", errors)
    _require_int(payload, "schema_version", errors)
    _require_string(payload, "version", errors)
    _require_string(payload, "gate", errors)
    _require_string(payload, "description", errors)
    _require_string(payload, "workflow_ref", errors)

    checks = payload.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("checks must be a non-empty list")
    else:
        seen_ids: set[str] = set()
        for index, check in enumerate(checks):
            label = f"checks[{index}]"
            if not isinstance(check, dict):
                errors.append(f"{label} must be a mapping")
                continue
            check_id = _require_string(check, "id", errors, prefix=label)
            _require_string(check, "name", errors, prefix=label)
            _require_string(check, "condition", errors, prefix=label)
            on_fail = _require_string(check, "on_fail", errors, prefix=label)
            escalation_level = _require_string(check, "escalation_level", errors, prefix=label)
            reviewer_type = check.get("reviewer_type")

            if check_id:
                if check_id in seen_ids:
                    errors.append(f"{label}.id must be unique")
                seen_ids.add(check_id)
            if on_fail and on_fail not in ALLOWED_ON_FAIL:
                errors.append(f"{label}.on_fail must be one of {sorted(ALLOWED_ON_FAIL)}")
            if escalation_level and escalation_level not in ALLOWED_ESCALATION_LEVELS:
                errors.append(f"{label}.escalation_level must be one of {sorted(ALLOWED_ESCALATION_LEVELS)}")
            if reviewer_type is not None and reviewer_type not in ALLOWED_REVIEWER_TYPES:
                errors.append(f"{label}.reviewer_type must be one of {sorted(ALLOWED_REVIEWER_TYPES)}")

    escalation_engine = payload.get("escalation_engine")
    if not isinstance(escalation_engine, dict):
        errors.append("escalation_engine must be a mapping")
        return errors

    _require_bool(escalation_engine, "enabled", errors, prefix="escalation_engine")
    _require_string(escalation_engine, "current_level_expr", errors, prefix="escalation_engine")
    _require_string(escalation_engine, "trigger_expr", errors, prefix="escalation_engine")

    matrix = escalation_engine.get("reviewer_type_matrix")
    if not isinstance(matrix, dict):
        errors.append("escalation_engine.reviewer_type_matrix must be a mapping")
        return errors
    for level in sorted(ALLOWED_ESCALATION_LEVELS):
        value = matrix.get(level)
        if not isinstance(value, str) or value not in ALLOWED_REVIEWER_TYPES:
            errors.append(
                f"escalation_engine.reviewer_type_matrix.{level} must be one of {sorted(ALLOWED_REVIEWER_TYPES)}"
            )
    return errors


def _require_string(
    payload: dict[str, Any],
    field: str,
    errors: list[str],
    *,
    prefix: str | None = None,
) -> str | None:
    value = payload.get(field)
    location = f"{prefix}.{field}" if prefix else field
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{location} must be a non-empty string")
        return None
    return value


def _require_int(payload: dict[str, Any], field: str, errors: list[str], *, prefix: str | None = None) -> int | None:
    value = payload.get(field)
    location = f"{prefix}.{field}" if prefix else field
    if not isinstance(value, int):
        errors.append(f"{location} must be an integer")
        return None
    return value


def _require_bool(
    payload: dict[str, Any],
    field: str,
    errors: list[str],
    *,
    prefix: str | None = None,
) -> bool | None:
    value = payload.get(field)
    location = f"{prefix}.{field}" if prefix else field
    if not isinstance(value, bool):
        errors.append(f"{location} must be a boolean")
        return None
    return value


def _require_string_list(value: Any, location: str, errors: list[str], *, allow_empty: bool) -> list[str] | None:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{location} must be a list[str]")
        return None
    if not allow_empty and not value:
        errors.append(f"{location} must not be empty")
        return None
    return value
