#!/usr/bin/env bash
set -u -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$REPO_ROOT}"
PAYLOAD_FILE="$(mktemp)"
trap 'rm -f "$PAYLOAD_FILE"' EXIT
cat >"$PAYLOAD_FILE"

emit_continue_json() {
  local message="$1"
  local escaped="${message//\\/\\\\}"
  escaped="${escaped//\"/\\\"}"
  escaped="${escaped//$'\n'/ }"
  printf '{"decision":"continue","systemMessage":"%s"}\n' "$escaped"
}

if ! command -v python3 >/dev/null 2>&1; then
  emit_continue_json "WARNING: plan auto-register skipped (python3 not available)"
  exit 0
fi

python3 - "$PAYLOAD_FILE" "$PROJECT_ROOT" "$REPO_ROOT" <<'PY'
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path


def emit(payload: dict[str, str]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def load_payload(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def extract_path(payload: dict) -> str:
    for section_name in ("tool_result", "tool_response", "tool_input"):
        section = payload.get(section_name)
        if not isinstance(section, dict):
            continue
        for key in ("filePath", "file_path", "path"):
            value = section.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def resolve_path(raw_path: str, project_root: Path) -> tuple[Path, str]:
    abs_path = Path(raw_path)
    if not abs_path.is_absolute():
        abs_path = project_root / abs_path
    try:
        rel_path = abs_path.resolve(strict=False).relative_to(project_root.resolve(strict=False)).as_posix()
    except Exception:
        rel_path = abs_path.as_posix()
    return abs_path, rel_path


def is_target_path(rel_path: str) -> bool:
    path = Path(rel_path)
    if path.parts[:2] == ("docs", "plans") and path.name.startswith("PLAN-") and path.suffix == ".md":
        return True
    if path.parts[:2] == ("docs", "adr") and path.name.startswith("ADR-") and path.suffix == ".md":
        return True
    return False


def load_plan_modules(repo_root: Path):
    sys.path.insert(0, str(repo_root / "cli" / "lib"))
    import plan_parser  # type: ignore
    from migrations import v35_plan_registry  # type: ignore

    return plan_parser, v35_plan_registry


def resolve_db_path(doc_path: Path, project_root: Path) -> Path:
    resolved_project_root = project_root.resolve(strict=False)
    for parent in doc_path.resolve(strict=False).parents:
        helix_dir = parent / ".helix"
        if helix_dir.is_dir():
            return helix_dir / "helix.db"
        if parent == resolved_project_root:
            break
    return project_root / ".helix" / "helix.db"


def record_failure(
    repo_root: Path,
    project_root: Path,
    doc_path: Path,
    failure_type: str,
    context: dict,
    plan_id: str | None = None,
) -> None:
    try:
        _, v35_plan_registry = load_plan_modules(repo_root)
        db_path = resolve_db_path(doc_path, project_root)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        try:
            v35_plan_registry.migrate_v34_to_v35(conn)
            with conn:
                conn.execute(
                    "INSERT INTO failure_log (failure_type, context, plan_id) VALUES (?, ?, ?)",
                    (failure_type, json.dumps(context, ensure_ascii=False), plan_id),
                )
        finally:
            conn.close()
    except Exception:
        return


def main() -> int:
    payload_path = Path(sys.argv[1])
    project_root = Path(sys.argv[2])
    repo_root = Path(sys.argv[3])
    parser_path = repo_root / "cli" / "lib" / "plan_parser.py"

    raw_path = extract_path(load_payload(payload_path))
    if not raw_path:
        return 0

    abs_path, rel_path = resolve_path(raw_path, project_root)
    if not is_target_path(rel_path):
        return 0

    (project_root / ".helix").mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["python3", str(parser_path), str(abs_path), "--mode", "upsert"],
        capture_output=True,
        text=True,
        check=False,
        cwd=project_root,
    )
    if proc.returncode != 0:
        record_failure(
            repo_root,
            project_root,
            abs_path,
            "hook_error",
            {"doc_path": rel_path, "stderr": proc.stderr.strip(), "returncode": proc.returncode},
        )
        emit({"decision": "continue", "systemMessage": f"WARNING: plan auto-register failed ({rel_path})"})
        return 0

    stdout = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    if not stdout:
        record_failure(
            repo_root,
            project_root,
            abs_path,
            "parse_error",
            {"doc_path": rel_path, "stderr": proc.stderr.strip()},
        )
        emit({"decision": "continue", "systemMessage": f"WARNING: frontmatter parse 失敗 ({rel_path})"})
        return 0

    try:
        result = json.loads(stdout[-1])
    except json.JSONDecodeError:
        record_failure(
            repo_root,
            project_root,
            abs_path,
            "hook_error",
            {"doc_path": rel_path, "stdout": proc.stdout, "stderr": proc.stderr.strip()},
        )
        emit({"decision": "continue", "systemMessage": f"WARNING: plan auto-register failed ({rel_path})"})
        return 0

    plan_id = str(result.get("plan_id") or Path(rel_path).stem)
    status = str(result.get("status") or "unknown")
    counts = result.get("counts") if isinstance(result.get("counts"), dict) else {}

    if status == "parse_error":
        emit({"decision": "continue", "systemMessage": f"WARNING: frontmatter parse 失敗 ({rel_path})"})
        return 0

    try:
        plan_parser, _ = load_plan_modules(repo_root)
        db_path = resolve_db_path(abs_path, project_root)
        conn = sqlite3.connect(str(db_path))
        try:
            cycle = plan_parser.detect_cycle(conn, plan_id)
        finally:
            conn.close()
    except Exception as exc:
        record_failure(
            repo_root,
            project_root,
            abs_path,
            "hook_error",
            {"doc_path": rel_path, "reason": f"cycle check failed: {exc}"},
            plan_id,
        )
        emit({"decision": "continue", "systemMessage": f"WARNING: dependency cycle check skipped ({rel_path})"})
        return 0

    if cycle:
        record_failure(
            repo_root,
            project_root,
            abs_path,
            "cycle_detected",
            {"doc_path": rel_path, "cycle": cycle},
            plan_id,
        )
        emit(
            {
                "decision": "block",
                "message": (
                    "dependency cycle detected: "
                    + " → ".join(cycle)
                    + ". 循環依存を解消してから再保存してください。"
                ),
            }
        )
        return 2

    emit(
        {
            "decision": "continue",
            "systemMessage": (
                f"plan_registry 登録完了: {plan_id} "
                f"(status: {status}, dependencies: {counts.get('dependencies', 0)}, "
                f"generates: {counts.get('generates', 0)})"
            ),
        }
    )
    return 0


raise SystemExit(main())
PY
status=$?

if [[ "$status" -eq 2 ]]; then
  exit 2
fi
exit 0
