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

@test "--ui のみ -> fe" {
  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' --files 5 --lines 100 --ui --json >'$TMP_ROOT/out.json' 2>'$TMP_ROOT/err.log'"
  [ "$status" -eq 0 ]
  grep -q '"drive": "fe"' "$TMP_ROOT/out.json"
  grep -q '\[drive-auto\] 判定: fe' "$TMP_ROOT/err.log"
}

@test "--ui --api -> fullstack" {
  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' --files 5 --lines 100 --ui --api --json >'$TMP_ROOT/out.json' 2>'$TMP_ROOT/err.log'"
  [ "$status" -eq 0 ]
  grep -q '"drive": "fullstack"' "$TMP_ROOT/out.json"
  grep -q '\[drive-auto\] 判定: fullstack' "$TMP_ROOT/err.log"
}

@test "--api --db -> be" {
  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' --files 5 --lines 100 --api --db --json >'$TMP_ROOT/out.json' 2>'$TMP_ROOT/err.log'"
  [ "$status" -eq 0 ]
  grep -q '"drive": "be"' "$TMP_ROOT/out.json"
  grep -q '\[drive-auto\] 判定: be' "$TMP_ROOT/err.log"
}

@test "フラグなし -> be" {
  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' --files 5 --lines 100 --json >'$TMP_ROOT/out.json' 2>'$TMP_ROOT/err.log'"
  [ "$status" -eq 0 ]
  grep -q '"drive": "be"' "$TMP_ROOT/out.json"
  grep -q '\[drive-auto\] 判定: be' "$TMP_ROOT/err.log"
}

@test "--drive fe 明示 -> fe (自動判定しない)" {
  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' --files 5 --lines 100 --drive fe --json >'$TMP_ROOT/out.json' 2>'$TMP_ROOT/err.log'"
  [ "$status" -eq 0 ]
  grep -q '"drive": "fe"' "$TMP_ROOT/out.json"
  ! grep -q '\[drive-auto\]' "$TMP_ROOT/err.log"
}

@test "--drive be + --ui -> be (明示優先)" {
  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' --files 5 --lines 100 --ui --drive be --json >'$TMP_ROOT/out.json' 2>'$TMP_ROOT/err.log'"
  [ "$status" -eq 0 ]
  grep -q '"drive": "be"' "$TMP_ROOT/out.json"
  ! grep -q '\[drive-auto\]' "$TMP_ROOT/err.log"
}

@test "--uncertain -> scrum (検証駆動 案内)" {
  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' --files 5 --lines 100 --uncertain --json >'$TMP_ROOT/out.json' 2>'$TMP_ROOT/err.log'"
  [ "$status" -eq 0 ]
  grep -q '"drive": "scrum"' "$TMP_ROOT/out.json"
  grep -q '"mode": "scrum"' "$TMP_ROOT/out.json"
  grep -q '\[drive-auto\] 判定: scrum' "$TMP_ROOT/err.log"
}

@test "--uncertain --ui -> scrum (uncertain が最優先)" {
  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' --files 5 --lines 100 --uncertain --ui --json >'$TMP_ROOT/out.json' 2>'$TMP_ROOT/err.log'"
  [ "$status" -eq 0 ]
  grep -q '"drive": "scrum"' "$TMP_ROOT/out.json"
}

@test "--drive scrum 明示 -> scrum" {
  run bash -lc "HELIX_HOME='$REPO_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' --files 5 --lines 100 --drive scrum --json >'$TMP_ROOT/out.json' 2>'$TMP_ROOT/err.log'"
  [ "$status" -eq 0 ]
  grep -q '"drive": "scrum"' "$TMP_ROOT/out.json"
  ! grep -q '\[drive-auto\]' "$TMP_ROOT/err.log"
}
