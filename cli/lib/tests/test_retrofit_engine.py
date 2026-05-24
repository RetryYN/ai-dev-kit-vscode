"""DoD 検証: docs/v2/L7-test-design/L7-cli-helix-retrofit-impl-test-design.md U-001-U-011."""

from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import retrofit_engine


MODULE_PATH = LIB_DIR / "retrofit_engine.py"


def _project_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / "docs" / "plans" / "L7").mkdir(parents=True)
    (root / "cli" / "config").mkdir(parents=True)
    return root


def test_module_py_compile() -> None:
    """DoD 検証: docs/v2/L7-test-design/L7-cli-helix-retrofit-impl-test-design.md U-001."""
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_init_retrofit_creates_matrix_config_and_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: docs/v2/L7-test-design/L7-cli-helix-retrofit-impl-test-design.md U-002,U-006."""
    root = _project_root(tmp_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(root))

    payload = retrofit_engine.init_retrofit("python312-migration", project_root=root)

    matrix_path = root / payload["matrix"]
    config_path = root / payload["config"]
    plan_path = root / payload["plan"]

    assert matrix_path.exists()
    assert config_path.exists()
    assert plan_path.exists()

    matrix_frontmatter, body = retrofit_engine._load_frontmatter(matrix_path)
    assert matrix_frontmatter["slug"] == "python312-migration"
    assert matrix_frontmatter["rows"][0]["id"] == "R001"
    assert retrofit_engine.TABLE_MARKER in body

    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert config["phases"]["regression"] == ["L8", "L9"]

    plan_frontmatter, _ = retrofit_engine._load_frontmatter(plan_path)
    assert plan_frontmatter["kind"] == "retrofit"


def test_matrix_add_update_and_summary_round_trip(tmp_path: Path) -> None:
    """DoD 検証: docs/v2/L7-test-design/L7-cli-helix-retrofit-impl-test-design.md U-003,U-004."""
    root = _project_root(tmp_path)
    path = retrofit_engine.matrix_path_for_slug(root, "demo")
    matrix = retrofit_engine.RetrofitMatrix.create(path, slug="demo", plan_id="L7-demo-retrofitplan", drive="be")
    matrix.add_row(from_value="A", to_value="B", scope="cli/lib/*.py", phase="L7")
    matrix.update_row("R001", status="done")
    matrix.save()

    loaded = retrofit_engine.RetrofitMatrix.load(path)
    summary = loaded.summary()

    assert len(loaded.rows) == 2
    assert loaded.find_row("R001")["done_at"] is not None
    assert summary["counts"]["done"] == 1
    assert summary["completion_pct"] == 50


def test_config_template_contains_required_keys(tmp_path: Path) -> None:
    """DoD 検証: docs/v2/L7-test-design/L7-cli-helix-retrofit-impl-test-design.md U-005."""
    root = _project_root(tmp_path)
    path = retrofit_engine.config_path_for_slug(root, "demo")
    config = retrofit_engine.RetrofitConfig(path, retrofit_engine.RetrofitConfig.template_payload("demo", "be"))
    config.save_template()

    loaded = retrofit_engine.RetrofitConfig.load(path)
    payload = loaded.show_diff()

    assert payload["design_supplement"] == ["L4", "L5"]
    assert payload["regression"] == ["L8", "L9"]


def test_kind_checker_prefers_signal_then_file_patterns() -> None:
    """DoD 検証: docs/v2/L7-test-design/L7-cli-helix-retrofit-impl-test-design.md U-007."""
    checker = retrofit_engine.KindChecker()

    assert checker.check(signal="dependency_outdated") == ("retrofit", "signal=dependency_outdated (priority 1)")
    assert checker.check(files=["pyproject.toml"])[0] == "retrofit"
    assert checker.check(files=["db/schema.sql"])[0] == "reverse"
    assert checker.check(files=["cli/lib/foo.py", "docs/x.md"])[0] == "refactor"


def test_status_payload_warns_on_blocked_rows_and_plan_mismatch(tmp_path: Path) -> None:
    """DoD 検証: docs/v2/L7-test-design/L7-cli-helix-retrofit-impl-test-design.md U-008."""
    root = _project_root(tmp_path)
    matrix_path = retrofit_engine.matrix_path_for_slug(root, "demo")
    matrix = retrofit_engine.RetrofitMatrix.create(matrix_path, slug="demo", plan_id="L7-demo-retrofitplan", drive="be")
    matrix.update_row("R001", status="blocked")
    matrix.save()

    config_path = retrofit_engine.config_path_for_slug(root, "demo")
    retrofit_engine.RetrofitConfig(config_path, retrofit_engine.RetrofitConfig.template_payload("demo", "be")).save_template()

    plan_path = retrofit_engine.plan_path_for_id(root, "L7-demo-retrofitplan")
    plan_path.write_text(
        "---\nplan_id: L7-demo-retrofitplan\nkind: retrofit\nstatus: draft\n---\nbody\n",
        encoding="utf-8",
    )

    payload = retrofit_engine.get_retrofit_status("demo", as_json=True, project_root=root)

    assert payload["summary"]["blocked_rows"] == 1
    assert any("blocked rows present" in warning for warning in payload["warnings"])


def test_done_rolls_back_to_in_progress_when_regression_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: docs/v2/L7-test-design/L7-cli-helix-retrofit-impl-test-design.md U-009."""
    root = _project_root(tmp_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(root))

    retrofit_engine.init_retrofit("demo", project_root=root)

    def fake_run(args, cwd=None, capture_output=None, text=None, check=None):
        return subprocess.CompletedProcess(args, 1, "", "failed")

    monkeypatch.setattr(retrofit_engine.subprocess, "run", fake_run)

    rc = retrofit_engine.main(["done", "--slug", "demo", "--row", "R001", "--run-regression"])
    matrix = retrofit_engine.RetrofitMatrix.load(retrofit_engine.matrix_path_for_slug(root, "demo"))

    assert rc == 3
    assert matrix.find_row("R001")["status"] == "in_progress"
    assert matrix.find_row("R001")["regression_failed"] is True


def test_invalid_slug_fails_close(tmp_path: Path) -> None:
    """DoD 検証: docs/v2/L7-test-design/L7-cli-helix-retrofit-impl-test-design.md U-010."""
    root = _project_root(tmp_path)
    with pytest.raises(retrofit_engine.RetrofitError):
        retrofit_engine.init_retrofit("Bad_Slug", project_root=root)


def test_plan_command_creates_plan_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DoD 検証: docs/v2/L7-test-design/L7-cli-helix-retrofit-impl-test-design.md U-011."""
    root = _project_root(tmp_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(root))

    rc = retrofit_engine.main(["plan", "--slug", "demo"])
    output = capsys.readouterr().out.strip()

    assert rc == 0
    assert output.endswith("docs/plans/L7/L7-demo-retrofitplan.md")
    assert (root / output).exists()
