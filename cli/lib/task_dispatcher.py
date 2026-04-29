#!/usr/bin/env python3
from __future__ import annotations

import os
import shlex
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


TASK_TYPES = ("helix:command", "shell:script", "http:webhook")
ALLOWLIST_PATH: Path | None = None


class DispatchError(ValueError):
    pass


def _strip_scalar(value: str) -> str:
    return value.strip().strip("\"'")


def _load_simple_allowlist(path: Path | None = None) -> dict[str, list[str]]:
    allowlist_path = path or ALLOWLIST_PATH or Path.home() / ".config" / "helix" / "automation-allowlist.yaml"
    if not allowlist_path.exists():
        return {}
    sections = {
        "helix_commands": [],
        "shell_scripts": [],
        "webhooks": [],
    }
    aliases = {
        "helix": "helix_commands",
        "commands": "helix_commands",
        "helix_commands": "helix_commands",
        "shell": "shell_scripts",
        "scripts": "shell_scripts",
        "shell_scripts": "shell_scripts",
        "http": "webhooks",
        "urls": "webhooks",
        "webhooks": "webhooks",
    }
    current: str | None = None
    for raw_line in allowlist_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        if stripped.endswith(":") and not stripped.startswith("-"):
            current = aliases.get(stripped[:-1].strip())
            continue
        if stripped.startswith("-") and current:
            item = _strip_scalar(stripped[1:].strip())
            if item:
                sections[current].append(item)
            continue
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            section = aliases.get(key.strip())
            if section and value.strip():
                sections[section].append(_strip_scalar(value))
    return sections


def _is_allowed(kind: str, value: str, allowlist: dict[str, list[str]]) -> bool:
    allowed = allowlist.get(kind, [])
    if value in allowed:
        return True
    if kind == "helix_commands":
        head = value.split()[0] if value.split() else ""
        return head in allowed
    return False


def _helix_binary() -> str:
    helix_home = os.environ.get("HELIX_HOME")
    if helix_home:
        candidate = Path(helix_home) / "cli" / "helix"
        if candidate.exists():
            return str(candidate)
    return str(Path(__file__).resolve().parents[1] / "helix")


def dispatch_task(task_type: str, task_payload: str) -> tuple[bool, str]:
    task_type = (task_type or "").strip()
    task_payload = (task_payload or "").strip()
    allowlist = _load_simple_allowlist()
    if task_type not in TASK_TYPES:
        return False, f"unsupported task_type: {task_type}"
    if not task_payload:
        return False, "task_payload is required"

    try:
        if task_type == "helix:command":
            return _dispatch_helix_command(task_payload, allowlist)
        if task_type == "shell:script":
            return _dispatch_shell_script(task_payload, allowlist)
        if task_type == "http:webhook":
            return _dispatch_webhook(task_payload, allowlist)
    except DispatchError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    return False, f"unsupported task_type: {task_type}"


def _dispatch_helix_command(payload: str, allowlist: dict[str, list[str]]) -> tuple[bool, str]:
    args = shlex.split(payload)
    if not args:
        raise DispatchError("helix command payload is empty")
    if not _is_allowed("helix_commands", payload, allowlist):
        raise DispatchError("helix command is not allowlisted")
    proc = subprocess.run(
        [_helix_binary(), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    output = (proc.stdout + proc.stderr).strip()
    return proc.returncode == 0, output


def _dispatch_shell_script(payload: str, allowlist: dict[str, list[str]]) -> tuple[bool, str]:
    script_path = Path(payload).expanduser().resolve()
    if str(script_path) not in allowlist.get("shell_scripts", []):
        raise DispatchError("shell script is not allowlisted")
    if not script_path.is_file():
        raise DispatchError(f"shell script not found: {script_path}")
    proc = subprocess.run(
        [str(script_path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    output = (proc.stdout + proc.stderr).strip()
    return proc.returncode == 0, output


def _dispatch_webhook(payload: str, allowlist: dict[str, list[str]]) -> tuple[bool, str]:
    parts = shlex.split(payload)
    method = "POST"
    url = payload.strip()
    if len(parts) == 2 and parts[0].upper() in {"GET", "POST"}:
        method, url = parts[0].upper(), parts[1]
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise DispatchError("webhook payload must be an http(s) URL")
    if url not in allowlist.get("webhooks", []):
        raise DispatchError("webhook URL is not allowlisted")
    request = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read(2048).decode("utf-8", errors="replace")
            return 200 <= response.status < 300, f"HTTP {response.status} {body}".strip()
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"


if __name__ == "__main__":
    import sys

    ok, message = dispatch_task(sys.argv[1], " ".join(sys.argv[2:])) if len(sys.argv) >= 3 else (False, "usage")
    print(message)
    raise SystemExit(0 if ok else 1)
