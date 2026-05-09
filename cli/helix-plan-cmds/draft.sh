create_design_skeleton() {
  local plan_id="$1"
  local title="$2"
  python3 - <<'PY' "$PROJECT_ROOT" "$plan_id" "$title"
import sys
from pathlib import Path

project_root = Path(sys.argv[1])
plan_id = sys.argv[2]
title = sys.argv[3]

for shard in ("D-API", "D-DB", "D-ARCH", "D-TEST", "D-THREAT"):
    shard_dir = project_root / "docs" / "features" / plan_id / shard
    shard_dir.mkdir(parents=True, exist_ok=True)
    readme = shard_dir / "README.md"
    if readme.exists():
        continue
    readme.write_text(
        f"> 目的: {title} の {shard} 設計\n\n"
        "## Overview\n\n"
        "## Decisions\n\n"
        "## Acceptance\n",
        encoding="utf-8",
    )
PY
}

cmd_draft() {
  local title=""
  local source_file=""
  local requested_plan_id=""
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

  if [[ -z "$title" ]]; then
    echo "エラー: --title は必須です" >&2
    exit 1
  fi

  ensure_dirs

  local plan_id plan_file created_at
  if [[ -n "$requested_plan_id" ]]; then
    validate_plan_id "$requested_plan_id"
    plan_id="$requested_plan_id"
  else
    plan_id="$(next_plan_id)"
  fi
  plan_file="$PLAN_DIR/$plan_id.yaml"
  if [[ -e "$plan_file" ]]; then
    echo "エラー: プランは既に存在します: $plan_id" >&2
    exit 1
  fi
  created_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  python3 - <<'PY' "$plan_file" "$plan_id" "$title" "$created_at" "$source_file"
import json
import sys
from pathlib import Path

plan_file = Path(sys.argv[1])
plan_id = sys.argv[2]
title = sys.argv[3]
created_at = sys.argv[4]
source_file = sys.argv[5]


def q(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


source_line = "null" if source_file == "" else q(source_file)

content = f"""id: {plan_id}
title: {q(title)}
status: draft
created_at: {q(created_at)}
source_file: {source_line}
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

  create_design_skeleton "$plan_id" "$title"

  echo "作成: ${plan_file#$PROJECT_ROOT/}"
  echo "ID: $plan_id"
  echo "D-shard skeleton: docs/features/$plan_id/"
}
