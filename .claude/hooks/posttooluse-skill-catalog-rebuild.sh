#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$REPO_ROOT}"
DEBOUNCE_SECONDS="${HELIX_SKILL_CATALOG_REBUILD_DEBOUNCE_SECONDS:-30}"
DEBOUNCE_FILE="${HELIX_SKILL_CATALOG_REBUILD_DEBOUNCE_FILE:-${TMPDIR:-/tmp}/.helix_skill_catalog_rebuild_debounce}"
CACHE_DIR="${HELIX_SKILL_CATALOG_REBUILD_CACHE_DIR:-$PROJECT_ROOT/.helix/cache/recommendations}"
LOG_FILE="${HELIX_SKILL_CATALOG_REBUILD_LOG_FILE:-${TMPDIR:-/tmp}/helix_skill_catalog_rebuild.log}"
REBUILD_COMMAND="${HELIX_SKILL_CATALOG_REBUILD_COMMAND:-helix skill catalog rebuild}"

payload_file="$(mktemp)"
trap 'rm -f "$payload_file"' EXIT
cat >"$payload_file" || true

should_trigger="$(
python3 - "$payload_file" "$PROJECT_ROOT" <<'PY'
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TARGET_TOOLS = {"Edit", "Write", "MultiEdit"}
TARGET_PATH = re.compile(r"^skills/[^/]+/[^/]+/SKILL\.md$")


def normalize_path(raw_path: str, project_root: Path) -> str:
    if not raw_path:
        return ""
    path = Path(raw_path)
    absolute = path if path.is_absolute() else project_root / path
    try:
        return absolute.resolve(strict=False).relative_to(
            project_root.resolve(strict=False)
        ).as_posix()
    except Exception:
        return path.as_posix()


def collect_paths(payload: dict, project_root: Path) -> list[str]:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return []

    paths: list[str] = []
    seen: set[str] = set()
    candidates: list[str] = []
    file_path = tool_input.get("file_path")
    if isinstance(file_path, str):
        candidates.append(file_path)
    file_paths = tool_input.get("file_paths")
    if isinstance(file_paths, list):
        candidates.extend(path for path in file_paths if isinstance(path, str))

    for raw_path in candidates:
        normalized = normalize_path(raw_path, project_root)
        if normalized and normalized not in seen:
            seen.add(normalized)
            paths.append(normalized)
    return paths


try:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
except Exception:
    print("0")
    raise SystemExit(0)

if not isinstance(payload, dict):
    print("0")
    raise SystemExit(0)

tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
if tool_name not in TARGET_TOOLS:
    print("0")
    raise SystemExit(0)

project_root = Path(sys.argv[2]).resolve(strict=False)
paths = collect_paths(payload, project_root)
print("1" if any(TARGET_PATH.fullmatch(path) for path in paths) else "0")
PY
)"

if [[ "$should_trigger" != "1" ]]; then
  exit 0
fi

now="$(date +%s)"
if [[ -f "$DEBOUNCE_FILE" ]]; then
  last_run="$(cat "$DEBOUNCE_FILE" 2>/dev/null || echo 0)"
  if [[ "$last_run" =~ ^[0-9]+$ ]]; then
    elapsed=$((now - last_run))
    if (( elapsed < DEBOUNCE_SECONDS )); then
      exit 0
    fi
  fi
fi
printf '%s\n' "$now" >"$DEBOUNCE_FILE"

if [[ -d "$CACHE_DIR" ]]; then
  rm -f "$CACHE_DIR"/*.json 2>/dev/null || true
fi

(
  cd "$PROJECT_ROOT" || exit 0
  nohup sh -c "$REBUILD_COMMAND" >>"$LOG_FILE" 2>&1 &
) >/dev/null 2>&1 || true

exit 0
