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
                "commands": ["security-audit", "owasp-check"],
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


def test_load_jsonl_candidates_allows_partial_success_on_single_parse_failure(tmp_path: Path, capsys) -> None:
    jsonl_path = tmp_path / "catalog.jsonl"
    jsonl_path.write_text(
        "\n".join(
            [
                json.dumps(_jsonl_entry(status="approved"), ensure_ascii=False),
                "{invalid json",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    candidates, reason = skill_recommender._load_jsonl_candidates(jsonl_path)

    captured = capsys.readouterr()
    assert reason is None
    assert candidates is not None
    assert [entry["id"] for entry in candidates] == ["common/security"]
    assert "有効行のみで継続" in captured.err


def test_load_jsonl_candidates_falls_back_when_all_lines_are_invalid(tmp_path: Path, capsys) -> None:
    jsonl_path = tmp_path / "catalog.jsonl"
    jsonl_path.write_text("{invalid json\n", encoding="utf-8")

    candidates, reason = skill_recommender._load_jsonl_candidates(jsonl_path)

    captured = capsys.readouterr()
    assert candidates is None
    assert reason == "jsonl_parse_failed"
    assert "JSON fallback" in captured.err


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
    assert result["candidates"][0]["commands"] == ["security-audit", "owasp-check"]


def test_recommend_normalizes_legacy_helix_codex_agent_name(monkeypatch, tmp_path: Path) -> None:
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
                        "recommended_agent": "helix-codex --role security",
                        "match_reason": "legacy format",
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


def test_recommend_clears_agent_when_llm_returns_value_outside_allowlist(monkeypatch, tmp_path: Path) -> None:
    catalog_path = tmp_path / "skill-catalog.json"
    jsonl_path = tmp_path / "skill-catalog.jsonl"
    cache_dir = tmp_path / "cache"
    _write_json(catalog_path, _catalog_fixture())
    _write_jsonl(
        jsonl_path,
        [
            _jsonl_entry(status="approved"),
            {**_jsonl_entry(status="approved", agent="qa"), "id": "common/testing", "source_hash": "b" * 64},
        ],
    )

    def _fake_run(_: str) -> str:
        return json.dumps(
            {
                "recommendations": [
                    {
                        "skill_id": "unknown/skill",
                        "recommended_agent": "frontend",
                        "match_reason": "invalid agent",
                        "references": [],
                    }
                ]
            },
            ensure_ascii=False,
        )

    monkeypatch.setattr(skill_recommender, "_run_recommender", _fake_run)

    result = skill_recommender.recommend(
        task_text="未知タスク",
        top_n=1,
        catalog_path=catalog_path,
        jsonl_catalog_path=jsonl_path,
        cache_dir=cache_dir,
        force_refresh=True,
    )

    assert result["candidates"][0]["recommended_agent"] == ""
    assert result["candidates"][0]["commands"] == []


def test_recommend_attaches_commands_on_cached_legacy_payload(monkeypatch, tmp_path: Path) -> None:
    catalog_path = tmp_path / "skill-catalog.json"
    jsonl_path = tmp_path / "skill-catalog.jsonl"
    cache_dir = tmp_path / "cache"
    _write_json(catalog_path, _catalog_fixture())
    _write_jsonl(jsonl_path, [_jsonl_entry(status="approved")])

    catalog_version = _catalog_fixture().get("version", "1.0")
    key = skill_recommender._cache_key(
        "認証レビュー",
        1,
        None,
        None,
        str(catalog_version),
        None,
        False,
        skill_recommender._jsonl_version(jsonl_path),
    )
    legacy_payload = {
        "candidates": [
            {
                "skill_id": "common/security",
                "score": 0.8,
                "reason": "legacy cache payload",
                "references": [],
                "recommended_agent": "security",
            }
        ],
        "task_summary": "認証レビュー",
        "no_match_reason": None,
    }
    cache_file = cache_dir / f"{key}.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(legacy_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _should_not_run(_: str) -> str:
        raise AssertionError("fresh cache should bypass LLM call")

    monkeypatch.setattr(skill_recommender, "_run_recommender", _should_not_run)

    result = skill_recommender.recommend(
        task_text="認証レビュー",
        top_n=1,
        catalog_path=catalog_path,
        jsonl_catalog_path=jsonl_path,
        cache_dir=cache_dir,
        force_refresh=False,
    )

    assert result["_cached"] is True
    assert result["candidates"][0]["commands"] == ["security-audit", "owasp-check"]


def test_recommend_writes_cache_atomically(monkeypatch, tmp_path: Path) -> None:
    catalog_path = tmp_path / "skill-catalog.json"
    jsonl_path = tmp_path / "skill-catalog.jsonl"
    cache_dir = tmp_path / "cache"
    _write_json(catalog_path, _catalog_fixture())
    _write_jsonl(jsonl_path, [_jsonl_entry(status="approved")])

    replace_calls: list[tuple[Path, Path]] = []
    real_replace = skill_recommender.os.replace

    def _record_replace(src, dst):
        replace_calls.append((Path(src), Path(dst)))
        return real_replace(src, dst)

    def _fake_run(_: str) -> str:
        return json.dumps({"recommendations": []}, ensure_ascii=False)

    monkeypatch.setattr(skill_recommender, "_run_recommender", _fake_run)
    monkeypatch.setattr(skill_recommender.os, "replace", _record_replace)

    result = skill_recommender.recommend(
        task_text="認証レビュー",
        top_n=1,
        catalog_path=catalog_path,
        jsonl_catalog_path=jsonl_path,
        cache_dir=cache_dir,
        force_refresh=True,
    )

    key = skill_recommender._cache_key(
        "認証レビュー",
        1,
        None,
        None,
        str(_catalog_fixture().get("version", "1.0")),
        None,
        False,
        skill_recommender._jsonl_version(jsonl_path),
    )
    cache_file = cache_dir / f"{key}.json"
    tmp_file = cache_file.with_suffix(".tmp")

    assert result["_cached"] is False
    assert cache_file.exists()
    assert not tmp_file.exists()
    assert replace_calls == [(tmp_file, cache_file)]


def test_recommend_gc_removes_expired_cache_files(monkeypatch, tmp_path: Path) -> None:
    catalog_path = tmp_path / "skill-catalog.json"
    jsonl_path = tmp_path / "skill-catalog.jsonl"
    cache_dir = tmp_path / "cache"
    _write_json(catalog_path, _catalog_fixture())
    _write_jsonl(jsonl_path, [_jsonl_entry(status="approved")])

    stale = cache_dir / "stale.json"
    fresh = cache_dir / "fresh.json"
    cache_dir.mkdir(parents=True, exist_ok=True)
    stale.write_text("{}", encoding="utf-8")
    fresh.write_text("{}", encoding="utf-8")

    now = skill_recommender.time.time()
    ttl = skill_recommender.CACHE_TTL_SECONDS
    stale_mtime = now - ttl - 10
    fresh_mtime = now - 10
    stale.touch()
    fresh.touch()
    import os

    os.utime(stale, (stale_mtime, stale_mtime))
    os.utime(fresh, (fresh_mtime, fresh_mtime))

    def _fake_run(_: str) -> str:
        return json.dumps({"recommendations": []}, ensure_ascii=False)

    monkeypatch.setattr(skill_recommender, "_run_recommender", _fake_run)

    skill_recommender.recommend(
        task_text="認証レビュー",
        top_n=1,
        catalog_path=catalog_path,
        jsonl_catalog_path=jsonl_path,
        cache_dir=cache_dir,
        force_refresh=True,
    )

    assert not stale.exists()
    assert fresh.exists()
