"""Validation and normalization for HELIX review JSON output."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DIMENSIONS = ("density", "depth", "breadth", "accuracy", "maintainability")
DEFAULT_LEVEL = 3
DEFAULT_COMMENT = "legacy review output: default Lv3"


class ReviewOutputError(ValueError):
    """Raised when a review JSON payload does not match the HELIX contract."""


def extract_normalized_review_json(text: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Return the last schema-compliant JSON object from mixed model output."""
    candidates = list(_json_object_candidates(text))
    if not candidates:
        raise ReviewOutputError("No JSON object found in review output.")

    last_errors: list[str] = []
    for candidate in reversed(candidates):
        try:
            return normalize_review(candidate, schema)
        except ReviewOutputError as exc:
            last_errors = str(exc).splitlines()

    details = "\n".join(f"- {err}" for err in last_errors)
    raise ReviewOutputError(f"No schema-compliant review JSON found.\n{details}")


def normalize_review(obj: Any, schema: dict[str, Any]) -> dict[str, Any]:
    """Validate review JSON and fill legacy missing scores with Lv3 defaults."""
    if not isinstance(obj, dict):
        raise ReviewOutputError("Top-level JSON must be an object.")

    normalized = json.loads(json.dumps(obj, ensure_ascii=False))
    normalized.setdefault("overall_scores", _default_scores())

    errors = _validate_review_schema(normalized, schema)
    if errors:
        raise ReviewOutputError("\n".join(errors))

    normalized["overall_scores"] = _normalize_scores(
        normalized["overall_scores"], "overall_scores", require_all=True
    )
    for idx, finding in enumerate(normalized.get("findings", [])):
        if "dimension_scores" in finding:
            finding["dimension_scores"] = _normalize_scores(
                finding["dimension_scores"], f"findings[{idx}].dimension_scores", require_all=False
            )

    return normalized


def load_schema(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _json_object_candidates(text: str):
    decoder = json.JSONDecoder()
    for idx, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            yield obj


def _default_scores() -> list[dict[str, Any]]:
    return [
        {"dimension": dimension, "level": DEFAULT_LEVEL, "comment": DEFAULT_COMMENT}
        for dimension in DIMENSIONS
    ]


def _normalize_scores(scores: Any, path: str, *, require_all: bool) -> list[dict[str, Any]]:
    if not isinstance(scores, list):
        raise ReviewOutputError(f"{path} must be an array")

    by_dimension: dict[str, dict[str, Any]] = {}
    for idx, score in enumerate(scores):
        prefix = f"{path}[{idx}]"
        if not isinstance(score, dict):
            raise ReviewOutputError(f"{prefix} must be an object")
        dimension = score.get("dimension")
        level = score.get("level")
        comment = score.get("comment", "")
        if dimension not in DIMENSIONS:
            raise ReviewOutputError(f"{prefix}.dimension must be one of: {DIMENSIONS}")
        if type(level) is not int or not 1 <= level <= 5:
            raise ReviewOutputError(f"{prefix}.level must be an integer between 1 and 5")
        if not isinstance(comment, str):
            raise ReviewOutputError(f"{prefix}.comment must be a string")
        by_dimension[str(dimension)] = {
            "dimension": str(dimension),
            "level": level,
            "comment": comment,
        }

    if require_all:
        missing = [dimension for dimension in DIMENSIONS if dimension not in by_dimension]
        if missing:
            raise ReviewOutputError(f"{path} missing dimensions: {', '.join(missing)}")
        return [by_dimension[dimension] for dimension in DIMENSIONS]

    return [by_dimension[dimension] for dimension in DIMENSIONS if dimension in by_dimension]


def _validate_review_schema(obj: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = set(schema.get("required", []))
    allowed = set(schema.get("properties", {}).keys())

    missing = sorted(required - set(obj.keys()))
    if missing:
        errors.append(f"Missing top-level keys: {', '.join(missing)}")

    extra = sorted(set(obj.keys()) - allowed)
    if extra:
        errors.append(f"Unexpected top-level keys: {', '.join(extra)}")

    verdict = obj.get("verdict")
    verdict_enum = schema["properties"]["verdict"].get("enum", [])
    if verdict not in verdict_enum:
        errors.append(f"verdict must be one of: {verdict_enum}")

    summary = obj.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        errors.append("summary must be a non-empty string")

    _validate_score_array(obj.get("overall_scores"), "overall_scores", errors, require_all=True)
    _validate_findings(obj, schema, errors)
    _validate_next_steps(obj, errors)
    return errors


def _validate_findings(obj: dict[str, Any], schema: dict[str, Any], errors: list[str]) -> None:
    findings = obj.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be an array")
        return

    finding_schema = schema["properties"]["findings"]["items"]
    f_required = set(finding_schema.get("required", []))
    f_allowed = set(finding_schema.get("properties", {}).keys())
    severity_enum = finding_schema["properties"]["severity"].get("enum", [])

    for idx, finding in enumerate(findings):
        prefix = f"findings[{idx}]"
        if not isinstance(finding, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing_f = sorted(f_required - set(finding.keys()))
        if missing_f:
            errors.append(f"{prefix} missing keys: {', '.join(missing_f)}")
        extra_f = sorted(set(finding.keys()) - f_allowed)
        if extra_f:
            errors.append(f"{prefix} unexpected keys: {', '.join(extra_f)}")

        severity = finding.get("severity")
        if severity not in severity_enum:
            errors.append(f"{prefix}.severity must be one of: {severity_enum}")

        for key in ("title", "body", "file"):
            value = finding.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{prefix}.{key} must be a non-empty string")

        for key in ("line_start", "line_end"):
            value = finding.get(key)
            if not isinstance(value, int) or value < 1:
                errors.append(f"{prefix}.{key} must be an integer >= 1")

        conf = finding.get("confidence")
        if not isinstance(conf, (int, float)) or conf < 0 or conf > 1:
            errors.append(f"{prefix}.confidence must be between 0 and 1")

        recommendation = finding.get("recommendation")
        if recommendation is not None and not isinstance(recommendation, str):
            errors.append(f"{prefix}.recommendation must be a string")

        helix_phase = finding.get("helix_phase")
        if helix_phase is not None and not isinstance(helix_phase, str):
            errors.append(f"{prefix}.helix_phase must be a string")

        if "dimension_scores" in finding:
            _validate_score_array(
                finding.get("dimension_scores"), f"{prefix}.dimension_scores", errors, require_all=False
            )


def _validate_next_steps(obj: dict[str, Any], errors: list[str]) -> None:
    next_steps = obj.get("next_steps")
    if not isinstance(next_steps, list):
        errors.append("next_steps must be an array")
        return
    for i, step in enumerate(next_steps):
        if not isinstance(step, str) or not step.strip():
            errors.append(f"next_steps[{i}] must be a non-empty string")


def _validate_score_array(scores: Any, path: str, errors: list[str], *, require_all: bool) -> None:
    try:
        _normalize_scores(scores, path, require_all=require_all)
    except ReviewOutputError as exc:
        errors.extend(str(exc).splitlines())
