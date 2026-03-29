#!/bin/bash
set -eo pipefail
# 検証: helix-size がタスクサイジングとフェーズスキップを正しく判定するか
# 受入条件: S/M/L 全パターン + フェーズスキップ決定木が SKILL_MAP.md と一致

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"

echo "=== 002: helix-size ==="

# S bugfix → L4 only
out=$($CLI/helix-size --files 1 --lines 20 --type bugfix 2>&1)
echo "$out" | grep -q "サイズ: S" || { echo "FAIL: S bugfix size"; exit 1; }
echo "$out" | grep -q "L4" || { echo "FAIL: S bugfix phases"; exit 1; }

# M new-feature + API + UI → full
out=$($CLI/helix-size --files 5 --lines 200 --api --ui --type new-feature 2>&1)
echo "$out" | grep -q "サイズ: M" || { echo "FAIL: M size"; exit 1; }

# L → full
out=$($CLI/helix-size --files 15 --lines 800 --api --db --ui 2>&1)
echo "$out" | grep -q "サイズ: L" || { echo "FAIL: L size"; exit 1; }

# S doc → L4 only
out=$($CLI/helix-size --files 1 --lines 10 --type doc 2>&1)
echo "$out" | grep -q "L4" || { echo "FAIL: S doc phases"; exit 1; }

# M no UI → L5 skip
out=$($CLI/helix-size --files 6 --lines 300 --api --type new-feature 2>&1)
echo "$out" | grep "推奨フェーズ" | grep -q "L5" && { echo "FAIL: M no-UI should skip L5"; exit 1; }

echo "PASS"
