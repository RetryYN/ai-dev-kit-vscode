#!/usr/bin/env bats

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  HOOK="$REPO_ROOT/.claude/hooks/posttooluse-skill-catalog-rebuild.sh"
  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  PAYLOAD_FILE="$TMP_ROOT/payload.json"
  CACHE_DIR="$PROJECT_ROOT/.helix/cache/recommendations"
  BIN_DIR="$TMP_ROOT/bin"
  HELIX_LOG="$TMP_ROOT/rebuild.log"
  DEBOUNCE_FILE="$TMP_ROOT/debounce.stamp"
  mkdir -p "$PROJECT_ROOT/skills/writing/demo" "$PROJECT_ROOT/docs" "$CACHE_DIR" "$BIN_DIR"

  cat >"$BIN_DIR/mock-rebuild" <<'EOF'
#!/usr/bin/env bash
set -eu
printf 'rebuild:%s\n' "$(date +%s)" >>"$HELIX_LOG"
EOF
  chmod +x "$BIN_DIR/mock-rebuild"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

payload_for() {
  local tool_name="$1"
  local path="$2"
  python3 - "$tool_name" "$path" <<'PY'
import json
import sys

tool_name, path = sys.argv[1], sys.argv[2]
print(
    json.dumps(
        {
            "tool_name": tool_name,
            "tool_input": {
                "file_path": path,
                "content": "# updated\n",
            },
        },
        ensure_ascii=False,
    )
)
PY
}

invoke_hook() {
  local payload="$1"
  shift
  printf '%s' "$payload" >"$PAYLOAD_FILE"
  env \
    CLAUDE_PROJECT_DIR="$PROJECT_ROOT" \
    HELIX_LOG="$HELIX_LOG" \
    HELIX_SKILL_CATALOG_REBUILD_CACHE_DIR="$CACHE_DIR" \
    HELIX_SKILL_CATALOG_REBUILD_DEBOUNCE_FILE="$DEBOUNCE_FILE" \
    HELIX_SKILL_CATALOG_REBUILD_COMMAND="$BIN_DIR/mock-rebuild" \
    PATH="$BIN_DIR:$PATH" \
    "$@" \
    bash "$HOOK" <"$PAYLOAD_FILE"
}

assert_rebuild_count() {
  local expected="$1"
  local count=0
  if [[ -f "$HELIX_LOG" ]]; then
    count="$(wc -l <"$HELIX_LOG" | tr -d ' ')"
  fi
  [ "$count" -eq "$expected" ]
}

@test "skills/*/*/SKILL.md の Write で rebuild を起動する" {
  payload="$(payload_for Write "$PROJECT_ROOT/skills/writing/demo/SKILL.md")"
  run invoke_hook "$payload"
  [ "$status" -eq 0 ]
  sleep 1
  assert_rebuild_count 1
}

@test "skills 配下でも SKILL.md 以外は skip する" {
  payload="$(payload_for Write "$PROJECT_ROOT/skills/writing/demo/README.md")"
  run invoke_hook "$payload"
  [ "$status" -eq 0 ]
  sleep 1
  assert_rebuild_count 0
}

@test "skills 外のファイルは skip する" {
  payload="$(payload_for Write "$PROJECT_ROOT/docs/guide.md")"
  run invoke_hook "$payload"
  [ "$status" -eq 0 ]
  sleep 1
  assert_rebuild_count 0
}

@test "30 秒以内の連続呼び出しは debounce される" {
  payload="$(payload_for Write "$PROJECT_ROOT/skills/writing/demo/SKILL.md")"
  run invoke_hook "$payload"
  [ "$status" -eq 0 ]
  run invoke_hook "$payload"
  [ "$status" -eq 0 ]
  sleep 1
  assert_rebuild_count 1
}

@test "rebuild 前に recommendations cache を invalidate する" {
  printf '{"stale":true}\n' >"$CACHE_DIR/skill-search.json"
  payload="$(payload_for MultiEdit "$PROJECT_ROOT/skills/writing/demo/SKILL.md")"
  run invoke_hook "$payload"
  [ "$status" -eq 0 ]
  sleep 1
  [ ! -e "$CACHE_DIR/skill-search.json" ]
  assert_rebuild_count 1
}
