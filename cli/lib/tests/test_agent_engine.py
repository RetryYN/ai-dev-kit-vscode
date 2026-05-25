"""DoD 検証: L7-drive-agent-cli-connectplan の HELIX W agent CLI 実装."""

from __future__ import annotations

import importlib
import io
import py_compile
from contextlib import redirect_stdout
from datetime import datetime
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


def _phase_payload(label: str, drive: str) -> dict[str, object]:
    return {
        "label": label,
        "drive": drive,
        "plan_id": None,
        "status": "pending",
        "summary": None,
        "started_at": None,
        "completed_at": None,
        "current_layer": None,
        "layer_history": [],
    }


def _write_plan(root: Path, layer: str, slug: str) -> Path:
    plan_dir = root / "docs" / "plans" / layer
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plan_dir / f"{layer}-{slug}plan.md"
    plan_path.write_text(f"# {layer} {slug}\n", encoding="utf-8")
    return plan_path


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
    assert session.phase1["current_layer"] is None
    assert session.phase1["layer_history"] == []
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


def test_from_dict_defaults_layer_state_for_backward_compatibility() -> None:
    """DoD 検証: 旧 payload から current_layer/layer_history を後方互換復元する。"""
    module = _load_module()

    session = module.AgentSession.from_dict(
        {
            "agent_id": "AG-006",
            "summary": "legacy payload",
            "phase1": {"label": "一般システム", "drive": "fullstack", "status": "pending"},
            "phase2": {"label": "エージェント昇華", "drive": "agent", "status": "pending"},
            "phase3": {"label": "L10-L14 合流", "drive": "agent", "status": "pending"},
        }
    )

    assert session.phase1["current_layer"] is None
    assert session.phase1["layer_history"] == []
    assert session.phase2["current_layer"] is None
    assert session.phase2["layer_history"] == []
    assert session.phase3["current_layer"] is None
    assert session.phase3["layer_history"] == []


def test_route_with_explicit_phase3_uses_phase3_layers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: phase 指定 route は phase3 layer 定義を返す。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.AgentEngine(project_root=root)
    engine.init_session(agent_id="AG-007", summary="explicit phase3 route")

    route = engine.route_current("phase3")

    assert route["phase"] == "phase3"
    assert route["layers"] == ["L10", "L11", "L12", "L13", "L14"]


def test_route_rejects_invalid_phase(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: route は不正 phase 指定を reject する。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.AgentEngine(project_root=root)
    engine.init_session(agent_id="AG-008", summary="invalid phase")

    with pytest.raises(module.AgentEngineError, match="unsupported phase"):
        engine.route_current("phase9")


def test_advance_layer_entered_initializes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: layer entered で current_layer と履歴を初期化する。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.AgentEngine(project_root=root)
    engine.init_session(agent_id="AG-009", summary="layer init")

    session = engine.advance_layer(phase="phase1", layer="L1", status="entered")

    entry = session.phase1["layer_history"][0]
    assert session.phase1["current_layer"] == "L1"
    assert entry["layer"] == "L1"
    assert entry["completed_at"] is None
    assert datetime.fromisoformat(entry["entered_at"])


def test_advance_layer_entered_auto_completes_previous(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: 新 layer entered 時に直前未完了 entry を自動完了する。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.AgentEngine(project_root=root)
    engine.init_session(agent_id="AG-010", summary="layer rollover")
    engine.advance_layer(phase="phase1", layer="L1", status="entered")

    session = engine.advance_layer(phase="phase1", layer="L2", status="entered")

    first, second = session.phase1["layer_history"]
    assert session.phase1["current_layer"] == "L2"
    assert first["layer"] == "L1"
    assert datetime.fromisoformat(first["completed_at"])
    assert second["layer"] == "L2"
    assert second["completed_at"] is None


def test_advance_layer_completed_marks_current(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: layer completed で最新 entry に completed_at を設定する。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.AgentEngine(project_root=root)
    engine.init_session(agent_id="AG-011", summary="complete layer")
    engine.advance_layer(phase="phase1", layer="L1", status="entered")

    session = engine.advance_layer(phase="phase1", layer="L1", status="completed")

    entry = session.phase1["layer_history"][-1]
    assert session.phase1["current_layer"] == "L1"
    assert entry["layer"] == "L1"
    assert datetime.fromisoformat(entry["completed_at"])


def test_advance_layer_rejects_invalid_layer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: phase に対応しない layer は exit_code=2 で reject する。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.AgentEngine(project_root=root)
    engine.init_session(agent_id="AG-012", summary="invalid layer")

    with pytest.raises(module.AgentEngineError, match="unsupported layer"):
        engine.advance_layer(phase="phase1", layer="L20", status="entered")


def test_advance_layer_rejects_completed_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: completed 対象が最新 entry と不一致なら fail-close。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.AgentEngine(project_root=root)
    engine.init_session(agent_id="AG-013", summary="mismatch complete")
    engine.advance_layer(phase="phase1", layer="L1", status="entered")

    with pytest.raises(module.AgentEngineError, match="layer mismatch"):
        engine.advance_layer(phase="phase1", layer="L2", status="completed")


def test_advance_layer_emits_pair_warning_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: L7-advance-layer-pair-check-connectplan.md U-001 pair_missing は warning/timeline を追加する。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    _write_plan(root, "L4", "design")
    engine = module.AgentEngine(project_root=root)
    engine.init_session(agent_id="AG-014", summary="pair missing warning")

    session = engine.advance_layer(phase="phase1", layer="L4", status="entered")

    assert any("vmodel pair freeze missing: layer=L4" in warning for warning in session.warnings)
    assert session.timeline[-1]["event"] == "vmodel_pair_warning"
    assert "pair_missing: layer=L4" in session.timeline[-1]["detail"]


def test_advance_layer_no_warning_when_pair_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: L7-advance-layer-pair-check-connectplan.md U-002 pair 存在時は warning を増やさない。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    _write_plan(root, "L4", "design")
    _write_plan(root, "L9", "system-test")
    engine = module.AgentEngine(project_root=root)
    engine.init_session(agent_id="AG-015", summary="pair exists")

    session = engine.advance_layer(phase="phase1", layer="L4", status="entered")

    assert not any("vmodel pair freeze" in warning for warning in session.warnings)
    assert session.timeline[-1]["event"] == "layer"


def test_advance_layer_no_warning_for_no_pair_layer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: L7-advance-layer-pair-check-connectplan.md U-003 pair なし layer は通常進行する。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.AgentEngine(project_root=root)
    engine.init_session(agent_id="AG-016", summary="no pair layer")

    session = engine.advance_layer(phase="phase3", layer="L11", status="entered")

    assert session.phase3["current_layer"] == "L11"
    assert not any("vmodel pair freeze" in warning for warning in session.warnings)
    assert session.timeline[-1]["event"] == "layer"


def test_init_session_sets_active_phases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: init_session 後に active_phases は phase1 で初期化される。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.AgentEngine(project_root=root)

    session = engine.init_session(agent_id="AG-017", summary="active phases init")

    assert session.active_phases == ["phase1"]
    assert session.current_phase == "phase1"


def test_start_phase_adds_to_active(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: start_phase は active_phases に重複なく phase を追加する。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.AgentEngine(project_root=root)
    engine.init_session(agent_id="AG-018", summary="start phase")

    session = engine.start_phase(phase="phase2")

    assert session.active_phases == ["phase1", "phase2"]
    assert session.phase2["status"] == "in_progress"


def test_pause_phase_removes_from_active(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: pause_phase は active_phases から対象 phase を取り除く。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.AgentEngine(project_root=root)
    engine.init_session(agent_id="AG-019", summary="pause phase")
    engine.start_phase(phase="phase2")

    session = engine.pause_phase(phase="phase1")

    assert session.active_phases == ["phase2"]


def test_resume_phase_re_adds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: resume_phase は pause 済み phase を末尾へ再追加する。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.AgentEngine(project_root=root)
    engine.init_session(agent_id="AG-020", summary="resume phase")
    engine.start_phase(phase="phase2")
    engine.pause_phase(phase="phase1")

    session = engine.resume_phase(phase="phase1")

    assert session.active_phases == ["phase2", "phase1"]


def test_start_phase_rejects_invalid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: start_phase は不正 phase を exit_code=2 で reject する。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.AgentEngine(project_root=root)
    engine.init_session(agent_id="AG-021", summary="invalid start phase")

    with pytest.raises(module.AgentEngineError, match="unsupported phase") as exc_info:
        engine.start_phase(phase="phase99")

    assert exc_info.value.exit_code == 2


def test_from_dict_legacy_compatibility_active_phases_default() -> None:
    """DoD 検証: active_phases がない旧 payload は phase1 を補完する。"""
    module = _load_module()

    session = module.AgentSession.from_dict(
        {
            "agent_id": "AG-019",
            "summary": "legacy active phases",
            "current_phase": "phase2",
            "phase1": {"label": "一般システム", "drive": "fullstack", "status": "pending"},
            "phase2": {"label": "エージェント昇華", "drive": "agent", "status": "pending"},
            "phase3": {"label": "L10-L14 合流", "drive": "agent", "status": "pending"},
        }
    )

    assert session.active_phases == ["phase1"]
    assert session.current_phase == "phase1"


def test_current_phase_property_returns_first_active() -> None:
    """DoD 検証: current_phase property は active_phases の先頭を返す。"""
    module = _load_module()

    session = module.AgentSession(
        agent_id="AG-020",
        summary="current phase property",
        status="initialized",
        active_phases=["phase2"],
        parent_design=module.PARENT_DESIGN,
        phase1=_phase_payload("一般システム", "fullstack"),
        phase2=_phase_payload("エージェント昇華", "agent"),
        phase3=_phase_payload("L10-L14 合流", "agent"),
        warnings=[],
        timeline=[],
        log_path=".helix/agent/AG-020.md",
    )

    assert session.current_phase == "phase2"
