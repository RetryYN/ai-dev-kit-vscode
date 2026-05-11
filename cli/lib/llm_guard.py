#!/usr/bin/env python3
"""PreToolUse guard for raw LLM CLI execution."""

from __future__ import annotations

import json
import os
import os.path
import posixpath
import re
import shlex
import sys
from dataclasses import dataclass
from typing import Any


SHELL_BINS = {"bash", "sh", "dash", "fish", "ksh", "mksh", "yash", "zsh"}
SHELL_SCRIPT_RE = re.compile(r"\b(?:bash|sh|dash|fish|ksh|mksh|yash|zsh)\s+(?:-[a-zA-Z]*c|-lc)\s+(['\"])(.*?)\1", re.DOTALL)
HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
SHELL_CONTROL_PREFIX_TOKENS = {"{", "if", "while", "until", "then", "do", "else", "elif"}
SHELL_CONTROL_TRAILER_TOKENS = {"}", "fi", "done", "esac"}
NPX_OPTIONS_WITH_VALUE = {
    "--package",
    "-p",
    "--cache",
    "--prefix",
    "--userconfig",
    "--node-options",
    "--call",
    "-c",
}
ENV_OPTIONS_WITH_VALUE = {"--unset", "-u", "--chdir", "-C", "--split-string", "-S"}
TIMEOUT_OPTIONS_WITH_VALUE = {"--kill-after", "-k", "--signal", "-s"}
TIME_WRAPPER_OPTIONS_WITH_VALUE = {"--format", "-f", "--output", "-o"}
COMMAND_WRAPPERS = {
    "chrt",
    "command",
    "doas",
    "exec",
    "flock",
    "ionice",
    "nice",
    "nohup",
    "rlwrap",
    "setsid",
    "stdbuf",
    "sudo",
    "time",
    "unbuffer",
    "xvfb-run",
}
SUDO_OPTIONS_WITH_VALUE = {
    "-u",
    "-g",
    "-h",
    "-p",
    "-C",
    "-T",
    "--user",
    "--group",
    "--host",
    "--prompt",
    "--chdir",
    "--close-from",
    "--command-timeout",
}
XARGS_OPTIONS_WITH_VALUE = {
    "-a",
    "--arg-file",
    "-d",
    "--delimiter",
    "-E",
    "-I",
    "-L",
    "-n",
    "--max-args",
    "-P",
    "--max-procs",
    "-s",
    "--max-chars",
}
XARGS_OPTIONS_NO_VALUE = {"-0", "--null", "-r", "--no-run-if-empty", "-t", "--verbose"}
PARALLEL_OPTIONS_WITH_VALUE = {
    "-j",
    "--jobs",
    "-S",
    "--sshlogin",
    "--delay",
    "--load",
    "--memfree",
    "--timeout",
    "--results",
    "--joblog",
    "--tmpdir",
    "--workdir",
    "--env",
    "--colsep",
    "--tagstring",
}
PARALLEL_OPTIONS_NO_VALUE = {"--will-cite", "--bar", "--eta", "--halt-on-error", "-k", "--keep-order"}
SCRIPT_OPTIONS_WITH_VALUE = {
    "-c",
    "--command",
    "-E",
    "--echo",
    "-B",
    "--log-io",
    "-I",
    "--log-in",
    "-O",
    "--log-out",
    "-T",
    "--log-timing",
    "-m",
    "--logging-format",
    "-o",
    "--output-limit",
}
SCRIPT_OPTIONS_NO_VALUE = {
    "-a",
    "--append",
    "-e",
    "--return",
    "-f",
    "--flush",
    "--force",
    "-q",
    "--quiet",
    "-t",
    "--timing",
    "-h",
    "--help",
    "-V",
    "--version",
}
SCRIPT_OPTIONS_OPTIONAL_EQUALS_VALUE = {"--timing"}
WATCH_OPTIONS_WITH_VALUE = {"-n", "--interval", "-q", "--equexit"}
WATCH_OPTIONS_NO_VALUE = {
    "-b",
    "--beep",
    "-c",
    "--color",
    "-d",
    "--differences",
    "-e",
    "--errexit",
    "-g",
    "--chgexit",
    "-p",
    "--precise",
    "-t",
    "--no-title",
    "-w",
    "--no-wrap",
    "-r",
    "--no-rerun",
    "-x",
    "--exec",
    "-h",
    "--help",
    "-v",
    "--version",
}
WATCH_OPTIONS_OPTIONAL_EQUALS_VALUE = {"--differences"}
CODEX_OPTIONS_WITH_VALUE = {
    "-c",
    "--config",
    "--enable",
    "--disable",
    "--remote",
    "--remote-auth-token-env",
    "-i",
    "--image",
    "-m",
    "--model",
    "--local-provider",
    "-p",
    "--profile",
    "-s",
    "--sandbox",
    "-C",
    "--cd",
    "--add-dir",
    "-a",
    "--ask-for-approval",
    "--color",
    "-o",
    "--output-last-message",
}
CODEX_OPTIONS_NO_VALUE = {
    "--dangerously-bypass-approvals-and-sandbox",
    "--full-auto",
    "--no-alt-screen",
    "--oss",
    "--search",
    "--skip-git-repo-check",
}
PACKAGE_RUNNER_OPTIONS_WITH_VALUE = {
    "--package",
    "-p",
    "--cwd",
    "-C",
    "--cache",
    "--dir",
    "--prefix",
    "--userconfig",
    "--node-options",
}
PACKAGE_RUNNER_OPTIONS_NO_VALUE = {"-q", "--quiet", "--silent", "--bun"}
DYNAMIC_CODEX_LOOKUP = r"(?:which|command\s+-v|type\s+-P)\s+codex"
DYNAMIC_CODEX_SUB_RE = re.compile(rf"(['\"]?)(?:\$\(\s*{DYNAMIC_CODEX_LOOKUP}\s*\)|`\s*{DYNAMIC_CODEX_LOOKUP}\s*`)\1")
DYNAMIC_CLAUDE_LOOKUP = r"(?:which|command\s+-v|type\s+-P)\s+claude"
DYNAMIC_CLAUDE_SUB_RE = re.compile(rf"(['\"]?)(?:\$\(\s*{DYNAMIC_CLAUDE_LOOKUP}\s*\)|`\s*{DYNAMIC_CLAUDE_LOOKUP}\s*`)\1")
SHELL_PARAM_EXPANSION_RE = re.compile(r"\$(?:\{[^}]+\}|[A-Za-z_][A-Za-z0-9_]*|[0-9@*#?$!-])")
EVAL_CODE_BINS = {
    "node": {"-e", "--eval", "--print", "-p"},
    "nodejs": {"-e", "--eval", "--print", "-p"},
    "perl": {"-e"},
    "php": {"-r"},
    "python": {"-c"},
    "python3": {"-c"},
    "ruby": {"-e"},
}
EVAL_SCRIPT_OPTIONS_WITH_VALUE = {
    "node": {"--require", "-r", "--import"},
    "nodejs": {"--require", "-r", "--import"},
    "perl": {"-I", "-M", "-m"},
    "php": {"-d"},
    "python": {"-W", "-X"},
    "python3": {"-W", "-X"},
    "ruby": {"-I", "-r", "-W"},
}
ARGV_PASSTHROUGH_MARKER = "__HELIX_ARGV_PASSTHROUGH__"


@dataclass(frozen=True)
class GuardResult:
    ok: bool
    reason: str = ""


def _load_payload(stream: Any) -> dict[str, Any]:
    raw = stream.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def extract_bash_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def _read_dollar_paren_body(text: str, start: int) -> tuple[str, int] | None:
    depth = 1
    quote = ""
    escaped = False
    i = start
    while i < len(text):
        char = text[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if char == "\\":
            escaped = True
            i += 1
            continue
        if quote:
            if char == quote:
                quote = ""
            i += 1
            continue
        if char in {"'", '"'}:
            quote = char
            i += 1
            continue
        if char == "$" and i + 1 < len(text) and text[i + 1] == "(":
            depth += 1
            i += 2
            continue
        if char == ")":
            depth -= 1
            if depth == 0:
                return text[start:i], i
        i += 1
    return None


def _read_backtick_body(text: str, start: int) -> tuple[str, int] | None:
    escaped = False
    i = start
    body: list[str] = []
    while i < len(text):
        char = text[i]
        if escaped:
            escaped = False
            body.append(char)
            i += 1
            continue
        if char == "\\":
            escaped = True
            i += 1
            continue
        if char == "`":
            return "".join(body), i
        body.append(char)
        i += 1
    return None


def _command_substitution_bodies(text: str) -> list[str]:
    bodies: list[str] = []
    quote = ""
    escaped = False
    i = 0
    while i < len(text):
        char = text[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if char == "\\":
            escaped = True
            i += 1
            continue
        if quote == "'":
            if char == quote:
                quote = ""
            i += 1
            continue
        if char == "'":
            quote = char
            i += 1
            continue
        if char == '"':
            quote = "" if quote == '"' else '"'
            i += 1
            continue
        if char == "$" and i + 1 < len(text) and text[i + 1] == "(":
            read = _read_dollar_paren_body(text, i + 2)
            if read:
                body, end = read
                bodies.append(body)
                bodies.extend(_command_substitution_bodies(body))
                i = end + 1
                continue
        if char == "`":
            read = _read_backtick_body(text, i + 1)
            if read:
                body, end = read
                bodies.append(body)
                bodies.extend(_command_substitution_bodies(body))
                i = end + 1
                continue
        i += 1
    return bodies


def _process_substitution_bodies(text: str) -> list[str]:
    bodies: list[str] = []
    quote = ""
    escaped = False
    i = 0
    while i < len(text):
        char = text[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if char == "\\":
            escaped = True
            i += 1
            continue
        if quote == "'":
            if char == quote:
                quote = ""
            i += 1
            continue
        if char == "'":
            quote = char
            i += 1
            continue
        if char == '"':
            quote = "" if quote == '"' else '"'
            i += 1
            continue
        if char in {"<", ">"} and i + 1 < len(text) and text[i + 1] == "(":
            read = _read_dollar_paren_body(text, i + 2)
            if read:
                body, end = read
                bodies.append(body)
                bodies.extend(_command_substitution_bodies(body))
                bodies.extend(_process_substitution_bodies(body))
                i = end + 1
                continue
        i += 1
    return bodies


def _join_line_continuations(text: str) -> str:
    return re.sub(r"\\\r?\n[ \t]*", "", text)


def _decode_ansi_c_quoted_fragments(text: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(text):
        if text[i : i + 2] != "$'":
            out.append(text[i])
            i += 1
            continue
        i += 2
        body: list[str] = []
        escaped = False
        while i < len(text):
            char = text[i]
            if escaped:
                body.append("\\" + char)
                escaped = False
                i += 1
                continue
            if char == "\\":
                escaped = True
                i += 1
                continue
            if char == "'":
                i += 1
                break
            body.append(char)
            i += 1
        out.append(_decode_printf_escapes("".join(body)))
    return "".join(out)


def _split_shell_segments(text: str, maxsplit: int = 0) -> list[str]:
    segments: list[str] = []
    current: list[str] = []
    quote = ""
    escaped = False
    substitution_depth = 0
    splits = 0
    i = 0
    while i < len(text):
        char = text[i]
        if escaped:
            escaped = False
            current.append(char)
            i += 1
            continue
        if char == "\\":
            escaped = True
            current.append(char)
            i += 1
            continue
        if quote:
            current.append(char)
            if char == quote:
                quote = ""
            i += 1
            continue
        if char in {"'", '"', "`"}:
            quote = char
            current.append(char)
            i += 1
            continue
        if char == "$" and i + 1 < len(text) and text[i + 1] == "(":
            substitution_depth += 1
            current.append(char)
            current.append(text[i + 1])
            i += 2
            continue
        if char in {"<", ">"} and i + 1 < len(text) and text[i + 1] == "(":
            substitution_depth += 1
            current.append(char)
            current.append(text[i + 1])
            i += 2
            continue
        if substitution_depth and char == ")":
            substitution_depth -= 1
            current.append(char)
            i += 1
            continue
        if not substitution_depth and (not maxsplit or splits < maxsplit):
            if char in {";", "\n", "|", "&"}:
                if i + 1 < len(text) and text[i : i + 2] in {"&&", "||", "|&"}:
                    i += 2
                else:
                    i += 1
                segments.append("".join(current))
                current = []
                splits += 1
                continue
        current.append(char)
        i += 1
    segments.append("".join(current))
    return segments


def _iter_command_surfaces(command: str) -> list[str]:
    command = _join_line_continuations(command)
    candidates = [command]
    candidates.extend(match.group(2) for match in SHELL_SCRIPT_RE.finditer(command))
    surfaces: list[str] = []
    seen: set[str] = set()
    queued: list[str] = []
    for candidate in candidates:
        candidate = _without_safe_heredoc_bodies(candidate)
        queued.append(candidate)
    while queued:
        surface = queued.pop(0)
        if not surface or surface in seen:
            continue
        seen.add(surface)
        surfaces.append(surface)
        queued.extend(_function_definition_bodies(surface))
        queued.extend(_command_substitution_bodies(surface))
        queued.extend(_process_substitution_bodies(surface))
        queued.extend(_runner_embedded_command_bodies(surface))
        queued.extend(_eval_stdin_code_command_bodies(surface))
        queued.extend(_xargs_literal_pipeline_bodies(surface))
        queued.extend(_pipeline_script_write_bodies(surface))
        queued.extend(_eval_code_script_write_bodies(surface))
        queued.extend(_shell_stdin_command_bodies(surface))
        queued.extend(_shell_redirection_command_bodies(surface))
        queued.extend(_literal_script_write_bodies(surface))
    return surfaces


def _function_definition_bodies(text: str) -> list[str]:
    bodies: list[str] = []
    patterns = [
        r"(?:^|[;&\n])\s*[A-Za-z_][A-Za-z0-9_]*\s*\(\)\s*\{([^}]*)\}",
        r"(?:^|[;&\n])\s*function\s+[A-Za-z_][A-Za-z0-9_]*\s*(?:\(\))?\s*\{([^}]*)\}",
    ]
    for pattern in patterns:
        bodies.extend(match.group(1) for match in re.finditer(pattern, text, flags=re.DOTALL))
    return bodies


def _literal_script_write_bodies(text: str) -> list[str]:
    executed_script_paths = _shell_executed_paths(text)
    if not executed_script_paths:
        return []
    bodies: list[str] = []
    for segment in _split_shell_segments(text):
        write_targets = _heredoc_write_targets(segment)
        if not write_targets or not (write_targets & executed_script_paths):
            continue
        command_part = re.split(r"(?:^|\s)(?:\d?>|>>)\s*['\"]?[^'\"\s;&|<>]+['\"]?", segment, maxsplit=1)[0]
        command_part = re.split(r"\btee\b(?:\s+-[A-Za-z]+)*\s+['\"]?[^'\"\s;&|<>]+['\"]?", command_part, maxsplit=1)[0]
        try:
            tokens = [_decode_detection_token(token) for token in shlex.split(command_part, comments=False, posix=True)]
        except ValueError:
            continue
        bodies.extend(_stdout_literal_bodies(tokens))
    return bodies


def _without_safe_heredoc_bodies(text: str) -> str:
    lines = text.splitlines()
    output: list[str] = []
    executed_script_paths = _shell_executed_paths(text)
    pending: list[tuple[str, bool, bool]] = []
    for line in lines:
        if pending:
            delimiter, keep_body, inspect_expansions = pending[0]
            if line.strip() == delimiter:
                pending.pop(0)
                output.append(line)
            elif keep_body or (inspect_expansions and _has_command_substitution_syntax(line)):
                output.append(line)
            continue

        output.append(line)
        for match in HEREDOC_RE.finditer(line):
            write_targets = _heredoc_write_targets(line)
            pending.append(
                (
                    match.group(2),
                    _heredoc_body_executes(line[: match.start()], line[match.end() :])
                    or _heredoc_body_interpreter_executes(line[: match.start()], line[match.end() :])
                    or bool(write_targets & executed_script_paths),
                    not bool(match.group(1)),
                )
            )
    return "\n".join(output)


def _eval_stdin_code_command_bodies(text: str) -> list[str]:
    lines = text.splitlines()
    bodies: list[str] = []
    pending: list[tuple[str, list[str]]] = []
    executed_script_paths = _shell_executed_paths(text)
    for line in lines:
        if pending:
            delimiter, body = pending[0]
            if line.strip() == delimiter:
                pending.pop(0)
                bodies.extend(_code_string_command_bodies("\n".join(body)))
            else:
                body.append(line)
            continue

        for match in HEREDOC_RE.finditer(line):
            write_targets = _heredoc_write_targets(line)
            if _heredoc_body_interpreter_executes(line[: match.start()], line[match.end() :]) or bool(
                write_targets & executed_script_paths
            ):
                pending.append((match.group(2), []))
                break
    return bodies


def _heredoc_write_targets(line: str) -> set[str]:
    targets: set[str] = set()
    for match in re.finditer(r"(?:^|\s)(?:\d?>|>>)\s*(['\"]?)([^'\"\s;&|<>]+)\1", line):
        targets.add(_normalize_script_path(match.group(2)))
    for match in re.finditer(r"\btee\b(?:\s+-[A-Za-z]+)*\s+(['\"]?)([^'\"\s;&|<>]+)\1", line):
        targets.add(_normalize_script_path(match.group(2)))
    for match in re.finditer(r"\bdd\b(?:\s+[^ \t;&|<>]+)*\s+of=(['\"]?)([^'\"\s;&|<>]+)\1", line):
        targets.add(_normalize_script_path(match.group(2)))
    return targets


def _shell_executed_paths(text: str) -> set[str]:
    paths: set[str] = set()
    for segment in _split_shell_segments(text):
        try:
            tokens = shlex.split(segment, comments=False, posix=True)
        except ValueError:
            continue
        path = (
            _shell_script_path(tokens)
            or _interpreter_script_path(tokens)
            or _shell_input_redirect_path(tokens)
            or _sourced_script_path(tokens)
            or _direct_executable_path(tokens)
        )
        if not path:
            try:
                lexer = shlex.shlex(segment, posix=True, punctuation_chars="<>")
                lexer.commenters = ""
                lexer.whitespace_split = True
                punct_tokens = list(lexer)
            except ValueError:
                punct_tokens = []
            path = _shell_input_redirect_path(punct_tokens) if punct_tokens else None
        if path:
            paths.add(_normalize_script_path(path))
    return paths


def _normalize_script_path(path: str) -> str:
    path = path.rstrip(";")
    normalized = posixpath.normpath(path)
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _sourced_script_path(tokens: list[str]) -> str | None:
    remaining = _strip_env_prefix(tokens)
    for _ in range(4):
        if not remaining:
            return None
        base = _basename(remaining[0])
        if base in COMMAND_WRAPPERS:
            remaining = _strip_env_prefix(_strip_command_wrapper(remaining))
            continue
        if base in {"source", "."} and len(remaining) > 1:
            return remaining[1]
        return None
    return None


def _direct_executable_path(tokens: list[str]) -> str | None:
    remaining = _strip_env_prefix(tokens)
    for _ in range(4):
        if not remaining:
            return None
        base = _basename(remaining[0])
        if base in COMMAND_WRAPPERS:
            remaining = _strip_env_prefix(_strip_command_wrapper(remaining))
            continue
        command = remaining[0]
        return command if command.startswith(("/", "./", "../")) else None
    return None


def _shell_script_path(tokens: list[str]) -> str | None:
    remaining = _strip_env_prefix(tokens)
    for _ in range(4):
        if not remaining:
            return None
        base = _basename(remaining[0])
        if base in COMMAND_WRAPPERS:
            remaining = _strip_env_prefix(_strip_command_wrapper(remaining))
            continue
        if base not in SHELL_BINS:
            return None
        script_args = remaining[1:]
        while script_args:
            token = script_args.pop(0)
            if token == "--":
                break
            if token == "-c" or (token.startswith("-") and not token.startswith("--") and "c" in token[1:]):
                return None
            if token in {"<", "0<"} or token.startswith(("0<", "<")):
                return None
            if token.startswith("-"):
                continue
            return token
        return script_args[0] if script_args else None
    return None


def _shell_input_redirect_path(tokens: list[str]) -> str | None:
    remaining = _strip_env_prefix(tokens)
    for _ in range(4):
        if not remaining:
            return None
        base = _basename(remaining[0])
        if base in COMMAND_WRAPPERS:
            remaining = _strip_env_prefix(_strip_command_wrapper(remaining))
            continue
        if base not in SHELL_BINS:
            return None
        for index, token in enumerate(remaining[1:]):
            if token in {"<", "0<"} and index + 2 < len(remaining):
                candidate = remaining[index + 2]
                if not candidate.startswith(("<(", "<<", "<<<")):
                    return candidate
            for prefix in ("0<", "<"):
                if token.startswith(prefix) and len(token) > len(prefix):
                    candidate = token[len(prefix) :]
                    if not candidate.startswith(("(", "<")):
                        return candidate
        return None
    return None


def _interpreter_script_path(tokens: list[str]) -> str | None:
    remaining = _strip_env_prefix(tokens)
    for _ in range(4):
        if not remaining:
            return None
        base = _basename(remaining[0])
        if base in COMMAND_WRAPPERS:
            remaining = _strip_env_prefix(_strip_command_wrapper(remaining))
            continue
        if base not in EVAL_CODE_BINS:
            return None
        args = remaining[1:]
        while args:
            token = args.pop(0)
            if token == "--":
                break
            if token in EVAL_CODE_BINS[base]:
                return None
            if any(token.startswith(f"{option}=") for option in EVAL_SCRIPT_OPTIONS_WITH_VALUE.get(base, set()) if option.startswith("--")):
                continue
            if token in EVAL_SCRIPT_OPTIONS_WITH_VALUE.get(base, set()):
                if args:
                    args.pop(0)
                continue
            if token.startswith("-"):
                continue
            return token
        return args[0] if args else None
    return None


def _has_command_substitution_syntax(text: str) -> bool:
    return "$(" in text or "`" in text


def _shell_stdin_command_bodies(text: str) -> list[str]:
    try:
        lexer = shlex.shlex(text.replace("|&", "|"), posix=True, punctuation_chars="|")
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return []

    stages: list[list[str]] = []
    start = 0
    for index, token in enumerate(tokens):
        if token == "|":
            stages.append([_decode_detection_token(item) for item in tokens[start:index]])
            start = index + 1
    stages.append([_decode_detection_token(item) for item in tokens[start:]])

    bodies: list[str] = []
    carried_literals: list[str] = []
    for stage in stages:
        if not stage:
            carried_literals = []
            continue
        literal_bodies = [*_stdout_literal_bodies(stage), *_here_string_literal_bodies(stage)]
        if literal_bodies:
            carried_literals = literal_bodies
            continue
        if _tokens_execute_shell(stage):
            bodies.extend(carried_literals)
            carried_literals = []
            continue
        if carried_literals and _tokens_passthrough_stdin(stage):
            if _tokens_sed_stdin(stage):
                sed_literals = _sed_transformed_literals(stage, carried_literals)
                carried_literals = [
                    *carried_literals,
                    *sed_literals,
                    *(body.lower() for body in carried_literals),
                    *(body.lower() for body in sed_literals),
                ]
            continue
        carried_literals = []
    return bodies


def _here_string_literal_bodies(tokens: list[str]) -> list[str]:
    bodies: list[str] = []
    for index, token in enumerate(tokens):
        body = ""
        if token == "<<<" and index + 1 < len(tokens):
            body = tokens[index + 1]
        elif token.startswith("<<<") and len(token) > 3:
            body = token[3:]
        if not body:
            continue
        if body.startswith("$") and len(body) > 1:
            body = body[1:]
        literal_body = _shell_word_literal_body(body) or body
        bodies.append(_decode_printf_escapes(literal_body))
    return bodies


def _xargs_literal_pipeline_bodies(text: str) -> list[str]:
    try:
        lexer = shlex.shlex(text.replace("|&", "|"), posix=True, punctuation_chars="|")
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return []

    stages: list[list[str]] = []
    start = 0
    for index, token in enumerate(tokens):
        if token == "|":
            stages.append([_decode_detection_token(item) for item in tokens[start:index]])
            start = index + 1
    stages.append([_decode_detection_token(item) for item in tokens[start:]])

    bodies: list[str] = []
    carried_literals: list[str] = []
    for stage in stages:
        if not stage:
            carried_literals = []
            continue
        literal_bodies = _stdout_literal_bodies(stage)
        if literal_bodies:
            carried_literals = literal_bodies
            continue
        substituted = _xargs_substituted_bodies(stage, carried_literals)
        if substituted:
            bodies.extend(substituted)
            carried_literals = []
            continue
        carried_literals = []
    return bodies


def _xargs_substituted_bodies(tokens: list[str], literals: list[str]) -> list[str]:
    if not literals:
        return []
    remaining = _strip_env_prefix(tokens)
    if not remaining or _basename(remaining[0]) != "xargs":
        return []
    placeholder = "{}"
    command_tokens: list[str] = []
    args = remaining[1:]
    i = 0
    while i < len(args):
        token = args[i]
        if token == "--":
            command_tokens = args[i + 1 :]
            break
        if token in {"-I", "--replace"} and i + 1 < len(args):
            placeholder = args[i + 1]
            i += 2
            continue
        if token.startswith("--replace="):
            placeholder = token.split("=", 1)[1]
            i += 1
            continue
        if token in XARGS_OPTIONS_WITH_VALUE:
            i += 2
            continue
        if any(token.startswith(f"{option}=") for option in XARGS_OPTIONS_WITH_VALUE if option.startswith("--")):
            i += 1
            continue
        if token in XARGS_OPTIONS_NO_VALUE or token.startswith("-"):
            i += 1
            continue
        command_tokens = args[i:]
        break
    if not command_tokens:
        return []
    bodies: list[str] = []
    for literal in literals:
        literal_tokens = literal.split()
        rendered_tokens: list[str] = []
        for token in command_tokens:
            if token == placeholder:
                rendered_tokens.extend(literal_tokens)
            else:
                rendered_tokens.append(token.replace(placeholder, literal))
        bodies.append(" ".join(rendered_tokens))
    return bodies


def _pipeline_script_write_bodies(text: str) -> list[str]:
    executed_script_paths = _shell_executed_paths(text)
    if not executed_script_paths:
        return []
    try:
        lexer = shlex.shlex(text.replace("|&", "|"), posix=True, punctuation_chars="|")
        lexer.whitespace_split = True
        raw_tokens = list(lexer)
    except ValueError:
        return []

    stages: list[list[str]] = []
    start = 0
    for index, token in enumerate(raw_tokens):
        if token == "|":
            stages.append([_decode_detection_token(item) for item in raw_tokens[start:index]])
            start = index + 1
    stages.append([_decode_detection_token(item) for item in raw_tokens[start:]])

    bodies: list[str] = []
    carried_literals: list[str] = []
    for stage in stages:
        if not stage:
            carried_literals = []
            continue
        literal_bodies = _stdout_literal_bodies(stage)
        if literal_bodies:
            carried_literals = literal_bodies
            continue
        if carried_literals and _tokens_write_to_paths(stage, executed_script_paths):
            bodies.extend(carried_literals)
            carried_literals = []
            continue
        if carried_literals and _tokens_passthrough_stdin(stage):
            continue
        carried_literals = []
    return bodies


def _eval_code_script_write_bodies(text: str) -> list[str]:
    executed_script_paths = _shell_executed_paths(text)
    if not executed_script_paths:
        return []
    bodies: list[str] = []
    for segment in _split_shell_segments(text):
        try:
            tokens = [_decode_detection_token(token) for token in shlex.split(segment, comments=False, posix=True)]
        except ValueError:
            continue
        runner_tokens = _strip_env_prefix(tokens)
        if not _tokens_start_eval_code_runner(runner_tokens):
            continue
        for value in _embedded_command_values(runner_tokens):
            if not re.search(r"\b(?:open|write\w*|Path)\b", value, flags=re.IGNORECASE):
                continue
            literals = _quoted_string_literals(_collapse_simple_string_concats(value))
            literal_paths = {_normalize_script_path(literal) for literal in literals}
            if not (literal_paths & executed_script_paths):
                continue
            bodies.extend(literal for literal in literals if re.search(r"\bcodex\s+(?:exec|e)\b", literal))
            bodies.extend(literal for literal in literals if _segment_has_raw_claude_cli(literal))
            joined = " ".join(literals)
            if _segment_has_raw_codex_exec(joined):
                bodies.append(joined)
            if _segment_has_raw_claude_cli(joined):
                bodies.append(joined)
    return bodies


def _tokens_write_to_paths(tokens: list[str], target_paths: set[str]) -> bool:
    if not target_paths:
        return False
    remaining = _strip_env_prefix(tokens)
    if not remaining:
        return False
    base = _basename(remaining[0])
    if base == "tee":
        for token in remaining[1:]:
            if token == "--":
                continue
            if token.startswith("-"):
                continue
            if token.startswith(">"):
                break
            if _normalize_script_path(token) in target_paths:
                return True
    if base == "dd":
        for token in remaining[1:]:
            if token.startswith("of=") and _normalize_script_path(token.split("=", 1)[1]) in target_paths:
                return True
    for index, token in enumerate(remaining):
        if token in {">", "1>", ">>", "1>>"} and index + 1 < len(remaining):
            if _normalize_script_path(remaining[index + 1]) in target_paths:
                return True
        for prefix in (">", "1>", ">>", "1>>"):
            if token.startswith(prefix) and len(token) > len(prefix):
                if _normalize_script_path(token[len(prefix) :]) in target_paths:
                    return True
    return False


def _shell_redirection_command_bodies(text: str) -> list[str]:
    bodies: list[str] = []
    shell_name = r"(?:bash|sh|dash|fish|ksh|mksh|yash|zsh)"
    for match in re.finditer(rf"\b{shell_name}\b[^;&|]*<<<\s*(['\"])(.*?)\1", text, flags=re.DOTALL):
        bodies.append(match.group(2))
    for match in re.finditer(rf"\b{shell_name}\b[^;&|]*<<<\s*", text, flags=re.DOTALL):
        read = _read_shell_word(text, match.end())
        if not read:
            continue
        word, _ = read
        literal_body = _shell_word_literal_body(word)
        if literal_body:
            bodies.append(literal_body)
        for body in _command_substitution_bodies(word):
            bodies.extend(_stdout_body_literals(body))
            bodies.extend(_stdout_script_literals(body))
    shell_consumes_process_substitution = bool(
        re.search(rf"\b{shell_name}\b[^;&|]*(?:<\s*<\(|\s<\()", text)
        or re.search(rf"\|\s*{shell_name}\b", text)
        or re.search(r"(?:^|[;&|\n])\s*(?:source|\.)\s+<\(", text)
    )
    if not shell_consumes_process_substitution:
        return bodies
    for body in _process_substitution_bodies(text):
        try:
            tokens = [_decode_detection_token(token) for token in shlex.split(body, comments=False, posix=True)]
        except ValueError:
            continue
        bodies.extend(_stdout_literal_bodies(tokens))
    return bodies


def _stdout_literal_bodies(tokens: list[str]) -> list[str]:
    remaining = _strip_env_prefix(tokens)
    for _ in range(4):
        if not remaining:
            return []
        base = _basename(remaining[0])
        if base in COMMAND_WRAPPERS:
            remaining = _strip_env_prefix(_strip_command_wrapper(remaining))
            continue
        if base == "printf":
            return _printf_literal_bodies(remaining[1:])
        if base == "echo":
            return _echo_literal_bodies(remaining[1:])
        return []
    return []


def _tokens_passthrough_stdin(tokens: list[str]) -> bool:
    remaining = _strip_env_prefix(tokens)
    for _ in range(4):
        if not remaining:
            return False
        base = _basename(remaining[0])
        if base in COMMAND_WRAPPERS:
            remaining = _strip_env_prefix(_strip_command_wrapper(remaining))
            continue
        return base in {"cat", "tee", "sed"}
    return False


def _tokens_sed_stdin(tokens: list[str]) -> bool:
    remaining = _strip_env_prefix(tokens)
    for _ in range(4):
        if not remaining:
            return False
        base = _basename(remaining[0])
        if base in COMMAND_WRAPPERS:
            remaining = _strip_env_prefix(_strip_command_wrapper(remaining))
            continue
        return base == "sed"
    return False


def _sed_transformed_literals(tokens: list[str], bodies: list[str]) -> list[str]:
    expressions: list[str] = []
    remaining = _strip_env_prefix(tokens)
    if not remaining:
        return []
    args = remaining[1:] if _basename(remaining[0]) == "sed" else remaining
    i = 0
    while i < len(args):
        token = args[i]
        if token == "--":
            i += 1
            continue
        if token in {"-e", "--expression"} and i + 1 < len(args):
            expressions.append(args[i + 1])
            i += 2
            continue
        if token.startswith("--expression="):
            expressions.append(token.split("=", 1)[1])
            i += 1
            continue
        if token.startswith("-"):
            i += 1
            continue
        expressions.append(token)
        i += 1

    transformed: list[str] = []
    for expression in expressions:
        operation = _parse_sed_substitution(expression)
        if not operation:
            continue
        old, new, count = operation
        transformed.extend(body.replace(old, new, count) for body in bodies)
    return transformed


def _parse_sed_substitution(expression: str) -> tuple[str, str, int] | None:
    if not expression.startswith("s") or len(expression) < 4:
        return None
    delimiter = expression[1]
    if delimiter.isalnum() or delimiter.isspace():
        return None
    parts: list[str] = []
    current: list[str] = []
    escaped = False
    for char in expression[2:]:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == delimiter and len(parts) < 2:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    if len(parts) != 2:
        return None
    flags = "".join(current)
    old, new = parts
    if not old:
        return None
    return old, new, 0 if "g" in flags else 1


def _printf_literal_bodies(args: list[str]) -> list[str]:
    remaining = list(args)
    while remaining and remaining[0].startswith("-"):
        if remaining[0] == "--":
            remaining.pop(0)
            break
        remaining.pop(0)
    if not remaining:
        return []
    fmt = _decode_printf_escapes(remaining[0])
    values = [_decode_printf_escapes(value) for value in remaining[1:]]
    bodies = [fmt, *values]
    if values:
        bodies.append(_render_printf_sample(fmt, values))
    return bodies


def _echo_literal_bodies(args: list[str]) -> list[str]:
    remaining = list(args)
    decode_escapes = False
    while remaining and remaining[0].startswith("-") and set(remaining[0][1:]) <= {"e", "E", "n"}:
        option = remaining.pop(0)
        if "e" in option:
            decode_escapes = True
        if "E" in option:
            decode_escapes = False
    body = " ".join(remaining)
    return [_decode_printf_escapes(body) if decode_escapes else body]


def _shell_word_literal_body(word: str) -> str:
    if word.startswith("$'") and word.endswith("'") and len(word) >= 3:
        return _decode_printf_escapes(word[2:-1])
    if (word.startswith("'") and word.endswith("'")) or (word.startswith('"') and word.endswith('"')):
        return word[1:-1]
    try:
        tokens = shlex.split(word, comments=False, posix=True)
    except ValueError:
        return ""
    return tokens[0] if len(tokens) == 1 else ""


def _render_printf_sample(fmt: str, values: list[str]) -> str:
    rendered_parts: list[str] = []
    index = 0
    while index < len(values):
        used = False

        def replace(_: re.Match[str]) -> str:
            nonlocal index, used
            if index >= len(values):
                return ""
            used = True
            value = values[index]
            index += 1
            return value

        rendered = re.sub(r"%s", replace, fmt)
        rendered_parts.append(rendered)
        if not used:
            break
    return "".join(rendered_parts) if rendered_parts else fmt


def _decode_printf_escapes(value: str) -> str:
    try:
        return bytes(value, "utf-8").decode("unicode_escape")
    except UnicodeDecodeError:
        return value


def _read_shell_word(text: str, start: int = 0) -> tuple[str, int] | None:
    word: list[str] = []
    quote = ""
    escaped = False
    i = start
    while i < len(text):
        char = text[i]
        if escaped:
            escaped = False
            word.append(char)
            i += 1
            continue
        if char == "\\":
            escaped = True
            word.append(char)
            i += 1
            continue
        if quote:
            word.append(char)
            if char == quote:
                quote = ""
            i += 1
            continue
        if char in {"'", '"'}:
            quote = char
            word.append(char)
            i += 1
            continue
        if char == "$" and i + 1 < len(text) and text[i + 1] == "(":
            read = _read_dollar_paren_body(text, i + 2)
            if read:
                _, end = read
                word.append(text[i : end + 1])
                i = end + 1
                continue
        if char == "`":
            read = _read_backtick_body(text, i + 1)
            if read:
                _, end = read
                word.append(text[i : end + 1])
                i = end + 1
                continue
        if char.isspace():
            break
        word.append(char)
        i += 1
    return ("".join(word), i) if word else None


def _raw_command_word_and_rest(segment: str) -> tuple[str, str] | None:
    i = 0
    while i < len(segment):
        while i < len(segment) and segment[i].isspace():
            i += 1
        read = _read_shell_word(segment, i)
        if not read:
            return None
        word, end = read
        if _raw_word_is_assignment(word):
            i = end
            continue
        return word, segment[end:].lstrip()
    return None


def _raw_word_is_assignment(word: str) -> bool:
    return _split_shell_assignment_word(word) is not None


def _split_shell_assignment_word(word: str) -> tuple[str, str, str] | None:
    match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)(\+?=)(.*)$", word)
    if not match:
        return None
    return match.group(1), match.group(2), match.group(3)


def _strip_outer_shell_quotes(word: str) -> str:
    if len(word) >= 2 and word[0] == word[-1] and word[0] in {"'", '"'}:
        return word[1:-1]
    return word


def _stdout_body_may_emit_codex(body: str) -> bool:
    try:
        tokens = [_decode_detection_token(token) for token in shlex.split(body, comments=False, posix=True)]
    except ValueError:
        return False
    return any(value.strip() == "codex" for value in _stdout_literal_bodies(tokens))


def _stdout_body_may_emit_claude(body: str) -> bool:
    try:
        tokens = [_decode_detection_token(token) for token in shlex.split(body, comments=False, posix=True)]
    except ValueError:
        return False
    return any(value.strip() == "claude" for value in _stdout_literal_bodies(tokens))


def _stdout_body_literals(body: str) -> list[str]:
    try:
        tokens = [_decode_detection_token(token) for token in shlex.split(body, comments=False, posix=True)]
    except ValueError:
        return []
    return _stdout_literal_bodies(tokens)


def _stdout_script_literals(body: str) -> list[str]:
    segments = [segment.strip() for segment in _split_shell_segments(body) if segment.strip()]
    if len(segments) <= 1:
        return []
    outputs: list[str] = []
    for segment in segments:
        try:
            tokens = [_decode_detection_token(token) for token in shlex.split(segment, comments=False, posix=True)]
        except ValueError:
            return []
        literals = _stdout_literal_bodies(tokens)
        if not literals:
            return []
        outputs.append(literals[-1])
    return ["\n".join(outputs)]


def _word_substitution_renders(word: str) -> list[str]:
    renders = [word]
    for body in _command_substitution_bodies(word):
        replacements = [*_stdout_body_literals(body), *_stdout_script_literals(body)]
        if not replacements:
            continue
        next_renders: list[str] = []
        for current in renders:
            for replacement in replacements:
                next_renders.append(current.replace(f"$({body})", replacement).replace(f"`{body}`", replacement))
        renders = next_renders or renders
    return renders


def _append_embedded_command_value(values: list[str], value: str) -> None:
    values.append(value)
    for rendered in _word_substitution_renders(value):
        if rendered != value:
            values.append(rendered)


def _shell_script_value(tokens: list[str], script_index: int) -> str:
    value = tokens[script_index]
    if value.startswith(("$(", "`")) and script_index + 1 < len(tokens):
        return " ".join(tokens[script_index:])
    return value


def _word_may_expand_to_codex(word: str) -> bool:
    normalized = _strip_outer_shell_quotes(word)
    base = _basename(normalized)
    if base == "codex" or base == "@openai/codex" or base.startswith("codex@") or base.startswith("@openai/codex@"):
        return True
    if not any(marker in normalized for marker in ("$", "`")):
        return False
    if any(_stdout_body_may_emit_codex(body) for body in _command_substitution_bodies(normalized)):
        return True
    if any(re.fullmatch(rf"\s*{DYNAMIC_CODEX_LOOKUP}\s*", body) for body in _command_substitution_bodies(normalized)):
        return True
    if any(_basename(rendered) == "codex" for rendered in _word_substitution_renders(normalized)):
        return True
    variable_refs = SHELL_PARAM_EXPANSION_RE.findall(normalized)
    if any("codex" in ref.lower() for ref in variable_refs):
        return True
    skeleton = SHELL_PARAM_EXPANSION_RE.sub("", normalized)
    for body in _command_substitution_bodies(skeleton):
        skeleton = skeleton.replace(f"$({body})", "")
        skeleton = skeleton.replace(f"`{body}`", "")
    return _basename(skeleton) == "codex"


def _word_may_expand_to_claude(word: str) -> bool:
    normalized = _strip_outer_shell_quotes(word)
    base = _basename(normalized)
    if base == "claude" or base == "@anthropic-ai/claude-code" or base.startswith("claude@") or base.startswith(
        "@anthropic-ai/claude-code@"
    ):
        return True
    if not any(marker in normalized for marker in ("$", "`")):
        return False
    if any(_stdout_body_may_emit_claude(body) for body in _command_substitution_bodies(normalized)):
        return True
    if any(re.fullmatch(rf"\s*{DYNAMIC_CLAUDE_LOOKUP}\s*", body) for body in _command_substitution_bodies(normalized)):
        return True
    if any(_basename(rendered) == "claude" for rendered in _word_substitution_renders(normalized)):
        return True
    variable_refs = SHELL_PARAM_EXPANSION_RE.findall(normalized)
    if any("claude" in ref.lower() for ref in variable_refs):
        return True
    skeleton = SHELL_PARAM_EXPANSION_RE.sub("", normalized)
    for body in _command_substitution_bodies(skeleton):
        skeleton = skeleton.replace(f"$({body})", "")
        skeleton = skeleton.replace(f"`{body}`", "")
    return _basename(skeleton) == "claude"


def _raw_rest_is_codex_exec(rest: str) -> bool:
    try:
        tokens = [_decode_detection_token(token) for token in shlex.split(rest, comments=False, posix=True)]
    except ValueError:
        return False
    return _tokens_are_raw_codex_command(tokens)


def _raw_command_word_may_expand_to_codex_exec(segment: str) -> bool:
    command = _raw_command_word_and_rest(segment)
    if not command:
        return False
    word, rest = command
    return _word_may_expand_to_codex(word) and _raw_rest_is_codex_exec(rest)


def _raw_command_word_may_expand_to_claude_cli(segment: str) -> bool:
    command = _raw_command_word_and_rest(segment)
    if not command:
        return False
    word, _ = command
    return _word_may_expand_to_claude(word)


def _tokens_execute_shell(tokens: list[str]) -> bool:
    remaining = _strip_env_prefix(tokens)
    for _ in range(4):
        if not remaining:
            return False
        if _basename(remaining[0]) in SHELL_BINS:
            return True
        if _basename(remaining[0]) not in COMMAND_WRAPPERS:
            return False
        remaining = _strip_env_prefix(_strip_command_wrapper(remaining))
    return False


def _heredoc_body_executes(command_prefix: str, command_suffix: str) -> bool:
    try:
        tokens = shlex.split(command_prefix, comments=False, posix=True)
    except ValueError:
        tokens = []
    if _tokens_execute_shell(tokens):
        return True
    for pipeline_part in re.split(r"\|&?", command_suffix)[1:]:
        try:
            pipeline_tokens = shlex.split(pipeline_part, comments=False, posix=True)
        except ValueError:
            continue
        if _tokens_execute_shell(pipeline_tokens):
            return True
    return False


def _heredoc_body_interpreter_executes(command_prefix: str, command_suffix: str) -> bool:
    try:
        tokens = shlex.split(command_prefix, comments=False, posix=True)
    except ValueError:
        tokens = []
    if _tokens_execute_eval_stdin(tokens):
        return True
    for pipeline_part in re.split(r"\|&?", command_suffix)[1:]:
        try:
            pipeline_tokens = shlex.split(pipeline_part, comments=False, posix=True)
        except ValueError:
            continue
        if _tokens_execute_eval_stdin(pipeline_tokens):
            return True
    return False


def _tokens_execute_eval_stdin(tokens: list[str]) -> bool:
    remaining = _strip_env_prefix(tokens)
    for _ in range(4):
        if not remaining:
            return False
        base = _basename(remaining[0])
        if base in EVAL_CODE_BINS:
            return True
        if base not in COMMAND_WRAPPERS:
            return False
        remaining = _strip_env_prefix(_strip_command_wrapper(remaining))
    return False


def _runner_embedded_command_bodies(text: str) -> list[str]:
    try:
        tokens = shlex.split(text, comments=False, posix=True)
    except ValueError:
        return []
    tokens = [_decode_detection_token(token) for token in tokens]
    runner_tokens = _strip_env_prefix(tokens)
    values = _embedded_command_values(runner_tokens)
    if _tokens_start_eval_code_runner(runner_tokens):
        for value in list(values):
            values.extend(_code_string_command_bodies(value))
    return values


def _tokens_start_eval_code_runner(tokens: list[str]) -> bool:
    remaining = _strip_env_prefix(tokens)
    for _ in range(4):
        if not remaining:
            return False
        base = _basename(remaining[0])
        if base in EVAL_CODE_BINS:
            return True
        if base not in COMMAND_WRAPPERS:
            return False
        remaining = _strip_env_prefix(_strip_command_wrapper(remaining))
    return False


def _code_string_command_bodies(text: str) -> list[str]:
    code_surface = _mask_quoted_string_contents(text)
    if not _code_surface_has_process_call(code_surface):
        return []
    literals = _quoted_string_literals(_collapse_simple_string_concats(text))
    bodies = [literal for literal in literals if re.search(r"\bcodex\s+(?:exec|e)\b", literal)]
    bodies.extend(literal for literal in literals if re.search(r"(?:^|[^\w./-])(?:/[^ \t;&|]+/)?claude(?:\s|$)", literal))
    for index, literal in enumerate(literals[:-1]):
        if _basename(literal) == "codex" and literals[index + 1] in {"exec", "e"}:
            bodies.append(" ".join(literals[index : index + 3]))
        if _basename(literal) == "claude":
            bodies.append(" ".join(literals[index : index + 3]))
    for index in range(len(literals)):
        window = " ".join(literals[index : index + 6])
        if _segment_has_raw_codex_exec(window):
            bodies.append(window)
        if _segment_has_raw_claude_cli(window):
            bodies.append(window)
    joined = " ".join(literals)
    if _segment_has_raw_codex_exec(joined):
        bodies.append(joined)
    if _segment_has_raw_claude_cli(joined):
        bodies.append(joined)
    return bodies


def _code_surface_has_process_call(code_surface: str) -> bool:
    if re.search(
        r"(?:"
        r"\bsubprocess\.(?:run|call|check_call|check_output|Popen)\s*\("
        r"|\bos\.(?:exec\w*|spawn\w*|system|popen)\s*\("
        r"|\bgetattr\s*\(\s*subprocess\s*,"
        r"|\bgetattr\s*\(\s*os\s*,"
        r"|\bgetattr\s*\(\s*__import__\s*\([^)]*\)\s*,"
        r"|\b__import__\s*\([^)]*\)\s*\.\s*(?:run|call|check_call|check_output|Popen|exec\w*|spawn\w*|system|popen)\s*\("
        r"|\brequire\s*\([^)]*\)\s*(?:\.\s*)?(?:\[\s*[^]]+\s*\]|\b(?:exec|execFile|execSync|spawn|spawnSync))\s*\("
        r"|\.(?:exec|execFile|execSync|spawn|spawnSync|exec\w*|spawn\w*|system|popen)\s*\("
        r"|(?:^|[^\w.])(?:exec|execSync|popen|spawn\w*|system)\s*\("
        r"|(?:^|[^\w.])(?:exec|system)\s+"
        r")",
        code_surface,
    ):
        return True
    for alias in re.findall(r"\bimport\s+subprocess\s+as\s+([A-Za-z_][A-Za-z0-9_]*)", code_surface):
        if re.search(rf"\b{re.escape(alias)}\.(?:run|call|check_call|check_output|Popen)\s*\(", code_surface):
            return True
        if re.search(rf"\bgetattr\s*\(\s*{re.escape(alias)}\s*,", code_surface):
            return True
    for alias in re.findall(r"\bimport\s+os\s+as\s+([A-Za-z_][A-Za-z0-9_]*)", code_surface):
        if re.search(rf"\b{re.escape(alias)}\.(?:exec\w*|spawn\w*|system|popen)\s*\(", code_surface):
            return True
        if re.search(rf"\bgetattr\s*\(\s*{re.escape(alias)}\s*,", code_surface):
            return True
    imported = re.findall(r"\bfrom\s+subprocess\s+import\s+([^;\n]+)", code_surface)
    for imported_names in imported:
        for name in re.split(r"\s*,\s*", imported_names):
            parts = re.split(r"\s+as\s+", name.strip(), maxsplit=1)
            imported_name = parts[0].strip()
            call_name = parts[-1].strip()
            if imported_name in {"run", "call", "check_call", "check_output", "Popen"} and re.search(
                rf"(?<!\.)\b{re.escape(call_name)}\s*\(",
                code_surface,
            ):
                return True
    imported_os = re.findall(r"\bfrom\s+os\s+import\s+([^;\n]+)", code_surface)
    for imported_names in imported_os:
        for name in re.split(r"\s*,\s*", imported_names):
            parts = re.split(r"\s+as\s+", name.strip(), maxsplit=1)
            imported_name = parts[0].strip()
            call_name = parts[-1].strip()
            if re.fullmatch(r"(?:exec\w*|spawn\w*|system|popen)", imported_name) and re.search(
                rf"(?<!\.)\b{re.escape(call_name)}\s*\(",
                code_surface,
            ):
                return True
    return False


def _mask_quoted_string_contents(text: str) -> str:
    masked: list[str] = []
    quote = ""
    escaped = False
    for char in text:
        if quote:
            if escaped:
                masked.append(" ")
                escaped = False
                continue
            if char == "\\":
                masked.append(" ")
                escaped = True
                continue
            if char == quote:
                masked.append(char)
                quote = ""
                continue
            masked.append(" ")
            continue
        if char in {"'", '"'}:
            quote = char
            masked.append(char)
            continue
        masked.append(char)
    return "".join(masked)


SIMPLE_STRING_CONCAT_RE = re.compile(
    r"(?:'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\")"
    r"(?:\s*\+\s*(?:'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"))+",
    re.DOTALL,
)
ADJACENT_STRING_CONCAT_RE = re.compile(
    r"(?:'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\")"
    r"(?:\s+(?:'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"))+",
    re.DOTALL,
)


def _collapse_simple_string_concats(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return json.dumps("".join(_quoted_string_literals(match.group(0))))

    collapsed = SIMPLE_STRING_CONCAT_RE.sub(replace, text)
    return ADJACENT_STRING_CONCAT_RE.sub(replace, collapsed)


def _quoted_string_literals(text: str) -> list[str]:
    literals: list[str] = []
    quote = ""
    escaped = False
    current: list[str] = []
    for char in text:
        if quote:
            if escaped:
                current.append("\\" + char)
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == quote:
                literals.append(_decode_printf_escapes("".join(current)))
                quote = ""
                current = []
                continue
            current.append(char)
            continue
        if char in {"'", '"'}:
            quote = char
    for match in re.finditer(r"(?:%[qQ]|qq?|QQ)\{([^{}]*)\}", text, flags=re.DOTALL):
        literals.append(_decode_printf_escapes(match.group(1)))
    return literals


def _is_assignment(token: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", token))


def _decode_detection_token(token: str) -> str:
    if not token.startswith("$") or token.startswith(("$(", "${")):
        return token
    decoded = _decode_printf_escapes(token[1:])
    first = decoded.split(None, 1)[0] if decoded.split(None, 1) else ""
    first_base = _basename(first)
    if first_base in {"bash", "sh", "codex", "claude", "eval", "builtin", "npx"} or _is_codex_package(first) or _is_claude_package(first):
        return decoded
    if re.search(r"\bcodex\s+exec\b", decoded) or re.search(r"\bclaude(?:\s|$)", decoded):
        return decoded
    return token


def _basename(token: str) -> str:
    return os.path.basename(token)


def _consume_env_prefix(tokens: list[str]) -> tuple[list[str], dict[str, str]]:
    remaining = list(tokens)
    assignments: dict[str, str] = {}
    while remaining and _is_assignment(remaining[0]):
        key, value = remaining.pop(0).split("=", 1)
        assignments[key] = value.strip("'\"")
    if remaining and _basename(remaining[0]) == "env":
        remaining.pop(0)
        while remaining:
            token = remaining[0]
            if _is_assignment(token):
                key, value = remaining.pop(0).split("=", 1)
                assignments[key] = value.strip("'\"")
                continue
            if token in {"-i", "-0", "--ignore-environment"}:
                remaining.pop(0)
                continue
            if token == "--":
                remaining.pop(0)
                break
            if token in ENV_OPTIONS_WITH_VALUE:
                remaining = remaining[2:] if len(remaining) >= 2 else []
                continue
            if any(token.startswith(f"{option}=") for option in ENV_OPTIONS_WITH_VALUE if option.startswith("--")):
                remaining.pop(0)
                continue
            if token.startswith("-") and not token.startswith("--"):
                remaining.pop(0)
                continue
            if token.startswith("--"):
                remaining.pop(0)
                continue
            break
    return remaining, assignments


def _strip_leading_assignments(tokens: list[str]) -> list[str]:
    remaining = list(tokens)
    while remaining and _is_assignment(remaining[0]):
        remaining.pop(0)
    return remaining


def _strip_env_prefix(tokens: list[str]) -> list[str]:
    remaining, _ = _consume_env_prefix(tokens)
    if remaining and _basename(remaining[0]) == "timeout":
        remaining.pop(0)
        while remaining:
            token = remaining[0]
            if token == "--":
                remaining.pop(0)
                break
            if token in TIMEOUT_OPTIONS_WITH_VALUE:
                remaining = remaining[2:] if len(remaining) >= 2 else []
                continue
            if any(token.startswith(f"{option}=") for option in TIMEOUT_OPTIONS_WITH_VALUE if option.startswith("--")):
                remaining.pop(0)
                continue
            if token.startswith("-"):
                remaining.pop(0)
                continue
            break
        if remaining:
            remaining.pop(0)
    while remaining and _is_assignment(remaining[0]):
        remaining.pop(0)
    return remaining


def _normalize_shell_control_tokens(tokens: list[str]) -> list[str]:
    remaining = list(tokens)
    while remaining:
        first = remaining[0]
        stripped = first.lstrip("({")
        if stripped != first:
            remaining[0] = stripped
            if not stripped:
                remaining.pop(0)
                continue
        if remaining[0] in SHELL_CONTROL_PREFIX_TOKENS:
            remaining.pop(0)
            continue
        if remaining[0] == "case":
            while remaining and remaining[0] != "in":
                remaining.pop(0)
            if remaining and remaining[0] == "in":
                remaining.pop(0)
            while remaining and not remaining[0].endswith(")"):
                remaining.pop(0)
            if remaining:
                remaining.pop(0)
            continue
        if remaining[0] == "coproc":
            remaining.pop(0)
            if len(remaining) >= 2 and remaining[1].lstrip("({") != remaining[1]:
                remaining.pop(0)
            elif len(remaining) >= 2 and remaining[1] == "{":
                remaining.pop(0)
            continue
        break
    while remaining and remaining[-1] in SHELL_CONTROL_TRAILER_TOKENS:
        remaining.pop()
    if remaining and not _is_shell_parameter_expansion_token(remaining[-1]):
        remaining[-1] = remaining[-1].rstrip(")}")
        if not remaining[-1]:
            remaining.pop()
    return remaining


def _is_shell_parameter_expansion_token(token: str) -> bool:
    return bool(re.fullmatch(r"\$\{[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]+\])?\}", token))


def _leading_assignments(tokens: list[str]) -> dict[str, str]:
    _, assignments = _consume_env_prefix(tokens)
    return assignments


def _segment_has_raw_codex_exec(segment: str) -> bool:
    decoded_ansi = _decode_ansi_c_quoted_fragments(segment)
    if decoded_ansi != segment:
        return _segment_has_raw_codex_exec(decoded_ansi)
    normalized_dynamic = DYNAMIC_CODEX_SUB_RE.sub("codex", segment)
    if normalized_dynamic != segment:
        return _segment_has_raw_codex_exec(normalized_dynamic)
    for rendered in _word_substitution_renders(segment):
        if rendered != segment and _segment_has_raw_codex_exec(rendered):
            return True
    if _raw_command_word_may_expand_to_codex_exec(segment):
        return True
    if _dynamic_codex_command_substitution(segment):
        return True
    try:
        tokens = shlex.split(segment, comments=False, posix=True)
    except ValueError:
        return False
    tokens = [_decode_detection_token(token) for token in tokens]
    tokens = _normalize_shell_control_tokens(tokens)
    assignment_stripped_tokens = _strip_leading_assignments(tokens)
    stripped_tokens = _normalize_shell_control_tokens(_strip_env_prefix(tokens))
    if any(_segment_has_raw_codex_exec(value) for value in _embedded_command_values(tokens)):
        return True
    if _shell_c_passthrough_contains_raw_codex(tokens):
        return True
    if _eval_code_argv_passthrough_contains_raw_codex(tokens):
        return True
    if assignment_stripped_tokens != tokens and any(
        _segment_has_raw_codex_exec(value) for value in _embedded_command_values(assignment_stripped_tokens)
    ):
        return True
    if stripped_tokens != tokens and any(_segment_has_raw_codex_exec(value) for value in _embedded_command_values(stripped_tokens)):
        return True
    tokens = stripped_tokens
    if tokens and _basename(tokens[0]) == "codex" and _tokens_are_raw_codex_command(tokens[1:]):
        return True
    if tokens and _word_may_expand_to_codex(tokens[0]) and _tokens_are_raw_codex_command(tokens[1:]):
        return True
    if tokens and _basename(tokens[0]) == "env":
        remaining = _strip_env_prefix(tokens)
        return remaining != tokens and _segment_has_raw_codex_exec(" ".join(shlex.quote(token) for token in remaining))
    if tokens and _basename(tokens[0]) in COMMAND_WRAPPERS:
        return _segment_has_raw_codex_exec(" ".join(shlex.quote(token) for token in _strip_command_wrapper(tokens)))
    if _basename(tokens[0]) == "npx" if tokens else False:
        rest = _strip_npx_options(tokens[1:])
        return _tokens_start_raw_codex(rest)
    if tokens and _basename(tokens[0]) in {"pnpm", "yarn"}:
        rest = _strip_package_runner_options(tokens[1:])
        if len(rest) >= 2 and rest[0] == "dlx":
            return _tokens_start_raw_codex(_strip_package_runner_options(rest[1:]))
        if len(rest) >= 2 and rest[0] == "exec":
            return _tokens_start_raw_codex(_strip_package_runner_options(rest[1:]))
        return False
    if tokens and _basename(tokens[0]) == "npm":
        rest = _strip_package_runner_options(tokens[1:])
        return len(rest) >= 2 and rest[0] in {"exec", "x"} and _tokens_start_raw_codex(
            _strip_package_runner_options(rest[1:])
        )
    if _basename(tokens[0]) in {"bunx", "uvx"} if tokens else False:
        return _tokens_start_raw_codex(_strip_package_runner_options(tokens[1:]))
    if tokens and _basename(tokens[0]) == "corepack" and len(tokens) > 1:
        return _segment_has_raw_codex_exec(" ".join(shlex.quote(token) for token in tokens[1:]))
    if _basename(tokens[0]) == "xargs" if tokens else False:
        return _tokens_start_raw_codex(_strip_xargs_options(tokens[1:]))
    if _basename(tokens[0]) == "find" if tokens else False:
        return _find_exec_contains_raw_codex(tokens)
    if _basename(tokens[0]) == "parallel" if tokens else False:
        return _parallel_contains_raw_codex(tokens)
    return False


def _segment_has_raw_claude_cli(segment: str) -> bool:
    decoded_ansi = _decode_ansi_c_quoted_fragments(segment)
    if decoded_ansi != segment:
        return _segment_has_raw_claude_cli(decoded_ansi)
    normalized_dynamic = DYNAMIC_CLAUDE_SUB_RE.sub("claude", segment)
    if normalized_dynamic != segment:
        return _segment_has_raw_claude_cli(normalized_dynamic)
    for rendered in _word_substitution_renders(segment):
        if rendered != segment and _segment_has_raw_claude_cli(rendered):
            return True
    if _raw_command_word_may_expand_to_claude_cli(segment):
        return True
    if _dynamic_claude_command_substitution(segment):
        return True
    try:
        tokens = shlex.split(segment, comments=False, posix=True)
    except ValueError:
        return False
    tokens = [_decode_detection_token(token) for token in tokens]
    tokens = _normalize_shell_control_tokens(tokens)
    assignment_stripped_tokens = _strip_leading_assignments(tokens)
    stripped_tokens = _normalize_shell_control_tokens(_strip_env_prefix(tokens))
    if any(_segment_has_raw_claude_cli(value) for value in _embedded_command_values(tokens)):
        return True
    if _shell_c_passthrough_contains_raw_claude(tokens):
        return True
    if _eval_code_argv_passthrough_contains_raw_claude(tokens):
        return True
    if assignment_stripped_tokens != tokens and any(
        _segment_has_raw_claude_cli(value) for value in _embedded_command_values(assignment_stripped_tokens)
    ):
        return True
    if stripped_tokens != tokens and any(_segment_has_raw_claude_cli(value) for value in _embedded_command_values(stripped_tokens)):
        return True
    tokens = stripped_tokens
    if tokens and (_basename(tokens[0]) == "claude" or _word_may_expand_to_claude(tokens[0])):
        return True
    if tokens and _basename(tokens[0]) == "env":
        remaining = _strip_env_prefix(tokens)
        return remaining != tokens and _segment_has_raw_claude_cli(" ".join(shlex.quote(token) for token in remaining))
    if tokens and _basename(tokens[0]) in COMMAND_WRAPPERS:
        return _segment_has_raw_claude_cli(" ".join(shlex.quote(token) for token in _strip_command_wrapper(tokens)))
    if _basename(tokens[0]) == "npx" if tokens else False:
        rest = _strip_npx_options(tokens[1:])
        return _tokens_start_raw_claude(rest)
    if tokens and _basename(tokens[0]) in {"pnpm", "yarn"}:
        rest = _strip_package_runner_options(tokens[1:])
        if len(rest) >= 2 and rest[0] == "dlx":
            return _tokens_start_raw_claude(_strip_package_runner_options(rest[1:]))
        if len(rest) >= 2 and rest[0] == "exec":
            return _tokens_start_raw_claude(_strip_package_runner_options(rest[1:]))
        return False
    if tokens and _basename(tokens[0]) == "npm":
        rest = _strip_package_runner_options(tokens[1:])
        return len(rest) >= 2 and rest[0] in {"exec", "x"} and _tokens_start_raw_claude(
            _strip_package_runner_options(rest[1:])
        )
    if _basename(tokens[0]) in {"bunx", "uvx"} if tokens else False:
        return _tokens_start_raw_claude(_strip_package_runner_options(tokens[1:]))
    if tokens and _basename(tokens[0]) == "corepack" and len(tokens) > 1:
        return _segment_has_raw_claude_cli(" ".join(shlex.quote(token) for token in tokens[1:]))
    if _basename(tokens[0]) == "xargs" if tokens else False:
        return _tokens_start_raw_claude(_strip_xargs_options(tokens[1:]))
    if _basename(tokens[0]) == "find" if tokens else False:
        return _find_exec_contains_raw_claude(tokens)
    if _basename(tokens[0]) == "parallel" if tokens else False:
        return _parallel_contains_raw_claude(tokens)
    return False


def _embedded_command_values(tokens: list[str]) -> list[str]:
    if not tokens:
        return []
    base = _basename(tokens[0])
    values: list[str] = []
    if base == "npx":
        i = 1
        while i < len(tokens):
            token = tokens[i]
            if token in {"-c", "--call"} and i + 1 < len(tokens):
                _append_embedded_command_value(values, " ".join(tokens[i + 1 :]))
                break
            if token.startswith("--call="):
                _append_embedded_command_value(values, " ".join([token.split("=", 1)[1], *tokens[i + 1 :]]))
                break
            i += 1
    if base in SHELL_BINS:
        i = 1
        while i < len(tokens):
            token = tokens[i]
            if token == "-c" or (token.startswith("-") and not token.startswith("--") and "c" in token[1:]):
                script_index = i + 1
                if script_index < len(tokens) and tokens[script_index] == "--":
                    script_index += 1
                if script_index < len(tokens):
                    _append_embedded_command_value(values, _shell_script_value(tokens, script_index))
                break
            i += 1
    if base == "env":
        i = 1
        while i < len(tokens):
            token = tokens[i]
            if token in {"-S", "--split-string"} and i + 1 < len(tokens):
                _append_embedded_command_value(values, " ".join(tokens[i + 1 :]))
                break
            if token.startswith("--split-string="):
                split_value = token.split("=", 1)[1]
                _append_embedded_command_value(values, " ".join([split_value, *tokens[i + 1 :]]))
                break
            i += 1
    if base == "eval" and len(tokens) > 1:
        _append_embedded_command_value(values, " ".join(tokens[1:]))
    if base == "builtin" and len(tokens) > 2 and tokens[1] == "eval":
        _append_embedded_command_value(values, " ".join(tokens[2:]))
    if base == "script":
        i = 1
        while i < len(tokens):
            token = tokens[i]
            if token == "--":
                break
            if token in {"-c", "--command"} and i + 1 < len(tokens):
                _append_embedded_command_value(values, tokens[i + 1])
                break
            if token.startswith("--command="):
                _append_embedded_command_value(values, token.split("=", 1)[1])
                break
            if token in SCRIPT_OPTIONS_WITH_VALUE:
                i += 2
                continue
            if any(token.startswith(f"{option}=") for option in SCRIPT_OPTIONS_WITH_VALUE if option.startswith("--")):
                i += 1
                continue
            if token in SCRIPT_OPTIONS_NO_VALUE:
                i += 1
                continue
            if any(token.startswith(f"{option}=") for option in SCRIPT_OPTIONS_OPTIONAL_EQUALS_VALUE):
                i += 1
                continue
            i += 1
    if base == "watch":
        command_tokens = _strip_watch_options(tokens[1:])
        if command_tokens:
            _append_embedded_command_value(values, " ".join(command_tokens))
    if base in EVAL_CODE_BINS:
        options = EVAL_CODE_BINS[base]
        i = 1
        while i < len(tokens):
            token = tokens[i]
            if token == "--":
                break
            if token in options and i + 1 < len(tokens):
                _append_embedded_command_value(values, tokens[i + 1])
                break
            if any(token.startswith(f"{option}=") for option in options if option.startswith("--")):
                _append_embedded_command_value(values, token.split("=", 1)[1])
                break
            i += 1
    return values


def _shell_c_passthrough_contains_raw_codex(tokens: list[str]) -> bool:
    if not tokens or _basename(tokens[0]) not in SHELL_BINS:
        return False
    script_index = -1
    i = 1
    while i < len(tokens):
        token = tokens[i]
        if token == "-c" or (token.startswith("-") and not token.startswith("--") and "c" in token[1:]):
            script_index = i + 1
            if script_index < len(tokens) and tokens[script_index] == "--":
                script_index += 1
            break
        i += 1
    if script_index < 0 or script_index >= len(tokens):
        return False
    argv_tokens = tokens[script_index + 2 :]
    if not argv_tokens:
        return False

    script = tokens[script_index]
    codex_vars = _assigned_codex_vars(script)
    shell_vars: dict[str, str] = {}
    for segment in _split_shell_segments(script):
        text = segment.strip()
        if not text:
            continue
        codex_vars.update(_assigned_codex_vars(text))
        shell_vars.update(_assigned_shell_var_values(text, shell_vars))
        prefix = _argv_passthrough_prefix(text, codex_vars, shell_vars)
        if not prefix:
            continue
        if prefix == [ARGV_PASSTHROUGH_MARKER]:
            if _tokens_start_raw_codex_with_vars(argv_tokens, codex_vars) or _segment_has_raw_codex_exec(
                " ".join(shlex.quote(token) for token in argv_tokens)
            ):
                return True
            continue
        expanded = [*[_render_shell_var_word(token, shell_vars) for token in prefix], *argv_tokens]
        if _tokens_start_raw_codex_with_vars(expanded, codex_vars) or _segment_has_raw_codex_exec(
            " ".join(shlex.quote(token) for token in expanded)
        ):
            return True
    return False


def _shell_c_passthrough_contains_raw_claude(tokens: list[str]) -> bool:
    if not tokens or _basename(tokens[0]) not in SHELL_BINS:
        return False
    script_index = -1
    i = 1
    while i < len(tokens):
        token = tokens[i]
        if token == "-c" or (token.startswith("-") and not token.startswith("--") and "c" in token[1:]):
            script_index = i + 1
            if script_index < len(tokens) and tokens[script_index] == "--":
                script_index += 1
            break
        i += 1
    if script_index < 0 or script_index >= len(tokens):
        return False
    argv_tokens = tokens[script_index + 2 :]
    if not argv_tokens:
        return False

    script = tokens[script_index]
    claude_vars = _assigned_claude_vars(script)
    shell_vars: dict[str, str] = {}
    for segment in _split_shell_segments(script):
        text = segment.strip()
        if not text:
            continue
        claude_vars.update(_assigned_claude_vars(text))
        shell_vars.update(_assigned_shell_var_values(text, shell_vars))
        prefix = _argv_passthrough_prefix_for_command(text, claude_vars, shell_vars, _word_may_expand_to_claude, _tokens_are_claude_execution_prefix)
        if not prefix:
            continue
        if prefix == [ARGV_PASSTHROUGH_MARKER]:
            if _tokens_start_raw_claude_with_vars(argv_tokens, claude_vars) or _segment_has_raw_claude_cli(
                " ".join(shlex.quote(token) for token in argv_tokens)
            ):
                return True
            continue
        expanded = [*[_render_shell_var_word(token, shell_vars) for token in prefix], *argv_tokens]
        if _tokens_start_raw_claude_with_vars(expanded, claude_vars) or _segment_has_raw_claude_cli(
            " ".join(shlex.quote(token) for token in expanded)
        ):
            return True
    return False


def _eval_code_argv_passthrough_contains_raw_codex(tokens: list[str]) -> bool:
    if not tokens:
        return False
    base = _basename(tokens[0])
    if base not in EVAL_CODE_BINS:
        return False
    code_index = -1
    options = EVAL_CODE_BINS[base]
    i = 1
    while i < len(tokens):
        token = tokens[i]
        if token == "--":
            break
        if token in options and i + 1 < len(tokens):
            code_index = i + 1
            break
        if any(token.startswith(f"{option}=") for option in options if option.startswith("--")):
            code_index = i
            break
        i += 1
    if code_index < 0:
        return False
    code = tokens[code_index].split("=", 1)[1] if tokens[code_index].startswith("--") else tokens[code_index]
    argv_tokens = tokens[code_index + 1 :]
    if not argv_tokens:
        return False
    if base in {"python", "python3"}:
        surface = _mask_quoted_string_contents(code)
        if "sys.argv[1:]" not in code or not _code_surface_has_process_call(surface):
            return False
        argv_segment = " ".join(shlex.quote(token) for token in argv_tokens)
        if _segment_has_raw_codex_exec(argv_segment):
            return True
        return bool(_tokens_are_raw_codex_command(argv_tokens) and re.search(r"['\"]codex['\"]", code))
    return False


def _eval_code_argv_passthrough_contains_raw_claude(tokens: list[str]) -> bool:
    if not tokens:
        return False
    base = _basename(tokens[0])
    if base not in EVAL_CODE_BINS:
        return False
    code_index = -1
    options = EVAL_CODE_BINS[base]
    i = 1
    while i < len(tokens):
        token = tokens[i]
        if token == "--":
            break
        if token in options and i + 1 < len(tokens):
            code_index = i + 1
            break
        if any(token.startswith(f"{option}=") for option in options if option.startswith("--")):
            code_index = i
            break
        i += 1
    if code_index < 0:
        return False
    code = tokens[code_index].split("=", 1)[1] if tokens[code_index].startswith("--") else tokens[code_index]
    argv_tokens = tokens[code_index + 1 :]
    if not argv_tokens:
        return False
    if base in {"python", "python3"}:
        surface = _mask_quoted_string_contents(code)
        if "sys.argv[1:]" not in code or not _code_surface_has_process_call(surface):
            return False
        argv_segment = " ".join(shlex.quote(token) for token in argv_tokens)
        if _segment_has_raw_claude_cli(argv_segment):
            return True
        return bool(_tokens_start_raw_claude(argv_tokens) and re.search(r"['\"]claude['\"]", code))
    return False


def _argv_passthrough_prefix(segment: str, codex_vars: set[str], shell_vars: dict[str, str]) -> list[str]:
    try:
        tokens = [_decode_detection_token(token) for token in shlex.split(segment, comments=False, posix=True)]
    except ValueError:
        return []
    if not tokens:
        return []
    passthrough_indexes = [index for index, token in enumerate(tokens) if token in {"$@", "$*"}]
    if not passthrough_indexes:
        return []
    first_passthrough = min(passthrough_indexes)
    prefix = tokens[:first_passthrough]
    if not prefix:
        return [ARGV_PASSTHROUGH_MARKER]
    if _tokens_execute_argv_passthrough(prefix):
        return [ARGV_PASSTHROUGH_MARKER]
    stripped = _strip_wrappers_for_command_detection(prefix)
    if not stripped:
        return []
    command = stripped[0]
    rendered = _render_shell_var_word(command, shell_vars)
    if (
        _word_may_expand_to_codex(command)
        or _token_references_codex_var(command, codex_vars)
        or _basename(rendered) == "codex"
        or _tokens_are_codex_execution_prefix(prefix)
    ):
        return prefix
    return []


def _argv_passthrough_prefix_for_command(
    segment: str,
    command_vars: set[str],
    shell_vars: dict[str, str],
    word_detector: Any,
    prefix_detector: Any,
) -> list[str]:
    try:
        tokens = [_decode_detection_token(token) for token in shlex.split(segment, comments=False, posix=True)]
    except ValueError:
        return []
    if not tokens:
        return []
    passthrough_indexes = [index for index, token in enumerate(tokens) if token in {"$@", "$*"}]
    if not passthrough_indexes:
        return []
    first_passthrough = min(passthrough_indexes)
    prefix = tokens[:first_passthrough]
    if not prefix:
        return [ARGV_PASSTHROUGH_MARKER]
    if _tokens_execute_argv_passthrough(prefix):
        return [ARGV_PASSTHROUGH_MARKER]
    stripped = _strip_wrappers_for_command_detection(prefix)
    if not stripped:
        return []
    command = stripped[0]
    rendered = _render_shell_var_word(command, shell_vars)
    if (
        word_detector(command)
        or any(_command_references_var(command, name) for name in command_vars)
        or prefix_detector(prefix)
        or word_detector(rendered)
    ):
        return prefix
    return []


def _strip_command_wrapper(tokens: list[str]) -> list[str]:
    remaining = tokens[1:]
    wrapper = _basename(tokens[0])
    if wrapper == "nice":
        while remaining and remaining[0].startswith("-"):
            option = remaining.pop(0)
            if option in {"-n", "--adjustment"} and remaining:
                remaining.pop(0)
    elif wrapper in {"command", "setsid"}:
        while remaining and remaining[0].startswith("-"):
            remaining.pop(0)
    elif wrapper == "exec":
        while remaining and remaining[0].startswith("-"):
            option = remaining.pop(0)
            if option == "--":
                break
            if option == "-a" and remaining:
                remaining.pop(0)
    elif wrapper == "nohup":
        if remaining and remaining[0] == "--":
            remaining.pop(0)
    elif wrapper == "time":
        while remaining and remaining[0].startswith("-"):
            option = remaining.pop(0)
            if option in TIME_WRAPPER_OPTIONS_WITH_VALUE and remaining:
                remaining.pop(0)
                continue
            if any(
                option.startswith(f"{option_with_value}=")
                for option_with_value in TIME_WRAPPER_OPTIONS_WITH_VALUE
                if option_with_value.startswith("--")
            ):
                continue
    elif wrapper in {"sudo", "doas"}:
        while remaining and remaining[0].startswith("-"):
            option = remaining.pop(0)
            if option in SUDO_OPTIONS_WITH_VALUE and remaining:
                remaining.pop(0)
    elif wrapper == "stdbuf":
        while remaining and remaining[0].startswith("-"):
            option = remaining.pop(0)
            if option in {"-i", "-o", "-e", "--input", "--output", "--error"} and remaining:
                remaining.pop(0)
    elif wrapper == "flock":
        while remaining and remaining[0].startswith("-"):
            option = remaining.pop(0)
            if option in {"-c", "--command"} and remaining:
                return ["bash", "-c", remaining.pop(0)]
            if option.startswith("--command="):
                return ["bash", "-c", option.split("=", 1)[1]]
            if option in {"-E", "--conflict-exit-code"} and remaining:
                remaining.pop(0)
        if remaining:
            remaining.pop(0)
        if remaining and remaining[0] in {"-c", "--command"}:
            remaining.pop(0)
            if remaining:
                return ["bash", "-c", remaining.pop(0)]
        if remaining and remaining[0].startswith("--command="):
            return ["bash", "-c", remaining.pop(0).split("=", 1)[1]]
    elif wrapper == "ionice":
        while remaining and remaining[0].startswith("-"):
            option = remaining.pop(0)
            if option in {"-c", "--class", "-n", "--classdata", "-p", "--pid", "-P", "--pgid", "-u", "--uid"} and remaining:
                remaining.pop(0)
    elif wrapper == "chrt":
        while remaining and remaining[0].startswith("-"):
            option = remaining.pop(0)
            if option in {"-p", "--pid", "-R", "--reset-on-fork", "-m", "--max"}:
                continue
        if remaining and re.fullmatch(r"[0-9]+", remaining[0]):
            remaining.pop(0)
    elif wrapper in {"rlwrap", "unbuffer"}:
        while remaining and remaining[0].startswith("-"):
            option = remaining.pop(0)
            if option in {"-a", "-A", "-b", "-c", "-C", "-f", "-g", "-h", "-H", "-i", "-I", "-l", "-m", "-O", "-p", "-P", "-q", "-r", "-s", "-S", "-t"} and remaining:
                remaining.pop(0)
    elif wrapper == "xvfb-run":
        while remaining and remaining[0].startswith("-"):
            option = remaining.pop(0)
            if option in {"-e", "-f", "-n", "-s", "-w", "--error-file", "--auth-file", "--server-num", "--server-args", "--wait"} and remaining:
                remaining.pop(0)
    return remaining


def _dynamic_codex_command_substitution(segment: str) -> bool:
    return bool(
        re.search(rf"(?:\$\(\s*{DYNAMIC_CODEX_LOOKUP}\s*\)|`\s*{DYNAMIC_CODEX_LOOKUP}\s*`)\s+exec\b", segment)
    )


def _dynamic_claude_command_substitution(segment: str) -> bool:
    return bool(re.search(rf"(?:\$\(\s*{DYNAMIC_CLAUDE_LOOKUP}\s*\)|`\s*{DYNAMIC_CLAUDE_LOOKUP}\s*`)(?:\s|$)", segment))


def _assigned_codex_vars(segment: str) -> set[str]:
    assigned: set[str] = set()
    i = 0
    while i < len(segment):
        while i < len(segment) and segment[i].isspace():
            i += 1
        read = _read_shell_word(segment, i)
        if not read:
            break
        word, end = read
        parsed = _split_shell_assignment_word(word)
        if parsed:
            key, _, value = parsed
            if _word_may_expand_to_codex(value):
                assigned.add(key)
        i = end
    pattern = re.compile(r"(?:^|\s)([A-Za-z_][A-Za-z0-9_]*)=('[^']*'|\"[^\"]*\"|\$\([^)]*\)|`[^`]*`|[^ \t;&|]+)")
    for match in pattern.finditer(segment):
        value = match.group(2)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if _word_may_expand_to_codex(value) or re.fullmatch(
            rf"(?:\$\(\s*{DYNAMIC_CODEX_LOOKUP}\s*\)|`\s*{DYNAMIC_CODEX_LOOKUP}\s*`)", value
        ) or re.fullmatch(
            r"(?:/[^ \t;&|]+/)?codex", value
        ):
            assigned.add(match.group(1))
    return assigned


def _assigned_claude_vars(segment: str) -> set[str]:
    assigned: set[str] = set()
    i = 0
    while i < len(segment):
        while i < len(segment) and segment[i].isspace():
            i += 1
        read = _read_shell_word(segment, i)
        if not read:
            break
        word, end = read
        parsed = _split_shell_assignment_word(word)
        if parsed:
            key, _, value = parsed
            if _word_may_expand_to_claude(value):
                assigned.add(key)
        i = end
    pattern = re.compile(r"(?:^|\s)([A-Za-z_][A-Za-z0-9_]*)=('[^']*'|\"[^\"]*\"|\$\([^)]*\)|`[^`]*`|[^ \t;&|]+)")
    for match in pattern.finditer(segment):
        value = match.group(2)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if _word_may_expand_to_claude(value) or re.fullmatch(
            rf"(?:\$\(\s*{DYNAMIC_CLAUDE_LOOKUP}\s*\)|`\s*{DYNAMIC_CLAUDE_LOOKUP}\s*`)", value
        ) or re.fullmatch(
            r"(?:/[^ \t;&|]+/)?claude", value
        ):
            assigned.add(match.group(1))
    return assigned


def _assigned_shell_var_values(segment: str, shell_vars: dict[str, str] | None = None) -> dict[str, str]:
    known_values = dict(shell_vars or {})
    assigned: dict[str, str] = {}
    i = 0
    while i < len(segment):
        while i < len(segment) and segment[i].isspace():
            i += 1
        read = _read_shell_word(segment, i)
        if not read:
            break
        word, end = read
        parsed = _split_shell_assignment_word(word)
        if not parsed:
            i = end
            continue
        key, operator, value = parsed
        rendered_value = _render_shell_assignment_value(value, known_values)
        if operator == "+=":
            rendered_value = known_values.get(key, "") + rendered_value
        known_values[key] = rendered_value
        assigned[key] = rendered_value
        i = end
    assigned.update(_printf_v_shell_var_values(segment, known_values))
    return assigned


def _printf_v_shell_var_values(segment: str, shell_vars: dict[str, str]) -> dict[str, str]:
    try:
        tokens = shlex.split(segment, comments=False, posix=True)
    except ValueError:
        return {}
    if len(tokens) < 4 or _basename(tokens[0]) != "printf" or tokens[1] != "-v":
        return {}
    name = tokens[2]
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        return {}
    # The guard only needs conservative command-word rendering. For simple
    # printf -v NAME %s value assignments, use the last argument as NAME.
    return {name: _render_shell_var_word(tokens[-1], shell_vars)}


def _assigned_shell_array_values(
    segment: str,
    shell_vars: dict[str, str] | None = None,
    shell_arrays: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    known_arrays = dict(shell_arrays or {})
    assigned: dict[str, list[str]] = {}
    for name, operator, body in _iter_shell_array_assignments(segment):
        values = _render_shell_array_body(body, shell_vars or {})
        if not values:
            continue
        if operator == "+=":
            values = [*known_arrays.get(name, []), *values]
        known_arrays[name] = values
        assigned[name] = values
    return assigned


def _iter_shell_array_assignments(segment: str) -> list[tuple[str, str, str]]:
    assignments: list[tuple[str, str, str]] = []
    pattern = re.compile(r"(?<![A-Za-z0-9_])([A-Za-z_][A-Za-z0-9_]*)(\+?=)\(")
    for match in pattern.finditer(segment):
        end = _matching_shell_paren(segment, match.end() - 1)
        if end is None:
            continue
        assignments.append((match.group(1), match.group(2), segment[match.end() : end]))
    return assignments


def _matching_shell_paren(text: str, open_index: int) -> int | None:
    depth = 1
    quote = ""
    escaped = False
    i = open_index + 1
    while i < len(text):
        char = text[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if char == "\\":
            escaped = True
            i += 1
            continue
        if quote:
            if char == quote:
                quote = ""
            i += 1
            continue
        if char in {"'", '"', "`"}:
            quote = char
            i += 1
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def _render_shell_array_body(body: str, shell_vars: dict[str, str]) -> list[str]:
    normalized = DYNAMIC_CODEX_SUB_RE.sub("codex", body)
    normalized = DYNAMIC_CLAUDE_SUB_RE.sub("claude", normalized)
    rendered = _render_shell_var_word(normalized, shell_vars)
    try:
        return [_decode_detection_token(token) for token in shlex.split(rendered, comments=False, posix=True)]
    except ValueError:
        return []


def _render_shell_assignment_value(value: str, shell_vars: dict[str, str]) -> str:
    rendered = _render_shell_var_word(_strip_outer_shell_quotes(value), shell_vars)
    try:
        parts = shlex.split(rendered, comments=False, posix=True)
    except ValueError:
        return _strip_outer_shell_quotes(rendered)
    if len(parts) == 1:
        return parts[0]
    return _strip_outer_shell_quotes(rendered)


def _segment_uses_codex_var(segment: str, codex_vars: set[str]) -> bool:
    if not codex_vars:
        return False
    try:
        tokens = shlex.split(segment, comments=False, posix=True)
    except ValueError:
        return False
    tokens = _strip_wrappers_for_command_detection(_normalize_shell_control_tokens(tokens))
    if len(tokens) < 2:
        return False
    command = tokens[0]
    if not any(_command_references_codex_var(command, name) for name in codex_vars):
        return False
    return _tokens_are_raw_codex_command(tokens[1:])


def _segment_uses_claude_var(segment: str, claude_vars: set[str]) -> bool:
    if not claude_vars:
        return False
    try:
        tokens = shlex.split(segment, comments=False, posix=True)
    except ValueError:
        return False
    tokens = _strip_wrappers_for_command_detection(_normalize_shell_control_tokens(tokens))
    if not tokens:
        return False
    command = tokens[0]
    return any(_command_references_var(command, name) for name in claude_vars)


def _segment_uses_codex_var_package_runner(segment: str, codex_vars: set[str]) -> bool:
    if not codex_vars:
        return False
    try:
        tokens = [_decode_detection_token(token) for token in shlex.split(segment, comments=False, posix=True)]
    except ValueError:
        return False
    tokens = _strip_wrappers_for_command_detection(_normalize_shell_control_tokens(tokens))
    if not tokens:
        return False
    base = _basename(tokens[0])
    if base == "npx":
        return _tokens_start_raw_codex_with_vars(_strip_npx_options(tokens[1:]), codex_vars)
    if base in {"pnpm", "yarn"}:
        rest = _strip_package_runner_options(tokens[1:])
        if len(rest) >= 2 and rest[0] == "dlx":
            return _tokens_start_raw_codex_with_vars(_strip_package_runner_options(rest[1:]), codex_vars)
        if len(rest) >= 2 and rest[0] == "exec":
            return _tokens_start_raw_codex_with_vars(_strip_package_runner_options(rest[1:]), codex_vars)
        return False
    if base == "npm":
        rest = _strip_package_runner_options(tokens[1:])
        return len(rest) >= 2 and rest[0] in {"exec", "x"} and _tokens_start_raw_codex_with_vars(
            _strip_package_runner_options(rest[1:]), codex_vars
        )
    if base in {"bunx", "uvx"}:
        return _tokens_start_raw_codex_with_vars(_strip_package_runner_options(tokens[1:]), codex_vars)
    return False


def _segment_uses_claude_var_package_runner(segment: str, claude_vars: set[str]) -> bool:
    if not claude_vars:
        return False
    try:
        tokens = [_decode_detection_token(token) for token in shlex.split(segment, comments=False, posix=True)]
    except ValueError:
        return False
    tokens = _strip_wrappers_for_command_detection(_normalize_shell_control_tokens(tokens))
    if not tokens:
        return False
    base = _basename(tokens[0])
    if base == "npx":
        return _tokens_start_raw_claude_with_vars(_strip_npx_options(tokens[1:]), claude_vars)
    if base in {"pnpm", "yarn"}:
        rest = _strip_package_runner_options(tokens[1:])
        if len(rest) >= 2 and rest[0] == "dlx":
            return _tokens_start_raw_claude_with_vars(_strip_package_runner_options(rest[1:]), claude_vars)
        if len(rest) >= 2 and rest[0] == "exec":
            return _tokens_start_raw_claude_with_vars(_strip_package_runner_options(rest[1:]), claude_vars)
        return False
    if base == "npm":
        rest = _strip_package_runner_options(tokens[1:])
        return len(rest) >= 2 and rest[0] in {"exec", "x"} and _tokens_start_raw_claude_with_vars(
            _strip_package_runner_options(rest[1:]), claude_vars
        )
    if base in {"bunx", "uvx"}:
        return _tokens_start_raw_claude_with_vars(_strip_package_runner_options(tokens[1:]), claude_vars)
    return False


def _segment_uses_codex_array(segment: str, shell_arrays: dict[str, list[str]]) -> bool:
    expanded = _expand_shell_array_command_tokens(segment, shell_arrays)
    if not expanded:
        return False
    expanded_segment = " ".join(shlex.quote(token) for token in expanded)
    return _tokens_start_raw_codex(expanded) or _segment_has_raw_codex_exec(expanded_segment)


def _segment_uses_claude_array(segment: str, shell_arrays: dict[str, list[str]]) -> bool:
    expanded = _expand_shell_array_command_tokens(segment, shell_arrays)
    if not expanded:
        return False
    expanded_segment = " ".join(shlex.quote(token) for token in expanded)
    return _tokens_start_raw_claude(expanded) or _segment_has_raw_claude_cli(expanded_segment)


def _segment_renders_to_raw_codex(
    segment: str,
    shell_vars: dict[str, str],
    shell_arrays: dict[str, list[str]],
) -> bool:
    rendered = _render_shell_expansions(segment, shell_vars, shell_arrays)
    return rendered != segment and _segment_has_raw_codex_exec(rendered)


def _segment_renders_to_raw_claude(
    segment: str,
    shell_vars: dict[str, str],
    shell_arrays: dict[str, list[str]],
) -> bool:
    rendered = _render_shell_expansions(segment, shell_vars, shell_arrays)
    return rendered != segment and _segment_has_raw_claude_cli(rendered)


def _render_shell_expansions(
    text: str,
    shell_vars: dict[str, str],
    shell_arrays: dict[str, list[str]],
) -> str:
    rendered = _render_shell_array_refs(text, shell_arrays)
    return _render_shell_var_word(rendered, shell_vars)


def _render_shell_array_refs(text: str, shell_arrays: dict[str, list[str]]) -> str:
    if not shell_arrays:
        return text

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        index = match.group(2) or match.group(3)
        values = shell_arrays.get(name)
        if not values:
            return match.group(0)
        if index in {"@", "*"}:
            return " ".join(values)
        if index is None:
            return values[0]
        try:
            offset = int(index)
        except ValueError:
            return match.group(0)
        return values[offset] if 0 <= offset < len(values) else ""

    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?:\[(?:([@*])|([0-9]+))\])?\}", replace, text)


def _expand_shell_array_command_tokens(segment: str, shell_arrays: dict[str, list[str]]) -> list[str]:
    if not shell_arrays:
        return []
    try:
        tokens = [_decode_detection_token(token) for token in shlex.split(segment, comments=False, posix=True)]
    except ValueError:
        return []
    tokens = _strip_wrappers_for_command_detection(_normalize_shell_control_tokens(tokens))
    if not tokens:
        return []
    array_name = _array_expansion_name(tokens[0])
    if not array_name or array_name not in shell_arrays:
        return []
    values = shell_arrays[array_name]
    if not values:
        return []
    if _array_expands_all(tokens[0]):
        return [*values, *tokens[1:]]
    return [values[0], *tokens[1:]]


def _array_expansion_name(token: str) -> str | None:
    match = re.fullmatch(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?:\[(?:@|\*|[0-9]+)\])?\}", token)
    if match:
        return match.group(1)
    match = re.fullmatch(r"\$([A-Za-z_][A-Za-z0-9_]*)", token)
    if match:
        return match.group(1)
    return None


def _array_expands_all(token: str) -> bool:
    return bool(re.fullmatch(r"\$\{[A-Za-z_][A-Za-z0-9_]*\[(?:@|\*)\]\}", token))


def _segment_uses_codex_fragment_vars(segment: str, shell_vars: dict[str, str]) -> bool:
    if not shell_vars:
        return False
    try:
        tokens = shlex.split(segment, comments=False, posix=True)
    except ValueError:
        return False
    tokens = _strip_wrappers_for_command_detection(_normalize_shell_control_tokens(tokens))
    if len(tokens) < 2:
        return False
    rendered = _render_shell_var_word(tokens[0], shell_vars)
    if _basename(rendered) != "codex":
        return False
    return _tokens_are_raw_codex_command(tokens[1:])


def _segment_uses_claude_fragment_vars(segment: str, shell_vars: dict[str, str]) -> bool:
    if not shell_vars:
        return False
    try:
        tokens = shlex.split(segment, comments=False, posix=True)
    except ValueError:
        return False
    tokens = _strip_wrappers_for_command_detection(_normalize_shell_control_tokens(tokens))
    if not tokens:
        return False
    rendered = _render_shell_var_word(tokens[0], shell_vars)
    return _basename(rendered) == "claude"


def _strip_wrappers_for_command_detection(tokens: list[str]) -> list[str]:
    remaining = _strip_leading_assignments(tokens)
    for _ in range(6):
        stripped = _strip_env_prefix(remaining)
        if stripped != remaining:
            remaining = _strip_leading_assignments(stripped)
            continue
        if remaining and _basename(remaining[0]) in COMMAND_WRAPPERS:
            remaining = _strip_leading_assignments(_strip_env_prefix(_strip_command_wrapper(remaining)))
            continue
        return remaining
    return remaining


def _render_shell_var_word(word: str, shell_vars: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        if token.startswith("${") and token.endswith("}"):
            name = token[2:-1].split(":", 1)[0]
        else:
            name = token[1:]
        return shell_vars.get(name, token)

    return SHELL_PARAM_EXPANSION_RE.sub(replace, word)


def _command_references_codex_var(command: str, name: str) -> bool:
    return _command_references_var(command, name)


def _command_references_var(command: str, name: str) -> bool:
    if command in {f"${name}", f"${{{name}}}"}:
        return True
    return bool(re.fullmatch(rf"\$\{{{re.escape(name)}(?::?[-=+?][^}}]*)?\}}", command))


def _is_codex_package(token: str) -> bool:
    return token in {"codex", "@openai/codex"} or token.startswith("codex@") or token.startswith("@openai/codex@")


def _is_claude_package(token: str) -> bool:
    return token in {"claude", "@anthropic-ai/claude-code"} or token.startswith("claude@") or token.startswith(
        "@anthropic-ai/claude-code@"
    )


def _token_references_codex_var(token: str, codex_vars: set[str]) -> bool:
    return any(_command_references_codex_var(token, name) for name in codex_vars)


def _token_references_var(token: str, command_vars: set[str]) -> bool:
    return any(_command_references_var(token, name) for name in command_vars)


def _tokens_start_raw_codex(tokens: list[str]) -> bool:
    if len(tokens) < 2 or not _is_codex_package(tokens[0]):
        return False
    if _tokens_are_raw_codex_command(tokens[1:]):
        return True
    return len(tokens) >= 3 and tokens[1] == "codex" and _tokens_are_raw_codex_command(tokens[2:])


def _tokens_start_raw_claude(tokens: list[str]) -> bool:
    if not tokens:
        return False
    if _is_claude_package(tokens[0]):
        return True
    return len(tokens) >= 2 and _is_claude_package(tokens[0]) and tokens[1] == "claude"


def _tokens_start_raw_codex_with_vars(tokens: list[str], codex_vars: set[str]) -> bool:
    if len(tokens) < 2:
        return False
    if _tokens_start_raw_codex(tokens):
        return True
    if not (_is_codex_package(tokens[0]) or _token_references_codex_var(tokens[0], codex_vars)):
        return False
    if _tokens_are_raw_codex_command(tokens[1:]):
        return True
    return len(tokens) >= 3 and tokens[1] == "codex" and _tokens_are_raw_codex_command(tokens[2:])


def _tokens_start_raw_claude_with_vars(tokens: list[str], claude_vars: set[str]) -> bool:
    if not tokens:
        return False
    return _tokens_start_raw_claude(tokens) or _token_references_var(tokens[0], claude_vars)


def _tokens_are_codex_execution_prefix(tokens: list[str]) -> bool:
    remaining = _strip_wrappers_for_command_detection(_normalize_shell_control_tokens(tokens))
    if not remaining:
        return False
    base = _basename(remaining[0])
    if _word_may_expand_to_codex(remaining[0]):
        return True
    if base == "npx":
        rest = _strip_npx_options(remaining[1:])
        return bool(rest and _is_codex_package(rest[0]))
    if base in {"pnpm", "yarn"}:
        rest = _strip_package_runner_options(remaining[1:])
        if len(rest) >= 2 and rest[0] in {"dlx", "exec"}:
            stripped = _strip_package_runner_options(rest[1:])
            return bool(stripped and _is_codex_package(stripped[0]))
        return False
    if base == "npm":
        rest = _strip_package_runner_options(remaining[1:])
        if len(rest) >= 2 and rest[0] in {"exec", "x"}:
            stripped = _strip_package_runner_options(rest[1:])
            return bool(stripped and _is_codex_package(stripped[0]))
        return False
    if base in {"bunx", "uvx"}:
        rest = _strip_package_runner_options(remaining[1:])
        return bool(rest and _is_codex_package(rest[0]))
    return False


def _tokens_are_claude_execution_prefix(tokens: list[str]) -> bool:
    remaining = _strip_wrappers_for_command_detection(_normalize_shell_control_tokens(tokens))
    if not remaining:
        return False
    base = _basename(remaining[0])
    if _word_may_expand_to_claude(remaining[0]):
        return True
    if base == "npx":
        rest = _strip_npx_options(remaining[1:])
        return bool(rest and _is_claude_package(rest[0]))
    if base in {"pnpm", "yarn"}:
        rest = _strip_package_runner_options(remaining[1:])
        if len(rest) >= 2 and rest[0] in {"dlx", "exec"}:
            stripped = _strip_package_runner_options(rest[1:])
            return bool(stripped and _is_claude_package(stripped[0]))
        return False
    if base == "npm":
        rest = _strip_package_runner_options(remaining[1:])
        if len(rest) >= 2 and rest[0] in {"exec", "x"}:
            stripped = _strip_package_runner_options(rest[1:])
            return bool(stripped and _is_claude_package(stripped[0]))
        return False
    if base in {"bunx", "uvx"}:
        rest = _strip_package_runner_options(remaining[1:])
        return bool(rest and _is_claude_package(rest[0]))
    return False


def _tokens_are_raw_codex_command(tokens: list[str]) -> bool:
    rest = _strip_codex_options(tokens)
    return bool(rest and (rest[0] in {"exec", "e"} or _token_may_expand_to_codex_exec_subcommand(rest[0])))


def _token_may_expand_to_codex_exec_subcommand(token: str) -> bool:
    return "$" in token or "`" in token


def _strip_codex_options(tokens: list[str]) -> list[str]:
    remaining = list(tokens)
    while remaining:
        token = remaining[0]
        if token == "--":
            return remaining[1:]
        if token in CODEX_OPTIONS_WITH_VALUE:
            remaining = remaining[2:] if len(remaining) >= 2 else []
            continue
        if token in CODEX_OPTIONS_NO_VALUE:
            remaining = remaining[1:]
            continue
        if any(token.startswith(f"{option}=") for option in CODEX_OPTIONS_WITH_VALUE if option.startswith("--")):
            remaining = remaining[1:]
            continue
        if token.startswith("-"):
            remaining = remaining[1:]
            continue
        break
    return remaining


def _strip_package_runner_options(tokens: list[str]) -> list[str]:
    remaining = list(tokens)
    while remaining:
        token = remaining[0]
        if token == "--":
            return remaining[1:]
        if token in PACKAGE_RUNNER_OPTIONS_WITH_VALUE:
            remaining = remaining[2:] if len(remaining) >= 2 else []
            continue
        if token in PACKAGE_RUNNER_OPTIONS_NO_VALUE:
            remaining = remaining[1:]
            continue
        if any(token.startswith(f"{option}=") for option in PACKAGE_RUNNER_OPTIONS_WITH_VALUE if option.startswith("--")):
            remaining = remaining[1:]
            continue
        if token.startswith("-"):
            remaining = remaining[1:]
            continue
        break
    return remaining


def _strip_npx_options(tokens: list[str]) -> list[str]:
    remaining = list(tokens)
    while remaining:
        token = remaining[0]
        if token in NPX_OPTIONS_WITH_VALUE:
            remaining = remaining[2:] if len(remaining) >= 2 else []
            continue
        if any(token.startswith(f"{option}=") for option in NPX_OPTIONS_WITH_VALUE if option.startswith("--")):
            remaining = remaining[1:]
            continue
        if token.startswith("-"):
            remaining = remaining[1:]
            continue
        break
    return remaining


def _strip_xargs_options(tokens: list[str]) -> list[str]:
    remaining = list(tokens)
    while remaining:
        token = remaining[0]
        if token == "--":
            return remaining[1:]
        if token in XARGS_OPTIONS_NO_VALUE:
            remaining = remaining[1:]
            continue
        if token in XARGS_OPTIONS_WITH_VALUE:
            remaining = remaining[2:] if len(remaining) >= 2 else []
            continue
        if any(token.startswith(f"{option}=") for option in XARGS_OPTIONS_WITH_VALUE if option.startswith("--")):
            remaining = remaining[1:]
            continue
        if token.startswith("-"):
            remaining = remaining[1:]
            continue
        break
    return remaining


def _strip_watch_options(tokens: list[str]) -> list[str]:
    remaining = list(tokens)
    while remaining:
        token = remaining[0]
        if token == "--":
            return remaining[1:]
        if token in WATCH_OPTIONS_WITH_VALUE:
            remaining = remaining[2:] if len(remaining) >= 2 else []
            continue
        if any(token.startswith(f"{option}=") for option in WATCH_OPTIONS_WITH_VALUE if option.startswith("--")):
            remaining = remaining[1:]
            continue
        if any(token.startswith(f"{option}=") for option in WATCH_OPTIONS_OPTIONAL_EQUALS_VALUE):
            remaining = remaining[1:]
            continue
        if token in WATCH_OPTIONS_NO_VALUE:
            remaining = remaining[1:]
            continue
        if token.startswith("-"):
            remaining = remaining[1:]
            continue
        break
    return remaining


def _find_exec_contains_raw_codex(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if token in {"-exec", "-execdir", "-ok", "-okdir"}:
            rest = tokens[index + 1 :]
            command_tokens: list[str] = []
            for rest_token in rest:
                if rest_token in {";", "\\;", "+"}:
                    break
                command_tokens.append(rest_token)
            if _tokens_start_raw_codex(command_tokens) or _segment_has_raw_codex_exec(
                " ".join(shlex.quote(rest_token) for rest_token in command_tokens)
            ):
                return True
    return False


def _find_exec_contains_raw_claude(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if token in {"-exec", "-execdir", "-ok", "-okdir"}:
            rest = tokens[index + 1 :]
            command_tokens: list[str] = []
            for rest_token in rest:
                if rest_token in {";", "\\;", "+"}:
                    break
                command_tokens.append(rest_token)
            if _tokens_start_raw_claude(command_tokens) or _segment_has_raw_claude_cli(
                " ".join(shlex.quote(rest_token) for rest_token in command_tokens)
            ):
                return True
    return False


def _parallel_contains_raw_codex(tokens: list[str]) -> bool:
    command_tokens: list[str] = []
    for token in _strip_parallel_options(tokens[1:]):
        if token == ":::":
            break
        command_tokens.append(token)
    if not command_tokens:
        return False
    return _tokens_start_raw_codex(command_tokens) or _segment_has_raw_codex_exec(
        " ".join(shlex.quote(token) for token in command_tokens)
    )


def _parallel_contains_raw_claude(tokens: list[str]) -> bool:
    command_tokens: list[str] = []
    for token in _strip_parallel_options(tokens[1:]):
        if token == ":::":
            break
        command_tokens.append(token)
    if not command_tokens:
        return False
    return _tokens_start_raw_claude(command_tokens) or _segment_has_raw_claude_cli(
        " ".join(shlex.quote(token) for token in command_tokens)
    )


def _strip_parallel_options(tokens: list[str]) -> list[str]:
    remaining = list(tokens)
    while remaining:
        token = remaining[0]
        if token == "--":
            return remaining[1:]
        if token in PARALLEL_OPTIONS_WITH_VALUE:
            remaining = remaining[2:] if len(remaining) >= 2 else []
            continue
        if any(token.startswith(f"{option}=") for option in PARALLEL_OPTIONS_WITH_VALUE if option.startswith("--")):
            remaining.pop(0)
            continue
        if re.fullmatch(r"-j[0-9]+", token):
            remaining.pop(0)
            continue
        if token in PARALLEL_OPTIONS_NO_VALUE:
            remaining.pop(0)
            continue
        if token.startswith("-"):
            remaining.pop(0)
            continue
        break
    return remaining


def raw_codex_segments(command: str) -> list[str]:
    segments: list[str] = []
    command_codex_vars = _assigned_codex_vars(command)
    command_codex_aliases = _codex_aliases(command)
    command_codex_functions = _codex_passthrough_functions(command)
    for surface in _iter_command_surfaces(command):
        codex_vars: set[str] = set(command_codex_vars)
        shell_vars: dict[str, str] = {}
        shell_arrays: dict[str, list[str]] = {}
        codex_aliases: dict[str, list[str]] = dict(command_codex_aliases)
        codex_functions: dict[str, list[str]] = dict(command_codex_functions)
        codex_aliases.update(_codex_aliases(surface))
        codex_functions.update(_codex_passthrough_functions(surface))
        for segment in _split_shell_segments(surface):
            text = segment.strip()
            codex_vars.update(_assigned_codex_vars(text))
            shell_vars.update(_assigned_shell_var_values(text, shell_vars))
            shell_arrays.update(_assigned_shell_array_values(text, shell_vars, shell_arrays))
            codex_aliases.update(_codex_aliases(text))
            codex_functions.update(_codex_passthrough_functions(text))
            embedded_uses_codex_var = any(
                _segment_uses_codex_var(value, codex_vars) for value in _runner_embedded_command_bodies(text)
            )
            embedded_uses_codex_fragment_var = any(
                _segment_uses_codex_fragment_vars(value, shell_vars) for value in _runner_embedded_command_bodies(text)
            )
            embedded_renders_to_raw_codex = any(
                _segment_renders_to_raw_codex(value, shell_vars, shell_arrays)
                for value in _runner_embedded_command_bodies(text)
            )
            alias_raw = _segment_uses_codex_alias(text, codex_aliases)
            function_raw = _segment_uses_codex_function(text, codex_functions)
            if text and (
                _segment_has_raw_codex_exec(text)
                or _segment_uses_codex_var(text, codex_vars)
                or _segment_uses_codex_var_package_runner(text, codex_vars)
                or _segment_uses_codex_array(text, shell_arrays)
                or _segment_uses_codex_fragment_vars(text, shell_vars)
                or _segment_renders_to_raw_codex(text, shell_vars, shell_arrays)
                or embedded_uses_codex_fragment_var
                or embedded_renders_to_raw_codex
                or alias_raw
                or function_raw
            ):
                segments.append(text)
            elif embedded_uses_codex_var:
                segments.append(text)
    return segments


def raw_claude_segments(command: str) -> list[str]:
    segments: list[str] = []
    command_claude_vars = _assigned_claude_vars(command)
    command_claude_aliases = _claude_aliases(command)
    command_claude_functions = _claude_passthrough_functions(command)
    for surface in _iter_command_surfaces(command):
        claude_vars: set[str] = set(command_claude_vars)
        shell_vars: dict[str, str] = {}
        shell_arrays: dict[str, list[str]] = {}
        claude_aliases: dict[str, list[str]] = dict(command_claude_aliases)
        claude_functions: dict[str, list[str]] = dict(command_claude_functions)
        claude_aliases.update(_claude_aliases(surface))
        claude_functions.update(_claude_passthrough_functions(surface))
        for segment in _split_shell_segments(surface):
            text = segment.strip()
            claude_vars.update(_assigned_claude_vars(text))
            shell_vars.update(_assigned_shell_var_values(text, shell_vars))
            shell_arrays.update(_assigned_shell_array_values(text, shell_vars, shell_arrays))
            claude_aliases.update(_claude_aliases(text))
            claude_functions.update(_claude_passthrough_functions(text))
            embedded_uses_claude_var = any(
                _segment_uses_claude_var(value, claude_vars) for value in _runner_embedded_command_bodies(text)
            )
            embedded_uses_claude_fragment_var = any(
                _segment_uses_claude_fragment_vars(value, shell_vars) for value in _runner_embedded_command_bodies(text)
            )
            embedded_renders_to_raw_claude = any(
                _segment_renders_to_raw_claude(value, shell_vars, shell_arrays)
                for value in _runner_embedded_command_bodies(text)
            )
            alias_raw = _segment_uses_claude_alias(text, claude_aliases)
            function_raw = _segment_uses_claude_function(text, claude_functions)
            if text and (
                _segment_has_raw_claude_cli(text)
                or _segment_uses_claude_var(text, claude_vars)
                or _segment_uses_claude_var_package_runner(text, claude_vars)
                or _segment_uses_claude_array(text, shell_arrays)
                or _segment_uses_claude_fragment_vars(text, shell_vars)
                or _segment_renders_to_raw_claude(text, shell_vars, shell_arrays)
                or embedded_uses_claude_fragment_var
                or embedded_renders_to_raw_claude
                or alias_raw
                or function_raw
            ):
                segments.append(text)
            elif embedded_uses_claude_var:
                segments.append(text)
    return segments


def _codex_aliases(segment: str) -> dict[str, list[str]]:
    aliases: dict[str, list[str]] = {}
    pattern = re.compile(r"(?:^|[;&\n])\s*alias\s+([A-Za-z_][A-Za-z0-9_]*)=(?:'([^']*)'|\"([^\"]*)\"|([^ \t;&|]+))")
    for match in pattern.finditer(segment):
        value = next(group for group in match.groups()[1:] if group is not None)
        try:
            tokens = [_decode_detection_token(token) for token in shlex.split(value, comments=False, posix=True)]
        except ValueError:
            continue
        if tokens and (_word_may_expand_to_codex(tokens[0]) or _tokens_are_codex_execution_prefix(tokens)):
            aliases[match.group(1)] = tokens
    return aliases


def _claude_aliases(segment: str) -> dict[str, list[str]]:
    aliases: dict[str, list[str]] = {}
    pattern = re.compile(r"(?:^|[;&\n])\s*alias\s+([A-Za-z_][A-Za-z0-9_]*)=(?:'([^']*)'|\"([^\"]*)\"|([^ \t;&|]+))")
    for match in pattern.finditer(segment):
        value = next(group for group in match.groups()[1:] if group is not None)
        try:
            tokens = [_decode_detection_token(token) for token in shlex.split(value, comments=False, posix=True)]
        except ValueError:
            continue
        if tokens and (_word_may_expand_to_claude(tokens[0]) or _tokens_are_claude_execution_prefix(tokens)):
            aliases[match.group(1)] = tokens
    return aliases


def _segment_uses_codex_alias(segment: str, aliases: dict[str, list[str]]) -> bool:
    if not aliases:
        return False
    try:
        tokens = shlex.split(segment, comments=False, posix=True)
    except ValueError:
        return False
    tokens = _normalize_shell_control_tokens(_strip_env_prefix(tokens))
    if not tokens or _basename(tokens[0]) not in aliases:
        return False
    expanded = [*aliases[_basename(tokens[0])], *tokens[1:]]
    return _segment_has_raw_codex_exec(" ".join(shlex.quote(token) for token in expanded))


def _segment_uses_claude_alias(segment: str, aliases: dict[str, list[str]]) -> bool:
    if not aliases:
        return False
    try:
        tokens = shlex.split(segment, comments=False, posix=True)
    except ValueError:
        return False
    tokens = _normalize_shell_control_tokens(_strip_env_prefix(tokens))
    if not tokens or _basename(tokens[0]) not in aliases:
        return False
    expanded = [*aliases[_basename(tokens[0])], *tokens[1:]]
    return _segment_has_raw_claude_cli(" ".join(shlex.quote(token) for token in expanded))


def _codex_passthrough_functions(segment: str) -> dict[str, list[str]]:
    functions: dict[str, list[str]] = {}
    patterns = [
        r"(?:^|[;&\n])\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{([^}]*)\}",
        r"(?:^|[;&\n])\s*function\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\(\))?\s*\{([^}]*)\}",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, segment, flags=re.DOTALL):
            prefix = _codex_passthrough_prefix(match.group(2))
            if prefix:
                functions[match.group(1)] = prefix
    return functions


def _claude_passthrough_functions(segment: str) -> dict[str, list[str]]:
    functions: dict[str, list[str]] = {}
    patterns = [
        r"(?:^|[;&\n])\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{([^}]*)\}",
        r"(?:^|[;&\n])\s*function\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\(\))?\s*\{([^}]*)\}",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, segment, flags=re.DOTALL):
            prefix = _claude_passthrough_prefix(match.group(2))
            if prefix:
                functions[match.group(1)] = prefix
    return functions


def _codex_passthrough_prefix(body: str) -> list[str]:
    body = _split_shell_segments(body.strip(), maxsplit=1)[0]
    try:
        tokens = [_decode_detection_token(token) for token in shlex.split(body.strip(), comments=False, posix=True)]
    except ValueError:
        return []
    if not tokens:
        return []
    passthrough_indexes = [index for index, token in enumerate(tokens) if token in {"$@", "$*"}]
    if not passthrough_indexes:
        return []
    first_passthrough = min(passthrough_indexes)
    prefix = tokens[:first_passthrough]
    if not prefix:
        return [ARGV_PASSTHROUGH_MARKER]
    if _tokens_execute_argv_passthrough(prefix):
        return [ARGV_PASSTHROUGH_MARKER]
    return prefix if prefix and (_word_may_expand_to_codex(prefix[0]) or _tokens_are_codex_execution_prefix(prefix)) else []


def _claude_passthrough_prefix(body: str) -> list[str]:
    body = _split_shell_segments(body.strip(), maxsplit=1)[0]
    try:
        tokens = [_decode_detection_token(token) for token in shlex.split(body.strip(), comments=False, posix=True)]
    except ValueError:
        return []
    if not tokens:
        return []
    passthrough_indexes = [index for index, token in enumerate(tokens) if token in {"$@", "$*"}]
    if not passthrough_indexes:
        return []
    first_passthrough = min(passthrough_indexes)
    prefix = tokens[:first_passthrough]
    if not prefix:
        return [ARGV_PASSTHROUGH_MARKER]
    if _tokens_execute_argv_passthrough(prefix):
        return [ARGV_PASSTHROUGH_MARKER]
    return prefix if prefix and (_word_may_expand_to_claude(prefix[0]) or _tokens_are_claude_execution_prefix(prefix)) else []


def _tokens_execute_argv_passthrough(tokens: list[str]) -> bool:
    remaining = _strip_env_prefix(tokens)
    for _ in range(4):
        if not remaining:
            return True
        base = _basename(remaining[0])
        if base in {"eval", "command", "exec"}:
            remaining = remaining[1:]
            continue
        if base == "builtin" and len(remaining) >= 2 and remaining[1] == "eval":
            remaining = remaining[2:]
            continue
        return False
    return False


def _segment_uses_codex_function(segment: str, functions: dict[str, list[str]]) -> bool:
    if not functions:
        return False
    try:
        tokens = shlex.split(segment, comments=False, posix=True)
    except ValueError:
        return False
    tokens = _normalize_shell_control_tokens(_strip_env_prefix(tokens))
    if not tokens or _basename(tokens[0]) not in functions:
        return False
    prefix = functions[_basename(tokens[0])]
    if prefix == [ARGV_PASSTHROUGH_MARKER]:
        return _tokens_start_raw_codex(tokens[1:]) or _segment_has_raw_codex_exec(
            " ".join(shlex.quote(token) for token in tokens[1:])
        )
    expanded = [*prefix, *tokens[1:]]
    return _segment_has_raw_codex_exec(" ".join(shlex.quote(token) for token in expanded))


def _segment_uses_claude_function(segment: str, functions: dict[str, list[str]]) -> bool:
    if not functions:
        return False
    try:
        tokens = shlex.split(segment, comments=False, posix=True)
    except ValueError:
        return False
    tokens = _normalize_shell_control_tokens(_strip_env_prefix(tokens))
    if not tokens or _basename(tokens[0]) not in functions:
        return False
    prefix = functions[_basename(tokens[0])]
    if prefix == [ARGV_PASSTHROUGH_MARKER]:
        return _tokens_start_raw_claude(tokens[1:]) or _segment_has_raw_claude_cli(
            " ".join(shlex.quote(token) for token in tokens[1:])
        )
    expanded = [*prefix, *tokens[1:]]
    return _segment_has_raw_claude_cli(" ".join(shlex.quote(token) for token in expanded))


def has_raw_codex_evidence(segment: str) -> bool:
    try:
        assignments = _leading_assignments(shlex.split(segment, comments=False, posix=True))
    except ValueError:
        assignments = {}
    allow_raw = assignments.get("HELIX_ALLOW_RAW_CODEX") == "1"
    reason = assignments.get("HELIX_RAW_CODEX_REASON", "")
    return bool(allow_raw and reason.strip())


def has_raw_claude_evidence(segment: str) -> bool:
    try:
        assignments = _leading_assignments(shlex.split(segment, comments=False, posix=True))
    except ValueError:
        assignments = {}
    allow_raw = assignments.get("HELIX_ALLOW_RAW_CLAUDE") == "1"
    reason = assignments.get("HELIX_RAW_CLAUDE_REASON", "")
    return bool(allow_raw and reason.strip())


def _raw_segment_is_command_substitution(segment: str) -> bool:
    stripped = segment.strip()
    return stripped.startswith("$(") or stripped.startswith("`")


def _outer_evidence_covers_child_raw(segment: str) -> bool:
    try:
        tokens = [_decode_detection_token(token) for token in shlex.split(segment, comments=False, posix=True)]
    except ValueError:
        return False
    runner_tokens = _strip_env_prefix(tokens)
    return bool(_embedded_command_values(runner_tokens))


def _raw_segments_are_authorized(command: str) -> bool:
    codex_vars: set[str] = set()
    saw_raw = False
    for segment in _split_shell_segments(_join_line_continuations(command)):
        text = segment.strip()
        if not text:
            continue
        codex_vars.update(_assigned_codex_vars(text))
        segment_raw = raw_codex_segments(text)
        if _segment_uses_codex_var(text, codex_vars):
            segment_raw.append(text)
        if not segment_raw:
            continue
        saw_raw = True
        child_raw = [raw_segment for raw_segment in segment_raw if raw_segment != text]
        if has_raw_codex_evidence(text) and _segment_has_raw_codex_exec(text) and not child_raw:
            continue
        if (
            has_raw_codex_evidence(text)
            and len(child_raw) == 1
            and not _raw_segment_is_command_substitution(child_raw[0])
            and _outer_evidence_covers_child_raw(text)
        ):
            continue
        if child_raw and all(has_raw_codex_evidence(raw_segment) for raw_segment in child_raw):
            continue
        if all(has_raw_codex_evidence(raw_segment) for raw_segment in segment_raw):
            continue
        return False
    return saw_raw


def _raw_claude_segments_are_authorized(command: str) -> bool:
    claude_vars: set[str] = set()
    saw_raw = False
    for segment in _split_shell_segments(_join_line_continuations(command)):
        text = segment.strip()
        if not text:
            continue
        claude_vars.update(_assigned_claude_vars(text))
        segment_raw = raw_claude_segments(text)
        if _segment_uses_claude_var(text, claude_vars):
            segment_raw.append(text)
        if not segment_raw:
            continue
        saw_raw = True
        child_raw = [raw_segment for raw_segment in segment_raw if raw_segment != text]
        if has_raw_claude_evidence(text) and _segment_has_raw_claude_cli(text) and not child_raw:
            continue
        if (
            has_raw_claude_evidence(text)
            and len(child_raw) == 1
            and not _raw_segment_is_command_substitution(child_raw[0])
            and _outer_evidence_covers_child_raw(text)
        ):
            continue
        if child_raw and all(has_raw_claude_evidence(raw_segment) for raw_segment in child_raw):
            continue
        if all(has_raw_claude_evidence(raw_segment) for raw_segment in segment_raw):
            continue
        return False
    return saw_raw


def inspect_command(command: str) -> GuardResult:
    if not command.strip():
        return GuardResult(ok=True)
    raw_codex = raw_codex_segments(command)
    raw_claude = raw_claude_segments(command)
    if not raw_codex and not raw_claude:
        return GuardResult(ok=True)
    if (not raw_codex or _raw_segments_are_authorized(command)) and (
        not raw_claude or _raw_claude_segments_are_authorized(command)
    ):
        return GuardResult(ok=True)
    if raw_claude and not raw_codex:
        return GuardResult(
            ok=False,
            reason=(
                "raw `claude` は HELIX discipline が効かないためブロックしました。"
                " `helix claude --role <role> --task ... --dry-run` を使ってください。"
                " 例外時は `HELIX_ALLOW_RAW_CLAUDE=1 HELIX_RAW_CLAUDE_REASON=<理由>` を同じコマンドに含め、"
                "final/evidence に代替不能性を残してください。"
            ),
        )
    return GuardResult(
        ok=False,
        reason=(
            "raw LLM CLI 実行は HELIX discipline が効かないためブロックしました。"
            " Codex は `helix codex --role <role> --task ... --plan-only|--approved`、"
            "Claude は `helix claude --role <role> --task ... --dry-run` を使ってください。"
            " 例外時は対象 CLI の `HELIX_ALLOW_RAW_*` と `HELIX_RAW_*_REASON=<理由>` を同じコマンドに含め、"
            "final/evidence に代替不能性を残してください。"
        ),
    )


def deny_payload(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "check-bash"
    if command in {"--help", "-h"}:
        print("Usage: llm_guard.py check-bash")
        return 0
    if command != "check-bash":
        print("Usage: llm_guard.py check-bash", file=sys.stderr)
        return 2

    result = inspect_command(extract_bash_command(_load_payload(sys.stdin)))
    if result.ok:
        return 0
    print(json.dumps(deny_payload(result.reason), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
