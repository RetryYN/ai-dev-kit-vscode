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
    hook_verdict = "pass"
    sys.path.insert(0, str(helix_root / "cli" / "lib"))
    import helix_db  # type: ignore
    os.environ["HELIX_PROJECT_ROOT"] = str(project_root)
    db_path = Path(helix_db.resolve_default_db_path())
    def parse_optional_int(raw: str) -> int | None:
        value = (raw or "").strip()
        if value.isdigit():
            return int(value)
        return None
    run_id = parse_optional_int(os.environ.get("HELIX_AUTOMATION_RUN_ID", ""))
    now = parse_datetime(os.environ.get("HELIX_ASKUSERQUESTION_NOW", "")) or datetime.now()
    if tool_name == "AskUserQuestion":
        if not db_path.exists():
            hook_verdict = "warn"
        else:
            try:
                conn = helix_db.get_connection(str(db_path))
            except Exception:
                hook_verdict = "warn"
            else:
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
                        hook_verdict = "pass"
                        break
                else:
                    hook_verdict = "warn"

    def record_audit(audit_kind: str, payload_dict: dict[str, object | None]) -> None:
        safe_payload = {key: value for key, value in payload_dict.items() if value is not None}
        with helix_db._write_connection(str(db_path)) as conn:
            helix_db.insert_audit_log(
                conn,
                audit_kind=audit_kind,
                actor="pretooluse-askuserquestion.sh",
                run_id=run_id,
                payload=safe_payload,
            )

    try:
        record_audit(
            "hook_exec",
            {
                "hook_name": "pretooluse-askuserquestion",
                "tool_name": tool_name or None,
                "project_root": str(project_root),
            },
        )
        if tool_name == "AskUserQuestion":
            record_audit(
                "gate_eval",
                {
                    "gate_name": "tl_advisor_recent_check",
                    "tool_name": tool_name,
                    "verdict": hook_verdict,
                },
            )
    except Exception:
        pass
    return hook_verdict
print(main())
PY
)"; then
  result="warn"
fi

if [[ "$result" == "warn" ]]; then
  # env バイパス: ユーザー選好など TL 判断不要の質問は理由を evidence に残して許可する
  # (既存の HELIX_ALLOW_RAW_* パターン踏襲)。
  if [[ "${HELIX_ALLOW_ASKUSER:-0}" == "1" ]]; then
    note="[helix] AskUserQuestion: TL 相談チェックを HELIX_ALLOW_ASKUSER=1 でバイパス。理由: ${HELIX_ASKUSER_REASON:-未記載}"
    printf '%s\n' "$note" >&2
    python3 - "$note" <<'PY'
import json
import sys
print(json.dumps({"systemMessage": sys.argv[1]}, ensure_ascii=False))
PY
    exit 0
  fi

  # fail-close: 直近 5 分以内に tl-advisor 相談が無ければ AskUserQuestion を deny。
  # 技術判断はユーザーに振る前に TL へ通す (停滞防止ルール、CLAUDE.md §AskUserQuestion 前 TL 相談)。
  reason="[helix] AskUserQuestion をブロックしました。直近 5 分以内に tl-advisor 相談がありません。先に 'helix codex --role tl-advisor' で技術判断を諮ってから質問してください。ユーザー選好など TL 不要の質問は HELIX_ALLOW_ASKUSER=1 HELIX_ASKUSER_REASON=<理由> でバイパス可。正本: helix/CLAUDE_RUNTIME_ADAPTER.md §2 (AskUserQuestion 前 TL 相談)"
  printf '%s\n' "$reason" >&2
  python3 - "$reason" <<'PY'
import json
import sys
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": sys.argv[1],
    }
}, ensure_ascii=False))
PY
fi
exit 0
