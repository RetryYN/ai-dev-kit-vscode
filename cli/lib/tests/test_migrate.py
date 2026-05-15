import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import migrate
import helix_db


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
    (templates_dir / "CLAUDE.md.template").write_text(
        "<!-- helix_template_version: 2 -->\n# CLAUDE template\nHELIX Claude rules\n",
        encoding="utf-8",
    )
    (templates_dir / "AGENTS.md.template").write_text(
        "<!-- helix_template_version: 2 -->\n# AGENTS template\nHELIX Codex rules\n",
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


def _write_current_yaml_files(helix_dir: Path) -> None:
    helix_dir.mkdir(parents=True, exist_ok=True)
    for name in [
        "phase.yaml",
        "gate-checks.yaml",
        "doc-map.yaml",
        "matrix.yaml",
        "framework.yaml",
    ]:
        (helix_dir / name).write_text("# helix_template_version: 2\n{}\n", encoding="utf-8")


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


def test_target_registry_contains_new_project_targets() -> None:
    targets = {target["id"]: target for target in migrate.TARGET_REGISTRY}

    assert targets["claude_md"] == {
        "id": "claude_md",
        "root": "project_root",
        "path": "CLAUDE.md",
        "template": "cli/templates/CLAUDE.md.template",
        "merge_strategy": "text_append",
        "backup_policy": "migrate_backups",
        "rollback_policy": "target_snapshot",
        "tracked_or_local": "tracked_or_local",
    }
    assert targets["agents_md"]["merge_strategy"] == "text_append"
    assert targets["claude_settings"]["template"] is None
    assert targets["claude_settings"]["merge_strategy"] == "json_hooks"
    assert targets["claude_settings"]["backup_policy"] == "migrate_backups_secret_isolated"


def test_dry_run_reports_claude_and_agents_without_writing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project_root = tmp_path
    helix_dir = project_root / ".helix"
    templates_dir = tmp_path / "templates"
    _write_templates(templates_dir)
    _write_current_yaml_files(helix_dir)
    (project_root / "CLAUDE.md").write_text(
        "<!-- helix_template_version: 1 -->\n# Local Claude\nuser note\n",
        encoding="utf-8",
    )
    (project_root / "AGENTS.md").write_text(
        "# Local Agents\nproject rule\n",
        encoding="utf-8",
    )

    result = migrate.do_merge(helix_dir, templates_dir, apply=False, project_root=project_root)

    assert result == 0
    out = capsys.readouterr().out
    assert "[claude_md]" in out
    assert "[agents_md]" in out
    assert "HELIX Claude rules" in out
    assert "HELIX Codex rules" in out
    assert "HELIX-MANAGED-START" not in (project_root / "CLAUDE.md").read_text(encoding="utf-8")
    assert "HELIX-MANAGED-START" not in (project_root / "AGENTS.md").read_text(encoding="utf-8")


def test_apply_creates_missing_project_targets_and_rollback_removes_them(tmp_path: Path) -> None:
    project_root = tmp_path
    helix_dir = project_root / ".helix"
    templates_dir = tmp_path / "templates"
    _write_templates(templates_dir)
    _write_current_yaml_files(helix_dir)

    assert migrate.do_merge(helix_dir, templates_dir, apply=True, project_root=project_root) == 0
    assert (project_root / "CLAUDE.md").exists()
    assert (project_root / "AGENTS.md").exists()
    assert (project_root / ".claude/settings.json").exists()

    latest = migrate.rollback(helix_dir, project_root=project_root)

    assert latest.parent == helix_dir / "migrate-backups"
    assert not (project_root / "CLAUDE.md").exists()
    assert not (project_root / "AGENTS.md").exists()
    assert not (project_root / ".claude/settings.json").exists()


def test_json_hooks_preserve_non_helix_hooks(tmp_path: Path) -> None:
    project_root = tmp_path
    helix_dir = project_root / ".helix"
    templates_dir = tmp_path / "templates"
    settings_path = project_root / ".claude/settings.json"
    _write_templates(templates_dir)
    _write_current_yaml_files(helix_dir)
    (project_root / "CLAUDE.md").write_text("<!-- helix_template_version: 2 -->\n", encoding="utf-8")
    (project_root / "AGENTS.md").write_text("<!-- helix_template_version: 2 -->\n", encoding="utf-8")
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Read",
                            "hooks": [{"type": "command", "command": "custom-reader"}],
                        }
                    ]
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert migrate.do_merge(helix_dir, templates_dir, apply=True, project_root=project_root) == 0

    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    pre_tool = payload["hooks"]["PreToolUse"]
    assert any(entry.get("matcher") == "Read" for entry in pre_tool)
    assert any(entry.get("matcher") == "Bash" for entry in pre_tool)


def test_json_hooks_invalid_json_fails_close_without_writing_or_backup(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project_root = tmp_path
    helix_dir = project_root / ".helix"
    templates_dir = tmp_path / "templates"
    settings_path = project_root / ".claude/settings.json"
    _write_templates(templates_dir)
    _write_current_yaml_files(helix_dir)
    (project_root / "CLAUDE.md").write_text("<!-- helix_template_version: 2 -->\n", encoding="utf-8")
    (project_root / "AGENTS.md").write_text("<!-- helix_template_version: 2 -->\n", encoding="utf-8")
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text("{bad", encoding="utf-8")

    result = migrate.do_merge(helix_dir, templates_dir, apply=True, project_root=project_root)

    assert result == 3
    assert settings_path.read_text(encoding="utf-8") == "{bad"
    assert not (helix_dir / "migrate-backups").exists()
    assert "invalid JSON" in capsys.readouterr().err


def test_secret_bearing_settings_backup_is_isolated_in_migrate_backups(tmp_path: Path) -> None:
    project_root = tmp_path
    helix_dir = project_root / ".helix"
    templates_dir = tmp_path / "templates"
    settings_path = project_root / ".claude/settings.json"
    _write_templates(templates_dir)
    _write_current_yaml_files(helix_dir)
    (project_root / "CLAUDE.md").write_text("<!-- helix_template_version: 2 -->\n", encoding="utf-8")
    (project_root / "AGENTS.md").write_text("<!-- helix_template_version: 2 -->\n", encoding="utf-8")
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps({"env": {"API_TOKEN": "secret-value"}}, ensure_ascii=False),
        encoding="utf-8",
    )

    assert migrate.do_merge(helix_dir, templates_dir, apply=True, project_root=project_root) == 0

    backup_files = list((helix_dir / "migrate-backups").glob("*/.claude/settings.json"))
    assert len(backup_files) == 1
    assert "secret-value" in backup_files[0].read_text(encoding="utf-8")
    assert not list((helix_dir / "backup").glob("*/.claude/settings.json"))


def test_helix_migrate_cli_dry_run_apply_and_rollback(tmp_path: Path) -> None:
    project_root = tmp_path
    helix_dir = project_root / ".helix"
    helix_dir.mkdir(parents=True)
    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "cli/helix-migrate"
    env = os.environ.copy()
    env["HELIX_HOME"] = str(repo_root)
    env["HELIX_PROJECT_ROOT"] = str(project_root)

    dry_run = subprocess.run(
        [str(script), "--dry-run"],
        cwd=project_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert dry_run.returncode == 0
    assert "[claude_md]" in dry_run.stdout
    assert not (project_root / "CLAUDE.md").exists()

    apply_run = subprocess.run(
        [str(script), "--yes"],
        cwd=project_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert apply_run.returncode == 0
    assert (project_root / "CLAUDE.md").exists()
    assert (project_root / "AGENTS.md").exists()
    assert (project_root / ".claude/settings.json").exists()

    rollback_run = subprocess.run(
        [str(script), "--rollback"],
        cwd=project_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert rollback_run.returncode == 0
    assert not (project_root / "CLAUDE.md").exists()
    assert not (project_root / "AGENTS.md").exists()
    assert not (project_root / ".claude/settings.json").exists()


def test_is_helix_self_repo_matches_default_home_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    project_root = home / "ai-dev-kit-vscode"
    project_root.mkdir(parents=True)
    monkeypatch.delenv("HELIX_HOME", raising=False)
    monkeypatch.setenv("HOME", str(home))

    assert migrate.is_helix_self_repo(project_root) is True


def test_is_helix_self_repo_does_not_treat_fresh_clone_as_self(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    project_root = tmp_path / "work" / "ai-dev-kit-vscode"
    templates_dir = project_root / "cli" / "templates"
    _write_templates(templates_dir)
    (project_root / "skills").mkdir(parents=True)
    (project_root / "skills" / "SKILL_MAP.md").write_text("# SKILL_MAP\n", encoding="utf-8")
    monkeypatch.delenv("HELIX_HOME", raising=False)
    monkeypatch.setenv("HOME", str(home))

    assert migrate.is_helix_self_repo(project_root) is False


def test_is_helix_self_repo_matches_helix_home_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "custom-helix"
    project_root.mkdir()
    monkeypatch.setenv("HELIX_HOME", str(project_root))

    assert migrate.is_helix_self_repo(project_root) is True


def test_self_host_skips_project_targets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path
    helix_dir = project_root / ".helix"
    templates_dir = project_root / "cli" / "templates"
    _write_templates(templates_dir)
    _write_current_yaml_files(helix_dir)
    monkeypatch.setenv("HELIX_HOME", str(project_root))

    assert migrate.is_helix_self_repo(project_root) is True

    result = migrate.do_merge(helix_dir, templates_dir, apply=True, project_root=project_root)
    assert result == 0
    assert not (project_root / "CLAUDE.md").exists()
    assert not (project_root / "AGENTS.md").exists()
    assert not (project_root / ".claude" / "settings.json").exists()


def test_idempotent_text_append_with_managed_markers(tmp_path: Path) -> None:
    project_root = tmp_path
    helix_dir = project_root / ".helix"
    templates_dir = tmp_path / "templates"
    _write_templates(templates_dir)
    (templates_dir / "CLAUDE.md.template").write_text(
        "<!-- helix_template_version: 3 -->\n"
        "<!-- HELIX-MANAGED-START -->\n"
        "# CLAUDE template v3\nrules\n"
        "<!-- HELIX-MANAGED-END -->\n",
        encoding="utf-8",
    )
    _write_current_yaml_files(helix_dir)
    (project_root / "CLAUDE.md").write_text(
        "<!-- helix_template_version: 2 -->\n"
        "<!-- HELIX-MANAGED-START -->\n"
        "# CLAUDE template v2\nold rules\n"
        "<!-- HELIX-MANAGED-END -->\n"
        "\nuser custom\n",
        encoding="utf-8",
    )
    (project_root / "AGENTS.md").write_text(
        "<!-- helix_template_version: 3 -->\nplaceholder\n", encoding="utf-8"
    )

    assert migrate.do_merge(helix_dir, templates_dir, apply=True, project_root=project_root) == 0
    after_first = (project_root / "CLAUDE.md").read_text(encoding="utf-8")
    assert "v3" in after_first
    assert "user custom" in after_first
    assert after_first.count("HELIX-MANAGED-START") == 1

    assert migrate.do_merge(helix_dir, templates_dir, apply=True, project_root=project_root) == 0
    after_second = (project_root / "CLAUDE.md").read_text(encoding="utf-8")
    assert after_first == after_second


LEGACY_CONTRACT_ENTRIES_SCHEMA_V20 = """
CREATE TABLE contract_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_type TEXT NOT NULL,
    source_path TEXT NOT NULL,
    symbol_id TEXT,
    version TEXT,
    schema_hash TEXT,
    breaking_change_flag INTEGER DEFAULT 0,
    introduced_plan TEXT,
    raw_spec TEXT,
    design_level TEXT NOT NULL DEFAULT 'detailed'
        CHECK (design_level IN ('planning','requirement','architecture','detailed','functional'))
);
CREATE INDEX idx_contract_type ON contract_entries(contract_type);
CREATE INDEX idx_contract_breaking ON contract_entries(breaking_change_flag);
CREATE INDEX idx_contract_design_level ON contract_entries(design_level);
"""


def _build_legacy_v20_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.executescript(helix_db.SCHEMA)
    conn.executescript(helix_db.SCHEMA_VERSION_SCHEMA)
    conn.executescript(helix_db.ACCURACY_SCORE_SCHEMA)
    conn.executescript(helix_db.INFRA_SCHEMA_V9)
    conn.executescript(helix_db.AUDIT_DECISIONS_SCHEMA_V10)
    helix_db._migrate_v10_to_v11(conn)
    helix_db._migrate_v11_to_v12(conn)
    helix_db._migrate_v12_to_v13(conn)
    helix_db._migrate_v13_to_v14(conn)
    helix_db._migrate_v14_to_v15(conn)
    helix_db._migrate_v15_to_v16(conn)
    helix_db._migrate_v16_to_v17(conn)
    helix_db._migrate_v17_to_v18(conn)
    helix_db._migrate_v18_to_v19(conn)
    helix_db._migrate_v19_to_v20(conn)
    conn.execute("DROP TABLE IF EXISTS contract_entries")
    conn.executescript(LEGACY_CONTRACT_ENTRIES_SCHEMA_V20)
    conn.execute(
        "INSERT INTO contract_entries (contract_type, source_path, raw_spec) VALUES (?, ?, ?)",
        ("cli-contract", "docs/features/demo/D-API/api.yaml", "{}"),
    )
    conn.execute("DELETE FROM schema_version")
    conn.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (20, '2026-05-12T00:00:00')"
    )
    conn.commit()
    return conn


def _column_default(conn: sqlite3.Connection, table: str, column: str) -> str:
    row = conn.execute(f"PRAGMA table_info({table})").fetchall()
    defaults = {entry[1]: entry[4] for entry in row}
    return defaults[column]


def _column_signature(conn: sqlite3.Connection, table: str) -> list[tuple]:
    return [
        (row[1], row[2], row[3], row[4], row[5])
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    ]


def test_v20_to_v21_adds_drive_column(tmp_path: Path) -> None:
    conn = _build_legacy_v20_db(tmp_path / "legacy-v20-drive.db")
    try:
        helix_db.migrate(conn)
        assert _column_default(conn, "contract_entries", "drive") == "'be'"
    finally:
        conn.close()


def test_v20_to_v21_adds_origin_mode_column(tmp_path: Path) -> None:
    conn = _build_legacy_v20_db(tmp_path / "legacy-v20-origin.db")
    try:
        helix_db.migrate(conn)
        assert _column_default(conn, "contract_entries", "origin_mode") == "'forward'"
    finally:
        conn.close()


def test_v20_to_v21_adds_evidence_status_column(tmp_path: Path) -> None:
    conn = _build_legacy_v20_db(tmp_path / "legacy-v20-evidence.db")
    try:
        helix_db.migrate(conn)
        assert _column_default(conn, "contract_entries", "evidence_status") == "'confirmed'"
    finally:
        conn.close()


def test_v20_to_v21_creates_design_sprint_entries(tmp_path: Path) -> None:
    conn = _build_legacy_v20_db(tmp_path / "legacy-v20-sprint-entries.db")
    try:
        helix_db.migrate(conn)
        table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'design_sprint_entries'"
        ).fetchone()
        assert table is not None
    finally:
        conn.close()


def test_v20_to_v21_creates_design_sprint_artifact_links(tmp_path: Path) -> None:
    conn = _build_legacy_v20_db(tmp_path / "legacy-v20-sprint-links.db")
    try:
        helix_db.migrate(conn)
        table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'design_sprint_artifact_links'"
        ).fetchone()
        assert table is not None
    finally:
        conn.close()


def test_v20_to_v21_creates_view_vmodel_integrity(tmp_path: Path) -> None:
    conn = _build_legacy_v20_db(tmp_path / "legacy-v20-vmodel-view.db")
    try:
        helix_db.migrate(conn)
        view = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'view' AND name = 'view_vmodel_integrity'"
        ).fetchone()
        assert view is not None
    finally:
        conn.close()


def test_view_vmodel_integrity_joins_code_index(tmp_path: Path) -> None:
    conn = _build_legacy_v20_db(tmp_path / "legacy-v20-vmodel-join.db")
    try:
        helix_db.migrate(conn)
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'view' AND name = 'view_vmodel_integrity'"
        ).fetchone()
        assert row is not None
        view_sql = row[0]
        assert "LEFT JOIN code_index" in view_sql
    finally:
        conn.close()


def test_v21_sprint_type_impl_requires_layer_functional(tmp_path: Path) -> None:
    conn = _build_legacy_v20_db(tmp_path / "legacy-v20-vmodel-check.db")
    try:
        helix_db.migrate(conn)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO design_sprint_entries
                    (plan_id, sprint_type, layer, drive)
                VALUES (?, ?, ?, ?)
                """,
                ("PLAN-TEST", "impl", "architecture", "be"),
            )
    finally:
        conn.close()


def test_migrate_is_idempotent_at_v23(tmp_path: Path) -> None:
    db_path = tmp_path / "v21-idempotent.db"
    helix_db.init_db(str(db_path))
    helix_db.init_db(str(db_path))
    conn = helix_db.get_connection(db_path)
    try:
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(contract_entries)").fetchall()]
        versions = conn.execute(
            "SELECT version FROM schema_version WHERE version = 23"
        ).fetchall()
        sprint_columns = [row["name"] for row in conn.execute("PRAGMA table_info(design_sprint_entries)").fetchall()]
        artifact_link_columns = [
            row["name"] for row in conn.execute("PRAGMA table_info(design_sprint_artifact_links)").fetchall()
        ]
    finally:
        conn.close()
    assert columns.count("drive") == 1
    assert columns.count("origin_mode") == 1
    assert columns.count("evidence_status") == 1
    assert sprint_columns.count("previous_drive") == 1
    assert sprint_columns.count("drive_switch_reason") == 1
    assert sprint_columns.count("status_on_switch") == 1
    assert sprint_columns.count("supersedes_entry_id") == 1
    assert sprint_columns.count("correction_reason") == 1
    assert sprint_columns.count("voided_at") == 1
    assert artifact_link_columns.count("supersedes_entry_id") == 1
    assert artifact_link_columns.count("correction_reason") == 1
    assert artifact_link_columns.count("voided_at") == 1
    assert len(versions) == 1


def test_migrate_idempotent_v20_to_v23(tmp_path: Path) -> None:
    conn = _build_legacy_v20_db(tmp_path / "legacy-v20-to-v23-idempotent.db")
    try:
        helix_db.migrate(conn)
        helix_db.migrate(conn)
        versions = [row[0] for row in conn.execute("SELECT version FROM schema_version ORDER BY version").fetchall()]
        max_version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
        entry_columns = [row[1] for row in conn.execute("PRAGMA table_info(design_sprint_entries)").fetchall()]
        link_columns = [
            row[1] for row in conn.execute("PRAGMA table_info(design_sprint_artifact_links)").fetchall()
        ]
    finally:
        conn.close()

    assert max_version == helix_db.CURRENT_SCHEMA_VERSION
    assert versions.count(21) == 1
    assert versions.count(22) == 1
    assert versions.count(23) == 1
    assert entry_columns.count("previous_drive") == 1
    assert entry_columns.count("supersedes_entry_id") == 1
    assert link_columns.count("supersedes_entry_id") == 1


def test_migrate_idempotent_individual_versions(tmp_path: Path) -> None:
    conn = _build_legacy_v20_db(tmp_path / "legacy-individual-idempotent.db")
    try:
        helix_db._migrate_v20_to_v21(conn)
        v21_first = {
            "contract_entries": _column_signature(conn, "contract_entries"),
            "design_sprint_entries": _column_signature(conn, "design_sprint_entries"),
            "design_sprint_artifact_links": _column_signature(conn, "design_sprint_artifact_links"),
        }
        helix_db._migrate_v20_to_v21(conn)
        v21_second = {
            "contract_entries": _column_signature(conn, "contract_entries"),
            "design_sprint_entries": _column_signature(conn, "design_sprint_entries"),
            "design_sprint_artifact_links": _column_signature(conn, "design_sprint_artifact_links"),
        }

        helix_db._migrate_v21_to_v22(conn)
        v22_first = _column_signature(conn, "design_sprint_entries")
        helix_db._migrate_v21_to_v22(conn)
        v22_second = _column_signature(conn, "design_sprint_entries")

        helix_db._migrate_v22_to_v23(conn)
        v23_first = {
            "design_sprint_entries": _column_signature(conn, "design_sprint_entries"),
            "design_sprint_artifact_links": _column_signature(conn, "design_sprint_artifact_links"),
        }
        helix_db._migrate_v22_to_v23(conn)
        v23_second = {
            "design_sprint_entries": _column_signature(conn, "design_sprint_entries"),
            "design_sprint_artifact_links": _column_signature(conn, "design_sprint_artifact_links"),
        }
    finally:
        conn.close()

    assert v21_first == v21_second
    assert v22_first == v22_second
    assert v23_first == v23_second
    assert [column[0] for column in v21_second["contract_entries"]].count("drive") == 1
    assert [column[0] for column in v22_second].count("status_on_switch") == 1
    assert [column[0] for column in v23_second["design_sprint_entries"]].count("voided_at") == 1
    assert [column[0] for column in v23_second["design_sprint_artifact_links"]].count("voided_at") == 1


def test_v21_to_v22_adds_drive_switch_columns(tmp_path: Path) -> None:
    conn = _build_legacy_v20_db(tmp_path / "legacy-v21-switch-columns.db")
    try:
        helix_db._migrate_v20_to_v21(conn)
        conn.execute("DELETE FROM schema_version")
        conn.execute(
            "INSERT INTO schema_version (version, applied_at) VALUES (21, '2026-05-12T00:00:00')"
        )
        helix_db.migrate(conn)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(design_sprint_entries)").fetchall()}
        max_version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    finally:
        conn.close()

    assert {"previous_drive", "drive_switch_reason", "status_on_switch"} <= columns
    assert max_version == helix_db.CURRENT_SCHEMA_VERSION


def test_schema_version_advances_to_27(tmp_path: Path) -> None:
    conn = _build_legacy_v20_db(tmp_path / "legacy-v20-version.db")
    try:
        helix_db.migrate(conn)
        max_version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
        assert max_version == helix_db.CURRENT_SCHEMA_VERSION
    finally:
        conn.close()
