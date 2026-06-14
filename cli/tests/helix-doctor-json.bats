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
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  cd "$PROJECT_ROOT"
  git init >/dev/null 2>&1
  git config user.email "t@t"
  git config user.name "T"
  printf "# doctor test\n" > README.md
  git add README.md
  git commit -q -m "init"
  "$HELIX_ROOT/cli/helix" init --project-name doctor-json >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix doctor --json emits valid JSON" {
  run bash -lc "\"$HELIX_ROOT/cli/helix\" doctor --json | python3 -c 'import json,sys; d=json.load(sys.stdin); assert \"pass\" in d and \"warn\" in d and isinstance(d[\"advisories\"], list)'"
  [ "$status" -eq 0 ]
}

@test "helix doctor without --json keeps text output" {
  run "$HELIX_ROOT/cli/helix" doctor
  [ "$status" -eq 0 ]
  [[ "$output" == *"=== HELIX Doctor ==="* ]]
  [[ "$output" == *"結果:"* ]]
  [[ "$output" != \{* ]]
}

@test "helix doctor --json accepts --max-age-days in any order" {
  run bash -lc "\"$HELIX_ROOT/cli/helix\" doctor --json --max-age-days 7 | python3 -c 'import json,sys; json.load(sys.stdin)'"
  [ "$status" -eq 0 ]

  run bash -lc "\"$HELIX_ROOT/cli/helix\" doctor --max-age-days 7 --json | python3 -c 'import json,sys; json.load(sys.stdin)'"
  [ "$status" -eq 0 ]
}

@test "helix doctor --json keeps stdout free of text pollution" {
  run "$HELIX_ROOT/cli/helix" doctor --json
  [ "$status" -eq 0 ]
  [[ "$output" == \{* ]]
  [[ "$output" != *"HELIX Doctor"* ]]
  [[ "$output" != *"[必須依存]"* ]]
  [[ "$output" != *"結果:"* ]]
}

@test "helix-doctor check_g7_subcheck --json emits valid JSON" {
  run env HELIX_PROJECT_ROOT="$HELIX_ROOT" HELIX_DOCTOR_SKIP_EXEC_TESTS=1 bash -lc "set -o pipefail; \"$HELIX_ROOT/cli/helix-doctor\" check_g7_subcheck --json | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d[\"exit_code\"] == 0; assert \"missing\" in d and \"exec_pass\" in d; all_ids = d[\"anchored\"][\"ids\"] + d[\"missing\"][\"ids\"] + d[\"unanchored_but_exists\"][\"ids\"]; assert d[\"ut_total\"] == 98; assert not any(item.startswith((\"RD-UT-\", \"DGA-UT-\", \"EGA-UT-\")) for item in all_ids), all_ids'"
  [ "$status" -eq 0 ]
}

@test "helix-doctor check_vg_overview --json emits valid JSON" {
  run env HELIX_PROJECT_ROOT="$HELIX_ROOT" HELIX_DOCTOR_SKIP_EXEC_TESTS=1 bash -lc "set -o pipefail; \"$HELIX_ROOT/cli/helix-doctor\" check_vg_overview --json | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d[\"exit_code\"] == 0; assert \"vg_overview\" in d and \"g7_subcheck\" in d; vg=d[\"vg_overview\"]; rd=vg[\"required_clean\"].get(\"requirement_drift\"); assert rd and rd[\"focus\"] == \"L6\"; assert rd[\"requirements\"] == 31; assert rd[\"design_links\"] == 31; assert rd[\"finding_count\"] == 0; full=vg[\"full_flow_execution\"]; assert full[\"enforced\"] is False; assert full[\"clean\"] is False; assert full[\"deferred_count\"] == 4'"
  [ "$status" -eq 0 ]
}

@test "helix-doctor check_vg_overview --strict-full-flow exposes deferred execution gates" {
  run env HELIX_PROJECT_ROOT="$HELIX_ROOT" HELIX_DOCTOR_SKIP_EXEC_TESTS=1 bash -lc "set -o pipefail; \"$HELIX_ROOT/cli/helix-doctor\" check_vg_overview --strict-full-flow --json | python3 -c 'import json,sys; d=json.load(sys.stdin); vg=d[\"vg_overview\"]; full=vg[\"full_flow_execution\"]; pairs={item[\"pair\"]: item[\"gate_id\"] for item in full[\"deferred_pairs\"]}; assert full[\"enforced\"] is True; assert full[\"clean\"] is False; assert full[\"deferred_count\"] == 4; assert pairs == {\"L5-L8\":\"G8\", \"L4-L9\":\"G9\", \"L3-L12\":\"G12\", \"L1-L14\":\"G14\"}; assert vg[\"overall_clean\"] is False'"
  [ "$status" -eq 0 ]
}

@test "helix-doctor --gate --json matches VG-overview pre-push cleanliness" {
  run env HELIX_PROJECT_ROOT="$HELIX_ROOT" HELIX_DOCTOR_SKIP_EXEC_TESTS=1 bash -lc "set -o pipefail; clean=\$(\"$HELIX_ROOT/cli/helix-doctor\" check_vg_overview --json | python3 -c 'import json,sys; print(str(json.load(sys.stdin)[\"vg_overview\"][\"overall_clean\"]).lower())'); export clean; (\"$HELIX_ROOT/cli/helix-doctor\" --gate --json || true) | python3 -c 'import json,os,sys; d=json.load(sys.stdin); clean=os.environ[\"clean\"] == \"true\"; names=[a[\"name\"] for a in d[\"advisories\"]]; has_vg=any(name == \"VG-overview pre-push\" for name in names); assert has_vg is (not clean), (clean, names); assert ((d[\"fail\"] == 0) if clean else (d[\"fail\"] > 0)), d'"
  [ "$status" -eq 0 ]
}

@test "helix-doctor --gate --json reports phase_gate_progress when G6 passed but current_phase lags" {
  cat > "$PROJECT_ROOT/.helix/phase.yaml" <<'EOF'
current_mode: forward
current_phase: L4
gates:
  G6:
    status: passed
EOF

  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" HELIX_DOCTOR_SKIP_EXEC_TESTS=1 bash -lc "(\"$HELIX_ROOT/cli/helix-doctor\" --gate --json || true) | python3 -c 'import json,sys; d=json.load(sys.stdin); assert any(a.get(\"status\") == \"warning\" and \"phase_gate_progress: G6 passed\" in a.get(\"name\", \"\") for a in d[\"advisories\"]), d[\"advisories\"]'"
  [ "$status" -eq 0 ]
}

@test "helix-doctor --gate --json accepts G6 passed when current_phase is L6" {
  cat > "$PROJECT_ROOT/.helix/phase.yaml" <<'EOF'
current_mode: forward
current_phase: L6
gates:
  G6:
    status: passed
EOF

  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" HELIX_DOCTOR_SKIP_EXEC_TESTS=1 bash -lc "(\"$HELIX_ROOT/cli/helix-doctor\" --gate --json || true) | python3 -c 'import json,sys; d=json.load(sys.stdin); names=[a.get(\"name\", \"\") for a in d[\"advisories\"]]; assert not any(\"phase_gate_progress\" in name for name in names), names'"
  [ "$status" -eq 0 ]
}

@test "helix-doctor check_recovery_plan_freshness --json stays blocked" {
  run env HELIX_PROJECT_ROOT="$HELIX_ROOT" "$HELIX_ROOT/cli/helix-doctor" check_recovery_plan_freshness --json
  [ "$status" -eq 2 ]
  [[ "$output" == *"--json はデフォルト doctor 出力でのみ使用できます"* ]]
}

@test "helix recover check shows C2 CLEAR when doctor json is clean" {
  STUB_HOME="$TMP_ROOT/stub-home"
  mkdir -p "$STUB_HOME/cli"
  cat > "$STUB_HOME/cli/helix-doctor" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' '{"timestamp":"2026-05-24T00:00:00+09:00","pass":1,"fail":0,"warn":0,"advisories":[],"summary":"1 pass, 0 fail, 0 warn"}'
EOF
  cat > "$STUB_HOME/cli/helix-budget" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' '{"claude":{"weekly_used_pct":0},"codex":{"weekly_used_pct":0}}'
EOF
  chmod +x "$STUB_HOME/cli/helix-doctor" "$STUB_HOME/cli/helix-budget"
  printf '%s\n' 'current_phase: L1' > "$PROJECT_ROOT/.helix/phase.yaml"

  run env HELIX_HOME="$STUB_HOME" HELIX_PROJECT_ROOT="$PROJECT_ROOT" PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$HELIX_ROOT/cli/helix-recover" check
  [ "$status" -eq 0 ]
  [[ "$output" == *"C2 工程逸脱: CLEAR"* ]]
}

# --- check_vg_overview --gate exit semantics (CI Required check が依存する契約) ---

@test "check_vg_overview --gate --json exits 0 when overall_clean" {
  run env HELIX_PROJECT_ROOT="$HELIX_ROOT" HELIX_DOCTOR_SKIP_EXEC_TESTS=1 "$HELIX_ROOT/cli/helix-doctor" check_vg_overview --gate --json
  [ "$status" -eq 0 ]
}

@test "check_vg_overview --json (no --gate) stays advisory exit 0" {
  run env HELIX_PROJECT_ROOT="$HELIX_ROOT" HELIX_DOCTOR_SKIP_EXEC_TESTS=1 "$HELIX_ROOT/cli/helix-doctor" check_vg_overview --json
  [ "$status" -eq 0 ]
}

@test "check_vg_overview --gate --strict-full-flow --json fails closed (exit 1) when overall_clean false" {
  run env HELIX_PROJECT_ROOT="$HELIX_ROOT" HELIX_DOCTOR_SKIP_EXEC_TESTS=1 "$HELIX_ROOT/cli/helix-doctor" check_vg_overview --gate --strict-full-flow --json
  [ "$status" -eq 1 ]
}

@test "check_vg_overview --strict-full-flow --json (no --gate) stays advisory exit 0" {
  run env HELIX_PROJECT_ROOT="$HELIX_ROOT" HELIX_DOCTOR_SKIP_EXEC_TESTS=1 "$HELIX_ROOT/cli/helix-doctor" check_vg_overview --strict-full-flow --json
  [ "$status" -eq 0 ]
}

@test "check_vg_overview --gate is project-state independent (passes in fresh checkout without .helix)" {
  FRESH="$TMP_ROOT/fresh-checkout"
  mkdir -p "$FRESH"
  git -C "$HELIX_ROOT" archive HEAD | tar -x -C "$FRESH"
  # uncommitted な helix-doctor / vg_overview を反映 (CI と同じ fresh tree + 検証対象の実装)
  cp "$HELIX_ROOT/cli/helix-doctor" "$FRESH/cli/helix-doctor"
  cp "$HELIX_ROOT/cli/lib/vg_overview.py" "$FRESH/cli/lib/vg_overview.py"
  [ ! -d "$FRESH/.helix" ]
  run env HELIX_HOME="$FRESH" HELIX_PROJECT_ROOT="$FRESH" HELIX_DOCTOR_SKIP_EXEC_TESTS=1 "$FRESH/cli/helix-doctor" check_vg_overview --gate --json
  [ "$status" -eq 0 ]
}
