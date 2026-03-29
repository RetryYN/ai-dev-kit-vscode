#!/bin/bash
set -eo pipefail
# 検証: API契約突合が契約と実装のエンドポイント差分を正しく検出するか
# 受入条件: 一致→pass、未実装→fail、未承認→fail

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT

cd "$DIR"
git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "i"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1

echo "=== 006: api-contract ==="

# 一致するケース
mkdir -p docs/design src/api
cat > docs/design/L3-api-contract.yaml << 'EOF'
contracts:
  - method: "GET"
    endpoint: "/api/v1/users"
  - method: "POST"
    endpoint: "/api/v1/users"
EOF
cat > src/api/users.ts << 'EOF'
router.get('/api/v1/users', h);
router.post('/api/v1/users', h);
EOF

set +e
out=$($CLI/helix-gate-api-check 2>&1)
exit_code=$?
set -e
[[ $exit_code -eq 0 ]] || { echo "FAIL: matching endpoints should pass (got exit $exit_code)"; exit 1; }

# 未実装エンドポイント追加
printf '  - method: "DELETE"\n    endpoint: "/api/v1/users/:id"\n' >> docs/design/L3-api-contract.yaml

set +e
out=$($CLI/helix-gate-api-check 2>&1)
exit_code=$?
set -e
[[ $exit_code -eq 1 ]] || { echo "FAIL: missing impl should fail"; exit 1; }
echo "$out" | grep -q "契約にあるが未実装" || { echo "FAIL: missing impl message"; exit 1; }

echo "PASS"
