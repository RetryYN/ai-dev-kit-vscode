#!/usr/bin/env bats

setup() {
  REPO_ROOT="/home/tenni/ai-dev-kit-vscode"
  CLI="$REPO_ROOT/cli/helix-drift-check"
  TMP_ROOT="$(mktemp -d)"
  PROJ="$TMP_ROOT/proj"

  mkdir -p "$PROJ/.helix"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

@test "generic deliverable は index.json から検出されれば generic deliverable change になる" {
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

  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' '$PROJ/docs/features/auth/D-PERF/custom.md' 1>'$TMP_ROOT/out.log' 2>'$TMP_ROOT/err.log'"

  [ "$status" -eq 0 ]
  grep -q '\[drift-check\] generic deliverable change: D-PERF' "$TMP_ROOT/err.log"
  ! grep -q '\[drift-check\] unknown deliverable: D-PERF' "$TMP_ROOT/err.log"
}
