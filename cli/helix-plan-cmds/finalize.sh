cmd_finalize() {
  local plan_id=""
  local no_lint=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --id)
        plan_id="$2"
        shift 2
        ;;
      --no-lint)
        no_lint=1
        shift
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
  validate_plan_id "$plan_id"
  ensure_plan_exists "$plan_id"

  local plan_file review_status
  plan_file="$(plan_file_path "$plan_id")"
  review_status="$(yaml_read "$plan_file" "review.status")"

  if [[ "$review_status" != "approve" ]]; then
    echo "エラー: TL review が approve ではないため finalize できません (review.status=$review_status)" >&2
    exit 1
  fi

  if [[ "$no_lint" -eq 0 ]]; then
    local docs_path
    docs_path="$(python3 - <<'PY' "$SCRIPT_DIR/lib" "$plan_file"
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])

import plan_frontmatter
import yaml_parser

plan_path = Path(sys.argv[2])
plan_data = yaml_parser.parse_yaml(plan_path.read_text(encoding="utf-8"))

try:
    resolved = plan_frontmatter.resolve_plan_doc_path(plan_path, plan_data)
except plan_frontmatter.PlanFrontmatterError as exc:
    if "PLAN markdown not found" in str(exc):
        print("__YAML_ONLY__")
        raise SystemExit(0)
    raise

docs_text = resolved.read_text(encoding="utf-8")
try:
    plan_frontmatter._parse_frontmatter(docs_text)
except plan_frontmatter.PlanFrontmatterError as exc:
    if "must start with YAML frontmatter" in str(exc):
        print("__YAML_ONLY__")
        raise SystemExit(0)
    raise

print(resolved)
PY
)"

    if [[ "$docs_path" == "__YAML_ONLY__" ]]; then
      echo "[helix-plan] auto-lint skipped: legacy YAML-only PLAN ($plan_id)"
    else
      local lint_output lint_status duplicate_count
      set +e
      lint_output="$(python3 "$PLAN_LINT" --duplicates "$docs_path" 2>&1)"
      lint_status=$?
      set -e
      duplicate_count="$(printf '%s\n' "$lint_output" | awk 'NR > 2 && /^\| / {count++} END {print count+0}')"

      if [[ "$lint_status" -ne 0 || "$duplicate_count" -gt 0 ]]; then
        echo "エラー: duplicate detected のため finalize を中止しました: $plan_id" >&2
        printf '%s\n' "$lint_output" >&2
        exit 1
      fi
    fi
  fi

  local finalized_on
  finalized_on="$(date -u +"%Y-%m-%d")"
  python3 "$PLAN_FRONTMATTER" finalize "$plan_file" "$finalized_on"

  echo "finalize 完了: $plan_id"
}
