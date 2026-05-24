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


INJECTION_FIELDS = (
    "owner_role",
    "mandatory_agents",
    "recommended_agents",
    "recommended_skills",
    "recommended_commands",
    "orchestration_mode",
)


@pytest.fixture
def valid_semantics() -> dict:
    return deepcopy(vmodel_loader.load_default().data)


def _write_semantics(tmp_path: Path, semantics: dict) -> Path:
    config_path = tmp_path / "broken-vmodel.yaml"
    config_path.write_text(yaml.safe_dump(semantics, sort_keys=False), encoding="utf-8")
    return config_path


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

    assert set(layer.keys()) == {"design", "test", "pair", "injection"}
    assert layer["design"]["review_unit"] == "plan"
    assert layer["test"]["test_level"] == "operational"
    assert layer["pair"]["vertical_to"] == "requirement"
    assert layer["injection"]["owner_role"] == "pm"
    assert layer["injection"]["orchestration_mode"] == "pm_lead"


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


@pytest.mark.parametrize("missing_field", INJECTION_FIELDS)
def test_injection_required_6_fields(valid_semantics: dict, tmp_path: Path, missing_field: str) -> None:
    broken = deepcopy(valid_semantics)
    injection = broken["drives"]["be"]["layers"]["planning"]["injection"]
    injection.pop(missing_field)
    config_path = _write_semantics(tmp_path, broken)

    with pytest.raises(
        vmodel_loader.VmodelInjectionError,
        match=rf"be/planning/injection: missing required fields: .*{missing_field}",
    ):
        vmodel_loader.VModelSemantics.load(config_path)


def test_injection_owner_role_enum(valid_semantics: dict, tmp_path: Path) -> None:
    broken = deepcopy(valid_semantics)
    broken["drives"]["be"]["layers"]["planning"]["injection"]["owner_role"] = "boss"
    config_path = _write_semantics(tmp_path, broken)

    with pytest.raises(vmodel_loader.VmodelInjectionError, match="be/planning/injection: unknown owner_role 'boss'"):
        vmodel_loader.VModelSemantics.load(config_path)


def test_injection_orchestration_mode_enum(valid_semantics: dict, tmp_path: Path) -> None:
    broken = deepcopy(valid_semantics)
    broken["drives"]["be"]["layers"]["planning"]["injection"]["orchestration_mode"] = "freestyle"
    config_path = _write_semantics(tmp_path, broken)

    with pytest.raises(
        vmodel_loader.VmodelInjectionError,
        match="be/planning/injection: unknown orchestration_mode 'freestyle'",
    ):
        vmodel_loader.VModelSemantics.load(config_path)


def test_injection_unknown_skill_id_fails(valid_semantics: dict, tmp_path: Path) -> None:
    broken = deepcopy(valid_semantics)
    broken["drives"]["be"]["layers"]["planning"]["injection"]["recommended_skills"] = ["workflow/nonexistent"]
    config_path = _write_semantics(tmp_path, broken)

    with pytest.raises(
        vmodel_loader.VmodelInjectionError,
        match="be/planning/injection: unknown skill 'workflow/nonexistent' in recommended_skills",
    ):
        vmodel_loader.VModelSemantics.load(config_path)


def test_injection_unknown_command_fails(valid_semantics: dict, tmp_path: Path) -> None:
    broken = deepcopy(valid_semantics)
    broken["drives"]["be"]["layers"]["planning"]["injection"]["recommended_commands"] = ["helix detect"]
    config_path = _write_semantics(tmp_path, broken)

    with pytest.raises(
        vmodel_loader.VmodelInjectionError,
        match="be/planning/injection: unknown command 'helix detect' in recommended_commands",
    ):
        vmodel_loader.VModelSemantics.load(config_path)


@pytest.mark.parametrize(
    ("field_name", "expected_message"),
    (
        ("mandatory_agents", "be/planning/injection: unknown agent 'ghost-agent' in mandatory_agents"),
        ("recommended_agents", "be/planning/injection: unknown agent 'ghost-agent' in recommended_agents"),
    ),
)
def test_injection_unknown_agent_fails(
    valid_semantics: dict,
    tmp_path: Path,
    field_name: str,
    expected_message: str,
) -> None:
    broken = deepcopy(valid_semantics)
    broken["drives"]["be"]["layers"]["planning"]["injection"][field_name] = ["ghost-agent"]
    config_path = _write_semantics(tmp_path, broken)

    with pytest.raises(vmodel_loader.VmodelInjectionError, match=expected_message):
        vmodel_loader.VModelSemantics.load(config_path)
