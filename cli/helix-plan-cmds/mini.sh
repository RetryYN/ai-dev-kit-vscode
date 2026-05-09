cmd_mini() {
  local title=""
  local source_file=""
  local requested_plan_id=""
  local parent_plan_id=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --title)
        title="$2"
        shift 2
        ;;
      --file)
        source_file="$2"
        shift 2
        ;;
      --plan-id)
        requested_plan_id="$2"
        shift 2
        ;;
      --parent)
        parent_plan_id="$2"
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

  if [[ -z "$parent_plan_id" ]]; then
    echo "エラー: --parent は必須です" >&2
    exit 1
  fi
  if [[ -z "$title" ]]; then
    echo "エラー: --title は必須です" >&2
    exit 1
  fi

  validate_parent_plan_id "$parent_plan_id"
  ensure_dirs

  local plan_id plan_file created_at cycle mini_rel
  if [[ -n "$requested_plan_id" ]]; then
    validate_mini_plan_id "$requested_plan_id"
    plan_id="$requested_plan_id"
  else
    plan_id="$(next_mini_plan_id)"
  fi
  plan_file="$MINI_PLAN_DIR/$plan_id.yaml"
  if [[ -e "$plan_file" ]]; then
    echo "エラー: mini-PLAN は既に存在します: $plan_id" >&2
    exit 1
  fi
  if cycle="$(check_mini_plan_cycle "$plan_id" "$parent_plan_id" 2>/dev/null)"; then
    :
  else
    echo "エラー: mini-PLAN の親子関係が循環します: ${cycle:-$plan_id -> $parent_plan_id}" >&2
    exit 1
  fi
  created_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  python3 - <<'PY' "$plan_file" "$plan_id" "$title" "$created_at" "$source_file" "$parent_plan_id"
import json
import sys
from pathlib import Path

plan_file = Path(sys.argv[1])
plan_id = sys.argv[2]
title = sys.argv[3]
created_at = sys.argv[4]
source_file = sys.argv[5]
parent_plan_id = sys.argv[6]


def q(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


source_line = "null" if source_file == "" else q(source_file)

content = f"""id: {plan_id}
kind: mini-plan
title: {q(title)}
parent_plan_id: {parent_plan_id}
status: draft
created_at: {q(created_at)}
source_file: {source_line}
phases:
  - L1
  - L2
  - L4
  - L6
references: []
artifacts: []
finalized_at: null
review:
  status: pending
  reviewed_at: null
  review_file: null
"""
plan_file.parent.mkdir(parents=True, exist_ok=True)
plan_file.write_text(content, encoding="utf-8")
PY

  mini_rel=".helix/mini-plans/$plan_id.yaml"
  record_mini_plan_relation "$parent_plan_id" "$plan_id" "$mini_rel"

  echo "作成: ${plan_file#$PROJECT_ROOT/}"
  echo "ID: $plan_id"
  echo "Parent: $parent_plan_id"
  echo "Flow: L1 -> L2 -> L4 -> L6"
}
