"""decisions.yaml schema validator (PLAN-002 Sprint 2a)。

schema:
  version: int (== 1)
  metadata:
    scope_hash: sha256 hex 64
    source_hash: sha256 hex 64
    schema_version: int
  decisions: list of:
    candidate_id: str
    schema_version: int
    scope_hash: sha256 hex 64
    decision: enum keep|remove|merge|deprecate
    rationale: str
    evidence:
      source: str
      hash: str
      redacted: bool
    fail_safe_action: enum skip|quarantine|manual_review
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

SHA256_HEX_RE = re.compile(r"^[a-f0-9]{64}$")
DECISION_ENUM = ("keep", "remove", "merge", "deprecate")
FAIL_SAFE_ENUM = ("skip", "quarantine", "manual_review")


@dataclass
class ValidationResult:
    success: bool
    errors: list[str] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    metadata: dict | None = None


def _validate_metadata(metadata, errors):
    if not isinstance(metadata, dict):
        errors.append("metadata must be a dict")
        return False
    for key in ("scope_hash", "source_hash"):
        val = metadata.get(key)
        if not isinstance(val, str) or not SHA256_HEX_RE.match(val):
            errors.append(f"metadata.{key} must be sha256 hex 64 chars")
    sv = metadata.get("schema_version")
    if not isinstance(sv, int):
        errors.append("metadata.schema_version must be int")


def _validate_decision(idx, decision, errors):
    if not isinstance(decision, dict):
        errors.append(f"decisions[{idx}] must be a dict")
        return

    cid = decision.get("candidate_id")
    if not isinstance(cid, str) or not cid:
        errors.append(f"decisions[{idx}].candidate_id must be non-empty str")

    sv = decision.get("schema_version")
    if not isinstance(sv, int):
        errors.append(f"decisions[{idx}].schema_version must be int")

    sh = decision.get("scope_hash")
    if not isinstance(sh, str) or not SHA256_HEX_RE.match(sh):
        errors.append(f"decisions[{idx}].scope_hash must be sha256 hex 64")

    d = decision.get("decision")
    if d not in DECISION_ENUM:
        errors.append(
            f"decisions[{idx}].decision must be one of {DECISION_ENUM}"
        )

    rationale = decision.get("rationale")
    if not isinstance(rationale, str):
        errors.append(f"decisions[{idx}].rationale must be str")

    ev = decision.get("evidence")
    if isinstance(ev, dict):
        for ek in ("source", "hash"):
            if not isinstance(ev.get(ek), str):
                errors.append(f"decisions[{idx}].evidence.{ek} must be str")
        if not isinstance(ev.get("redacted"), bool):
            errors.append(f"decisions[{idx}].evidence.redacted must be bool")
    else:
        errors.append(f"decisions[{idx}].evidence must be dict")

    fa = decision.get("fail_safe_action")
    if fa not in FAIL_SAFE_ENUM:
        errors.append(
            f"decisions[{idx}].fail_safe_action must be one of {FAIL_SAFE_ENUM}"
        )


def validate_decisions_yaml(yaml_path) -> ValidationResult:
    """decisions.yaml をロードして schema 検証。

    Args:
        yaml_path: Path or str の decisions.yaml ファイルパス

    Returns:
        ValidationResult: success/errors/decisions/metadata
    """
    path = Path(yaml_path)
    if not path.exists():
        return ValidationResult(
            success=False,
            errors=[f"file not found: {path}"],
        )

    try:
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
    except Exception as e:
        return ValidationResult(
            success=False,
            errors=[f"yaml load error: {e}"],
        )

    if not isinstance(data, dict):
        return ValidationResult(
            success=False,
            errors=["top-level must be a dict"],
        )

    errors: list[str] = []

    if data.get("version") != 1:
        errors.append("version must be 1")

    metadata = data.get("metadata")
    _validate_metadata(metadata, errors)

    decisions_raw = data.get("decisions", [])
    if not isinstance(decisions_raw, list):
        errors.append("decisions must be a list")
        decisions_raw = []

    valid_decisions = []
    for i, dec in enumerate(decisions_raw):
        before = len(errors)
        _validate_decision(i, dec, errors)
        if len(errors) == before and isinstance(dec, dict):
            valid_decisions.append(dec)

    return ValidationResult(
        success=len(errors) == 0,
        errors=errors,
        decisions=valid_decisions,
        metadata=metadata if isinstance(metadata, dict) else None,
    )
