#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  mkdir -p "$PROJECT_ROOT/docs/v2/L3-requirements" "$PROJECT_ROOT/docs/v2/L6-functional-design" "$PROJECT_ROOT/cli/lib/tests"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "requirement_drift pytest suite passes" {
  run python3 -m pytest "$HELIX_ROOT/cli/lib/tests/test_requirement_drift.py" -q
  [ "$status" -eq 0 ]
  [[ "$output" == *"17 passed"* ]]
}

@test "helix-doctor check_requirement_drift --json emits clean JSON" {
  cat > "$PROJECT_ROOT/docs/v2/L3-requirements/fr.md" <<'EOF'
| ID | Name |
|---|---|
| FR-001 | Export reports |
EOF
  cat > "$PROJECT_ROOT/docs/v2/L6-functional-design/spec.md" <<'EOF'
| ID | Name |
|---|---|
| FR-001 | Export reports |
EOF
  cat > "$PROJECT_ROOT/cli/lib/reports.py" <<'EOF'
# FR-001 Export reports
EOF
  cat > "$PROJECT_ROOT/cli/lib/tests/test_reports.py" <<'EOF'
# FR-001 Export reports
EOF

  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" "$HELIX_ROOT/cli/helix-doctor" check_requirement_drift --json
  [ "$status" -eq 0 ]
  printf '%s' "$output" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["clean"] is True; assert d["focus"] == "L6"; assert d["stale_check_enabled"] is False; assert d["scope"] == "L1_FR -> L3_FR -> L4-L6_design"; assert d["summary"]["requirements"] == 1; assert d["summary"]["code_links"] == 0'
}

@test "helix-doctor check_requirement_drift --focus L7 scans code/test links" {
  cat > "$PROJECT_ROOT/docs/v2/L3-requirements/fr.md" <<'EOF'
| ID | Name |
|---|---|
| FR-001 | Export reports |
EOF
  cat > "$PROJECT_ROOT/docs/v2/L6-functional-design/spec.md" <<'EOF'
| ID | Name |
|---|---|
| FR-001 | Export reports |
EOF
  cat > "$PROJECT_ROOT/cli/lib/reports.py" <<'EOF'
# FR-001 Export reports
EOF
  cat > "$PROJECT_ROOT/cli/lib/tests/test_reports.py" <<'EOF'
# FR-001 Export reports
EOF

  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" "$HELIX_ROOT/cli/helix-doctor" check_requirement_drift --focus L7 --json
  [ "$status" -eq 0 ]
  printf '%s' "$output" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["clean"] is True; assert d["focus"] == "L7"; assert d["summary"]["code_links"] == 1; assert d["summary"]["test_links"] == 1'
}

@test "helix-doctor check_requirement_drift --check-stale enables stale advisory" {
  cat > "$PROJECT_ROOT/docs/v2/L3-requirements/fr.md" <<'EOF'
| ID | Name |
|---|---|
| FR-001 | Export reports |
EOF
  cat > "$PROJECT_ROOT/docs/v2/L6-functional-design/spec.md" <<'EOF'
| ID | Name |
|---|---|
| FR-001 | Export reports |
EOF
  touch -t 200001010000 "$PROJECT_ROOT/docs/v2/L6-functional-design/spec.md"
  touch -t 200001010001 "$PROJECT_ROOT/docs/v2/L3-requirements/fr.md"

  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" "$HELIX_ROOT/cli/helix-doctor" check_requirement_drift --check-stale --json
  [ "$status" -eq 0 ]
  printf '%s' "$output" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["blocking_clean"] is True; assert d["stale_check_enabled"] is True; assert d["findings"]["stale_freeze"][0]["requirement_id"] == "FR-001"'
}
