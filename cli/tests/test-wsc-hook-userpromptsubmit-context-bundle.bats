#!/usr/bin/env bats

# DoD 検証: docs/v2/L7-test-design/whole-source-coverage-単体テスト設計.md UT-WSC-17

json_field() {
  local json_text="$1"
  local field_name="$2"
  JSON_TEXT="$json_text" FIELD_NAME="$field_name" python3 - <<'PY'
import json
import os

value = json.loads(os.environ["JSON_TEXT"])
for segment in os.environ["FIELD_NAME"].split("."):
    value = value[segment]
print(value)
PY
}

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  HOOK="$HELIX_ROOT/.claude/hooks/userpromptsubmit-context-bundle.sh"
  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/.helix/handover" "$PROJECT_ROOT/docs/plans" "$HOME_DIR/.claude"
  export HOME="$HOME_DIR"
  cat >"$PROJECT_ROOT/.helix/handover/CURRENT.md" <<'EOF'
## Next Action (Codex 向け)
1. carry を閉じる
2. next action を確認する
EOF
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

run_hook() {
  local payload="$1"
  shift
  env CLAUDE_PROJECT_DIR="$PROJECT_ROOT" HOME="$HOME_DIR" "$@" /bin/bash "$HOOK" <<<"$payload"
}

project_memory_dir() {
  python3 - "$PROJECT_ROOT" "$HOME_DIR" <<'PY'
from pathlib import Path
import sys
project_root = Path(sys.argv[1]).resolve()
home_dir = Path(sys.argv[2])
slug = "-" + str(project_root).strip("/").replace("/", "-")
print(home_dir / ".claude" / "projects" / slug / "memory")
PY
}

@test "UT-WSC-17: keyword match かつ PLAN 不在でも handover/memory bundle を返す" {
  local memory_dir
  memory_dir="$(project_memory_dir)"
  mkdir -p "$memory_dir"
  cat >"$memory_dir/feedback_latest.md" <<'EOF'
# feedback
resume するときは handover を読む
EOF

  run run_hook '{"hook_event_name":"UserPromptSubmit","prompt":"carry を確認して継続したい"}'
  [ "$status" -eq 0 ]
  bundle="$(json_field "$output" "hookSpecificOutput.additionalContext")"
  [[ "$bundle" == *"HELIX Prompt Bundle"* ]]
  [[ "$bundle" == *"handover"* ]]
  [[ "$bundle" == *"feedback_latest"* ]]
  [[ "$bundle" != *"plan:"* ]]
}

@test "UT-WSC-17: keyword 非該当なら additionalContext は空になる" {
  run run_hook '{"hook_event_name":"UserPromptSubmit","prompt":"通常の雑談です"}'
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "hookSpecificOutput.additionalContext")" = "" ]
}

@test "UT-WSC-17: feedback は新しい 2 件だけを bundle に含める" {
  local memory_dir
  memory_dir="$(project_memory_dir)"
  mkdir -p "$memory_dir"
  cat >"$PROJECT_ROOT/docs/plans/PLAN-321-context.md" <<'EOF'
plan_id: PLAN-321
title: "PLAN-321: bundle"
EOF
  cat >"$memory_dir/feedback_old.md" <<'EOF'
# feedback
old note
EOF
  cat >"$memory_dir/feedback_mid.md" <<'EOF'
# feedback
mid note
EOF
  cat >"$memory_dir/feedback_new.md" <<'EOF'
# feedback
new note
EOF
  touch -d '2026-06-07 10:00:00' "$memory_dir/feedback_old.md"
  touch -d '2026-06-07 11:00:00' "$memory_dir/feedback_mid.md"
  touch -d '2026-06-07 12:00:00' "$memory_dir/feedback_new.md"

  run run_hook '{"hook_event_name":"UserPromptSubmit","prompt":"PLAN-321 を resume して carry を閉じる"}'
  [ "$status" -eq 0 ]
  bundle="$(json_field "$output" "hookSpecificOutput.additionalContext")"
  [[ "$bundle" == *"- plan: PLAN-321: PLAN-321: bundle"* ]]
  [[ "$bundle" == *"feedback_new"* ]]
  [[ "$bundle" == *"feedback_mid"* ]]
  [[ "$bundle" != *"feedback_old"* ]]
}
