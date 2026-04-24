import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import migrate


def _write_templates(templates_dir: Path) -> None:
    templates_dir.mkdir(parents=True, exist_ok=True)
    (templates_dir / "phase.yaml").write_text(
        "# helix_template_version: 2\n"
        "current_phase: L5\n"
        "sprint:\n"
        "  current_step: .1a\n"
        "gates:\n"
        "  G4: { status: passed }\n"
        "  G6: { status: pending }\n"
        "new_flag: true\n",
        encoding="utf-8",
    )
    (templates_dir / "gate-checks.yaml").write_text(
        "# helix_template_version: 2\nchecks: {}\n",
        encoding="utf-8",
    )
    (templates_dir / "doc-map.yaml").write_text(
        "# helix_template_version: 2\nrules: {}\n",
        encoding="utf-8",
    )
    (templates_dir / "matrix.yaml").write_text(
        "# helix_template_version: 2\nfeatures: {}\nwaivers: {}\n",
        encoding="utf-8",
    )
    (templates_dir / "framework.yaml").write_text(
        "# helix_template_version: 2\ndetected: node\ntools: {}\n",
        encoding="utf-8",
    )


def _write_legacy_files(helix_dir: Path) -> None:
    helix_dir.mkdir(parents=True, exist_ok=True)
    (helix_dir / "phase.yaml").write_text(
        "# local header\n"
        "# helix_template_version: 1\n"
        "phase: L4\n"
        "sprint_step: .2\n"
        "gate:\n"
        "  G4: { status: pending }\n"
        "custom_key: keep-me\n",
        encoding="utf-8",
    )
    (helix_dir / "gate-checks.yaml").write_text(
        "# helix_template_version: 2\nchecks: {}\n",
        encoding="utf-8",
    )
    (helix_dir / "doc-map.yaml").write_text(
        "# helix_template_version: 2\nrules: {}\n",
        encoding="utf-8",
    )
    (helix_dir / "matrix.yaml").write_text(
        "# helix_template_version: 2\nfeatures: {}\nwaivers: {}\n",
        encoding="utf-8",
    )
    (helix_dir / "framework.yaml").write_text(
        "# helix_template_version: 2\ndetected: node\ntools: {}\n",
        encoding="utf-8",
    )


def test_do_merge_apply_migrates_legacy_phase_yaml_and_creates_backup(tmp_path: Path) -> None:
    helix_dir = tmp_path / ".helix"
    templates_dir = tmp_path / "templates"
    _write_templates(templates_dir)
    _write_legacy_files(helix_dir)

    result = migrate.do_merge(helix_dir, templates_dir, apply=True)

    assert result == 0
    migrated = (helix_dir / "phase.yaml").read_text(encoding="utf-8")
    assert "current_phase: L4" in migrated
    assert 'current_step: ".2"' in migrated
    assert "G4: { status: pending }" in migrated
    assert "G6: { status: pending }" in migrated
    assert "custom_key: keep-me" in migrated
    backups = list((helix_dir / "backup").iterdir())
    assert len(backups) == 1
    assert (backups[0] / "phase.yaml").exists()


def test_do_merge_is_idempotent_after_apply(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    helix_dir = tmp_path / ".helix"
    templates_dir = tmp_path / "templates"
    _write_templates(templates_dir)
    _write_legacy_files(helix_dir)

    assert migrate.do_merge(helix_dir, templates_dir, apply=True) == 0
    capsys.readouterr()

    assert migrate.do_merge(helix_dir, templates_dir, apply=True) == 0
    assert capsys.readouterr().out.strip() == "no changes"


def test_merge_yaml_preserves_invalid_yaml_conservatively() -> None:
    existing_text = "phase:\n  current: L4\n@\n"
    template_text = "# helix_template_version: 2\ncurrent_phase: L5\n"

    merged = migrate.merge_yaml(existing_text, template_text, "phase.yaml")

    assert merged == existing_text


def test_load_template_text_uses_framework_fallback_when_missing(tmp_path: Path) -> None:
    text, exists = migrate.load_template_text("framework.yaml", tmp_path / "missing-framework.yaml")

    assert exists is False
    assert "helix_template_version: 3" in text


def test_migrate_gate_checks() -> None:
    existing_text = """# helix_template_version: 1
G2:
  name: "設計凍結ゲート"
  ai:
    - role: tl
      task: |
        旧タスク
        2行目
  static:
    - name: "legacy-check"
      cmd: "echo legacy"
      level: advisory
"""
    template_text = """# helix_template_version: 2
G2:
  name: "設計凍結ゲート"
  static:
    - name: "updated-check"
      cmd: "echo updated"
      level: mandatory
G4:
  name: "実装凍結ゲート"
  static:
    - name: "new-check"
      cmd: "echo new"
      level: mandatory
"""

    merged = migrate.merge_yaml(existing_text, template_text, "gate-checks.yaml")

    assert merged != existing_text
    assert "G4:" in merged
    assert "new-check" in merged
    assert "旧タスク" in merged
