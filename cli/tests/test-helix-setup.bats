#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR"
  cd "$PROJECT_ROOT"
  git init >/dev/null 2>&1
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix setup list shows sample components" {
  run "$HELIX_ROOT/cli/helix" setup list
  [ "$status" -eq 0 ]
  [[ "$output" == *"gitleaks"* ]]
  [[ "$output" == *"gitignore-helix"* ]]
  [[ "$output" == *"redaction-denylist"* ]]
}

@test "helix setup install redaction-denylist creates template" {
  run "$HELIX_ROOT/cli/helix" setup install --name redaction-denylist
  [ "$status" -eq 0 ]
  [[ "$output" == *"created redaction denylist example"* ]]
  [ -f "$PROJECT_ROOT/.helix/audit/redaction-denylist.example.yaml" ]

  run python3 - "$PROJECT_ROOT/.helix/helix.db" <<'PY'
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
check = conn.execute(
    "SELECT installed FROM setup_checks WHERE component = ?",
    ("redaction-denylist",),
).fetchone()
event = conn.execute(
    "SELECT status FROM setup_events WHERE component = ? AND action = 'install'",
    ("redaction-denylist",),
).fetchone()
raise SystemExit(0 if check and check[0] == 1 and event and event[0] == "success" else 1)
PY
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix" setup install --name redaction-denylist
  [ "$status" -eq 0 ]
  [[ "$output" == *"already exists"* ]]
}

@test "helix setup verify unknown component returns 2" {
  run "$HELIX_ROOT/cli/helix" setup verify --name missing-component
  [ "$status" -eq 2 ]
  [[ "$output" == *"unknown component: missing-component"* ]]
}

@test "helix setup preflight project works before init with warnings" {
  run "$HELIX_ROOT/cli/helix" setup preflight --profile project --json
  [ "$status" -eq 0 ]
  PAYLOAD="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["PAYLOAD"])
assert payload["profile"] == "project"
assert payload["status"] == "pass"
assert payload["summary"]["warn"] >= 1
assert any(check["name"] == "helix-initialized" for check in payload["checks"])
PY
}

@test "helix setup preflight reverse fails before init" {
  run "$HELIX_ROOT/cli/helix" setup preflight --profile reverse
  [ "$status" -eq 1 ]
  [[ "$output" == *"FAIL: helix-initialized"* ]]
}

@test "helix setup preflight reverse passes after init" {
  run "$HELIX_ROOT/cli/helix" init --project-name setup-preflight
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix" setup preflight --profile reverse --reverse-type code --target .
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: helix-initialized"* ]]
  [[ "$output" == *"PASS: reverse-code-target"* ]]
}

@test "helix setup bootstrap initializes project in one command" {
  run "$HELIX_ROOT/cli/helix" setup bootstrap --project-name one-shot --json
  [ "$status" -eq 0 ]
  PAYLOAD="$output" PROJECT_ROOT="$PROJECT_ROOT" python3 - <<'PY'
import json
import os
from pathlib import Path

payload = json.loads(os.environ["PAYLOAD"])
root = Path(os.environ["PROJECT_ROOT"])
assert payload["status"] == "pass"
step_names = {step["name"] for step in payload["steps"]}
assert {"preflight-before", "helix-init", "helix-log-init", "matrix-compile", "matrix-auto-detect", "preflight-after"} <= step_names
assert (root / ".helix" / "phase.yaml").exists()
assert (root / ".helix" / "helix.db").exists()
assert (root / ".helix" / "runtime" / "index.json").exists()
assert (root / ".helix" / "audit" / "redaction-denylist.example.yaml").exists()
assert (root / "CLAUDE.md").exists()
assert (root / "AGENTS.md").exists()
PY
}

@test "helix setup bootstrap is idempotent" {
  run "$HELIX_ROOT/cli/helix" setup bootstrap --project-name one-shot
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix" setup bootstrap --project-name one-shot
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: preflight-after"* ]]
}

@test "helix setup packages list shows installable package scripts" {
  run "$HELIX_ROOT/cli/helix" setup packages list --json
  [ "$status" -eq 0 ]
  PAYLOAD="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["PAYLOAD"])
names = {row["name"] for row in payload["packages"]}
assert {"textlint", "playwright", "axe", "marp", "d2", "crawl4ai", "bats"} <= names
assert all(row["available"] == "yes" for row in payload["packages"])
PY
}

@test "helix setup packages install defaults to dry-run" {
  run "$HELIX_ROOT/cli/helix" setup packages install --name textlint
  [ "$status" -eq 0 ]
  [[ "$output" == *"dry-run"* ]]
  [[ "$output" == *"setup-textlint.sh"* ]]
  [ ! -f "$PROJECT_ROOT/package.json" ]
}

@test "helix setup packages install rejects unknown package" {
  run "$HELIX_ROOT/cli/helix" setup packages install --name unknown
  [ "$status" -eq 2 ]
  [[ "$output" == *"invalid choice"* ]]
}
