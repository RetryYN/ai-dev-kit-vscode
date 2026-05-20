#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  HOOK="$HELIX_ROOT/.claude/hooks/posttooluse-plan-auto-register.sh"

  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  mkdir -p "$PROJECT_ROOT/docs/plans" "$PROJECT_ROOT/docs/adr"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

run_hook() {
  local payload="$1"
  shift
  env CLAUDE_PROJECT_DIR="$PROJECT_ROOT" "$@" bash "$HOOK" <<<"$payload"
}

write_doc() {
  local path="$1"
  local frontmatter="$2"
  mkdir -p "$(dirname "$path")"
  printf -- '---\n%s\n---\n\n# Body\n' "$frontmatter" >"$path"
}

payload_for() {
  local path="$1"
  printf '{"tool_name":"Write","tool_result":{"filePath":"%s"}}' "$path"
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

@test "PLAN.md Write 後に hook が plan_registry 登録メッセージを返す" {
  write_doc "$PROJECT_ROOT/docs/plans/PLAN-901-smoke.md" $'plan_id: PLAN-901\nkind: impl\nlayer: L4\nstatus: draft\ngenerates:\n  - artifact_path: cli/lib/example.py\n    artifact_type: python_module'

  run run_hook "$(payload_for "docs/plans/PLAN-901-smoke.md")"
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "continue" ]
  [[ "$(json_field "$output" "systemMessage")" == *"plan_registry 登録完了: PLAN-901"* ]]
}

@test "ADR-*.md Write 後も hook が発火する" {
  write_doc "$PROJECT_ROOT/docs/adr/ADR-901-smoke.md" $'plan_id: ADR-901\nkind: adr\nlayer: L2\nstatus: active'

  run run_hook "$(payload_for "docs/adr/ADR-901-smoke.md")"
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "continue" ]
  [[ "$(json_field "$output" "systemMessage")" == *"ADR-901"* ]]
}

@test "非対象 file は exit 0 pass-through する" {
  printf '# readme\n' >"$PROJECT_ROOT/README.md"

  run run_hook "$(payload_for "README.md")"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "python3 未インストール時も fail-open する" {
  mkdir -p "$TMP_ROOT/no-python"
  ln -sf /usr/bin/cat "$TMP_ROOT/no-python/cat"
  ln -sf /usr/bin/dirname "$TMP_ROOT/no-python/dirname"
  ln -sf /usr/bin/mktemp "$TMP_ROOT/no-python/mktemp"
  ln -sf /usr/bin/rm "$TMP_ROOT/no-python/rm"
  write_doc "$PROJECT_ROOT/docs/plans/PLAN-902-no-python.md" $'plan_id: PLAN-902\nkind: impl\nlayer: L4'

  run env PATH="$TMP_ROOT/no-python" CLAUDE_PROJECT_DIR="$PROJECT_ROOT" /bin/bash "$HOOK" <<<"$(payload_for "docs/plans/PLAN-902-no-python.md")"
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "continue" ]
  [[ "$(json_field "$output" "systemMessage")" == *"python3 not available"* ]]
}

@test "cycle 検出時は decision:block を返す" {
  write_doc "$PROJECT_ROOT/docs/plans/PLAN-A.md" $'plan_id: PLAN-A\nkind: impl\nlayer: L4\ndependencies:\n  requires:\n    - PLAN-B'
  write_doc "$PROJECT_ROOT/docs/plans/PLAN-B.md" $'plan_id: PLAN-B\nkind: impl\nlayer: L4\ndependencies:\n  requires:\n    - PLAN-A'

  run run_hook "$(payload_for "docs/plans/PLAN-B.md")"
  [ "$status" -eq 0 ]

  run run_hook "$(payload_for "docs/plans/PLAN-A.md")"
  [ "$status" -eq 2 ]
  [ "$(json_field "$output" "decision")" = "block" ]
  [[ "$(json_field "$output" "message")" == *"dependency cycle detected: PLAN-A → PLAN-B → PLAN-A"* ]]
}
