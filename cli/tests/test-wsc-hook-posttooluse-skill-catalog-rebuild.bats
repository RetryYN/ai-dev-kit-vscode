#!/usr/bin/env bats

# DoD 検証: docs/v2/L7-test-design/whole-source-coverage-単体テスト設計.md UT-WSC-05

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  HOOK="$HELIX_ROOT/.claude/hooks/posttooluse-skill-catalog-rebuild.sh"
  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  mkdir -p "$PROJECT_ROOT/skills/common/demo" "$PROJECT_ROOT/.helix/cache/recommendations"
  printf '{}' >"$PROJECT_ROOT/.helix/cache/recommendations/stale.json"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

run_hook() {
  local payload="$1"
  shift
  env CLAUDE_PROJECT_DIR="$PROJECT_ROOT" "$@" /bin/bash "$HOOK" <<<"$payload"
}

wait_for_path() {
  local path="$1"
  for _ in $(seq 1 50); do
    [[ -e "$path" ]] && return 0
    sleep 0.1
  done
  return 1
}

@test "UT-WSC-05: SKILL.md 更新で cache を掃除して rebuild を起動する" {
  local marker="$TMP_ROOT/rebuilt"
  local log_file="$TMP_ROOT/rebuild.log"

  run run_hook '{"tool_name":"Write","tool_input":{"file_path":"skills/common/demo/SKILL.md"}}' \
    HELIX_SKILL_CATALOG_REBUILD_COMMAND="printf rebuilt > '$marker'" \
    HELIX_SKILL_CATALOG_REBUILD_LOG_FILE="$log_file" \
    HELIX_SKILL_CATALOG_REBUILD_DEBOUNCE_FILE="$TMP_ROOT/trigger.debounce"
  [ "$status" -eq 0 ]
  wait_for_path "$marker"
  [ ! -f "$PROJECT_ROOT/.helix/cache/recommendations/stale.json" ]
}

@test "UT-WSC-05: debounce 期間内の連続更新は 2 回目を skip する" {
  local log_file="$TMP_ROOT/debounce.log"
  local debounce_file="$TMP_ROOT/debounce.state"

  run run_hook '{"tool_name":"Edit","tool_input":{"file_path":"skills/common/demo/SKILL.md"}}' \
    HELIX_SKILL_CATALOG_REBUILD_COMMAND="printf run >> '$log_file'" \
    HELIX_SKILL_CATALOG_REBUILD_DEBOUNCE_FILE="$debounce_file"
  [ "$status" -eq 0 ]
  wait_for_path "$log_file"

  run run_hook '{"tool_name":"Edit","tool_input":{"file_path":"skills/common/demo/SKILL.md"}}' \
    HELIX_SKILL_CATALOG_REBUILD_COMMAND="printf run >> '$log_file'" \
    HELIX_SKILL_CATALOG_REBUILD_DEBOUNCE_FILE="$debounce_file"
  [ "$status" -eq 0 ]
  sleep 0.2

  run bash -lc "wc -c < '$log_file' | tr -d ' '"
  [ "$status" -eq 0 ]
  [ "$output" -eq 3 ]
}

@test "UT-WSC-05: SKILL.md 以外の更新では rebuild しない" {
  local marker="$TMP_ROOT/should-not-run"

  run run_hook '{"tool_name":"Write","tool_input":{"file_path":"README.md"}}' \
    HELIX_SKILL_CATALOG_REBUILD_COMMAND="printf rebuilt > '$marker'"
  [ "$status" -eq 0 ]
  sleep 0.2
  [ ! -e "$marker" ]
}
