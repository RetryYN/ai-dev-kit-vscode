cmd_generates() {
  local target=""
  local reverse=false
  local json=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --reverse)
        reverse=true
        shift
        ;;
      --json)
        json=true
        shift
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      -*)
        echo "エラー: 不明なオプションです: $1" >&2
        exit 1
        ;;
      *)
        if [[ -n "$target" ]]; then
          echo "エラー: 引数は 1 つだけ指定できます" >&2
          exit 1
        fi
        target="$1"
        shift
        ;;
    esac
  done

  if [[ -z "$target" ]]; then
    if [[ "$reverse" == true ]]; then
      echo "エラー: --reverse では artifact_path が必須です" >&2
    else
      echo "エラー: plan id は必須です" >&2
    fi
    exit 1
  fi

  local args=("generates")
  if [[ "$reverse" == true ]]; then
    args+=("--reverse" "$target")
  else
    validate_plan_id "$target"
    args+=("$target")
  fi
  if [[ "$json" == true ]]; then
    args+=("--json")
  fi

  python3 "$GENERATES_HELPER" "${args[@]}"
}
