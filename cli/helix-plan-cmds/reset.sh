cmd_reset() {
  local plan_id=""
  local to_status="draft"
  local reason=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --id)
        plan_id="$2"
        shift 2
        ;;
      --to)
        to_status="$2"
        shift 2
        ;;
      --reason)
        reason="$2"
        shift 2
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        echo "エラー: 不明なオプションです: $1" >&2
        exit 1
        ;;
    esac
  done

  if [[ -z "$plan_id" ]]; then
    echo "エラー: --id は必須です" >&2
    exit 1
  fi
  if [[ "$to_status" != "draft" && "$to_status" != "reviewed" ]]; then
    echo "エラー: --to は draft または reviewed のみ指定できます (現在: $to_status)" >&2
    exit 1
  fi
  validate_plan_id "$plan_id"
  ensure_plan_exists "$plan_id"
  ensure_dirs

  local plan_file result
  plan_file="$(plan_file_path "$plan_id")"

  set +e
  result="$(python3 - <<'PY' "$SCRIPT_DIR/lib" "$HELIX_DIR/helix.db" "$plan_file" "$plan_id" "$to_status" "$reason"
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

lib_dir = Path(sys.argv[1])
db_path = sys.argv[2]
plan_file = Path(sys.argv[3])
plan_id = sys.argv[4]
to_status = sys.argv[5]
reason = sys.argv[6]
sys.path.insert(0, str(lib_dir))

import helix_db
import yaml_parser

plan_text = plan_file.read_text(encoding="utf-8")
data = yaml_parser.parse_yaml(plan_text)
current_status = data.get("status")
if current_status not in ("finalized", "reviewed"):
    print(
        f"エラー: reset 可能な status は finalized/reviewed のみです (現在: {current_status})",
        file=sys.stderr,
    )
    sys.exit(1)
if current_status == "reviewed" and to_status == "reviewed":
    print("エラー: 既に reviewed のため reset は不要です", file=sys.stderr)
    sys.exit(1)

review = data.get("review")
if not isinstance(review, dict):
    review = {}

history = data.get("revision_history")
if history is None:
    history = []
if not isinstance(history, list):
    print("エラー: revision_history が配列ではありません", file=sys.stderr)
    sys.exit(1)

revision = len(history) + 1
entry = {
    "revision": revision,
    "action": "plan_reset",
    "from_status": current_status,
    "to_status": to_status,
    "reset_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "reason": reason if reason else None,
    "reviewed_at": review.get("reviewed_at"),
    "verdict": review.get("status"),
    "review_file": review.get("review_file"),
    "finalized_at": data.get("finalized_at"),
}

data["status"] = to_status
data["finalized_at"] = None
if to_status == "draft":
    review["status"] = None
    data["review"] = review
data["revision_history"] = history + [entry]

plan_file.write_text(yaml_parser._build_output_with_header(plan_text, data), encoding="utf-8")

helix_db.insert_event(
    db_path,
    "plan_reset",
    {
        "plan_id": plan_id,
        "from_status": current_status,
        "to_status": to_status,
        "reason": reason if reason else None,
        "revision": revision,
    },
    source="helix-plan",
)

print(json.dumps({"from_status": current_status, "to_status": to_status, "revision": revision}, ensure_ascii=False))
PY
)"
  local reset_exit=$?
  set -e
  if [[ $reset_exit -ne 0 ]]; then
    exit $reset_exit
  fi

  local from_status revision
  from_status="$(python3 - <<'PY' "$result"
import json, sys
print(json.loads(sys.argv[1])["from_status"])
PY
)"
  revision="$(python3 - <<'PY' "$result"
import json, sys
print(json.loads(sys.argv[1])["revision"])
PY
)"

  echo "reset 完了: $plan_id ($from_status -> $to_status, revision=$revision)"
}
