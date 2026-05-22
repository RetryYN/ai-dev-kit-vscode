#!/usr/bin/env python3
"""merge_settings.py — ~/.claude/settings.json に HELIX hooks を安全にマージ/除去する

責務: Claude settings の hook 設定を安全に追加・削除して整合性を保つ。

Usage:
    python3 merge_settings.py <settings.json>            # マージ（追加）
    python3 merge_settings.py <settings.json> --remove   # HELIX hooks を除去
"""

import copy
import json
import os
import sys


def _resolve_helix_home():
    """HELIX_HOME を絶対パスとして解決する。未設定時は self-host 既定値を使う。"""
    raw_home = os.environ.get("HELIX_HOME") or os.path.expanduser("~/ai-dev-kit-vscode")
    return os.path.abspath(os.path.expanduser(raw_home))


def _hook_command(helix_home, relative_path):
    return os.path.join(helix_home, *relative_path.split("/"))


def _build_hooks():
    helix_home = _resolve_helix_home()
    return {
        "SessionStart": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": _hook_command(helix_home, "cli/helix-session-start"),
                        "timeout": 5,
                        "statusMessage": "Loading HELIX framework...",
                        "blockOnFailure": True,
                    }
                ]
            }
        ],
        "PreToolUse": [
            {
                "matcher": "Write",
                "hooks": [
                    {
                        "type": "command",
                        "command": _hook_command(helix_home, "cli/helix-check-claudemd"),
                        "timeout": 5,
                        "statusMessage": "Checking CLAUDE.md template...",
                        "blockOnFailure": True,
                    }
                ]
            },
            {
                "matcher": "Bash",
                "hooks": [
                    {
                        "type": "command",
                        "command": _hook_command(helix_home, "cli/libexec/helix-pre-bash"),
                        "timeout": 5,
                        "statusMessage": "Checking HELIX LLM execution guard...",
                        "blockOnFailure": True,
                    }
                ]
            },
            {
                "matcher": "WebSearch|WebFetch",
                "hooks": [
                    {
                        "type": "command",
                        "command": _hook_command(helix_home, "cli/libexec/helix-pre-research"),
                        "timeout": 5,
                        "statusMessage": "Checking HELIX research tool guard...",
                        "blockOnFailure": True,
                    }
                ]
            }
        ],
        "PostToolUse": [
            {
                "matcher": "Edit|Write|MultiEdit",
                "hooks": [
                    {
                        "type": "command",
                        "command": _hook_command(helix_home, "cli/libexec/helix-post-tool-use"),
                        "timeout": 10,
                        "statusMessage": "HELIX design sync check...",
                        "blockOnFailure": True,
                    }
                ]
            }
        ],
        "Stop": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": _hook_command(helix_home, "cli/helix-session-summary"),
                        "timeout": 8,
                        "statusMessage": "Generating session summary...",
                        "blockOnFailure": False,
                    }
                ]
            }
        ]
    }


HELIX_HOOKS = _build_hooks()


def _normalize_hook_command(command):
    if not command:
        return ""
    if "/" in command or command.startswith("~"):
        return os.path.abspath(os.path.expanduser(command))
    return command


def _is_helix_hook(entry):
    """hook エントリが HELIX_HOOKS 登録 command と完全一致するかを判定する。

    command に "helix" を含むかという緩い判定ではなく、_build_hooks() が返す
    HELIX_HOOKS の各 hook command と一致する場合のみ HELIX 由来とみなす。
    比較前に `~` を含む path は絶対 path へ正規化し、既存 settings.json の
    チルダ表記とも整合させる。
    """
    known_commands = set()
    for event_entries in HELIX_HOOKS.values():
        for event_entry in event_entries:
            for hook in event_entry.get("hooks", []):
                command = _normalize_hook_command(hook.get("command"))
                if command:
                    known_commands.add(command)

    hooks = entry.get("hooks", [])
    for hook in hooks:
        command = _normalize_hook_command(hook.get("command", ""))
        if command in known_commands:
            return True
    return False


def _merge_hooks(settings, hooks_to_install):
    """HELIX hooks を追加・正規化する。変更があったか返す"""
    if "hooks" not in settings:
        settings["hooks"] = {}

    changed = False
    for event, helix_entries in hooks_to_install.items():
        existing = settings["hooks"].get(event, [])
        non_helix_entries = [entry for entry in existing if not _is_helix_hook(entry)]
        current_helix_entries = [entry for entry in existing if _is_helix_hook(entry)]
        if current_helix_entries != helix_entries:
            settings["hooks"][event] = non_helix_entries + helix_entries
            changed = True

    return changed


def merge(settings):
    """HELIX hooks を追加・正規化する。変更があったか返す"""
    return _merge_hooks(settings, HELIX_HOOKS)


def merge_settings_for_migrate(current, hooks_to_install):
    """migrate.py から使う非破壊 API。

    current は JSON decode 済み dict に限定する。invalid JSON の fail-close は
    呼び出し側で decode 時に止める。
    """
    if not isinstance(current, dict):
        raise ValueError("settings root must be object")
    if not isinstance(hooks_to_install, dict):
        raise ValueError("hooks_to_install must be object")

    merged = copy.deepcopy(current)
    _merge_hooks(merged, copy.deepcopy(hooks_to_install))
    return merged


def remove(settings):
    """HELIX hooks を除去。変更があったか返す"""
    hooks = settings.get("hooks")
    if not hooks:
        return False

    changed = False
    for event in list(hooks.keys()):
        original = hooks[event]
        filtered = [e for e in original if not _is_helix_hook(e)]
        if len(filtered) != len(original):
            changed = True
            if filtered:
                hooks[event] = filtered
            else:
                del hooks[event]

    if not hooks:
        del settings["hooks"]

    return changed


def main():
    try:
        if len(sys.argv) < 2:
            print("Usage: merge_settings.py <settings.json> [--remove]", file=sys.stderr)
            sys.exit(1)

        path = sys.argv[1]
        do_remove = "--remove" in sys.argv

        if os.path.exists(path):
            with open(path, "r") as f:
                settings = json.load(f)
        else:
            settings = {}

        if do_remove:
            changed = remove(settings)
        else:
            changed = merge(settings)

        if changed:
            with open(path, "w") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                f.write("\n")

        # 終了コード: 0=変更あり, 1=変更なし（スクリプト側で判定に使う）
        sys.exit(0 if changed else 1)
    except Exception as e:
        print(f"エラー: 設定マージに失敗しました — {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
