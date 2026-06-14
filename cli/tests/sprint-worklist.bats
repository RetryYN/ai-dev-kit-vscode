#!/usr/bin/env bats

snapshot_helix_state() {
  python3 - <<'PY' "$PROJECT_ROOT/.helix"
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
payload = []
for path in sorted(p for p in root.rglob("*") if p.is_file()):
    payload.append(
        {
            "path": str(path.relative_to(root)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    )
print(json.dumps(payload, sort_keys=True))
PY
}

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/.helix" "$PROJECT_ROOT/cli/config" "$PROJECT_ROOT/docs/v2/L7-test-design" "$HOME_DIR"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PYTHONPATH="$HELIX_ROOT/cli/lib${PYTHONPATH:+:$PYTHONPATH}"
  cd "$PROJECT_ROOT"

  cat > "$PROJECT_ROOT/.helix/phase.yaml" <<'YAML'
project: sprint-worklist-test
current_phase: L7
sprint:
  drive: be
  current_step: .2
  steps:
    .1a:
      status: completed
    .1b:
      status: completed
    .2:
      status: pending
YAML

  cat > "$PROJECT_ROOT/cli/config/functional-registry.yaml" <<'YAML'
entries:
  - id: FR-A
    name: fr-a
    domain: cli
    status: active
    coverage_layer: L6_required
    design_ids: [FN-WSC-221]
    test_design_ids: [UT-WSC-221]
    code_paths: [cli/lib/fr_a.py]
    doc_paths: []
  - id: FR-B
    name: fr-b
    domain: cli
    status: active
    coverage_layer: L6_required
    design_ids: [FN-WSC-222]
    test_design_ids: [UT-WSC-222]
    code_paths: [cli/lib/fr_b.py]
    doc_paths: []
  - id: FR-C
    name: fr-c
    domain: cli
    status: active
    coverage_layer: L6_required
    design_ids: [FN-WSC-223]
    test_design_ids: [UT-WSC-223]
    code_paths: [cli/lib/fr_c.py]
    doc_paths: []
fn_ut_pair_waivers:
  - fn: FN-WSC-222
    ut: UT-WSC-222
    reason: deferred
    owner: TL
YAML

  cat > "$PROJECT_ROOT/docs/v2/L7-test-design/g7-test-anchor-map.yaml" <<'YAML'
anchors:
  UT-WSC-221:
    - cli/lib/tests/test_alpha.py
YAML
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix sprint status surfaces L7 worklist summary counts" {
  run "$HELIX_ROOT/cli/helix" sprint status
  [ "$status" -eq 0 ]
  [[ "$output" == *"L7 worklist (FN↔UT 充足ビュー)"* ]]
  [[ "$output" == *"total=3 anchored=1 waived=1 separate_inventory=0 missing_ut=1"* ]]
  [[ "$output" == *"hint: missing_ut を L7 sprint 起票前に backlog/PLAN へ手動反映してください"* ]]
}

@test "helix sprint next start path also surfaces worklist summary" {
  python3 "$HELIX_ROOT/cli/lib/yaml_parser.py" write "$PROJECT_ROOT/.helix/phase.yaml" sprint.current_step null >/dev/null

  run "$HELIX_ROOT/cli/helix" sprint next
  [ "$status" -eq 0 ]
  [[ "$output" == *"Sprint 開始: .1a"* ]]
  [[ "$output" == *"L7 worklist (FN↔UT 充足ビュー)"* ]]
  [[ "$output" == *"missing_ut=1"* ]]
}

@test "helix sprint status surfacing is read-only for sprint state" {
  before_snapshot="$(snapshot_helix_state)"

  run "$HELIX_ROOT/cli/helix" sprint status
  [ "$status" -eq 0 ]

  after_snapshot="$(snapshot_helix_state)"
  [ "$before_snapshot" = "$after_snapshot" ]
}
