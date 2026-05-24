"""DoD 検証: L7-helix-recover-implplan §2.D / §4.

RecoveryEngine の入口判定、recovery-log 生成、rollback 制約を固定する。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import recovery_plan_check
from recovery_engine import RecoveryCondition, RecoveryEngine, main


def _completed(
    args: list[str] | tuple[str, ...],
    *,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(list(args), returncode, stdout, stderr)


def _write_phase(path: Path, current_phase: str = "L4") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"current_phase: {current_phase}\n", encoding="utf-8")


def _make_engine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> RecoveryEngine:
    project_root = tmp_path / "project"
    project_root.mkdir()
    helix_dir = project_root / ".helix"
    helix_dir.mkdir()
    phase_path = helix_dir / "phase.yaml"
    _write_phase(phase_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("HELIX_HOME", str(Path(__file__).resolve().parents[3]))
    return RecoveryEngine(
        helix_db_path=helix_dir / "helix.db",
        phase_yaml_path=phase_path,
        project_root=project_root,
    )


def test_recovery_condition_validates_literals_and_properties() -> None:
    cond = RecoveryCondition(
        condition_id="C1",
        severity="WARN",
        source="git_diff_numstat",
        metric_value=31,
        threshold=30,
        evidence="31 files changed",
        detail="detail",
    )

    assert cond.triggered is True
    assert cond.requires_attention is True
    assert RecoveryCondition(
        condition_id="C2",
        severity="UNKNOWN",
        source="agent_mandatory_audit",
        metric_value=None,
        threshold=None,
        evidence="unknown",
        detail="unknown detail",
    ).requires_attention is True
    with pytest.raises(TypeError):
        RecoveryCondition(
            condition_id="CX",  # type: ignore[arg-type]
            severity="WARN",
            source="git_diff_numstat",
            metric_value=None,
            threshold=None,
            evidence="bad",
            detail="bad",
        )
    with pytest.raises(TypeError):
        RecoveryCondition(
            condition_id="C1",
            severity="BAD",  # type: ignore[arg-type]
            source="git_diff_numstat",
            metric_value=None,
            threshold=None,
            evidence="bad",
            detail="bad",
        )


def test_check_condition_c1_all_clear_for_zero_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _make_engine(tmp_path, monkeypatch)

    def fake_run(args, cwd=None):
        if args[:2] == ["git", "diff"]:
            return _completed(args, stdout="")
        raise AssertionError(args)

    monkeypatch.setattr(engine, "_run_command", fake_run)

    cond = engine._check_c1(since_commits=1)

    assert cond.condition_id == "C1"
    assert cond.severity == "CLEAR"
    assert cond.metric_value == "0 files / 0 lines"
    assert cond.triggered is False


def test_check_condition_c1_warns_for_large_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _make_engine(tmp_path, monkeypatch)
    diff = "".join(f"1\t0\tfile-{idx}.py\n" for idx in range(31))

    monkeypatch.setattr(
        engine,
        "_run_command",
        lambda args, cwd=None: _completed(args, stdout=diff),
    )

    cond = engine._check_c1(since_commits=1)

    assert cond.severity == "WARN"
    assert cond.triggered is True
    assert "31 files" in cond.evidence


def test_check_condition_c1_respects_line_boundaries_and_binary_numstat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _make_engine(tmp_path, monkeypatch)

    cases = [
        ("750\t750\talpha.py\n-\t-\tbinary.dat\n", "CLEAR", "2 files / 1500 lines"),
        ("750\t751\talpha.py\n", "WARN", "1 files / 1501 lines"),
        ("1500\t1500\talpha.py\n", "WARN", "1 files / 3000 lines"),
        ("1500\t1501\talpha.py\n", "FAIL", "1 files / 3001 lines"),
    ]

    for stdout, expected_severity, expected_metric in cases:
        monkeypatch.setattr(
            engine,
            "_run_command",
            lambda args, cwd=None, stdout=stdout: _completed(args, stdout=stdout),
        )
        cond = engine._check_c1(since_commits=1)
        assert cond.severity == expected_severity
        assert cond.metric_value == expected_metric


def test_check_condition_c1_returns_unknown_when_git_diff_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _make_engine(tmp_path, monkeypatch)
    monkeypatch.setattr(
        engine,
        "_run_command",
        lambda args, cwd=None: _completed(args, returncode=128, stderr="fatal: bad revision 'HEAD~1'"),
    )

    cond = engine._check_c1(since_commits=1)

    assert cond.severity == "UNKNOWN"
    assert "bad revision" in cond.evidence


def test_check_condition_c2_warns_on_missing_mandatory_audit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _make_engine(tmp_path, monkeypatch)
    monkeypatch.setattr(
        sys.modules[RecoveryEngine.__module__],
        "agent_mandatory",
        type(
            "AgentMandatoryStub",
            (),
            {"audit_phase": staticmethod(lambda phase: {"phase": phase, "missing_count": 1, "warning": True})},
        )(),
    )
    monkeypatch.setattr(
        engine,
        "_run_command",
        lambda args, cwd=None: _completed(args, stdout=json.dumps({"fail": 0, "warn": 0})),
    )

    cond = engine._check_c2()

    assert cond.severity == "WARN"
    assert "missing_count=1" in cond.evidence


def test_check_condition_c2_returns_unknown_on_doctor_json_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _make_engine(tmp_path, monkeypatch)
    monkeypatch.setattr(
        sys.modules[RecoveryEngine.__module__],
        "agent_mandatory",
        type(
            "AgentMandatoryStub",
            (),
            {"audit_phase": staticmethod(lambda phase: {"phase": phase, "missing_count": 0, "warning": False})},
        )(),
    )
    monkeypatch.setattr(
        engine,
        "_run_command",
        lambda args, cwd=None: _completed(args, returncode=1, stderr="doctor json failed"),
    )

    cond = engine._check_c2()

    assert cond.severity == "UNKNOWN"
    assert "doctor json failed" in cond.evidence


def test_check_condition_c3_warns_on_escalated_handover(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _make_engine(tmp_path, monkeypatch)
    handover = engine.project_root / ".helix" / "handover" / "CURRENT.json"
    handover.parent.mkdir(parents=True, exist_ok=True)
    handover.write_text('{"task": {"status": "escalated"}}\n', encoding="utf-8")

    cond = engine._check_c3()

    assert cond.severity == "WARN"
    assert "escalated" in cond.evidence


def test_check_condition_c3_returns_unknown_on_handover_parse_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _make_engine(tmp_path, monkeypatch)
    handover = engine.project_root / ".helix" / "handover" / "CURRENT.json"
    handover.parent.mkdir(parents=True, exist_ok=True)
    handover.write_text("{broken\n", encoding="utf-8")

    cond = engine._check_c3()

    assert cond.severity == "UNKNOWN"
    assert "CURRENT.json parse failed" in cond.evidence


def test_check_condition_c4_warns_when_single_budget_exceeds_threshold(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _make_engine(tmp_path, monkeypatch)
    payload = {"claude": {"weekly_used_pct": 81}, "codex": {"weekly_used_pct": 20}}
    monkeypatch.setattr(
        engine,
        "_run_command",
        lambda args, cwd=None: _completed(args, stdout=json.dumps(payload)),
    )

    cond = engine._check_c4()

    assert cond.severity == "WARN"
    assert "claude=81" in cond.evidence


def test_check_condition_c4_fails_when_both_budgets_exceed_threshold(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _make_engine(tmp_path, monkeypatch)
    payload = {"claude": {"weekly_used_pct": 82}, "codex": {"weekly_used_pct": 90}}
    monkeypatch.setattr(
        engine,
        "_run_command",
        lambda args, cwd=None: _completed(args, stdout=json.dumps(payload)),
    )

    cond = engine._check_c4()

    assert cond.severity == "FAIL"
    assert "claude=82" in cond.evidence
    assert "codex=90" in cond.evidence


def test_check_condition_c4_returns_unknown_when_budget_keys_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _make_engine(tmp_path, monkeypatch)
    payload = {"claude": {"weekly_used_pct": 82}, "codex": {}}
    monkeypatch.setattr(
        engine,
        "_run_command",
        lambda args, cwd=None: _completed(args, stdout=json.dumps(payload)),
    )

    cond = engine._check_c4()

    assert cond.severity == "UNKNOWN"
    assert "missing weekly_used_pct" in cond.evidence


def test_dump_state_generates_recovery_log_with_required_sections(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _make_engine(tmp_path, monkeypatch)
    output_path = engine.project_root / ".helix" / "recovery" / "recovery-log.md"
    conditions = [
        RecoveryCondition("C1", "WARN", "git_diff_numstat", "31 files / 31 lines", "30 files / 1500 lines", "31 files changed", "detail-1"),
        RecoveryCondition("C3", "WARN", "handover_current_json", "escalated", "status=escalated", "handover escalated", "detail-3"),
    ]
    monkeypatch.setattr(
        engine,
        "_run_command",
        lambda args, cwd=None: _completed(args, stdout="abc123 fix\n"),
    )

    generated = Path(
        engine.dump_state(
            output_path,
            conditions,
            auto_routed_from="helix-route",
            route_signal="runaway",
        )
    )
    text = generated.read_text(encoding="utf-8")

    assert generated == output_path
    assert "## 事故記録" in text
    assert "## timeline" in text
    assert "## 認識訂正履歴" in text
    assert "route_signal: runaway" in text
    assert "routed_from: helix-route" in text
    assert "signal_to_condition_mapping: runaway -> C2" in text
    assert recovery_plan_check.check_recovery_template_sections(generated) == []


def test_draft_recovery_plan_structure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _make_engine(tmp_path, monkeypatch)
    plan = engine.draft_recovery_plan(
        [
            RecoveryCondition("C2", "WARN", "agent_mandatory_audit", 1, 1, "mandatory missing", "detail-2"),
        ],
        reopen_point="HEAD",
        auto_routed_from="helix-route",
    )

    assert "kind: recovery" in plan
    assert "reopen_point: HEAD" in plan
    assert "auto_routed_from: helix-route" in plan
    assert "## 再開ポイント" in plan


def test_rollback_cli_respects_dry_run_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    engine = _make_engine(tmp_path, monkeypatch)
    monkeypatch.setattr(
        sys.modules[RecoveryEngine.__module__],
        "RecoveryEngine",
        lambda *args, **kwargs: engine,
    )
    monkeypatch.setattr(
        engine,
        "suggest_rollback_point",
        lambda: {
            "git_commit_candidates": ["abc123"],
            "plan_candidates": ["PLAN-100"],
            "phase_snapshot": {"current_phase": "L4"},
            "note": "実行は手動ガード、--apply 不可",
        },
    )

    assert main(["rollback", "--dry-run"]) == 0
    dry_run = capsys.readouterr()
    assert "[dry-run]" in dry_run.out
    assert "abc123" in dry_run.out

    assert main(["rollback", "--apply"]) == 2
    apply_run = capsys.readouterr()
    assert "use 'helix recover rollback --dry-run' first" in apply_run.err
