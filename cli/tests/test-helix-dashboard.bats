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
  cd "$PROJECT_ROOT"
  git init >/dev/null 2>&1
  git config user.email "t@t"
  git config user.name "T"
  echo "# test" > README.md
  git add . && git commit -q -m "init"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  "$HELIX_ROOT/cli/helix" init --project-name dash >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix dashboard shows project state" {
  run "$HELIX_ROOT/cli/helix" dashboard
  [ "$status" -eq 0 ]
  [[ "$output" == *"HELIX Dashboard"* ]]
  [[ "$output" == *"Project: dash"* ]]
  [[ "$output" == *"Gates:"* ]]
  [[ "$output" == *"Next:"* ]]
}

@test "helix dashboard json is parseable" {
  run "$HELIX_ROOT/cli/helix" dashboard --json
  [ "$status" -eq 0 ]
  DASHBOARD_JSON="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["DASHBOARD_JSON"])
assert payload["project"] == "dash", payload
assert "gates" in payload, payload
assert "plans" in payload, payload
assert "next_action" in payload, payload
PY
}

@test "helix dashboard reads reverse yaml gap register and run phases" {
  mkdir -p "$PROJECT_ROOT/.helix/reverse"
  cat > "$PROJECT_ROOT/.helix/reverse/R4-gap-register.yaml" <<'YAML'
gaps:
  - gap_id: GAP-001
    status: open
  - gap_id: GAP-002
    status: resolved
YAML
  python3 "$HELIX_ROOT/cli/lib/yaml_parser.py" write "$PROJECT_ROOT/.helix/phase.yaml" current_phase L10

  run "$HELIX_ROOT/cli/helix" dashboard --json
  [ "$status" -eq 0 ]
  DASHBOARD_JSON="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["DASHBOARD_JSON"])
assert payload["reverse"]["gap_register"] == ".helix/reverse/R4-gap-register.yaml", payload
assert payload["reverse"]["total"] == 2, payload
assert payload["reverse"]["counts"]["open"] == 1, payload
assert "G10" in payload["next_action"], payload
PY
}
