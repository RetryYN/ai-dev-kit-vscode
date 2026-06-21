import copy
import json
import py_compile
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import merge_settings


MODULE_PATH = LIB_DIR / "merge_settings.py"


def _first_hook_command(hooks: dict, event: str) -> str:
    return hooks[event][0]["hooks"][0]["command"]


def _hook_commands(entry: dict) -> list[str]:
    return [hook["command"] for hook in entry.get("hooks", [])]


def _post_tool_entry(entries: list[dict], command_suffix: str) -> dict:
    for entry in entries:
        commands = _hook_commands(entry)
        if any(command.endswith(command_suffix) for command in commands):
            return entry
    raise AssertionError(f"PostToolUse entry not found: {command_suffix}")


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_merge_adds_helix_hooks_once() -> None:
    settings = {"hooks": {"SessionStart": [{"hooks": [{"command": "custom-start"}]}]}}

    changed = merge_settings.merge(settings)
    changed_again = merge_settings.merge(settings)

    assert changed is True
    assert changed_again is False
    assert len(settings["hooks"]["SessionStart"]) == 2
    assert "PreToolUse" in settings["hooks"]


def test_remove_keeps_non_helix_hooks_and_cleans_empty_events() -> None:
    settings = {
        "hooks": {
            "SessionStart": [
                {"hooks": [{"command": "~/ai-dev-kit-vscode/cli/helix-session-start"}]},
                {"hooks": [{"command": "custom-start"}]},
            ],
            "Stop": [
                {"hooks": [{"command": "~/ai-dev-kit-vscode/cli/helix-session-summary"}]},
            ],
        }
    }

    changed = merge_settings.remove(settings)

    assert changed is True
    assert settings["hooks"]["SessionStart"] == [{"hooks": [{"command": "custom-start"}]}]
    assert "Stop" not in settings["hooks"]


def test_main_writes_settings_file_and_exits_zero_when_changed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings_path = tmp_path / "settings.json"
    monkeypatch.setattr(sys, "argv", ["merge_settings.py", str(settings_path)])

    with pytest.raises(SystemExit) as exc:
        merge_settings.main()

    assert exc.value.code == 0
    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "hooks" in payload
    assert "SessionStart" in payload["hooks"]


def test_main_exits_one_when_no_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps({"hooks": copy.deepcopy(merge_settings.HELIX_HOOKS)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "argv", ["merge_settings.py", str(settings_path)])

    with pytest.raises(SystemExit) as exc:
        merge_settings.main()

    assert exc.value.code == 1


def test_main_exits_three_when_settings_json_is_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text("{bad", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["merge_settings.py", str(settings_path)])

    with pytest.raises(SystemExit) as exc:
        merge_settings.main()

    assert exc.value.code == 3
    assert "設定マージに失敗" in capsys.readouterr().err


def test_post_tool_use_hook_preserves_fail_close_behavior(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # PLAN-223: session fixture が HELIX_HOME=worker_base に固定するため、
    # REPO_ROOT を期待する _resolve_helix_home() default に戻す
    monkeypatch.delenv("HELIX_HOME", raising=False)
    entry = merge_settings.HELIX_HOOKS["PostToolUse"][0]
    hook = merge_settings.HELIX_HOOKS["PostToolUse"][0]["hooks"][0]
    command = hook["command"]

    assert "|| true" not in command
    assert command == str(
        Path(merge_settings._resolve_helix_home()) / "cli" / "libexec" / "helix-post-tool-use"
    )
    assert entry["matcher"] == "Edit|Write|MultiEdit"
    assert hook["blockOnFailure"] is True


def test_post_tool_use_code_catalog_register_hook_is_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HELIX_HOME", raising=False)
    entry = merge_settings.HELIX_HOOKS["PostToolUse"][1]
    hook = entry["hooks"][0]

    assert entry["matcher"] == "Edit|Write|MultiEdit"
    assert entry["continueOnBlock"] is True
    assert hook["command"] == str(
        Path(merge_settings._resolve_helix_home()) / ".claude" / "hooks" / "posttooluse-code-catalog-register.sh"
    )
    assert hook["blockOnFailure"] is False
    assert hook["timeout"] == 10


def test_pre_tool_use_bash_guard_is_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HELIX_HOME", raising=False)
    entries = merge_settings.HELIX_HOOKS["PreToolUse"]
    bash_entries = [entry for entry in entries if entry.get("matcher") == "Bash"]

    assert len(bash_entries) == 1
    hook = bash_entries[0]["hooks"][0]
    assert hook["command"] == str(
        Path(merge_settings._resolve_helix_home()) / "cli" / "libexec" / "helix-pre-bash"
    )
    assert hook["blockOnFailure"] is True


def test_pre_tool_use_research_guard_is_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HELIX_HOME", raising=False)
    entries = merge_settings.HELIX_HOOKS["PreToolUse"]
    research_entries = [entry for entry in entries if entry.get("matcher") == "WebSearch|WebFetch"]

    assert len(research_entries) == 1
    hook = research_entries[0]["hooks"][0]
    assert hook["command"] == str(
        Path(merge_settings._resolve_helix_home()) / "cli" / "libexec" / "helix-pre-research"
    )
    assert hook["blockOnFailure"] is True


def test_build_hooks_uses_default_helix_home_when_env_is_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HELIX_HOME", raising=False)

    hooks = merge_settings._build_hooks()
    command = _first_hook_command(hooks, "SessionStart")

    assert command == str(
        Path.home() / "ai-dev-kit-vscode" / "cli" / "helix-session-start"
    )
    assert Path(command).is_absolute()


def test_build_hooks_uses_helix_home_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HELIX_HOME", "/tmp/x")

    hooks = merge_settings._build_hooks()

    assert _first_hook_command(hooks, "SessionStart") == "/tmp/x/cli/helix-session-start"
    assert (
        _first_hook_command(hooks, "PostToolUse")
        == "/tmp/x/cli/libexec/helix-post-tool-use"
    )


def test_build_hooks_expands_tilde_in_helix_home(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HELIX_HOME", "~/foo")

    hooks = merge_settings._build_hooks()

    assert _first_hook_command(hooks, "Stop") == str(
        Path.home() / "foo" / "cli" / "helix-session-summary"
    )


def test_merge_replaces_stale_helix_hook_with_canonical() -> None:
    stale_registered_command = "~/ai-dev-kit-vscode/cli/libexec/helix-post-tool-use"
    settings = {
        "hooks": {
            "PostToolUse": [
                {"hooks": [{"command": "custom-post"}]},
                {
                    "matcher": "Edit|Write",
                    "hooks": [{"command": stale_registered_command}],
                },
            ]
        }
    }

    changed = merge_settings.merge(settings)

    assert changed is True
    assert settings["hooks"]["PostToolUse"] == [
        {"hooks": [{"command": "custom-post"}]},
        merge_settings.HELIX_HOOKS["PostToolUse"][0],
        merge_settings.HELIX_HOOKS["PostToolUse"][1],
    ]


def test_is_helix_hook_rejects_external_command_with_helix_in_name() -> None:
    entry = {"hooks": [{"command": "/usr/local/bin/some-helix-tool"}]}

    assert merge_settings._is_helix_hook(entry) is False


def test_is_helix_hook_rejects_unregistered_command_under_helix_home() -> None:
    command = str(Path(merge_settings._resolve_helix_home()) / "cli" / "libexec" / "helix-future-hook")
    entry = {"hooks": [{"command": command}]}

    assert merge_settings._is_helix_hook(entry) is False


def test_is_helix_hook_accepts_registered_command_with_tilde_path() -> None:
    entry = {"hooks": [{"command": "~/ai-dev-kit-vscode/cli/helix-session-start"}]}

    assert merge_settings._is_helix_hook(entry) is True


def test_merge_settings_for_migrate_returns_merged_copy() -> None:
    current = {
        "hooks": {
            "Stop": [
                {"hooks": [{"command": "custom-stop"}]},
            ]
        }
    }

    merged = merge_settings.merge_settings_for_migrate(current, merge_settings.HELIX_HOOKS)

    assert merged is not current
    assert current == {"hooks": {"Stop": [{"hooks": [{"command": "custom-stop"}]}]}}
    assert merged["hooks"]["Stop"][0] == {"hooks": [{"command": "custom-stop"}]}
    assert merged["hooks"]["Stop"][1] == merge_settings.HELIX_HOOKS["Stop"][0]


def test_merge_preserves_custom_sessionstart_history_injection() -> None:
    history_hook = "$CLAUDE_PROJECT_DIR/.claude/hooks/sessionstart-history-injection.sh"
    harness_hook = "$CLAUDE_PROJECT_DIR/.claude/hooks/sessionstart-harness-summary.sh"
    settings = {
        "hooks": {
            "SessionStart": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": "~/ai-dev-kit-vscode/cli/helix-session-start",
                            "timeout": 5,
                            "statusMessage": "Loading HELIX framework...",
                            "blockOnFailure": True,
                        },
                        {
                            "type": "command",
                            "command": history_hook,
                            "timeout": 5,
                            "statusMessage": "Injecting HELIX resume bundle...",
                            "blockOnFailure": False,
                        },
                    ]
                },
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": harness_hook,
                            "timeout": 5,
                            "blockOnFailure": False,
                        }
                    ]
                },
            ]
        }
    }

    changed = merge_settings.merge(settings)

    assert changed is True
    assert _hook_commands(settings["hooks"]["SessionStart"][0]) == [
        merge_settings.HELIX_HOOKS["SessionStart"][0]["hooks"][0]["command"],
        history_hook,
    ]
    assert _hook_commands(settings["hooks"]["SessionStart"][1]) == [harness_hook]


def test_merge_preserves_canonical_helix_session_start_path() -> None:
    settings = {
        "hooks": {
            "SessionStart": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": "~/ai-dev-kit-vscode/cli/helix-session-start",
                        }
                    ]
                }
            ]
        }
    }

    changed = merge_settings.merge(settings)

    assert changed is True
    assert settings["hooks"]["SessionStart"][0]["hooks"][0]["command"] == (
        merge_settings.HELIX_HOOKS["SessionStart"][0]["hooks"][0]["command"]
    )


def test_merge_preserves_design_doc_web_search_revert_first() -> None:
    revert_hook = "$CLAUDE_PROJECT_DIR/.claude/hooks/posttooluse-design-doc-web-search-revert.sh"
    settings = {
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "Edit|Write|MultiEdit",
                    "continueOnBlock": True,
                    "hooks": [
                        {
                            "type": "command",
                            "command": revert_hook,
                            "timeout": 5,
                            "statusMessage": "Checking design-doc revert guard...",
                            "blockOnFailure": False,
                        },
                        {
                            "type": "command",
                            "command": "~/ai-dev-kit-vscode/cli/libexec/helix-post-tool-use",
                            "timeout": 10,
                            "statusMessage": "HELIX design sync check...",
                            "blockOnFailure": True,
                        },
                    ],
                }
            ]
        }
    }

    changed = merge_settings.merge(settings)

    assert changed is True
    assert settings["hooks"]["PostToolUse"][0]["hooks"][0]["command"] == revert_hook
    assert settings["hooks"]["PostToolUse"][0]["hooks"][1]["command"] == (
        merge_settings.HELIX_HOOKS["PostToolUse"][0]["hooks"][0]["command"]
    )
    assert _post_tool_entry(
        settings["hooks"]["PostToolUse"],
        "/.claude/hooks/posttooluse-code-catalog-register.sh",
    ) == merge_settings.HELIX_HOOKS["PostToolUse"][1]


def test_remove_only_helix_hook_preserves_custom() -> None:
    history_hook = "$CLAUDE_PROJECT_DIR/.claude/hooks/sessionstart-history-injection.sh"
    settings = {
        "hooks": {
            "SessionStart": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": "~/ai-dev-kit-vscode/cli/helix-session-start",
                        },
                        {
                            "type": "command",
                            "command": history_hook,
                        },
                    ]
                }
            ]
        }
    }

    changed = merge_settings.remove(settings)

    assert changed is True
    assert settings["hooks"]["SessionStart"] == [{"hooks": [{"type": "command", "command": history_hook}]}]


def test_merge_idempotency() -> None:
    settings = {
        "hooks": {
            "SessionStart": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": "~/ai-dev-kit-vscode/cli/helix-session-start",
                            "timeout": 5,
                            "statusMessage": "Loading HELIX framework...",
                            "blockOnFailure": True,
                        },
                        {
                            "type": "command",
                            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/sessionstart-history-injection.sh",
                            "timeout": 5,
                            "statusMessage": "Injecting HELIX resume bundle...",
                            "blockOnFailure": False,
                        },
                    ]
                }
            ]
        }
    }

    first_changed = merge_settings.merge(settings)
    first_snapshot = json.dumps(settings, ensure_ascii=False, sort_keys=True)
    second_changed = merge_settings.merge(settings)
    second_snapshot = json.dumps(settings, ensure_ascii=False, sort_keys=True)

    assert first_changed is True
    assert second_changed is False
    assert first_snapshot == second_snapshot
