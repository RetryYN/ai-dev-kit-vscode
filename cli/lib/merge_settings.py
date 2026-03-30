#!/usr/bin/env python3
"""merge_settings.py — ~/.claude/settings.json に HELIX hooks を安全にマージ/除去する

Usage:
    python3 merge_settings.py <settings.json>            # マージ（追加）
    python3 merge_settings.py <settings.json> --remove   # HELIX hooks を除去
"""

import json
import os
import sys

HELIX_HOOKS = {
    "SessionStart": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": "~/ai-dev-kit-vscode/cli/helix-session-start",
                    "timeout": 5,
                    "statusMessage": "Loading HELIX framework..."
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
                    "command": "~/ai-dev-kit-vscode/cli/helix-check-claudemd",
                    "timeout": 5,
                    "statusMessage": "Checking CLAUDE.md template..."
                }
            ]
        }
    ],
    "PostToolUse": [
        {
            "matcher": "Edit|Write",
            "hooks": [
                {
                    "type": "command",
                    "command": "python3 -c \"import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path','') or d.get('tool_response',{}).get('filePath',''))\" | { read -r f; [ -n \"$f\" ] && ~/ai-dev-kit-vscode/cli/helix-hook \"$f\"; } 2>/dev/null || true",
                    "timeout": 10,
                    "statusMessage": "HELIX design sync check..."
                }
            ]
        }
    ]
}


def _is_helix_hook(entry):
    """hook エントリが HELIX 由来かどうか（command に 'helix' を含む）"""
    hooks = entry.get("hooks", [])
    for h in hooks:
        cmd = h.get("command", "")
        if "helix" in cmd:
            return True
    return False


def _has_helix_hook(entries):
    """リスト内に HELIX hook が既にあるか"""
    for entry in entries:
        if _is_helix_hook(entry):
            return True
    return False


def merge(settings):
    """HELIX hooks を追加（既存があればスキップ）。変更があったか返す"""
    if "hooks" not in settings:
        settings["hooks"] = {}

    changed = False
    for event, helix_entries in HELIX_HOOKS.items():
        existing = settings["hooks"].get(event, [])
        if not _has_helix_hook(existing):
            settings["hooks"][event] = existing + helix_entries
            changed = True

    return changed


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


if __name__ == "__main__":
    main()
