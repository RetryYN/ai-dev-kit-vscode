from pathlib import Path

import meta_phase


def test_check_patterns_accepts_repo_pattern_contract() -> None:
    root = Path(__file__).resolve().parents[3]

    status = meta_phase.check_patterns(root)

    assert status.ok
    assert status.pattern_count >= 3
    assert not status.errors


def test_valid_gates_include_pre_release_gates() -> None:
    for gate in ("G6.5", "G6.7", "G6.9"):
        assert gate in meta_phase.VALID_GATES


def test_check_patterns_rejects_gate_in_phase(tmp_path: Path) -> None:
    pattern_dir = tmp_path / ".helix" / "patterns"
    pattern_dir.mkdir(parents=True)
    (tmp_path / "cli").mkdir()
    (tmp_path / "docs" / "commands").mkdir(parents=True)
    (tmp_path / "cli" / "helix").write_text("#!/bin/sh\n", encoding="utf-8")
    (pattern_dir / "pattern.yaml").write_text(
        """
version: 1
patterns:
  - id: bad
    scope:
      layer: [Plan]
      phase: [G1]
      gate: [G1]
      subphase: [L-1]
    priority: 1
    applies_when:
      all:
        - drive: [be]
    outputs:
      - path: docs/adr/{id}.md
        type: ADR
    conflicts_with: []
    exception_policy:
      requires_approval: PM
      audit_log: true
    audit_log:
      enabled: true
      path: .helix/audit/pattern-applications.yaml
""",
        encoding="utf-8",
    )

    status = meta_phase.check_patterns(tmp_path)

    assert not status.ok
    assert any("invalid scope.phase G1" in error for error in status.errors)


def test_check_patterns_prefers_project_root_env(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / "project"
    pattern_dir = project_root / ".helix" / "patterns"
    pattern_dir.mkdir(parents=True)
    (pattern_dir / "pattern.yaml").write_text(
        """
version: 1
patterns:
  - id: bad-project-local
    scope:
      layer: [Plan]
      phase: [G1]
      gate: [G1]
      subphase: [L-1]
    priority: 1
    applies_when:
      all:
        - drive: [be]
    outputs:
      - path: docs/adr/{id}.md
        type: ADR
    conflicts_with: []
    exception_policy:
      requires_approval: PM
      audit_log: true
    audit_log:
      enabled: true
      path: .helix/audit/pattern-applications.yaml
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))
    monkeypatch.chdir(project_root)

    status = meta_phase.check_patterns()

    assert not status.ok
    assert status.path == str(pattern_dir / "pattern.yaml")
    assert any("invalid scope.phase G1" in error for error in status.errors)


def test_check_patterns_rejects_missing_required_scope_fields(tmp_path: Path) -> None:
    pattern_dir = tmp_path / ".helix" / "patterns"
    pattern_dir.mkdir(parents=True)
    (pattern_dir / "pattern.yaml").write_text(
        """
version: 1
patterns:
  - id: missing-scope-fields
    scope: {}
    priority: 1
    applies_when:
      all:
        - drive: [be]
    outputs:
      - path: docs/adr/{id}.md
        type: ADR
    conflicts_with: []
    audit_log:
      enabled: true
      path: .helix/audit/pattern-applications.yaml
""",
        encoding="utf-8",
    )

    status = meta_phase.check_patterns(tmp_path)

    assert not status.ok
    assert any("scope.layer is required" in error for error in status.errors)
    assert any("scope.phase is required" in error for error in status.errors)
    assert any("scope.subphase is required" in error for error in status.errors)


def test_check_patterns_rejects_non_kebab_pattern_id(tmp_path: Path) -> None:
    pattern_dir = tmp_path / ".helix" / "patterns"
    pattern_dir.mkdir(parents=True)
    (pattern_dir / "pattern.yaml").write_text(
        """
version: 1
patterns:
  - id: Bad ID
    scope:
      layer: [Plan]
      phase: [L1]
      subphase: []
    priority: 1
    applies_when:
      all:
        - drive: [be]
    outputs:
      - path: docs/adr/{id}.md
        type: ADR
    conflicts_with: []
    audit_log:
      enabled: true
      path: .helix/audit/pattern-applications.yaml
""",
        encoding="utf-8",
    )

    status = meta_phase.check_patterns(tmp_path)

    assert not status.ok
    assert any("id must be kebab-case" in error for error in status.errors)


def test_check_patterns_fails_from_uninitialized_cwd_even_with_external_env(tmp_path: Path, monkeypatch) -> None:
    initialized_root = tmp_path / "initialized"
    initialized_pattern_dir = initialized_root / ".helix" / "patterns"
    initialized_pattern_dir.mkdir(parents=True)
    (initialized_pattern_dir / "pattern.yaml").write_text(
        """
version: 1
patterns:
  - id: valid
    scope:
      layer: [Plan]
      phase: [L1]
      subphase: []
    priority: 1
    applies_when:
      all:
        - drive: [be]
    outputs:
      - path: docs/adr/{id}.md
        type: ADR
    conflicts_with: []
    audit_log:
      enabled: true
      path: .helix/audit/pattern-applications.yaml
""",
        encoding="utf-8",
    )
    uninitialized_root = tmp_path / "uninitialized"
    uninitialized_root.mkdir()
    real_exists = Path.exists

    def _isolated_exists(path: Path) -> bool:
        if str(path) == "/tmp/.helix":
            return False
        return real_exists(path)

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(initialized_root))
    monkeypatch.setattr(meta_phase.Path, "exists", _isolated_exists)
    monkeypatch.chdir(uninitialized_root)

    status = meta_phase.check_patterns()

    assert not status.ok
    assert status.path == str(uninitialized_root / ".helix" / "patterns" / "pattern.yaml")
    assert any("missing pattern file" in error for error in status.errors)


def test_check_patterns_accepts_nested_applies_when(tmp_path: Path) -> None:
    pattern_dir = tmp_path / ".helix" / "patterns"
    pattern_dir.mkdir(parents=True)
    (pattern_dir / "pattern.yaml").write_text(
        """
version: 1
patterns:
  - id: nested
    scope:
      layer: [Plan]
      phase: [L1]
      gate: [G1]
      subphase: [L-1]
    priority: 1
    applies_when:
      all:
        - drive: [be]
        - any:
            - has_external_api: true
            - has_db_migration: true
    outputs:
      - path: docs/adr/{id}.md
        type: ADR
    conflicts_with: []
    exception_policy:
      requires_approval: PM
      audit_log: true
    audit_log:
      enabled: true
      path: .helix/audit/pattern-applications.yaml
""",
        encoding="utf-8",
    )

    status = meta_phase.check_patterns(tmp_path)

    assert status.ok
    assert status.pattern_count == 1
