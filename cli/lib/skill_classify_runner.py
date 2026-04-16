from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re

try:
    from .skill_catalog import build_jsonl_catalog, read_jsonl_catalog, write_jsonl_catalog
    from .skill_classifier import ClassifierError, MODEL_NAME, classify_skill
    from .skill_jsonl_schema import compute_source_hash, validate_entry
except ImportError:  # pragma: no cover - script execution fallback
    from skill_catalog import build_jsonl_catalog, read_jsonl_catalog, write_jsonl_catalog
    from skill_classifier import ClassifierError, MODEL_NAME, classify_skill
    from skill_jsonl_schema import compute_source_hash, validate_entry


_TASK_ID_LINE = re.compile(r"^\s{2}([A-Za-z0-9][A-Za-z0-9-]*):\s*$")


def _now_iso8601_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_known_task_ids(task_catalog_path: Path | None = None) -> set[str]:
    """
    task-catalog.yaml から task id を抽出する。
    形式は top-level category -> 2スペース indent の task-id を想定。
    """
    if task_catalog_path is None:
        task_catalog_path = Path(__file__).resolve().parents[1] / "templates" / "task-catalog.yaml"

    if not task_catalog_path.is_file():
        return set()

    known_task_ids: set[str] = set()
    for raw in task_catalog_path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line:
            continue
        matched = _TASK_ID_LINE.match(line)
        if matched:
            known_task_ids.add(matched.group(1))
    return known_task_ids


def _skill_md_path(skills_root: Path, skill_id: str) -> Path:
    category, _, name = skill_id.partition("/")
    if not category or not name:
        raise ValueError(f"invalid skill id: {skill_id}")
    return skills_root / category / name / "SKILL.md"


def _classification_payload(*, approved: bool, confidence: float) -> dict:
    status = "approved" if approved else "pending"
    return {
        "status": status,
        "classified_at": _now_iso8601_utc(),
        "classifier_model": MODEL_NAME,
        "confidence": confidence,
    }


def classify_one(
    skill_id: str,
    *,
    skills_root: Path,
    jsonl_path: Path,
    known_task_ids: set[str],
    approve: bool = False,
    dry_run: bool = False,
) -> dict:
    entries = build_jsonl_catalog(skills_root, existing_jsonl_path=jsonl_path)

    target_entry: dict | None = None
    for entry in entries:
        if entry.get("id") == skill_id:
            target_entry = entry
            break
    if target_entry is None:
        raise FileNotFoundError(f"skill not found: {skill_id}")

    skill_md_content = _skill_md_path(skills_root, skill_id).read_text(encoding="utf-8")
    source_hash = compute_source_hash(skill_md_content)

    classified = classify_skill(skill_id, skill_md_content, known_task_ids=known_task_ids)
    confidence_value = float(classified.pop("confidence", 0.0))
    target_entry.update(classified)
    target_entry["source_hash"] = source_hash
    target_entry["classification"] = _classification_payload(
        approved=approve,
        confidence=confidence_value,
    )
    validate_entry(target_entry, known_task_ids=known_task_ids)

    if not dry_run:
        write_jsonl_catalog(entries, jsonl_path)

    return {
        "skill_id": skill_id,
        "dry_run": dry_run,
        "approved": approve,
        "entry": target_entry,
    }


def classify_all(
    *,
    skills_root: Path,
    jsonl_path: Path,
    known_task_ids: set[str],
    only_pending: bool = False,
    dry_run: bool = False,
) -> dict:
    entries = build_jsonl_catalog(skills_root, existing_jsonl_path=jsonl_path)
    existing_map = {entry.get("id"): entry for entry in read_jsonl_catalog(jsonl_path) if isinstance(entry, dict)}

    classified_count = 0
    skipped_count = 0
    skipped_approved_hash_match = 0
    to_classify_count = 0
    errors: list[dict] = []

    for entry in entries:
        skill_id = str(entry.get("id") or "")
        classification = entry.get("classification")
        status = classification.get("status") if isinstance(classification, dict) else ""

        existing = existing_map.get(skill_id)
        existing_hash = existing.get("source_hash") if isinstance(existing, dict) else None
        existing_classification = existing.get("classification") if isinstance(existing, dict) else None
        existing_status = existing_classification.get("status") if isinstance(existing_classification, dict) else ""
        hash_matches = isinstance(existing_hash, str) and existing_hash == entry.get("source_hash")

        if hash_matches and status in {"approved", "manual"}:
            skipped_count += 1
            skipped_approved_hash_match += 1
            continue

        if only_pending and status != "pending":
            skipped_count += 1
            continue

        to_classify_count += 1
        try:
            skill_md_content = _skill_md_path(skills_root, skill_id).read_text(encoding="utf-8")
            source_hash = compute_source_hash(skill_md_content)
            classified = classify_skill(skill_id, skill_md_content, known_task_ids=known_task_ids)
            confidence_value = float(classified.pop("confidence", 0.0))

            entry.update(classified)
            entry["source_hash"] = source_hash
            entry["classification"] = _classification_payload(
                approved=False,
                confidence=confidence_value,
            )
            validate_entry(entry, known_task_ids=known_task_ids)
            classified_count += 1
        except ClassifierError as exc:
            errors.append({"skill_id": skill_id, "code": exc.code, "message": str(exc)})
            if existing_status == "manual" and hash_matches:
                # manual/hash一致は通常ここに来ないが、保険として既存値保持
                entry["classification"] = existing_classification
            continue

    if not dry_run:
        write_jsonl_catalog(entries, jsonl_path)

    return {
        "target": len(entries),
        "classified": classified_count,
        "skipped": skipped_count,
        "skipped_approved_hash_match": skipped_approved_hash_match,
        "to_classify": to_classify_count,
        "errors": errors,
    }
