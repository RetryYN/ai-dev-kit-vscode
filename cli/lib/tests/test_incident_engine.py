"""DoD 検証: docs/plans/L7/L7-cli-helix-incident-implplan.md §4."""

from __future__ import annotations

import py_compile
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import incident_engine


MODULE_PATH = LIB_DIR / "incident_engine.py"


def _engine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> incident_engine.IncidentEngine:
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(root))
    return incident_engine.IncidentEngine(project_root=root)


def test_module_py_compile() -> None:
    """DoD 検証: incident_engine.py が py_compile を通る。"""
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_detect_creates_session_and_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: detect は CURRENT.json と incident log を初期化する。"""
    engine = _engine(tmp_path, monkeypatch)

    session = engine.detect_incident(
        incident_id="INC-001",
        summary="API 500 spike",
        severity="P0",
        env="prod",
    )

    assert session.status == "detected"
    assert engine.current_path.exists()
    assert (engine.project_root / session.log_path).exists()


def test_triage_defaults_kind_from_env_prod(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: prod incident は triage 時に recovery を既定とする。"""
    engine = _engine(tmp_path, monkeypatch)
    engine.detect_incident(incident_id="INC-001", summary="prod outage", severity="P0", env="prod")

    session = engine.triage_incident(owner="oncall", impact="checkout unavailable")

    assert session.status == "triaged"
    assert session.kind == "recovery"


def test_triage_defaults_kind_from_env_dev(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: dev incident は triage 時に troubleshoot を既定とする。"""
    engine = _engine(tmp_path, monkeypatch)
    engine.detect_incident(incident_id="INC-002", summary="staging regression", severity="P2", env="dev")

    session = engine.triage_incident(owner="dev", impact="preview broken")

    assert session.kind == "troubleshoot"


def test_hotfix_marks_mitigated_and_records_release_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: hotfix は mitigated へ遷移し release_ref を記録する。"""
    engine = _engine(tmp_path, monkeypatch)
    engine.detect_incident(incident_id="INC-003", summary="latency spike", severity="P1", env="prod")
    engine.triage_incident(owner="sre", impact="latency > SLO")

    session = engine.apply_hotfix(change="rollback config", release_ref="deploy-123")

    assert session.status == "mitigated"
    assert session.release_ref == "deploy-123"
    assert session.resolved_at is not None


def test_route_payload_connects_forward_layers_after_hotfix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: route は hotfix 後に L1/L3/L4-L6/L8/L9/L14 連携を返す。"""
    engine = _engine(tmp_path, monkeypatch)
    engine.detect_incident(incident_id="INC-004", summary="prod issue", severity="P1", env="prod")
    engine.triage_incident(owner="team", impact="login degraded")
    engine.apply_hotfix(change="feature flag off")

    payload = engine.build_route_payload()

    assert payload["ready_for_formalization"] is True
    assert [item["layer"] for item in payload["routes"]] == ["L1", "L3", "L4-L6", "L8", "L9", "L14"]


def test_postmortem_writes_markdown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: postmortem は markdown を生成する。"""
    engine = _engine(tmp_path, monkeypatch)
    engine.detect_incident(incident_id="INC-005", summary="queue stall", severity="P1", env="prod")
    engine.triage_incident(owner="ops", impact="jobs delayed")
    engine.apply_hotfix(change="worker restart")

    output = engine.generate_postmortem(engine.project_root / "docs" / "postmortem" / "INC-005.md")

    assert output.exists()
    assert "Forward Formalization" in output.read_text(encoding="utf-8")
