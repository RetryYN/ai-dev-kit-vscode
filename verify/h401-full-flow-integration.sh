#!/bin/bash
set -eo pipefail
# H401: HELIX フルフロー統合テスト
# init → scrum → gate → sprint → api-check → freeze-break → status → pr → log
# 受入条件: 20ステップ全て正常完了

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
YP="$CLI/lib/yaml_parser.py"
DIR=$(mktemp -d /tmp/helix-fulltest-XXXXXX)
trap 'rm -rf "$DIR"' EXIT

cd "$DIR"
git init -q && git config user.email "t@t" && git config user.name "T"
echo '{"name":"myapp","scripts":{"test":"echo PASS"}}' > package.json
echo "# myapp" > README.md
git add . && git commit -q -m "init"
export HELIX_PROJECT_ROOT="$DIR"

PASS=0
FAIL=0

check() {
  local name="$1"
  shift
  set +e
  eval "$@" >/dev/null 2>&1
  local r=$?
  set -e
  if [[ $r -eq 0 ]]; then
    PASS=$((PASS + 1))
  else
    echo "FAIL: $name"
    FAIL=$((FAIL + 1))
  fi
}

check_contains() {
  local name="$1" cmd="$2" pattern="$3"
  set +e
  local out=$(eval "$cmd" 2>&1)
  set -e
  if echo "$out" | grep -q "$pattern"; then
    PASS=$((PASS + 1))
  else
    echo "FAIL: $name (pattern '$pattern' not found)"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== H401: Full Flow Integration ==="

# 1. init
check "init" "$CLI/helix-init --project-name myapp"
check "init idempotent" "$CLI/helix-init --project-name myapp"
cp "$CLI/templates/gate-checks.yaml" .helix/gate-checks.yaml
rm -f .helix/runtime/index.json .helix/state/deliverables.json

# 2. log init
check "log init" "$CLI/helix-log init"

# 3. size
check_contains "size M" "$CLI/helix-size --files 5 --lines 200 --api --ui --type new-feature" "サイズ:.*M"

# 4. scrum init + backlog
check "scrum init" "$CLI/helix-scrum init"
check "scrum backlog add" "$CLI/helix-scrum backlog add --id H001 --title Test --question Q --acceptance A"
check_contains "scrum backlog list" "$CLI/helix-scrum backlog list" "H001"

# 5. scrum plan
check_contains "scrum plan" "$CLI/helix-scrum plan --goal Test --hypotheses H001" "Sprint"

# 6. scrum verify fail
check_contains "scrum verify fail" "$CLI/helix-scrum verify 2>&1 || true" "1 failed"

# 7. fix verify script
echo '#!/bin/bash' > verify/h001-test.sh
echo 'exit 0' >> verify/h001-test.sh
chmod +x verify/h001-test.sh

# 8. scrum verify pass
check "scrum verify pass" "$CLI/helix-scrum verify"

# 9. scrum decide
check_contains "scrum decide" "$CLI/helix-scrum decide --hypothesis H001 --confirmed" "confirmed"

# 10. gate G2
mkdir -p docs/design && printf '# L2 設計書\n## セキュリティ設計\nSTRIDE 脅威分析\n## スコープ\n対象外: なし\nREQ-F-001\n' > docs/design/L2-arch.md
python3 "$YP" write .helix/phase.yaml gates.G1.status passed 2>/dev/null
check_contains "gate G2 pass" "$CLI/helix-gate G2 --static-only" "PASS"

# 11. gate G3
echo "contracts:" > docs/design/L3-api-contract.yaml
check_contains "gate G3 pass" "$CLI/helix-gate G3 --static-only" "PASS"

# 12. sprint
$CLI/helix-sprint reset >/dev/null 2>&1
check_contains "sprint start" "$CLI/helix-sprint next" ".1a"
check_contains "sprint advance" "$CLI/helix-sprint next" ".1b"

# 13. api contract match
mkdir -p src/api
echo "contracts:" > docs/design/L3-api-contract.yaml
printf '  - method: "GET"\n    endpoint: "/api/v1/health"\n' >> docs/design/L3-api-contract.yaml
echo 'router.get("/api/v1/health", h);' > src/api/health.ts
check_contains "api contract match" "$CLI/helix-gate-api-check" "OK"

# 14. freeze-break
echo "change" > src/api/users.ts
check_contains "freeze-break" "$CLI/helix-hook $DIR/src/api/users.ts 2>&1 || true" "凍結違反"

# 15. status
set +e
out=$($CLI/helix-status 2>&1)
set -e
echo "$out" | grep -q "Gates:" && PASS=$((PASS + 1)) || { echo "FAIL: status gates"; FAIL=$((FAIL + 1)); }
echo "$out" | grep -q "G2" && PASS=$((PASS + 1)) || { echo "FAIL: status G2"; FAIL=$((FAIL + 1)); }

# 16. task catalog
check_contains "task catalog" "$CLI/helix-task catalog review" "review-security"

# 17. pr dry-run
git checkout -b feature/test 2>/dev/null
git add . && git commit -q -m "feat: test" 2>/dev/null || true
check_contains "pr dry-run" "$CLI/helix-pr --dry-run --base master" "Summary"

# 18. retro exists
[[ -d .helix/retros ]] && ls .helix/retros/*.md >/dev/null 2>&1 && PASS=$((PASS + 1)) || { echo "FAIL: retro missing"; FAIL=$((FAIL + 1)); }

# 19. log feedback
check "log feedback" "$CLI/helix-log feedback --desc 'test feedback' --type praise"

# 20. scrum status
check_contains "scrum status" "$CLI/helix-scrum status" "Sprint"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[[ $FAIL -eq 0 ]] || exit 1
echo "PASS"
