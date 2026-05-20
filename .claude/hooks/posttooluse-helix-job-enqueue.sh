#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$REPO_ROOT}"

payload_file="$(mktemp)"
trap 'rm -f "$payload_file"' EXIT
cat >"$payload_file" || true

python3 - "$payload_file" "$REPO_ROOT" "$PROJECT_ROOT" <<'PY' || true
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

TARGET_TOOLS = {"Write", "Edit", "MultiEdit"}
TARGET_PATH_RE = re.compile(
    r"(^|/)(PLAN(?:-[^/]+)?\.md|ADR(?:-[^/]+)?\.md)$",
    re.IGNORECASE,
)


def truthy_env(*names: str) -> bool:
    for name in names:
        value = os.environ.get(name, "").strip().lower()
        if value and value not in {"0", "false", "no", "off"}:
            return True
    return False


def env_default_true(*names: str) -> bool:
    for name in names:
        raw = os.environ.get(name, "").strip()
        if not raw:
            continue
        return raw.lower() not in {"0", "false", "no", "off"}
    return True


def load_payload(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


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
    repo_root = Path(sys.argv[2])
    sys.path.insert(0, str(repo_root))
    try:
        from cli.lib import hook_payload  # type: ignore
    except Exception:
        hook_payload = None

    paths: list[str] = []
    seen: set[str] = set()
    candidates: list[str] = []
    if hook_payload is not None:
        safe_paths, _rejected = hook_payload.extract_changed_paths(payload)
        candidates.extend(safe_paths)
    else:
        tool_input = payload.get("tool_input")
        if isinstance(tool_input, dict):
            file_path = tool_input.get("file_path")
            if isinstance(file_path, str):
                candidates.append(file_path)
            file_paths = tool_input.get("file_paths")
            if isinstance(file_paths, list):
                candidates.extend(str(path) for path in file_paths if isinstance(path, str))

    for raw_path in candidates:
        normalized = normalize_path(raw_path, project_root)
        if normalized and normalized not in seen:
            seen.add(normalized)
            paths.append(normalized)
    return paths


def plan_token(path_text: str) -> str:
    match = re.search(r"(PLAN(?:-[A-Za-z0-9._-]+)?\.md|ADR(?:-[A-Za-z0-9._-]+)?\.md)$", path_text, re.IGNORECASE)
    if match:
        return match.group(1)
    return Path(path_text).name or path_text


payload = load_payload(Path(sys.argv[1]))
tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
if tool_name not in TARGET_TOOLS:
    raise SystemExit(0)

project_root = Path(sys.argv[3]).resolve(strict=False)
paths = collect_paths(payload, project_root)
targets = [path for path in paths if TARGET_PATH_RE.search(path)]
if not targets:
    raise SystemExit(0)

consent_required = env_default_true("HELIX_JOB_CONSENT_REQUIRED", "CLAUDE_JOB_CONSENT_REQUIRED")
explicit_consent = truthy_env("HELIX_JOB_EXPLICIT_CONSENT", "HELIX_EXPLICIT_CONSENT")
wbs_match = truthy_env("HELIX_JOB_WBS_MATCH", "HELIX_CURRENT_WBS_MATCH", "HELIX_WBS_MATCH")
handover_match = truthy_env("HELIX_JOB_HANDOVER_MATCH", "HELIX_HANDOVER_MATCH")

authorized_by = "none"
if explicit_consent:
    authorized_by = "explicit_consent"
elif wbs_match:
    authorized_by = "wbs_match"
elif handover_match:
    authorized_by = "handover_match"
elif not consent_required:
    authorized_by = "consent_not_required"

candidate_labels = ", ".join(plan_token(path) for path in targets[:3])
if len(targets) > 3:
    candidate_labels += f" (+{len(targets) - 3})"

if consent_required and authorized_by == "none":
    message = (
        f"[HELIX] {candidate_labels} 更新を検出。"
        " helix job 候補を提示します。"
        " P0 guard 未成立のため enqueue は advisory のみ、worker pop は禁止です"
        " (explicit_consent / wbs_match / handover_match 待ち)。"
    )
else:
    message = (
        f"[HELIX] {candidate_labels} 更新を検出。"
        f" helix job 候補を提示します。承認根拠: {authorized_by}。"
        " この hook 自体は enqueue せず、候補提示のみ行います。"
    )

print(
    json.dumps(
        {
            "decision": "continue",
            "systemMessage": message,
            "candidatePaths": targets,
            "authorizedBy": authorized_by,
            "consentRequired": consent_required,
        },
        ensure_ascii=False,
    )
)
PY

exit 0
