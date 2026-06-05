from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from registry_checks import RegistryLoadError
from functional_registry_checks import (
    check_fr_sot_alignment,
    check_functional_registry,
    load_functional_registry,
)


def _write_file(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_registry(path: Path, body: str) -> Path:
    return _write_file(path, textwrap.dedent(body).strip() + "\n")


def test_load_functional_registry_normalizes_entries_and_fails_closed(tmp_path: Path) -> None:
    """DoD 検証: functional-registry-detector-単体テスト設計.md UT-FREG-03"""
    registry_path = _write_registry(
        tmp_path / "functional-registry.yaml",
        """
        entries:
          - id: FR-CLI-001
            name: helix-alpha
            domain: cli
            description: alpha command
            l1_fr: FR-01
            l3_fr:
              - FR-9MODE-01
            status: active
            code_paths: cli/helix-alpha
            doc_paths: []
        """,
    )

    entries = load_functional_registry(registry_path)

    assert len(entries) == 1
    assert entries[0].id == "FR-CLI-001"
    assert entries[0].l1_fr == ["FR-01"]
    assert entries[0].l3_fr == ["FR-9MODE-01"]
    assert entries[0].code_paths == ["cli/helix-alpha"]
    assert entries[0].doc_paths == []

    missing_field_path = _write_registry(
        tmp_path / "broken-missing.yaml",
        """
        entries:
          - id: FR-CLI-002
            name: broken
            domain: cli
            description: missing status
            l1_fr: []
            l3_fr: []
            code_paths: []
            doc_paths: []
        """,
    )
    with pytest.raises(RegistryLoadError):
        load_functional_registry(missing_field_path)

    invalid_domain_path = _write_registry(
        tmp_path / "broken-domain.yaml",
        """
        entries:
          - id: FR-CLI-003
            name: broken-domain
            domain: invalid
            description: invalid domain
            l1_fr: []
            l3_fr: []
            status: active
            code_paths: []
            doc_paths: []
        """,
    )
    with pytest.raises(RegistryLoadError):
        load_functional_registry(invalid_domain_path)


def test_check_functional_registry_reports_four_finding_classes_and_stays_advisory(tmp_path: Path) -> None:
    """DoD 検証: functional-registry-detector-単体テスト設計.md UT-FREG-01"""
    _write_file(tmp_path / "cli/helix-alpha", "#!/bin/sh\n")
    _write_file(tmp_path / "cli/lib/beta.py", "print('beta')\n")
    _write_file(tmp_path / "cli/lib/gamma.py", "print('gamma')\n")
    orphan_path = _write_file(tmp_path / "cli/lib/orphan.py", "print('orphan')\n")

    registry_path = _write_registry(
        tmp_path / "functional-registry.yaml",
        """
        entries:
          - id: FR-CLI-001
            name: helix-alpha
            domain: cli
            description: alpha command
            l1_fr:
              - FR-01
            l3_fr:
              - FR-9MODE-01
            status: active
            code_paths:
              - cli/helix-alpha
            doc_paths: []
          - id: FR-LIB-001
            name: beta.py
            domain: lib
            description: beta library
            l1_fr:
              - FR-02
            l3_fr:
              - FR-INV-01
            status: active
            code_paths:
              - cli/lib/beta.py
            doc_paths: []
          - id: FR-LIB-002
            name: gamma.py
            domain: lib
            description: invalid trace library
            l1_fr: []
            l3_fr:
              - BAD-ID
            status: active
            code_paths:
              - cli/lib/gamma.py
            doc_paths: []
          - id: FR-LIB-002
            name: missing.py
            domain: lib
            description: duplicate id and missing path
            l1_fr:
              - FR-03
            l3_fr:
              - FR-EVT-01
            status: active
            code_paths:
              - cli/lib/missing.py
            doc_paths: []
          - id: FR-CLI-099
            name: helix-old
            domain: cli
            description: deprecated command
            l1_fr: []
            l3_fr: []
            status: deprecated
            code_paths:
              - cli/helix-old
            doc_paths: []
        """,
    )

    before_registry = registry_path.read_text(encoding="utf-8")
    before_orphan = orphan_path.read_text(encoding="utf-8")

    report = check_functional_registry(
        registry_path,
        tmp_path,
        scan_targets={
            "cli": ("cli/helix-*",),
            "lib": ("cli/lib/*.py",),
        },
    )

    finding_kinds = {finding.kind for finding in report.findings}
    finding_paths = {finding.path for finding in report.findings}
    finding_ids = {finding.entry_id for finding in report.findings}

    assert report.mode == "advisory"
    assert report.exit_policy == 0
    assert report.metrics["entries"] == 5
    assert {
        "missing_registered_path",
        "duplicate_id",
        "invalid_fr_trace",
        "unregistered_asset",
    }.issubset(finding_kinds)
    assert "cli/lib/missing.py" in finding_paths
    assert "cli/lib/orphan.py" in finding_paths
    assert "FR-LIB-002" in finding_ids
    assert "FR-CLI-099" not in finding_ids
    assert registry_path.read_text(encoding="utf-8") == before_registry
    assert orphan_path.read_text(encoding="utf-8") == before_orphan


def test_check_fr_sot_alignment_reports_count_and_name_drift_and_passes_when_aligned(tmp_path: Path) -> None:
    """DoD 検証: functional-registry-detector-単体テスト設計.md UT-FREG-02"""
    registry_path = _write_registry(
        tmp_path / "functional-registry.yaml",
        """
        entries:
          - id: FR-CLI-001
            name: helix-alpha
            domain: cli
            description: alpha command
            l1_fr:
              - FR-01
            l3_fr:
              - FR-9MODE-01
            status: active
            code_paths:
              - cli/helix-alpha
            doc_paths: []
          - id: FR-LIB-001
            name: beta.py
            domain: lib
            description: beta library
            l1_fr:
              - FR-02
            l3_fr:
              - FR-INV-01
            status: active
            code_paths:
              - cli/lib/beta.py
            doc_paths: []
        """,
    )
    md_path = _write_file(
        tmp_path / "functional-registry.md",
        textwrap.dedent(
            """
            # Registry

            ## §3. CLI binaries

            | CLI | 主機能 |
            |---|---|
            | helix-alpha | alpha |
            | helix-extra | extra |

            ## §4. CLI lib modules

            | Module | 責務 |
            |---|---|
            | beta.py | beta |
            """
        ).strip()
        + "\n",
    )
    aligned_md_path = _write_file(
        tmp_path / "functional-registry-aligned.md",
        textwrap.dedent(
            """
            # Registry

            ## §3. CLI binaries

            | CLI | 主機能 |
            |---|---|
            | helix-alpha | alpha |

            ## §4. CLI lib modules

            | Module | 責務 |
            |---|---|
            | beta.py | beta |
            """
        ).strip()
        + "\n",
    )

    before_md = md_path.read_text(encoding="utf-8")
    mismatch_report = check_fr_sot_alignment(md_path, registry_path)
    aligned_report = check_fr_sot_alignment(aligned_md_path, registry_path)

    mismatch_kinds = {finding.kind for finding in mismatch_report.findings}

    assert mismatch_report.mode == "advisory"
    assert mismatch_report.exit_policy == 0
    assert {"md_count_mismatch", "md_name_set_mismatch"} == mismatch_kinds
    assert aligned_report.findings == []
    assert md_path.read_text(encoding="utf-8") == before_md
