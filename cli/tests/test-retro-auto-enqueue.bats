#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  CLI="$HELIX_ROOT/cli/helix-retro"
  TMP_ROOT="$(mktemp -d)"
  PROJ="$TMP_ROOT/proj"

  mkdir -p "$PROJ/.helix/retros"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

@test "未記入 retro は debt 登録される" {
  cat > "$PROJ/.helix/retros/sprint-1.md" <<'EOF'
# sprint-1
- 
EOF

  run bash -lc "HELIX_HOME='$HELIX_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' auto-enqueue"
  [ "$status" -eq 0 ]

  [ -f "$PROJ/.helix/debt-register.yaml" ]
  grep -q 'id: RETRO-UNDOC-sprint-1' "$PROJ/.helix/debt-register.yaml"
  grep -q 'title: "ミニレトロ未記入: sprint-1 (1件)"' "$PROJ/.helix/debt-register.yaml"
}

@test "記入済み retro はスキップされる" {
  cat > "$PROJ/.helix/retros/sprint-2.md" <<'EOF'
# sprint-2
- done
EOF

  run bash -lc "HELIX_HOME='$HELIX_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' auto-enqueue"
  [ "$status" -eq 0 ]
  [[ "$output" =~ "記入済み: sprint-2" ]]
  [ ! -f "$PROJ/.helix/debt-register.yaml" ]
}

@test "--dry-run は debt-register を変更しない" {
  cat > "$PROJ/.helix/retros/sprint-3.md" <<'EOF'
# sprint-3
- 
EOF

  run bash -lc "HELIX_HOME='$HELIX_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' auto-enqueue --dry-run"
  [ "$status" -eq 0 ]
  [[ "$output" =~ "\\[dry-run\\] enqueue: id=RETRO-UNDOC-sprint-3" ]]
  [ ! -f "$PROJ/.helix/debt-register.yaml" ]
}

@test "既存 ID は再登録されない" {
  cat > "$PROJ/.helix/retros/sprint-4.md" <<'EOF'
# sprint-4
- 
EOF
  mkdir -p "$PROJ/.helix"
  cat > "$PROJ/.helix/debt-register.yaml" <<'EOF'
items:
  - id: RETRO-UNDOC-sprint-4
    title: "already exists"
    priority: medium
    category: "retro-undocumented"
    impact: medium
    effort: "S"
    owner: "PM"
    target_sprint: "next"
    source: "manual"
    status: open
    created_at: "2026-01-01T00:00:00"
    resolved_at: ""
EOF

  run bash -lc "HELIX_HOME='$HELIX_ROOT' HELIX_PROJECT_ROOT='$PROJ' '$CLI' auto-enqueue"
  [ "$status" -eq 0 ]
  [[ "$output" =~ "warn: 既存IDのためスキップ: RETRO-UNDOC-sprint-4" ]]
  run bash -lc "grep -c 'RETRO-UNDOC-sprint-4' '$PROJ/.helix/debt-register.yaml'"
  [ "$status" -eq 0 ]
  [ "$output" -eq 1 ]
}
