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


def test_load_default_config() -> None:
    model = vmodel_loader.load_default()

    assert isinstance(model, vmodel_loader.VModelSemantics)
    assert model.data["schema_version"] == 1


def test_list_drives_returns_4() -> None:
    model = vmodel_loader.load_default()

    assert model.list_drives() == ["be", "fe", "db", "fullstack"]


def test_list_layers_returns_5() -> None:
    model = vmodel_loader.load_default()

    assert model.list_layers() == ["planning", "requirement", "architecture", "detailed", "functional"]


def test_get_layer_be_planning() -> None:
    model = vmodel_loader.load_default()

    layer = model.get_layer("be", "planning")

    assert set(layer.keys()) == {"design", "test", "pair"}
    assert layer["design"]["review_unit"] == "plan"
    assert layer["test"]["test_level"] == "operational"
    assert layer["pair"]["vertical_to"] == "requirement"


def test_validate_passes_on_default() -> None:
    model = vmodel_loader.load_default()

    model.validate()


def test_validate_fails_on_missing_drive(tmp_path: Path) -> None:
    model = vmodel_loader.load_default()
    broken = deepcopy(model.data)
    broken["drives"].pop("db")
    config_path = tmp_path / "broken-vmodel.yaml"
    config_path.write_text(yaml.safe_dump(broken, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match="drives missing entries: db"):
        vmodel_loader.VModelSemantics.load(config_path)


def test_origin_modes_returns_3() -> None:
    model = vmodel_loader.load_default()

    assert model.origin_modes() == ["forward", "reverse", "scrum"]


def test_evidence_statuses_returns_3() -> None:
    model = vmodel_loader.load_default()

    assert model.evidence_statuses() == ["observed", "inferred", "confirmed"]
