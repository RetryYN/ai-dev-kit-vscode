#!/bin/bash
set -eo pipefail
# H203: CLAUDE.md テンプレート強制が正しく動くか

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"

echo "=== H203: CLAUDE.md Enforcement ==="

# テスト1: テンプレートなしで新規作成 → deny
input='{"tool_name":"Write","tool_input":{"file_path":"/tmp/nonexistent/CLAUDE.md","content":"# Random\nJust some text"}}'
set +e
out=$(echo "$input" | $CLI/helix-check-claudemd 2>&1)
set -e
echo "$out" | grep -q "deny\|テンプレート" || { echo "FAIL: should deny without template sections"; exit 1; }

# テスト2: テンプレート準拠で新規作成 → pass (no output)
input='{"tool_name":"Write","tool_input":{"file_path":"/tmp/nonexistent/CLAUDE.md","content":"# App\n## 技術スタック\nNode\n## コーディング規約\nstrict\n## コマンド\nnpm test\n## HELIX ワークフロー\nhelix"}}'
set +e
out=$(echo "$input" | $CLI/helix-check-claudemd 2>&1)
exit_code=$?
set -e
[[ $exit_code -eq 0 ]] || { echo "FAIL: compliant CLAUDE.md should pass (exit=$exit_code)"; exit 1; }

# テスト3: 既存ファイルの更新 → スルー
mkdir -p /tmp/helix-claudemd-test
echo "existing" > /tmp/helix-claudemd-test/CLAUDE.md
input='{"tool_name":"Write","tool_input":{"file_path":"/tmp/helix-claudemd-test/CLAUDE.md","content":"updated"}}'
set +e
out=$(echo "$input" | $CLI/helix-check-claudemd 2>&1)
exit_code=$?
set -e
rm -rf /tmp/helix-claudemd-test
[[ $exit_code -eq 0 ]] || { echo "FAIL: existing file update should pass"; exit 1; }

# テスト4: CLAUDE.md 以外 → スルー
input='{"tool_name":"Write","tool_input":{"file_path":"/tmp/README.md","content":"whatever"}}'
set +e
out=$(echo "$input" | $CLI/helix-check-claudemd 2>&1)
exit_code=$?
set -e
[[ $exit_code -eq 0 ]] || { echo "FAIL: non-CLAUDE.md should pass"; exit 1; }

echo "PASS: deny/pass/existing/non-CLAUDE all correct"
