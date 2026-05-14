#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
helix_root="$(cd "$script_dir/../.." && pwd)"
project_root="${CLAUDE_PROJECT_DIR:-$helix_root}"
tmp_input="$(mktemp)"
trap 'rm -f "$tmp_input"' EXIT
cat >"$tmp_input"

if ! result="$(
  python3 - "$helix_root" "$project_root" "$tmp_input" <<'PY'
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
def parse_datetime(raw: str) -> datetime | None:
    value = raw.strip()
    if not value:
        return None
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
def within_window(now: datetime, candidate: datetime) -> bool:
    if now.tzinfo is None and candidate.tzinfo is None:
        delta = now - candidate
    else:
        aware_now = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
        aware_candidate = candidate if candidate.tzinfo is not None else candidate.replace(tzinfo=aware_now.tzinfo)
        delta = aware_now - aware_candidate.astimezone(aware_now.tzinfo)
    return timedelta(0) <= delta <= timedelta(minutes=5)
def main() -> str:
    helix_root = Path(sys.argv[1])
    project_root = Path(sys.argv[2])
    payload_path = Path(sys.argv[3])
    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except Exception:
        return "pass"
    if not isinstance(payload, dict):
        return "pass"
    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
    if tool_name != "AskUserQuestion":
        return "pass"
    sys.path.insert(0, str(helix_root / "cli" / "lib"))
    import helix_db  # type: ignore
    os.environ.pop("HELIX_DB_PATH", None)
    os.environ["HELIX_PROJECT_ROOT"] = str(project_root)
    db_path = Path(helix_db.resolve_default_db_path())
    if not db_path.exists():
        return "warn"

    now = parse_datetime(os.environ.get("HELIX_ASKUSERQUESTION_NOW", "")) or datetime.now()
    try:
        conn = helix_db.get_connection(str(db_path))
    except Exception:
        return "warn"
    try:
        rows = conn.execute(
            "SELECT timestamp FROM invocation_log WHERE role = ? ORDER BY id DESC LIMIT 50",
            ("tl-advisor",),
        ).fetchall()
    finally:
        conn.close()
    for row in rows:
        recorded_at = parse_datetime(str(row["timestamp"] or ""))
        if recorded_at is not None and within_window(now, recorded_at):
            return "pass"
    return "warn"
print(main())
PY
)"; then
  result="warn"
fi

if [[ "$result" == "warn" ]]; then
  warning="[helix] AskUserQuestion 呼び出し前に tl-advisor 相談を推奨します。停滞防止ルール参照: CLAUDE.md §AskUserQuestion 前必須 TL 相談"
  printf '%s\n' "$warning" >&2
  python3 - "$warning" <<'PY'
import json
import sys
print(json.dumps({"systemMessage": sys.argv[1]}, ensure_ascii=False))
PY
fi
exit 0
