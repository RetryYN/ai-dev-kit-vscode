#!/usr/bin/env bats
# PLAN-082 Phase 2: helix-agent fire-mandatory / suggest / audit subcommand 結合テスト
# 契約: helix/HELIX_CORE.md §工程別 subagent 起動マップ (PLAN-076 framework)

setup() {
  export HELIX_TMP="$(mktemp -d)"
  export HELIX_DB_PATH="$HELIX_TMP/test_helix.db"
  python3 -c "
import sqlite3
from cli.lib import helix_db
conn = sqlite3.connect('$HELIX_DB_PATH')
helix_db.migrate_all(conn)
conn.close()
"
}

teardown() {
  rm -rf "$HELIX_TMP"
}

@test "I-MAN-001: helix agent fire-mandatory --phase L2 --json returns 4 subagents" {
  run ./cli/helix-agent fire-mandatory --phase L2 --json
  [ "$status" -eq 0 ]
  count=$(printf '%s' "$output" | python3 -c 'import sys, json; print(len(json.load(sys.stdin)["subagents"]))')
  [ "$count" = "4" ]
}

@test "I-MAN-002: helix agent fire-mandatory --phase G2 returns pmo-sonnet only" {
  run ./cli/helix-agent fire-mandatory --phase G2 --json
  [ "$status" -eq 0 ]
  sub=$(printf '%s' "$output" | python3 -c 'import sys, json; d=json.load(sys.stdin); print(d["subagents"][0]["subagent"])')
  [ "$sub" = "pmo-sonnet" ]
}

@test "I-MAN-003: helix agent fire-mandatory unknown phase noop" {
  run ./cli/helix-agent fire-mandatory --phase L99 --json
  [ "$status" -eq 0 ]
  action=$(printf '%s' "$output" | python3 -c 'import sys, json; print(json.load(sys.stdin)["action"])')
  [ "$action" = "noop" ]
}

@test "I-MAN-004: helix agent fire-mandatory missing --phase fails" {
  run ./cli/helix-agent fire-mandatory --json
  [ "$status" -ne 0 ]
}

@test "I-MAN-005: helix agent suggest matches pmo-haiku for web keyword" {
  run ./cli/helix-agent suggest --task "Web 検索したい" --json
  [ "$status" -eq 0 ]
  first=$(printf '%s' "$output" | python3 -c 'import sys, json; d=json.load(sys.stdin); print(d[0]["subagent"] if d else "")')
  [ "$first" = "pmo-haiku" ]
}

@test "I-MAN-006: helix agent suggest matches tl-advisor for 契約" {
  run ./cli/helix-agent suggest --task "契約の判断が必要" --json
  [ "$status" -eq 0 ]
  matched=$(printf '%s' "$output" | python3 -c 'import sys, json; d=json.load(sys.stdin); print("tl-advisor" if any(r["subagent"]=="tl-advisor" for r in d) else "")')
  [ "$matched" = "tl-advisor" ]
}

@test "I-MAN-007: helix agent suggest empty match returns empty JSON list" {
  run ./cli/helix-agent suggest --task "zzz_no_match_xxx" --json
  [ "$status" -eq 0 ]
  count=$(printf '%s' "$output" | python3 -c 'import sys, json; print(len(json.load(sys.stdin)))')
  [ "$count" = "0" ]
}

@test "I-MAN-008: helix agent audit --phase L2 empty DB returns missing=4" {
  run ./cli/helix-agent audit --phase L2 --json
  [ "$status" -eq 0 ]
  # stderr に DeprecationWarning が出る、stdout の最終行が JSON
  json_line=$(printf '%s' "$output" | grep -v "DeprecationWarning\|datetime.datetime" | tail -1)
  missing=$(printf '%s' "$json_line" | python3 -c 'import sys, json; print(json.load(sys.stdin)["missing_count"])')
  [ "$missing" = "4" ]
}

@test "I-MAN-009: helix agent audit unknown phase returns missing=0" {
  run ./cli/helix-agent audit --phase L99 --json
  [ "$status" -eq 0 ]
  json_line=$(printf '%s' "$output" | grep -v "DeprecationWarning\|datetime.datetime" | tail -1)
  missing=$(printf '%s' "$json_line" | python3 -c 'import sys, json; print(json.load(sys.stdin)["missing_count"])')
  [ "$missing" = "0" ]
}

@test "I-MAN-010: helix agent audit missing --phase fails" {
  run ./cli/helix-agent audit --json
  [ "$status" -ne 0 ]
}
