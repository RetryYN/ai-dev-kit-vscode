#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  mkdir -p "$PROJECT_ROOT/.helix"
  cd "$PROJECT_ROOT"
  git init -q
  git config user.email "test@example.com"
  git config user.name "Test User"
  echo init > README.md
  git add README.md
  git commit -q -m "init"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"

  cat > "$PROJECT_ROOT/.helix/phase.yaml" <<'YAML'
project: reverse-review-test
current_phase: L4
current_mode: forward
sprint:
  current_step: .2
  status: active
YAML
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix reverse R0 --review --dry-run smoke" {
  run "$HELIX_ROOT/cli/helix" reverse R0 --review --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"Reverse HELIX: code R0"* ]]
  [[ "$output" == *"--review"* ]]
  [[ "$output" == *".helix/reverse/r0/<YYYYmmddTHHMMSS>.json"* ]]
}

@test "helix reverse R0 --review writes review artifact on success" {
  MOCK_CODEX="$TMP_ROOT/mock-codex-reverse-r0"
  cat > "$MOCK_CODEX" <<'EOF'
#!/bin/bash
set -e
project_root="${HELIX_PROJECT_ROOT:-$(pwd)}"
mkdir -p "$project_root/.helix/reverse"
cat > "$project_root/.helix/reverse/R0-evidence-map.yaml" <<'YAML'
stage_id: R0
generated_at: "2026-05-08"
source_paths:
  - cli/helix-reverse
evidence_map:
  modules: []
YAML
EOF
  chmod +x "$MOCK_CODEX"

  run env CODEX_BIN="$MOCK_CODEX" "$HELIX_ROOT/cli/helix-reverse" R0 --review

  [ "$status" -eq 0 ]
  run bash -lc 'files=(.helix/reverse/r0/*.json); test ${#files[@]} -eq 1'
  [ "$status" -eq 0 ]
  run python3 - <<'PY'
import glob
import json

paths = glob.glob(".helix/reverse/r0/*.json")
assert len(paths) == 1, paths
payload = json.loads(open(paths[0], encoding="utf-8").read())
assert payload["reverse_type"] == "code", payload
assert payload["stage"] == "R0", payload
assert payload["gate"] == "RG0", payload
assert payload["status"] == "passed", payload
assert payload["output_artifact"].endswith(".helix/reverse/R0-evidence-map.yaml"), payload
PY
  [ "$status" -eq 0 ]
}

@test "helix handover dump accepts reverse-r0..r4 modes" {
  run bash -lc '
    set -euo pipefail
    for mode in reverse-r0 reverse-r1 reverse-r2 reverse-r3 reverse-r4; do
      rm -rf .helix/handover
      "'"$HELIX_ROOT"'/cli/helix" handover dump --mode "$mode" --sprint .2 --note "test" >/dev/null
      python3 - <<'"'"'PY'"'"' "$mode"
import json
import sys
from pathlib import Path

mode = sys.argv[1]
payload = json.loads(Path(".helix/handover/CURRENT.json").read_text(encoding="utf-8"))
assert payload["mode"] == mode, payload
PY
    done
  '

  [ "$status" -eq 0 ]
}
