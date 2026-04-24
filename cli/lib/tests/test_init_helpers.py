import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import init_helpers
import yaml_parser


TEMPLATE_PHASE = Path(__file__).resolve().parents[2] / "templates" / "phase.yaml"


def _copy_phase(tmp_path: Path) -> Path:
    phase_path = tmp_path / "phase.yaml"
    phase_path.write_text(TEMPLATE_PHASE.read_text(encoding="utf-8"), encoding="utf-8")
    return phase_path


def _load(path: Path) -> dict:
    return yaml_parser.parse_yaml(path.read_text(encoding="utf-8"))


def test_apply_start_phase_l4_sets_prereq_gates_skipped(tmp_path: Path) -> None:
    phase_path = _copy_phase(tmp_path)

    init_helpers.apply_start_phase(phase_path, "L4")

    data = _load(phase_path)
    assert data["current_phase"] == "L4"
    for gate in ("G0.5", "G1", "G2", "G3"):
        assert yaml_parser.get_nested(data, f"gates.{gate}.status") == "skipped"
    for gate in ("G4", "G5", "G6", "G7"):
        assert yaml_parser.get_nested(data, f"gates.{gate}.status") == "pending"
    assert yaml_parser.get_nested(data, "gates.G1.5.status") == "skipped"
    assert yaml_parser.get_nested(data, "gates.G1R.status") == "skipped"


def test_apply_start_phase_l1_is_noop(tmp_path: Path) -> None:
    phase_path = _copy_phase(tmp_path)
    before = phase_path.read_text(encoding="utf-8")

    init_helpers.apply_start_phase(phase_path, "L1")

    assert phase_path.read_text(encoding="utf-8") == before


def test_apply_start_phase_l8_sets_all_prereq_skipped(tmp_path: Path) -> None:
    phase_path = _copy_phase(tmp_path)

    init_helpers.apply_start_phase(phase_path, "L8")

    data = _load(phase_path)
    assert data["current_phase"] == "L8"
    for gate in ("G0.5", "G1", "G2", "G3", "G4", "G5", "G6", "G7"):
        assert yaml_parser.get_nested(data, f"gates.{gate}.status") == "skipped"


@pytest.mark.parametrize("phase", ["L9", "X"])
def test_apply_start_phase_rejects_unknown_phase(tmp_path: Path, phase: str) -> None:
    phase_path = _copy_phase(tmp_path)

    with pytest.raises(ValueError):
        init_helpers.apply_start_phase(phase_path, phase)


def test_apply_start_phase_preserves_other_fields(tmp_path: Path) -> None:
    phase_path = _copy_phase(tmp_path)

    init_helpers.apply_start_phase(phase_path, "L4")

    data = _load(phase_path)
    assert yaml_parser.get_nested(data, "sprint.status") == "active"
    assert data["sprint"]["phase_b"]["steps"][".b1"]["status"] == "pending"
    assert yaml_parser.get_nested(data, "reverse_gates.RG0.status") == "pending"
    assert yaml_parser.get_nested(data, "reverse.status") is None
