#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR"
  cd "$PROJECT_ROOT"

  git init -q
  git config user.email "add-feature@example.com"
  git config user.name "Add Feature Test"
  echo "# add-feature" > README.md
  git add README.md
  git commit -q -m "init"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  "$HELIX_ROOT/cli/helix" init --project-name add-feature >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix add-feature help and top-level help include add-feature" {
  run "$HELIX_ROOT/cli/helix-add-feature" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"usage: helix add-feature"* ]]
  [[ "$output" == *"add-design"* ]]

  run "$HELIX_ROOT/cli/helix" help
  [ "$status" -eq 0 ]
  [[ "$output" == *"add-feature"* ]]
}

@test "helix add-feature add-design creates session" {
  run "$HELIX_ROOT/cli/helix" add-feature add-design \
    --feature user-auth \
    --summary "認証 feature の設計追補" \
    --requires-plan PLAN-BASE-DESIGN \
    --design-doc docs/design/user-auth.md \
    --requirements-layer L1
  [ "$status" -eq 0 ]
  [[ "$output" == *"[HELIX Add-feature] user-auth (design_supplemented)"* ]]
  [ -f "$PROJECT_ROOT/.helix/add-feature/CURRENT.json" ]
}

@test "helix add-feature add-impl and route expose forward integration targets" {
  "$HELIX_ROOT/cli/helix" add-feature add-design \
    --feature user-auth \
    --summary "認証 feature の設計追補" \
    --requires-plan PLAN-BASE-DESIGN >/dev/null

  run "$HELIX_ROOT/cli/helix" add-feature add-impl \
    --feature user-auth \
    --summary "認証 feature の実装追補" \
    --requires-plan PLAN-BASE-IMPL \
    --module cli/lib/auth.py \
    --test-path cli/lib/tests/test_auth.py
  [ "$status" -eq 0 ]
  [[ "$output" == *"(implementation_supplemented)"* ]]

  run "$HELIX_ROOT/cli/helix" add-feature route
  [ "$status" -eq 0 ]
  [[ "$output" == *"L4:"* ]]
  [[ "$output" == *"L9:"* ]]
}

@test "helix commands check passes after add-feature registration" {
  run "$HELIX_ROOT/cli/helix" commands check
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: command catalog is consistent"* ]]
}
