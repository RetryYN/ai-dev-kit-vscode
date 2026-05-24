"""DoD 検証: docs/v2/L7-test-design/L7-cli-helix-recovery-impl-test-design.md"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import recovery_workflow_engine as rwe


def _completed(
    args: list[str] | tuple[str, ...],
    *,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(list(args), returncode, stdout, stderr)


def _write_recovery_plan(project_root: Path, plan_id: str = "RECOVERY-001", kind: str = "recovery") -> None:
    plan_path = project_root / "docs" / "plans" / "L7" / "sample-plan.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        "\n".join(
            [
                "---",
                f"plan_id: {plan_id}",
                f"kind: {kind}",
                "status: draft",
                "---",
                "",
                "# Sample",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _make_engine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> rwe.RecoveryWorkflowEngine:
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("HELIX_HOME", str(Path(__file__).resolve().parents[3]))
    return rwe.RecoveryWorkflowEngine(project_root=project_root, helix_home=Path(__file__).resolve().parents[3])


def _conditions(*items: tuple[str, str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for condition_id, severity in items:
        rows.append(
            {
                "condition_id": condition_id,
                "severity": severity,
                "source": "stub",
                "metric_value": None,
                "threshold": None,
                "evidence": f"{condition_id}-{severity}",
                "detail": "detail",
                "triggered": severity != "CLEAR",
                "requires_attention": severity != "CLEAR",
            }
        )
    return rows


def test_start_session_persists_current_json_and_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-001 start は session と recovery-log を初期化する"""
    engine = _make_engine(tmp_path, monkeypatch)
    _write_recovery_plan(engine.project_root)
    monkeypatch.setattr(engine, "_load_triggered_conditions_from_recover_check", lambda: _conditions(("C2", "WARN")))
    monkeypatch.setattr(engine, "_is_stop_hook_registered", lambda: True)

    session = engine.start_session("RECOVERY-001", "HEAD~3")

    assert session.current_phase == "RP-1"
    assert engine.current_path.exists()
    assert (engine.project_root / session.log_path).exists()


def test_start_session_dry_run_does_not_write_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-002 dry-run start は永続化しない"""
    engine = _make_engine(tmp_path, monkeypatch)
    _write_recovery_plan(engine.project_root)
    monkeypatch.setattr(engine, "_load_triggered_conditions_from_recover_check", lambda: _conditions(("C1", "WARN")))
    monkeypatch.setattr(engine, "_is_stop_hook_registered", lambda: True)

    session = engine.start_session("RECOVERY-001", "HEAD", dry_run=True)

    assert session.current_phase == "RP-2"
    assert not engine.current_path.exists()


def test_start_session_rejects_non_recovery_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-003 kind!=recovery は exit 1 相当で拒否する"""
    engine = _make_engine(tmp_path, monkeypatch)
    _write_recovery_plan(engine.project_root, kind="impl")

    with pytest.raises(rwe.RecoveryWorkflowError, match="PLAN kind must be recovery"):
        engine.start_session("RECOVERY-001", None)


def test_start_session_rejects_active_duplicate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-004 active session 重複は exit 2 相当で拒否する"""
    engine = _make_engine(tmp_path, monkeypatch)
    _write_recovery_plan(engine.project_root)
    monkeypatch.setattr(engine, "_load_triggered_conditions_from_recover_check", lambda: _conditions(("C1", "WARN")))
    monkeypatch.setattr(engine, "_is_stop_hook_registered", lambda: True)
    engine.start_session("RECOVERY-001", None)

    with pytest.raises(rwe.RecoveryWorkflowError) as exc_info:
        engine.start_session("RECOVERY-001", None)

    assert exc_info.value.exit_code == 2


def test_select_start_phase_prefers_severity_then_priority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-005 複数条件は severity/priority 順で初期 phase を選ぶ"""
    engine = _make_engine(tmp_path, monkeypatch)

    phase = engine._select_start_phase(_conditions(("C3", "WARN"), ("C1", "WARN")))
    assert phase == "RP-2"

    phase = engine._select_start_phase(_conditions(("C1", "WARN"), ("C2", "FAIL")))
    assert phase == "RP-1"


def test_get_status_returns_none_when_current_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-006 status は session 不在時に None を返す"""
    engine = _make_engine(tmp_path, monkeypatch)
    assert engine.get_status() is None


def test_advance_phase_updates_session_and_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-007 phase advance は session と timeline を更新する"""
    engine = _make_engine(tmp_path, monkeypatch)
    _write_recovery_plan(engine.project_root)
    monkeypatch.setattr(engine, "_load_triggered_conditions_from_recover_check", lambda: _conditions(("C2", "WARN")))
    monkeypatch.setattr(engine, "_is_stop_hook_registered", lambda: True)
    session = engine.start_session("RECOVERY-001", None)

    updated = engine.advance_phase(session.current_phase, "RP-4")

    assert updated.current_phase == "RP-4"
    text = (engine.project_root / session.log_path).read_text(encoding="utf-8")
    assert "phase advanced" in text


def test_advance_phase_rejects_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-008 current phase 不一致は拒否する"""
    engine = _make_engine(tmp_path, monkeypatch)
    _write_recovery_plan(engine.project_root)
    monkeypatch.setattr(engine, "_load_triggered_conditions_from_recover_check", lambda: _conditions(("C2", "WARN")))
    monkeypatch.setattr(engine, "_is_stop_hook_registered", lambda: True)
    engine.start_session("RECOVERY-001", None)

    with pytest.raises(rwe.RecoveryWorkflowError, match="current phase mismatch"):
        engine.advance_phase("RP-2", "RP-4")


def test_append_log_adds_entry_to_correction_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-009 log append は認識訂正履歴へ追記する"""
    engine = _make_engine(tmp_path, monkeypatch)
    _write_recovery_plan(engine.project_root)
    monkeypatch.setattr(engine, "_load_triggered_conditions_from_recover_check", lambda: _conditions(("C3", "WARN")))
    monkeypatch.setattr(engine, "_is_stop_hook_registered", lambda: True)
    session = engine.start_session("RECOVERY-001", None)

    engine.append_log("API 契約差分を修正")

    text = (engine.project_root / session.log_path).read_text(encoding="utf-8")
    assert "API 契約差分を修正" in text


def test_export_log_copies_markdown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-010 log export は任意 path へ複製する"""
    engine = _make_engine(tmp_path, monkeypatch)
    _write_recovery_plan(engine.project_root)
    monkeypatch.setattr(engine, "_load_triggered_conditions_from_recover_check", lambda: _conditions(("C3", "WARN")))
    monkeypatch.setattr(engine, "_is_stop_hook_registered", lambda: True)
    engine.start_session("RECOVERY-001", None)

    exported = engine.export_log(engine.project_root / "docs" / "runbook" / "out.md")

    assert exported.exists()
    assert exported.read_text(encoding="utf-8").startswith("---")


def test_generate_postmortem_uses_fallback_template(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-011 postmortem は fallback template でも生成できる"""
    engine = _make_engine(tmp_path, monkeypatch)
    _write_recovery_plan(engine.project_root)
    template = engine.project_root / "cli" / "templates" / "plan" / "recovery" / "template.md"
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text("# Recovery Template\n\n{{RECOVERY_LOG}}\n", encoding="utf-8")
    monkeypatch.setattr(engine, "_load_triggered_conditions_from_recover_check", lambda: _conditions(("C1", "WARN")))
    monkeypatch.setattr(engine, "_is_stop_hook_registered", lambda: True)
    engine.start_session("RECOVERY-001", None)

    output = engine.generate_postmortem(engine.project_root / "docs" / "postmortem" / "pm.md")

    assert output.exists()
    assert "Recovery Template" in output.read_text(encoding="utf-8")


def test_generate_postmortem_rejects_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-012 postmortem は既存出力を上書きしない"""
    engine = _make_engine(tmp_path, monkeypatch)
    _write_recovery_plan(engine.project_root)
    monkeypatch.setattr(engine, "_load_triggered_conditions_from_recover_check", lambda: _conditions(("C1", "WARN")))
    monkeypatch.setattr(engine, "_is_stop_hook_registered", lambda: True)
    engine.start_session("RECOVERY-001", None)
    output = engine.project_root / "docs" / "postmortem" / "pm.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("existing\n", encoding="utf-8")

    with pytest.raises(rwe.RecoveryWorkflowError) as exc_info:
        engine.generate_postmortem(output)

    assert exc_info.value.exit_code == 2


def test_complete_session_skip_cutover_requires_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-013 skip-cutover には skip_reason が必須"""
    engine = _make_engine(tmp_path, monkeypatch)
    _write_recovery_plan(engine.project_root)
    monkeypatch.setattr(engine, "_load_triggered_conditions_from_recover_check", lambda: _conditions(("C1", "WARN")))
    monkeypatch.setattr(engine, "_is_stop_hook_registered", lambda: True)
    engine.start_session("RECOVERY-001", None)

    with pytest.raises(rwe.RecoveryWorkflowError, match="skip-reason"):
        engine.complete_session(
            confirm_token=None,
            forward_target=None,
            dry_run=False,
            skip_cutover=True,
            skip_reason=None,
        )


def test_complete_session_skip_cutover_marks_completed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-014 skip-cutover は completed へ遷移する"""
    engine = _make_engine(tmp_path, monkeypatch)
    _write_recovery_plan(engine.project_root)
    monkeypatch.setattr(engine, "_load_triggered_conditions_from_recover_check", lambda: _conditions(("C1", "WARN")))
    monkeypatch.setattr(engine, "_is_stop_hook_registered", lambda: True)
    engine.start_session("RECOVERY-001", "L5")

    payload = engine.complete_session(
        confirm_token=None,
        forward_target=None,
        dry_run=False,
        skip_cutover=True,
        skip_reason="docs only",
    )

    assert payload["status"] == "skipped"
    assert engine.get_status().status == "completed"


def test_complete_session_rejects_invalid_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-015 confirm token 形式不正は exit 2 相当で拒否する"""
    engine = _make_engine(tmp_path, monkeypatch)
    _write_recovery_plan(engine.project_root)
    monkeypatch.setattr(engine, "_load_triggered_conditions_from_recover_check", lambda: _conditions(("C1", "WARN")))
    monkeypatch.setattr(engine, "_is_stop_hook_registered", lambda: True)
    engine.start_session("RECOVERY-001", None)

    with pytest.raises(rwe.RecoveryWorkflowError) as exc_info:
        engine.complete_session(
            confirm_token="BAD",
            forward_target=None,
            dry_run=True,
            skip_cutover=False,
            skip_reason=None,
        )

    assert exc_info.value.exit_code == 2


def test_complete_session_fail_closes_when_preflight_is_not_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-016 preflight NG は exit 1 相当で停止する"""
    engine = _make_engine(tmp_path, monkeypatch)
    _write_recovery_plan(engine.project_root)
    monkeypatch.setattr(engine, "_load_triggered_conditions_from_recover_check", lambda: _conditions(("C1", "WARN")))
    monkeypatch.setattr(engine, "_is_stop_hook_registered", lambda: True)
    engine.start_session("RECOVERY-001", None)
    monkeypatch.setattr(
        rwe.cutover_orchestrator,
        "cutover_preflight",
        lambda: rwe.cutover_orchestrator.CutoverPreflightResult(
            ready=False,
            blockers=["dual_write_unhealthy"],
            dual_write_health={"healthy": False},
            replay_completed=False,
        ),
    )

    with pytest.raises(rwe.RecoveryWorkflowError) as exc_info:
        engine.complete_session(
            confirm_token="PO-APPROVED-RECOVERY-001",
            forward_target=None,
            dry_run=False,
            skip_cutover=False,
            skip_reason=None,
        )

    assert exc_info.value.exit_code == 1


def test_complete_session_dry_run_returns_preflight_payload_without_completing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-017 done --dry-run は execute せず preflight のみ返す"""
    engine = _make_engine(tmp_path, monkeypatch)
    _write_recovery_plan(engine.project_root)
    monkeypatch.setattr(engine, "_load_triggered_conditions_from_recover_check", lambda: _conditions(("C1", "WARN")))
    monkeypatch.setattr(engine, "_is_stop_hook_registered", lambda: True)
    engine.start_session("RECOVERY-001", None)
    monkeypatch.setattr(
        rwe.cutover_orchestrator,
        "cutover_preflight",
        lambda: rwe.cutover_orchestrator.CutoverPreflightResult(
            ready=True,
            blockers=[],
            dual_write_health={"healthy": True},
            replay_completed=True,
        ),
    )

    payload = engine.complete_session(
        confirm_token="PO-APPROVED-RECOVERY-001",
        forward_target=None,
        dry_run=True,
        skip_cutover=False,
        skip_reason=None,
    )

    assert payload["status"] == "dry_run"
    assert engine.get_status().status == "active"


def test_complete_session_executes_cutover_and_marks_completed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-018 done 正常系は cutover 実行結果を返し completed へ遷移する"""
    engine = _make_engine(tmp_path, monkeypatch)
    _write_recovery_plan(engine.project_root)
    monkeypatch.setattr(engine, "_load_triggered_conditions_from_recover_check", lambda: _conditions(("C1", "WARN")))
    monkeypatch.setattr(engine, "_is_stop_hook_registered", lambda: True)
    engine.start_session("RECOVERY-001", None)
    monkeypatch.setattr(
        rwe.cutover_orchestrator,
        "cutover_preflight",
        lambda: rwe.cutover_orchestrator.CutoverPreflightResult(
            ready=True,
            blockers=[],
            dual_write_health={"healthy": True},
            replay_completed=True,
        ),
    )
    monkeypatch.setattr(
        rwe.cutover_orchestrator,
        "cutover_execute",
        lambda *, confirm_token: {"status": "ok", "confirm_token": confirm_token},
    )

    payload = engine.complete_session(
        confirm_token="PO-APPROVED-RECOVERY-001",
        forward_target="L5",
        dry_run=False,
        skip_cutover=False,
        skip_reason=None,
    )

    assert payload["status"] == "ok"
    assert engine.get_status().status == "completed"


def test_snapshot_on_stop_updates_timestamp_for_active_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-019 snapshot_on_stop は active session にのみ timestamp を残す"""
    engine = _make_engine(tmp_path, monkeypatch)
    _write_recovery_plan(engine.project_root)
    monkeypatch.setattr(engine, "_load_triggered_conditions_from_recover_check", lambda: _conditions(("C1", "WARN")))
    monkeypatch.setattr(engine, "_is_stop_hook_registered", lambda: True)
    engine.start_session("RECOVERY-001", None)

    engine.snapshot_on_stop()

    assert engine.get_status().last_snapshot_at is not None


def test_load_triggered_conditions_parses_recover_check_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD 検証: R-REC-020 recover check --json 出力を strict parse する"""
    engine = _make_engine(tmp_path, monkeypatch)
    payload = json.dumps(_conditions(("C4", "WARN")))
    monkeypatch.setattr(
        engine,
        "_run_command",
        lambda args: _completed(args, stdout=payload),
    )

    rows = engine._load_triggered_conditions_from_recover_check()

    assert rows[0]["condition_id"] == "C4"
    assert rows[0]["severity"] == "WARN"


def test_main_help_and_status_exit_codes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """DoD 検証: R-REC-021 CLI main は help 0 / status なし 1 を返す"""
    _make_engine(tmp_path, monkeypatch)

    assert rwe.main(["help"]) == 0
    help_output = capsys.readouterr().out
    assert "Usage: helix recovery" in help_output

    assert rwe.main(["status"]) == 1
    status_output = capsys.readouterr().out
    assert "No active recovery session" in status_output
