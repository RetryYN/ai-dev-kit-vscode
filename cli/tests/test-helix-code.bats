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

@test "helix code list --json outputs parseable json" {
  build_code_index >/dev/null

  run "$HELIX_ROOT/cli/helix" code list --json
  [ "$status" -eq 0 ]
  run python3 - <<'PY'
import json
import sys

payload = json.load(sys.stdin)
assert isinstance(payload, dict)
assert "entries" in payload
assert isinstance(payload["entries"], list)
PY
  [ "$status" -eq 0 ]
}

@test "helix code list --domain filters entries" {
  build_code_index >/dev/null

  run "$HELIX_ROOT/cli/helix" code list --domain cli/lib --json
  [ "$status" -eq 0 ]
  run python3 - <<'PY'
import json
import sys

payload = json.load(sys.stdin)
entries = payload.get("entries", [])
assert entries
assert all(item.get("domain") == "cli/lib" for item in entries)
PY
  [ "$status" -eq 0 ]
}

@test "helix code show unknown id returns error" {
  build_code_index >/dev/null

  run "$HELIX_ROOT/cli/helix" code show does-not-exist
  [ "$status" -eq 2 ]
  [[ "$output" == *"エラー: code index entry が見つかりません"* ]]
}

@test "helix code find requires query argument" {
  build_code_index >/dev/null

  run "$HELIX_ROOT/cli/helix" code find
  [ "$status" -eq 64 ]
  [[ "$output" == *"find には query が必要です"* ]]
}

@test "helix code stats --by since includes unknown bucket" {
  build_code_index >/dev/null

  run "$HELIX_ROOT/cli/helix" code stats --by since
  [ "$status" -eq 0 ]
  [[ "$output" == *$'unknown\t'* ]]
}

@test "helix code build self-hosts code_catalog.py with seed metadata" {
  cp "$HELIX_ROOT/cli/lib/code_catalog.py" "$PROJECT_ROOT/cli/lib/code_catalog.py"
  git add cli/lib/code_catalog.py >/dev/null 2>&1

  build_code_index >/dev/null

  run "$HELIX_ROOT/cli/helix" code list --domain cli/lib
  [ "$status" -eq 0 ]
  [[ "$output" == *"code-catalog.parse-helix-index-comment"* ]]
  [[ "$output" == *"code-catalog.scan-file"* ]]
  [[ "$output" == *"skill-catalog.strip-quotes"* ]]
}

@test "helix code dup detects identical summaries with default threshold" {
  cat > "$PROJECT_ROOT/cli/lib/dup_a.py" <<'PY'
# @helix:index id=dup.a domain=cli/lib summary=ファイル走査用ヘルパー実装
def a():
    return 1
PY
  cat > "$PROJECT_ROOT/cli/lib/dup_b.py" <<'PY'
# @helix:index id=dup.b domain=cli/lib summary=ファイル走査用ヘルパー実装
def b():
    return 2
PY
  git add cli/lib/dup_a.py cli/lib/dup_b.py >/dev/null 2>&1

  build_code_index >/dev/null

  run "$HELIX_ROOT/cli/helix" code dup --threshold 0.85 --domain cli/lib
  [ "$status" -eq 0 ]
  [[ "$output" == *"dup.a"* ]]
  [[ "$output" == *"dup.b"* ]]
}

@test "helix code build prunes stale entries on rescan" {
  build_code_index >/dev/null
  initial=$("$HELIX_ROOT/cli/helix" code list | wc -l)
  [ "$initial" -gt 0 ]

  rm "$PROJECT_ROOT/cli/lib/skill_catalog.py"
  git add -A cli/lib >/dev/null 2>&1

  build_code_index >/dev/null

  run "$HELIX_ROOT/cli/helix" code list
  [ "$status" -eq 0 ]
  [[ "$output" != *"skill-catalog.strip-quotes"* ]]
  after=$(wc -l <<<"$output")
  [ "$after" -lt "$initial" ]
}

@test "helix code build excludes markdown fixtures and string literals" {
  cat > "$PROJECT_ROOT/docs_example.md" <<'MD'
# 例

`# @helix:index id=docs.example domain=docs summary=ドキュメント例`
MD
  cat > "$PROJECT_ROOT/cli/lib/fixture_helper.py" <<'PY'
def f():
    return "# @helix:index id=fixture.in_string domain=cli/lib summary=文字列リテラル内"
PY
  git add docs_example.md cli/lib/fixture_helper.py >/dev/null 2>&1

  build_code_index >/dev/null

  run "$HELIX_ROOT/cli/helix" code list
  [ "$status" -eq 0 ]
  [[ "$output" != *"docs.example"* ]]
  [[ "$output" != *"fixture.in_string"* ]]
}

@test "helix code build fails closed on duplicate id" {
  cat > "$PROJECT_ROOT/cli/lib/dup_x.py" <<'PY'
# @helix:index id=duplicate.same domain=cli/lib summary=ヘルパーX実装
def x():
    return 1
PY
  cat > "$PROJECT_ROOT/cli/lib/dup_y.py" <<'PY'
# @helix:index id=duplicate.same domain=cli/lib summary=ヘルパーY実装
def y():
    return 2
PY
  git add cli/lib/dup_x.py cli/lib/dup_y.py >/dev/null 2>&1

  run "$HELIX_ROOT/cli/helix" code build
  [ "$status" -ne 0 ]
}
