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
import re
import sys
from pathlib import Path


MAX_BUNDLE_CHARS = 1500
PLAN_LIMIT = 2
MEMORY_LIMIT = 2
KEYWORDS = ("handover", "carry", "継続", "resume", "next action")


def load_payload(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def read_text(path: Path, limit: int = 4000) -> str:
    try:
        return path.read_text(encoding="utf-8")[:limit]
    except Exception:
        return ""


def extract_next_action(project_root: Path) -> str:
    handover_path = project_root / ".helix" / "handover" / "CURRENT.md"
    text = read_text(handover_path, limit=8000)
    match = re.search(r"## Next Action \(Codex 向け\)\n(.*?)(?:\n## |\Z)", text, re.S)
    if not match:
        return ""
    lines = [line.strip() for line in match.group(1).splitlines() if line.strip()]
    return compact_text(" / ".join(lines[:2]))


def extract_plan_ids(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
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
    text = read_text(candidates[0], limit=3500)
    title_match = re.search(r'^title:\s*"?(.*?)"?\s*$', text, re.M)
    heading_match = re.search(r"^#\s+(.+)$", text, re.M)
    title = title_match.group(1).strip() if title_match else (heading_match.group(1).strip() if heading_match else "")
    return compact_text(f"{plan_id}: {title}" if title else plan_id)


def project_memory_dir(project_root: Path) -> Path:
    slug = "-" + str(project_root.resolve()).strip("/").replace("/", "-")
    return Path.home() / ".claude" / "projects" / slug / "memory"


def summarize_memory(path: Path) -> str:
    text = read_text(path, limit=1600)
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


def should_inject(prompt: str) -> bool:
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in KEYWORDS) or bool(re.search(r"\bPLAN-\d+\b", prompt, re.I))


def build_bundle(project_root: Path, payload: dict) -> str:
    prompt = str(payload.get("prompt") or "")
    if not should_inject(prompt):
        return ""

    next_action = extract_next_action(project_root)
    plan_ids = extract_plan_ids(prompt)[:PLAN_LIMIT]
    plans = [summary for summary in (summarize_plan(project_root, plan_id) for plan_id in plan_ids) if summary]
    memories = collect_memory_feedback(project_root)

    lines = ["## HELIX Prompt Bundle"]
    if plans:
        for plan in plans:
            lines.append(f"- plan: {plan}")
    if next_action:
        lines.append(f"- handover: {next_action}")
    for memory in memories:
        lines.append(f"- memory: {memory}")

    return trim_bundle("\n".join(lines), MAX_BUNDLE_CHARS)


payload = load_payload(Path(sys.argv[1]))
project_root = Path(sys.argv[2])
bundle = build_bundle(project_root, payload)
print(
    json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": bundle,
            }
        },
        ensure_ascii=False,
    )
)
PY
