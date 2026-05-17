#!/usr/bin/env bats

# @helix:index id=plan084.dual-write-mismatch-smoke domain=cli/tests summary=dual-write mismatch gate smoke coverage

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  TMP_ROOT="$(mktemp -d)"
  ORIG_PWD="$PWD"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"

  TOOL_ROOT="$TMP_ROOT/tool"
  mkdir -p "$TOOL_ROOT/cli" "$TOOL_ROOT/scripts"
  cp -R "$HELIX_ROOT/cli/." "$TOOL_ROOT/cli/"
  cp "$HELIX_ROOT/scripts/check_dual_write_mismatch.sh" "$TOOL_ROOT/scripts/check_dual_write_mismatch.sh"
  chmod +x "$TOOL_ROOT/scripts/check_dual_write_mismatch.sh"
  cd "$TOOL_ROOT"
}

teardown() {
  cd "$ORIG_PWD"
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

write_mock_helper() {
  cat > "$TOOL_ROOT/mock_dual_write_mismatch.py" <<'PY'
import os


def run_ci_gate(*, scope: str, sample_size: int):
    mode = os.environ.get("HELIX_DUAL_WRITE_MISMATCH_MODE", "clean")
    payload = {
        "detected": False,
        "table_name": scope,
        "legacy_row_count": 1,
        "new_row_count": 1,
        "mismatch_keys": [],
        "detected_at": "2026-05-18T00:00:00Z",
        "severity": "warn",
        "sample_size": sample_size,
    }
    if mode == "critical":
        payload.update(
            {
                "detected": True,
                "new_row_count": 0,
                "mismatch_keys": ["slot-001"],
                "severity": "critical",
            }
        )
    return payload
PY
}

# DoD 検証: PLAN-084-integration-test-design.md I-DUALWRITE-001
@test "I-DUALWRITE-001: empty workspace fallback emits clean JSON and exits zero" {
  run "$TOOL_ROOT/scripts/check_dual_write_mismatch.sh" --scope cli --sample-size 25

  [ "$status" -eq 0 ]
  OUTPUT_JSON="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["OUTPUT_JSON"])
assert payload["detected"] is False
assert payload["table_name"] == "cli"
assert payload["severity"] == "warn"
assert payload["mismatch_keys"] == []
PY
}

# DoD 検証: PLAN-084-integration-test-design.md I-DUALWRITE-002
@test "I-DUALWRITE-002: critical mismatch mock triggers fail-close" {
  write_mock_helper

  run env \
    HELIX_DUAL_WRITE_MISMATCH_HELPER="$TOOL_ROOT/mock_dual_write_mismatch.py" \
    HELIX_DUAL_WRITE_MISMATCH_MODE=critical \
    "$TOOL_ROOT/scripts/check_dual_write_mismatch.sh" --scope cli --sample-size 7

  [ "$status" -eq 1 ]
  OUTPUT_JSON="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["OUTPUT_JSON"])
assert payload["detected"] is True
assert payload["severity"] == "critical"
assert payload["mismatch_keys"] == ["slot-001"]
PY
}

@test "I-DUALWRITE-003: carry until migration gates are ready" {
  skip "HELIX-SKIP: migration_pending | PLAN-084 | due_date: 2026-12-31"
}

@test "I-DUALWRITE-004: carry until migration gates are ready" {
  skip "HELIX-SKIP: migration_pending | PLAN-084 | due_date: 2026-12-31"
}

@test "I-DUALWRITE-005: carry until migration gates are ready" {
  skip "HELIX-SKIP: migration_pending | PLAN-084 | due_date: 2026-12-31"
}

@test "I-DUALWRITE-006: carry until migration gates are ready" {
  skip "HELIX-SKIP: migration_pending | PLAN-084 | due_date: 2026-12-31"
}

@test "I-DUALWRITE-007: carry until migration gates are ready" {
  skip "HELIX-SKIP: migration_pending | PLAN-084 | due_date: 2026-12-31"
}

@test "I-DUALWRITE-008: carry until migration gates are ready" {
  skip "HELIX-SKIP: migration_pending | PLAN-084 | due_date: 2026-12-31"
}
