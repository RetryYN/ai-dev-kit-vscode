from __future__ import annotations

from pathlib import Path

try:
    from .skill_catalog import read_jsonl_catalog, write_jsonl_catalog
except ImportError:  # pragma: no cover - script execution fallback
    from skill_catalog import read_jsonl_catalog, write_jsonl_catalog


class SkillEntryNotFoundError(ValueError):
    """指定 skill_id が JSONL catalog に存在しない。"""


def _classification_status(entry: dict) -> str:
    classification = entry.get("classification")
    if not isinstance(classification, dict):
        return ""
    status = classification.get("status")
    if not isinstance(status, str):
        return ""
    return status


def list_pending_entries(jsonl_path: Path) -> list[dict]:
    entries = read_jsonl_catalog(jsonl_path)
    return [entry for entry in entries if _classification_status(entry) == "pending"]


def approve_entry(jsonl_path: Path, skill_id: str) -> bool:
    entries = read_jsonl_catalog(jsonl_path)
    target_id = skill_id.strip()
    if not target_id:
        raise SkillEntryNotFoundError("skill_id is empty")

    for entry in entries:
        if entry.get("id") != target_id:
            continue
        if _classification_status(entry) != "pending":
            return False

        classification = entry.get("classification")
        if not isinstance(classification, dict):
            return False
        classification["status"] = "approved"
        write_jsonl_catalog(entries, jsonl_path)
        return True

    raise SkillEntryNotFoundError(f"skill_id not found: {target_id}")


def approve_all_pending(jsonl_path: Path) -> list[str]:
    entries = read_jsonl_catalog(jsonl_path)
    approved_ids: list[str] = []

    for entry in entries:
        if _classification_status(entry) != "pending":
            continue
        classification = entry.get("classification")
        if not isinstance(classification, dict):
            continue
        classification["status"] = "approved"
        entry_id = entry.get("id")
        if isinstance(entry_id, str) and entry_id:
            approved_ids.append(entry_id)

    if approved_ids:
        write_jsonl_catalog(entries, jsonl_path)
    return approved_ids
