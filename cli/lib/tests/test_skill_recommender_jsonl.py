from __future__ import annotations

import json
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import skill_recommender


def _catalog_fixture() -> dict:
    return {
        "version": "1.0",
        "generated_at": "2026-04-16T00:00:00Z",
        "skill_count": 1,
        "reference_count": 1,
        "skills": [
            {
                "id": "common/security",
                "name": "security",
                "category": "common",
                "path": "skills/common/security/SKILL.md",
                "description": "desc",
                "helix_layer": "L4",
                "triggers": ["認証"],
                "verification": [],
                "compatibility": {"claude": True, "codex": True},
                "references": [{"path": "references/a.md", "title": "a", "intro": ""}],
            }
        ],
    }


def _jsonl_entry(*, status: str = "approved", phases: list[str] | None = None, agent: str = "security") -> dict:
    return {
        "id": "common/security",
        "title": "security-jsonl",
        "summary": "jsonl summary",
        "phases": phases or ["L4"],
        "tasks": ["design-security"],
        "triggers": ["認証"],
        "anti_triggers": [],
        "agent": agent,
        "similar": [],
        "references": [{"path": "skills/common/security/references/x.md", "title": "x"}],
        "source_hash": "a" * 64,
        "classification": {
            "status": status,
            "classified_at": "2026-04-16T03:00:00Z",
            "classifier_model": "gpt-5.4-mini",
            "confidence": 0.9,
        },
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(entry, ensure_ascii=False) for entry in entries) + "\n", encoding="utf-8")


def test_load_jsonl_candidates_returns_missing_when_file_absent(tmp_path: Path) -> None:
    missing = tmp_path / "missing.jsonl"
    candidates, reason = skill_recommender._load_jsonl_candidates(missing)
    assert candidates is None
    assert reason == "jsonl_missing"


def test_load_jsonl_candidates_returns_no_approved_for_pending_only(tmp_path: Path) -> None:
    jsonl_path = tmp_path / "catalog.jsonl"
    _write_jsonl(jsonl_path, [_jsonl_entry(status="pending")])

    candidates, reason = skill_recommender._load_jsonl_candidates(jsonl_path)

    assert candidates is None
    assert reason == "jsonl_no_approved"


def test_load_jsonl_candidates_applies_phase_filter(tmp_path: Path) -> None:
    jsonl_path = tmp_path / "catalog.jsonl"
    entry_l4 = _jsonl_entry(status="approved", phases=["L4"])
    entry_l2 = dict(_jsonl_entry(status="manual", phases=["L2"]))
    entry_l2["id"] = "workflow/design-doc"
    entry_l2["source_hash"] = "b" * 64
    _write_jsonl(jsonl_path, [entry_l4, entry_l2])

    candidates, reason = skill_recommender._load_jsonl_candidates(jsonl_path, phase_filter=["L2"])

    assert reason is None
    assert candidates is not None
    assert [entry["id"] for entry in candidates] == ["workflow/design-doc"]


def test_load_jsonl_candidates_returns_empty_list_when_phase_filter_has_no_match(tmp_path: Path) -> None:
    jsonl_path = tmp_path / "catalog.jsonl"
    _write_jsonl(jsonl_path, [_jsonl_entry(status="approved", phases=["L4"])])

    candidates, reason = skill_recommender._load_jsonl_candidates(jsonl_path, phase_filter=["L2"])

    assert candidates == []
    assert reason is None


def test_recommend_renders_prompt_with_jsonl_candidates(monkeypatch, tmp_path: Path) -> None:
    catalog_path = tmp_path / "skill-catalog.json"
    jsonl_path = tmp_path / "skill-catalog.jsonl"
    cache_dir = tmp_path / "cache"
    _write_json(catalog_path, _catalog_fixture())
    _write_jsonl(jsonl_path, [_jsonl_entry(status="approved")])

    seen_prompts: list[str] = []

    def _fake_run(prompt: str) -> str:
        seen_prompts.append(prompt)
        return json.dumps(
            {
                "recommendations": [
                    {
                        "skill_id": "common/security",
                        "recommended_agent": "security",
                        "match_reason": "ok",
                        "references": [{"path": "skills/common/security/references/x.md", "title": "x"}],
                    }
                ]
            },
            ensure_ascii=False,
        )

    monkeypatch.setattr(skill_recommender, "_run_recommender", _fake_run)

    result = skill_recommender.recommend(
        task_text="認証レビュー",
        top_n=3,
        catalog_path=catalog_path,
        jsonl_catalog_path=jsonl_path,
        cache_dir=cache_dir,
        force_refresh=True,
    )

    assert seen_prompts
    prompt = seen_prompts[0]
    assert '"title":"security-jsonl"' in prompt
    assert '"skill_count":1' not in prompt
    assert result["candidates"][0]["skill_id"] == "common/security"


def test_recommend_renders_prompt_with_json_fallback(monkeypatch, tmp_path: Path) -> None:
    catalog_path = tmp_path / "skill-catalog.json"
    jsonl_path = tmp_path / "skill-catalog.jsonl"
    cache_dir = tmp_path / "cache"
    _write_json(catalog_path, _catalog_fixture())
    _write_jsonl(jsonl_path, [_jsonl_entry(status="approved")])

    seen_prompts: list[str] = []

    def _fake_run(prompt: str) -> str:
        seen_prompts.append(prompt)
        return json.dumps({"recommendations": []}, ensure_ascii=False)

    monkeypatch.setattr(skill_recommender, "_run_recommender", _fake_run)

    skill_recommender.recommend(
        task_text="認証レビュー",
        top_n=3,
        catalog_path=catalog_path,
        jsonl_catalog_path=jsonl_path,
        cache_dir=cache_dir,
        use_no_jsonl=True,
        force_refresh=True,
    )

    assert seen_prompts
    prompt = seen_prompts[0]
    assert '"skill_count":1' in prompt
    assert '"title":"security-jsonl"' not in prompt


def test_recommend_overwrites_agent_with_jsonl_value(monkeypatch, tmp_path: Path) -> None:
    catalog_path = tmp_path / "skill-catalog.json"
    jsonl_path = tmp_path / "skill-catalog.jsonl"
    cache_dir = tmp_path / "cache"
    _write_json(catalog_path, _catalog_fixture())
    _write_jsonl(jsonl_path, [_jsonl_entry(status="approved", agent="security")])

    def _fake_run(_: str) -> str:
        return json.dumps(
            {
                "recommendations": [
                    {
                        "skill_id": "common/security",
                        "recommended_agent": "pg",
                        "match_reason": "agent mismatch",
                        "references": [],
                    }
                ]
            },
            ensure_ascii=False,
        )

    monkeypatch.setattr(skill_recommender, "_run_recommender", _fake_run)

    result = skill_recommender.recommend(
        task_text="認証レビュー",
        top_n=1,
        catalog_path=catalog_path,
        jsonl_catalog_path=jsonl_path,
        cache_dir=cache_dir,
        force_refresh=True,
    )

    assert result["candidates"][0]["recommended_agent"] == "security"
