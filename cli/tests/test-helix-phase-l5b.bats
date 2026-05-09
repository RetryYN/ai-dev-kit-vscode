#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"
  export HELIX_DISABLE_FEEDBACK=1

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  mkdir -p "$PROJECT_ROOT/.helix"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"

  cp "$HELIX_ROOT/cli/templates/phase.yaml" "$PROJECT_ROOT/.helix/phase.yaml"
  cat > "$PROJECT_ROOT/.helix/gate-checks.yaml" <<'YAML'
G5:
  name: "G5 phase split smoke"
  static:
  ai:
YAML

  python3 "$HELIX_ROOT/cli/lib/yaml_parser.py" write "$PROJECT_ROOT/.helix/phase.yaml" "sprint.drive" "be" >/dev/null
  python3 "$HELIX_ROOT/cli/lib/yaml_parser.py" write "$PROJECT_ROOT/.helix/phase.yaml" "sprint.ui" "false" >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix gate G5 accepts L5a and L5b phase override in dry-run smoke" {
  run "$HELIX_ROOT/cli/helix" gate G5 --phase L5a --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"phase=L5a"* ]]
  [[ "$output" == *"auto-skipped"* ]]

  run "$HELIX_ROOT/cli/helix" gate G5 --phase L5b --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"phase=L5b"* ]]
  [[ "$output" == *"auto-skipped"* ]]
}
