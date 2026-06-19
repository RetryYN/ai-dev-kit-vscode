#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"

  TOOL_ROOT="$TMP_ROOT/tool"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  BIN_DIR="$TMP_ROOT/bin"
  GH_LOG="$TMP_ROOT/gh.log"
  PR_GATE_LOG="$TMP_ROOT/push-gate.log"

  mkdir -p "$TOOL_ROOT" "$PROJECT_ROOT" "$HOME_DIR" "$BIN_DIR"
  cp -R "$HELIX_ROOT/cli" "$TOOL_ROOT/cli"

  export HELIX_HOME="$TOOL_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export HELIX_DISABLE_FEEDBACK=1
  export GH_LOG PR_GATE_LOG
  export PATH="$BIN_DIR:/usr/bin:/bin"

  init_git_project
  write_mock_gh
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

init_git_project() {
  git init -q "$PROJECT_ROOT"
  git -C "$PROJECT_ROOT" config user.email "qa@example.com"
  git -C "$PROJECT_ROOT" config user.name "QA"
  echo "base" > "$PROJECT_ROOT/README.md"
  git -C "$PROJECT_ROOT" add README.md
  git -C "$PROJECT_ROOT" commit -q -m "feat: base"
  git -C "$PROJECT_ROOT" branch -M main
  git -C "$PROJECT_ROOT" checkout -q -b feature/pr-gate
  echo "change" >> "$PROJECT_ROOT/README.md"
  git -C "$PROJECT_ROOT" add README.md
  git -C "$PROJECT_ROOT" commit -q -m "feat: add pr gate"
  mkdir -p "$PROJECT_ROOT/.helix"
}

write_mock_gh() {
  cat > "$BIN_DIR/gh" <<'EOF'
#!/usr/bin/env bash
echo "$*" >> "$GH_LOG"
exit 0
EOF
  chmod +x "$BIN_DIR/gh"
}

write_push_gate_module() {
  local mode="$1"
  mkdir -p "$TOOL_ROOT/cli/lib"
  cat > "$TOOL_ROOT/cli/lib/push_gate.py" <<EOF
from pathlib import Path
import os


def run_all_gates():
    log_path = Path(os.environ["PR_GATE_LOG"])
    gates = ["gate-1", "gate-2", "gate-3", "gate-4", "gate-5", "gate-6"]
    log_path.write_text("\\n".join(gates) + "\\n", encoding="utf-8")
    return ${mode}
EOF
}

@test "test_pr_gate_runs_all_6_gates" {
  write_push_gate_module 0

  run "$TOOL_ROOT/cli/helix-pr" --gate

  [ "$status" -eq 0 ]
  [ "$(wc -l < "$PR_GATE_LOG")" -eq 6 ]
  grep -q "pr create" "$GH_LOG"
}

@test "test_pr_gate_dry_run_skips_pr_create" {
  write_push_gate_module 0

  run "$TOOL_ROOT/cli/helix-pr" --gate --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"PR creation skipped"* ]]
  [ ! -f "$GH_LOG" ]
}

@test "test_pr_auto_merge_requires_gate" {
  run "$TOOL_ROOT/cli/helix-pr" --auto-merge

  [ "$status" -eq 2 ]
  [[ "$output" == *"--auto-merge requires --gate"* ]]
}

## ST-IF-03
@test "test_pr_gate_blocks_on_test_fail" {
  write_push_gate_module 1

  run "$TOOL_ROOT/cli/helix-pr" --gate

  [ "$status" -eq 1 ]
  [[ "$output" == *"Error: gate validation failed"* ]]
  [ ! -f "$GH_LOG" ]
}
