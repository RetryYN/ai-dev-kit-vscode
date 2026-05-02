#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"

  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/cli/lib" "$HOME_DIR"
  cp "$HELIX_ROOT/cli/lib/skill_catalog.py" "$PROJECT_ROOT/cli/lib/skill_catalog.py"

  cd "$PROJECT_ROOT"
  git init >/dev/null 2>&1
  git add cli/lib/skill_catalog.py

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

build_code_index() {
  "$HELIX_ROOT/cli/helix" code build
}

@test "helix code --help displays usage" {
  run "$HELIX_ROOT/cli/helix" code --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"使い方: helix code <subcommand>"* ]]
  [[ "$output" == *"build"* ]]
  [[ "$output" == *"list"* ]]
  [[ "$output" == *"show"* ]]
}

@test "helix code build generates JSONL and syncs DB" {
  run build_code_index
  [ "$status" -eq 0 ]
  [[ "$output" == *"entry_count:"* ]]
  run python3 -c 'import re,sys; m=re.search(r"entry_count: ([0-9]+)", sys.stdin.read()); raise SystemExit(0 if m and int(m.group(1)) > 0 else 1)' <<<"$output"
  [ "$status" -eq 0 ]
  [ -f "$PROJECT_ROOT/.helix/cache/code-catalog.jsonl" ]
  [ -f "$PROJECT_ROOT/.helix/helix.db" ]

  run python3 - "$PROJECT_ROOT/.helix/helix.db" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
count = conn.execute("SELECT COUNT(*) FROM code_index").fetchone()[0]
raise SystemExit(0 if count > 0 else 1)
PY
  [ "$status" -eq 0 ]
}

@test "helix code list includes seed metadata id" {
  build_code_index >/dev/null

  run "$HELIX_ROOT/cli/helix" code list
  [ "$status" -eq 0 ]
  [[ "$output" == *"skill-catalog.strip-quotes"* ]]
}

@test "helix code show seed id displays path and line" {
  build_code_index >/dev/null

  run "$HELIX_ROOT/cli/helix" code show skill-catalog.strip-quotes
  [ "$status" -eq 0 ]
  [[ "$output" == *"id: skill-catalog.strip-quotes"* ]]
  [[ "$output" == *"location: cli/lib/skill_catalog.py:"* ]]
}

@test "helix code stats by domain includes cli lib seed metadata" {
  build_code_index >/dev/null

  run "$HELIX_ROOT/cli/helix" code stats --by domain
  [ "$status" -eq 0 ]
  [[ "$output" == *$'cli/lib\t'* ]]
}

@test "helix code dup threshold zero exits zero for cli lib domain" {
  build_code_index >/dev/null

  run "$HELIX_ROOT/cli/helix" code dup --threshold 0.0 --domain cli/lib
  [ "$status" -eq 0 ]
  if [[ -n "$output" ]]; then
    [[ "$output" == *"cli/lib"* ]]
  fi
}

@test "helix code find returns cached result without calling Codex" {
  build_code_index >/dev/null
  mkdir -p "$PROJECT_ROOT/.helix/cache/recommendations/code"
  python3 - "$PROJECT_ROOT" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

project_root = Path(sys.argv[1])
payload = {"query": "frontmatter parser", "n": 1}
raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
cache_key = hashlib.sha256(raw.encode("utf-8")).hexdigest()
cache_path = project_root / ".helix" / "cache" / "recommendations" / "code" / f"{cache_key}.json"
cache_path.write_text(
    json.dumps(
        [
            {
                "id": "skill-catalog.strip-quotes",
                "score": 0.99,
                "reason": "cache hit test",
            }
        ],
        ensure_ascii=False,
    )
    + "\n",
    encoding="utf-8",
)
PY

  run env HELIX_CODEX=/bin/false "$HELIX_ROOT/cli/helix" code find "frontmatter parser" -n 1
  [ "$status" -eq 0 ]
  [[ "$output" == *"skill-catalog.strip-quotes  cli/lib  cli/lib/skill_catalog.py:"* ]]
  [[ "$output" == *"0.99  cache hit test"* ]]
}
