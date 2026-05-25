from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    from .plan_validator import VALID_LAYERS
    from .skill_catalog import _extract_frontmatter
except ImportError:  # pragma: no cover - script execution fallback
    from plan_validator import VALID_LAYERS  # type: ignore[no-redef]
    from skill_catalog import _extract_frontmatter  # type: ignore[no-redef]


_MIN_DESCRIPTION_LENGTH = 50
_VALID_SKILL_LAYERS = {layer for layer in VALID_LAYERS if re.fullmatch(r"L(?:[1-9]|1[0-4])", layer)}
_VALID_SKILL_LAYERS.add("all")


def _append_error(findings: list[dict[str, str]], field: str, message: str) -> None:
    findings.append({"level": "error", "field": field, "message": message})


def _append_warning(findings: list[dict[str, str]], field: str, message: str) -> None:
    findings.append({"level": "warning", "field": field, "message": message})


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_skill_frontmatter(frontmatter: dict) -> list[dict[str, str]]:
    """Validate SKILL.md frontmatter and return structured findings."""

    findings: list[dict[str, str]] = []

    for field in ("name", "description"):
        value = frontmatter.get(field)
        if value is None:
            _append_error(findings, field, f"missing field: {field}")
        elif not _is_non_empty_string(value):
            _append_error(findings, field, f"{field} must be a non-empty string")

    triggers = frontmatter.get("triggers")
    if triggers is None:
        _append_error(findings, "triggers", "missing field: triggers")
    elif not isinstance(triggers, list) or not triggers:
        _append_error(findings, "triggers", "triggers must be a non-empty list")

    skill_id = frontmatter.get("skill_id")
    if skill_id is None:
        _append_warning(findings, "skill_id", "skill_id is recommended")
    elif not _is_non_empty_string(skill_id):
        _append_error(findings, "skill_id", "skill_id must be a non-empty string")

    description = frontmatter.get("description")
    if isinstance(description, str) and len(description.strip()) < _MIN_DESCRIPTION_LENGTH:
        _append_warning(
            findings,
            "description",
            f"description too short: expected >= {_MIN_DESCRIPTION_LENGTH} chars",
        )

    metadata = frontmatter.get("metadata")
    if metadata is not None:
        if not isinstance(metadata, dict):
            _append_error(findings, "metadata", "metadata must be a mapping")
        else:
            helix_layer = metadata.get("helix_layer")
            if helix_layer is not None and helix_layer not in _VALID_SKILL_LAYERS:
                _append_error(
                    findings,
                    "metadata.helix_layer",
                    "invalid helix_layer: expected one of L1-L14 or all",
                )

    return findings


def scan_skills_directory(skills_root: Path) -> dict[str, Any]:
    """Scan skills_root recursively and aggregate SKILL.md frontmatter findings."""

    total = 0
    valid = 0
    invalid = 0
    errors: list[dict[str, Any]] = []

    for skill_md in sorted(skills_root.rglob("SKILL.md")):
        total += 1
        try:
            frontmatter = _extract_frontmatter(skill_md.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - parser failure passthrough
            invalid += 1
            errors.append(
                {
                    "file": skill_md.relative_to(skills_root).as_posix(),
                    "errors": [{"level": "error", "field": "frontmatter", "message": str(exc)}],
                }
            )
            continue

        if not isinstance(frontmatter, dict):
            invalid += 1
            errors.append(
                {
                    "file": skill_md.relative_to(skills_root).as_posix(),
                    "errors": [{"level": "error", "field": "frontmatter", "message": "missing YAML frontmatter"}],
                }
            )
            continue

        findings = validate_skill_frontmatter(frontmatter)
        error_findings = [finding for finding in findings if finding["level"] == "error"]
        if error_findings:
            invalid += 1
            errors.append({"file": skill_md.relative_to(skills_root).as_posix(), "errors": error_findings})
        else:
            valid += 1

    return {"total": total, "valid": valid, "invalid": invalid, "errors": errors}
