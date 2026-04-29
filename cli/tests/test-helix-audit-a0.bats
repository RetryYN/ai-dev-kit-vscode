#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/.helix" "$HOME_DIR"
  cd "$PROJECT_ROOT"
  git init >/dev/null 2>&1
  git config user.email "test@example.com"
  git config user.name "HELIX Test"
  mkdir -p src
  echo "print('hello')" >src/app.py
  git add src/app.py
  git commit -m "initial" >/dev/null 2>&1
  echo "scratch" >scratch.txt
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

@test "helix-audit a0 discover generates decisions draft" {
  scope_hash="$(printf 'a' | sha256sum | head -c 64)"
  draft="$TMP_ROOT/draft.yaml"
  summary="$TMP_ROOT/summary.log"
  raw="$HOME_DIR/.helix/quarantine/raw.log"

  run "$HELIX_ROOT/cli/helix-audit" a0 discover \
    --scope-hash "$scope_hash" \
    --output "$summary" \
    --raw "$raw" \
    --draft "$draft"

  [ "$status" -eq 0 ]
  [ -f "$draft" ]
  [ -f "$summary" ]
  [ -f "$raw" ]
  [[ "$output" == *"draft: $draft"* ]]
  grep -q "candidate_id: src/app.py" "$draft"
  grep -q "decision: keep" "$draft"
  grep -q "scope_hash: $scope_hash" "$draft"
  grep -q "tracked_count: 1" "$summary"

  run python3 - "$HELIX_ROOT/cli/lib" "$draft" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from audit_validator import validate_decisions_yaml
result = validate_decisions_yaml(sys.argv[2])
assert result.success, result.errors
PY
  [ "$status" -eq 0 ]
}
