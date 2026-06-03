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
            },
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": _hook_command(helix_home, "cli/helix-stop-hook"),
                        "timeout": 10,
                        "statusMessage": "Syncing handover state...",
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
    if command.startswith("~"):
        return os.path.abspath(os.path.expanduser(command))
    if os.path.isabs(command):
        return os.path.abspath(command)
    return command


def _known_helix_commands(helix_entries):
    commands = set()
    for helix_entry in helix_entries:
        for hook in helix_entry.get("hooks", []):
            command = _normalize_hook_command(hook.get("command"))
            if command:
                commands.add(command)
    return commands


def _all_helix_entries():
    return [helix_entry for event_entries in HELIX_HOOKS.values() for helix_entry in event_entries]


def _is_helix_hook(entry):
    """hook エントリに HELIX_HOOKS 登録 command が含まれるかを厳密判定する。

    command に "helix" を含むかという緩い判定ではなく、_build_hooks() が返す
    HELIX_HOOKS の各 hook command と一致する hook のみ HELIX 由来とみなす。
    比較前に `~` を含む path は絶対 path へ正規化し、既存 settings.json の
    チルダ表記とも整合させる。
    """
    known_commands = _known_helix_commands(_all_helix_entries())

    hooks = entry.get("hooks", [])
    for hook in hooks:
        command = _normalize_hook_command(hook.get("command", ""))
        if command in known_commands:
            return True
    return False


def _canonical_entry_index(entry, helix_entries):
    command_to_index = {}
    for index, helix_entry in enumerate(helix_entries):
        for hook in helix_entry.get("hooks", []):
            command = _normalize_hook_command(hook.get("command"))
            if command:
                command_to_index[command] = index

    for hook in entry.get("hooks", []):
        command = _normalize_hook_command(hook.get("command", ""))
        if command in command_to_index:
            return command_to_index[command]
    return None


def _merge_entry_with_canonical(existing_entry, canonical_entry):
    merged_entry = copy.deepcopy(existing_entry)
    for key, value in canonical_entry.items():
        if key == "hooks":
            continue
        merged_entry[key] = copy.deepcopy(value)

    canonical_commands = _known_helix_commands([canonical_entry])
    canonical_hooks = copy.deepcopy(canonical_entry.get("hooks", []))
    merged_hooks = []
    inserted = False
    for hook in existing_entry.get("hooks", []):
        command = _normalize_hook_command(hook.get("command", ""))
        if command in canonical_commands:
            if not inserted:
                merged_hooks.extend(copy.deepcopy(canonical_hooks))
                inserted = True
            continue
        merged_hooks.append(copy.deepcopy(hook))

    if not inserted:
        merged_hooks.extend(copy.deepcopy(canonical_hooks))

    merged_entry["hooks"] = merged_hooks
    return merged_entry


def _strip_helix_hooks(entry):
    known_commands = _known_helix_commands(_all_helix_entries())
    remaining_hooks = []
    for hook in entry.get("hooks", []):
        command = _normalize_hook_command(hook.get("command", ""))
        if command not in known_commands:
            remaining_hooks.append(copy.deepcopy(hook))

    if not remaining_hooks:
        return None

    stripped_entry = copy.deepcopy(entry)
    stripped_entry["hooks"] = remaining_hooks
    return stripped_entry


def _merge_hooks(settings, hooks_to_install):
    """HELIX hooks を追加・正規化する。変更があったか返す"""
    if "hooks" not in settings:
        settings["hooks"] = {}

    changed = False
    for event, helix_entries in hooks_to_install.items():
        existing = settings["hooks"].get(event, [])
        anchor_index = len(existing)
        custom_entries = []
        merged_canonical_entries = {}

        for index, entry in enumerate(existing):
            canonical_index = _canonical_entry_index(entry, helix_entries)
            if canonical_index is None:
                custom_entries.append((index, copy.deepcopy(entry)))
                continue

            anchor_index = min(anchor_index, index)
            if canonical_index not in merged_canonical_entries:
                merged_canonical_entries[canonical_index] = _merge_entry_with_canonical(
                    entry, helix_entries[canonical_index]
                )

        prefix_custom = [entry for index, entry in custom_entries if index < anchor_index]
        suffix_custom = [entry for index, entry in custom_entries if index >= anchor_index]
        canonical_block = [
            copy.deepcopy(merged_canonical_entries.get(index, helix_entry))
            for index, helix_entry in enumerate(helix_entries)
        ]
        merged_entries = prefix_custom + canonical_block + suffix_custom

        if merged_entries != existing:
            settings["hooks"][event] = merged_entries
            changed = True

    return changed


def merge(settings):
    """HELIX hooks を追加・正規化する。変更があったか返す"""
    return _merge_hooks(settings, HELIX_HOOKS)


def _retile_known_helix_commands(settings):
    known_commands = _known_helix_commands(_all_helix_entries())
    home = os.path.abspath(os.path.expanduser("~"))
    for event_entries in settings.get("hooks", {}).values():
        for entry in event_entries:
            for hook in entry.get("hooks", []):
                command = hook.get("command")
                normalized = _normalize_hook_command(command)
                if normalized in known_commands and normalized.startswith(home + os.sep):
                    hook["command"] = "~" + normalized[len(home):]


def _should_retile_project_settings(path):
    normalized = os.path.normpath(path)
    return normalized.endswith(os.path.join(".claude", "settings.json"))


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
        filtered = []
        for entry in original:
            stripped_entry = _strip_helix_hooks(entry)
            if stripped_entry is not None:
                filtered.append(stripped_entry)

        if filtered != original:
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
            if _should_retile_project_settings(path):
                _retile_known_helix_commands(settings)

        if changed:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                f.write("\n")

        # 終了コード: 0=変更あり, 1=変更なし（スクリプト側で判定に使う）
        sys.exit(0 if changed else 1)
    except Exception as e:
        print(f"エラー: 設定マージに失敗しました — {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
