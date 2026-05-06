#!/usr/bin/env bash
# PLAN-023 Sprint .3 W-IT: 残課題 3 件統合 E2E テスト
#
# 検証項目 (AC-1〜AC-10):
# 1. 残課題 3 (policy 誤判定): IMPL_TASK_RE で false positive 解消
# 2. 残課題 2 (sessions 単位 hit_rate): helix.db v16 + sessions + session_id
# 3. 残課題 1 (effort prompt inject): _effort_prefix() が hint に inject

set -eu

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
TMPDIR="${TMPDIR:-/tmp}/helix-plan023-$$"
mkdir -p "$TMPDIR"
trap 'rm -rf "$TMPDIR"' EXIT

PASS=0
FAIL=0
log_pass() { echo "[PASS] $1"; PASS=$((PASS + 1)); }
log_fail() { echo "[FAIL] $1"; FAIL=$((FAIL + 1)); }

echo "=== PLAN-023 Sprint .3 W-IT: 残課題 3 件統合 E2E テスト ==="
echo ""

# ====================================================================
# 残課題 3: HELIX policy の research 誤判定解消
# ====================================================================

# Test 1: IMPL_TASK_RE が agent_policy_guard.py に存在
if grep -q "IMPL_TASK_RE" "$HELIX_HOME/cli/lib/agent_policy_guard.py"; then
    log_pass "Test 1: IMPL_TASK_RE 定義存在 (W-1)"
else
    log_fail "Test 1: IMPL_TASK_RE 未定義"
fi

# Test 2: 実装系 + research キーワード混在で pg 許可
result=$(python3 -c "
import sys
sys.path.insert(0, '$HELIX_HOME/cli/lib')
from agent_policy_guard import check_team_definition
import json
r = check_team_definition({'strategy': 'sequential', 'members': [{'role': 'pg', 'engine': 'codex', 'task': '以下のファイルを Read してから conf を編集して codex_thinking を追加'}]})
print(r['ok'])
")
if [[ "$result" == "True" ]]; then
    log_pass "Test 2: PLAN-022 W-P2-1a 再現タスク (実装系 + research 混在) で pg 許可"
else
    log_fail "Test 2: false positive 残存。result=$result"
fi

# Test 3: 純 research タスクは block 維持
result=$(python3 -c "
import sys
sys.path.insert(0, '$HELIX_HOME/cli/lib')
from agent_policy_guard import check_team_definition
r = check_team_definition({'strategy': 'sequential', 'members': [{'role': 'pg', 'engine': 'codex', 'task': 'React の最新 SDK を investigate して比較'}]})
print(r['ok'])
")
if [[ "$result" == "False" ]]; then
    log_pass "Test 3: 純 research タスクは block 維持 (回帰なし)"
else
    log_fail "Test 3: 純 research タスクが通過。回帰発生"
fi

# ====================================================================
# 残課題 2: sessions 単位の真 hit_rate 計測
# ====================================================================

# Test 4: helix.db v16 + sessions テーブル存在
test_dir="$TMPDIR/db-test"
mkdir -p "$test_dir/.helix"
python3 -c "
import sys
sys.path.insert(0, '$HELIX_HOME/cli/lib')
from helix_db import init_db
init_db('$test_dir/.helix/helix.db')
"
if sqlite3 "$test_dir/.helix/helix.db" ".schema sessions" 2>/dev/null | grep -q "id TEXT PRIMARY KEY"; then
    log_pass "Test 4: helix.db v16 sessions テーブル存在 (W-2a)"
else
    log_fail "Test 4: sessions テーブル未存在"
fi

# Test 5: skill_usage.session_id 列存在
if sqlite3 "$test_dir/.helix/helix.db" "PRAGMA table_info(skill_usage)" 2>/dev/null | grep -q "session_id"; then
    log_pass "Test 5: skill_usage.session_id 列存在 (W-2a)"
else
    log_fail "Test 5: session_id 列未追加"
fi

# Test 6: helix-session-start で UUID 生成 + sessions INSERT
PROJECT_ROOT="$test_dir" HELIX_PROJECT_ROOT="$test_dir" CLAUDE_SESSION_ID="plan023-test" \
    bash "$HELIX_HOME/cli/libexec/helix-session-start" > /dev/null 2>&1
inserted=$(sqlite3 "$test_dir/.helix/helix.db" "SELECT count(*) FROM sessions WHERE claude_session_id='plan023-test'" 2>/dev/null)
if [[ "$inserted" == "1" ]]; then
    log_pass "Test 6: helix-session-start で sessions INSERT 動作 (W-2b)"
else
    log_fail "Test 6: sessions INSERT 失敗 (count=$inserted)"
fi

# Test 7: HELIX_DISABLE_SESSIONS=1 で OFF
PROJECT_ROOT="$test_dir" HELIX_PROJECT_ROOT="$test_dir" HELIX_DISABLE_SESSIONS=1 CLAUDE_SESSION_ID="plan023-disabled" \
    bash "$HELIX_HOME/cli/libexec/helix-session-start" > /dev/null 2>&1
disabled_count=$(sqlite3 "$test_dir/.helix/helix.db" "SELECT count(*) FROM sessions WHERE claude_session_id='plan023-disabled'" 2>/dev/null)
if [[ "$disabled_count" == "0" ]]; then
    log_pass "Test 7: HELIX_DISABLE_SESSIONS=1 で OFF gate (W-2b)"
else
    log_fail "Test 7: OFF gate 効かず (count=$disabled_count)"
fi

# Test 8: stats() に hit_rate / active_sessions / total_sessions
output=$("$HELIX_HOME/cli/helix" skill stats --days 7 2>&1)
if echo "$output" | grep -q "hit_rate"; then
    log_pass "Test 8: helix skill stats が hit_rate を表示 (W-3c)"
else
    log_fail "Test 8: hit_rate 不出力"
fi

# ====================================================================
# 残課題 1: effort prompt inject (ADR-007 Option A)
# ====================================================================

# Test 9: _effort_prefix() 関数が存在
if grep -q "def _effort_prefix" "$HELIX_HOME/cli/lib/skill_dispatcher.py"; then
    log_pass "Test 9: _effort_prefix() 関数定義存在 (W-3a)"
else
    log_fail "Test 9: _effort_prefix() 未定義"
fi

# Test 10: effort 値別 prefix 生成 (high/medium/low/未定義)
result=$(python3 -c "
import sys
sys.path.insert(0, '$HELIX_HOME/cli/lib')
from skill_dispatcher import _effort_prefix
high = _effort_prefix('high')
medium = _effort_prefix('medium')
low = _effort_prefix('low')
empty = _effort_prefix('')
print('OK' if (
    'effort=high' in high and
    'effort=medium' in medium and
    'effort=low' in low and
    empty == ''
) else 'FAIL')
")
if [[ "$result" == "OK" ]]; then
    log_pass "Test 10: _effort_prefix() が effort 値別に prefix 生成 (W-3a)"
else
    log_fail "Test 10: prefix 生成が想定外"
fi

# Test 11: ADR-007 Status: Accepted
if grep -qE "^\*\*Status\*\*:.*Accepted" "$HELIX_HOME/docs/features/helix-effort-agent-adr/adr.md"; then
    log_pass "Test 11: ADR-007 Status: Accepted (W-4)"
else
    log_fail "Test 11: ADR-007 Status が Accepted でない"
fi

# Test 12: helix-codex env include に HELIX_SESSION_ID
if grep -q "HELIX_SESSION_ID" "$HELIX_HOME/cli/helix-codex"; then
    log_pass "Test 12: helix-codex env include に HELIX_SESSION_ID (W-2c)"
else
    log_fail "Test 12: env include に HELIX_SESSION_ID なし"
fi

# ====================================================================
# 回帰確認
# ====================================================================

# Test 13: PLAN-022 W-P1-2 helix-codex 動的 SKILL_PATHS 機能維持
if grep -q "PLAN-022 W-P1-2: 動的 skill 推挙" "$HELIX_HOME/cli/helix-codex"; then
    log_pass "Test 13: PLAN-022 W-P1-2 動的 SKILL_PATHS マージ機能維持"
else
    log_fail "Test 13: PLAN-022 機能が消失"
fi

# Test 14: PLAN-022 pg.conf codex_thinking=low 維持
if grep -q "^codex_thinking=low" "$HELIX_HOME/cli/roles/pg.conf"; then
    log_pass "Test 14: pg.conf codex_thinking=low 維持 (PLAN-022 W-P0-1)"
else
    log_fail "Test 14: pg.conf 退行"
fi

# Test 15: PLAN-022 全 20 ロール conf に codex_thinking
missing=$(grep -L "^codex_thinking=" "$HELIX_HOME"/cli/roles/*.conf || true)
if [[ -z "$missing" ]]; then
    log_pass "Test 15: 全 20 ロール conf に codex_thinking 設定済 (PLAN-022 W-P2-1)"
else
    log_fail "Test 15: codex_thinking 未設定: $missing"
fi

echo ""
echo "=== Result: $PASS passed / $FAIL failed ==="
[[ "$FAIL" -eq 0 ]] && exit 0 || exit 1
