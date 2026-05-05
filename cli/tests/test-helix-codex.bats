#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"

  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/docs" "$HOME_DIR"
  cat > "$PROJECT_ROOT/docs/ref.md" <<'DOC'
# Reference

WBS-017-001 .1a add core CLI bats coverage
DOC
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

@test "helix-codex help documents consent and approval guards" {
  run "$HELIX_ROOT/cli/helix-codex" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"--plan-only"* ]]
  [[ "$output" == *"--approved"* ]]
  [[ "$output" == *"HELIX_CODEX_REQUIRE_APPROVED"* ]]
  [[ "$output" == *"HELIX_CODEX_REQUIRE_APPROVAL_EVIDENCE"* ]]
}

@test "helix-codex rejects missing role or task" {
  run "$HELIX_ROOT/cli/helix-codex" --role docs --dry-run
  [ "$status" -ne 0 ]
  [[ "$output" == *"--role と --task は必須です"* ]]
}

@test "helix-codex rejects invalid role name before execution" {
  run "$HELIX_ROOT/cli/helix-codex" --role "bad/role" --task "x" --dry-run
  [ "$status" -ne 0 ]
  [[ "$output" == *"無効な --role 値"* ]]
}

@test "helix-codex plan-only dry-run forces read-only and disables full-auto" {
  run "$HELIX_ROOT/cli/helix-codex" --role docs --task "計画を整理して" --plan-only --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"plan-only guard: --consent plan-only -> sandbox=read-only, full-auto=off"* ]]
  [[ "$output" == *"Sandbox:   read-only"* ]]
  [[ "$output" == *"Full-Auto: off"* ]]
  [[ "$output" == *"Consent:   plan-only"* ]]
  [[ "$output" == *"Plan-Only: true (--consent plan-only)"* ]]
  [[ "$output" == *"plan_only_guard: true"* ]]
  [[ "$output" == *"sandbox: read-only"* ]]
}

@test "helix-codex dry-run injects HELIX execution context" {
  run "$HELIX_ROOT/cli/helix-codex" \
    --role docs \
    --task "実装して" \
    --approved \
    --dry-run \
    --plan-id PLAN-017 \
    --task-id TASK-017 \
    --wbs-id WBS-017-001 \
    --l4-sprint .1a \
    --reference-doc docs/ref.md \
    --acceptance "plan and codex bats pass" \
    --allowed-files "cli/tests/test-helix-*.bats"
  [ "$status" -eq 0 ]
  [[ "$output" == *"Consent:   approved"* ]]
  [[ "$output" == *"Plan ID:   PLAN-017"* ]]
  [[ "$output" == *"WBS ID:    WBS-017-001"* ]]
  [[ "$output" == *"L4 Sprint: .1a"* ]]
  [[ "$output" == *"plan_id: PLAN-017"* ]]
  [[ "$output" == *"task_id: TASK-017"* ]]
  [[ "$output" == *"wbs_id: WBS-017-001"* ]]
  [[ "$output" == *"l4_sprint: .1a"* ]]
  [[ "$output" == *"reference_docs:"* ]]
  [[ "$output" == *"docs/ref.md"* ]]
  [[ "$output" == *"plan and codex bats pass"* ]]
  [[ "$output" == *"allowed_files: cli/tests/test-helix-*.bats"* ]]
}

@test "helix-codex rejects missing reference doc" {
  run "$HELIX_ROOT/cli/helix-codex" --role docs --task "x" --dry-run --reference-doc docs/missing.md
  [ "$status" -ne 0 ]
  [[ "$output" == *"--reference-doc が見つかりません: docs/missing.md"* ]]
}

@test "helix-codex routes web research tasks to research role" {
  run "$HELIX_ROOT/cli/helix-codex" --role se --task "Web検索でSDKを調査" --dry-run
  [ "$status" -ne 0 ]
  [[ "$output" == *"HELIX agent policy に違反"* ]]
  [[ "$output" == *"research_task_wrong_role"* ]]
}

@test "helix-codex allows implementation code investigation wording" {
  run "$HELIX_ROOT/cli/helix-codex" --role se --task "影響範囲調査" --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"Role:      se"* ]]
}

@test "helix-codex require-approved blocks write execution without consent" {
  HELIX_CODEX_REQUIRE_APPROVED=1 run "$HELIX_ROOT/cli/helix-codex" --role docs --task "実装して"
  [ "$status" -ne 0 ]
  [[ "$output" == *"codex.require_approved=true"* ]]
  [[ "$output" == *"--approved または --consent approved"* ]]
}

@test "codex shim blocks raw exec when allow flag lacks reason" {
  HELIX_ALLOW_RAW_CODEX=1 run "$HELIX_ROOT/cli/codex" exec raw
  [ "$status" -eq 2 ]
  [[ "$output" == *"raw \`codex exec\` は HELIX discipline が効かないためブロックしました"* ]]
  [[ "$output" != *"unbound variable"* ]]
}

@test "claude shim blocks raw invocation when allow flag lacks reason" {
  HELIX_ALLOW_RAW_CLAUDE=1 run "$HELIX_ROOT/cli/claude" --print raw
  [ "$status" -eq 2 ]
  [[ "$output" == *"raw \`claude\` は HELIX discipline が効かないためブロックしました"* ]]
  [[ "$output" != *"unbound variable"* ]]
}

@test "claude shim allows explicit raw override with evidence" {
  mkdir -p "$TMP_ROOT/bin"
  cat > "$TMP_ROOT/bin/claude" <<'SH'
#!/bin/sh
printf 'real claude %s\n' "$*"
SH
  chmod +x "$TMP_ROOT/bin/claude"

  PATH="$HELIX_ROOT/cli:$TMP_ROOT/bin:$PATH" \
    HELIX_ALLOW_RAW_CLAUDE=1 \
    HELIX_RAW_CLAUDE_REASON=test-override \
    run "$HELIX_ROOT/cli/claude" --version

  [ "$status" -eq 0 ]
  [[ "$output" == "real claude --version" ]]
}
