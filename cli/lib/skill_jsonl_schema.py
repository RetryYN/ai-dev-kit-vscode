from __future__ import annotations

import hashlib
import json
import re
from typing import Any


ALLOWED_AGENTS = {
    "tl",
    "se",
    "pg",
    "qa",
    "security",
    "dba",
    "devops",
    "docs",
    "research",
    "legacy",
    "perf",
    "fe-design",
    "fe-component",
    "fe-style",
    "fe-test",
    "fe-a11y",
}
ALLOWED_PHASES = {"L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "R0", "R1", "R2", "R3", "R4"}
ALLOWED_STATUS = {"pending", "approved", "manual"}

ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*/[a-z][a-z0-9-]*$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
ISO8601_UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")

REQUIRED_FIELDS = {
    "id",
    "title",
    "summary",
    "phases",
    "tasks",
    "triggers",
    "agent",
    "source_hash",
    "classification",
}
OPTIONAL_FIELDS = {"anti_triggers", "similar", "references"}
ALL_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS


class JsonlSchemaError(ValueError):
    """JSONL entry schema violation."""

    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"[{field}] {message}")


def _ensure(condition: bool, field: str, message: str) -> None:
    if not condition:
        raise JsonlSchemaError(field, message)


def _ensure_unique_list(values: list[Any], field: str) -> None:
    seen: set[str] = set()
    for idx, value in enumerate(values):
        try:
            key = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        except TypeError:
            key = repr(value)
        if key in seen:
            raise JsonlSchemaError(field, f"duplicate element at index {idx}")
        seen.add(key)


def _validate_references(references: Any) -> None:
    field = "references"
    _ensure(isinstance(references, list), field, "must be a list")
    _ensure_unique_list(references, field)

    for idx, ref in enumerate(references):
        item_field = f"{field}[{idx}]"
        _ensure(isinstance(ref, dict), item_field, "must be an object")

        unknown = set(ref) - {"path", "title", "summary"}
        _ensure(not unknown, item_field, f"unknown fields: {sorted(unknown)}")

        _ensure("path" in ref, item_field, "missing required field 'path'")
        _ensure("title" in ref, item_field, "missing required field 'title'")
        _ensure(isinstance(ref["path"], str), f"{item_field}.path", "must be a string")
        _ensure(isinstance(ref["title"], str), f"{item_field}.title", "must be a string")
        if "summary" in ref:
            _ensure(isinstance(ref["summary"], str), f"{item_field}.summary", "must be a string")


def validate_entry(entry: dict, *, known_task_ids: set[str] | None = None) -> None:
    """
    JSONL 1 行の dict を検証。違反があれば JsonlSchemaError を raise。
    known_task_ids が指定されていれば tasks[] の要素をそれと照合（未指定なら skip）。
    """
    _ensure(isinstance(entry, dict), "entry", "must be a dict")

    unknown_fields = set(entry) - ALL_FIELDS
    _ensure(not unknown_fields, "entry", f"unknown fields: {sorted(unknown_fields)}")

    missing_fields = REQUIRED_FIELDS - set(entry)
    _ensure(not missing_fields, "entry", f"missing required fields: {sorted(missing_fields)}")

    _ensure(isinstance(entry["id"], str), "id", "must be a string")
    _ensure(bool(ID_PATTERN.fullmatch(entry["id"])), "id", "invalid format")

    _ensure(isinstance(entry["title"], str), "title", "must be a string")

    _ensure(isinstance(entry["summary"], str), "summary", "must be a string")
    _ensure(len(entry["summary"]) <= 60, "summary", "must be 60 characters or fewer")

    phases = entry["phases"]
    _ensure(isinstance(phases, list), "phases", "must be a list")
    _ensure(len(phases) > 0, "phases", "must not be empty")
    _ensure(all(isinstance(p, str) for p in phases), "phases", "all elements must be strings")
    _ensure_unique_list(phases, "phases")
    unknown_phases = set(phases) - ALLOWED_PHASES
    _ensure(not unknown_phases, "phases", f"contains unknown values: {sorted(unknown_phases)}")

    tasks = entry["tasks"]
    _ensure(isinstance(tasks, list), "tasks", "must be a list")
    _ensure(len(tasks) > 0, "tasks", "must not be empty")
    _ensure(all(isinstance(t, str) for t in tasks), "tasks", "all elements must be strings")
    _ensure_unique_list(tasks, "tasks")
    if known_task_ids is not None:
        unknown_tasks = set(tasks) - known_task_ids
        _ensure(not unknown_tasks, "tasks", f"contains unknown task ids: {sorted(unknown_tasks)}")

    _ensure(isinstance(entry["triggers"], list), "triggers", "must be a list")
    _ensure_unique_list(entry["triggers"], "triggers")

    if "anti_triggers" in entry:
        _ensure(isinstance(entry["anti_triggers"], list), "anti_triggers", "must be a list")
        _ensure_unique_list(entry["anti_triggers"], "anti_triggers")

    if "similar" in entry:
        _ensure(isinstance(entry["similar"], list), "similar", "must be a list")
        _ensure_unique_list(entry["similar"], "similar")

    _ensure(isinstance(entry["agent"], str), "agent", "must be a string")
    _ensure(entry["agent"] in ALLOWED_AGENTS, "agent", "must be one of ALLOWED_AGENTS")

    _ensure(isinstance(entry["source_hash"], str), "source_hash", "must be a string")
    _ensure(bool(SHA256_PATTERN.fullmatch(entry["source_hash"])), "source_hash", "must be 64 lowercase hex chars")

    classification = entry["classification"]
    _ensure(isinstance(classification, dict), "classification", "must be an object")

    _ensure("status" in classification, "classification.status", "is required")
    _ensure("classified_at" in classification, "classification.classified_at", "is required")
    _ensure("classifier_model" in classification, "classification.classifier_model", "is required")

    status = classification["status"]
    _ensure(isinstance(status, str), "classification.status", "must be a string")
    _ensure(status in ALLOWED_STATUS, "classification.status", "must be one of ALLOWED_STATUS")

    classified_at = classification["classified_at"]
    _ensure(isinstance(classified_at, str), "classification.classified_at", "must be a string")
    _ensure(
        bool(ISO8601_UTC_PATTERN.fullmatch(classified_at)),
        "classification.classified_at",
        "must be ISO8601 UTC with Z suffix",
    )

    classifier_model = classification["classifier_model"]
    _ensure(isinstance(classifier_model, str), "classification.classifier_model", "must be a string")

    if "confidence" in classification:
        confidence = classification["confidence"]
        _ensure(isinstance(confidence, (int, float)), "classification.confidence", "must be numeric")
        _ensure(0.0 <= float(confidence) <= 1.0, "classification.confidence", "must be in range [0.0, 1.0]")

    if "references" in entry:
        _validate_references(entry["references"])


def compute_source_hash(skill_md_text: str) -> str:
    """SKILL.md 全文の SHA256 16進小文字を返す。"""
    return hashlib.sha256(skill_md_text.encode("utf-8")).hexdigest()
