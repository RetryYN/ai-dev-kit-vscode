#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  HELIX_TEST_TMPDIR="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$HELIX_TEST_TMPDIR"
  export HOME="$HELIX_TEST_TMPDIR/helix-home"
  mkdir -p "$HOME"
}

teardown() {
  rm -rf "$HELIX_TEST_TMPDIR" 2>/dev/null || true
}

@test "helix doctor shows pmo role consistency" {
  run "$HELIX_ROOT/cli/helix-doctor"
  if [ "$status" -ne 0 ] || [[ "$output" != *"✓ pmo role consistency"* ]]; then
    echo "doctor status=$status" >&2
    printf '%s\n' "$output" >&2
  fi
  [ "$status" -eq 0 ]
  [[ "$output" == *"✓ pmo role consistency"* ]]
}

@test "helix doctor --summary outputs JSON" {
  run bash -lc "\"$HELIX_ROOT/cli/helix\" doctor --summary | python3 -c 'import json,sys; d=json.load(sys.stdin); assert \"pass_count\" in d and \"sections\" in d and isinstance(d[\"sections\"], list)'"
  [ "$status" -eq 0 ]
}

@test "helix doctor includes skill frontmatter section" {
  run "$HELIX_ROOT/cli/helix-doctor"
  if [ "$status" -ne 0 ] || [[ "$output" != *"[skill frontmatter]"* ]]; then
    echo "doctor status=$status" >&2
    printf '%s\n' "$output" >&2
  fi
  [ "$status" -eq 0 ]
  [[ "$output" == *"[skill frontmatter]"* ]]
  [[ "$output" == *"check skills/* frontmatter:"* ]]
}

@test "helix doctor includes plan health section" {
  run "$HELIX_ROOT/cli/helix-doctor"
  if [ "$status" -ne 0 ] || [[ "$output" != *"[plan health]"* ]]; then
    echo "doctor status=$status" >&2
    printf '%s\n' "$output" >&2
  fi
  [ "$status" -eq 0 ]
  [[ "$output" == *"[plan health]"* ]]
  [[ "$output" == *"check plan health:"* ]]
}

@test "helix doctor includes vmodel pair freeze section" {
  run "$HELIX_ROOT/cli/helix-doctor"
  if [ "$status" -ne 0 ] || [[ "$output" != *"[V-model pair freeze]"* ]]; then
    echo "doctor status=$status" >&2
    printf '%s\n' "$output" >&2
  fi
  [ "$status" -eq 0 ]
  [[ "$output" == *"[V-model pair freeze]"* ]]
  [[ "$output" == *"check vmodel pair freeze:"* ]]
}

@test "helix doctor strict mode fails on critical missing" {
  run "$HELIX_ROOT/cli/helix-doctor" --strict-vmodel-pair-freeze
  if [ "$status" -ne 1 ] || [[ "$output" != *"critical:"* ]]; then
    echo "doctor status=$status" >&2
    printf '%s\n' "$output" >&2
  fi
  [ "$status" -eq 1 ]
  [[ "$output" == *"[V-model pair freeze]"* ]]
  [[ "$output" == *"critical:"* ]]
}

@test "helix doctor strict mode passes when no critical missing" {
  local l9_plan="$HELIX_ROOT/docs/plans/L9/L9-bats-temporaryplan.md"
  local l12_plan="$HELIX_ROOT/docs/plans/L12/L12-bats-temporaryplan.md"
  local l14_plan="$HELIX_ROOT/docs/plans/L14/L14-bats-temporaryplan.md"

  mkdir -p "$(dirname "$l9_plan")" "$(dirname "$l12_plan")" "$(dirname "$l14_plan")"
  trap 'rm -f "$l9_plan" "$l12_plan" "$l14_plan"' RETURN

  printf -- "---\nplan_id: L9-bats-temporaryplan\ntitle: temp\n---\n" > "$l9_plan"
  printf -- "---\nplan_id: L12-bats-temporaryplan\ntitle: temp\n---\n" > "$l12_plan"
  printf -- "---\nplan_id: L14-bats-temporaryplan\ntitle: temp\n---\n" > "$l14_plan"

  run "$HELIX_ROOT/cli/helix-doctor" --strict-vmodel-pair-freeze
  if [ "$status" -ne 0 ] || [[ "$output" != *"critical:0"* ]]; then
    echo "doctor status=$status" >&2
    printf '%s\n' "$output" >&2
  fi
  [ "$status" -eq 0 ]
  [[ "$output" == *"[V-model pair freeze]"* ]]
  [[ "$output" == *"critical:0"* ]]
}

@test "helix doctor --vmodel-pair-freeze-active-only shows active-only marker" {
  run "$HELIX_ROOT/cli/helix-doctor" --vmodel-pair-freeze-active-only
  if [ "$status" -ne 0 ] || [[ "$output" != *"(active-only)"* ]]; then
    echo "doctor status=$status" >&2
    printf '%s\n' "$output" >&2
  fi
  [ "$status" -eq 0 ]
  [[ "$output" == *"[V-model pair freeze]"* ]]
  [[ "$output" == *"(active-only)"* ]]
}

@test "helix doctor includes vmodel status breakdown" {
  run "$HELIX_ROOT/cli/helix-doctor"
  if [ "$status" -ne 0 ] || [[ "$output" != *"status breakdown:"* ]]; then
    echo "doctor status=$status" >&2
    printf '%s\n' "$output" >&2
  fi
  [ "$status" -eq 0 ]
  [[ "$output" == *"status breakdown:"* ]]
  [[ "$output" == *"draft="* ]]
  [[ "$output" == *"in_progress="* ]]
  [[ "$output" == *"completed="* ]]
  [[ "$output" == *"superseded="* ]]
  [[ "$output" == *"other="* ]]
}

@test "helix doctor --vmodel-pair-freeze-since-days marker" {
  run "$HELIX_ROOT/cli/helix-doctor" --vmodel-pair-freeze-since-days 30
  if [ "$status" -ne 0 ] || [[ "$output" != *"(since 30d)"* ]]; then
    echo "doctor status=$status" >&2
    printf '%s\n' "$output" >&2
  fi
  [ "$status" -eq 0 ]
  [[ "$output" == *"[V-model pair freeze]"* ]]
  [[ "$output" == *"(since 30d)"* ]]
}

@test "helix doctor --vmodel-pair-freeze-since-days shows stale count" {
  local stale_plan="$HELIX_ROOT/docs/plans/L7/L7-bats-stale-temporaryplan.md"

  mkdir -p "$(dirname "$stale_plan")"
  trap 'rm -f "$stale_plan"' RETURN
  printf -- "---\nplan_id: L7-bats-stale-temporaryplan\ntitle: temp\nrevised: 2000-01-01\nstatus: draft\n---\n" > "$stale_plan"

  run "$HELIX_ROOT/cli/helix-doctor" --vmodel-pair-freeze-since-days 30
  if [ "$status" -ne 0 ] || [[ "$output" != *"stale (older than 30d):"* ]]; then
    echo "doctor status=$status" >&2
    printf '%s\n' "$output" >&2
  fi
  [ "$status" -eq 0 ]
  [[ "$output" == *"[V-model pair freeze]"* ]]
  [[ "$output" == *"stale (older than 30d):"* ]]
}

@test "helix doctor --suggest-revisions outputs hints" {
  local stale_plan="$HELIX_ROOT/docs/plans/L9/L9-bats-suggest-stale-temporaryplan.md"

  mkdir -p "$(dirname "$stale_plan")"
  trap 'rm -f "$stale_plan"' RETURN
  printf -- "---\nplan_id: L9-bats-suggest-stale-temporaryplan\ntitle: temp\nrevised: 2000-01-01\nstatus: draft\n---\n" > "$stale_plan"

  run "$HELIX_ROOT/cli/helix" doctor --vmodel-pair-freeze-since-days 30 --suggest-revisions
  if [ "$status" -ne 0 ] || [[ "$output" != *"suggest revisions (example):"* ]]; then
    echo "doctor status=$status" >&2
    printf '%s\n' "$output" >&2
  fi
  [ "$status" -eq 0 ]
  [[ "$output" == *"[V-model pair freeze]"* ]]
  [[ "$output" == *"stale (older than 30d):"* ]]
  [[ "$output" == *"suggest revisions (example):"* ]]
}

@test "helix doctor --apply-stale-revisions dry-run output" {
  local stale_plan="$HELIX_ROOT/docs/plans/L9/L9-bats-apply-stale-temporaryplan.md"

  mkdir -p "$(dirname "$stale_plan")"
  trap 'rm -f "$stale_plan"' RETURN
  printf -- "---\nplan_id: L9-bats-apply-stale-temporaryplan\ntitle: temp\nrevised: 2000-01-01\nstatus: draft\n---\n" > "$stale_plan"

  run "$HELIX_ROOT/cli/helix" doctor --vmodel-pair-freeze-since-days 30 --apply-stale-revisions
  if [ "$status" -ne 0 ] || [[ "$output" != *"apply stale revisions (dry-run):"* ]]; then
    echo "doctor status=$status" >&2
    printf '%s\n' "$output" >&2
  fi
  [ "$status" -eq 0 ]
  [[ "$output" == *"[V-model pair freeze]"* ]]
  [[ "$output" == *"stale (older than 30d):"* ]]
  [[ "$output" == *"apply stale revisions (dry-run):"* ]]
}

@test "helix doctor --rollback-stale-revisions dry-run output" {
  local audit_file="$HELIX_ROOT/.helix/audit/stale-revisions.json"
  local stale_plan="$HELIX_ROOT/docs/plans/L9/L9-bats-rollback-stale-temporaryplan.md"

  mkdir -p "$(dirname "$audit_file")" "$(dirname "$stale_plan")"
  trap 'rm -f "$audit_file" "$stale_plan"' RETURN
  printf -- "---\nplan_id: L9-bats-rollback-stale-temporaryplan\ntitle: temp\nrevised: 2026-05-25\nstatus: draft\n---\n" > "$stale_plan"
  printf -- '[{"applied_at":"2026-05-25T00:00:00+09:00","layer":"L4","changes":[{"plan_path":"%s","before_revised":"2000-01-01","after_revised":"2026-05-25"}]}]\n' "$stale_plan" > "$audit_file"

  run "$HELIX_ROOT/cli/helix" doctor --rollback-stale-revisions
  if [ "$status" -ne 0 ] || [[ "$output" != *"rollback stale revisions (dry-run):"* ]]; then
    echo "doctor status=$status" >&2
    printf '%s\n' "$output" >&2
  fi
  [ "$status" -eq 0 ]
  [[ "$output" == *"[V-model pair freeze]"* ]]
  [[ "$output" == *"rollback stale revisions (dry-run):"* ]]
}

@test "helix doctor --apply-patches dry-run output" {
  local stale_plan="$HELIX_ROOT/docs/plans/L9/L9-bats-apply-patches-temporaryplan.md"

  mkdir -p "$(dirname "$stale_plan")"
  trap 'rm -f "$stale_plan"' RETURN
  printf -- "---\nplan_id: L9-bats-apply-patches-temporaryplan\ntitle: temp\nrevised: 2000-01-01\nstatus: draft\n---\nbody\n" > "$stale_plan"

  run "$HELIX_ROOT/cli/helix" doctor --vmodel-pair-freeze-since-days 30 --apply-patches
  if [ "$status" -ne 0 ] || [[ "$output" != *"apply stale patches (dry-run):"* ]]; then
    echo "doctor status=$status" >&2
    printf '%s\n' "$output" >&2
  fi
  [ "$status" -eq 0 ]
  [[ "$output" == *"[V-model pair freeze]"* ]]
  [[ "$output" == *"stale (older than 30d):"* ]]
  [[ "$output" == *"apply stale patches (dry-run):"* ]]
}

@test "W58: helix doctor includes skill helix_layer audit section" {
  run "$HELIX_ROOT/cli/helix-doctor"
  [ "$status" -eq 0 ]
  [[ "$output" == *"[skill helix_layer audit]"* ]]
  [[ "$output" == *"check skill helix_layer:"* ]]
}
