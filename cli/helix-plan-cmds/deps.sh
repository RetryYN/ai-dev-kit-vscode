cmd_deps() {
  local plan_id=""
  local depth=1
  local json=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --depth)
        depth="$2"
        shift 2
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
        if [[ -n "$plan_id" ]]; then
          echo "エラー: plan id は 1 つだけ指定できます" >&2
          exit 1
        fi
        plan_id="$1"
        shift
        ;;
    esac
  done

  if [[ -z "$plan_id" ]]; then
    echo "エラー: plan id は必須です" >&2
    exit 1
  fi

  validate_plan_id "$plan_id"

  local args=("deps" "$plan_id" "--depth" "$depth")
  if [[ "$json" == true ]]; then
    args+=("--json")
  fi

  python3 "$DEPS_HELPER" "${args[@]}"
}
