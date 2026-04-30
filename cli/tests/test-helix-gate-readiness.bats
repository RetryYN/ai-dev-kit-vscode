#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"

  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/.helix" "$HOME_DIR"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export HELIX_DISABLE_FEEDBACK=1

  cat > "$PROJECT_ROOT/.helix/phase.yaml" <<'YAML'
project: gate-readiness-test
current_phase: L2
sprint:
  drive: be
  ui: false
gates:
  G1:
    status: passed
YAML

  cat > "$PROJECT_ROOT/.helix/gate-checks.yaml" <<'YAML'
G2:
  name: "G2 readiness test"
  static:
  ai:
YAML
}

teardown() {
  rm -rf "$TMP_ROOT"
}

add_p0_finding() {
  python3 - <<'PY' "$HELIX_ROOT" "$PROJECT_ROOT"
import sys
from pathlib import Path

helix_root = Path(sys.argv[1])
project_root = Path(sys.argv[2])
sys.path.insert(0, str(helix_root / "cli" / "lib"))

import deferred_findings

deferred_findings.add_finding(
    project_root / ".helix" / "audit" / "deferred-findings.yaml",
    {
        "plan_id": "PLAN-READINESS",
        "phase": "L2",
        "severity": "critical",
        "source": ".helix/reviews/plans/PLAN-READINESS.json#/findings/0",
        "title": "Blocking readiness finding",
        "body": "body",
        "recommendation": "fix",
    },
)
PY
}

@test "helix gate G2 --readiness-mode skip does not run readiness check" {
  run "$HELIX_ROOT/cli/helix" gate G2 --static-only --readiness-mode skip
  [ "$status" -eq 0 ]
  [[ "$output" == *"=== G2 PASS ==="* ]]
  [[ "$output" != *"readiness exit not satisfied"* ]]
}

@test "helix gate G2 default warning runs readiness check without changing gate result" {
  run "$HELIX_ROOT/cli/helix" gate G2 --static-only
  [ "$status" -eq 0 ]
  [[ "$output" == *"readiness exit not satisfied for L2 (warning mode)"* ]]
  [[ "$output" == *"=== G2 PASS ==="* ]]
}

@test "helix gate G2 --readiness-mode enforce fails when P0 finding is open" {
  mkdir -p docs/adr
  echo "# ADR" > docs/adr/base.md
  add_p0_finding

  run "$HELIX_ROOT/cli/helix" gate G2 --static-only --readiness-mode enforce
  [ "$status" -eq 1 ]
  [[ "$output" == *"readiness exit not satisfied for L2 (enforce mode)"* ]]
  [[ "$output" == *"=== G2 FAIL"* ]]
  [[ "$output" == *"readiness: 1 fail"* ]]

  run python3 "$HELIX_ROOT/cli/lib/yaml_parser.py" read "$PROJECT_ROOT/.helix/phase.yaml" "gates.G2.status"
  [ "$status" -eq 0 ]
  [[ "$output" == "failed" ]]
}
