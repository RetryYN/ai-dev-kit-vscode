#!/usr/bin/env bats

# DoD 検証: docs/v2/L7-test-design/whole-source-coverage-単体テスト設計.md UT-WSC-15

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  HOOK="$HELIX_ROOT/.claude/hooks/stop-recovery-update.sh"
  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  mkdir -p "$PROJECT_ROOT/.helix/recovery"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

write_current() {
  local status="$1"
  cat >"$PROJECT_ROOT/.helix/recovery/CURRENT.json" <<EOF
{
  "plan_id": "RECOVERY-001",
  "status": "$status",
  "started_at": "2026-06-07T12:00:00+09:00",
  "current_phase": "RP-2",
  "triggered_conditions": [],
  "reopen_point": null,
  "log_path": ".helix/recovery/recovery-log-RECOVERY-001.md",
  "forward_target": null,
  "warnings": []
}
EOF
}

@test "UT-WSC-15: active recovery なら snapshot と推奨メッセージを出す" {
  write_current "active"

  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" /bin/bash "$HOOK"
  [ "$status" -eq 0 ]
  [[ "$output" == *"状態を snapshot しました"* ]]
  [[ "$output" == *"/compact"* ]]
  run python3 - "$PROJECT_ROOT/.helix/recovery/CURRENT.json" <<'PY'
import json
import sys
payload = json.load(open(sys.argv[1], encoding="utf-8"))
assert payload["last_snapshot_at"]
PY
  [ "$status" -eq 0 ]
  grep -q 'stop-hook snapshot captured' "$PROJECT_ROOT/.helix/recovery/recovery-log-RECOVERY-001.md"
}

@test "UT-WSC-15: CURRENT.json 不在なら無出力で終了する" {
  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" /bin/bash "$HOOK"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "UT-WSC-15: active 以外の status は無出力で終了する" {
  write_current "completed"

  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" /bin/bash "$HOOK"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "UT-WSC-15: malformed CURRENT.json でも fail-open で終了する" {
  printf '{not-json' >"$PROJECT_ROOT/.helix/recovery/CURRENT.json"

  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" /bin/bash "$HOOK"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
