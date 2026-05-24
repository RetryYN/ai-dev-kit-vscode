"""DoD 検証: docs/v2/L7-test-design/L7-scrum-to-discovery-migration-enum-test-design.md MT-001-MT-006"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import discovery_compat


def test_get_compat_stage_defaults_to_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HELIX_DISCOVERY_COMPAT_STAGE", raising=False)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))

    assert discovery_compat.get_compat_stage() == 1


def test_get_compat_stage_reads_project_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    helix_dir = tmp_path / ".helix"
    helix_dir.mkdir()
    (helix_dir / "config.yaml").write_text(
        yaml.safe_dump({"discovery": {"compat_stage": 3}}, sort_keys=False),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HELIX_DISCOVERY_COMPAT_STAGE", raising=False)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))

    assert discovery_compat.get_compat_stage() == 3


def test_get_compat_stage_env_overrides_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    helix_dir = tmp_path / ".helix"
    helix_dir.mkdir()
    (helix_dir / "config.yaml").write_text(
        yaml.safe_dump({"discovery": {"compat_stage": 2}}, sort_keys=False),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("HELIX_DISCOVERY_COMPAT_STAGE", "4")

    assert discovery_compat.get_compat_stage() == 4


def test_get_compat_stage_rejects_invalid_value(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("HELIX_DISCOVERY_COMPAT_STAGE", "9")

    with pytest.raises(ValueError, match="HELIX_DISCOVERY_COMPAT_STAGE"):
        discovery_compat.get_compat_stage()


def test_phase_to_display_maps_s_phase_and_promotes_confirmed_decision() -> None:
    assert discovery_compat.phase_to_display("S0") == "D0"
    assert discovery_compat.phase_to_display("S2") == "D2"
    assert discovery_compat.phase_to_display("S3") == "D3"
    assert discovery_compat.phase_to_display("S3", decide_result="confirmed") == "D4"
    assert discovery_compat.phase_to_display("S3", decide_result="pivot") == "D3"


def test_display_to_phase_maps_d_phase_and_blocks_d4_write() -> None:
    assert discovery_compat.display_to_phase("D0") == "S0"
    assert discovery_compat.display_to_phase("D2") == "S2"
    with pytest.raises(ValueError, match="D4"):
        discovery_compat.display_to_phase("D4")

