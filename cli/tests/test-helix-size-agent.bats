#!/usr/bin/env bats

setup() {
  REPO_ROOT="/home/tenni/ai-dev-kit-vscode"
  CLI="$REPO_ROOT/cli/helix-size"
  TMP_ROOT="$(mktemp -d)"
  PROJ="$TMP_ROOT/proj"
  mkdir -p "$PROJ"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

@test "--agent --large で 2 段設計推奨を出す" {
  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' --agent --large --type new-feature --json >'$TMP_ROOT/out.json' 2>'$TMP_ROOT/err.log'"
  [ "$status" -eq 0 ]
  grep -q '"size": "L"' "$TMP_ROOT/out.json"
  grep -q '"drive": "agent"' "$TMP_ROOT/out.json"
  grep -q '2 段設計推奨' "$TMP_ROOT/err.log"
}

@test "--drive agent だけでは通常の agent 判定のまま" {
  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' --files 3 --lines 50 --drive agent --type new-feature --json >'$TMP_ROOT/out.json' 2>'$TMP_ROOT/err.log'"
  [ "$status" -eq 0 ]
  grep -q '"size": "S"' "$TMP_ROOT/out.json"
  grep -q '"drive": "agent"' "$TMP_ROOT/out.json"
  ! grep -q '2 段設計推奨' "$TMP_ROOT/err.log"
}
