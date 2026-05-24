#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  cd "$PROJECT_ROOT"
  git init >/dev/null 2>&1
  git config user.email "t@t"
  git config user.name "T"
  printf "# doctor test\n" > README.md
  git add README.md
  git commit -q -m "init"
  "$HELIX_ROOT/cli/helix" init --project-name doctor-json >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix doctor --json emits valid JSON" {
  run bash -lc "\"$HELIX_ROOT/cli/helix\" doctor --json | python3 -c 'import json,sys; d=json.load(sys.stdin); assert \"pass\" in d and \"warn\" in d and isinstance(d[\"advisories\"], list)'"
  [ "$status" -eq 0 ]
}

@test "helix doctor without --json keeps text output" {
  run "$HELIX_ROOT/cli/helix" doctor
  [ "$status" -eq 0 ]
  [[ "$output" == *"=== HELIX Doctor ==="* ]]
  [[ "$output" == *"結果:"* ]]
  [[ "$output" != \{* ]]
}

@test "helix doctor --json accepts --max-age-days in any order" {
  run bash -lc "\"$HELIX_ROOT/cli/helix\" doctor --json --max-age-days 7 | python3 -c 'import json,sys; json.load(sys.stdin)'"
  [ "$status" -eq 0 ]

  run bash -lc "\"$HELIX_ROOT/cli/helix\" doctor --max-age-days 7 --json | python3 -c 'import json,sys; json.load(sys.stdin)'"
  [ "$status" -eq 0 ]
}

@test "helix doctor --json keeps stdout free of text pollution" {
  run "$HELIX_ROOT/cli/helix" doctor --json
  [ "$status" -eq 0 ]
  [[ "$output" == \{* ]]
  [[ "$output" != *"HELIX Doctor"* ]]
  [[ "$output" != *"[必須依存]"* ]]
  [[ "$output" != *"結果:"* ]]
}

@test "helix recover check shows C2 CLEAR when doctor json is clean" {
  STUB_HOME="$TMP_ROOT/stub-home"
  mkdir -p "$STUB_HOME/cli"
  cat > "$STUB_HOME/cli/helix-doctor" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' '{"timestamp":"2026-05-24T00:00:00+09:00","pass":1,"fail":0,"warn":0,"advisories":[],"summary":"1 pass, 0 fail, 0 warn"}'
EOF
  cat > "$STUB_HOME/cli/helix-budget" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' '{"claude":{"weekly_used_pct":0},"codex":{"weekly_used_pct":0}}'
EOF
  chmod +x "$STUB_HOME/cli/helix-doctor" "$STUB_HOME/cli/helix-budget"
  printf '%s\n' 'current_phase: L1' > "$PROJECT_ROOT/.helix/phase.yaml"

  run env HELIX_HOME="$STUB_HOME" HELIX_PROJECT_ROOT="$PROJECT_ROOT" PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$HELIX_ROOT/cli/helix-recover" check
  [ "$status" -eq 0 ]
  [[ "$output" == *"C2 工程逸脱: CLEAR"* ]]
}
