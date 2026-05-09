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
  "$HELIX_ROOT/cli/helix" init --project-name meta >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix meta-phase check validates pattern contract" {
  run "$HELIX_ROOT/cli/helix" meta-phase check
  [ "$status" -eq 0 ]
  [[ "$output" == *"HELIX Meta Phase"* ]]
  [[ "$output" == *"status: PASS"* ]]
}

@test "helix meta-phase status --json is parseable" {
  run "$HELIX_ROOT/cli/helix" meta-phase status --json
  [ "$status" -eq 0 ]
  META_JSON="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["META_JSON"])
assert payload["ok"] is True, payload
assert payload["pattern_count"] >= 3, payload
PY
}

@test "helix meta-phase validates project-local pattern file" {
  cat > "$PROJECT_ROOT/.helix/patterns/pattern.yaml" <<'YAML'
version: 1
patterns:
  - id: bad
    scope:
      layer: [Plan]
      phase: [G1]
      gate: [G1]
      subphase: [L-1]
    priority: 1
    applies_when:
      all:
        - drive: [be]
    outputs:
      - path: docs/adr/{id}.md
        type: ADR
    conflicts_with: []
    exception_policy:
      requires_approval: PM
      audit_log: true
    audit_log:
      enabled: true
      path: .helix/audit/pattern-applications.yaml
YAML

  run "$HELIX_ROOT/cli/helix" meta-phase check
  [ "$status" -ne 0 ]
  [[ "$output" == *"invalid scope.phase G1"* ]]
}

@test "helix meta-phase honors explicit HELIX_PROJECT_ROOT outside cwd" {
  cd "$TMP_ROOT"

  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" "$HELIX_ROOT/cli/helix" meta-phase check --json

  [ "$status" -eq 0 ]
  [[ "$output" == *"\"ok\": true"* ]]
  [[ "$output" == *"$PROJECT_ROOT/.helix/patterns/pattern.yaml"* ]]
}
