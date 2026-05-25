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
  mkdir -p "$PROJECT_ROOT/docs/plans/L4" "$HOME_DIR"
  cat > "$PROJECT_ROOT/docs/plans/L4/L4-sample-design-plan.md" <<'EOF'
---
title: Sample Design
---

# Sample Design
EOF
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix-test-design-scaffold defaults to dry-run" {
  run "$HELIX_ROOT/cli/helix-test-design-scaffold" \
    --layer L4 \
    --paired-design docs/plans/L4/L4-sample-design-plan.md

  [ "$status" -eq 0 ]
  [[ "$output" == *"status: dry_run"* ]]
  [[ "$output" == *"output_path:"* ]]
  [ ! -d "$PROJECT_ROOT/docs/plans/L9" ]
}

@test "helix-test-design-scaffold applies scaffold with --apply" {
  run "$HELIX_ROOT/cli/helix-test-design-scaffold" \
    --layer L4 \
    --paired-design docs/plans/L4/L4-sample-design-plan.md \
    --apply

  [ "$status" -eq 0 ]
  [[ "$output" == *"status: applied"* ]]
  [[ "$output" == *"content_preview:"* ]]

  matches=("$PROJECT_ROOT"/docs/plans/L9/TEST-DESIGN-L9-auto-*.md)
  [ -f "${matches[0]}" ]
  grep -q "paired_design_doc: 'docs/plans/L4/L4-sample-design-plan.md'" "${matches[0]}"
}

@test "helix-test-design-scaffold --extract-sections includes acceptance section" {
  cat > "$PROJECT_ROOT/parent.md" <<'EOF'
---
plan_id: TEST
---

## §1 受入条件

- 受入 1
- 受入 2
EOF

  run "$HELIX_ROOT/cli/helix-test-design-scaffold" \
    --layer L4 \
    --paired-design parent.md \
    --extract-sections

  [ "$status" -eq 0 ]
  [[ "$output" == *"引用:"* ]]
}
