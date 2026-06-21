#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  HOOK="$HELIX_ROOT/.claude/hooks/posttooluse-code-catalog-register.sh"

  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  mkdir -p "$PROJECT_ROOT/cli/lib/tests" "$PROJECT_ROOT/cli/config" "$PROJECT_ROOT/docs"

  git -C "$PROJECT_ROOT" init >/dev/null 2>&1
  git -C "$PROJECT_ROOT" config user.email qa@example.com
  git -C "$PROJECT_ROOT" config user.name QA

  cat >"$PROJECT_ROOT/cli/lib/foo.py" <<'EOF'
# @helix:index id=hook.foo domain=cli/lib summary=hook foo
def foo():
    return "ok"
EOF
  cat >"$PROJECT_ROOT/cli/lib/tests/test_x.py" <<'EOF'
def test_x():
    assert True
EOF
  printf '# docs\n' >"$PROJECT_ROOT/docs/x.md"
  printf '# readme\n' >"$PROJECT_ROOT/README.md"
  printf 'entries: []\n' >"$PROJECT_ROOT/cli/config/functional-registry.yaml"

  git -C "$PROJECT_ROOT" add cli/lib/foo.py cli/lib/tests/test_x.py docs/x.md README.md cli/config/functional-registry.yaml
  git -C "$PROJECT_ROOT" commit -m init >/dev/null 2>&1
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

payload_for() {
  local path="$1"
  printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$path"
}

json_field() {
  local payload="$1"
  local field="$2"
  python3 - "$payload" "$field" <<'PY'
import json
import sys

value = json.loads(sys.argv[1])
for part in sys.argv[2].split("."):
    value = value.get(part, "") if isinstance(value, dict) else ""
print(value if not isinstance(value, (dict, list)) else json.dumps(value, ensure_ascii=False))
PY
}

run_hook() {
  local payload="$1"
  shift
  if [[ -n "$payload" ]]; then
    env CLAUDE_PROJECT_DIR="$PROJECT_ROOT" "$@" /bin/bash "$HOOK" <<<"$payload"
    return
  fi
  env CLAUDE_PROJECT_DIR="$PROJECT_ROOT" "$@" /bin/bash "$HOOK" </dev/null
}

run_hook_at() {
  local hook_path="$1"
  local payload="$2"
  shift 2
  if [[ -n "$payload" ]]; then
    env CLAUDE_PROJECT_DIR="$PROJECT_ROOT" "$@" /bin/bash "$hook_path" <<<"$payload"
    return
  fi
  env CLAUDE_PROJECT_DIR="$PROJECT_ROOT" "$@" /bin/bash "$hook_path" </dev/null
}

@test "payload から file_path を抽出して cli/lib/foo.py で発火する" {
  run run_hook "$(payload_for "cli/lib/foo.py")"
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "continue" ]
  [[ "$(json_field "$output" "systemMessage")" == *"cli/lib/foo.py"* ]]
  [[ "$(json_field "$output" "systemMessage")" == *"functional-registry"* ]]
  [ -f "$PROJECT_ROOT/.helix/cache/code-catalog.jsonl" ]
}

@test "非対象 path は skip する" {
  for path in "cli/lib/tests/test_x.py" "docs/x.md" "README.md"; do
    run run_hook "$(payload_for "$path")"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
  done
}

@test "不正 payload でも fail-open continue を返す" {
  run run_hook '{"tool_name":"Write","tool_input":'
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "continue" ]
  [[ "$(json_field "$output" "systemMessage")" == *"invalid payload"* ]]
}

@test "空 stdin でも fail-open continue を返す" {
  run run_hook ""
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "continue" ]
  [[ "$(json_field "$output" "systemMessage")" == *"empty payload"* ]]
}

@test "再入 guard があると skip して continue を返す" {
  run env HELIX_HOOK_RUNNING="posttooluse-code-catalog-register" CLAUDE_PROJECT_DIR="$PROJECT_ROOT" /bin/bash "$HOOK" <<<"$(payload_for "cli/lib/foo.py")"
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "continue" ]
  [[ "$(json_field "$output" "systemMessage")" == *"reentry guard"* ]]
}

@test "再入 guard は部分一致ではなく exact match だけで発火する" {
  run env HELIX_HOOK_RUNNING="prefix-posttooluse-code-catalog-register-suffix" CLAUDE_PROJECT_DIR="$PROJECT_ROOT" /bin/bash "$HOOK" <<<"$(payload_for "cli/lib/foo.py")"
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "continue" ]
  [[ "$(json_field "$output" "systemMessage")" == *"code_catalog updated: cli/lib/foo.py"* ]]
  [[ "$(json_field "$output" "systemMessage")" != *"reentry guard"* ]]
}

@test "import 失敗でも fail-open continue を返す" {
  local copied_hook_dir="$PROJECT_ROOT/.claude/hooks"
  mkdir -p "$copied_hook_dir"
  cp "$HOOK" "$copied_hook_dir/posttooluse-code-catalog-register.sh"

  run run_hook_at "$copied_hook_dir/posttooluse-code-catalog-register.sh" "$(payload_for "cli/lib/foo.py")"
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "continue" ]
  [[ "$(json_field "$output" "systemMessage")" == *"code catalog register failed"* ]]
}

@test "jsonl 更新失敗でも fail-open continue を返す" {
  mkdir -p "$PROJECT_ROOT/.helix"
  printf 'conflict\n' >"$PROJECT_ROOT/.helix/cache"

  run run_hook "$(payload_for "cli/lib/foo.py")"
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "continue" ]
  [[ "$(json_field "$output" "systemMessage")" == *"code catalog register failed"* ]]
}

@test "DB 更新失敗でも fail-open continue を返す" {
  mkdir -p "$PROJECT_ROOT/.helix/helix.db"

  run run_hook "$(payload_for "cli/lib/foo.py")"
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "continue" ]
  [[ "$(json_field "$output" "systemMessage")" == *"code catalog register failed"* ]]
}
