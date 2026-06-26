from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from cli.lib.v3.cutover import gate as gate_module
from cli.lib.v3.cutover.gate import analyze_cutover, cutover_messages, load_cutover_input


def _write_markdown(path: Path, frontmatter: dict[str, str], body: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    if body:
        lines.append(body)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_python(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _build_repo(root: Path) -> Path:
    _write_markdown(
        root / "docs/plans/L7/L7-v3-engine-cutover-gateplan.md",
        {
            "plan_id": "L7-v3-engine-cutover-gateplan",
            "kind": "impl",
            "layer": "L7",
            "drive": "be",
            "status": "draft",
            "updated_at": "2026-06-26T00:00:00Z",
        },
        "\n".join(
            [
                "related: [schema](../../v3/engine/schema-registry.md)",
                "generates:",
                "  - artifact_path: cli/lib/v3/cutover/gate.py",
                "dependencies:",
                "  requires:",
                "    - L7-v3-engine-c1-schema-registryplan",
            ]
        ),
    )
    _write_markdown(
        root / "docs/plans/L7/L7-v3-engine-c1-schema-registryplan.md",
        {
            "plan_id": "L7-v3-engine-c1-schema-registryplan",
            "kind": "impl",
            "layer": "L7",
            "drive": "be",
            "status": "ready",
            "updated_at": "2026-06-26T00:00:00Z",
        },
        "schema plan",
    )
    _write_markdown(
        root / "docs/v3/engine/schema-registry.md",
        {
            "source_kind": "artifact",
            "artifact_type": "design",
            "path": "docs/v3/engine/schema-registry.md",
            "status": "current",
            "updated_at": "2026-06-26T00:01:00Z",
        },
        "schema artifact",
    )
    _write_markdown(
        root / "docs/v3/cutover/cutover-design.md",
        {
            "source_kind": "artifact",
            "artifact_type": "design",
            "path": "docs/v3/cutover/cutover-design.md",
            "status": "current",
            "updated_at": "2026-06-26T00:02:00Z",
        },
        "See [schema](../engine/schema-registry.md).",
    )
    _write_python(
        root / "cli/lib/v3/cutover/helper.py",
        "VALUE = 'ok'\n",
    )
    _write_python(
        root / "cli/lib/v3/cutover/gate.py",
        "from .helper import VALUE\n\n\ndef marker() -> str:\n    return VALUE\n",
    )
    _write_python(
        root / "cli/lib/v3/cutover/__init__.py",
        "from .gate import marker\n",
    )
    return root


@pytest.fixture()
def repo_root(tmp_path: Path) -> Path:
    return _build_repo(tmp_path)


def _passing_config(repo_root: Path) -> dict[str, object]:
    archive_dir = repo_root / "archive"
    archive_dir.mkdir(exist_ok=True)
    return {
        "surviving_surface": [
            "cli/lib/v3/cutover/gate.py",
            "cli/lib/v3/cutover/__init__.py",
            "docs/v3/cutover/cutover-design.md",
        ],
        "retired_inventory": ["legacy/a.py", "legacy/b.py"],
        "retired_actual": ["legacy/a.py", "legacy/b.py"],
        "parity_attested": True,  # 退役(破壊)を伴う完全準備済 config は parity 明示 attestation を持つ
        "archive_dir": str(archive_dir),
        "v2_path_inventory": ["legacy/config.toml", "legacy/engine.py"],
        "current_v2_paths": ["legacy/config.toml", "legacy/engine.py"],
        "promote_reverse": {"mode": "shim", "steps": ["restore import"]},
        "window_expiry": "2026-06-30T00:00:00Z",
        "restore_dry_run": lambda: True,
        "detector_gap_policy": {
            "deadline": "2026-07-01T00:00:00Z",
            "owner": "qa",
            "bridge": "v2-detector",
        },
        "plan_paths": ["docs/plans/L7/L7-v3-engine-cutover-gateplan.md"],
    }


def test_ut_cut_01_rebuild_dry_run_passes_and_fails_on_writer_error(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: L7-v3-engine-cutover-gateplan UT-CUT-01"""
    result = analyze_cutover(load_cutover_input(repo_root, None, _passing_config(repo_root)))
    assert result.checks["rebuild_dry_run"].ok is True

    def _boom(db: sqlite3.Connection, sources: object) -> object:
        raise RuntimeError("boom")

    monkeypatch.setattr(gate_module.writer, "rebuild_projection", _boom)
    failed = analyze_cutover(load_cutover_input(repo_root, None, _passing_config(repo_root)))
    assert failed.checks["rebuild_dry_run"].ok is False
    assert "boom" in failed.checks["rebuild_dry_run"].missing[0]


def test_ut_cut_02_dangling_detects_broken_links_and_references(repo_root: Path) -> None:
    """DoD 検証: L7-v3-engine-cutover-gateplan UT-CUT-02"""
    ok_result = analyze_cutover(load_cutover_input(repo_root, None, _passing_config(repo_root)))
    assert ok_result.checks["dangling"].ok is True

    broken = repo_root / "docs/v3/cutover/broken.md"
    _write_markdown(
        broken,
        {
            "source_kind": "artifact",
            "artifact_type": "design",
            "path": "docs/v3/cutover/broken.md",
            "status": "current",
            "updated_at": "2026-06-26T00:03:00Z",
        },
        "See [missing](../engine/missing.md).",
    )

    failed = analyze_cutover(load_cutover_input(repo_root, None, _passing_config(repo_root)))
    assert failed.checks["dangling"].ok is False
    assert any("docs/v3/cutover/broken.md" in item for item in failed.checks["dangling"].missing)


def test_ut_cut_03_pin_inventory_uses_config_driven_set_equality(repo_root: Path) -> None:
    """DoD 検証: L7-v3-engine-cutover-gateplan UT-CUT-03"""
    result = analyze_cutover(load_cutover_input(repo_root, None, _passing_config(repo_root)))
    assert result.checks["pin_inventory"].ok is True

    config = _passing_config(repo_root)
    config["retired_actual"] = ["legacy/a.py"]
    failed = analyze_cutover(load_cutover_input(repo_root, None, config))
    assert failed.checks["pin_inventory"].ok is False
    assert failed.ok is False


def test_ut_cut_04_rollback_preflight_is_fail_close_for_missing_prereqs(repo_root: Path) -> None:
    """DoD 検証: L7-v3-engine-cutover-gateplan UT-CUT-04"""
    result = analyze_cutover(load_cutover_input(repo_root, None, _passing_config(repo_root)))
    assert result.checks["rollback_preflight"].ok is True

    config = _passing_config(repo_root)
    config["window_expiry"] = ""
    failed = analyze_cutover(load_cutover_input(repo_root, None, config))
    assert failed.checks["rollback_preflight"].ok is False
    assert "window_expiry" in failed.checks["rollback_preflight"].missing


def test_ut_cut_05_gate_ok_is_and_of_four_hard_checks(repo_root: Path) -> None:
    """DoD 検証: L7-v3-engine-cutover-gateplan UT-CUT-05"""
    result = analyze_cutover(load_cutover_input(repo_root, None, _passing_config(repo_root)))
    assert result.ok is True

    config = _passing_config(repo_root)
    config["surviving_surface"] = ["cli/lib/v3/cutover/missing.py"]
    failed = analyze_cutover(load_cutover_input(repo_root, None, config))
    assert failed.checks["pin_inventory"].ok is False
    assert failed.ok is False


def test_ut_cut_06_detector_gap_requires_deadline_owner_bridge(repo_root: Path) -> None:
    """DoD 検証: L7-v3-engine-cutover-gateplan UT-CUT-06"""
    result = analyze_cutover(load_cutover_input(repo_root, None, _passing_config(repo_root)))
    accepted = result.accepted_gap
    assert accepted is not None
    assert accepted.ok is True
    assert accepted.findings[0].id == "accepted_gap"

    config = _passing_config(repo_root)
    config["detector_gap_policy"] = {"deadline": "2026-07-01T00:00:00Z", "owner": "", "bridge": "v2-detector"}
    failed = analyze_cutover(load_cutover_input(repo_root, None, config))
    assert failed.accepted_gap is not None
    assert failed.accepted_gap.ok is False
    assert failed.ok is False


def test_ut_cut_07_findings_are_machine_readable(repo_root: Path) -> None:
    """DoD 検証: L7-v3-engine-cutover-gateplan UT-CUT-07"""
    result = analyze_cutover(load_cutover_input(repo_root, None, _passing_config(repo_root)))
    findings = cutover_messages(result)
    by_id = {finding["id"]: finding for finding in findings}

    for check_id in ("pin_inventory", "dangling", "rollback_preflight", "rebuild_dry_run"):
        finding = by_id[check_id]
        assert set(finding) == {"id", "severity", "subject", "missing"}
        assert isinstance(finding["missing"], list)


def test_parity_floor_blocks_destructive_retire_without_attestation(repo_root: Path) -> None:
    """parity floor: 退役(破壊)ありで parity_attested 無し → pin_inventory + gate が赤。"""
    config = _passing_config(repo_root)
    config["parity_attested"] = False
    result = analyze_cutover(load_cutover_input(repo_root, None, config))
    pin = result.checks["pin_inventory"]
    assert pin.ok is False
    assert any("parity-not-attested" in message for message in pin.missing)
    assert result.ok is False


def test_parity_floor_not_required_for_nondestructive_cutover(repo_root: Path) -> None:
    """retire 空(非破壊)なら parity attestation 不要。"""
    config = _passing_config(repo_root)
    config["retired_inventory"] = []
    config["retired_actual"] = []
    config["parity_attested"] = False
    pin = analyze_cutover(load_cutover_input(repo_root, None, config)).checks["pin_inventory"]
    assert pin.ok is True
