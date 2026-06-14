#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR" "$PROJECT_ROOT/cli/config" "$PROJECT_ROOT/cli/lib" "$PROJECT_ROOT/docs/plans/L7"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  cd "$PROJECT_ROOT"
  git init >/dev/null 2>&1
  git config user.email "t@t"
  git config user.name "T"
  git checkout -b main >/dev/null 2>&1
  cat > "$PROJECT_ROOT/cli/config/import-cycle-baseline.json" <<'EOF'
{
  "intentional_baseline": true,
  "owner": "codex",
  "created": "2026-06-14",
  "expiry": "2026-09-12",
  "generated_by": "bats",
  "reports": [
    {
      "check_name": "check_import_cycle",
      "mode": "advisory",
      "findings": [],
      "metrics": {
        "cycle_count": 0
      }
    }
  ]
}
EOF
  cat > "$PROJECT_ROOT/cli/config/plan-dependency-baseline.json" <<'EOF'
{
  "intentional_baseline": true,
  "owner": "codex",
  "created": "2026-06-14",
  "expiry": "2026-09-12",
  "generated_by": "bats",
  "accepted_dependency_warning": []
}
EOF
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix doctor check_import_cycle stays advisory by default" {
  cat > "$PROJECT_ROOT/cli/lib/alpha.py" <<'EOF'
import beta
EOF
  cat > "$PROJECT_ROOT/cli/lib/beta.py" <<'EOF'
import alpha
EOF

  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" "$HELIX_ROOT/cli/helix-doctor" check_import_cycle
  [ "$status" -eq 0 ]
  [[ "$output" == *"import_cycle"* ]]
}

@test "helix doctor check_import_cycle --gate fails on new changed-file cycle" {
  cat > "$PROJECT_ROOT/cli/lib/alpha.py" <<'EOF'
import beta
EOF
  cat > "$PROJECT_ROOT/cli/lib/beta.py" <<'EOF'
import alpha
EOF

  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" HELIX_CHANGED_FILES="cli/lib/alpha.py" "$HELIX_ROOT/cli/helix-doctor" check_import_cycle --gate
  [ "$status" -eq 1 ]
  [[ "$output" == *"import_cycle"* ]]
  [[ "$output" == *"new_findings=1"* ]]
}

@test "helix doctor check_plan_dependency_gate stays advisory by default" {
  cat > "$PROJECT_ROOT/docs/plans/L7/L7-701-alpha-plan.md" <<'EOF'
---
plan_id: L7-701-alpha-plan
title: Alpha
plan_scope: action
kind: impl
layer: L7
drive: be
status: draft
dependencies:
  parent: null
  requires:
    - L7-702-beta-plan
  blocks: []
---
EOF
  cat > "$PROJECT_ROOT/docs/plans/L7/L7-702-beta-plan.md" <<'EOF'
---
plan_id: L7-702-beta-plan
title: Beta
plan_scope: action
kind: impl
layer: L7
drive: be
status: draft
dependencies:
  parent: null
  requires:
    - L7-701-alpha-plan
  blocks: []
---
EOF

  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" "$HELIX_ROOT/cli/helix-doctor" check_plan_dependency_gate
  [ "$status" -eq 0 ]
  [[ "$output" == *"plan_dependency_gate"* ]]
}

@test "helix doctor check_plan_dependency_gate --gate fails on new changed-plan cycle" {
  cat > "$PROJECT_ROOT/docs/plans/L7/L7-701-alpha-plan.md" <<'EOF'
---
plan_id: L7-701-alpha-plan
title: Alpha
plan_scope: action
kind: impl
layer: L7
drive: be
status: draft
dependencies:
  parent: null
  requires:
    - L7-702-beta-plan
  blocks: []
---
EOF
  cat > "$PROJECT_ROOT/docs/plans/L7/L7-702-beta-plan.md" <<'EOF'
---
plan_id: L7-702-beta-plan
title: Beta
plan_scope: action
kind: impl
layer: L7
drive: be
status: draft
dependencies:
  parent: null
  requires:
    - L7-701-alpha-plan
  blocks: []
---
EOF

  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" HELIX_CHANGED_FILES="docs/plans/L7/L7-701-alpha-plan.md" "$HELIX_ROOT/cli/helix-doctor" check_plan_dependency_gate --gate
  [ "$status" -eq 1 ]
  [[ "$output" == *"plan_dependency_gate"* ]]
  [[ "$output" == *"blocking_findings=1"* ]]
}

@test "helix doctor check_fr_uses stays advisory by default" {
  cat > "$PROJECT_ROOT/cli/config/functional-registry.yaml" <<'EOF'
entries:
  - id: FR-A
    name: alpha
    domain: cli
    status: active
    uses: [FR-MISSING]
EOF

  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" "$HELIX_ROOT/cli/helix-doctor" check_fr_uses
  [ "$status" -eq 0 ]
  [[ "$output" == *"fr_uses"* ]]
}

@test "helix doctor check_fr_uses --gate fails on new missing uses target" {
  cat > "$PROJECT_ROOT/cli/config/functional-registry.yaml" <<'EOF'
entries:
  - id: FR-A
    name: alpha
    domain: cli
    status: active
    uses: [FR-MISSING]
EOF

  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" HELIX_CHANGED_FILES="cli/config/functional-registry.yaml" "$HELIX_ROOT/cli/helix-doctor" check_fr_uses --gate
  [ "$status" -eq 1 ]
  [[ "$output" == *"fr_uses"* ]]
  [[ "$output" == *"blocking_findings=1"* ]]
}
