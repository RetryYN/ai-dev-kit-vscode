#!/bin/bash
set -eo pipefail
# H204: session-start が有効な JSON で全ツール情報を含むか

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"

echo "=== H204: Session Context Injection ==="

out=$($CLI/helix-session-start 2>&1)

# JSON valid
echo "$out" | python3 -c "import sys,json; json.load(sys.stdin)" || { echo "FAIL: invalid JSON"; exit 1; }

# 必須ツール名が含まれるか
for tool in helix-codex helix-gate helix-size helix-sprint helix-pr helix-reverse "helix scrum"; do
  echo "$out" | grep -q "$tool" || { echo "FAIL: missing $tool"; exit 1; }
done

# FE サブエージェント
echo "$out" | grep -q "fe-design" || { echo "FAIL: missing fe-design"; exit 1; }

# Scrum 情報
echo "$out" | grep -q "Scrum\|scrum" || { echo "FAIL: missing Scrum info"; exit 1; }

# CLAUDE.md テンプレート言及
echo "$out" | grep -q "CLAUDE.md" || { echo "FAIL: missing CLAUDE.md template reference"; exit 1; }

echo "PASS"
