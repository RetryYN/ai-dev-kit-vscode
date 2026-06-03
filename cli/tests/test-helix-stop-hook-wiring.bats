#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  mkdir -p "$PROJECT_ROOT/.claude"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

assert_status_zero() {
  if [[ "$status" -ne 0 ]]; then
    echo "command failed: status=${status} output=${output}" >&2
    exit 1
  fi
}

init_fixture_repo() {
  ln -s "$HELIX_ROOT/cli" "$PROJECT_ROOT/cli"
  git -C "$PROJECT_ROOT" init >/dev/null 2>&1
  git -C "$PROJECT_ROOT" config user.email qa@example.com
  git -C "$PROJECT_ROOT" config user.name QA
  printf 'seed\n' > "$PROJECT_ROOT/README.md"
  git -C "$PROJECT_ROOT" add README.md
  git -C "$PROJECT_ROOT" commit -m init >/dev/null 2>&1
}

dump_fixture_handover() {
  (
    cd "$PROJECT_ROOT" &&
      PYTHONPATH="$PROJECT_ROOT/cli/lib${PYTHONPATH:+:$PYTHONPATH}" python3 "$HELIX_ROOT/cli/lib/handover.py" \
        --handover-dir "$PROJECT_ROOT/.helix/handover" \
        --project-root "$PROJECT_ROOT" \
        dump \
        --task-id TASK-STOP \
        --task-title "Stop hook sync" \
        --phase L4 \
        --sprint .2 \
        --project helix-cli \
        --files cli/lib/handover.py >/dev/null
  )
}

@test "merge_settings generates both Stop hooks" {
  run python3 "$HELIX_ROOT/cli/lib/merge_settings.py" "$PROJECT_ROOT/.claude/settings.json"
  assert_status_zero

  run python3 - "$PROJECT_ROOT/.claude/settings.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    payload = json.load(fh)

commands = [entry["hooks"][0]["command"] for entry in payload["hooks"]["Stop"]]
assert len(commands) == 2, commands
assert commands[0].endswith("/cli/helix-session-summary"), commands
assert commands[1].endswith("/cli/helix-stop-hook"), commands
PY
  assert_status_zero
}

@test "helix-stop-hook updates CURRENT.json git head and revision" {
  init_fixture_repo
  dump_fixture_handover

  printf 'next\n' > "$PROJECT_ROOT/feature.txt"
  git -C "$PROJECT_ROOT" add feature.txt
  git -C "$PROJECT_ROOT" commit -m "advance head" >/dev/null 2>&1
  expected_head="$(git -C "$PROJECT_ROOT" rev-parse HEAD)"

  run env PYTHONPATH="$PROJECT_ROOT/cli/lib${PYTHONPATH:+:$PYTHONPATH}" "$PROJECT_ROOT/cli/helix-stop-hook"
  assert_status_zero

  run python3 - "$PROJECT_ROOT/.helix/handover/CURRENT.json" "$expected_head" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    payload = json.load(fh)

assert payload["git"]["head_sha"] == sys.argv[2], payload["git"]["head_sha"]
assert payload["revision"] == 2, payload["revision"]
PY
  assert_status_zero
}
