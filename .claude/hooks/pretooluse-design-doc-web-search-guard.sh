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


def detect_session_id() -> str:
    for key in ("HELIX_SESSION_ID", "CLAUDE_SESSION_ID"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    task_output = os.environ.get("CLAUDE_TASK_OUTPUT_DIR", "")
    match = re.search(
        r"/tmp/claude-(?:\d+)/[^/]+/([a-f0-9]{8})[a-f0-9-]{28}",
        task_output,
    )
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


def transcript_candidates() -> list[Path]:
    candidates: list[Path] = []
    raw_dirs = []
    for env_name in ("HELIX_DESIGN_DOC_GUARD_TRANSCRIPT_DIR", "CLAUDE_TASK_OUTPUT_DIR"):
        raw = os.environ.get(env_name, "").strip()
        if raw:
            raw_dirs.extend([part for part in raw.split(os.pathsep) if part])
    seen: set[str] = set()
    for raw in raw_dirs:
        resolved = str(Path(raw).expanduser())
        if resolved in seen:
            continue
        seen.add(resolved)
        candidates.append(Path(resolved))
    return candidates


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


def scan_transcripts(session_id: str) -> set[str]:
    findings: set[str] = set()
    for candidate in transcript_candidates():
        for file_path in iter_candidate_files(candidate):
            try:
                if file_path.stat().st_size > MAX_SCAN_BYTES:
                    continue
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            if session_id and session_id not in text and candidate != file_path:
                # session 専用 dir の下では session_id がなくても許可。
                pass

            if any(pattern in text for pattern in WEB_PATTERNS):
                findings.add("transcript:web")
            if any(pattern in text for pattern in SUBAGENT_PATTERNS):
                findings.add("transcript:subagent")
            if findings:
                return findings
    return findings


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

session_id = detect_session_id()
evidence = scan_transcripts(session_id)
if query_agent_slots(repo_root, project_root, session_id):
    evidence.add("agent_slots:subagent")

if evidence:
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
