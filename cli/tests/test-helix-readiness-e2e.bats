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
project: readiness-e2e-test
current_phase: L0
sprint:
  drive: be
  ui: false
YAML
}

teardown() {
  rm -rf "$TMP_ROOT"
}

write_gate_fixture() {
  cat > "$PROJECT_ROOT/.helix/phase.yaml" <<'YAML'
project: readiness-e2e-test
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
  name: "G2 readiness E2E"
  static:
  ai:
YAML
}

add_finding() {
  local plan_id="$1"
  local phase="$2"
  local severity="$3"
  local title="$4"
  python3 - <<'PY' "$HELIX_ROOT" "$PROJECT_ROOT" "$plan_id" "$phase" "$severity" "$title"
import sys
from pathlib import Path

helix_root = Path(sys.argv[1])
project_root = Path(sys.argv[2])
plan_id = sys.argv[3]
phase = sys.argv[4]
severity = sys.argv[5]
title = sys.argv[6]
sys.path.insert(0, str(helix_root / "cli" / "lib"))

import deferred_findings

finding_id = deferred_findings.add_finding(
    project_root / ".helix" / "audit" / "deferred-findings.yaml",
    {
        "plan_id": plan_id,
        "phase": phase,
        "severity": severity,
        "source": f".helix/reviews/plans/{plan_id}.json#/findings/0",
        "title": title,
        "body": "E2E body",
        "recommendation": "Fix in E2E",
    },
)
print(finding_id)
PY
}

@test "import check defer accept syncs deferred finding and effective score" {
  mkdir -p "$PROJECT_ROOT/.helix/reviews/plans" "$PROJECT_ROOT/docs/evidence"
  cat > "$PROJECT_ROOT/.helix/reviews/plans/PLAN-TEST.json" <<'JSON'
{
  "verdict": "needs-attention",
  "summary": "E2E review fixture",
  "overall_scores": [
    {"dimension": "density", "level": 3, "comment": "fixture"},
    {"dimension": "depth", "level": 3, "comment": "fixture"},
    {"dimension": "breadth", "level": 3, "comment": "fixture"},
    {"dimension": "accuracy", "level": 3, "comment": "fixture"},
    {"dimension": "maintainability", "level": 3, "comment": "fixture"}
  ],
  "findings": [
    {
      "severity": "high",
      "title": "Imported readiness E2E finding",
      "body": "Imported body",
      "file": "docs/plans/PLAN-TEST.md",
      "line_start": 1,
      "line_end": 1,
      "confidence": 0.9,
      "recommendation": "Defer then resolve",
      "helix_phase": "XX",
      "dimension_scores": [
        {"dimension": "accuracy", "level": 2, "comment": "fixture"}
      ]
    }
  ],
  "next_steps": ["resolve fixture finding"]
}
JSON

  run python3 "$HELIX_ROOT/cli/scripts/import-review-findings.py" \
    --reviews-dir "$PROJECT_ROOT/.helix/reviews/plans" \
    --output "$PROJECT_ROOT/.helix/audit/deferred-findings.yaml"
  [ "$status" -eq 0 ]
  [[ "$output" == *"imported: 1"* ]]
  [[ "$output" == *"P1=1"* ]]

  run "$HELIX_ROOT/cli/helix" readiness check --phase L0
  [ "$status" -eq 0 ]
  [[ "$output" == *"ready: L0"* ]]

  run "$HELIX_ROOT/cli/helix" readiness list --level P1
  [ "$status" -eq 0 ]
  [[ "$output" == *"DF-PLAN-TEST-XX-001"*"P1"*"Imported readiness E2E finding"* ]]

  run "$HELIX_ROOT/cli/helix" readiness defer --finding DF-PLAN-TEST-XX-001 --to PLAN-TEST:G3 --approved-by PM
  [ "$status" -eq 0 ]
  [[ "$output" == *"deferred: DF-PLAN-TEST-XX-001 -> PLAN-TEST:G3"* ]]

  run python3 - <<'PY' "$HELIX_ROOT" "$PROJECT_ROOT"
import sys
from pathlib import Path

helix_root = Path(sys.argv[1])
project_root = Path(sys.argv[2])
sys.path.insert(0, str(helix_root / "cli" / "lib"))

import deferred_findings

finding = deferred_findings.load_findings(project_root / ".helix" / "audit" / "deferred-findings.yaml")["findings"][0]
assert finding["carry_chain"][0]["to"] == "PLAN-TEST:G3", finding
assert finding["target"] == {"plan_id": "PLAN-TEST", "phase": "G3"}, finding
PY
  [ "$status" -eq 0 ]

  echo "resolved" > "$PROJECT_ROOT/docs/evidence/test.md"
  run "$HELIX_ROOT/cli/helix" readiness accept --finding DF-PLAN-TEST-XX-001 --status resolved --evidence docs/evidence/test.md
  [ "$status" -eq 0 ]
  [[ "$output" == *"accepted: DF-PLAN-TEST-XX-001 status=resolved evidence=docs/evidence/test.md"* ]]

  run python3 - <<'PY' "$HELIX_ROOT" "$PROJECT_ROOT"
import sqlite3
import sys
from pathlib import Path

helix_root = Path(sys.argv[1])
project_root = Path(sys.argv[2])
sys.path.insert(0, str(helix_root / "cli" / "lib"))

import deferred_findings
import helix_db

yaml_path = project_root / ".helix" / "audit" / "deferred-findings.yaml"
db_path = project_root / ".helix" / "helix.db"
finding = deferred_findings.load_findings(yaml_path)["findings"][0]
assert finding["status"] == "resolved", finding
assert finding["evidence"]["path"] == "docs/evidence/test.md", finding

conn = sqlite3.connect(db_path)
row = conn.execute("SELECT status FROM deferred_findings WHERE id = ?", ("DF-PLAN-TEST-XX-001",)).fetchone()
conn.close()
assert row == ("resolved",), row

helix_db.record_accuracy_score(str(db_path), "PLAN-TEST", "G3", "accuracy", 4)
deferred_findings.adjust_score(db_path, "DF-PLAN-TEST-XX-001", "G3", "accuracy")

conn = sqlite3.connect(db_path)
row = conn.execute(
    "SELECT raw_score, effective_score FROM accuracy_score_effective "
    "WHERE plan_id = ? AND gate = ? AND dimension = ?",
    ("PLAN-TEST", "G3", "accuracy"),
).fetchone()
conn.close()
assert row is not None, row
raw_score, effective_score = row
assert effective_score < raw_score, row
PY
  [ "$status" -eq 0 ]
}

@test "gate enforce mode fails on open P0 readiness finding" {
  write_gate_fixture
  mkdir -p "$PROJECT_ROOT/docs/adr"
  echo "# ADR" > "$PROJECT_ROOT/docs/adr/base.md"
  add_finding "PLAN-GATE" "L2" "critical" "P0 gate blocker" >/dev/null

  run "$HELIX_ROOT/cli/helix" gate G2 --static-only --readiness-mode warning
  [ "$status" -eq 0 ]
  [[ "$output" == *"readiness exit not satisfied for L2 (warning mode)"* ]]
  [[ "$output" == *"=== G2 PASS ==="* ]]

  run "$HELIX_ROOT/cli/helix" gate G2 --static-only --readiness-mode enforce
  [ "$status" -eq 1 ]
  [[ "$output" == *"readiness exit not satisfied for L2 (enforce mode)"* ]]
  [[ "$output" == *"=== G2 FAIL"* ]]

  run python3 "$HELIX_ROOT/cli/lib/yaml_parser.py" read "$PROJECT_ROOT/.helix/phase.yaml" "gates.G2.status"
  [ "$status" -eq 0 ]
  [[ "$output" == "failed" ]]
}

@test "plan reset records revision history and event roundtrip" {
  mkdir -p "$PROJECT_ROOT/.helix/plans" "$PROJECT_ROOT/.helix/reviews/plans"
  cat > "$PROJECT_ROOT/.helix/plans/PLAN-200.yaml" <<'YAML'
id: PLAN-200
title: E2E Reset Plan
status: draft
created_at: "2026-05-01T00:00:00Z"
source_file: null
finalized_at: "2026-05-01T00:10:00Z"
review:
  status: approve
  reviewed_at: "2026-05-01T00:05:00Z"
  review_file: ".helix/reviews/plans/PLAN-200.json"
YAML
  python3 "$HELIX_ROOT/cli/lib/yaml_parser.py" write "$PROJECT_ROOT/.helix/plans/PLAN-200.yaml" "status" "finalized" >/dev/null

  run "$HELIX_ROOT/cli/helix" plan reset --id PLAN-200 --to draft --reason "E2E test"
  [ "$status" -eq 0 ]
  [[ "$output" == *"reset 完了: PLAN-200 (finalized -> draft, revision=1)"* ]]

  run python3 - <<'PY' "$HELIX_ROOT" "$PROJECT_ROOT"
import json
import sqlite3
import sys
from pathlib import Path

helix_root = Path(sys.argv[1])
project_root = Path(sys.argv[2])
sys.path.insert(0, str(helix_root / "cli" / "lib"))

import yaml_parser

plan = yaml_parser.parse_yaml((project_root / ".helix" / "plans" / "PLAN-200.yaml").read_text(encoding="utf-8"))
assert plan["status"] == "draft", plan
assert plan["revision_history"][0]["action"] == "plan_reset", plan
assert plan["revision_history"][0]["reason"] == "E2E test", plan

conn = sqlite3.connect(project_root / ".helix" / "helix.db")
row = conn.execute("SELECT data_json FROM events WHERE event_name = 'plan_reset'").fetchone()
conn.close()
payload = json.loads(row[0])
assert payload["plan_id"] == "PLAN-200", payload
assert payload["reason"] == "E2E test", payload
PY
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix" plan list
  [ "$status" -eq 0 ]
  [[ "$output" == *"PLAN-200"*"draft"* ]]
}

@test "carry chain can move a finding across plans" {
  finding_id="$(add_finding "PLAN-A" "Lx" "medium" "Cross plan carry")"

  run "$HELIX_ROOT/cli/helix" readiness defer --finding "$finding_id" --to PLAN-B:L9
  [ "$status" -eq 0 ]
  [[ "$output" == *"deferred: $finding_id -> PLAN-B:L9"* ]]

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
assert finding["current"] == {"plan_id": "PLAN-B", "phase": "L9"}, finding
assert finding["carry_chain"][0]["from"] == "PLAN-A:Lx", finding
assert finding["carry_chain"][0]["to"] == "PLAN-B:L9", finding
PY
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix" readiness list --plan PLAN-B
  [ "$status" -eq 0 ]
  [[ "$output" == *"$finding_id"*"P2"*"carried"*"Cross plan carry"* ]]
}
