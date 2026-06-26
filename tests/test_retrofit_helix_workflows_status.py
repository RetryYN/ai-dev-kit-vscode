from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "retrofit-helix-workflows-status.py"


def _load_module():
    module_name = "retrofit_helix_workflows_status"
    spec = importlib.util.spec_from_file_location(
        module_name,
        SCRIPT_PATH,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _write_markdown(
    path: Path,
    *,
    doc_id: str,
    status: str = "draft",
    accepted_date: str | None = None,
    newline: str = "\n",
) -> None:
    lines = [
        "---",
        f"doc_id: {doc_id}",
        "title: Sample",
        f"status: {status}",
    ]
    if accepted_date is not None:
        lines.append(f"accepted_date: {accepted_date}")
    lines.extend(
        [
            "created: 2026-05-24",
            "owner: PM",
            "---",
            "",
            "# Body",
            "",
            "content",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(newline.join(lines) + newline, encoding="utf-8", newline="")


def _parse_frontmatter(module, path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    frontmatter_lines, _body_lines = module.extract_frontmatter_lines(text)
    parsed = yaml.safe_load("".join(frontmatter_lines)) or {}
    return {
        key: module.normalize_scalar(value) if key in {"accepted_date", "created"} else value
        for key, value in parsed.items()
    }


def test_dry_run_renders_unified_diff_and_summary(tmp_path: Path) -> None:
    module = _load_module()
    root = tmp_path / "repo"
    workflows_dir = root / "HELIX-workflows" / "helix-process"
    _write_markdown(workflows_dir / "L0-concept.md", doc_id="l0-concept")
    _write_markdown(workflows_dir / "README.md", doc_id="workflows-index")

    result = module.execute(
        root=root,
        apply=False,
        force_date=False,
        verbose=False,
    )
    rendered = module.render_result(result)

    assert result.summary.changed == 2
    assert result.summary.skipped == 0
    assert result.summary.errors == 0
    assert result.summary.status_missing == 0
    assert result.summary.accepted_date_conflict == 0
    assert "--- HELIX-workflows/helix-process/L0-concept.md" in rendered
    assert "+accepted_date: 2026-05-24" in rendered
    assert "[REPORT] file × category × freeze_basis × exclude_reason:" in rendered
    assert "Summary:" in rendered


def test_apply_updates_files_and_validates_yaml(tmp_path: Path) -> None:
    module = _load_module()
    root = tmp_path / "repo"
    workflows_dir = root / "HELIX-workflows" / "helix-process"
    _write_markdown(workflows_dir / "L0-concept.md", doc_id="l0-concept")
    _write_markdown(workflows_dir / "README.md", doc_id="workflows-index")

    result = module.execute(
        root=root,
        apply=True,
        force_date=False,
        verbose=False,
    )

    assert result.ok is True
    assert result.summary.changed == 2
    assert result.summary.double_check_failed == 0
    assert _parse_frontmatter(module, workflows_dir / "L0-concept.md") == {
        "doc_id": "l0-concept",
        "title": "Sample",
        "status": "accepted",
        "accepted_date": "2026-05-24",
        "created": "2026-05-24",
        "owner": "PM",
    }
    assert _parse_frontmatter(module, workflows_dir / "README.md")["status"] == "accepted"


def test_second_run_is_idempotent_after_apply(tmp_path: Path) -> None:
    module = _load_module()
    root = tmp_path / "repo"
    workflows_dir = root / "HELIX-workflows" / "helix-process"
    _write_markdown(workflows_dir / "L0-concept.md", doc_id="l0-concept")

    first = module.execute(root=root, apply=True, force_date=False, verbose=False)
    second = module.execute(root=root, apply=False, force_date=False, verbose=False)

    assert first.summary.changed == 1
    assert second.summary.changed == 0
    assert second.summary.skipped == 1
    assert second.ok is True


def test_conflicting_accepted_date_blocks_without_force(tmp_path: Path) -> None:
    module = _load_module()
    root = tmp_path / "repo"
    workflows_dir = root / "HELIX-workflows" / "helix-process"
    target = workflows_dir / "L0-concept.md"
    _write_markdown(
        target,
        doc_id="l0-concept",
        accepted_date="2026-05-20",
    )
    before = target.read_text(encoding="utf-8")

    result = module.execute(root=root, apply=True, force_date=False, verbose=False)

    assert result.ok is False
    assert result.summary.accepted_date_conflict == 1
    assert result.summary.changed == 0
    assert target.read_text(encoding="utf-8") == before


def test_force_date_allows_overwrite(tmp_path: Path) -> None:
    module = _load_module()
    root = tmp_path / "repo"
    workflows_dir = root / "HELIX-workflows" / "helix-process"
    target = workflows_dir / "L0-concept.md"
    _write_markdown(
        target,
        doc_id="l0-concept",
        accepted_date="2026-05-20",
    )

    result = module.execute(root=root, apply=True, force_date=True, verbose=False)

    assert result.ok is True
    assert result.summary.changed == 1
    assert _parse_frontmatter(module, target)["accepted_date"] == "2026-05-24"


@pytest.mark.parametrize(("newline", "marker"), [("\n", "\n"), ("\r\n", "\r\n")])
def test_newline_style_is_preserved(tmp_path: Path, newline: str, marker: str) -> None:
    module = _load_module()
    root = tmp_path / "repo"
    workflows_dir = root / "HELIX-workflows" / "helix-process"
    target = workflows_dir / "L0-concept.md"
    _write_markdown(target, doc_id="l0-concept", newline=newline)

    result = module.execute(root=root, apply=True, force_date=False, verbose=False)
    with target.open(encoding="utf-8", newline="") as handle:
        content = handle.read()

    assert result.ok is True
    assert f"status: accepted{marker}accepted_date: 2026-05-24{marker}" in content
    if newline == "\r\n":
        assert "\n" not in content.replace("\r\n", "")
    else:
        assert "\r\n" not in content


def test_real_directory_scan_includes_readme_and_54_files() -> None:
    module = _load_module()
    paths = module.collect_target_paths(
        PROJECT_ROOT / "HELIX-workflows" / "helix-process"
    )

    # count-pin: helix-process は process doc 追加で増える。現状 54（旧 pin 46 は drift）。
    assert len(paths) == 54
    assert any(path.name == "README.md" for path in paths)
