import json
import subprocess
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import session_start_helpers


def write_phase(
    project_root: Path,
    *,
    phase: str = "L3",
    mode: str = "forward",
    step: str | None = ".2",
    status: str = "active",
    drive: str | None = "be",
) -> None:
    helix_dir = project_root / ".helix"
    helix_dir.mkdir(parents=True)
    step_value = "null" if step is None else step
    drive_value = "null" if drive is None else drive
    (helix_dir / "phase.yaml").write_text(
        "\n".join(
            [
                f"current_phase: {phase}",
                f"current_mode: {mode}",
                "sprint:",
                f"  current_step: {step_value}",
                f"  status: {status}",
                f"  drive: {drive_value}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def fake_completed(stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["helix"], returncode=0, stdout=stdout, stderr="")


def test_build_progress_block_no_helix(tmp_path: Path) -> None:
    assert session_start_helpers.build_progress_block(tmp_path) == ""


def test_build_progress_block_basic(tmp_path: Path) -> None:
    write_phase(tmp_path)

    block = session_start_helpers.build_progress_block(tmp_path)

    assert "## HELIX 現在の進捗" in block
    assert "Phase: L3 / Sprint: .2 / Mode: forward" in block
    assert "Drive: be" in block


def test_build_progress_block_with_interrupted(tmp_path: Path, monkeypatch) -> None:
    write_phase(tmp_path, status="interrupted")

    def fake_run(*args, **kwargs):
        payload = [{"id": "INT-001", "reason": "PC終了", "status": "open"}]
        return fake_completed(json.dumps(payload, ensure_ascii=False))

    monkeypatch.setattr(session_start_helpers.subprocess, "run", fake_run)

    block = session_start_helpers.build_progress_block(tmp_path)

    assert "⚠️ 前回セッション中断中" in block
    assert "Interrupt ID: INT-001 (reason: PC終了)" in block
    assert "helix interrupt resume --id INT-001" in block


def test_build_progress_block_with_handover(tmp_path: Path, monkeypatch) -> None:
    write_phase(tmp_path)
    handover_dir = tmp_path / ".helix" / "handover"
    handover_dir.mkdir()
    (handover_dir / "CURRENT.json").write_text("{}", encoding="utf-8")

    def fake_run(*args, **kwargs):
        payload = {
            "exists": True,
            "owner": "codex",
            "task": {"id": "T-001", "title": "JWT 実装", "status": "ready_for_review"},
        }
        return fake_completed(json.dumps(payload, ensure_ascii=False))

    monkeypatch.setattr(session_start_helpers.subprocess, "run", fake_run)

    block = session_start_helpers.build_progress_block(tmp_path)

    assert "🤝 Handover 引き継ぎ中" in block
    assert 'Task: T-001 "JWT 実装" (owner=codex, status=ready_for_review)' in block
    assert "helix handover resume" in block


def test_build_progress_block_all_states(tmp_path: Path, monkeypatch) -> None:
    write_phase(tmp_path, status="interrupted")
    handover_dir = tmp_path / ".helix" / "handover"
    handover_dir.mkdir()
    (handover_dir / "CURRENT.json").write_text("{}", encoding="utf-8")

    def fake_run(cmd, *args, **kwargs):
        if "interrupt" in cmd:
            return fake_completed(
                json.dumps([{"id": "INT-001", "reason": "test", "status": "open"}])
            )
        payload = {
            "exists": True,
            "owner": "opus",
            "task": {"id": "T-002", "title": "handover test", "status": "in_progress"},
        }
        return fake_completed(json.dumps(payload))

    monkeypatch.setattr(session_start_helpers.subprocess, "run", fake_run)

    block = session_start_helpers.build_progress_block(tmp_path)

    assert "⚠️ 前回セッション中断中" in block
    assert "🤝 Handover 引き継ぎ中" in block
    assert "helix handover status" in block


def test_build_progress_block_corrupt_yaml(tmp_path: Path) -> None:
    helix_dir = tmp_path / ".helix"
    helix_dir.mkdir()
    (helix_dir / "phase.yaml").write_text("current_phase L3\n", encoding="utf-8")

    assert session_start_helpers.build_progress_block(tmp_path) == ""
