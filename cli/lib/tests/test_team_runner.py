import json
import py_compile
import sys
from pathlib import Path

import pytest


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


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_parse_team_yaml_extracts_members_and_strips_quotes() -> None:
    parsed = team_runner._parse_team_yaml(_team_definition(strategy="parallel"))

    assert parsed["name"] == "QA Team"
    assert parsed["strategy"] == "parallel"
    assert parsed["members"][0]["role"] == "qa"
    assert parsed["members"][0]["thinking"] == "high"
    assert parsed["members"][1]["engine"] == "claude"


def test_run_member_codex_invokes_cli_with_project_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class _Result:
        returncode = 0
        stdout = "line1\nline2\n"
        stderr = ""

    def fake_run(cmd: list[str], capture_output: bool, text: bool, env: dict[str, str]) -> _Result:
        captured["cmd"] = cmd
        captured["capture_output"] = capture_output
        captured["text"] = text
        captured["env"] = env
        return _Result()

    monkeypatch.setattr(team_runner.subprocess, "run", fake_run)

    result = team_runner.run_member(
        {"role": "qa", "task": "verify", "engine": "codex", "thinking": "deep"},
        str(tmp_path),
        "/helix-home",
    )

    assert captured["cmd"] == [
        "/helix-home/cli/helix-codex",
        "--role",
        "qa",
        "--task",
        "verify",
        "--thinking",
        "deep",
    ]
    assert captured["capture_output"] is True
    assert captured["text"] is True
    assert captured["env"]["HELIX_PROJECT_ROOT"] == str(tmp_path)
    assert result["status"] == "completed"
    assert result["output"] == "line1\nline2"


def test_run_sequential_stops_after_first_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
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

    monkeypatch.setattr(team_runner, "run_member", fake_run_member)

    results = team_runner.run_sequential(
        [{"role": "qa"}, {"role": "docs"}],
        "/project",
        "/helix",
    )
    output = capsys.readouterr().out

    assert calls == ["qa"]
    assert len(results) == 1
    assert "チーム実行を中断" in output


def test_run_parallel_collects_claude_and_codex_members(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run_member(member: dict[str, str], _project_root: str, _helix_home: str) -> dict[str, object]:
        return {
            "role": member["role"],
            "engine": "codex",
            "exit_code": 0,
            "status": "completed",
            "output": f"done:{member['role']}",
        }

    monkeypatch.setattr(team_runner, "run_member", fake_run_member)

    results = team_runner.run_parallel(
        [
            {"role": "qa", "engine": "codex", "task": "verify"},
            {"role": "docs", "engine": "claude", "task": "summarize"},
        ],
        "/project",
        "/helix",
    )
    output = capsys.readouterr().out

    assert "Claude sub-agent" in output
    assert any(item["engine"] == "claude" and item["status"] == "delegated" for item in results)
    assert any(item["role"] == "qa" and item["status"] == "completed" for item in results)


def test_main_writes_team_status_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    definition_path = tmp_path / "team.yaml"
    definition_path.write_text(_team_definition(strategy="sequential"), encoding="utf-8")

    monkeypatch.setattr(
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
    )
    monkeypatch.setattr(
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
    )

    team_runner.main()

    status_path = tmp_path / ".helix" / "team-status.json"
    payload = json.loads(status_path.read_text(encoding="utf-8"))
    assert payload["name"] == "QA Team"
    assert payload["strategy"] == "sequential"
    assert payload["members"][0]["status"] == "completed"
