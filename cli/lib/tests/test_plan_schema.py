import py_compile
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import plan_schema


MODULE_PATH = LIB_DIR / "plan_schema.py"


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_normalize_plan_adds_list_defaults_without_mutating_input() -> None:
    raw = {"id": "PLAN-001", "references": "bad"}

    normalized = plan_schema.normalize_plan(raw)

    assert normalized["references"] == []
    assert normalized["artifacts"] == []
    assert "artifacts" not in raw


def test_is_legacy_plan_requires_references_and_artifacts_keys() -> None:
    assert plan_schema.is_legacy_plan({"id": "PLAN-019"}) is True
    assert plan_schema.is_legacy_plan({"id": "PLAN-020", "references": [], "artifacts": []}) is False


def test_evaluate_g2_design_evidence_skips_legacy_plan(tmp_path: Path) -> None:
    plans_dir = tmp_path / ".helix" / "plans"
    plans_dir.mkdir(parents=True)
    (plans_dir / "PLAN-019.yaml").write_text("id: PLAN-019\ntitle: legacy\n", encoding="utf-8")

    result = plan_schema.evaluate_g2_design_evidence(tmp_path, "PLAN-019")

    assert result["ok"] is True
    assert result["legacy"] is True
    assert result["reason"] == "legacy_plan"


def test_evaluate_g2_design_evidence_passes_with_three_references(tmp_path: Path) -> None:
    plans_dir = tmp_path / ".helix" / "plans"
    plans_dir.mkdir(parents=True)
    (plans_dir / "PLAN-020.yaml").write_text(
        "\n".join(
            [
                "id: PLAN-020",
                "title: new",
                "references:",
                "  - docs/a.md",
                "  - docs/b.md",
                "  - docs/c.md",
                "artifacts: []",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = plan_schema.evaluate_g2_design_evidence(tmp_path, "PLAN-020")

    assert result["ok"] is True
    assert result["legacy"] is False
    assert result["references_count"] == 3


def test_evaluate_g2_design_evidence_passes_with_three_design_shards(tmp_path: Path) -> None:
    plans_dir = tmp_path / ".helix" / "plans"
    plans_dir.mkdir(parents=True)
    (plans_dir / "PLAN-021.yaml").write_text(
        "id: PLAN-021\ntitle: new\nreferences: []\nartifacts: []\n",
        encoding="utf-8",
    )
    for shard in ("D-API", "D-DB", "D-ARCH"):
        (tmp_path / "docs" / "features" / "PLAN-021" / shard).mkdir(parents=True)

    result = plan_schema.evaluate_g2_design_evidence(tmp_path, "PLAN-021")

    assert result["ok"] is True
    assert result["design_shard_dirs_count"] == 3


def test_evaluate_g2_design_evidence_fails_new_plan_without_evidence(tmp_path: Path) -> None:
    plans_dir = tmp_path / ".helix" / "plans"
    plans_dir.mkdir(parents=True)
    (plans_dir / "PLAN-022.yaml").write_text(
        "id: PLAN-022\ntitle: new\nreferences: []\nartifacts: []\n",
        encoding="utf-8",
    )

    result = plan_schema.evaluate_g2_design_evidence(tmp_path, "PLAN-022")

    assert result["ok"] is False
    assert result["reason"] == "insufficient_g2_design_evidence"
