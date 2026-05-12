from __future__ import annotations

import json
from pathlib import Path


_SETTINGS_PATHS = (
    Path(".claude/settings.json"),
    Path(".claude/settings.local.json"),
)
_SHELL_LAUNCHERS = {"bash", "sh", "python", "python3"}


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _first_token(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    if stripped[0] not in {"'", '"'}:
        return stripped.split(None, 1)[0]

    quote = stripped[0]
    escaped = False
    token_chars: list[str] = []
    for char in stripped[1:]:
        if quote == '"' and char == "\\" and not escaped:
            escaped = True
            token_chars.append(char)
            continue
        if char == quote and not escaped:
            break
        token_chars.append(char)
        escaped = False
    return "".join(token_chars).strip()


def _script_path(command: str) -> str:
    first = _first_token(command)
    if first in _SHELL_LAUNCHERS:
        remainder = command[len(first) :].lstrip()
        second = _first_token(remainder)
        return second or first
    return first or command.strip()


def extract_hook_configs(repo_root: str | Path | None = None) -> list[dict[str, str]]:
    root = Path(repo_root).resolve() if repo_root is not None else _default_repo_root()
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str]] = set()

    for relative_path in _SETTINGS_PATHS:
        settings_path = root / relative_path
        if not settings_path.is_file():
            continue
        try:
            loaded = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(loaded, dict):
            continue
        hooks = loaded.get("hooks")
        if not isinstance(hooks, dict):
            continue

        for hook_event, entries in hooks.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                matcher = str(entry.get("matcher") or "*")
                nested_hooks = entry.get("hooks")
                if not isinstance(nested_hooks, list):
                    continue
                for hook in nested_hooks:
                    if not isinstance(hook, dict):
                        continue
                    command = hook.get("command")
                    if not isinstance(command, str) or not command.strip():
                        continue
                    row = {
                        "hook_event": str(hook_event),
                        "matcher": matcher,
                        "command": command.strip(),
                        "script_path": _script_path(command),
                    }
                    key = (
                        row["hook_event"],
                        row["matcher"],
                        row["command"],
                        row["script_path"],
                    )
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append(row)

    return rows
