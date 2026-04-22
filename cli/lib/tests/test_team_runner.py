import io
import json
import py_compile
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import team_runner


MODULE_PATH = LIB_DIR / "team_runner.py"


def _team_definition(strategy: str = "sequential") -> str:
    return (
        'name: "QA Team"\n'
        f'strategy: "{strategy}"\n'
        "members:\n"
        '  - role: "qa"\n'
        '    task: "verify regression"\n'
        '    engine: "codex"\n'
        '    thinking: "high"\n'
        "  - role: docs\n"
        "    task: summarize\n"
        "    engine: claude\n"
    )


class TeamRunnerTest(unittest.TestCase):
    def test_module_py_compile(self) -> None:
        py_compile.compile(str(MODULE_PATH), doraise=True)

    def test_parse_team_yaml_extracts_members_and_strips_quotes(self) -> None:
        parsed = team_runner._parse_team_yaml(_team_definition(strategy="parallel"))

        self.assertEqual(parsed["name"], "QA Team")
        self.assertEqual(parsed["strategy"], "parallel")
        self.assertEqual(parsed["members"][0]["role"], "qa")
        self.assertEqual(parsed["members"][0]["thinking"], "high")
        self.assertEqual(parsed["members"][1]["engine"], "claude")

    def test_run_member_codex_invokes_cli_with_project_env(self) -> None:
        captured: dict[str, object] = {}

        class _Result:
            returncode = 0
            stdout = "line1\nline2\n"
            stderr = ""

        def fake_run(
            cmd: list[str],
            capture_output: bool,
            text: bool,
            env: dict[str, str],
            timeout: int,
        ) -> _Result:
            captured["cmd"] = cmd
            captured["capture_output"] = capture_output
            captured["text"] = text
            captured["env"] = env
            captured["timeout"] = timeout
            return _Result()

        with tempfile.TemporaryDirectory() as td:
            with patch.object(team_runner.subprocess, "run", side_effect=fake_run):
                result = team_runner.run_member(
                    {"role": "qa", "task": "verify", "engine": "codex", "thinking": "deep"},
                    td,
                    "/helix-home",
                )

        self.assertEqual(
            captured["cmd"],
            [
                "/helix-home/cli/helix-codex",
                "--role",
                "qa",
                "--task",
                "verify",
                "--thinking",
                "deep",
            ],
        )
        self.assertIs(captured["capture_output"], True)
        self.assertIs(captured["text"], True)
        self.assertEqual(captured["timeout"], 1800)
        self.assertEqual(captured["env"]["HELIX_PROJECT_ROOT"], td)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["output"], "line1\nline2")

    def test_run_member_codex_timeout_returns_timeout_status(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            helix_home = tmp_path / "helix-home"
            bin_path = helix_home / "cli" / "helix-codex"
            bin_path.parent.mkdir(parents=True, exist_ok=True)
            bin_path.write_text("#!/usr/bin/env bash\nsleep 5\nexit 0\n", encoding="utf-8")
            bin_path.chmod(0o755)

            result = team_runner.run_member(
                {"role": "qa", "task": "verify", "engine": "codex"},
                str(tmp_path),
                str(helix_home),
                timeout=2,
            )

        self.assertEqual(result["exit_code"], 124)
        self.assertEqual(result["status"], "timeout")

    def test_run_sequential_stops_after_first_failure(self) -> None:
        calls: list[str] = []

        def fake_run_member(member: dict[str, str], _project_root: str, _helix_home: str) -> dict[str, object]:
            calls.append(member["role"])
            return {
                "role": member["role"],
                "engine": member.get("engine", "codex"),
                "exit_code": 1,
                "status": "failed",
                "output": "boom",
            }

        buf = io.StringIO()
        with patch.object(team_runner, "run_member", side_effect=fake_run_member):
            with redirect_stdout(buf):
                results = team_runner.run_sequential(
                    [{"role": "qa"}, {"role": "docs"}],
                    "/project",
                    "/helix",
                )
        output = buf.getvalue()

        self.assertEqual(calls, ["qa"])
        self.assertEqual(len(results), 1)
        self.assertIn("チーム実行を中断", output)

    def test_run_parallel_collects_claude_and_codex_members(self) -> None:
        def fake_run_member(member: dict[str, str], _project_root: str, _helix_home: str) -> dict[str, object]:
            return {
                "role": member["role"],
                "engine": "codex",
                "exit_code": 0,
                "status": "completed",
                "output": f"done:{member['role']}",
            }

        buf = io.StringIO()
        with patch.object(team_runner, "run_member", side_effect=fake_run_member):
            with redirect_stdout(buf):
                results = team_runner.run_parallel(
                    [
                        {"role": "qa", "engine": "codex", "task": "verify"},
                        {"role": "docs", "engine": "claude", "task": "summarize"},
                    ],
                    "/project",
                    "/helix",
                )
        output = buf.getvalue()

        self.assertIn("Claude sub-agent", output)
        self.assertTrue(any(item["engine"] == "claude" and item["status"] == "delegated" for item in results))
        self.assertTrue(any(item["role"] == "qa" and item["status"] == "completed" for item in results))

    def test_main_writes_team_status_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            definition_path = tmp_path / "team.yaml"
            definition_path.write_text(_team_definition(strategy="sequential"), encoding="utf-8")

            with patch.object(
                team_runner,
                "run_sequential",
                lambda members, project_root, helix_home: [
                    {
                        "role": members[0]["role"],
                        "engine": members[0]["engine"],
                        "exit_code": 0,
                        "status": "completed",
                        "output": "ok",
                    }
                ],
            ):
                with patch.object(
                    sys,
                    "argv",
                    [
                        "team_runner.py",
                        "--definition",
                        str(definition_path),
                        "--project-root",
                        str(tmp_path),
                        "--helix-home",
                        "/helix-home",
                    ],
                ):
                    with redirect_stdout(io.StringIO()):
                        team_runner.main()

            status_path = tmp_path / ".helix" / "team-status.json"
            payload = json.loads(status_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["name"], "QA Team")
            self.assertEqual(payload["strategy"], "sequential")
            self.assertEqual(payload["members"][0]["status"], "completed")


if __name__ == "__main__":
    unittest.main()
