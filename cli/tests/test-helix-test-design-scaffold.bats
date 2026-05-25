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

@test "helix-test-design-scaffold auto-detects paired design when omitted" {
  mkdir -p "$PROJECT_ROOT/docs/plans/L9"
  cat > "$PROJECT_ROOT/docs/plans/L9/L9-auto-plan.md" <<'EOF'
---
title: Auto Pair
status: draft
---

# Auto Pair
EOF

  run "$HELIX_ROOT/cli/helix-test-design-scaffold" \
    --layer L4

  [ "$status" -eq 0 ]
  [[ "$output" == *"status: dry_run"* ]]
  [[ "$output" == *"paired_design_doc"* ]]
  [[ "$output" == *"L9-auto-plan.md"* ]]
}

@test "helix-test-design-scaffold respects --prefer-status" {
  mkdir -p "$PROJECT_ROOT/docs/plans/L9"
  cat > "$PROJECT_ROOT/docs/plans/L9/L9-a-completed-plan.md" <<'EOF'
---
title: Completed Pair
status: completed
---
EOF
  cat > "$PROJECT_ROOT/docs/plans/L9/L9-z-draft-plan.md" <<'EOF'
---
title: Draft Pair
status: draft
---
EOF

  run "$HELIX_ROOT/cli/helix-test-design-scaffold" \
    --layer L4 \
    --prefer-status draft

  [ "$status" -eq 0 ]
  [[ "$output" == *"paired_design_doc"* ]]
  [[ "$output" == *"L9-z-draft-plan.md"* ]]
}

@test "helix-test-design-scaffold respects --prefer-kind" {
  mkdir -p "$PROJECT_ROOT/docs/plans/L9"
  cat > "$PROJECT_ROOT/docs/plans/L9/L9-impl-plan.md" <<'EOF'
---
title: Impl Pair
kind: impl
status: draft
---
EOF
  cat > "$PROJECT_ROOT/docs/plans/L9/L9-design-plan.md" <<'EOF'
---
title: Design Pair
kind: design
status: draft
---
EOF

  run "$HELIX_ROOT/cli/helix-test-design-scaffold" \
    --layer L4 \
    --prefer-kind design

  [ "$status" -eq 0 ]
  [[ "$output" == *"paired_design_doc"* ]]
  [[ "$output" == *"L9-design-plan.md"* ]]
}

@test "helix-test-design-scaffold respects --status-weight + --kind-weight" {
  mkdir -p "$PROJECT_ROOT/docs/plans/L9"
  cat > "$PROJECT_ROOT/docs/plans/L9/L9-status-match-plan.md" <<'EOF'
---
title: Status Match
status: draft
kind: impl
---
EOF
  cat > "$PROJECT_ROOT/docs/plans/L9/L9-kind-match-plan.md" <<'EOF'
---
title: Kind Match
status: completed
kind: design
---
EOF

  run "$HELIX_ROOT/cli/helix-test-design-scaffold" \
    --layer L4 \
    --weighted \
    --status-weight 3 \
    --kind-weight 1

  [ "$status" -eq 0 ]
  [[ "$output" == *"paired_design_doc"* ]]
  [[ "$output" == *"L9-status-match-plan.md"* ]]
}

@test "helix-test-design-scaffold --json outputs JSON" {
  run "$HELIX_ROOT/cli/helix-test-design-scaffold" \
    --layer L4 \
    --paired-design docs/plans/L4/L4-sample-design-plan.md \
    --json

  [ "$status" -eq 0 ]
  [[ "$output" == *"{"* ]]
  [[ "$output" == *"\"metadata\""* ]]
}

@test "helix-test-design-scaffold --interactive prompts and accepts" {
  mkdir -p "$PROJECT_ROOT/docs/plans/L9"
  cat > "$PROJECT_ROOT/docs/plans/L9/L9-a-plan.md" <<'EOF'
---
title: Auto Pair
plan_id: AUTO-PAIR
status: draft
kind: impl
---
EOF

  run bash -lc "printf '\\n' | \"$HELIX_ROOT/cli/helix-test-design-scaffold\" --layer L4 --interactive"

  [ "$status" -eq 0 ]
  [[ "$output" == *"Select paired design"* ]]
  [[ "$output" == *"L9-a-plan.md"* ]]
}
