#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  BIN_DIR="$TMP_ROOT/bin"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR" "$BIN_DIR"

  cd "$PROJECT_ROOT"
  git init -q
  git config user.email "helix@example.test"
  git config user.name "HELIX Test"
  touch README.md
  git add README.md
  git commit -q -m "init"

  cat > "$BIN_DIR/fake-helix-codex" <<'SH'
#!/bin/sh
role=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --role)
      role="$2"
      shift 2
      ;;
    --task|--task-file|--timeout)
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done
if [ "$role" = "recommender" ]; then
  printf '{"recommendations":[{"skill_id":"common/testing","score":0.99,"reason":"test","recommended_agent":"pg","references":[]}]}\n'
  exit 0
fi
printf 'fake codex role=%s\n' "$role"
exit 0
SH
  chmod +x "$BIN_DIR/fake-helix-codex"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HELIX_SKILLS_ROOT="$HELIX_ROOT/skills"
  export HELIX_CODEX="$BIN_DIR/fake-helix-codex"
  export HELIX_CODEX_BIN="$BIN_DIR/fake-helix-codex"
  export HELIX_DISPATCH_TIMEOUT=5
  export HOME="$HOME_DIR"
  export PATH="$HELIX_ROOT/cli:$PATH"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

assert_evidence_entries() {
  python3 - "$PROJECT_ROOT/.helix/helix.db" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
count = conn.execute("SELECT COUNT(*) FROM entries WHERE axis = 'evidence'").fetchone()[0]
raise SystemExit(0 if count > 0 else 1)
PY
}

@test "PLAN-024 W-2d: helix skill chain records evidence entry" {
  run "$HELIX_ROOT/cli/helix" skill chain "test"
  [ "$status" -eq 0 ]

  run assert_evidence_entries
  [ "$status" -eq 0 ]
}

@test "PLAN-024 W-2d: helix skill use records evidence entry" {
  run "$HELIX_ROOT/cli/helix" skill use common/testing --task "test" --agent pg
  [ "$status" -eq 0 ]

  run assert_evidence_entries
  [ "$status" -eq 0 ]
}
