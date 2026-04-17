from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch


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


def _jsonl_entry(*, status: str = "approved", phases: list[str] | None = None) -> dict:
    return {
        "id": "common/security",
        "title": "security-jsonl",
        "summary": "jsonl summary",
        "phases": phases or ["L4"],
        "tasks": ["design-security"],
        "triggers": ["認証"],
        "anti_triggers": [],
        "agent": "security",
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


def _write_jsonl(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _prepare_catalog_files(tmp_path: Path) -> tuple[Path, Path, Path]:
    catalog_path = tmp_path / "skill-catalog.json"
    jsonl_path = tmp_path / "skill-catalog.jsonl"
    cache_dir = tmp_path / "cache"
    _write_json(catalog_path, _catalog_fixture())
    return catalog_path, jsonl_path, cache_dir


def _run_recommend(
    *,
    tmp_path: Path,
    jsonl_lines: list[str] | None = None,
    phase_filter: list[str] | None = None,
    use_no_jsonl: bool = False,
) -> tuple[dict, list[str], str]:
    catalog_path, jsonl_path, cache_dir = _prepare_catalog_files(tmp_path)
    if jsonl_lines is not None:
        _write_jsonl(jsonl_path, jsonl_lines)

    seen_prompts: list[str] = []

    def _fake_run(prompt: str) -> str:
        seen_prompts.append(prompt)
        return json.dumps(
            {
                "recommendations": [
                    {
                        "skill_id": "common/security",
                        "recommended_agent": "pg",
                        "match_reason": "ok",
                        "references": [{"path": "references/a.md", "title": "a"}],
                    }
                ]
            },
            ensure_ascii=False,
        )

    stderr = io.StringIO()
    with patch.object(skill_recommender, "_run_recommender", _fake_run), redirect_stderr(stderr):
        result = skill_recommender.recommend(
            task_text="認証レビュー",
            top_n=3,
            catalog_path=catalog_path,
            jsonl_catalog_path=jsonl_path,
            cache_dir=cache_dir,
            phase_filter=phase_filter,
            use_no_jsonl=use_no_jsonl,
            force_refresh=True,
        )
    return result, seen_prompts, stderr.getvalue()


class SkillCatalogIntegrationTest(unittest.TestCase):
    def test_recommend_falls_back_to_json_when_jsonl_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result, prompts, stderr_text = _run_recommend(tmp_path=Path(tmpdir))

        self.assertEqual(result["candidates"][0]["skill_id"], "common/security")
        self.assertTrue(prompts)
        self.assertIn('"skill_count":1', prompts[0])
        self.assertNotIn('"title":"security-jsonl"', prompts[0])
        self.assertIn("JSONL fallback reason=jsonl_missing", stderr_text)

    def test_recommend_falls_back_to_json_when_jsonl_parse_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result, prompts, stderr_text = _run_recommend(
                tmp_path=Path(tmpdir),
                jsonl_lines=["{invalid json"],
            )

        self.assertEqual(result["candidates"][0]["skill_id"], "common/security")
        self.assertTrue(prompts)
        self.assertIn('"skill_count":1', prompts[0])
        self.assertNotIn('"title":"security-jsonl"', prompts[0])
        self.assertIn("JSONL parse failed. JSON fallback", stderr_text)
        self.assertIn("JSONL fallback reason=jsonl_parse_failed", stderr_text)

    def test_recommend_falls_back_to_json_when_jsonl_schema_is_invalid(self) -> None:
        invalid_entry = _jsonl_entry()
        del invalid_entry["title"]

        with tempfile.TemporaryDirectory() as tmpdir:
            result, prompts, stderr_text = _run_recommend(
                tmp_path=Path(tmpdir),
                jsonl_lines=[json.dumps(invalid_entry, ensure_ascii=False)],
            )

        self.assertEqual(result["candidates"][0]["skill_id"], "common/security")
        self.assertTrue(prompts)
        self.assertIn('"skill_count":1', prompts[0])
        self.assertNotIn('"title":"security-jsonl"', prompts[0])
        self.assertIn("JSONL schema invalid. JSON fallback", stderr_text)
        self.assertIn("JSONL fallback reason=jsonl_schema_invalid", stderr_text)

    def test_recommend_falls_back_to_json_when_jsonl_has_no_approved_or_manual_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result, prompts, stderr_text = _run_recommend(
                tmp_path=Path(tmpdir),
                jsonl_lines=[json.dumps(_jsonl_entry(status="pending"), ensure_ascii=False)],
            )

        self.assertEqual(result["candidates"][0]["skill_id"], "common/security")
        self.assertTrue(prompts)
        self.assertIn('"skill_count":1', prompts[0])
        self.assertNotIn('"title":"security-jsonl"', prompts[0])
        self.assertIn("JSONL fallback reason=jsonl_no_approved", stderr_text)

    def test_recommend_returns_no_candidates_without_json_fallback_when_phase_filter_excludes_all_jsonl_entries(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            catalog_path, jsonl_path, cache_dir = _prepare_catalog_files(Path(tmpdir))
            _write_jsonl(jsonl_path, [json.dumps(_jsonl_entry(phases=["L4"]), ensure_ascii=False)])

            seen_prompts: list[str] = []

            def _fake_run(prompt: str) -> str:
                seen_prompts.append(prompt)
                return json.dumps({"recommendations": []}, ensure_ascii=False)

            stderr = io.StringIO()
            with patch.object(skill_recommender, "_run_recommender", _fake_run), redirect_stderr(stderr):
                result = skill_recommender.recommend(
                    task_text="認証レビュー",
                    top_n=3,
                    catalog_path=catalog_path,
                    jsonl_catalog_path=jsonl_path,
                    cache_dir=cache_dir,
                    phase_filter=["L2"],
                    force_refresh=True,
                )

        self.assertEqual(result["candidates"], [])
        self.assertTrue(seen_prompts)
        self.assertNotIn('"skill_count":1', seen_prompts[0])
        self.assertNotIn('"title":"security-jsonl"', seen_prompts[0])
        self.assertNotIn("JSONL fallback reason=", stderr.getvalue())

    def test_recommend_forces_json_mode_when_use_no_jsonl_is_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result, prompts, stderr_text = _run_recommend(
                tmp_path=Path(tmpdir),
                jsonl_lines=[json.dumps(_jsonl_entry(), ensure_ascii=False)],
                use_no_jsonl=True,
            )

        self.assertEqual(result["candidates"][0]["skill_id"], "common/security")
        self.assertTrue(prompts)
        self.assertIn('"skill_count":1', prompts[0])
        self.assertNotIn('"title":"security-jsonl"', prompts[0])
        self.assertNotIn("JSONL fallback reason=", stderr_text)
