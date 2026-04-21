from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import skill_catalog


def _write_skill(skills_root: Path, category: str, name: str, frontmatter: str) -> None:
    skill_dir = skills_root / category / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(frontmatter + "\n\n# body\n", encoding="utf-8")


class SkillCatalogTest(unittest.TestCase):
    def test_build_catalog_and_jsonl_support_flat_frontmatter_metadata_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_root = Path(tmpdir) / "skills"
            _write_skill(
                skills_root,
                "agent-skills",
                "flat-skill",
                """---
name: flat-skill
description: flat style
helix_layer: [L1, L3]
triggers: [foo]
verification: [bar]
---""",
            )

            catalog_entry = skill_catalog.build_catalog(skills_root)["skills"][0]
            jsonl_entry = skill_catalog.build_jsonl_catalog(skills_root)[0]

        self.assertEqual(catalog_entry["helix_layer"], "['L1', 'L3']")
        self.assertEqual(jsonl_entry["phases"], ["L1", "L3"])

    def test_build_catalog_and_jsonl_include_both_flat_and_nested_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_root = Path(tmpdir) / "skills"
            _write_skill(
                skills_root,
                "workflow",
                "nested-skill",
                """---
name: nested-skill
description: nested style
metadata:
  helix_layer: L2
---""",
            )
            _write_skill(
                skills_root,
                "agent-skills",
                "flat-skill",
                """---
name: flat-skill
description: flat style
helix_layer: [L1, L3]
---""",
            )

            catalog_ids = {entry["id"] for entry in skill_catalog.build_catalog(skills_root)["skills"]}
            jsonl_entries = {entry["id"]: entry for entry in skill_catalog.build_jsonl_catalog(skills_root)}

        self.assertEqual(catalog_ids, {"workflow/nested-skill", "agent-skills/flat-skill"})
        self.assertEqual(set(jsonl_entries), {"workflow/nested-skill", "agent-skills/flat-skill"})
        self.assertEqual(jsonl_entries["workflow/nested-skill"]["phases"], ["L2"])
        self.assertEqual(jsonl_entries["agent-skills/flat-skill"]["phases"], ["L1", "L3"])

    def test_commands_include_derived_from_flat_helix_layers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_root = Path(tmpdir) / "skills"
            _write_skill(
                skills_root,
                "agent-skills",
                "flat-skill",
                """---
name: flat-skill
description: flat style
helix_layer: [L1, L3]
---""",
            )

            catalog_entry = skill_catalog.build_catalog(skills_root)["skills"][0]
            jsonl_entry = skill_catalog.build_jsonl_catalog(skills_root)[0]

        self.assertIn("helix-size", catalog_entry["commands"])
        self.assertIn("helix-plan", catalog_entry["commands"])
        self.assertIn("/sdd-plan", catalog_entry["commands"])
        self.assertIn("helix-size", jsonl_entry["commands"])
        self.assertIn("helix-plan", jsonl_entry["commands"])
        self.assertIn("/sdd-plan", jsonl_entry["commands"])

    def test_commands_include_derived_from_nested_helix_layer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_root = Path(tmpdir) / "skills"
            _write_skill(
                skills_root,
                "workflow",
                "nested-skill",
                """---
name: nested-skill
description: nested style
metadata:
  helix_layer: L2
---""",
            )

            catalog_entry = skill_catalog.build_catalog(skills_root)["skills"][0]
            jsonl_entry = skill_catalog.build_jsonl_catalog(skills_root)[0]

        self.assertIn("helix-gate G2", catalog_entry["commands"])
        self.assertIn("/spec", catalog_entry["commands"])
        self.assertIn("helix-gate G2", jsonl_entry["commands"])
        self.assertIn("/spec", jsonl_entry["commands"])

    def test_explicit_commands_are_prioritized_before_derived_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_root = Path(tmpdir) / "skills"
            _write_skill(
                skills_root,
                "workflow",
                "explicit-skill",
                """---
name: explicit-skill
description: explicit commands
metadata:
  helix_layer: L2
  commands:
    - custom-cmd
---""",
            )

            catalog_entry = skill_catalog.build_catalog(skills_root)["skills"][0]
            jsonl_entry = skill_catalog.build_jsonl_catalog(skills_root)[0]

        self.assertEqual(catalog_entry["commands"][0], "custom-cmd")
        self.assertEqual(jsonl_entry["commands"][0], "custom-cmd")
        self.assertIn("helix-gate G2", catalog_entry["commands"])
        self.assertIn("/spec", catalog_entry["commands"])
        self.assertIn("helix-gate G2", jsonl_entry["commands"])
        self.assertIn("/spec", jsonl_entry["commands"])
