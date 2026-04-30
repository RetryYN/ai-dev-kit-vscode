#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/.helix/plans" "$PROJECT_ROOT/.helix/reviews/plans" "$HOME_DIR"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

write_plan() {
  local id="$1"
  local status="$2"
  local finalized_at="$3"
  cat > "$PROJECT_ROOT/.helix/plans/$id.yaml" <<YAML
id: $id
title: Reset Test
status: $status
created_at: "2026-05-01T00:00:00Z"
source_file: null
finalized_at: $finalized_at
review:
  status: approve
  reviewed_at: "2026-04-30T15:57:16Z"
  review_file: ".helix/reviews/plans/$id.json"
YAML
}

@test "helix plan reset finalized to draft" {
  write_plan "PLAN-101" "finalized" "\"2026-04-30T15:57:34Z\""

  run "$HELIX_ROOT/cli/helix" plan reset --id PLAN-101 --to draft --reason "v2 改訂"
  [ "$status" -eq 0 ]
  [[ "$output" == *"reset 完了: PLAN-101 (finalized -> draft, revision=1)"* ]]

  run "$HELIX_ROOT/cli/helix" plan status --id PLAN-101
  [ "$status" -eq 0 ]
  [[ "$output" == *"Status:      draft"* ]]
  [[ "$output" == *"Finalized At:"* ]]
  [[ "$output" != *"2026-04-30T15:57:34Z"* ]]

  run python3 - <<'PY'
import json
import sqlite3
from pathlib import Path

import yaml

data = yaml.safe_load(Path(".helix/plans/PLAN-101.yaml").read_text(encoding="utf-8"))
assert data["status"] == "draft", data
assert data["finalized_at"] is None, data
assert data["review"]["status"] is None, data
hist = data["revision_history"]
assert len(hist) == 1, hist
entry = hist[0]
assert entry["revision"] == 1, entry
assert entry["from_status"] == "finalized", entry
assert entry["to_status"] == "draft", entry
assert entry["reason"] == "v2 改訂", entry
assert entry["reviewed_at"] == "2026-04-30T15:57:16Z", entry
assert entry["verdict"] == "approve", entry
assert entry["review_file"] == ".helix/reviews/plans/PLAN-101.json", entry
assert entry["finalized_at"] == "2026-04-30T15:57:34Z", entry

conn = sqlite3.connect(".helix/helix.db")
row = conn.execute("SELECT data_json FROM events WHERE event_name = 'plan_reset'").fetchone()
conn.close()
payload = json.loads(row[0])
assert payload == {
    "plan_id": "PLAN-101",
    "from_status": "finalized",
    "to_status": "draft",
    "reason": "v2 改訂",
    "revision": 1,
}, payload
PY
  [ "$status" -eq 0 ]
}

@test "helix plan reset finalized to reviewed" {
  write_plan "PLAN-102" "finalized" "\"2026-04-30T15:57:34Z\""

  run "$HELIX_ROOT/cli/helix" plan reset --id PLAN-102 --to reviewed --reason "finalize のみ取り消し"
  [ "$status" -eq 0 ]
  [[ "$output" == *"reset 完了: PLAN-102 (finalized -> reviewed, revision=1)"* ]]

  run python3 - <<'PY'
from pathlib import Path

import yaml

data = yaml.safe_load(Path(".helix/plans/PLAN-102.yaml").read_text(encoding="utf-8"))
assert data["status"] == "reviewed", data
assert data["finalized_at"] is None, data
assert data["review"]["status"] == "approve", data
entry = data["revision_history"][0]
assert entry["from_status"] == "finalized", entry
assert entry["to_status"] == "reviewed", entry
assert entry["verdict"] == "approve", entry
assert entry["finalized_at"] == "2026-04-30T15:57:34Z", entry
PY
  [ "$status" -eq 0 ]
}

@test "helix plan reset rejects draft status" {
  write_plan "PLAN-103" "draft" "null"

  run "$HELIX_ROOT/cli/helix" plan reset --id PLAN-103 --to draft
  [ "$status" -ne 0 ]
  [[ "$output" == *"reset 可能な status は finalized/reviewed のみです"* ]]
}
