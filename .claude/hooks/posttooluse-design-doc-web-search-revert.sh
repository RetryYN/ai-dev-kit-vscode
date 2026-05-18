#!/usr/bin/env bash
# Claude Code PostToolUse hook (matcher=Edit|Write|MultiEdit)
# PLAN-087 Phase 2 carry: PreToolUse block が無視された場合の最後の防衛線。
#
# 方針:
# - 対象は docs/adr/ADR-*.md と docs/plans/PLAN-*.md に限定
# - session 内の WebSearch / WebFetch / pmo-tech-fork / pmo-tech-docs 証跡がなければ warn
# - 新規 design doc は backup を残した上で自動 revert
# - 既存 tracked file は安全側で自動 revert せず warn のみ
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
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
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
REASON_ENV_NAMES = (
    "HELIX_DESIGN_DOC_NO_WEB_REASON",
    "HELIX_ALLOW_DESIGN_DOC_NO_WEB_REASON",
)
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


def bypass_reason() -> str:
    for name in REASON_ENV_NAMES:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


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


def resolve_path(raw_path: str, project_root: Path) -> tuple[Path | None, str]:
    if not raw_path:
        return None, ""
    path = Path(raw_path)
    abs_path = path if path.is_absolute() else project_root / path
    try:
        rel_path = abs_path.resolve(strict=False).relative_to(project_root.resolve(strict=False))
    except Exception:
        return abs_path, ""
    return abs_path, rel_path.as_posix()


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


def scan_transcripts() -> set[str]:
    findings: set[str] = set()
    for candidate in transcript_candidates():
        for file_path in iter_candidate_files(candidate):
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


def git_run(project_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(project_root), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def file_in_head(project_root: Path, rel_path: str) -> bool:
    result = git_run(project_root, "cat-file", "-e", f"HEAD:{rel_path}")
    return result.returncode == 0


def read_head_text(project_root: Path, rel_path: str) -> str | None:
    result = git_run(project_root, "show", f"HEAD:{rel_path}")
    if result.returncode != 0:
        return None
    return result.stdout


def diff_lines_vs_head(project_root: Path, rel_path: str, current_text: str) -> int:
    head_text = read_head_text(project_root, rel_path)
    if head_text is None:
        return UNKNOWN_DIFF
    return count_changed_lines(head_text, current_text)


def backup_root(project_root: Path) -> Path:
    raw = os.environ.get("HELIX_DESIGN_DOC_REVERT_BACKUP_DIR", "").strip()
    if raw:
        return Path(raw).expanduser()
    return project_root / ".helix" / "hooks" / "design-doc-web-search-revert"


def write_backup(abs_path: Path, project_root: Path, rel_path: str, session_id: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_session = session_id or "session-missing"
    backup_path = backup_root(project_root) / safe_session / stamp / rel_path
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(abs_path, backup_path)
    return backup_path


def warn(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


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
abs_path, rel_path = resolve_path(raw_path, project_root)
if abs_path is None or not is_target_design_doc(rel_path):
    raise SystemExit(0)
if not abs_path.exists():
    raise SystemExit(0)

if truthy_env("HELIX_ALLOW_DESIGN_DOC_NO_WEB"):
    reason = bypass_reason()
    if reason:
        raise SystemExit(0)
    bypass_note = " bypass_reason=missing"
else:
    bypass_note = ""

session_id = detect_session_id()
evidence = scan_transcripts()
if query_agent_slots(repo_root, project_root, session_id):
    evidence.add("agent_slots:subagent")
if evidence:
    raise SystemExit(0)

try:
    current_text = abs_path.read_text(encoding="utf-8")
except Exception as exc:
    raise SystemExit(
        warn(
            "[helix-guard] WARN: design-doc revert guard が "
            f"{rel_path} の読み取りに失敗したため自動 revert を実行できませんでした: {exc}"
        )
    )

tracked_in_head = file_in_head(project_root, rel_path)
diff_threshold = int(os.environ.get("HELIX_DESIGN_DOC_GUARD_DIFF_THRESHOLD", "50"))
if tracked_in_head:
    diff_lines = diff_lines_vs_head(project_root, rel_path, current_text)
    if diff_lines != UNKNOWN_DIFF and diff_lines <= diff_threshold:
        raise SystemExit(0)
    raise SystemExit(
        warn(
            "[helix-guard] WARN: 事前調査なしの設計 doc 変更を検出しましたが、"
            f"{rel_path} は既存 tracked file のため自動 revert を skip しました. "
            f"diff_lines={diff_lines if diff_lines != UNKNOWN_DIFF else 'unknown'} "
            f"session_id={session_id or 'missing'}{bypass_note}"
        )
    )

try:
    backup_path = write_backup(abs_path, project_root, rel_path, session_id)
except Exception as exc:
    raise SystemExit(
        warn(
            "[helix-guard] WARN: 事前調査なしの新規設計 doc を検出しましたが、"
            f"backup 作成に失敗したため revert を中止しました: {exc}"
        )
    )

try:
    abs_path.unlink()
except FileNotFoundError:
    pass
except Exception as exc:
    raise SystemExit(
        warn(
            "[helix-guard] WARN: 事前調査なしの新規設計 doc の revert に失敗しました. "
            f"path={rel_path} backup={backup_path} error={exc}"
        )
    )

raise SystemExit(
    warn(
        "[helix-guard] WARN: 事前調査なしの新規設計 doc 変更を検出したため "
        f"{rel_path} を revert しました. "
        f"backup={backup_path} session_id={session_id or 'missing'} "
        "WebSearch / WebFetch / pmo-tech-fork / pmo-tech-docs を先に実行してください."
        f"{bypass_note}"
    )
)
PY
