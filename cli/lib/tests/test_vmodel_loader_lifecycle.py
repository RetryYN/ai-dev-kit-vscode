from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path

import pytest
import yaml


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import vmodel_loader


def _write_config(tmp_path: Path, payload: dict) -> Path:
    config_path = tmp_path / "broken-lifecycle.yaml"
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return config_path


def test_validate_accepts_default_lifecycle_extensions() -> None:
    model = vmodel_loader.load_default()

    assert model.lifecycle["origin_mode_transitions"]["reverse_to_forward"]["automatic"] is True
    assert "observed_to_inferred" in model.lifecycle["evidence_status_transitions"]
    assert "forward_mode" in model.lifecycle["functional_freeze_applicability"]
    model.validate()


def test_validate_fails_when_origin_mode_transitions_missing(tmp_path: Path) -> None:
    broken = deepcopy(vmodel_loader.load_default().data)
    broken["lifecycle"].pop("origin_mode_transitions")

    with pytest.raises(ValueError, match="lifecycle.origin_mode_transitions must be a mapping"):
        vmodel_loader.VModelSemantics.load(_write_config(tmp_path, broken))


def test_validate_fails_when_reverse_to_forward_key_missing(tmp_path: Path) -> None:
    broken = deepcopy(vmodel_loader.load_default().data)
    broken["lifecycle"]["origin_mode_transitions"].pop("reverse_to_forward")

    with pytest.raises(
        ValueError,
        match="lifecycle.origin_mode_transitions.reverse_to_forward must be a mapping",
    ):
        vmodel_loader.VModelSemantics.load(_write_config(tmp_path, broken))


def test_validate_fails_when_evidence_status_transition_missing(tmp_path: Path) -> None:
    broken = deepcopy(vmodel_loader.load_default().data)
    broken["lifecycle"]["evidence_status_transitions"].pop("inferred_to_confirmed")

    with pytest.raises(
        ValueError,
        match="lifecycle.evidence_status_transitions.inferred_to_confirmed must be a non-empty string",
    ):
        vmodel_loader.VModelSemantics.load(_write_config(tmp_path, broken))
