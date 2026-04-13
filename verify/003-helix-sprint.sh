#!/bin/bash
set -eo pipefail
# 検証: helix-sprint が .1a→.5→completed のフル周回と
#       推奨アクション表示 / .2/.5 完了時レビュー起動を正しく行うか

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI_SRC="$HELIX_HOME/cli"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT

cp -a "$CLI_SRC" "$DIR/cli"
CLI="$DIR/cli"

cd "$DIR"
git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "i"
export HELIX_PROJECT_ROOT="$DIR"
"$CLI/helix-init" --project-name t >/dev/null 2>&1

# helix-review をモックして自動レビュー発火を観測
cat > "$CLI/helix-review" << 'EOF'
#!/bin/bash
echo "$*" >> "${HELIX_PROJECT_ROOT}/review_calls.log"
exit 0
EOF
chmod +x "$CLI/helix-review"

wait_for_review_call() {
  local expected_min="$1"
  local retries=20
  local count=0
  while (( retries > 0 )); do
    if [[ -f "$DIR/review_calls.log" ]]; then
      count=$(wc -l < "$DIR/review_calls.log" | tr -d ' ')
      if (( count >= expected_min )); then
        return 0
      fi
    fi
    sleep 0.1
    retries=$((retries - 1))
  done
  return 1
}

echo "=== 003: helix-sprint ==="

"$CLI/helix-sprint" reset >/dev/null 2>&1

# 未開始 -> .1a
out=$("$CLI/helix-sprint" next 2>&1)
echo "$out" | grep -q "Sprint 開始: .1a" || { echo "FAIL: start .1a"; exit 1; }
echo "$out" | grep -q "\[helix-sprint\] 推奨アクション:" || { echo "FAIL: recommended action header for .1a"; exit 1; }
echo "$out" | grep -q "role legacy" || { echo "FAIL: recommended action body for .1a"; exit 1; }

# .1a -> .1b（推奨表示あり）
out=$("$CLI/helix-sprint" next 2>&1)
echo "$out" | grep -q ".1a 完了 → .1b" || { echo "FAIL: .1a to .1b"; exit 1; }
echo "$out" | grep -q "role tl --task 'change plan" || { echo "FAIL: recommended action body for .1b"; exit 1; }

# .1b -> .2（推奨表示あり）
out=$("$CLI/helix-sprint" next 2>&1)
echo "$out" | grep -q ".1b 完了 → .2" || { echo "FAIL: .1b to .2"; exit 1; }
echo "$out" | grep -q "role se --task 'skeleton" || { echo "FAIL: recommended action body for .2"; exit 1; }

# .2 完了時に自動レビュー発火（次は .3）
out=$("$CLI/helix-sprint" next 2>&1)
echo "$out" | grep -q ".2 完了 → .3" || { echo "FAIL: .2 to .3"; exit 1; }
echo "$out" | grep -q "Codex レビューをバックグラウンドで起動" || { echo "FAIL: auto review message after .2"; exit 1; }
wait_for_review_call 1 || { echo "FAIL: auto review call not observed after .2"; exit 1; }
tail -n 1 "$DIR/review_calls.log" | grep -q -- "--uncommitted --bg" || { echo "FAIL: auto review args after .2"; exit 1; }

# .3 -> .4
out=$("$CLI/helix-sprint" next 2>&1)
echo "$out" | grep -q ".3 完了 → .4" || { echo "FAIL: .3 to .4"; exit 1; }
echo "$out" | grep -q "role qa --task 'test and verify" || { echo "FAIL: recommended action body for .4"; exit 1; }

# .4 -> .5
out=$("$CLI/helix-sprint" next 2>&1)
echo "$out" | grep -q ".4 完了 → .5" || { echo "FAIL: .4 to .5"; exit 1; }
echo "$out" | grep -q "role tl --task 'full review" || { echo "FAIL: recommended action body for .5"; exit 1; }

# .5 完了で Sprint completed + 自動レビュー発火
out=$("$CLI/helix-sprint" next 2>&1)
echo "$out" | grep -q ".5 完了 — Sprint 完了" || { echo "FAIL: .5 to completed"; exit 1; }
echo "$out" | grep -q "Codex レビューをバックグラウンドで起動" || { echo "FAIL: auto review message after .5"; exit 1; }
wait_for_review_call 2 || { echo "FAIL: auto review call not observed after .5"; exit 1; }
tail -n 1 "$DIR/review_calls.log" | grep -q -- "--uncommitted --bg" || { echo "FAIL: auto review args after .5"; exit 1; }

# completed 状態確認
out=$("$CLI/helix-sprint" status 2>&1)
echo "$out" | grep -q "Sprint 完了" || echo "$out" | grep -q "completed" || { echo "FAIL: not completed"; exit 1; }

echo "PASS"
