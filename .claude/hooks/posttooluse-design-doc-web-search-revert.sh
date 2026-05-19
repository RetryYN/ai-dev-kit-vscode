#!/usr/bin/env bash
# Claude Code PostToolUse hook (matcher=Edit|Write|MultiEdit)
# PLAN-089 / handover W9: self-revert の誤検出を減らし、
# 大規模な設計 doc のみ最後の fail-close 対象にする。
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$REPO_ROOT}"

payload_file="$(mktemp)"
trap 'rm -f "$payload_file"' EXIT
cat >"$payload_file"

python3 - "$payload_file" "$PROJECT_ROOT" "$REPO_ROOT" <<'PY'
from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
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
MIN_REVERT_LINES = 100
BLOCK_REASON = "web_search_history_empty"
BLOCK_DETAIL = (
    "Web 検索履歴が見つかりません。"
    "設計 doc は WebSearch 3 query 以上実施後に書き出してください"
)


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
    if rel_path.startswith("docs/adr/") and rel_path.endswith(".md"):
        return True
    if re.fullmatch(r"docs/plans/PLAN-[^/]+\.md", rel_path):
        return True
    if re.fullmatch(r"docs/specs/SPEC-[^/]+\.md", rel_path):
        return True
    return False


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


def emit_json(
    *,
    action: str,
    reason: str,
    detail: str,
    exit_code: int,
    file_path: str = "",
    backup_path: str = "",
    evidence: set[str] | None = None,
) -> int:
    payload: dict[str, object] = {
        "action": action,
        "reason": reason,
        "detail": detail,
    }
    if file_path:
        payload["file"] = file_path
    if backup_path:
        payload["backup"] = backup_path
    if evidence:
        payload["evidence"] = sorted(evidence)
    print(json.dumps(payload, ensure_ascii=False))
    return exit_code


def git_run(project_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(project_root), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def read_head_text(project_root: Path, rel_path: str) -> str | None:
    result = git_run(project_root, "show", f"HEAD:{rel_path}")
    if result.returncode != 0:
        return None
    return result.stdout


def has_frontmatter(abs_path: Path, current_text: str) -> bool:
    try:
        result = subprocess.run(
            ["rg", "^---", str(abs_path)],
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        first_line = current_text.splitlines()[0] if current_text.splitlines() else ""
        return first_line == "---"

    if result.returncode not in {0, 1}:
        return False
    first_match = result.stdout.splitlines()[0].strip() if result.stdout else ""
    return first_match == "---"


def count_lines(current_text: str) -> int:
    return len(current_text.splitlines())


def backup_path_for(abs_path: Path, project_root: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    return (
        project_root
        / ".helix"
        / "backups"
        / f"posttooluse-revert-{stamp}-{abs_path.name}.bak"
    )


def write_backup(abs_path: Path, project_root: Path) -> Path:
    backup_path = backup_path_for(abs_path, project_root)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(abs_path, backup_path)
    return backup_path


def revert_file(
    abs_path: Path,
    project_root: Path,
    rel_path: str,
) -> str:
    backup_path = write_backup(abs_path, project_root)
    head_text = read_head_text(project_root, rel_path)
    if head_text is None:
        abs_path.unlink(missing_ok=True)
        return str(backup_path)

    abs_path.write_text(head_text, encoding="utf-8")
    return str(backup_path)


payload_path = Path(sys.argv[1])
project_root = Path(sys.argv[2]).resolve(strict=False)
repo_root = Path(sys.argv[3]).resolve(strict=False)
payload = load_payload(payload_path)
tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
tool_input = payload.get("tool_input") or {}
if not isinstance(tool_input, dict):
    tool_input = {}

if tool_name not in TARGET_TOOLS:
    raise SystemExit(
        emit_json(
            action="pass",
            reason="skip_non_target_tool",
            detail="design-doc guard の対象外 tool のため verification を skip しました",
            exit_code=0,
        )
    )

raw_path = str(tool_input.get("file_path") or payload.get("file_path") or "")
abs_path, rel_path = resolve_path(raw_path, project_root)
if abs_path is None or not is_target_design_doc(rel_path):
    raise SystemExit(
        emit_json(
            action="pass",
            reason="skip_non_target_path",
            detail="design-doc guard の対象外 path のため verification を skip しました",
            exit_code=0,
            file_path=str(abs_path) if abs_path is not None else "",
        )
    )
if not abs_path.exists():
    raise SystemExit(
        emit_json(
            action="pass",
            reason="skip_missing_file",
            detail="対象 file が存在しないため verification を skip しました",
            exit_code=0,
            file_path=str(abs_path),
        )
    )

if truthy_env("HELIX_ALLOW_DESIGN_DOC_NO_WEB"):
    reason = bypass_reason()
    if not reason:
        raise SystemExit(
            emit_json(
                action="warn",
                reason="bypass_reason_missing",
                detail=(
                    "HELIX_ALLOW_DESIGN_DOC_NO_WEB=1 ですが reason が未設定のため、"
                    "warn-only で verification を skip しました"
                ),
                exit_code=1,
                file_path=str(abs_path),
            )
        )
    raise SystemExit(
        emit_json(
            action="warn",
            reason="bypass_allowed",
            detail=(
                "HELIX_ALLOW_DESIGN_DOC_NO_WEB=1 により verification を skip しました: "
                f"{reason}"
            ),
            exit_code=1,
            file_path=str(abs_path),
        )
    )

session_id = detect_session_id()
if not session_id:
    raise SystemExit(
        emit_json(
            action="warn",
            reason="session_id_missing",
            detail="session_id が取得できないため warn-only で verification を skip しました",
            exit_code=1,
            file_path=str(abs_path),
        )
    )

evidence = scan_transcripts()
if query_agent_slots(repo_root, project_root, session_id):
    evidence.add("agent_slots:subagent")
if evidence:
    raise SystemExit(
        emit_json(
            action="pass",
            reason="verification_passed",
            detail="Web 検索または許可済み subagent の証跡を確認しました",
            exit_code=0,
            file_path=str(abs_path),
            evidence=evidence,
        )
    )

try:
    current_text = abs_path.read_text(encoding="utf-8")
except Exception as exc:
    raise SystemExit(
        emit_json(
            action="warn",
            reason="read_failed",
            detail=f"design-doc revert guard failed to read {rel_path}: {exc}",
            exit_code=1,
            file_path=str(abs_path),
        )
    )

frontmatter = has_frontmatter(abs_path, current_text)
line_count = count_lines(current_text)
if frontmatter and line_count >= MIN_REVERT_LINES:
    try:
        backup_path = revert_file(abs_path, project_root, rel_path)
    except Exception as exc:
        raise SystemExit(
            emit_json(
                action="warn",
                reason="revert_failed",
                detail=(
                    "design doc を revert できませんでした: "
                    f"path={rel_path} error={exc}"
                ),
                exit_code=1,
                file_path=str(abs_path),
            )
        )
    raise SystemExit(
        emit_json(
            action="block",
            reason=BLOCK_REASON,
            detail=BLOCK_DETAIL,
            exit_code=2,
            file_path=str(abs_path),
            backup_path=backup_path,
        )
    )

raise SystemExit(
    emit_json(
        action="warn",
        reason="revert_conditions_not_met",
        detail=(
            "design doc changed without web-search evidence, "
            f"but revert conditions were not met: path={rel_path} "
            f"frontmatter={'yes' if frontmatter else 'no'} line_count={line_count}"
        ),
        exit_code=1,
        file_path=str(abs_path),
    )
)
PY
