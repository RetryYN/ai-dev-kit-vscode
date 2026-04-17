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

import skill_catalog
import skill_classify_runner
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


def _write_skill(
    skills_root: Path,
    category: str,
    name: str,
    *,
    description: str = "desc",
    helix_layer: str = "L4",
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


def _existing_jsonl_entry(
    skills_root: Path,
    *,
    status: str,
    source_hash: str | None = None,
    classifier_model: str = "gpt-5.4-mini",
    confidence: float = 0.9,
) -> dict:
    entry = skill_catalog.build_jsonl_catalog(skills_root)[0]
    entry["classification"] = {
        "status": status,
        "classified_at": "2026-04-16T03:00:00Z",
        "classifier_model": classifier_model,
        "confidence": confidence,
    }
    if source_hash is not None:
        entry["source_hash"] = source_hash
    return entry


def _run_classify_all(
    *,
    skills_root: Path,
    jsonl_path: Path,
    only_pending: bool,
) -> tuple[dict, list[str], list[dict]]:
    calls: list[str] = []

    def _fake_classify(skill_id: str, skill_md_content: str, *, known_task_ids: set[str]) -> dict:
        del skill_md_content, known_task_ids
        calls.append(skill_id)
        return {
            "phases": ["L4"],
            "tasks": ["design-security"],
            "triggers": ["reclassified"],
            "anti_triggers": [],
            "agent": "security",
            "similar": [],
            "confidence": 0.93,
        }

    with patch.object(skill_classify_runner, "classify_skill", _fake_classify):
        summary = skill_classify_runner.classify_all(
            skills_root=skills_root,
            jsonl_path=jsonl_path,
            known_task_ids={"design-security"},
            only_pending=only_pending,
            dry_run=False,
        )

    return summary, calls, skill_catalog.read_jsonl_catalog(jsonl_path)


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

    def test_build_jsonl_catalog_preserves_approved_on_hash_match_without_reclassification(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            skills_root = tmp_path / "skills"
            _write_skill(skills_root, "common", "alpha")
            existing = _existing_jsonl_entry(skills_root, status="approved")
            jsonl_path = tmp_path / "catalog.jsonl"
            _write_jsonl(jsonl_path, [json.dumps(existing, ensure_ascii=False)])

            rebuilt = skill_catalog.build_jsonl_catalog(skills_root, existing_jsonl_path=jsonl_path)
            summary, calls, written = _run_classify_all(
                skills_root=skills_root,
                jsonl_path=jsonl_path,
                only_pending=False,
            )

        self.assertEqual(rebuilt[0]["classification"], existing["classification"])
        self.assertEqual(calls, [])
        self.assertEqual(summary["classified"], 0)
        self.assertEqual(summary["skipped_approved_hash_match"], 1)
        self.assertEqual(written[0]["classification"], existing["classification"])

    def test_build_jsonl_catalog_preserves_manual_on_hash_match_without_reclassification(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            skills_root = tmp_path / "skills"
            _write_skill(skills_root, "common", "alpha")
            existing = _existing_jsonl_entry(
                skills_root,
                status="manual",
                classifier_model="human",
                confidence=0.77,
            )
            jsonl_path = tmp_path / "catalog.jsonl"
            _write_jsonl(jsonl_path, [json.dumps(existing, ensure_ascii=False)])

            rebuilt = skill_catalog.build_jsonl_catalog(skills_root, existing_jsonl_path=jsonl_path)
            summary, calls, written = _run_classify_all(
                skills_root=skills_root,
                jsonl_path=jsonl_path,
                only_pending=False,
            )

        self.assertEqual(rebuilt[0]["classification"], existing["classification"])
        self.assertEqual(calls, [])
        self.assertEqual(summary["classified"], 0)
        self.assertEqual(summary["skipped_approved_hash_match"], 1)
        self.assertEqual(written[0]["classification"], existing["classification"])

    def test_build_jsonl_catalog_keeps_pending_on_hash_match_and_only_pending_reclassifies(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            skills_root = tmp_path / "skills"
            _write_skill(skills_root, "common", "alpha")
            existing = _existing_jsonl_entry(skills_root, status="pending")
            jsonl_path = tmp_path / "catalog.jsonl"
            _write_jsonl(jsonl_path, [json.dumps(existing, ensure_ascii=False)])

            rebuilt = skill_catalog.build_jsonl_catalog(skills_root, existing_jsonl_path=jsonl_path)
            summary, calls, written = _run_classify_all(
                skills_root=skills_root,
                jsonl_path=jsonl_path,
                only_pending=True,
            )

        self.assertEqual(
            rebuilt[0]["classification"],
            {"status": "pending", "classified_at": None, "classifier_model": None},
        )
        self.assertEqual(calls, ["common/alpha"])
        self.assertEqual(summary["classified"], 1)
        self.assertEqual(summary["to_classify"], 1)
        self.assertEqual(written[0]["classification"]["status"], "pending")
        self.assertEqual(written[0]["classification"]["classifier_model"], skill_classify_runner.MODEL_NAME)
        self.assertEqual(written[0]["triggers"], ["reclassified"])

    def test_build_jsonl_catalog_downgrades_hash_mismatch_approved_then_reclassifies(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            skills_root = tmp_path / "skills"
            _write_skill(skills_root, "common", "alpha")
            existing = _existing_jsonl_entry(skills_root, status="approved", source_hash="b" * 64)
            jsonl_path = tmp_path / "catalog.jsonl"
            _write_jsonl(jsonl_path, [json.dumps(existing, ensure_ascii=False)])

            rebuilt = skill_catalog.build_jsonl_catalog(skills_root, existing_jsonl_path=jsonl_path)
            summary, calls, written = _run_classify_all(
                skills_root=skills_root,
                jsonl_path=jsonl_path,
                only_pending=True,
            )

        self.assertEqual(
            rebuilt[0]["classification"],
            {"status": "pending", "classified_at": None, "classifier_model": None},
        )
        self.assertEqual(calls, ["common/alpha"])
        self.assertEqual(summary["classified"], 1)
        self.assertEqual(written[0]["classification"]["status"], "pending")
        self.assertEqual(written[0]["triggers"], ["reclassified"])

    def test_build_jsonl_catalog_downgrades_hash_mismatch_manual_then_reclassifies(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            skills_root = tmp_path / "skills"
            _write_skill(skills_root, "common", "alpha")
            existing = _existing_jsonl_entry(
                skills_root,
                status="manual",
                source_hash="c" * 64,
                classifier_model="human",
                confidence=0.7,
            )
            jsonl_path = tmp_path / "catalog.jsonl"
            _write_jsonl(jsonl_path, [json.dumps(existing, ensure_ascii=False)])

            rebuilt = skill_catalog.build_jsonl_catalog(skills_root, existing_jsonl_path=jsonl_path)
            summary, calls, written = _run_classify_all(
                skills_root=skills_root,
                jsonl_path=jsonl_path,
                only_pending=True,
            )

        self.assertEqual(rebuilt[0]["classification"]["status"], "pending")
        self.assertEqual(rebuilt[0]["classification"]["classifier_model"], "human")
        self.assertEqual(rebuilt[0]["classification"]["confidence"], 0.7)
        self.assertEqual(calls, ["common/alpha"])
        self.assertEqual(summary["classified"], 1)
        self.assertEqual(written[0]["classification"]["classifier_model"], skill_classify_runner.MODEL_NAME)

    def test_build_jsonl_catalog_keeps_pending_on_hash_mismatch_and_reclassifies(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            skills_root = tmp_path / "skills"
            _write_skill(skills_root, "common", "alpha")
            existing = _existing_jsonl_entry(skills_root, status="pending", source_hash="d" * 64)
            jsonl_path = tmp_path / "catalog.jsonl"
            _write_jsonl(jsonl_path, [json.dumps(existing, ensure_ascii=False)])

            rebuilt = skill_catalog.build_jsonl_catalog(skills_root, existing_jsonl_path=jsonl_path)
            summary, calls, written = _run_classify_all(
                skills_root=skills_root,
                jsonl_path=jsonl_path,
                only_pending=True,
            )

        self.assertEqual(
            rebuilt[0]["classification"],
            {"status": "pending", "classified_at": None, "classifier_model": None},
        )
        self.assertEqual(calls, ["common/alpha"])
        self.assertEqual(summary["classified"], 1)
        self.assertEqual(written[0]["classification"]["status"], "pending")
        self.assertEqual(written[0]["agent"], "security")

    def test_recommend_with_55_jsonl_entries_only_approved_candidates_reach_search_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            catalog_path, jsonl_path, cache_dir = _prepare_catalog_files(tmp_path)

            approved_entries = []
            pending_entries = []
            for index in range(50):
                approved_entries.append(
                    {
                        **_jsonl_entry(status="approved"),
                        "id": f"common/approved-{index:02d}",
                        "title": f"approved-{index:02d}",
                        "summary": f"approved summary {index}",
                    }
                )
            for index in range(5):
                pending_entries.append(
                    {
                        **_jsonl_entry(status="pending"),
                        "id": f"common/pending-{index:02d}",
                        "title": f"pending-{index:02d}",
                        "summary": f"pending summary {index}",
                    }
                )
            _write_jsonl(
                jsonl_path,
                [json.dumps(entry, ensure_ascii=False) for entry in approved_entries + pending_entries],
            )

            seen_prompts: list[str] = []

            def _fake_run(prompt: str) -> str:
                seen_prompts.append(prompt)
                return json.dumps(
                    {
                        "recommendations": [
                            {
                                "skill_id": "common/approved-00",
                                "recommended_agent": "pg",
                                "match_reason": "ok",
                                "references": [],
                            },
                            {
                                "skill_id": "common/approved-49",
                                "recommended_agent": "pg",
                                "match_reason": "ok",
                                "references": [],
                            },
                        ]
                    },
                    ensure_ascii=False,
                )

            with patch.object(skill_recommender, "_run_recommender", _fake_run):
                result = skill_recommender.recommend(
                    task_text="認証レビュー",
                    top_n=3,
                    catalog_path=catalog_path,
                    jsonl_catalog_path=jsonl_path,
                    cache_dir=cache_dir,
                    force_refresh=True,
                )

        self.assertEqual(
            [candidate["skill_id"] for candidate in result["candidates"]],
            ["common/approved-00", "common/approved-49"],
        )
        self.assertEqual(
            [candidate["recommended_agent"] for candidate in result["candidates"]],
            ["security", "security"],
        )
        self.assertTrue(seen_prompts)
        self.assertIn('"id":"common/approved-00"', seen_prompts[0])
        self.assertIn('"id":"common/approved-49"', seen_prompts[0])
        self.assertNotIn('"id":"common/pending-00"', seen_prompts[0])
        self.assertNotIn('"id":"common/pending-04"', seen_prompts[0])
