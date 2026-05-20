cmd_status() {
  local plan_id=""
  local frontmatter=false
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --id)
        plan_id="$2"
        shift 2
        ;;
      --frontmatter)
        frontmatter=true
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

  local plan_file
  plan_file="$(plan_file_path "$plan_id")"
  if [[ -f "$plan_file" ]]; then
    echo "ID:          $(yaml_read "$plan_file" "id")"
    echo "Title:       $(yaml_read "$plan_file" "title")"
    echo "Status:      $(yaml_read "$plan_file" "status")"
    echo "Created At:  $(yaml_read "$plan_file" "created_at")"
    echo "Finalized At:$(yaml_read "$plan_file" "finalized_at")"
    echo "Source File: $(yaml_read "$plan_file" "source_file")"
    echo "Review:"
    echo "  Status:    $(yaml_read "$plan_file" "review.status")"
    echo "  Reviewed At: $(yaml_read "$plan_file" "review.reviewed_at")"
    echo "  Review File: $(yaml_read "$plan_file" "review.review_file")"
  elif [[ "$frontmatter" == false ]]; then
    ensure_plan_exists "$plan_id"
  fi

  if [[ "$frontmatter" == true ]]; then
    if [[ -f "$plan_file" ]]; then
      echo
    fi
    echo "Frontmatter:"
    python3 "$DEPS_HELPER" frontmatter "$plan_id"
  fi
}
