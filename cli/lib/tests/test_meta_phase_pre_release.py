from pathlib import Path

import meta_phase


def _write_pattern(root: Path, gate: str) -> None:
    pattern_dir = root / ".helix" / "patterns"
    pattern_dir.mkdir(parents=True)
    (pattern_dir / "pattern.yaml").write_text(
        f"""
version: 1
patterns:
  - id: pre-release-{gate.lower().replace(".", "-")}
    scope:
      layer: [Plan]
      phase: [L6]
      gate: [{gate}]
      subphase: [L-6]
    priority: 1
    applies_when:
      all:
        - drive: [be]
    outputs:
      - path: docs/adr/{{id}}.md
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


def test_valid_gates_include_all_pre_release_gates_as_distinct_values() -> None:
    pre_release = {"G6.5", "G6.7", "G6.9"}

    assert pre_release <= meta_phase.VALID_GATES
    assert "G6.6" not in meta_phase.VALID_GATES


def test_check_patterns_accepts_pre_release_gate_scope(tmp_path: Path) -> None:
    _write_pattern(tmp_path, "G6.7")

    status = meta_phase.check_patterns(tmp_path)

    assert status.ok
    assert status.pattern_count == 1
    assert status.errors == []


def test_check_patterns_rejects_unknown_pre_release_like_gate(tmp_path: Path) -> None:
    _write_pattern(tmp_path, "G6.6")

    status = meta_phase.check_patterns(tmp_path)

    assert not status.ok
    assert any("invalid scope.gate G6.6" in error for error in status.errors)
