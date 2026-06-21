#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$REPO_ROOT}"
HOOK_TOKEN="posttooluse-code-catalog-register"
PAYLOAD_FILE="$(mktemp)"
trap 'rm -f "$PAYLOAD_FILE"' EXIT
cat >"$PAYLOAD_FILE" || true

emit_continue_json() {
  local message="$1"
  local escaped="${message//\\/\\\\}"
  escaped="${escaped//\"/\\\"}"
  escaped="${escaped//$'\n'/ }"
  printf '{"decision":"continue","systemMessage":"%s"}\n' "$escaped"
}

hook_running_exact_match() {
  local token="$1"
  local item
  IFS=',' read -r -a items <<<"${HELIX_HOOK_RUNNING:-}"
  for item in "${items[@]}"; do
    if [[ "$item" == "$token" ]]; then
      return 0
    fi
  done
  return 1
}

if hook_running_exact_match "$HOOK_TOKEN"; then
  emit_continue_json "INFO: code catalog register skipped (reentry guard)"
  exit 0
fi

if [[ ! -s "$PAYLOAD_FILE" ]]; then
  emit_continue_json "WARNING: code catalog register skipped (empty payload)"
  exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
  emit_continue_json "WARNING: code catalog register skipped (python3 not available)"
  exit 0
fi

export HELIX_HOOK_RUNNING="${HELIX_HOOK_RUNNING:+$HELIX_HOOK_RUNNING,}$HOOK_TOKEN"

OUT="$(
python3 - "$PAYLOAD_FILE" "$PROJECT_ROOT" "$REPO_ROOT" <<'PY'
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

TARGET_TOOLS = {"Edit", "Write", "MultiEdit"}
NOOP_SENTINEL = "__HELIX_CODE_CATALOG_REGISTER_NOOP__"


def emit(payload: dict[str, str]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def emit_noop() -> None:
    print(NOOP_SENTINEL)


def load_payload(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        emit(
            {
                "decision": "continue",
                "systemMessage": "WARNING: code catalog register skipped (invalid payload)",
            }
        )
        raise SystemExit(0)
    if not isinstance(payload, dict):
        emit(
            {
                "decision": "continue",
                "systemMessage": "WARNING: code catalog register skipped (invalid payload)",
            }
        )
        raise SystemExit(0)
    return payload


def normalize_path(raw_path: str, project_root: Path) -> str:
    path = Path(raw_path)
    absolute = path if path.is_absolute() else project_root / path
    try:
        return absolute.resolve(strict=False).relative_to(project_root.resolve(strict=False)).as_posix()
    except Exception:
        return path.as_posix()


def unique_paths(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


def main() -> int:
    payload_path = Path(sys.argv[1])
    project_root = Path(sys.argv[2]).resolve(strict=False)
    repo_root = Path(sys.argv[3]).resolve(strict=False)

    sys.path.insert(0, str(repo_root / "cli" / "lib"))
    import code_catalog  # type: ignore
    import hook_payload  # type: ignore
    from functional_registry_checks import RegistryLoadError, load_functional_registry  # type: ignore

    payload = load_payload(payload_path)
    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
    if tool_name and tool_name not in TARGET_TOOLS:
        emit_noop()
        return 0

    safe_paths, _rejected = hook_payload.extract_changed_paths(payload)
    normalized_paths = unique_paths([normalize_path(path, project_root) for path in safe_paths if path])

    target_paths = [
        path
        for path in normalized_paths
        if path.startswith("cli/")
        and path.endswith(".py")
        and not code_catalog.is_non_indexable_path(path)
    ]
    if not target_paths:
        emit_noop()
        return 0

    jsonl_path = project_root / ".helix" / "cache" / "code-catalog.jsonl"
    db_path = project_root / ".helix" / "helix.db"

    try:
        code_catalog.upsert_catalog_paths(project_root, target_paths, jsonl_path, db_path)
    except Exception as exc:
        emit(
            {
                "decision": "continue",
                "systemMessage": f"WARNING: code catalog register failed ({exc})",
            }
        )
        return 0

    messages = [f"code_catalog updated: {', '.join(target_paths)}"]

    registry_path = project_root / "cli" / "config" / "functional-registry.yaml"
    if registry_path.is_file():
        try:
            registered_paths = {
                path
                for entry in load_functional_registry(registry_path)
                for path in entry.code_paths
            }
            unregistered = [path for path in target_paths if path not in registered_paths]
            if unregistered:
                messages.append(
                    "WARNING: functional-registry missing code_paths entry for "
                    + ", ".join(unregistered)
                )
        except RegistryLoadError as exc:
            messages.append(f"WARNING: functional-registry check skipped ({exc})")
    else:
        messages.append("WARNING: functional-registry check skipped (yaml missing)")

    emit({"decision": "continue", "systemMessage": " | ".join(messages)})
    return 0


try:
    raise SystemExit(main())
except SystemExit:
    raise
except Exception as exc:
    emit(
        {
            "decision": "continue",
            "systemMessage": f"WARNING: code catalog register failed ({exc})",
        }
    )
    raise SystemExit(0)
PY
)"; PYTHON_STATUS=$?

if [[ $PYTHON_STATUS -ne 0 ]]; then
  emit_continue_json "WARNING: code catalog register skipped (python execution failed)"
  exit 0
fi

if [[ -z "$OUT" ]]; then
  emit_continue_json "WARNING: code catalog register skipped (python produced no output)"
  exit 0
fi

if [[ "$OUT" == "__HELIX_CODE_CATALOG_REGISTER_NOOP__" ]]; then
  exit 0
fi

printf '%s\n' "$OUT"

exit 0
