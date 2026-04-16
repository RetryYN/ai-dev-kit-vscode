from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import skill_jsonl_schema


def _valid_entry() -> dict:
    return {
        "id": "common/security",
        "title": "セキュリティ",
        "summary": "脆弱性対策と認証認可実装の指針",
        "phases": ["L2", "L4", "L6"],
        "tasks": ["design-security", "review-security"],
        "triggers": ["認証", "認可", "OWASP"],
        "anti_triggers": ["UI"],
        "agent": "security",
        "similar": ["workflow/compliance"],
        "references": [
            {
                "path": "references/checklist.md",
                "title": "チェックリスト",
                "summary": "要点",
            }
        ],
        "source_hash": "a" * 64,
        "classification": {
            "status": "approved",
            "classified_at": "2026-04-16T03:00:00Z",
            "classifier_model": "gpt-5.4-mini",
            "confidence": 0.92,
        },
    }


def test_validate_entry_accepts_full_valid_entry() -> None:
    entry = _valid_entry()

    skill_jsonl_schema.validate_entry(entry, known_task_ids={"design-security", "review-security", "fix-security"})



def test_validate_entry_rejects_unknown_field() -> None:
    entry = _valid_entry()
    entry["unknown"] = "x"

    with pytest.raises(skill_jsonl_schema.JsonlSchemaError):
        skill_jsonl_schema.validate_entry(entry)



def test_validate_entry_rejects_missing_required_field() -> None:
    entry = _valid_entry()
    del entry["agent"]

    with pytest.raises(skill_jsonl_schema.JsonlSchemaError):
        skill_jsonl_schema.validate_entry(entry)


@pytest.mark.parametrize("invalid_id", ["Common/security", "common/security!", "common-security"])
def test_validate_entry_rejects_invalid_id_format(invalid_id: str) -> None:
    entry = _valid_entry()
    entry["id"] = invalid_id

    with pytest.raises(skill_jsonl_schema.JsonlSchemaError):
        skill_jsonl_schema.validate_entry(entry)



def test_validate_entry_rejects_invalid_agent() -> None:
    entry = _valid_entry()
    entry["agent"] = "frontend"

    with pytest.raises(skill_jsonl_schema.JsonlSchemaError):
        skill_jsonl_schema.validate_entry(entry)



def test_validate_entry_rejects_unknown_phase() -> None:
    entry = _valid_entry()
    entry["phases"] = ["L2", "L9"]

    with pytest.raises(skill_jsonl_schema.JsonlSchemaError):
        skill_jsonl_schema.validate_entry(entry)



def test_validate_entry_rejects_duplicated_tasks() -> None:
    entry = _valid_entry()
    entry["tasks"] = ["design-security", "design-security"]

    with pytest.raises(skill_jsonl_schema.JsonlSchemaError):
        skill_jsonl_schema.validate_entry(entry)



def test_validate_entry_rejects_unknown_task_id_when_catalog_is_given() -> None:
    entry = _valid_entry()

    with pytest.raises(skill_jsonl_schema.JsonlSchemaError):
        skill_jsonl_schema.validate_entry(entry, known_task_ids={"design-security"})



def test_validate_entry_rejects_summary_longer_than_60_chars() -> None:
    entry = _valid_entry()
    entry["summary"] = "a" * 61

    with pytest.raises(skill_jsonl_schema.JsonlSchemaError):
        skill_jsonl_schema.validate_entry(entry)



def test_validate_entry_rejects_invalid_source_hash_length() -> None:
    entry = _valid_entry()
    entry["source_hash"] = "a" * 63

    with pytest.raises(skill_jsonl_schema.JsonlSchemaError):
        skill_jsonl_schema.validate_entry(entry)



def test_validate_entry_rejects_invalid_classification_status() -> None:
    entry = _valid_entry()
    entry["classification"]["status"] = "staged"

    with pytest.raises(skill_jsonl_schema.JsonlSchemaError):
        skill_jsonl_schema.validate_entry(entry)



def test_validate_entry_rejects_out_of_range_classification_confidence() -> None:
    entry = _valid_entry()
    entry["classification"]["confidence"] = 1.5

    with pytest.raises(skill_jsonl_schema.JsonlSchemaError):
        skill_jsonl_schema.validate_entry(entry)



def test_validate_entry_accepts_manual_classification_without_confidence() -> None:
    entry = _valid_entry()
    entry["classification"] = {
        "status": "manual",
        "classified_at": "2026-04-16T03:00:00.123Z",
        "classifier_model": "human",
    }

    skill_jsonl_schema.validate_entry(entry)



def test_compute_source_hash_returns_lowercase_sha256_hex() -> None:
    digest = skill_jsonl_schema.compute_source_hash("# SKILL\nhello\n")

    assert re.fullmatch(r"[0-9a-f]{64}", digest)



def test_validate_entry_rejects_invalid_reference_shape() -> None:
    entry = _valid_entry()
    entry["references"] = [{"path": "x.md"}]

    with pytest.raises(skill_jsonl_schema.JsonlSchemaError):
        skill_jsonl_schema.validate_entry(entry)


@pytest.mark.parametrize("reference", ["references/a.md", 42, ["nested"]])
def test_validate_entry_rejects_reference_items_that_are_not_dict(reference) -> None:
    entry = _valid_entry()
    entry["references"] = [reference]

    with pytest.raises(skill_jsonl_schema.JsonlSchemaError):
        skill_jsonl_schema.validate_entry(entry)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("path", ""),
        ("path", "   "),
        ("title", ""),
        ("title", "   "),
    ],
)
def test_validate_entry_rejects_empty_reference_path_or_title(field: str, value: str) -> None:
    entry = _valid_entry()
    entry["references"] = [{"path": "references/a.md", "title": "doc"}]
    entry["references"][0][field] = value

    with pytest.raises(skill_jsonl_schema.JsonlSchemaError):
        skill_jsonl_schema.validate_entry(entry)


@pytest.mark.parametrize(
    "classified_at",
    [
        "2026-04-16T03:00:00",
        "2026-04-16T03:00:00+00:00",
        "2026-04-16T03:00:00.Z",
    ],
)
def test_validate_entry_rejects_invalid_classified_at_format(classified_at: str) -> None:
    entry = _valid_entry()
    entry["classification"]["classified_at"] = classified_at

    with pytest.raises(skill_jsonl_schema.JsonlSchemaError):
        skill_jsonl_schema.validate_entry(entry)


def test_validate_entry_rejects_string_confidence() -> None:
    entry = _valid_entry()
    entry["classification"]["confidence"] = "0.8"

    with pytest.raises(skill_jsonl_schema.JsonlSchemaError):
        skill_jsonl_schema.validate_entry(entry)
