"""PLAN-083 Phase 4: session_helper 単体テスト."""

from __future__ import annotations

import json
import os
import re
import subprocess

import pytest

from cli.lib import session_helper


def _run_module(args: list[str], env: dict[str, str], cwd: str | os.PathLike[str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "-m", "cli.lib.session_helper", *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
    )


class TestDetectSessionId:
    def test_helix_session_id_priority_1(self, monkeypatch):
        monkeypatch.setenv("HELIX_SESSION_ID", "helix-abc")
        monkeypatch.setenv("CLAUDE_SESSION_ID", "claude-xyz")
        assert session_helper.detect_session_id() == "helix-abc"

    def test_claude_session_id_fallback(self, monkeypatch):
        monkeypatch.delenv("HELIX_SESSION_ID", raising=False)
        monkeypatch.setenv("CLAUDE_SESSION_ID", "claude-xyz")
        assert session_helper.detect_session_id() == "claude-xyz"

    def test_helix_empty_falls_back_to_claude(self, monkeypatch):
        monkeypatch.setenv("HELIX_SESSION_ID", "  ")
        monkeypatch.setenv("CLAUDE_SESSION_ID", "claude-xyz")
        assert session_helper.detect_session_id() == "claude-xyz"

    def test_infer_from_tmp_path(self, monkeypatch):
        for key in ("HELIX_SESSION_ID", "CLAUDE_SESSION_ID", "CLAUDE_TASK_OUTPUT_DIR", "CLAUDE_PROJECT_DIR"):
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv(
            "CLAUDE_TASK_OUTPUT_DIR",
            "/tmp/claude-1001/-foo-bar/abcd1234-5678-90ab-cdef-1234567890ab/tasks",
        )
        assert session_helper.detect_session_id() == "abcd1234"

    def test_infer_from_project_dir(self, monkeypatch):
        for key in ("HELIX_SESSION_ID", "CLAUDE_SESSION_ID", "CLAUDE_TASK_OUTPUT_DIR", "CLAUDE_PROJECT_DIR"):
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/tmp/claude-7/a/11223344-5566-7788-99aa-bbccddeeff00")
        assert session_helper.detect_session_id() == "11223344"

    def test_uuid_fallback_when_no_env(self, monkeypatch):
        for k in ("HELIX_SESSION_ID", "CLAUDE_SESSION_ID", "CLAUDE_TASK_OUTPUT_DIR", "CLAUDE_PROJECT_DIR"):
            monkeypatch.delenv(k, raising=False)
        result = session_helper.detect_session_id()
        assert result.startswith("unknown-")
        assert len(result) == len("unknown-") + 8

    def test_priority_order_helix_first(self, monkeypatch):
        monkeypatch.setenv("HELIX_SESSION_ID", "h1")
        monkeypatch.setenv("CLAUDE_SESSION_ID", "c1")
        monkeypatch.setenv(
            "CLAUDE_TASK_OUTPUT_DIR",
            "/tmp/claude-1/-foo/aaaa1111-bbbb-2222-cccc-3333dddd4444/x",
        
        )
        assert session_helper.detect_session_id() == "h1"

    def test_invalid_tmp_path_falls_back_to_uuid(self, monkeypatch):
        for k in ("HELIX_SESSION_ID", "CLAUDE_SESSION_ID"):
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setenv("CLAUDE_TASK_OUTPUT_DIR", "/var/log/foo")
        result = session_helper.detect_session_id()
        assert result.startswith("unknown-")


class TestGetSessionMeta:
    def test_meta_includes_detected_id(self, monkeypatch):
        monkeypatch.setenv("HELIX_SESSION_ID", "helix-meta")
        meta = session_helper.get_session_meta()
        assert meta["detected"] == "helix-meta"
        assert meta["helix_session_id"] == "helix-meta"

    def test_meta_none_when_env_missing(self, monkeypatch):
        for k in ("HELIX_SESSION_ID", "CLAUDE_SESSION_ID", "CLAUDE_TASK_OUTPUT_DIR", "CLAUDE_PROJECT_DIR"):
            monkeypatch.delenv(k, raising=False)
        meta = session_helper.get_session_meta()
        assert meta["helix_session_id"] is None
        assert meta["claude_session_id"] is None
        assert meta["detected"].startswith("unknown-")


class TestCliEntry:
    def test_main_prints_detected_id(self, monkeypatch, tmp_path):
        env = {
            **os.environ,
            "HELIX_SESSION_ID": "cli-test",
            "PYTHONPATH": os.getcwd(),
        }
        result = _run_module([], env=env, cwd=str(tmp_path))
        assert result.returncode == 0
        assert "cli-test" in result.stdout

    def test_main_meta_prints_json(self, monkeypatch, tmp_path):
        env = {
            **os.environ,
            "HELIX_SESSION_ID": "meta-test",
            "PYTHONPATH": os.getcwd(),
        }
        result = _run_module(["--meta"], env=env, cwd=str(tmp_path))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["detected"] == "meta-test"


class TestInferPattern:
    @pytest.mark.parametrize(
        "path,expected",
        [
            ("/tmp/claude-1001/proj/abcd1234-5678-90ab-cdef-1234567890ab", "abcd1234"),
            ("/tmp/claude-10/x/a1b2c3d4-1111-2222-3333-444455556666", "a1b2c3d4"),
        ],
    )
    def test_regex_extract_prefix(self, path: str, expected: str):
        match = re.search(r"/tmp/claude-\d+/[^/]+/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})", path)
        assert match
        assert match.group(1)[:8] == expected
