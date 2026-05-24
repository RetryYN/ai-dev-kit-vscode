"""DoD 検証: L7-drive-agent-cli-connectplan の HELIX W agent CLI 実装."""

from __future__ import annotations

import importlib
import io
import py_compile
from contextlib import redirect_stdout
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(LIB_DIR))

MODULE_PATH = LIB_DIR / "agent_engine.py"


def _load_module():
    return importlib.import_module("agent_engine")


def _project_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(root))
    return root


def test_module_py_compile() -> None:
    """DoD 検証: agent_engine.py が py_compile を通る。"""
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_init_creates_current_state_and_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: init で HELIX W state を初期化する。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.AgentEngine(project_root=root)

    session = engine.init_session(agent_id="AG-001", summary="agent drive kickoff")

    assert session.agent_id == "AG-001"
    assert session.current_phase == "phase1"
    assert session.phase1["drive"] == "fullstack"
    assert (root / ".helix" / "agent" / "CURRENT.json").exists()
    assert (root / ".helix" / "agent" / "AG-001.md").exists()


def test_stage_progression_and_merge_route(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: stage1/stage2 完了後に merge と phase3 route へ進める。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.AgentEngine(project_root=root)
    engine.init_session(agent_id="AG-002", summary="two-stage flow")

    stage1 = engine.update_stage1(plan_id="L7-phase1-plan", drive="fullstack", status="ready")
    stage2 = engine.update_stage2(plan_id="L7-phase2-plan", status="ready")
    merged = engine.merge(plan_id="L10-phase3-plan")
    route = engine.route_current()

    assert stage1.phase1["status"] == "ready"
    assert stage2.phase2["status"] == "ready"
    assert merged.current_phase == "phase3"
    assert merged.phase3["status"] == "ready"
    assert route["phase"] == "phase3"
    assert route["drive"] == "agent"
    assert route["layers"] == ["L10", "L11", "L12", "L13", "L14"]


def test_merge_requires_ready_stage1_and_stage2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: merge は stage1/stage2 ready 前に fail-close。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.AgentEngine(project_root=root)
    engine.init_session(agent_id="AG-003", summary="blocked merge")
    engine.update_stage1(plan_id="L7-phase1-plan", drive="be", status="ready")

    with pytest.raises(module.AgentEngineError, match="stage2"):
        engine.merge(plan_id="L10-phase3-plan")


def test_route_defaults_to_phase2_after_stage1_ready(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: stage1 ready 後で stage2 未完なら route は phase2 を返す。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.AgentEngine(project_root=root)
    engine.init_session(agent_id="AG-004", summary="route to phase2")
    engine.update_stage1(plan_id="L7-phase1-plan", drive="db", status="ready")

    route = engine.route_current()

    assert route["phase"] == "phase2"
    assert route["drive"] == "agent"
    assert route["layers"] == ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9"]
    assert route["recommended_command"] == "helix agent stage2 --plan-id <PLAN> --status ready"


def test_main_prints_phase3_route_guidance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: CLI main は merge 後の route を表示する。"""
    module = _load_module()
    _project_root(tmp_path, monkeypatch)

    assert module.main(["init", "--agent-id", "AG-005", "--summary", "route guidance"]) == 0
    assert module.main(["stage1", "--plan-id", "L7-phase1-plan", "--drive", "fullstack", "--status", "ready"]) == 0
    assert module.main(["stage2", "--plan-id", "L7-phase2-plan", "--status", "ready"]) == 0
    assert module.main(["merge", "--plan-id", "L10-phase3-plan"]) == 0

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        assert module.main(["route"]) == 0

    output = buffer.getvalue()
    assert "phase: phase3" in output
    assert "L10, L11, L12, L13, L14" in output
