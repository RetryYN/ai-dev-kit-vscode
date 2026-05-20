#!/usr/bin/env bats

json_field() {
  local json_text="$1"
  local field_name="$2"
  JSON_TEXT="$json_text" FIELD_NAME="$field_name" python3 - <<'PY'
import json
import os

value = json.loads(os.environ["JSON_TEXT"])
for segment in os.environ["FIELD_NAME"].split("."):
    value = value[segment]
if isinstance(value, bool):
    print("true" if value else "false")
else:
    print(value)
PY
}

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"

  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  export CLAUDE_PROJECT_DIR="$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  mkdir -p "$PROJECT_ROOT/.helix/handover" "$PROJECT_ROOT/docs/plans" "$HOME_DIR/.claude"

  cat >"$PROJECT_ROOT/.helix/handover/CURRENT.md" <<'EOF'
## Next Action (Codex 向け)
1. PLAN-099 Sprint .3 Layer 4+5 を継続
2. bats smoke を回す

## イベントログ
EOF

  cat >"$PROJECT_ROOT/docs/plans/PLAN-099-autonomous-runtime-framework-5layer.md" <<'EOF'
plan_id: PLAN-099
title: "PLAN-099: 自動走行 framework 5-layer"
EOF

  local memory_dir="$HOME_DIR/.claude/projects/-${PROJECT_ROOT#/}/memory"
  mkdir -p "$memory_dir"
  cat >"$memory_dir/feedback_dont_stop_with_carry_remaining.md" <<'EOF'
# feedback
carry が残っているときに stop しない。
EOF
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

_make_scheduler_stub() {
  local bin_dir="$1"
  local handover_path="$2"
  local budget_path="$3"
  mkdir -p "$bin_dir"
  cat >"$bin_dir/helix" <<EOF
#!/bin/bash
set -euo pipefail
if [[ "\${1:-}" == "handover" && "\${2:-}" == "status" && "\${3:-}" == "--json" ]]; then
  cat "$handover_path"
  exit 0
fi
if [[ "\${1:-}" == "budget" && "\${2:-}" == "status" && "\${3:-}" == "--json" ]]; then
  cat "$budget_path"
  exit 0
fi
exit 2
EOF
  chmod +x "$bin_dir/helix"
}

@test "Layer 4 SessionStart cleared は bundle を注入し secret を redact する" {
  local transcript="$TMP_ROOT/transcript.jsonl"
  cat >"$transcript" <<'EOF'
{"prompt":"continue PLAN-099 api_key=sk-1234567890ABCDE","summary":"carry remaining"}
EOF

  local payload="$TMP_ROOT/sessionstart.json"
  cat >"$payload" <<EOF
{"hook_event_name":"SessionStart","source":"clear","transcript_path":"$transcript"}
EOF

  run env HELIX_SESSION_TYPE=cleared bash -lc "cat '$payload' | '$HELIX_ROOT/.claude/hooks/sessionstart-history-injection.sh'"
  [ "$status" -eq 0 ]
  [[ "$(json_field "$output" hookSpecificOutput.hookEventName)" == "SessionStart" ]]
  local bundle
  bundle="$(json_field "$output" hookSpecificOutput.additionalContext)"
  [[ "$bundle" == *"PLAN-099"* ]]
  [[ "$bundle" == *"handover"* ]]
  [[ "$bundle" == *"[REDACTED:api_key]"* ]]
}

@test "Layer 4 SessionStart new は bundle を空にする" {
  local payload="$TMP_ROOT/sessionstart-new.json"
  cat >"$payload" <<'EOF'
{"hook_event_name":"SessionStart","source":"startup"}
EOF

  run bash -lc "cat '$payload' | '$HELIX_ROOT/.claude/hooks/sessionstart-history-injection.sh'"
  [ "$status" -eq 0 ]
  [[ "$(json_field "$output" hookSpecificOutput.additionalContext)" == "" ]]
}

@test "Layer 4 UserPromptSubmit keyword match は 1500 文字以内の bundle を返す" {
  local payload="$TMP_ROOT/userprompt.json"
  cat >"$payload" <<'EOF'
{"hook_event_name":"UserPromptSubmit","prompt":"PLAN-099 の継続。handover と carry を確認して"}
EOF

  run bash -lc "cat '$payload' | '$HELIX_ROOT/.claude/hooks/userpromptsubmit-context-bundle.sh'"
  [ "$status" -eq 0 ]
  local bundle
  bundle="$(json_field "$output" hookSpecificOutput.additionalContext)"
  [[ "$bundle" == *"PLAN-099"* ]]
  [[ "$bundle" == *"carry"* || "$bundle" == *"handover"* ]]
  run env BUNDLE_TEXT="$bundle" bash -lc "printf '%s' \"\$BUNDLE_TEXT\" | wc -c | tr -d ' '"
  [ "$status" -eq 0 ]
  [[ "$output" -le 1500 ]]
}

@test "Layer 5 scheduler は healthy low critical で interval を切り替える" {
  local fake_bin="$TMP_ROOT/bin"
  local handover_json="$TMP_ROOT/handover.json"
  local budget_json="$TMP_ROOT/budget.json"
  printf '%s\n' '{"files":{"pending_count":2}}' >"$handover_json"
  printf '%s\n' '{"claude":{"weekly_remaining_pct":70},"codex":{"weekly_used_pct":20},"recommendations":[]}' >"$budget_json"
  _make_scheduler_stub "$fake_bin" "$handover_json" "$budget_json"

  run env PATH="$fake_bin:$PATH" HELIX_PROJECT_ROOT="$PROJECT_ROOT" "$HELIX_ROOT/cli/helix-heartbeat-scheduler" --json
  [ "$status" -eq 0 ]
  [[ "$(json_field "$output" budget_tier)" == "healthy" ]]
  [[ "$(json_field "$output" interval_minutes)" == "15" ]]

  printf '%s\n' '{"claude":{"weekly_remaining_pct":25},"codex":{"weekly_used_pct":20},"recommendations":[]}' >"$budget_json"
  run env PATH="$fake_bin:$PATH" HELIX_PROJECT_ROOT="$PROJECT_ROOT" "$HELIX_ROOT/cli/helix-heartbeat-scheduler" --json
  [ "$status" -eq 0 ]
  [[ "$(json_field "$output" budget_tier)" == "low" ]]
  [[ "$(json_field "$output" interval_minutes)" == "30" ]]

  printf '%s\n' '{"claude":{"weekly_remaining_pct":70},"codex":{"weekly_used_pct":20},"recommendations":[{"severity":"critical"}]}' >"$budget_json"
  run env PATH="$fake_bin:$PATH" HELIX_PROJECT_ROOT="$PROJECT_ROOT" "$HELIX_ROOT/cli/helix-heartbeat-scheduler" --json
  [ "$status" -eq 0 ]
  [[ "$(json_field "$output" budget_tier)" == "critical" ]]
  [[ "$(json_field "$output" interval_minutes)" == "5" ]]
}

@test "Layer 5 scheduler は carry なしまたは bg task active なら skip する" {
  local fake_bin="$TMP_ROOT/bin2"
  local handover_json="$TMP_ROOT/handover2.json"
  local budget_json="$TMP_ROOT/budget2.json"
  printf '%s\n' '{"files":{"pending_count":0}}' >"$handover_json"
  printf '%s\n' '{"claude":{"weekly_remaining_pct":70},"codex":{"weekly_used_pct":20},"recommendations":[]}' >"$budget_json"
  _make_scheduler_stub "$fake_bin" "$handover_json" "$budget_json"

  run env PATH="$fake_bin:$PATH" HELIX_PROJECT_ROOT="$PROJECT_ROOT" "$HELIX_ROOT/cli/helix-heartbeat-scheduler" --json
  [ "$status" -eq 0 ]
  [[ "$(json_field "$output" should_schedule)" == "false" ]]
  [[ "$(json_field "$output" next_action)" == "skip" ]]

  printf '%s\n' '{"files":{"pending_count":3}}' >"$handover_json"
  run env PATH="$fake_bin:$PATH" HELIX_PROJECT_ROOT="$PROJECT_ROOT" HELIX_BG_TASK_ACTIVE=1 "$HELIX_ROOT/cli/helix-heartbeat-scheduler" --json
  [ "$status" -eq 0 ]
  [[ "$(json_field "$output" bg_task_active)" == "true" ]]
  [[ "$(json_field "$output" should_schedule)" == "false" ]]
  [[ "$(json_field "$output" interval_minutes)" == "None" || "$(json_field "$output" interval_minutes)" == "null" ]]
}
