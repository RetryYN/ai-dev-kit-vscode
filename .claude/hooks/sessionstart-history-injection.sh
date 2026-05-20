#!/usr/bin/env bash
set -u -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$REPO_ROOT}"
PAYLOAD_FILE="$(mktemp)"
trap 'rm -f "$PAYLOAD_FILE"' EXIT
cat >"$PAYLOAD_FILE" || true

if ! command -v python3 >/dev/null 2>&1; then
  exit 0
fi

python3 - "$PAYLOAD_FILE" "$PROJECT_ROOT" "$REPO_ROOT" <<'PY'
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


MAX_BUNDLE_CHARS = 1800
TRANSCRIPT_CHARS = 700
PLAN_LIMIT = 2
MEMORY_LIMIT = 2


def load_payload(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def normalize_session_type(raw: str) -> str:
    value = (raw or "").strip().lower()
    mapping = {
        "clear": "cleared",
        "cleared": "cleared",
        "compact": "compacted",
        "compacted": "compacted",
        "startup": "new",
        "resume": "new",
        "new": "new",
    }
    return mapping.get(value, "new")


def read_text(path: Path, limit: int = 4000) -> str:
    try:
        return path.read_text(encoding="utf-8")[:limit]
    except Exception:
        return ""


def compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_next_action(project_root: Path) -> str:
    handover_path = project_root / ".helix" / "handover" / "CURRENT.md"
    text = read_text(handover_path, limit=8000)
    if not text:
        return ""
    match = re.search(r"## Next Action \(Codex 向け\)\n(.*?)(?:\n## |\Z)", text, re.S)
    if not match:
        return ""
    lines = [line.strip() for line in match.group(1).splitlines() if line.strip()]
    return compact_text(" / ".join(lines[:2]))


def extract_plan_ids(*texts: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for plan_id in re.findall(r"\bPLAN-\d+\b", text or "", flags=re.IGNORECASE):
            normalized = plan_id.upper()
            if normalized not in seen:
                seen.add(normalized)
                found.append(normalized)
    return found


def summarize_plan(project_root: Path, plan_id: str) -> str:
    plans_dir = project_root / "docs" / "plans"
    candidates = sorted(plans_dir.glob(f"{plan_id}-*.md"))
    if not candidates:
        return ""
    text = read_text(candidates[0], limit=4000)
    if not text:
        return ""
    title_match = re.search(r'^title:\s*"?(.*?)"?\s*$', text, re.M)
    heading_match = re.search(r"^#\s+(.+)$", text, re.M)
    title = ""
    if title_match:
        title = title_match.group(1).strip()
    elif heading_match:
        title = heading_match.group(1).strip()
    return compact_text(f"{plan_id}: {title}" if title else plan_id)


def project_memory_dir(project_root: Path) -> Path:
    slug = "-" + str(project_root.resolve()).strip("/").replace("/", "-")
    return Path.home() / ".claude" / "projects" / slug / "memory"


def summarize_memory(path: Path) -> str:
    text = read_text(path, limit=2000)
    if not text:
        return ""
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    snippet = lines[0] if lines else ""
    return compact_text(f"{path.stem}: {snippet}")[:220]


def collect_memory_feedback(project_root: Path) -> list[str]:
    memory_dir = project_memory_dir(project_root)
    if not memory_dir.exists():
        return []
    items: list[str] = []
    for path in sorted(memory_dir.glob("feedback_*.md"), key=lambda item: item.stat().st_mtime, reverse=True):
        summary = summarize_memory(path)
        if summary:
            items.append(summary)
        if len(items) >= MEMORY_LIMIT:
            break
    return items


def trim_bundle(text: str, limit: int) -> str:
    compact = text.strip()
    if len(compact) <= limit:
        return compact
    if limit <= 1:
        return compact[:limit]
    return compact[: limit - 1].rstrip() + "…"


def build_bundle(project_root: Path, payload: dict) -> str:
    session_type = normalize_session_type(
        os.environ.get("HELIX_SESSION_TYPE")
        or str(payload.get("source") or payload.get("session_type") or "")
    )
    if session_type not in {"cleared", "compacted"}:
        return ""

    transcript_path = (
        os.environ.get("TRANSCRIPT_PATH")
        or os.environ.get("HELIX_TRANSCRIPT_PATH")
        or str(payload.get("transcript_path") or "")
    )
    transcript_summary = ""
    if transcript_path:
        try:
            sys.path.insert(0, str((Path(sys.argv[3]) / "cli" / "lib").resolve()))
            import transcript_summary as transcript_summary_lib  # type: ignore

            transcript_summary = transcript_summary_lib.summarize_transcript(transcript_path, max_chars=TRANSCRIPT_CHARS)
        except Exception:
            transcript_summary = ""

    next_action = extract_next_action(project_root)
    plan_ids = extract_plan_ids(next_action, transcript_summary)[:PLAN_LIMIT]
    plans = [summary for summary in (summarize_plan(project_root, plan_id) for plan_id in plan_ids) if summary]
    memories = collect_memory_feedback(project_root)

    lines = [
        "## HELIX Resume Bundle",
        f"- session_type: {session_type}",
    ]
    if next_action:
        lines.append(f"- handover: {next_action}")
    for plan in plans:
        lines.append(f"- plan: {plan}")
    for memory in memories:
        lines.append(f"- memory: {memory}")
    if transcript_summary:
        lines.append(f"- transcript: {compact_text(transcript_summary)}")

    return trim_bundle("\n".join(lines), MAX_BUNDLE_CHARS)


payload = load_payload(Path(sys.argv[1]))
project_root = Path(sys.argv[2])
bundle = build_bundle(project_root, payload)
print(
    json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": bundle,
            }
        },
        ensure_ascii=False,
    )
)
PY
