import json
import py_compile
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import context_guard


MODULE_PATH = LIB_DIR / "context_guard.py"


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def _write_project_context_files(root: Path) -> None:
    for rel in context_guard.PROJECT_CONTEXT_FILES:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# test\n", encoding="utf-8")


def _write_framework_context_files(root: Path) -> None:
    for rel in context_guard.FRAMEWORK_CONTEXT_FILES:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# test\n", encoding="utf-8")


def _write_required_files(root: Path) -> None:
    _write_project_context_files(root)
    _write_framework_context_files(root)


def _write_settings(root: Path, include_bash_guard: bool = True, bash_guard_blocks: bool = True) -> None:
    pretool = [
        {
            "matcher": "Write",
            "hooks": [{"command": "~/ai-dev-kit-vscode/cli/helix-check-claudemd"}],
        }
    ]
    if include_bash_guard:
        pretool.append(
            {
                "matcher": "Bash",
                "hooks": [
                    {
                        "command": "~/ai-dev-kit-vscode/cli/libexec/helix-pre-bash",
                        "blockOnFailure": bash_guard_blocks,
                    }
                ],
            }
        )
    pretool.append(
        {
            "matcher": "WebSearch|WebFetch",
            "hooks": [
                {
                    "command": "~/ai-dev-kit-vscode/cli/libexec/helix-pre-research",
                    "blockOnFailure": True,
                }
            ],
        }
    )
    payload = {
        "hooks": {
            "SessionStart": [{"hooks": [{"command": "~/ai-dev-kit-vscode/cli/helix-session-start"}]}],
            "PreToolUse": pretool,
            "PostToolUse": [
                {
                    "matcher": "Edit|Write|MultiEdit",
                    "hooks": [{"command": "~/ai-dev-kit-vscode/cli/libexec/helix-post-tool-use"}],
                }
            ],
            "Stop": [{"hooks": [{"command": "~/ai-dev-kit-vscode/cli/helix-session-summary"}]}],
        }
    }
    settings = root / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(json.dumps(payload), encoding="utf-8")


def test_check_context_fails_when_bash_guard_missing(tmp_path: Path) -> None:
    _write_required_files(tmp_path)
    _write_settings(tmp_path, include_bash_guard=False)
    (tmp_path / "docs" / "memory").mkdir(parents=True)

    payload = context_guard.check_context(tmp_path)

    assert payload["ok"] is False
    assert any(item["code"] == "missing_hook" and "helix-pre-bash" in item["message"] for item in payload["errors"])


def test_check_context_fails_when_research_tool_guard_missing(tmp_path: Path) -> None:
    _write_required_files(tmp_path)
    _write_settings(tmp_path)
    (tmp_path / "docs" / "memory").mkdir(parents=True)
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    settings["hooks"]["PreToolUse"] = [
        entry for entry in settings["hooks"]["PreToolUse"] if entry.get("matcher") != "WebSearch|WebFetch"
    ]
    (tmp_path / ".claude" / "settings.json").write_text(json.dumps(settings), encoding="utf-8")

    payload = context_guard.check_context(tmp_path)

    assert payload["ok"] is False
    assert any(item["code"] == "missing_hook" and "helix-pre-research" in item["message"] for item in payload["errors"])


def test_check_context_passes_with_required_files_and_hooks(tmp_path: Path) -> None:
    _write_required_files(tmp_path)
    _write_settings(tmp_path)
    (tmp_path / "docs" / "memory").mkdir(parents=True)

    payload = context_guard.check_context(tmp_path)

    assert payload["ok"] is True
    assert payload["summary"]["error"] == 0
    assert any(item["code"] == "missing_project_memory" for item in payload["warnings"])


def test_check_context_external_project_uses_helix_home_and_user_hooks(monkeypatch, tmp_path: Path) -> None:
    framework_root = tmp_path / "framework"
    project_root = tmp_path / "project"
    home = tmp_path / "home"
    _write_framework_context_files(framework_root)
    _write_project_context_files(project_root)
    _write_settings(home)
    (project_root / "docs" / "memory").mkdir(parents=True)
    monkeypatch.setenv("HELIX_HOME", str(framework_root))
    monkeypatch.setenv("HOME", str(home))

    payload = context_guard.check_context(project_root)

    assert payload["ok"] is True
    assert payload["framework_root"] == str(framework_root.resolve())
    assert payload["settings_scope"] == "user"
    assert not any("framework context file missing" in item["message"] for item in payload["errors"])


def test_check_context_rejects_invalid_project_settings_before_user_fallback(monkeypatch, tmp_path: Path) -> None:
    framework_root = tmp_path / "framework"
    project_root = tmp_path / "project"
    home = tmp_path / "home"
    _write_framework_context_files(framework_root)
    _write_project_context_files(project_root)
    _write_settings(home)
    (project_root / "docs" / "memory").mkdir(parents=True)
    project_settings = project_root / ".claude" / "settings.json"
    project_settings.parent.mkdir(parents=True, exist_ok=True)
    project_settings.write_text("{bad", encoding="utf-8")
    monkeypatch.setenv("HELIX_HOME", str(framework_root))
    monkeypatch.setenv("HOME", str(home))

    payload = context_guard.check_context(project_root)

    assert payload["ok"] is False
    assert payload["settings_scope"] == "project"
    assert any(item["code"] == "invalid_project_settings" for item in payload["errors"])


def test_check_context_uses_installed_cli_when_project_cli_is_absent(tmp_path: Path) -> None:
    _write_required_files(tmp_path)
    _write_settings(tmp_path)
    (tmp_path / "docs" / "memory").mkdir(parents=True)
    (tmp_path / "helix" / "HELIX_CORE.md").write_text("helix code find --bucket\n", encoding="utf-8")

    payload = context_guard.check_context(tmp_path)

    assert payload["ok"] is True


def test_check_context_fails_when_bash_guard_is_non_blocking(tmp_path: Path) -> None:
    _write_required_files(tmp_path)
    _write_settings(tmp_path, bash_guard_blocks=False)
    (tmp_path / "docs" / "memory").mkdir(parents=True)

    payload = context_guard.check_context(tmp_path)

    assert payload["ok"] is False
    assert any(item["code"] == "non_blocking_hook" for item in payload["errors"])


def test_check_context_fails_when_research_guard_is_non_blocking(tmp_path: Path) -> None:
    _write_required_files(tmp_path)
    _write_settings(tmp_path)
    (tmp_path / "docs" / "memory").mkdir(parents=True)
    settings_path = tmp_path / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    for entry in settings["hooks"]["PreToolUse"]:
        if entry.get("matcher") == "WebSearch|WebFetch":
            for hook in entry["hooks"]:
                hook["blockOnFailure"] = False
    settings_path.write_text(json.dumps(settings), encoding="utf-8")

    payload = context_guard.check_context(tmp_path)

    assert payload["ok"] is False
    assert any(
        item["code"] == "non_blocking_hook" and "helix-pre-research" in item["message"]
        for item in payload["errors"]
    )


def test_context_bundle_is_compact(tmp_path: Path) -> None:
    _write_required_files(tmp_path)
    _write_settings(tmp_path)

    text = context_guard.context_bundle(tmp_path)

    assert "HELIX Context Guard" in text
    assert "- ok:" in text


def test_main_defaults_to_check_without_subcommand(monkeypatch, capsys, tmp_path: Path) -> None:
    _write_required_files(tmp_path)
    _write_settings(tmp_path)
    (tmp_path / "docs" / "memory").mkdir(parents=True)

    monkeypatch.setattr(sys, "argv", ["helix context", "--root", str(tmp_path)])

    assert context_guard.main() == 0
    assert "HELIX Context Guard" in capsys.readouterr().out


def test_check_context_reports_guarded_local_raw_codex_allow_as_info(tmp_path: Path) -> None:
    _write_required_files(tmp_path)
    _write_settings(tmp_path)
    (tmp_path / "docs" / "memory").mkdir(parents=True)
    (tmp_path / ".claude" / "memory").mkdir(parents=True)
    local_settings = tmp_path / ".claude" / "settings.local.json"
    local_settings.write_text(
        json.dumps(
            {
                "permissions": {
                    "allow": [
                        "Bash(codex exec:*)",
                        "Bash($HOME/.npm-global/bin/codex exec:*)",
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    payload = context_guard.check_context(tmp_path)

    assert payload["ok"] is True
    assert not any(item["code"] == "local_raw_codex_allow" for item in payload["warnings"])
    assert any(item["code"] == "local_raw_codex_allow_guarded" for item in payload["infos"])


def test_check_context_warns_for_unprotected_local_raw_codex_allow(tmp_path: Path) -> None:
    _write_required_files(tmp_path)
    _write_settings(tmp_path, bash_guard_blocks=False)
    (tmp_path / "docs" / "memory").mkdir(parents=True)
    (tmp_path / ".claude" / "memory").mkdir(parents=True)
    local_settings = tmp_path / ".claude" / "settings.local.json"
    local_settings.write_text(
        json.dumps({"permissions": {"allow": ["Bash(codex exec:*)"]}}),
        encoding="utf-8",
    )

    payload = context_guard.check_context(tmp_path)

    assert payload["ok"] is False
    assert any(item["code"] == "non_blocking_hook" for item in payload["errors"])
    assert any(item["code"] == "local_raw_codex_allow" for item in payload["warnings"])


def test_check_context_rejects_stale_team_command_docs(tmp_path: Path) -> None:
    _write_required_files(tmp_path)
    _write_settings(tmp_path)
    (tmp_path / "docs" / "memory").mkdir(parents=True)
    (tmp_path / "AGENTS.md").write_text("use helix team <team> --task now\n", encoding="utf-8")

    payload = context_guard.check_context(tmp_path)

    assert payload["ok"] is False
    assert any(item["code"] == "stale_team_command_doc" for item in payload["errors"])
