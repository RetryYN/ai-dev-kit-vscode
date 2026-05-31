#!/usr/bin/env python3
"""HELIX context and guardrail consistency checks."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


PROJECT_CONTEXT_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
]

FRAMEWORK_CONTEXT_FILES = [
    "helix/HELIX_CORE.md",
    "helix/HELIX_RUNTIME_RULES.md",
    "skills/SKILL_MAP.md",
    "helix/CODEX_RUNTIME_ADAPTER.md",
    "helix/CLAUDE_RUNTIME_ADAPTER.md",
    "docs/commands/index.md",
    "docs/commands/ai-harness.md",
]

FRAMEWORK_GUARD_FILES = [
    "cli/lib/research_guard.py",
    "cli/lib/research_tool_guard.py",
    "cli/lib/agent_policy_guard.py",
]


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_json_status(path: Path) -> tuple[str, dict[str, Any]]:
    if not path.exists():
        return "missing", {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return "invalid", {}
    if not isinstance(payload, dict):
        return "invalid", {}
    return "ok", payload


def _hook_entries(settings: dict[str, Any], event: str) -> list[tuple[str, dict[str, Any]]]:
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return []
    entries = hooks.get(event)
    if not isinstance(entries, list):
        return []
    hook_entries: list[tuple[str, dict[str, Any]]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        matcher = str(entry.get("matcher") or "")
        for hook in entry.get("hooks") or []:
            if isinstance(hook, dict) and isinstance(hook.get("command"), str):
                hook_entries.append((matcher, hook))
    return hook_entries


def _hook_commands(settings: dict[str, Any], event: str) -> list[tuple[str, str]]:
    return [(matcher, hook["command"]) for matcher, hook in _hook_entries(settings, event)]


def _has_hook(settings: dict[str, Any], event: str, command_part: str, matcher_part: str = "") -> bool:
    for matcher, command in _hook_commands(settings, event):
        if command_part in command and (not matcher_part or matcher_part in matcher):
            return True
    return False


def _has_blocking_hook(settings: dict[str, Any], event: str, command_part: str, matcher_part: str = "") -> bool:
    for matcher, hook in _hook_entries(settings, event):
        command = hook["command"]
        if command_part in command and (not matcher_part or matcher_part in matcher):
            return hook.get("blockOnFailure") is True
    return False


def _iter_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(_iter_strings(item))
        return out
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_iter_strings(item))
        return out
    return []


def _looks_like_raw_codex_bash_allow(value: str) -> bool:
    if not value.startswith("Bash("):
        return False
    command_pattern = value[5:-1] if value.endswith(")") else value[5:]
    command_pattern = command_pattern.strip()
    first = command_pattern.split(None, 1)[0].split(":", 1)[0].strip("'\"")
    return os.path.basename(first) == "codex"


def _has_local_raw_codex_allow(settings: dict[str, Any]) -> bool:
    return any(_looks_like_raw_codex_bash_allow(value) for value in _iter_strings(settings))


def _git_untracked(root: Path, path: str) -> bool:
    if not (root / ".git").exists():
        return False
    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", path],
        cwd=str(root),
        text=True,
        capture_output=True,
        check=False,
        timeout=5,
    )
    return bool(result.stdout.strip())


def _looks_like_framework_root(path: Path) -> bool:
    return all((path / rel).is_file() for rel in FRAMEWORK_CONTEXT_FILES)


def _framework_root(project_root: Path) -> Path:
    env_root = os.environ.get("HELIX_HOME", "").strip()
    if env_root:
        return Path(env_root).expanduser().resolve()
    if _looks_like_framework_root(project_root):
        return project_root
    return Path(__file__).resolve().parents[2]


def _effective_settings(root: Path) -> tuple[str, Path, dict[str, Any], str]:
    project_path = root / ".claude" / "settings.json"
    project_status, project_settings = _read_json_status(project_path)
    if project_status == "invalid":
        return "project", project_path, {}, "invalid_project_settings"
    if project_status == "ok":
        return "project", project_path, project_settings, ""

    user_path = Path.home() / ".claude" / "settings.json"
    user_status, user_settings = _read_json_status(user_path)
    if user_status == "invalid":
        return "user", user_path, {}, "invalid_user_settings"
    if user_status == "ok":
        return "user", user_path, user_settings, ""

    return "missing", project_path, {}, "missing_project_settings"


def _settings_error_message(error_code: str) -> str:
    if error_code == "invalid_project_settings":
        return ".claude/settings.json is invalid"
    if error_code == "invalid_user_settings":
        return "~/.claude/settings.json is invalid"
    return ".claude/settings.json or ~/.claude/settings.json missing"


def _settings_error_code(error_code: str) -> str:
    return error_code or "missing_project_settings"


def check_context(root: Path) -> dict[str, Any]:
    findings: list[Finding] = []
    infos: list[Finding] = []
    bash_guard_blocks = False
    framework_root = _framework_root(root)

    for rel in PROJECT_CONTEXT_FILES:
        if not (root / rel).is_file():
            findings.append(Finding("error", "missing_context_file", f"required context file missing: {rel}"))

    for rel in FRAMEWORK_CONTEXT_FILES:
        if not (framework_root / rel).is_file():
            findings.append(
                Finding(
                    "error",
                    "missing_context_file",
                    f"required framework context file missing: {rel} (framework_root={framework_root})",
                )
            )

    if (framework_root / "cli").is_dir():
        for rel in FRAMEWORK_GUARD_FILES:
            if not (framework_root / rel).is_file():
                findings.append(Finding("error", "missing_guard_file", f"required guard file missing: {rel}"))

    stale_team_command = "helix team <team>"
    stale_doc_targets = [
        (root, "README.md"),
        (root, "AGENTS.md"),
        (framework_root, "helix/AGENTS.md.example"),
        (framework_root, "cli/templates/AGENTS.md.template"),
    ]
    for base_dir, rel in stale_doc_targets:
        path = base_dir / rel
        if path.is_file() and stale_team_command in path.read_text(encoding="utf-8", errors="replace"):
            findings.append(
                Finding(
                    "error",
                    "stale_team_command_doc",
                    f"{rel} still documents removed team syntax; use `helix team run --definition ...`",
                )
            )

    settings_scope, settings_path, project_settings, settings_error = _effective_settings(root)
    if settings_error:
        findings.append(Finding("error", _settings_error_code(settings_error), _settings_error_message(settings_error)))
    else:
        required_hooks = [
            ("SessionStart", "helix-session-start", ""),
            ("PreToolUse", "helix-check-claudemd", "Write"),
            ("PreToolUse", "helix-pre-bash", "Bash"),
            ("PreToolUse", "helix-pre-research", "WebSearch|WebFetch"),
            ("PostToolUse", "helix-post-tool-use", "Edit|Write|MultiEdit"),
            ("Stop", "helix-session-summary", ""),
        ]
        for event, command_part, matcher_part in required_hooks:
            if not _has_hook(project_settings, event, command_part, matcher_part):
                findings.append(
                    Finding("error", "missing_hook", f"{event} hook missing: {command_part} matcher={matcher_part or '*'}")
                )
        bash_guard_blocks = _has_blocking_hook(project_settings, "PreToolUse", "helix-pre-bash", "Bash")
        if _has_hook(project_settings, "PreToolUse", "helix-pre-bash", "Bash") and not bash_guard_blocks:
            findings.append(
                Finding(
                    "error",
                    "non_blocking_hook",
                    "PreToolUse Bash hook helix-pre-bash must set blockOnFailure=true",
                )
            )
        research_hook_matcher = "WebSearch|WebFetch"
        research_guard_blocks = _has_blocking_hook(
            project_settings, "PreToolUse", "helix-pre-research", research_hook_matcher
        )
        if (
            _has_hook(project_settings, "PreToolUse", "helix-pre-research", research_hook_matcher)
            and not research_guard_blocks
        ):
            findings.append(
                Finding(
                    "error",
                    "non_blocking_hook",
                    "PreToolUse research hook helix-pre-research must set blockOnFailure=true",
                )
            )

    if (root / ".claude" / "settings.local.json").is_file():
        local_settings = _read_json(root / ".claude" / "settings.local.json")
        if _has_local_raw_codex_allow(local_settings):
            if bash_guard_blocks:
                infos.append(
                    Finding(
                        "info",
                        "local_raw_codex_allow_guarded",
                        ".claude/settings.local.json allows raw codex commands, guarded by blockOnFailure Bash PreToolUse",
                    )
                )
            else:
                findings.append(
                    Finding(
                        "warning",
                        "local_raw_codex_allow",
                        ".claude/settings.local.json allows raw codex commands; PreToolUse Bash guard must use blockOnFailure",
                    )
                )

    if not (root / "docs" / "memory").is_dir():
        findings.append(Finding("warning", "missing_docs_memory", "docs/memory directory is absent"))
    if not (root / ".claude" / "memory").exists():
        findings.append(
            Finding(
                "warning",
                "missing_project_memory",
                ".claude/memory is absent; decision/constraint reminder injection is not yet available",
            )
        )
    if (root / ".claude" / "agent-memory").exists() and _git_untracked(root, ".claude/agent-memory"):
        findings.append(
            Finding(
                "warning",
                "untracked_agent_memory",
                ".claude/agent-memory exists as untracked data; decide gitignore or tracked memory policy",
            )
        )

    if (framework_root / "helix" / "HELIX_CORE.md").is_file():
        core_text = (framework_root / "helix" / "HELIX_CORE.md").read_text(encoding="utf-8", errors="replace")
        if "helix code find" in core_text and "--bucket" in core_text:
            cli_path = framework_root / "cli" / "helix"
            if not cli_path.is_file():
                cli_path = Path(__file__).resolve().parents[1] / "helix"
            try:
                help_result = subprocess.run(
                    [str(cli_path), "code", "find", "--help"],
                    cwd=str(root),
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=5,
                )
                help_stdout = help_result.stdout
            except FileNotFoundError:
                help_stdout = ""
            if "--bucket" not in help_stdout:
                findings.append(
                    Finding(
                        "warning",
                        "code_find_bucket_contract_gap",
                        "HELIX_CORE mentions `helix code find --bucket`, but current CLI help does not expose --bucket",
                    )
                )

    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    return {
        "ok": not errors,
        "root": str(root),
        "framework_root": str(framework_root),
        "settings_scope": settings_scope,
        "settings_path": str(settings_path),
        "errors": [asdict(item) for item in errors],
        "warnings": [asdict(item) for item in warnings],
        "infos": [asdict(item) for item in infos],
        "summary": {"error": len(errors), "warning": len(warnings), "info": len(infos)},
    }


def context_bundle(root: Path) -> str:
    payload = check_context(root)
    lines = [
        "## HELIX Context Guard",
        f"- root: {payload['root']}",
        f"- framework_root: {payload['framework_root']}",
        f"- settings: {payload['settings_scope']} ({payload['settings_path']})",
        f"- ok: {str(payload['ok']).lower()}",
        f"- errors: {payload['summary']['error']}",
        f"- warnings: {payload['summary']['warning']}",
        f"- infos: {payload['summary']['info']}",
    ]
    for finding in payload["errors"][:5]:
        lines.append(f"- ERROR {finding['code']}: {finding['message']}")
    for finding in payload["warnings"][:5]:
        lines.append(f"- WARN {finding['code']}: {finding['message']}")
    for finding in payload["infos"][:5]:
        lines.append(f"- INFO {finding['code']}: {finding['message']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(prog="helix context")
    parser.add_argument("--root", default=".")
    subparsers = parser.add_subparsers(dest="command")
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--json", action="store_true")
    bundle_parser = subparsers.add_parser("bundle")
    bundle_parser.add_argument("--json", action="store_true")
    remind_parser = subparsers.add_parser("remind")
    remind_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()
    command = args.command or "check"
    root = Path(args.root).resolve()

    if command == "check":
        payload = check_context(root)
        if getattr(args, "json", False):
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            print(context_bundle(root))
        return 0 if payload["ok"] else 1

    if command in {"bundle", "remind"}:
        if getattr(args, "json", False):
            payload = check_context(root)
            payload["bundle"] = context_bundle(root)
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            print(context_bundle(root))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
