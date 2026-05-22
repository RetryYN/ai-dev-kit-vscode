#!/usr/bin/env bash
# Claude Code PreToolUse hook (matcher=Edit|Write|MultiEdit)
# PLAN-087 Phase 2: 設計 doc の新規作成 / 大幅変更前に
# WebSearch / WebFetch / pmo-tech-fork / pmo-tech-docs の事前調査を fail-close で強制する。
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$REPO_ROOT}"

payload_file="$(mktemp)"
trap 'rm -f "$payload_file"' EXIT
cat >"$payload_file"

python3 - "$payload_file" "$PROJECT_ROOT" "$REPO_ROOT" <<'PY'
from __future__ import annotations

import difflib
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path


TARGET_TOOLS = {"Edit", "Write", "MultiEdit"}
TARGET_SUBAGENTS = {"pmo-tech-fork", "pmo-tech-docs"}
WEB_PATTERNS = (
    '"tool_name":"WebSearch"',
    '"tool_name": "WebSearch"',
    '"tool_name":"WebFetch"',
    '"tool_name": "WebFetch"',
    "WebSearch(",
    "WebFetch(",
)
SUBAGENT_PATTERNS = tuple(TARGET_SUBAGENTS)
MAX_SCAN_FILES = 64
MAX_SCAN_BYTES = 512 * 1024
MAX_TRANSCRIPT_AGE_SECONDS = 60 * 60
UNKNOWN_DIFF = 10**9


def load_payload(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def truthy_env(name: str) -> bool:
    value = os.environ.get(name, "").strip().lower()
    return value not in {"", "0", "false", "no"}


def find_first(value, names: set[str]):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in names:
                return child
        for child in value.values():
            result = find_first(child, names)
            if result is not None:
                return result
    elif isinstance(value, list):
        for child in value:
            result = find_first(child, names)
            if result is not None:
                return result
    return None


def detect_transcript_path(payload: dict) -> Path | None:
    for env_name in ("CLAUDE_TRANSCRIPT_PATH", "TRANSCRIPT_PATH", "HELIX_TRANSCRIPT_PATH"):
        value = os.environ.get(env_name, "").strip()
        if value:
            return Path(value).expanduser()
    payload_path = find_first(payload, {"transcript_path"})
    if payload_path not in (None, ""):
        return Path(str(payload_path).strip()).expanduser()
    return None


def detect_session_id(payload: dict) -> str:
    for key in ("HELIX_SESSION_ID", "CLAUDE_SESSION_ID"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    payload_session_id = find_first(payload, {"session_id", "sessionId"})
    if payload_session_id not in (None, ""):
        return str(payload_session_id).strip()
    task_output = os.environ.get("CLAUDE_TASK_OUTPUT_DIR", "")
    match = re.search(
        r"/tmp/claude-(?:\d+)/[^/]+/([a-f0-9]{8})[a-f0-9-]{28}",
        task_output,
    )
    if match:
        return match.group(1)
    transcript_path = detect_transcript_path(payload)
    if transcript_path:
        match = re.search(r"/([a-f0-9-]{36})\.jsonl(?:$|/)", str(transcript_path))
        if match:
            return match.group(1)
    return ""


def resolve_path(raw_path: str, project_root: Path) -> tuple[str, str]:
    if not raw_path:
        return "", ""
    path = Path(raw_path)
    abs_path = path if path.is_absolute() else project_root / path
    try:
        rel_path = abs_path.resolve(strict=False).relative_to(project_root.resolve(strict=False))
    except Exception:
        return str(abs_path), ""
    return str(abs_path), rel_path.as_posix()


def is_target_design_doc(rel_path: str) -> bool:
    if not rel_path:
        return False
    if rel_path.startswith("docs/templates/"):
        return False
    if rel_path == "docs/adr/index.md":
        return False
    if re.fullmatch(r"docs/adr/ADR-[^/]+\.md", rel_path):
        return True
    if re.fullmatch(r"docs/plans/PLAN-[^/]+\.md", rel_path):
        return True
    return False


def count_changed_lines(before: str, after: str) -> int:
    count = 0
    for line in difflib.unified_diff(
        before.splitlines(),
        after.splitlines(),
        fromfile="before",
        tofile="after",
        lineterm="",
    ):
        if line.startswith(("---", "+++")):
            continue
        if line.startswith(("+", "-")):
            count += 1
    return count


def apply_single_edit(content: str, edit: dict) -> str | None:
    old = str(edit.get("old_string") or "")
    new = str(edit.get("new_string") or "")
    replace_all = bool(edit.get("replace_all"))
    if old:
        if old not in content:
            return None
        return content.replace(old, new) if replace_all else content.replace(old, new, 1)
    if new:
        return content + new
    return content


def projected_diff_lines(tool_name: str, tool_input: dict, file_path: Path) -> int:
    if not file_path.exists():
        return UNKNOWN_DIFF

    try:
        current = file_path.read_text(encoding="utf-8")
    except Exception:
        return UNKNOWN_DIFF

    candidate: str | None = None
    if tool_name == "Write":
        if isinstance(tool_input.get("content"), str):
            candidate = tool_input["content"]
        elif isinstance(tool_input.get("text"), str):
            candidate = tool_input["text"]
    elif tool_name == "Edit":
        candidate = apply_single_edit(current, tool_input if isinstance(tool_input, dict) else {})
    elif tool_name == "MultiEdit":
        edits = tool_input.get("edits")
        if isinstance(edits, list):
            candidate = current
            for edit in edits:
                if not isinstance(edit, dict):
                    return UNKNOWN_DIFF
                candidate = apply_single_edit(candidate, edit)
                if candidate is None:
                    return UNKNOWN_DIFF

    if candidate is None:
        return UNKNOWN_DIFF
    return count_changed_lines(current, candidate)


def is_recent(path: Path) -> bool:
    try:
        return time.time() - path.stat().st_mtime <= MAX_TRANSCRIPT_AGE_SECONDS
    except OSError:
        return False


def claude_projects_root(project_root: Path) -> Path:
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR", "").strip()
    if config_dir:
        return Path(config_dir).expanduser() / "projects"
    home = os.environ.get("HOME", "").strip()
    if home:
        return Path(home).expanduser() / ".claude" / "projects"
    return project_root / ".claude" / "projects"


def project_slug(project_root: Path) -> str:
    return "-" + project_root.resolve(strict=False).as_posix().lstrip("/").replace("/", "-")


def session_transcript_paths(project_root: Path, session_id: str) -> list[Path]:
    project_dir = claude_projects_root(project_root) / project_slug(project_root)
    return [
        project_dir / f"{session_id}.jsonl",
        project_dir / "sessions" / session_id / "transcript.jsonl",
        project_dir / session_id / "transcript.jsonl",
    ]


def latest_project_transcript(project_root: Path) -> Path | None:
    project_dir = claude_projects_root(project_root) / project_slug(project_root)
    if not project_dir.is_dir():
        return None
    files: list[Path] = []
    for pattern in ("*.jsonl", "sessions/*/transcript.jsonl", "*/transcript.jsonl"):
        files.extend(path for path in project_dir.glob(pattern) if path.is_file())
    recent_files = [path for path in files if is_recent(path)]
    if not recent_files:
        return None
    return max(recent_files, key=lambda path: path.stat().st_mtime)


def iter_candidate_files(path: Path):
    if path.is_file():
        yield path
        return
    if not path.is_dir():
        return
    count = 0
    for child in sorted(path.rglob("*")):
        if not child.is_file():
            continue
        count += 1
        if count > MAX_SCAN_FILES:
            break
        yield child


def collect_transcript_candidates(session_id: str, payload: dict, project_root: Path) -> tuple[list[Path], str]:
    candidates: list[Path] = []
    fallback_kind = ""
    seen: set[str] = set()

    def add_file(path: Path, kind: str = "") -> None:
        nonlocal fallback_kind
        expanded = path.expanduser()
        resolved = str(expanded.resolve(strict=False))
        if resolved in seen or not expanded.is_file() or not is_recent(expanded):
            return
        seen.add(resolved)
        candidates.append(expanded)
        if kind and not fallback_kind:
            fallback_kind = kind

    transcript_path = detect_transcript_path(payload)
    if transcript_path is not None:
        add_file(transcript_path, "transcript_path")

    raw_dirs = []
    for env_name in ("HELIX_DESIGN_DOC_GUARD_TRANSCRIPT_DIR", "CLAUDE_TASK_OUTPUT_DIR"):
        raw = os.environ.get(env_name, "").strip()
        if raw:
            raw_dirs.extend([part for part in raw.split(os.pathsep) if part])
    for raw in raw_dirs:
        candidate = Path(raw).expanduser()
        if candidate.is_file():
            add_file(candidate)
            continue
        if candidate.is_dir():
            if session_id:
                for session_path in (
                    candidate / f"{session_id}.jsonl",
                    candidate / "sessions" / session_id / "transcript.jsonl",
                    candidate / session_id / "transcript.jsonl",
                ):
                    add_file(session_path)
            for file_path in iter_candidate_files(candidate):
                add_file(file_path)

    if session_id:
        for path in session_transcript_paths(project_root, session_id):
            add_file(path)
    else:
        latest_transcript = latest_project_transcript(project_root)
        if latest_transcript is not None:
            add_file(latest_transcript, "project_latest")

    return candidates, fallback_kind


def scan_transcripts(session_id: str, payload: dict, project_root: Path) -> tuple[set[str], str, str]:
    findings: set[str] = set()
    candidates, fallback_kind = collect_transcript_candidates(session_id, payload, project_root)
    for file_path in candidates:
        try:
            if file_path.stat().st_size > MAX_SCAN_BYTES:
                continue
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if any(pattern in text for pattern in WEB_PATTERNS):
            findings.add("transcript:web")
        if any(pattern in text for pattern in SUBAGENT_PATTERNS):
            findings.add("transcript:subagent")
        if findings:
            return findings, str(file_path), fallback_kind
    return findings, "", fallback_kind


def resolve_db_path(repo_root: Path, project_root: Path) -> str:
    for env_name in ("HELIX_DESIGN_DOC_GUARD_DB_PATH", "HELIX_DB_PATH"):
        value = os.environ.get(env_name, "").strip()
        if value:
            return str(Path(value).expanduser())

    sys.path.insert(0, str(repo_root))
    try:
        from cli.lib import helix_db  # type: ignore
    except Exception:
        return str(project_root / ".helix" / "helix.db")
    return str(Path(helix_db.resolve_default_db_path()))


def query_agent_slots(repo_root: Path, project_root: Path, session_id: str) -> bool:
    if not session_id:
        return False
    db_path = Path(resolve_db_path(repo_root, project_root))
    if not db_path.exists():
        return False
    try:
        conn = sqlite3.connect(str(db_path))
        row = conn.execute(
            """
            SELECT 1
            FROM agent_slots
            WHERE session_id = ?
              AND subagent_type IN (?, ?)
            ORDER BY id DESC
            LIMIT 1
            """,
            (session_id, "pmo-tech-fork", "pmo-tech-docs"),
        ).fetchone()
    except sqlite3.Error:
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return row is not None


def block(message: str) -> int:
    print(message, file=sys.stderr)
    return 2


payload_path = Path(sys.argv[1])
project_root = Path(sys.argv[2]).resolve(strict=False)
repo_root = Path(sys.argv[3]).resolve(strict=False)
payload = load_payload(payload_path)
tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
tool_input = payload.get("tool_input") or {}
if not isinstance(tool_input, dict):
    tool_input = {}

if tool_name not in TARGET_TOOLS:
    raise SystemExit(0)

raw_path = str(tool_input.get("file_path") or payload.get("file_path") or "")
abs_path_text, rel_path = resolve_path(raw_path, project_root)
if not is_target_design_doc(rel_path):
    raise SystemExit(0)

if truthy_env("HELIX_ALLOW_DESIGN_DOC_NO_WEB"):
    reason = os.environ.get("HELIX_DESIGN_DOC_NO_WEB_REASON", "").strip()
    if not reason:
        raise SystemExit(
            block(
                "[helix-guard] BLOCK: HELIX_ALLOW_DESIGN_DOC_NO_WEB=1 には "
                "HELIX_DESIGN_DOC_NO_WEB_REASON が必須です。"
            )
        )
    raise SystemExit(0)

abs_path = Path(abs_path_text)
diff_threshold = int(os.environ.get("HELIX_DESIGN_DOC_GUARD_DIFF_THRESHOLD", "50"))
is_new_file = not abs_path.exists()
diff_lines = projected_diff_lines(tool_name, tool_input, abs_path)
is_large_change = is_new_file or diff_lines > diff_threshold or diff_lines == UNKNOWN_DIFF

if not is_large_change:
    raise SystemExit(0)

session_id = detect_session_id(payload)
evidence, transcript_source, transcript_fallback = scan_transcripts(session_id, payload, project_root)
if query_agent_slots(repo_root, project_root, session_id):
    evidence.add("agent_slots:subagent")

if evidence:
    if not session_id and transcript_source:
        warning = (
            "[helix-guard] WARN: session_id missing, "
            f"{transcript_fallback or 'transcript'} fallback accepted evidence from {transcript_source}"
        )
        print(warning, file=sys.stderr)
    raise SystemExit(0)

if not session_id and truthy_env("HELIX_DESIGN_DOC_GUARD_ALLOW_MISSING_SESSION"):
    reason = os.environ.get("HELIX_DESIGN_DOC_GUARD_ALLOW_MISSING_SESSION_REASON", "").strip()
    if not reason:
        raise SystemExit(
            block(
                "[helix-guard] BLOCK: HELIX_DESIGN_DOC_GUARD_ALLOW_MISSING_SESSION=1 には "
                "HELIX_DESIGN_DOC_GUARD_ALLOW_MISSING_SESSION_REASON が必須です。"
            )
        )
    print(
        "[helix-guard] WARN: session_id missing but bypassed by "
        f"HELIX_DESIGN_DOC_GUARD_ALLOW_MISSING_SESSION=1 reason={reason}",
        file=sys.stderr,
    )
    raise SystemExit(0)

reason_bits = [
    f"path={rel_path}",
    "change=new-file" if is_new_file else f"diff_lines={diff_lines}",
    f"session_id={session_id or 'missing'}",
]
raise SystemExit(
    block(
        "[helix-guard] BLOCK: 設計 doc の新規作成または大幅変更の前に "
        "WebSearch / WebFetch / pmo-tech-fork / pmo-tech-docs による業界 standard 確認が必要です. "
        + " ".join(reason_bits)
    )
)
PY
