import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import command_mapper


def test_derive_commands_merges_explicit_layer_gate_and_category_commands() -> None:
    skill_data = {
        "id": "common/testing",
        "metadata": {
            "commands": ["custom-cmd", "/test"],
            "helix_layer": "L6",
            "helix_gate": ["G6", "G4"],
        },
    }

    result = command_mapper.derive_commands(skill_data)

    assert result[0:2] == ["custom-cmd", "/test"]
    assert "helix-gate G6" in result
    assert "helix-gate G4" in result
    assert "qa-test" in result
    assert result.count("/test") == 1


def test_derive_commands_builds_skill_id_from_category_and_name() -> None:
    skill_data = {"category": "workflow", "name": "deploy"}

    result = command_mapper.derive_commands(skill_data)

    assert result == ["helix-pr", "/ship"]


def test_derive_commands_returns_empty_for_unknown_skill() -> None:
    assert command_mapper.derive_commands({"id": "unknown/skill"}) == []
