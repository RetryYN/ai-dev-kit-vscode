cmd_lint() {
  local duplicates=0
  local v5=0
  local plan_file=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --help|-h)
        usage
        exit 0
        ;;
      --duplicates)
        duplicates=1
        shift
        ;;
      --v5)
        v5=1
        shift
        ;;
      -*)
        echo "エラー: 不明なオプションです: $1" >&2
        exit 1
        ;;
      *)
        if [[ -n "$plan_file" ]]; then
          echo "エラー: plan-file は 1 つだけ指定できます" >&2
          exit 1
        fi
        plan_file="$1"
        shift
        ;;
    esac
  done

  if [[ -z "$plan_file" ]]; then
    echo "エラー: plan-file は必須です" >&2
    exit 1
  fi

  if [[ "$duplicates" -eq 1 && "$v5" -eq 1 ]]; then
    echo "エラー: --v5 と --duplicates は同時に指定できません" >&2
    exit 1
  fi

  if [[ "$duplicates" -eq 1 ]]; then
    python3 "$PLAN_LINT" --duplicates "$plan_file"
    return
  fi

  if [[ "$v5" -eq 1 ]]; then
    python3 "$PLAN_VALIDATOR" "$plan_file"
    return
  fi

  python3 "$PLAN_LINT" "$plan_file"
}
