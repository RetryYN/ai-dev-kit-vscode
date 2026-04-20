#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export PATH="$HELIX_ROOT/cli:$PATH"
}

@test "helix-budget status exits 0" {
  run "$HELIX_ROOT/cli/helix-budget" status --no-cache
  [ "$status" -eq 0 ]
}

@test "helix-budget status --json emits valid JSON" {
  run bash -c "$HELIX_ROOT/cli/helix-budget status --json --no-cache | python3 -c 'import json,sys; d=json.load(sys.stdin); assert \"claude\" in d and \"codex\" in d'"
  [ "$status" -eq 0 ]
}

@test "helix-budget classify returns low/medium for trivial task" {
  run bash -c "$HELIX_ROOT/cli/helix-budget classify --task 'typo 修正' --size S --files 1 --json | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d[\"effort\"] in (\"low\",\"medium\"), d'"
  [ "$status" -eq 0 ]
}

@test "helix-budget classify returns high/xhigh for design task" {
  run bash -c "$HELIX_ROOT/cli/helix-budget classify --task '新規 API 設計 + DB migration + 複数モジュール' --role tl --size L --files 8 --json | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d[\"effort\"] in (\"high\",\"xhigh\"), d'"
  [ "$status" -eq 0 ]
}

@test "helix-budget simulate produces recommendation" {
  run "$HELIX_ROOT/cli/helix-budget" simulate --task 'API ハンドラ 3 本実装' --role se --size M
  [ "$status" -eq 0 ]
  [[ "$output" =~ "推奨モデル" ]]
}

@test "helix-budget cache status works" {
  run "$HELIX_ROOT/cli/helix-budget" cache status
  [ "$status" -eq 0 ]
}

@test "effort_classifier score boundary low→medium" {
  run python3 -c "
import sys
sys.path.insert(0, '$HELIX_ROOT/cli/lib')
from effort_classifier import map_to_effort
assert map_to_effort(3) == 'low'
assert map_to_effort(4) == 'medium'
assert map_to_effort(7) == 'medium'
assert map_to_effort(8) == 'high'
assert map_to_effort(12) == 'high'
assert map_to_effort(13) == 'xhigh'
print('OK')
"
  [ "$status" -eq 0 ]
  [[ "$output" =~ "OK" ]]
}

@test "model_fallback suggests same_tier for spark exhaustion" {
  run python3 -c "
import sys
sys.path.insert(0, '$HELIX_ROOT/cli/lib')
from model_fallback import suggest_model
budget = {'codex': {'weekly_used_pct': 95, 'by_model': {}}}
result = suggest_model('gpt-5.3-codex-spark', budget, effort='medium', size='M')
assert result['fallback_applied'], result
assert result['recommended_model'] in ('gpt-5.4-mini', 'gpt-5.3-codex'), result
print('OK')
"
  [ "$status" -eq 0 ]
  [[ "$output" =~ "OK" ]]
}

@test "model_fallback holds gpt-5.4" {
  run python3 -c "
import sys
sys.path.insert(0, '$HELIX_ROOT/cli/lib')
from model_fallback import suggest_model
budget = {'codex': {'weekly_used_pct': 98, 'by_model': {}}}
result = suggest_model('gpt-5.4', budget, effort='high', size='M')
assert not result['fallback_applied'], result
assert result['recommended_model'] == 'gpt-5.4', result
print('OK')
"
  [ "$status" -eq 0 ]
  [[ "$output" =~ "OK" ]]
}

@test "helix-budget --help exits 0" {
  run "$HELIX_ROOT/cli/helix-budget" --help
  [ "$status" -eq 0 ]
  [[ "$output" =~ "status" ]]
  [[ "$output" =~ "classify" ]]
}
