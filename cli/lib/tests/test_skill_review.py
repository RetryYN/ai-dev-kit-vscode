from __future__ import annotations

import json
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import skill_review


def _entry(skill_id: str, status: str) -> dict:
    return {
        "id": skill_id,
        "title": skill_id.split("/")[-1],
        "summary": "summary",
        "phases": ["L2"],
        "tasks": ["design-security"],
        "triggers": ["認証"],
        "anti_triggers": [],
        "agent": "security",
        "similar": [],
        "references": [{"path": "skills/common/security/references/a.md", "title": "a"}],
        "source_hash": "a" * 64,
        "classification": {
            "status": status,
            "classified_at": "2026-04-16T03:00:00Z",
            "classifier_model": "gpt-5.4-mini",
            "confidence": 0.9,
        },
    }


def _write_jsonl(path: Path, entries: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(entry, ensure_ascii=False) for entry in entries) + "\n", encoding="utf-8")


def test_list_pending_entries_returns_only_pending(tmp_path: Path) -> None:
    path = tmp_path / "catalog.jsonl"
    _write_jsonl(path, [_entry("common/security", "pending"), _entry("common/testing", "approved")])

    pending = skill_review.list_pending_entries(path)

    assert len(pending) == 1
    assert pending[0]["id"] == "common/security"


def test_approve_entry_updates_pending_to_approved(tmp_path: Path) -> None:
    path = tmp_path / "catalog.jsonl"
    _write_jsonl(path, [_entry("common/security", "pending")])

    changed = skill_review.approve_entry(path, "common/security")

    assert changed is True
    updated = skill_review.list_pending_entries(path)
    assert updated == []


def test_approve_entry_returns_false_for_non_pending(tmp_path: Path) -> None:
    path = tmp_path / "catalog.jsonl"
    _write_jsonl(path, [_entry("common/security", "approved")])

    changed = skill_review.approve_entry(path, "common/security")

    assert changed is False


def test_approve_entry_raises_for_unknown_skill_id(tmp_path: Path) -> None:
    path = tmp_path / "catalog.jsonl"
    _write_jsonl(path, [_entry("common/security", "pending")])

    try:
        skill_review.approve_entry(path, "common/unknown")
        raised = False
    except skill_review.SkillEntryNotFoundError:
        raised = True

    assert raised is True


def test_approve_all_pending_updates_all_pending_entries(tmp_path: Path) -> None:
    path = tmp_path / "catalog.jsonl"
    _write_jsonl(
        path,
        [
            _entry("common/security", "pending"),
            _entry("common/testing", "pending"),
            _entry("workflow/design-doc", "approved"),
        ],
    )

    approved_ids = skill_review.approve_all_pending(path)

    assert approved_ids == ["common/security", "common/testing"]
    assert skill_review.list_pending_entries(path) == []


def test_missing_jsonl_returns_empty_and_approve_all_is_noop(tmp_path: Path) -> None:
    missing = tmp_path / "missing.jsonl"

    assert skill_review.list_pending_entries(missing) == []
    assert skill_review.approve_all_pending(missing) == []
