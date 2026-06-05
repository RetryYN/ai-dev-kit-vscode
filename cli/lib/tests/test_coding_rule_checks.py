from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from registry_checks import RegistryLoadError
from coding_rule_checks import (
    build_coding_rule_baseline_payload,
    check_coding_rule_alignment,
    check_coding_rule_sot,
    load_coding_rule_registry,
    main,
)


def _write_file(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_yaml(path: Path, body: str) -> Path:
    return _write_file(path, textwrap.dedent(body).strip() + "\n")


def _write_claude_md(path: Path, body: str) -> Path:
    return _write_file(path, textwrap.dedent(body).strip() + "\n")


def test_load_coding_rule_registry_normalizes_entries_and_fails_closed(tmp_path: Path) -> None:
    """DoD 検証: coding-rule-detector-単体テスト設計.md UT-CRREG-01"""
    registry_path = _write_yaml(
        tmp_path / "coding-rule-registry.yaml",
        """
        entries:
          - id: CR-CODE-01
            rule: Prefer Bash for CLI glue
            sot_section: コーディング規約
            enforcement:
              kind: manual
              paths: []
              status: manual
          - id: CR-COMMIT-01
            rule: Conventional commit prefix
            sot_section: コミット規約
            enforcement:
              kind: commitlint
              paths: .commitlintrc.json
              status: enforced
        """,
    )

    entries = load_coding_rule_registry(registry_path)

    assert len(entries) == 2
    assert entries[0].id == "CR-CODE-01"
    assert entries[0].enforcement.kind == "manual"
    assert entries[0].enforcement.paths == []
    assert entries[1].enforcement.paths == [".commitlintrc.json"]
    assert entries[1].enforcement.status == "enforced"

    missing_field_path = _write_yaml(
        tmp_path / "broken-missing.yaml",
        """
        entries:
          - id: CR-FORBID-01
            rule: Keep secrets out of docs
            sot_section: 禁止事項
        """,
    )
    with pytest.raises(RegistryLoadError):
        load_coding_rule_registry(missing_field_path)

    invalid_status_path = _write_yaml(
        tmp_path / "broken-status.yaml",
        """
        entries:
          - id: CR-FORBID-02
            rule: Human approval for auth changes
            sot_section: 禁止事項
            enforcement:
              kind: manual
              paths: []
              status: unknown
        """,
    )
    with pytest.raises(RegistryLoadError):
        load_coding_rule_registry(invalid_status_path)


def test_check_coding_rule_sot_reports_gap_path_mismatch_and_self_asset_leak(tmp_path: Path) -> None:
    """DoD 検証: coding-rule-detector-単体テスト設計.md UT-CRREG-02"""
    _write_file(tmp_path / "cli/lib/coding_rule_checks.py", "# coding rule detector\n")
    _write_file(tmp_path / ".commitlintrc.json", "{}\n")
    functional_registry_path = _write_yaml(
        tmp_path / "cli/config/functional-registry.yaml",
        """
        entries:
          - id: FR-LIB-001
            name: coding_rule_checks.py
            domain: lib
            description: coding rule detector implementation
            l1_fr:
              - FR-03
            l3_fr:
              - FR-GR-01
            status: active
            code_paths:
              - cli/lib/coding_rule_checks.py
            doc_paths: []
        """,
    )
    registry_path = _write_yaml(
        tmp_path / "cli/config/coding-rule-registry.yaml",
        """
        entries:
          - id: CR-CODE-01
            rule: Keep Bash/Python split
            sot_section: コーディング規約
            enforcement:
              kind: manual
              paths: []
              status: manual
          - id: CR-COMMIT-01
            rule: Commit prefix must match enum
            sot_section: コミット規約
            enforcement:
              kind: commitlint
              paths:
                - .commitlintrc.json
              status: enforced
          - id: CR-FORBID-01
            rule: Secrets must be blocked before push
            sot_section: 禁止事項
            enforcement:
              kind: hook
              paths:
                - cli/templates/hooks/pre-commit
              status: not-implemented
          - id: CR-FORBID-02
            rule: Missing path must surface
            sot_section: 禁止事項
            enforcement:
              kind: ci_gate
              paths:
                - .github/workflows/does-not-exist.yml
              status: partial
          - id: CR-FORBID-03
            rule: Enforced entries need concrete paths
            sot_section: 禁止事項
            enforcement:
              kind: hook
              paths: []
              status: enforced
        """,
    )

    before_registry = registry_path.read_text(encoding="utf-8")

    report = check_coding_rule_sot(
        registry_path=registry_path,
        repo_root=tmp_path,
        functional_registry_path=functional_registry_path,
    )

    finding_kinds = {finding.kind for finding in report.findings}
    finding_paths = {finding.path for finding in report.findings}
    finding_ids = {finding.entry_id for finding in report.findings}

    assert report.mode == "advisory"
    assert report.exit_policy == 0
    assert {
        "enforcement_gap",
        "missing_enforcement_path",
        "status_path_mismatch",
        "unregistered_self_asset",
    }.issubset(finding_kinds)
    assert ".github/workflows/does-not-exist.yml" in finding_paths
    assert "cli/config/coding-rule-registry.yaml" in finding_paths
    assert "CR-FORBID-03" in finding_ids
    assert registry_path.read_text(encoding="utf-8") == before_registry


def test_check_coding_rule_alignment_reports_section_drift_and_passes_when_aligned(tmp_path: Path) -> None:
    """DoD 検証: coding-rule-detector-単体テスト設計.md UT-CRREG-03"""
    claude_md_path = _write_claude_md(
        tmp_path / "CLAUDE.md",
        """
        ## コーディング規約
        - rule a
        - rule b

        ## コミット規約
        - rule c
        - rule d

        ## 禁止事項
        - rule e
        """,
    )
    mismatch_registry_path = _write_yaml(
        tmp_path / "coding-rule-registry.yaml",
        """
        entries:
          - id: CR-CODE-01
            rule: rule a
            sot_section: コーディング規約
            enforcement:
              kind: manual
              paths: []
              status: manual
          - id: CR-COMMIT-01
            rule: rule c
            sot_section: コミット規約
            enforcement:
              kind: manual
              paths: []
              status: manual
        """,
    )
    aligned_registry_path = _write_yaml(
        tmp_path / "coding-rule-registry-aligned.yaml",
        """
        entries:
          - id: CR-CODE-01
            rule: rule a
            sot_section: コーディング規約
            enforcement:
              kind: manual
              paths: []
              status: manual
          - id: CR-CODE-02
            rule: rule b
            sot_section: コーディング規約
            enforcement:
              kind: manual
              paths: []
              status: manual
          - id: CR-COMMIT-01
            rule: rule c
            sot_section: コミット規約
            enforcement:
              kind: manual
              paths: []
              status: manual
          - id: CR-COMMIT-02
            rule: rule d
            sot_section: コミット規約
            enforcement:
              kind: manual
              paths: []
              status: manual
          - id: CR-FORBID-01
            rule: rule e
            sot_section: 禁止事項
            enforcement:
              kind: manual
              paths: []
              status: manual
        """,
    )

    before_claude = claude_md_path.read_text(encoding="utf-8")
    mismatch_report = check_coding_rule_alignment(claude_md_path, mismatch_registry_path)
    aligned_report = check_coding_rule_alignment(claude_md_path, aligned_registry_path)

    mismatch_kinds = {finding.kind for finding in mismatch_report.findings}

    assert mismatch_report.mode == "advisory"
    assert mismatch_report.exit_policy == 0
    assert {"rule_count_mismatch", "section_count_mismatch"} == mismatch_kinds
    assert aligned_report.findings == []
    assert claude_md_path.read_text(encoding="utf-8") == before_claude


def test_build_coding_rule_baseline_payload_is_deterministic_and_main_writes_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """DoD 検証: coding-rule-detector-単体テスト設計.md UT-CRREG-04"""
    _write_file(tmp_path / "cli/lib/coding_rule_checks.py", "# coding rule detector\n")
    _write_file(tmp_path / "cli/templates/hooks/pre-commit", "#!/usr/bin/env bash\n")
    _write_file(tmp_path / ".commitlintrc.json", "{}\n")
    _write_file(tmp_path / ".github/workflows/feature.yml", "name: feature\n")
    _write_claude_md(
        tmp_path / "CLAUDE.md",
        """
        ## コーディング規約
        - keep split

        ## コミット規約
        - commit prefix

        ## 禁止事項
        - block secrets
        """,
    )
    _write_yaml(
        tmp_path / "cli/config/functional-registry.yaml",
        """
        entries:
          - id: FR-LIB-001
            name: coding_rule_checks.py
            domain: lib
            description: coding rule detector implementation
            l1_fr:
              - FR-03
            l3_fr:
              - FR-GR-01
            status: active
            code_paths:
              - cli/lib/coding_rule_checks.py
              - cli/config/coding-rule-registry.yaml
            doc_paths: []
        """,
    )
    registry_path = _write_yaml(
        tmp_path / "cli/config/coding-rule-registry.yaml",
        """
        entries:
          - id: CR-CODE-01
            rule: keep split
            sot_section: コーディング規約
            enforcement:
              kind: manual
              paths: []
              status: manual
          - id: CR-COMMIT-01
            rule: commit prefix
            sot_section: コミット規約
            enforcement:
              kind: commitlint
              paths:
                - .commitlintrc.json
              status: enforced
          - id: CR-FORBID-01
            rule: block secrets
            sot_section: 禁止事項
            enforcement:
              kind: hook
              paths:
                - cli/templates/hooks/pre-commit
              status: partial
        """,
    )

    first = build_coding_rule_baseline_payload(
        registry_path=registry_path,
        claude_md_path=tmp_path / "CLAUDE.md",
        repo_root=tmp_path,
        created="2026-06-06",
        expiry="2026-09-04",
    )
    second = build_coding_rule_baseline_payload(
        registry_path=registry_path,
        claude_md_path=tmp_path / "CLAUDE.md",
        repo_root=tmp_path,
        created="2026-06-06",
        expiry="2026-09-04",
    )

    assert first == second
    assert first["created"] == "2026-06-06"
    assert first["expiry"] == "2026-09-04"
    assert any(report["findings"] for report in first["reports"])
    for report in first["reports"]:
        for finding in report["findings"]:
            assert finding["fingerprint"]

    output_path = tmp_path / "cli/config/coding-rule-registry-baseline.json"
    rc = main(
        [
            "--emit-baseline",
            "--repo-root",
            tmp_path.as_posix(),
            "--registry-path",
            registry_path.as_posix(),
            "--claude-md-path",
            (tmp_path / "CLAUDE.md").as_posix(),
            "--output",
            output_path.as_posix(),
            "--created",
            "2026-06-06",
            "--expiry",
            "2026-09-04",
        ]
    )

    written_payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert rc == 0
    assert written_payload == first
    assert capsys.readouterr().out.strip() == output_path.as_posix()
