from __future__ import annotations

import json
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from registry_checks import (
    DetectorReport,
    Finding,
    GatePolicy,
    RegistryEntry,
    RegistryLoadError,
    RegistryLoader,
    ValidationError,
)


def _write_file(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _full_evidence() -> dict[str, bool]:
    return {
        "baseline_clean": True,
        "full_audit_p0p1_zero": True,
        "changed_files_ratchet": True,
        "fp_zero_period": True,
        "perf_within_nfr": True,
    }


def test_registry_loader_load_normalizes_yaml_and_markdown_and_fails_closed(tmp_path: Path) -> None:
    """DoD 検証: registry-detector-単体テスト設計.md UT-RDB-01"""
    yaml_path = _write_file(
        tmp_path / "registry.yaml",
        "\n".join(
            [
                "entries:",
                "  - id: REG-001",
                "    name: YAML Entry",
                "    domain: cli",
                "    status: active",
                "    source_docs: docs/spec.md",
                "    traces: TRACE-001",
                "    paths:",
                "      - cli/lib/example.py",
                "    patterns: registry",
            ]
        )
        + "\n",
    )
    yaml_entries = RegistryLoader.load(yaml_path)
    assert len(yaml_entries) == 1
    assert yaml_entries[0].id == "REG-001"
    assert yaml_entries[0].source_docs == ["docs/spec.md"]
    assert yaml_entries[0].traces == ["TRACE-001"]
    assert yaml_entries[0].patterns == ["registry"]

    markdown_path = _write_file(
        tmp_path / "registry.md",
        "\n".join(
            [
                "---",
                "entries:",
                "  - id: REG-002",
                "    name: Markdown Entry",
                "    domain: docs",
                "    status: draft",
                "    source_docs:",
                "      - docs/spec.md",
                "    traces:",
                "      - TRACE-002",
                "    paths: cli/lib/example.py",
                "---",
                "",
                "# Registry",
            ]
        )
        + "\n",
    )
    markdown_entries = RegistryLoader.load(markdown_path)
    assert len(markdown_entries) == 1
    assert markdown_entries[0].id == "REG-002"
    assert markdown_entries[0].paths == ["cli/lib/example.py"]

    broken_path = _write_file(
        tmp_path / "broken.yaml",
        "\n".join(
            [
                "entries:",
                "  - id: REG-003",
                "    name: Broken Entry",
                "    domain: cli",
            ]
        )
        + "\n",
    )
    with pytest.raises(RegistryLoadError):
        RegistryLoader.load(broken_path)


def test_registry_entry_validate_normalizes_lists_and_rejects_missing_required_fields() -> None:
    """DoD 検証: registry-detector-単体テスト設計.md UT-RDB-02"""
    entry = RegistryEntry.validate(
        {
            "id": "REG-010",
            "name": "Sample",
            "domain": "cli",
            "status": "active",
            "source_docs": "docs/spec.md",
            "traces": ["TRACE-010"],
            "paths": "cli/lib/sample.py",
            "patterns": ["registry", "loader"],
            "metadata": {"owner": "qa"},
        }
    )
    assert entry.id == "REG-010"
    assert entry.source_docs == ["docs/spec.md"]
    assert entry.traces == ["TRACE-010"]
    assert entry.paths == ["cli/lib/sample.py"]
    assert entry.patterns == ["registry", "loader"]
    assert entry.metadata == {"owner": "qa"}

    with pytest.raises(ValidationError):
        RegistryEntry.validate(
            {
                "id": "REG-011",
                "name": "Missing Status",
                "domain": "cli",
            }
        )


def test_finding_validates_severity_and_kind_and_is_frozen() -> None:
    """DoD 検証: registry-detector-単体テスト設計.md UT-RDB-03"""
    finding = Finding(
        severity="P2",
        kind="missing_path",
        entry_id="REG-020",
        path="cli/lib/sample.py",
        message="missing path",
        remediation="register the path",
    )
    assert finding.entry_id == "REG-020"
    with pytest.raises(FrozenInstanceError):
        finding.kind = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError):
        Finding(
            severity="PX",
            kind="missing_path",
            entry_id="REG-020",
            path="cli/lib/sample.py",
            message="bad severity",
            remediation="fix",
        )
    with pytest.raises(ValueError):
        Finding(
            severity="P1",
            kind="",
            entry_id="REG-020",
            path="cli/lib/sample.py",
            message="missing kind",
            remediation="fix",
        )


def test_detector_report_build_derives_exit_policy_and_rejects_invalid_mode() -> None:
    """DoD 検証: registry-detector-単体テスト設計.md UT-RDB-04"""
    findings = [
        Finding(
            severity="P2",
            kind="missing_path",
            entry_id="REG-030",
            path="cli/lib/sample.py",
            message="missing path",
            remediation="register the path",
        )
    ]

    report = DetectorReport.build(
        check_name="check_registry",
        domain="cli",
        mode="advisory",
        findings=findings,
        metrics={"scanned": 1},
        baseline=set(),
    )
    assert report.check_name == "check_registry"
    assert report.domain == "cli"
    assert report.exit_policy == 0
    assert report.metrics == {"scanned": 1}

    with pytest.raises(ValueError):
        DetectorReport.build(
            check_name="check_registry",
            domain="cli",
            mode="invalid",
            findings=findings,
            metrics={},
            baseline=set(),
        )


def test_gate_policy_decide_respects_mode_invariants() -> None:
    """DoD 検証: registry-detector-単体テスト設計.md UT-RDB-05"""
    p0 = Finding(
        severity="P0",
        kind="critical_missing_path",
        entry_id="REG-040",
        path="cli/lib/sample.py",
        message="critical path missing",
        remediation="restore the file",
    )
    p2 = Finding(
        severity="P2",
        kind="missing_doc",
        entry_id="REG-041",
        path="docs/spec.md",
        message="doc missing",
        remediation="restore the doc",
    )

    assert GatePolicy.decide("advisory", [p0, p2], baseline=set()) == 0
    assert GatePolicy.decide("ratchet", [p2], baseline={p2.as_fingerprint()}) == 0
    assert GatePolicy.decide("ratchet", [p2], baseline=set()) == 1
    assert GatePolicy.decide("fail_close", [p2], baseline=set()) == 0
    assert GatePolicy.decide("fail_close", [p0], baseline=set()) == 1


def test_gate_policy_promote_requires_all_evidence_and_rejects_skip() -> None:
    """DoD 検証: registry-detector-単体テスト設計.md UT-RDB-06"""
    evidence = _full_evidence()
    assert GatePolicy.promote("advisory", evidence) == "ratchet"
    assert GatePolicy.promote("ratchet", evidence) == "fail_close"

    partial = _full_evidence()
    partial["fp_zero_period"] = False
    assert GatePolicy.promote("advisory", partial) == "advisory"

    with pytest.raises(ValueError):
        GatePolicy.promote(
            "advisory",
            {
                **_full_evidence(),
                "target_state": "fail_close",
            },
        )


def test_detector_report_render_outputs_text_and_json_in_stable_order() -> None:
    """DoD 検証: registry-detector-単体テスト設計.md UT-RDB-07"""
    findings = [
        Finding(
            severity="P2",
            kind="missing_doc",
            entry_id="REG-072",
            path="docs/b.md",
            message="doc missing",
            remediation="add doc",
        ),
        Finding(
            severity="P1",
            kind="missing_path",
            entry_id="REG-071",
            path="cli/lib/a.py",
            message="path missing",
            remediation="add path",
        ),
        Finding(
            severity="P1",
            kind="missing_trace",
            entry_id="REG-070",
            path="cli/lib/c.py",
            message="trace missing",
            remediation="add trace",
        ),
    ]
    report = DetectorReport.build(
        check_name="check_registry",
        domain="cli",
        mode="fail_close",
        findings=findings,
        metrics={"scanned": 3},
        baseline={"baseline-entry"},
    )

    text_output = report.render("text")
    assert text_output.index("REG-070") < text_output.index("REG-071") < text_output.index("REG-072")

    json_output = report.render("json")
    payload = json.loads(json_output)
    assert [item["entry_id"] for item in payload["findings"]] == ["REG-070", "REG-071", "REG-072"]
    assert payload["exit_policy"] == 1

    with pytest.raises(ValueError):
        report.render("yaml")
