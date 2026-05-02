#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"

  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  mkdir -p "$PROJECT_ROOT"
  cd "$PROJECT_ROOT"

  git init -q
  git config user.email "test@example.com"
  git config user.name "Test User"
  echo "init" > README.md
  git add README.md
  git commit -q -m "init"

  mkdir -p .helix
  cat > .helix/phase.yaml <<'YAML'
project: handover-test
current_phase: L4
sprint:
  current_step: .2
  status: active
YAML

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

handover_dump() {
  "$HELIX_ROOT/cli/helix-handover" dump \
    --task-id T-001 \
    --task-title "test task" \
    --files "src/a.py,tests/test_a.py" \
    --pending "src/a.py,tests/test_a.py" \
    --tests "pytest tests/test_a.py -q"
}

@test "1 dump creates CURRENT.json and CURRENT.md" {
  run handover_dump
  [ "$status" -eq 0 ]
  [ -f "$PROJECT_ROOT/.helix/handover/CURRENT.json" ]
  [ -f "$PROJECT_ROOT/.helix/handover/CURRENT.md" ]
}

@test "2 dump reads phase and sprint from phase.yaml" {
  handover_dump
  run python3 - <<'PY'
import json
from pathlib import Path
p = Path('.helix/handover/CURRENT.json')
d = json.loads(p.read_text())
assert d['phase'] == 'L4', d
assert d['sprint'] == '.2', d
assert d['project'] == 'handover-test', d
PY
  [ "$status" -eq 0 ]
}

@test "3 dump stores git branch and full 40-char head_sha" {
  handover_dump
  run python3 - <<'PY'
import json
import re
import subprocess
from pathlib import Path
s = json.loads(Path('.helix/handover/CURRENT.json').read_text())
branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip()
sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
assert s['git']['branch'] == branch, s
assert s['git']['head_sha'] == sha, s
assert re.fullmatch(r'[0-9a-f]{40}', s['git']['head_sha']), s['git']['head_sha']
PY
  [ "$status" -eq 0 ]
}

@test "4 status --json returns structured payload" {
  handover_dump
  run "$HELIX_ROOT/cli/helix-handover" status --json
  [ "$status" -eq 0 ]
  run python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); assert d["exists"] and d["task"]["id"]=="T-001" and "stale" in d' <<<"$output"
  [ "$status" -eq 0 ]
}

@test "5 status without CURRENT returns exists false" {
  run "$HELIX_ROOT/cli/helix-handover" status --json
  [ "$status" -eq 0 ]
  run python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); assert d=={"exists":False}' <<<"$output"
  [ "$status" -eq 0 ]
}

@test "6 update status in_progress -> ready_for_review" {
  handover_dump
  run "$HELIX_ROOT/cli/helix-handover" update --status ready_for_review
  [ "$status" -eq 0 ]
  run python3 - <<'PY'
import json
from pathlib import Path
s = json.loads(Path('.helix/handover/CURRENT.json').read_text())
assert s['task']['status'] == 'ready_for_review', s
PY
  [ "$status" -eq 0 ]
}

@test "7 update --complete moves file pending -> completed" {
  handover_dump
  run "$HELIX_ROOT/cli/helix-handover" update --complete src/a.py --complete-note "done"
  [ "$status" -eq 0 ]
  run python3 - <<'PY'
import json
from pathlib import Path
s = json.loads(Path('.helix/handover/CURRENT.json').read_text())
assert 'src/a.py' not in s['files']['pending'], s
assert any(x['path']=='src/a.py' for x in s['files']['completed']), s
PY
  [ "$status" -eq 0 ]
}

@test "8 update --note appends timestamped event to CURRENT.md" {
  handover_dump
  run "$HELIX_ROOT/cli/helix-handover" update --note "memo"
  [ "$status" -eq 0 ]
  run grep -E "^### \[[^]]+\] note \(owner: opus\)$" "$PROJECT_ROOT/.helix/handover/CURRENT.md"
  [ "$status" -eq 0 ]
}

@test "9 update --blocker sets status blocked and logs blocker event" {
  handover_dump
  run "$HELIX_ROOT/cli/helix-handover" update --blocker "blocked now"
  [ "$status" -eq 0 ]
  run python3 - <<'PY'
import json
from pathlib import Path
s = json.loads(Path('.helix/handover/CURRENT.json').read_text())
assert s['task']['status'] == 'blocked', s
md = Path('.helix/handover/CURRENT.md').read_text()
assert 'blocker' in md and 'blocked now' in md
PY
  [ "$status" -eq 0 ]
}

@test "10 update --unblock returns blocked -> in_progress" {
  handover_dump
  "$HELIX_ROOT/cli/helix-handover" update --blocker "wait" >/dev/null
  run "$HELIX_ROOT/cli/helix-handover" update --unblock "fixed"
  [ "$status" -eq 0 ]
  run python3 - <<'PY'
import json
from pathlib import Path
s = json.loads(Path('.helix/handover/CURRENT.json').read_text())
assert s['task']['status'] == 'in_progress', s
assert 'unblock' in Path('.helix/handover/CURRENT.md').read_text()
PY
  [ "$status" -eq 0 ]
}

@test "11 update --owner codex writes owner_change event" {
  handover_dump
  run "$HELIX_ROOT/cli/helix-handover" update --owner codex
  [ "$status" -eq 0 ]
  run python3 - <<'PY'
import json
from pathlib import Path
s = json.loads(Path('.helix/handover/CURRENT.json').read_text())
assert s['owner'] == 'codex', s
assert 'owner_change' in Path('.helix/handover/CURRENT.md').read_text()
PY
  [ "$status" -eq 0 ]
}

@test "12 clear completed archives files when ready_for_review" {
  handover_dump
  "$HELIX_ROOT/cli/helix-handover" update --status ready_for_review >/dev/null
  run "$HELIX_ROOT/cli/helix-handover" clear --reason completed
  [ "$status" -eq 0 ]
  [ ! -f "$PROJECT_ROOT/.helix/handover/CURRENT.json" ]
  run bash -c 'ls .helix/handover/archive/*/CURRENT.json >/dev/null 2>&1'
  [ "$status" -eq 0 ]
}

@test "13 dump does not overwrite without --force" {
  handover_dump
  run "$HELIX_ROOT/cli/helix-handover" dump --task-id T-002 --task-title "other"
  [ "$status" -eq 1 ]
}

@test "14 invalid status transition is rejected" {
  handover_dump
  run "$HELIX_ROOT/cli/helix-handover" update --status in_progress
  [ "$status" -eq 1 ]
}

@test "15 clear completed is rejected unless status is ready_for_review" {
  handover_dump
  run "$HELIX_ROOT/cli/helix-handover" clear --reason completed
  [ "$status" -eq 1 ]
}

@test "16 clear abandoned requires --force" {
  handover_dump
  run "$HELIX_ROOT/cli/helix-handover" clear --reason abandoned
  [ "$status" -eq 2 ]
}

@test "17 revision conflict rejects update" {
  handover_dump
  (
    sleep 0.05
    python3 - <<'PY'
import json
from pathlib import Path
p = Path('.helix/handover/CURRENT.json')
d = json.loads(p.read_text())
d['revision'] += 1
p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
PY
  ) &
  run env HELIX_HANDOVER_TEST_SLEEP_SEC=0.2 "$HELIX_ROOT/cli/helix-handover" update --note "race"
  [ "$status" -eq 1 ]
  [[ "$output" =~ "revision conflict" ]]
}

@test "18 flock serializes concurrent updates" {
  handover_dump
  python3 - <<'PY' &
import fcntl
from pathlib import Path
p = Path('.helix/handover/.lock')
p.parent.mkdir(parents=True, exist_ok=True)
with p.open('a+') as fh:
    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
    import time
    time.sleep(0.2)
PY
  run "$HELIX_ROOT/cli/helix-handover" update --note "after lock"
  [ "$status" -eq 0 ]
}

@test "19 update --unblock rejected when not blocked" {
  handover_dump
  run "$HELIX_ROOT/cli/helix-handover" update --unblock "noop"
  [ "$status" -eq 1 ]
}

@test "20 dump fails when phase sprint is null and --sprint missing" {
  cat > .helix/phase.yaml <<'YAML'
project: handover-test
current_phase: L4
sprint:
  current_step: null
  status: active
YAML
  run "$HELIX_ROOT/cli/helix-handover" dump --task-id T-001 --task-title "test"
  [ "$status" -eq 2 ]
}

@test "21 stale branch mismatch" {
  handover_dump
  git checkout -q -b other
  run "$HELIX_ROOT/cli/helix-handover" status --json
  [ "$status" -eq 0 ]
  run python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); assert d["stale"] and "branch_mismatch" in d["stale_reasons"]' <<<"$output"
  [ "$status" -eq 0 ]
}

@test "22 stale when head_sha unreachable from recent log" {
  handover_dump
  python3 - <<'PY'
import json
from pathlib import Path
p = Path('.helix/handover/CURRENT.json')
d = json.loads(p.read_text())
d['git']['head_sha'] = '0'*40
p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
PY
  run "$HELIX_ROOT/cli/helix-handover" status --json
  [ "$status" -eq 0 ]
  run python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); assert "head_sha_unreachable" in d["stale_reasons"]' <<<"$output"
  [ "$status" -eq 0 ]
}

@test "23 stale when updated_at exceeds default 72h" {
  handover_dump
  python3 - <<'PY'
import json
from pathlib import Path
p = Path('.helix/handover/CURRENT.json')
d = json.loads(p.read_text())
d['updated_at'] = '2000-01-01T00:00:00+00:00'
p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
PY
  run "$HELIX_ROOT/cli/helix-handover" status --json
  [ "$status" -eq 0 ]
  run python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); assert "updated_at_expired" in d["stale_reasons"]' <<<"$output"
  [ "$status" -eq 0 ]
}

@test "24 stale includes multiple reasons" {
  handover_dump
  git checkout -q -b other
  python3 - <<'PY'
import json
from pathlib import Path
p = Path('.helix/handover/CURRENT.json')
d = json.loads(p.read_text())
d['git']['head_sha'] = '0'*40
d['updated_at'] = '2000-01-01T00:00:00+00:00'
p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
PY
  run "$HELIX_ROOT/cli/helix-handover" status --json
  [ "$status" -eq 0 ]
  run python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); rs=set(d["stale_reasons"]); assert {"branch_mismatch","head_sha_unreachable","updated_at_expired"}.issubset(rs)' <<<"$output"
  [ "$status" -eq 0 ]
}

@test "25 --no-check-stale disables stale detection" {
  handover_dump
  git checkout -q -b other
  run "$HELIX_ROOT/cli/helix-handover" status --json --no-check-stale
  [ "$status" -eq 0 ]
  run python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); assert d["stale"] is False and d["stale_reasons"]==[]' <<<"$output"
  [ "$status" -eq 0 ]
}

@test "26 HELIX_HANDOVER_STALE_HOURS overrides threshold" {
  handover_dump
  python3 - <<'PY'
import json
from pathlib import Path
p = Path('.helix/handover/CURRENT.json')
d = json.loads(p.read_text())
d['updated_at'] = '2026-01-01T00:00:00+00:00'
p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
PY
  run env HELIX_HANDOVER_STALE_HOURS=24 "$HELIX_ROOT/cli/helix-handover" status --json
  [ "$status" -eq 0 ]
  run python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); assert "updated_at_expired" in d["stale_reasons"]' <<<"$output"
  [ "$status" -eq 0 ]
}

@test "27 escalate generates ESCALATION.md" {
  handover_dump
  run "$HELIX_ROOT/cli/helix-handover" escalate --reason "need decision" --context "details"
  [ "$status" -eq 0 ]
  [ -f "$PROJECT_ROOT/.helix/handover/ESCALATION.md" ]
}

@test "28 escalate sets status escalated" {
  handover_dump
  "$HELIX_ROOT/cli/helix-handover" escalate --reason "need decision" --context "details" >/dev/null
  run python3 - <<'PY'
import json
from pathlib import Path
d = json.loads(Path('.helix/handover/CURRENT.json').read_text())
assert d['task']['status'] == 'escalated', d
PY
  [ "$status" -eq 0 ]
}

@test "29 ESCALATION.md contains reason/context/current snapshot" {
  handover_dump
  "$HELIX_ROOT/cli/helix-handover" escalate --reason "need decision" --context "details" >/dev/null
  run grep -q "need decision" "$PROJECT_ROOT/.helix/handover/ESCALATION.md"
  [ "$status" -eq 0 ]
  run grep -q "details" "$PROJECT_ROOT/.helix/handover/ESCALATION.md"
  [ "$status" -eq 0 ]
  run grep -q "## CURRENT snapshot" "$PROJECT_ROOT/.helix/handover/ESCALATION.md"
  [ "$status" -eq 0 ]
}

@test "30 clear --reason escalated succeeds after escalate" {
  handover_dump
  "$HELIX_ROOT/cli/helix-handover" escalate --reason "need decision" --context "details" >/dev/null
  run "$HELIX_ROOT/cli/helix-handover" clear --reason escalated
  [ "$status" -eq 0 ]
}

@test "31 handover subcommand is callable from main dispatcher" {
  run "$HELIX_ROOT/cli/helix" handover status --json
  [ "$status" -eq 0 ]
  run python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); assert "exists" in d' <<<"$output"
  [ "$status" -eq 0 ]
}

@test "32 helix test bats glob includes test-handover.bats" {
  run bash -c "ls '$HELIX_ROOT/cli/tests/'*.bats | grep -q 'test-handover.bats'"
  [ "$status" -eq 0 ]
  run grep -q '"$SCRIPT_DIR/tests/"\*.bats' "$HELIX_ROOT/cli/helix-test"
  [ "$status" -eq 0 ]
}

@test "33 head_sha is always full SHA-40" {
  handover_dump
  run python3 - <<'PY'
import json
import re
from pathlib import Path
sha = json.loads(Path('.helix/handover/CURRENT.json').read_text())['git']['head_sha']
assert re.fullmatch(r'[0-9a-f]{40}', sha), sha
PY
  [ "$status" -eq 0 ]
}

@test "34 owner enum rejects pm" {
  handover_dump
  run "$HELIX_ROOT/cli/helix-handover" update --owner pm
  [ "$status" -eq 2 ]
}

@test "35 update --status escalated is rejected" {
  handover_dump
  run "$HELIX_ROOT/cli/helix-handover" update --status escalated
  [ "$status" -eq 2 ]
}

@test "36 phase enum allows only L1-L11" {
  cat > .helix/phase.yaml <<'YAML'
project: handover-test
current_phase: R0
sprint:
  current_step: .2
  status: active
YAML
  run "$HELIX_ROOT/cli/helix-handover" dump --task-id T-001 --task-title "test"
  [ "$status" -eq 2 ]
}

@test "37 phase enum accepts L11" {
  cat > .helix/phase.yaml <<'YAML'
project: handover-test
current_phase: L11
sprint:
  current_step: .2
  status: active
YAML
  run "$HELIX_ROOT/cli/helix-handover" dump --task-id T-001 --task-title "test"
  [ "$status" -eq 0 ]
}
