import logging
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
        assert codex_thinking.resolve_thinking("pg") == "low"

    assert "resolved thinking=low" in caplog.text
    assert "source=role-default" in caplog.text
