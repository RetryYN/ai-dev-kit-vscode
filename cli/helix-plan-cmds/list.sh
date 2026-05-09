cmd_list() {
  ensure_dirs

  local files=()
  shopt -s nullglob
  files=("$PLAN_DIR"/PLAN-*.yaml)
  shopt -u nullglob

  if [[ ${#files[@]} -eq 0 ]]; then
    echo "プランは登録されていません。"
    return
  fi

  printf "%-10s | %-36s | %-10s | %-16s\n" "ID" "Title" "Status" "Review"
  printf -- "--------------------------------------------------------------------------------\n"
  local f id title status review_status
  for f in $(printf "%s\n" "${files[@]}" | sort); do
    id="$(yaml_read "$f" "id")"
    title="$(yaml_read "$f" "title")"
    status="$(yaml_read "$f" "status")"
    review_status="$(yaml_read "$f" "review.status")"
    printf "%-10s | %-36.36s | %-10s | %-16s\n" "$id" "$title" "$status" "${review_status:-pending}"
  done
}
