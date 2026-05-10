#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR"
  cd "$PROJECT_ROOT"
  git init >/dev/null 2>&1
  git config user.email "t@t"
  git config user.name "T"
  echo "# test" > README.md
  git add . && git commit -q -m "init"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  "$HELIX_ROOT/cli/helix" init --project-name route >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "bench and test-debug commands are implemented" {
  run "$HELIX_ROOT/cli/helix" bench --json
  [ "$status" -eq 0 ]
  DASHBOARD_JSON="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["DASHBOARD_JSON"])
assert payload["project"] == "route", payload
PY

  run "$HELIX_ROOT/cli/helix" test-debug --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"HELIX_DEBUG=1"* ]]
}

@test "documented compatibility commands are routed" {
  export HELIX_SUPPRESS_LEGACY_WARN=1

  run "$HELIX_ROOT/cli/helix" gate-api-check --help
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix" hook --help
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix" check-claudemd --help
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix" session-start --help
  [ "$status" -eq 0 ]

  run env HELIX_PROJECT_ROOT="$HELIX_ROOT" "$HELIX_ROOT/cli/helix" context --json
  [ "$status" -eq 0 ]
  [[ "$output" == *'"ok": true'* ]]

  run "$HELIX_ROOT/cli/helix" claude --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"Claude Code 用"* ]]
}

@test "claude dry-run emits plan based prompt without API wording" {
  run "$HELIX_ROOT/cli/helix" claude --role pg --task "route test" --plan-id PLAN-ROUTE --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"helix-claude dry-run"* ]]
  [[ "$output" == *"plan_id: PLAN-ROUTE"* ]]
  [[ "$output" == *"Claude Code の契約プラン/CLI 利用"* ]]
  [[ "$output" != *"Claude API"* ]]
}

@test "top-level help and command index classify every routed command" {
  run "$HELIX_ROOT/cli/helix" help
  [ "$status" -eq 0 ]
  help_output="$output"
  index_file="$HELIX_ROOT/docs/commands/index.md"

  for category in \
    "HELIX 全体管理" \
    "HELIX プロジェクト管理" \
    "Codex / Claude Code 管理 harness" \
    "Reverse / Scrum / 検証" \
    "学習・再利用" \
    "補助・運用"; do
    [[ "$help_output" == *"$category"* ]]
    grep -q "$category" "$index_file"
  done

  for cmd in \
    init status dashboard mode doctor migrate commands setup test test-debug debug bench \
    size plan research meta-phase matrix gate gate-api-check readiness sprint task interrupt handover pr retro debt bats-cleanup drift-check \
    codex claude team review skill budget hook check-claudemd context session-start session-summary \
    reverse scrum verify-all verify-agent \
    log recipe learn promote discover builder code entry audit \
    scheduler job lock observe; do
    [[ "$help_output" == *"$cmd"* ]]
    grep -q "helix $cmd" "$index_file"
  done

  grep -q "reverse.md" "$index_file"
  grep -q "scrum.md" "$index_file"
  grep -q "入口判定" "$index_file"
  grep -q "Gate 判定" "$HELIX_ROOT/docs/commands/reverse.md"
  grep -q "Hypothesis 判定" "$HELIX_ROOT/docs/commands/scrum.md"
}

@test "active docs do not describe stale command names or API based harness assumptions" {
  run grep -rnE \
    "helix-codex --role|helix-codex review|codex review --uncommitted|Claude API|API key fallback|HELIX_ENABLE_CLAUDE_FALLBACK|CLI 未実装.*helix reverse rgc|OpenAI API 実応答|OpenAI API 障害|Anthropic API 障害|HTTPS → OpenAI API|HTTPS → Anthropic API|L1-L8|L1〜L8|G1-G7|G1〜G7|G2-G7|G2〜G7|G2-G6|G2〜G6|HELIX 9 フェーズ|v1 ?[-→>] ?v4|Status: Draft|ステータス: Draft|実装未着手|全 28|28 スキル|HELIX 独自 7|reverse-helix" \
    "$HELIX_ROOT/README.md" \
    "$HELIX_ROOT/CLAUDE.md" \
    "$HELIX_ROOT/AGENTS.md" \
    "$HELIX_ROOT/docs/commands" \
    "$HELIX_ROOT/docs/quickstart.md" \
    "$HELIX_ROOT/docs/security-guidelines.md" \
    "$HELIX_ROOT/docs/setup-guide.md" \
    "$HELIX_ROOT/cli/templates/AGENTS.md.template" \
    "$HELIX_ROOT/cli/templates/CLAUDE.md.template"
  [ "$status" -eq 1 ]
  [ -z "$output" ]
}

@test "framework validation covers docs links placeholders and deferred backlog" {
  run "$HELIX_ROOT/helix/validate.sh"
  [ "$status" -eq 1 ]
  [[ "$output" == *"HELIX Self-Validation"* ]]
  [[ "$output" == *"Skill Count"* ]]

  grep -q "DEF-DB-001" "$HELIX_ROOT/docs/backlog/intentional-deferred.md"
  grep -q "DEF-REC-001" "$HELIX_ROOT/docs/backlog/intentional-deferred.md"
}

@test "command help uses public helix command names" {
  export HELIX_SUPPRESS_LEGACY_WARN=1

  commands=$(
    awk '/^[[:space:]]+[a-zA-Z0-9_-]+\)/ {gsub(/[) ]/,"",$1); print $1}' "$HELIX_ROOT/cli/helix" | sort -u
  )

  for cmd in $commands; do
    run "$HELIX_ROOT/cli/helix" "$cmd" --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage:"* || "$output" == *"usage:"* || "$output" == *"使い方:"* ]]
    [[ "$output" != *"Usage: helix-"* ]]
    [[ "$output" != *"helix-codex --role"* ]]
    [[ "$output" != *"helix-size "* ]]
    [[ "$output" != *"helix-sprint "* ]]
    [[ "$output" != *"helix-pr "* ]]
    [[ "$output" != *"helix-reverse "* ]]
  done
}

@test "helix commands automates route help docs consistency" {
  run "$HELIX_ROOT/cli/helix" commands list --json
  [ "$status" -eq 0 ]
  COMMANDS_JSON="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["COMMANDS_JSON"])
names = {entry["name"] for entry in payload}
assert "commands" in names
assert "scheduler" in names
PY

  run "$HELIX_ROOT/cli/helix" commands check
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: command catalog is consistent"* ]]
}

@test "project agent instruction files are present and linked from docs" {
  for file in CLAUDE.md AGENTS.md; do
    [ -f "$HELIX_ROOT/$file" ]
    grep -q "HELIX" "$HELIX_ROOT/$file"
    grep -q "docs/commands/index.md" "$HELIX_ROOT/$file"
    grep -q "docs/commands/ai-harness.md" "$HELIX_ROOT/$file"
  done

  grep -q "CLAUDE.md" "$HELIX_ROOT/README.md"
  grep -q "AGENTS.md" "$HELIX_ROOT/README.md"
  grep -q "AGENTS.override.md" "$HELIX_ROOT/.gitignore"
  grep -q "指示ファイル" "$HELIX_ROOT/docs/commands/ai-harness.md"
  grep -q "Codex / Claude Code Harness" "$HELIX_ROOT/cli/templates/AGENTS.md.template"
  grep -q "指示ファイル" "$HELIX_ROOT/cli/templates/CLAUDE.md.template"
}

@test "helix init creates claude and codex instruction files from templates" {
  NEW_ROOT="$TMP_ROOT/init-project"
  mkdir -p "$NEW_ROOT"
  cd "$NEW_ROOT"
  git init >/dev/null 2>&1

  HELIX_PROJECT_ROOT="$NEW_ROOT" HELIX_SKIP_HOOK_INSTALL=1 "$HELIX_ROOT/cli/helix" init --project-name template-app >/dev/null

  [ -f "$NEW_ROOT/CLAUDE.md" ]
  [ -f "$NEW_ROOT/AGENTS.md" ]
  [ -f "$NEW_ROOT/.claude/settings.json" ]
  grep -q "# template-app" "$NEW_ROOT/CLAUDE.md"
  grep -q "# Codex CLI — template-app" "$NEW_ROOT/AGENTS.md"
  grep -q "helix-pre-bash" "$NEW_ROOT/.claude/settings.json"
  grep -q "AGENTS.override.md" "$NEW_ROOT/.gitignore"
  grep -q ".claude/agent-memory/" "$NEW_ROOT/.gitignore"
  grep -q "helix claude" "$NEW_ROOT/CLAUDE.md"
  grep -q "helix claude" "$NEW_ROOT/AGENTS.md"

  run env HELIX_PROJECT_ROOT="$NEW_ROOT" "$HELIX_ROOT/cli/helix" context --json
  [ "$status" -eq 0 ]
  [[ "$output" == *'"ok": true'* ]]
}

@test "helix init fails when existing claude settings is invalid" {
  NEW_ROOT="$TMP_ROOT/init-invalid-settings"
  mkdir -p "$NEW_ROOT/.claude"
  cd "$NEW_ROOT"
  git init >/dev/null 2>&1
  printf '{bad' > "$NEW_ROOT/.claude/settings.json"

  run env HELIX_PROJECT_ROOT="$NEW_ROOT" HELIX_SKIP_HOOK_INSTALL=1 \
    "$HELIX_ROOT/cli/helix" init --project-name invalid-settings

  [ "$status" -ne 0 ]
  [[ "$output" == *"設定マージに失敗"* ]]
}

@test "setup fails when user claude settings merge fails" {
  mkdir -p "$HOME/.claude"
  printf '{bad' > "$HOME/.claude/settings.json"

  run env HOME="$HOME" HELIX_HOME="$HELIX_ROOT" CODEX_BIN="" bash "$HELIX_ROOT/setup.sh"

  [ "$status" -ne 0 ]
  [[ "$output" == *"HELIX hooks merge failed"* ]]
  [[ "$output" == *"Setup completed with errors"* ]]
}

@test "setup uninstall fails when user claude settings removal fails" {
  mkdir -p "$HOME/.claude"
  printf '{bad' > "$HOME/.claude/settings.json"

  run env HOME="$HOME" HELIX_HOME="$HELIX_ROOT" CODEX_BIN="" bash "$HELIX_ROOT/setup.sh" --uninstall

  [ "$status" -ne 0 ]
  [[ "$output" == *"HELIX hooks removal failed"* ]]
  [[ "$output" == *"Setup completed with errors"* ]]
}

@test "management document templates are current and L3 schedule is generated" {
  grep -q "feature flag" "$HELIX_ROOT/cli/templates/docs/L3-schedule-wbs.md"
  grep -q "rollback" "$HELIX_ROOT/cli/templates/docs/L3-schedule-wbs.md"
  grep -q "Implementation Schedule" "$HELIX_ROOT/cli/templates/docs/PLAN.md.template"
  grep -q "Project Status" "$HELIX_ROOT/cli/templates/docs/project-status.md.template"
  grep -q "L3-schedule-wbs.md" "$HELIX_ROOT/docs/commands/plan.md"

  run "$HELIX_ROOT/cli/helix" size --files 8 --lines 240 --api --type new-feature --drive be
  [ "$status" -eq 0 ]
  [ -f "$PROJECT_ROOT/docs/design/L3-detailed-design.md" ]
  [ -f "$PROJECT_ROOT/docs/design/L3-schedule-wbs.md" ]
  grep -q "G3 チェック" "$PROJECT_ROOT/docs/design/L3-schedule-wbs.md"
}
