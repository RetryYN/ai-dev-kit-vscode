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

  cat > "$PROJECT_ROOT/.helix/phase.yaml" <<'YAML'
project: readiness-test
current_phase: L0
sprint:
  drive: be
  ui: false
YAML
}

teardown() {
  rm -rf "$TMP_ROOT"
}

add_finding() {
  local severity="$1"
  local phase="${2:-L2}"
  python3 - <<'PY' "$HELIX_ROOT" "$PROJECT_ROOT" "$severity" "$phase"
import sys
from pathlib import Path

helix_root = Path(sys.argv[1])
project_root = Path(sys.argv[2])
severity = sys.argv[3]
phase = sys.argv[4]
sys.path.insert(0, str(helix_root / "cli" / "lib"))

import deferred_findings

finding_id = deferred_findings.add_finding(
    project_root / ".helix" / "audit" / "deferred-findings.yaml",
    {
        "plan_id": "PLAN-007",
        "phase": phase,
        "severity": severity,
        "source": ".helix/reviews/plans/PLAN-007.json#/findings/0",
        "title": "Readiness test finding",
        "body": "body",
        "recommendation": "fix",
    },
)
print(finding_id)
PY
}

@test "helix readiness check --phase L0 exits 0 when phase.yaml has project" {
  run "$HELIX_ROOT/cli/helix" readiness check --phase L0
  [ "$status" -eq 0 ]
  [[ "$output" == *"ready: L0"* ]]
}

@test "helix readiness list prints no findings when empty" {
  run "$HELIX_ROOT/cli/helix" readiness list
  [ "$status" -eq 0 ]
  [[ "$output" == *"no findings"* ]]
}

@test "helix readiness defer records carry chain in yaml" {
  finding_id="$(add_finding medium L2)"

  run "$HELIX_ROOT/cli/helix" readiness defer --finding "$finding_id" --to PLAN-009:L9 --approved-by PM
  [ "$status" -eq 0 ]
  [[ "$output" == *"deferred: $finding_id -> PLAN-009:L9"* ]]

  run python3 - <<'PY' "$HELIX_ROOT" "$PROJECT_ROOT" "$finding_id"
import sys
from pathlib import Path

helix_root = Path(sys.argv[1])
project_root = Path(sys.argv[2])
finding_id = sys.argv[3]
sys.path.insert(0, str(helix_root / "cli" / "lib"))

import deferred_findings

payload = deferred_findings.load_findings(project_root / ".helix" / "audit" / "deferred-findings.yaml")
finding = next(item for item in payload["findings"] if item["id"] == finding_id)
assert finding["status"] == "carried", finding
assert finding["target"] == {"plan_id": "PLAN-009", "phase": "L9"}, finding
assert finding["carry_chain"][-1]["to"] == "PLAN-009:L9", finding
PY
  [ "$status" -eq 0 ]
}

@test "helix readiness accept --status resolved transitions status" {
  finding_id="$(add_finding medium L2)"
  mkdir -p docs/evidence
  echo "resolved" > docs/evidence/readiness.md

  run "$HELIX_ROOT/cli/helix" readiness accept --finding "$finding_id" --status resolved --evidence docs/evidence/readiness.md
  [ "$status" -eq 0 ]
  [[ "$output" == *"accepted: $finding_id status=resolved evidence=docs/evidence/readiness.md"* ]]

  run python3 - <<'PY' "$HELIX_ROOT" "$PROJECT_ROOT" "$finding_id"
import sys
from pathlib import Path

helix_root = Path(sys.argv[1])
project_root = Path(sys.argv[2])
finding_id = sys.argv[3]
sys.path.insert(0, str(helix_root / "cli" / "lib"))

import deferred_findings

finding = next(
    item
    for item in deferred_findings.load_findings(project_root / ".helix" / "audit" / "deferred-findings.yaml")["findings"]
    if item["id"] == finding_id
)
assert finding["status"] == "resolved", finding
assert finding["resolved_at"].endswith("Z"), finding
assert finding["evidence"]["path"] == "docs/evidence/readiness.md", finding
PY
  [ "$status" -eq 0 ]
}

@test "helix readiness check exits 2 when P0 open finding exists" {
  add_finding critical L0 >/dev/null

  run "$HELIX_ROOT/cli/helix" readiness check --phase L0
  [ "$status" -eq 2 ]
  [[ "$output" == *"blocking finding: DF-PLAN-007-L0-001 P0 open Readiness test finding"* ]]
}
