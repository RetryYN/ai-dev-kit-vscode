from __future__ import annotations

import subprocess
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import push_gate


def _completed(args: list[str], returncode: int, *, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=args, returncode=returncode, stdout=stdout, stderr=stderr)


def test_run_gate_tests_returns_pass_when_pytest_succeeds(monkeypatch) -> None:
    calls: list[list[str]] = []
    repo_root = push_gate.Path("/tmp/repo")
    tests_dir = repo_root / "cli" / "tests"

    def fake_run(command: list[str], *, cwd=None):  # type: ignore[no-untyped-def]
        calls.append(command)
        if command[:3] == ["python3", "-m", "pytest"]:
            return _completed(command, 0, stdout="1147 passed in 1.23s\n")
        return _completed(command, 0, stdout="1..452\n")

    monkeypatch.setattr(push_gate, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(push_gate, "_run_command", fake_run)
    monkeypatch.setattr(push_gate.Path, "glob", lambda self, pattern: [tests_dir / "sample.bats"])

    result = push_gate.run_gate_tests()

    assert result["passed"] is True
    assert result["detail"] == "pytest 1147 + bats 452"
    assert calls == [push_gate.PYTEST_TESTS_CMD, ["bats", "cli/tests/sample.bats"]]


def test_run_gate_attr_detects_missing_coauthor(monkeypatch) -> None:
    def fake_run(command: list[str], *, cwd=None):  # type: ignore[no-untyped-def]
        if command[:3] == ["git", "rev-list", "--count"]:
            return _completed(command, 0, stdout="2\n")
        if command[:3] == ["git", "log", "origin/main..HEAD"]:
            return _completed(command, 0, stdout="abc123\n")
        raise AssertionError(command)

    monkeypatch.setattr(push_gate, "_repo_root", lambda: push_gate.Path("/tmp/repo"))
    monkeypatch.setattr(push_gate, "_run_command", fake_run)

    result = push_gate.run_gate_attr()

    assert result["passed"] is False
    assert result["detail"] == "2 commits / 1 with Co-Authored-By"
    assert "amend or rebase -i" in result["fix"]


def test_run_gate_nondestructive_detects_drop_table(monkeypatch) -> None:
    diff = """diff --git a/schema.sql b/schema.sql
+DROP TABLE users;
"""

    monkeypatch.setattr(push_gate, "_repo_root", lambda: push_gate.Path("/tmp/repo"))
    monkeypatch.setattr(
        push_gate,
        "_run_command",
        lambda command, *, cwd=None: _completed(command, 0, stdout=diff),
    )

    result = push_gate.run_gate_nondestructive()

    assert result["passed"] is False
    assert result["detail"] == "destructive pattern: DROP TABLE in schema.sql"


def test_run_gate_nondestructive_ignores_destructive_pattern_in_test_code(monkeypatch) -> None:
    monkeypatch.setattr(push_gate, "_repo_root", lambda: push_gate.Path("/tmp/repo"))
    for path in ("cli/lib/tests/test_fixture.py", "cli/tests/push.bats", "tests/test_fixture.py"):
        diff = f"""diff --git a/{path} b/{path}
+fixture_sql = "DROP TABLE users"
"""
        monkeypatch.setattr(
            push_gate,
            "_run_command",
            lambda command, *, cwd=None, stdout=diff: _completed(command, 0, stdout=stdout),
        )

        result = push_gate.run_gate_nondestructive()

        assert result["passed"] is True
        assert result["detail"] == "no destructive pattern"


def test_run_gate_nondestructive_ignores_destructive_pattern_in_docs(monkeypatch) -> None:
    diff = """diff --git a/docs/push.md b/docs/push.md
+Use DROP TABLE only as an example in this document.
"""

    monkeypatch.setattr(push_gate, "_repo_root", lambda: push_gate.Path("/tmp/repo"))
    monkeypatch.setattr(
        push_gate,
        "_run_command",
        lambda command, *, cwd=None: _completed(command, 0, stdout=diff),
    )

    result = push_gate.run_gate_nondestructive()

    assert result["passed"] is True
    assert result["detail"] == "no destructive pattern"


def test_run_gate_nondestructive_ignores_destructive_pattern_in_rollback_sql(monkeypatch) -> None:
    diff = """diff --git a/cli/migrations/rollback/001_drop_users.sql b/cli/migrations/rollback/001_drop_users.sql
+DROP TABLE users;
"""

    monkeypatch.setattr(push_gate, "_repo_root", lambda: push_gate.Path("/tmp/repo"))
    monkeypatch.setattr(
        push_gate,
        "_run_command",
        lambda command, *, cwd=None: _completed(command, 0, stdout=diff),
    )

    result = push_gate.run_gate_nondestructive()

    assert result["passed"] is True
    assert result["detail"] == "no destructive pattern"


def test_run_gate_nondestructive_detects_destructive_pattern_in_implementation_code(monkeypatch) -> None:
    diff = """diff --git a/cli/lib/helix_db.py b/cli/lib/helix_db.py
+sql = "DROP TABLE temp_users"
"""

    monkeypatch.setattr(push_gate, "_repo_root", lambda: push_gate.Path("/tmp/repo"))
    monkeypatch.setattr(
        push_gate,
        "_run_command",
        lambda command, *, cwd=None: _completed(command, 0, stdout=diff),
    )

    result = push_gate.run_gate_nondestructive()

    assert result["passed"] is False
    assert result["detail"] == "destructive pattern: DROP TABLE in cli/lib/helix_db.py"


def test_run_gate_ff_detects_diverged_branch(monkeypatch) -> None:
    def fake_run(command: list[str], *, cwd=None):  # type: ignore[no-untyped-def]
        if command[:2] == ["git", "fetch"]:
            return _completed(command, 0)
        if command[:3] == ["git", "merge-base", "--is-ancestor"]:
            return _completed(command, 1)
        raise AssertionError(command)

    monkeypatch.setattr(push_gate, "_repo_root", lambda: push_gate.Path("/tmp/repo"))
    monkeypatch.setattr(push_gate, "_run_command", fake_run)

    result = push_gate.run_gate_ff()

    assert result["passed"] is False
    assert result["detail"] == "origin/main is not an ancestor of HEAD"
