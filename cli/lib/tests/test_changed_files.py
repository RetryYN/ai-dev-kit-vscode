from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import changed_files as changed_files_module


def test_changed_files_prefers_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: WI-B changed-files helper は HELIX_CHANGED_FILES を最優先する。"""

    def _unexpected_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("git should not run when HELIX_CHANGED_FILES is set")

    monkeypatch.setenv("HELIX_CHANGED_FILES", "a.py\nb.sh  c.py")
    monkeypatch.setattr(changed_files_module.subprocess, "run", _unexpected_run)

    payload = changed_files_module.changed_files()

    assert payload == {
        "files": ["a.py", "b.sh", "c.py"],
        "source_status": "available_nonempty",
    }


def test_changed_files_uses_git_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: WI-B changed-files helper は env 未設定時に git diff fallback を使う。"""

    def _fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
        assert command[:4] == ["git", "diff", "--name-only", "origin/main..HEAD"]
        return subprocess.CompletedProcess(command, 0, stdout="cli/a.py\ncli/b.sh\n", stderr="")

    monkeypatch.delenv("HELIX_CHANGED_FILES", raising=False)
    monkeypatch.setattr(changed_files_module, "_default_upstream", lambda: "origin/main")
    monkeypatch.setattr(changed_files_module.subprocess, "run", _fake_run)

    payload = changed_files_module.changed_files()

    assert payload == {
        "files": ["cli/a.py", "cli/b.sh"],
        "source_status": "available_nonempty",
    }


def test_changed_files_distinguishes_empty_from_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: WI-B changed-files helper は empty と unavailable を分離する。"""

    monkeypatch.delenv("HELIX_CHANGED_FILES", raising=False)
    monkeypatch.setattr(changed_files_module, "_default_upstream", lambda: "origin/main")

    def _empty_run(command, **kwargs):  # type: ignore[no-untyped-def]
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(changed_files_module.subprocess, "run", _empty_run)
    assert changed_files_module.changed_files() == {
        "files": [],
        "source_status": "available_empty",
    }

    def _failing_run(command, **kwargs):  # type: ignore[no-untyped-def]
        return subprocess.CompletedProcess(command, 128, stdout="", stderr="fatal")

    monkeypatch.setattr(changed_files_module.subprocess, "run", _failing_run)
    assert changed_files_module.changed_files() == {
        "files": [],
        "source_status": "unavailable",
    }


def test_changed_files_returns_unavailable_on_resolution_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: WI-B changed-files helper は upstream 解決例外でも unavailable を返す。"""

    monkeypatch.delenv("HELIX_CHANGED_FILES", raising=False)
    monkeypatch.setattr(
        changed_files_module,
        "_default_upstream",
        lambda: (_ for _ in ()).throw(RuntimeError("branch resolution failed")),
    )

    payload = changed_files_module.changed_files()

    assert payload == {
        "files": [],
        "source_status": "unavailable",
    }


def test_changed_files_returns_unavailable_on_subprocess_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: WI-B changed-files helper は git 実行例外でも unavailable を返す。"""

    def _raising_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise subprocess.TimeoutExpired(cmd="git diff", timeout=1)

    monkeypatch.delenv("HELIX_CHANGED_FILES", raising=False)
    monkeypatch.setattr(changed_files_module, "_default_upstream", lambda: "origin/main")
    monkeypatch.setattr(changed_files_module.subprocess, "run", _raising_run)

    payload = changed_files_module.changed_files()

    assert payload == {
        "files": [],
        "source_status": "unavailable",
    }
