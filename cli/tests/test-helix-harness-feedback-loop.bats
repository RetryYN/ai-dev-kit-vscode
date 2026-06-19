#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  TMP_ROOT="$(mktemp -d)"
  DB_PATH="$TMP_ROOT/helix.db"
  export HELIX_DB_PATH="$DB_PATH"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  python3 - "$HELIX_ROOT" "$DB_PATH" <<'PY'
import sqlite3
import sys

sys.path.insert(0, sys.argv[1])
from cli.lib import helix_db

conn = sqlite3.connect(sys.argv[2])
helix_db.migrate_all(conn)
conn.close()
PY
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

seed_feedback_loop_inputs() {
  python3 - "$HELIX_ROOT" "$DB_PATH" <<'PY'
import sqlite3
import sys
from datetime import UTC, datetime, timedelta

sys.path.insert(0, sys.argv[1])
from cli.lib import helix_db, harness_monitor

db_path = sys.argv[2]
now = datetime.now(UTC)
with helix_db._write_connection(db_path) as conn:
    conn.execute(
        """
        INSERT INTO automation_runs (
            run_kind, trigger_actor, plan_id, started_at, status, summary, retry_count, max_retries
        ) VALUES (?, ?, ?, ?, ?, ?, 0, 0)
        """,
        (
            "push",
            "system",
            "PLAN-FEEDBACK",
            (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "running",
            "long-running push",
        ),
    )
    conn.execute(
        """
        INSERT INTO hook_events (event_type, file, result, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            "drift_check_db_schema_drift",
            "docs/v2/L3-detailed-design/D-DB/D-DB-SEP-draft.md",
            "warn",
            (now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )

harness_monitor.record_event(
    "push",
    "slot_count_warning",
    severity="warning",
    payload={"active": 7},
)
PY
}

@test "helix harness is routed from top-level help" {
  run "$HELIX_ROOT/cli/helix" help
  [ "$status" -eq 0 ]
  [[ "$output" == *"harness"* ]]

  run "$HELIX_ROOT/cli/helix" harness --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"feedback-loop"* ]]
}

@test "helix harness feedback-loop emits route and learning candidates as json" {
  seed_feedback_loop_inputs

  run "$HELIX_ROOT/cli/helix" harness feedback-loop --json --days 30
  [ "$status" -eq 0 ]

  FEEDBACK_JSON="$output" python3 - "$HELIX_ROOT/docs/v2/L7-test-design/right-arm-execution-gates-adoption.yaml" <<'PY'
import json
import os
import sys
import yaml

manifest_path = sys.argv[1]
payload = json.loads(os.environ["FEEDBACK_JSON"])
with open(manifest_path, encoding="utf-8") as handle:
    manifest = yaml.safe_load(handle)
manifest_deferred = {
    item["pair"]: item["gate_id"]
    for item in manifest["gates"]
}
manifest_plans = {
    item["gate_id"]: item["plan_id"]
    for item in manifest["gates"]
}
assert payload["schema_version"] == "helix_harness_feedback_loop_snapshot_v1"
assert "plan_candidates" in payload
assert "plan_draft_candidates" not in payload
assert payload["counts"]["automation_running"] == 1
assert payload["counts"]["hook_warn_fail"] == 1
assert payload["counts"]["harness_warning_critical"] == 1
signals = [item["signal"] for item in payload["route_candidates"]]
assert "long_running_task" in signals
assert "drift" in signals
assert "regression_dev" in signals
assert any(item["kind"] == "detector_pattern" for item in payload["learning_candidates"])
assert any(item["kind"] == "full_flow_deferred_execution_gate" for item in payload["learning_candidates"])
assert any(item["kind"] == "not_applicable_pair_waiver" for item in payload["learning_candidates"])
expected_live_deferred = {
    "L4-L9": "G9",
    "L3-L12": "G12",
    "L1-L14": "G14",
}
expected_manifest_deferred = {
    "L5-L8": "G8",
    **expected_live_deferred,
}
deferred_pairs = {
    item["pair"]: item["gate_id"]
    for item in payload["vg_overview"]["deferred_pairs"]
}
deferred_learning_pairs = {
    (item["pair"], item["gate_id"])
    for item in payload["learning_candidates"]
    if item["kind"] == "full_flow_deferred_execution_gate"
}
vg_pr_candidates = [
    item
    for item in payload["pr_candidates"]
    if item.get("source_pattern_key") == "vg_overview:full_flow_deferred_execution_gate"
]
pr_source_keys = {
    item.get("source_pattern_key")
    for item in payload["pr_candidates"]
    if item.get("source_pattern_key")
}
assert payload["vg_overview"]["available"] is True
assert payload["vg_overview"]["enforced"] is True
assert payload["vg_overview"]["deferred_count"] == 3
assert payload["vg_overview"]["not_applicable_count"] == 1
assert deferred_pairs == expected_live_deferred
assert manifest_deferred == expected_manifest_deferred
assert manifest_plans == {
    "G8": "PLAN-G8-INTEGRATION-EXECUTION-GATE",
    "G9": "PLAN-G9-SYSTEM-EXECUTION-GATE",
    "G12": "PLAN-G12-ACCEPTANCE-EXECUTION-GATE",
    "G14": "PLAN-G14-OPERATIONAL-LEARNING-GATE",
}
assert set(expected_live_deferred.items()) <= deferred_learning_pairs
for pair, gate_id in expected_live_deferred.items():
    assert any(pair in item["change_summary"][0] and gate_id in item["change_summary"][0] for item in vg_pr_candidates)
assert pr_source_keys == {
    "automation_runs:automation_running_pattern",
    "events/metrics:missing_observability_input",
    "feedback:missing_feedback_input",
    "harness_check_events:harness_warning_pattern",
    "hook_events:detector_pattern",
    "verify_runs:missing_verify_input",
    "vg_overview:full_flow_deferred_execution_gate",
    "vg_overview:not_applicable_pair_waiver",
}
assert payload["plan_candidates"]
assert payload["plan_candidates"][0]["candidate_type"] == "plan"
assert payload["pr_candidates"]
assert any(item["candidate_type"] == "pr" for item in payload["pr_candidates"])
assert payload["safety"]["schema_migration"] is False
assert payload["safety"]["auto_apply"] is False
assert payload["safety"]["writes_detector_or_gate"] is False
PY

  python3 - "$DB_PATH" "$HELIX_ROOT/docs/v2/L7-test-design/right-arm-execution-gates-adoption.yaml" <<'PY'
import json
import sqlite3
import sys
import yaml

conn = sqlite3.connect(sys.argv[1])
with open(sys.argv[2], encoding="utf-8") as handle:
    manifest = yaml.safe_load(handle)
manifest_deferred = {
    item["pair"]: item["gate_id"]
    for item in manifest["gates"]
}
event_count = conn.execute(
    "SELECT COUNT(*) FROM events WHERE event_name = 'harness.feedback_loop.snapshot'"
).fetchone()[0]
metric_count = conn.execute(
    "SELECT COUNT(*) FROM metrics WHERE metric_name LIKE 'harness.feedback_loop.%'"
).fetchone()[0]
metric_values = dict(
    conn.execute(
        """
        SELECT metric_name, value
        FROM metrics
        WHERE metric_name IN (
            'harness.feedback_loop.full_flow_deferred_gates',
            'harness.feedback_loop.not_applicable_pairs'
        )
        """
    ).fetchall()
)
feedback_count = conn.execute(
    "SELECT COUNT(*) FROM feedback WHERE category = 'missing-action'"
).fetchone()[0]
event_row = conn.execute(
    """
    SELECT data_json, source, severity
    FROM events
    WHERE event_name = 'harness.feedback_loop.snapshot'
    ORDER BY id DESC
    LIMIT 1
    """
).fetchone()
assert event_count == 1
assert metric_count == 7
assert metric_values["harness.feedback_loop.full_flow_deferred_gates"] == 3
assert metric_values["harness.feedback_loop.not_applicable_pairs"] == 1
assert feedback_count == 1
assert event_row is not None
event_payload = json.loads(event_row[0])
assert event_row[1] == "helix-harness"
assert event_row[2] == "warning"
assert event_payload["schema_version"] == "helix_harness_feedback_loop_snapshot_v1"
assert event_payload["route_candidates"] == 3
assert event_payload["learning_candidates"] == 10
assert event_payload["plan_candidates"] == 3
assert event_payload["pr_candidates"] == 10
assert event_payload["missing_inputs"] == 3
assert event_payload["safety"]["schema_migration"] is False
assert event_payload["safety"]["auto_apply"] is False
assert event_payload["safety"]["writes_detector_or_gate"] is False
assert event_payload["vg_overview"]["deferred_count"] == 3
assert event_payload["vg_overview"]["not_applicable_count"] == 1
PY
}

@test "helix harness feedback-loop text output is human readable" {
  run "$HELIX_ROOT/cli/helix" harness feedback-loop --days 1
  [ "$status" -eq 0 ]
  [[ "$output" == *"[Feedback Loop]"* ]]
  [[ "$output" == *"[Route Candidates]"* ]]
  [[ "$output" == *"[Learning Candidates]"* ]]
  [[ "$output" == *"[PLAN Draft Candidates]"* ]]
  [[ "$output" == *"[PR Candidates]"* ]]
  [[ "$output" == *"L4-L9 remains deferred for G9; implement G9 system-test execution gate"* ]]
  [[ "$output" == *"L3-L12 remains deferred for G12; implement G12 acceptance-test execution gate"* ]]
  [[ "$output" == *"L1-L14 remains deferred for G14; implement G14 operational-learning execution gate"* ]]
  [[ "$output" == *"L2-L10 is not_applicable by ui_absent waiver owned by TL"* ]]
}
