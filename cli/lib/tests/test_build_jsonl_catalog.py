from __future__ import annotations

import json
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import skill_catalog


def _write_skill(
    skills_root: Path,
    category: str,
    name: str,
    *,
    description: str,
    helix_layer: str = "L2",
) -> Path:
    skill_dir = skills_root / category / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        "\n".join(
            [
                "---",
                f"name: {name}",
                f"description: {description}",
                "metadata:",
                f"  helix_layer: {helix_layer}",
                "  triggers:",
                "    - trigger-a",
                "---",
                "",
                "# body",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return skill_md


def _valid_jsonl_entry() -> dict:
    return {
        "id": "common/security",
        "title": "security",
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
            "status": "approved",
            "classified_at": "2026-04-16T03:00:00Z",
            "classifier_model": "gpt-5.4-mini",
            "confidence": 0.9,
        },
    }


def test_build_jsonl_catalog_returns_sorted_entries(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    _write_skill(skills_root, "workflow", "zeta", description="desc z")
    _write_skill(skills_root, "common", "alpha", description="desc a")

    entries = skill_catalog.build_jsonl_catalog(skills_root)

    assert len(entries) == 2
    assert [entry["id"] for entry in entries] == ["common/alpha", "workflow/zeta"]


def test_build_jsonl_catalog_source_hash_changes_on_skill_update(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    skill_md = _write_skill(skills_root, "common", "alpha", description="before")

    before = skill_catalog.build_jsonl_catalog(skills_root)[0]["source_hash"]
    skill_md.write_text(skill_md.read_text(encoding="utf-8").replace("before", "after"), encoding="utf-8")
    after = skill_catalog.build_jsonl_catalog(skills_root)[0]["source_hash"]

    assert before != after


def test_build_jsonl_catalog_keeps_classification_when_approved_and_hash_matches(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    _write_skill(skills_root, "common", "alpha", description="same")
    current = skill_catalog.build_jsonl_catalog(skills_root)[0]

    existing_path = tmp_path / "catalog.jsonl"
    existing_entry = dict(current)
    existing_entry["classification"] = {
        "status": "approved",
        "classified_at": "2026-04-16T03:00:00Z",
        "classifier_model": "gpt-5.4-mini",
        "confidence": 0.88,
    }
    existing_path.write_text(json.dumps(existing_entry, ensure_ascii=False) + "\n", encoding="utf-8")

    rebuilt = skill_catalog.build_jsonl_catalog(skills_root, existing_jsonl_path=existing_path)
    assert rebuilt[0]["classification"] == existing_entry["classification"]


def test_build_jsonl_catalog_keeps_manual_classification_when_hash_matches(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    _write_skill(skills_root, "common", "alpha", description="same")
    current = skill_catalog.build_jsonl_catalog(skills_root)[0]

    existing_path = tmp_path / "catalog.jsonl"
    existing_entry = dict(current)
    existing_entry["classification"] = {
        "status": "manual",
        "classified_at": "2026-04-16T03:00:00Z",
        "classifier_model": "human",
        "confidence": 0.77,
    }
    existing_path.write_text(json.dumps(existing_entry, ensure_ascii=False) + "\n", encoding="utf-8")

    rebuilt = skill_catalog.build_jsonl_catalog(skills_root, existing_jsonl_path=existing_path)
    assert rebuilt[0]["classification"] == existing_entry["classification"]


def test_build_jsonl_catalog_downgrades_approved_to_pending_on_hash_mismatch(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    _write_skill(skills_root, "common", "alpha", description="new-content")

    existing_path = tmp_path / "catalog.jsonl"
    existing_entry = skill_catalog.build_jsonl_catalog(skills_root)[0]
    existing_entry["source_hash"] = "b" * 64
    existing_entry["classification"] = {
        "status": "approved",
        "classified_at": "2026-04-16T03:00:00Z",
        "classifier_model": "gpt-5.4-mini",
        "confidence": 0.91,
    }
    existing_path.write_text(json.dumps(existing_entry, ensure_ascii=False) + "\n", encoding="utf-8")

    rebuilt = skill_catalog.build_jsonl_catalog(skills_root, existing_jsonl_path=existing_path)
    assert rebuilt[0]["classification"] == {"status": "pending", "classified_at": None, "classifier_model": None}


def test_build_jsonl_catalog_downgrades_manual_but_keeps_classifier_fields(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    _write_skill(skills_root, "common", "alpha", description="new-content")

    existing_path = tmp_path / "catalog.jsonl"
    existing_entry = skill_catalog.build_jsonl_catalog(skills_root)[0]
    existing_entry["source_hash"] = "c" * 64
    existing_entry["classification"] = {
        "status": "manual",
        "classified_at": "2026-04-15T10:00:00Z",
        "classifier_model": "human",
        "confidence": 0.7,
    }
    existing_path.write_text(json.dumps(existing_entry, ensure_ascii=False) + "\n", encoding="utf-8")

    rebuilt = skill_catalog.build_jsonl_catalog(skills_root, existing_jsonl_path=existing_path)
    assert rebuilt[0]["classification"] == {
        "status": "pending",
        "classified_at": "2026-04-15T10:00:00Z",
        "classifier_model": "human",
        "confidence": 0.7,
    }


def test_write_jsonl_catalog_writes_one_json_per_line(tmp_path: Path) -> None:
    output_path = tmp_path / "catalog.jsonl"
    entries = [_valid_jsonl_entry(), {**_valid_jsonl_entry(), "id": "workflow/design-doc"}]

    skill_catalog.write_jsonl_catalog(entries, output_path)

    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["id"] == "common/security"
    assert json.loads(lines[1])["id"] == "workflow/design-doc"


def test_write_jsonl_catalog_skips_invalid_entry(tmp_path: Path) -> None:
    output_path = tmp_path / "catalog.jsonl"
    valid = _valid_jsonl_entry()
    invalid = dict(valid)
    invalid.pop("agent")

    skill_catalog.write_jsonl_catalog([valid, invalid], output_path)

    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["id"] == "common/security"


def test_read_jsonl_catalog_skips_parse_failures(tmp_path: Path) -> None:
    path = tmp_path / "catalog.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps({"id": "common/security"}),
                "{invalid json",
                json.dumps({"id": "workflow/design-doc"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    loaded = skill_catalog.read_jsonl_catalog(path)
    assert [entry["id"] for entry in loaded] == ["common/security", "workflow/design-doc"]


def test_read_jsonl_catalog_returns_empty_when_missing(tmp_path: Path) -> None:
    missing = tmp_path / "missing.jsonl"
    assert skill_catalog.read_jsonl_catalog(missing) == []


def test_read_jsonl_catalog_returns_empty_for_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "catalog.jsonl"
    path.write_text("", encoding="utf-8")

    assert skill_catalog.read_jsonl_catalog(path) == []


def test_read_jsonl_catalog_accepts_leading_blank_line_and_bom(tmp_path: Path) -> None:
    path = tmp_path / "catalog.jsonl"
    path.write_text("\n\ufeff" + json.dumps(_valid_jsonl_entry(), ensure_ascii=False) + "\n", encoding="utf-8")

    loaded = skill_catalog.read_jsonl_catalog(path)

    assert [entry["id"] for entry in loaded] == ["common/security"]


def test_write_jsonl_catalog_sorts_entries_by_id(tmp_path: Path) -> None:
    output_path = tmp_path / "catalog.jsonl"
    later = _valid_jsonl_entry()
    earlier = {**_valid_jsonl_entry(), "id": "common/alpha"}

    skill_catalog.write_jsonl_catalog([later, earlier], output_path)

    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["id"] for line in lines] == ["common/alpha", "common/security"]


def test_write_then_read_jsonl_catalog_round_trips_entries(tmp_path: Path) -> None:
    output_path = tmp_path / "catalog.jsonl"
    entries = [
        _valid_jsonl_entry(),
        {**_valid_jsonl_entry(), "id": "workflow/design-doc", "source_hash": "b" * 64},
    ]

    skill_catalog.write_jsonl_catalog(entries, output_path)
    loaded = skill_catalog.read_jsonl_catalog(output_path)

    assert loaded == sorted(entries, key=lambda item: item["id"])
