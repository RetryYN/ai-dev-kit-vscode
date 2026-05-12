from __future__ import annotations

import re
from pathlib import Path


MAIN_FUNCTION = "__main__"
_FUNCTION_PATTERNS = (
    re.compile(r"^\s*function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)\s*\{"),
    re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)\s*\{"),
)
_CONTROL_HEADS = {
    "if",
    "then",
    "elif",
    "else",
    "fi",
    "for",
    "while",
    "until",
    "do",
    "done",
    "case",
    "esac",
    "select",
    "function",
    "{",
    "}",
    "(",
    ")",
    "[[",
    "[",
    "]]",
    "]",
    "local",
    "export",
    "readonly",
    "declare",
    "typeset",
    "unset",
    "shift",
    "return",
    "exit",
    "exec",
}
_COMMAND_SPLIT_RE = re.compile(r"(?:&&|\|\||;|\|)")
_BRACE_SANITIZE_RE = re.compile(r"\$\{[^}]*\}")


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _relative_path(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _strip_comments(line: str) -> str:
    if "#" not in line:
        return line
    in_single = False
    in_double = False
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if char == "#" and not in_single and not in_double:
            return line[:index]
    return line


def _function_name(line: str) -> str | None:
    for pattern in _FUNCTION_PATTERNS:
        match = pattern.match(line)
        if match:
            return match.group(1)
    return None


def _quoted_token(text: str) -> str:
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


def _source_target(line: str) -> str | None:
    stripped = line.strip()
    if stripped.startswith("source "):
        return _quoted_token(stripped[len("source ") :]) or None
    if stripped.startswith(". "):
        return _quoted_token(stripped[2:]) or None
    return None


def _brace_delta(line: str) -> int:
    sanitized = _BRACE_SANITIZE_RE.sub("", line)
    return sanitized.count("{") - sanitized.count("}")


def _command_head(segment: str) -> str | None:
    stripped = segment.strip()
    if not stripped:
        return None
    head = stripped.split(None, 1)[0]
    return head if head else None


def _record(records: dict[tuple[str, str], set[str]], script: str, function_name: str, callee: str) -> None:
    if not callee:
        return
    records.setdefault((script, function_name), set()).add(callee)


def extract_script_trace(file_path: str | Path, repo_root: str | Path | None = None) -> list[dict[str, object]]:
    path = Path(file_path)
    root = Path(repo_root).resolve() if repo_root is not None else _default_repo_root()
    script = _relative_path(path, root)
    lines = path.read_text(encoding="utf-8").splitlines()
    function_names = {
        name
        for name in (_function_name(_strip_comments(line)) for line in lines)
        if name
    }

    records: dict[tuple[str, str], set[str]] = {(script, MAIN_FUNCTION): set()}
    for function_name in sorted(function_names):
        records.setdefault((script, function_name), set())

    current_function = MAIN_FUNCTION
    brace_depth = 0
    for raw_line in lines:
        line = _strip_comments(raw_line).rstrip()
        if not line.strip():
            if current_function != MAIN_FUNCTION:
                brace_depth += _brace_delta(line)
                if brace_depth <= 0:
                    current_function = MAIN_FUNCTION
                    brace_depth = 0
            continue

        function_name = _function_name(line)
        if function_name:
            current_function = function_name
            brace_depth = _brace_delta(line)
            if brace_depth <= 0:
                brace_depth = 1
            continue

        source_target = _source_target(line)
        if source_target:
            _record(records, script, current_function, f"source:{source_target}")

        for segment in _COMMAND_SPLIT_RE.split(line):
            head = _command_head(segment)
            if not head or head in _CONTROL_HEADS:
                continue
            if head in function_names:
                _record(records, script, current_function, head)

        if current_function != MAIN_FUNCTION:
            brace_depth += _brace_delta(line)
            if brace_depth <= 0:
                current_function = MAIN_FUNCTION
                brace_depth = 0

    return [
        {
            "script": script,
            "function": function_name,
            "callees": sorted(callees),
        }
        for (script, function_name), callees in sorted(records.items())
    ]


def scan_helix_bash_scripts(repo_root: str | Path | None = None) -> list[dict[str, object]]:
    root = Path(repo_root).resolve() if repo_root is not None else _default_repo_root()
    records: list[dict[str, object]] = []
    for path in sorted((root / "cli").glob("helix-*")):
        if path.is_file():
            records.extend(extract_script_trace(path, root))
    return records
