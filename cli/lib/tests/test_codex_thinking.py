import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import codex_thinking


def test_resolve_thinking_cli_explicit_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(codex_thinking, "_auto_thinking", lambda *args, **kwargs: ("low", "ignored"))

    assert codex_thinking.resolve_thinking("se", cli_explicit="xhigh", auto_thinking=True, task="tiny fix") == "xhigh"


def test_resolve_thinking_auto_then_role_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(codex_thinking, "_auto_thinking", lambda *args, **kwargs: ("medium", "effort=medium score=4"))

    assert codex_thinking.resolve_thinking("se", auto_thinking=True, task="update tests") == "medium"


def test_resolve_thinking_role_default_fallback() -> None:
    assert codex_thinking.resolve_thinking("se") == "high"


def test_resolve_thinking_invalid_role_raises() -> None:
    with pytest.raises(ValueError, match="role not found"):
        codex_thinking.resolve_thinking("missing-role")


def test_resolve_thinking_env_inject(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setenv("HELIX_CURRENT_SPRINT", ".2")
    monkeypatch.setenv("HELIX_CURRENT_AGENT", "codex-se")

    with caplog.at_level(logging.INFO, logger=codex_thinking.__name__):
        assert codex_thinking.resolve_thinking("se") == "high"

    assert "sprint=.2" in caplog.text
    assert "agent=codex-se" in caplog.text


def test_resolve_thinking_logs_decision(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger=codex_thinking.__name__):
        assert codex_thinking.resolve_thinking("pg") == "medium"

    assert "resolved thinking=medium" in caplog.text
    assert "source=role-default" in caplog.text


def test_helix_codex_thinking_uses_resolve_function(tmp_path: Path) -> None:
    cli_dir = Path(__file__).resolve().parents[2]
    home_dir = tmp_path / "home"
    project_root = tmp_path / "project"
    home_dir.mkdir()
    project_root.mkdir()
    env = {
        **os.environ,
        "HELIX_HOME": str(cli_dir.parent),
        "HELIX_PROJECT_ROOT": str(project_root),
        "HOME": str(home_dir),
        "PATH": f"{cli_dir}:{os.environ.get('PATH', '')}",
    }

    proc = subprocess.run(
        [str(cli_dir / "helix-codex"), "--role", "pg", "--task", "tiny", "--dry-run"],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
        env=env,
    )

    assert proc.returncode == 0
    assert "[codex-thinking] resolved thinking=medium source=role-default role=pg" in proc.stderr
    assert "Thinking:  medium" in proc.stdout


def test_codex_thinking_priority_full(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def _fake_auto(task: str, role: str) -> tuple[str, str]:
        calls.append(f"auto:{task}:{role}")
        return "high", "effort=high score=8"

    def _fake_role_default(role: str) -> str:
        calls.append(f"default:{role}")
        return "medium"

    monkeypatch.setattr(codex_thinking, "_auto_thinking", _fake_auto)
    monkeypatch.setattr(codex_thinking, "_read_role_default", _fake_role_default)

    assert codex_thinking.resolve_thinking("se", cli_explicit="xhigh", auto_thinking=True, task="task") == "xhigh"
    assert calls == []

    assert codex_thinking.resolve_thinking("se", auto_thinking=True, task="task") == "high"
    assert calls == ["auto:task:se"]

    assert codex_thinking.resolve_thinking("se") == "medium"
    assert calls == ["auto:task:se", "default:se"]
