#!/usr/bin/env bats

setup() {
  REPO_ROOT="/home/tenni/ai-dev-kit-vscode"
  CLI="$REPO_ROOT/cli/helix-drift-check"
  TMP_ROOT="$(mktemp -d)"
  PROJ="$TMP_ROOT/proj"
  FAKE_BIN="$TMP_ROOT/bin"

  mkdir -p "$PROJ/.helix" "$FAKE_BIN"

  cat > "$FAKE_BIN/jq" <<'JQEOF'
#!/usr/bin/env bash
set -euo pipefail
id=""
file=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -c)
      shift
      ;;
    --arg)
      if [[ "${2:-}" == "id" ]]; then
        id="${3:-}"
      fi
      shift 3
      ;;
    *)
      file="$1"
      shift
      ;;
  esac
done

if [[ -n "$id" ]] && [[ -f "$file" ]] && grep -q '"id"[[:space:]]*:[[:space:]]*"'"$id"'"' "$file"; then
  echo "{\"id\":\"$id\",\"layer\":\"L6\"}"
fi
JQEOF
  chmod +x "$FAKE_BIN/jq"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

@test "D-PERF/custom.md は汎用 drift メッセージを stderr に出す" {
  mkdir -p "$PROJ/docs/features/auth/D-PERF"
  printf 'performance spec\n' > "$PROJ/docs/features/auth/D-PERF/custom.md"

  cat > "$PROJ/.helix/index.json" <<'JSONEOF'
{
  "rules": {
    "deliverables": [
      { "id": "D-PERF", "layer": "L6" }
    ]
  }
}
JSONEOF

  run bash -lc "PATH='$FAKE_BIN':\$PATH HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' '$PROJ/docs/features/auth/D-PERF/custom.md' 1>'$TMP_ROOT/out.log' 2>'$TMP_ROOT/err.log'"

  [ "$status" -eq 0 ]
  grep -q '\[drift-check\] generic deliverable change: D-PERF' "$TMP_ROOT/err.log"
}

@test "D-API/contract.yaml は従来どおり API チェック分岐に入る" {
  mkdir -p "$PROJ/docs/features/auth/D-API"
  printf 'openapi: 3.0.0\n' > "$PROJ/docs/features/auth/D-API/contract.yaml"

  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' '$PROJ/docs/features/auth/D-API/contract.yaml' >'$TMP_ROOT/out.log' 2>'$TMP_ROOT/err.log'"

  [ "$status" -eq 0 ]
  grep -q '\[helix-drift\] D-API 変更検出:' "$TMP_ROOT/out.log"
}

@test ".helix/index.json がない場合は警告を出して exit 0" {
  mkdir -p "$PROJ/docs/features/auth/D-AUDIT"
  printf 'audit note\n' > "$PROJ/docs/features/auth/D-AUDIT/custom.md"
  rm -f "$PROJ/.helix/index.json"

  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' '$PROJ/docs/features/auth/D-AUDIT/custom.md' 1>'$TMP_ROOT/out.log' 2>'$TMP_ROOT/err.log'"

  [ "$status" -eq 0 ]
  grep -q '\[drift-check\] WARN: missing index.json' "$TMP_ROOT/err.log"
}
