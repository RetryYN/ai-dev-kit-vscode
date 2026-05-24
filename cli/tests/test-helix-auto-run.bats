#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"

  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  BIN_DIR="$TMP_ROOT/bin"

  mkdir -p "$PROJECT_ROOT" "$HOME_DIR" "$BIN_DIR"
  export HELIX_HOME="$HELIX_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PATH="$BIN_DIR:$HELIX_ROOT/cli:/usr/bin:/bin"

  cat > "$BIN_DIR/helix" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "handover" && "${2:-}" == "status" && "${3:-}" == "--json" ]]; then
  cat <<'JSON'
{"files":{"pending_count":2}}
JSON
  exit 0
fi
if [[ "${1:-}" == "budget" && "${2:-}" == "status" && "${3:-}" == "--json" ]]; then
  cat <<'JSON'
{"claude":{"weekly_remaining_pct":80},"codex":{"weekly_used_pct":10},"recommendations":[]}
JSON
  exit 0
fi
echo "unexpected args: $*" >&2
exit 2
EOF
  chmod +x "$BIN_DIR/helix"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix-auto-run start and status --json work" {
  run "$HELIX_ROOT/cli/helix-auto-run" start --plan-id L7-auto-run-loop-frameworkplan --duration-minutes 25 --json
  [ "$status" -eq 0 ]
  [[ "$output" == *"L7-auto-run-loop-frameworkplan"* ]]

  run bash -c "$HELIX_ROOT/cli/helix-auto-run status --json | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d[\"status\"] == \"running\"; assert d[\"budget\"][\"duration_minutes\"] == 25'"
  [ "$status" -eq 0 ]
}

@test "helix auto-run heartbeat and resume work through router" {
  "$HELIX_ROOT/cli/helix-auto-run" start --plan-id L7-auto-run-loop-frameworkplan --duration-minutes 25 >/dev/null

  run bash -c "$HELIX_ROOT/cli/helix auto-run heartbeat --json | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d[\"heartbeat\"][\"should_schedule\"] is True; assert d[\"resume\"][\"resume_ready\"] is True'"
  [ "$status" -eq 0 ]

  run bash -c "$HELIX_ROOT/cli/helix auto-run resume --json | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d[\"resume\"][\"action\"] == \"resume_plan\"; assert d[\"resume\"][\"plan_id\"] == \"L7-auto-run-loop-frameworkplan\"'"
  [ "$status" -eq 0 ]
}

@test "helix-auto-run budget updates window" {
  "$HELIX_ROOT/cli/helix-auto-run" start --plan-id L7-auto-run-loop-frameworkplan >/dev/null

  run bash -c "$HELIX_ROOT/cli/helix-auto-run budget --set-minutes 5 --json | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d[\"budget\"][\"duration_minutes\"] == 5'"
  [ "$status" -eq 0 ]
}

@test "helix-auto-run stop marks stopped state" {
  "$HELIX_ROOT/cli/helix-auto-run" start --plan-id L7-auto-run-loop-frameworkplan >/dev/null

  run bash -c "$HELIX_ROOT/cli/helix-auto-run stop --json | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d[\"status\"] == \"stopped\"; assert d[\"resume\"][\"resume_ready\"] is False'"
  [ "$status" -eq 0 ]
}
