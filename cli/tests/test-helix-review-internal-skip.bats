#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  while IFS='=' read -r name _; do
    [[ "$name" == HELIX_TEST_* ]] && unset "$name"
  done < <(env)
  unset CODEX_BIN HELIX_CODEX_BIN HELIX_CODEX_AUTO_FALLBACK HELIX_CODEX_NO_FOOTER
  unset HELIX_CODEX_INTERNAL HELIX_DISABLE_SPARK HELIX_MODEL_OVERRIDE

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  mkdir -p "$PROJECT_ROOT"
  cd "$PROJECT_ROOT"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "HELIX_CODEX_INTERNAL=1 causes review to be skipped before CODEX_BIN check" {
  HELIX_CODEX_INTERNAL=1 run "$HELIX_ROOT/cli/helix-review"

  [ "$status" -eq 0 ]
  [[ "$output" == "[helix-review] skipped: nested review unsupported in read-only sandbox" ]]
}

@test "Without HELIX_CODEX_INTERNAL and no codex, it fails with codex missing error" {
  HELIX_CODEX_INTERNAL="" PATH="/usr/bin:/bin" run "$HELIX_ROOT/cli/helix-review"

  [ "$status" -eq 1 ]
  [[ "$output" == *"エラー: codex が見つかりません" ]]
  [[ "$output" != *"skipped: nested review unsupported in read-only sandbox" ]]
}
