#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/home/tenni/ai-dev-kit-vscode"
CLI="$REPO_ROOT/cli/helix-gate"
TMP_ROOT="$(mktemp -d)"

pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1" >&2; return 1; }

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

write_gate_checks() {
  local proj="$1"
  mkdir -p "$proj/.helix"
  cat > "$proj/.helix/gate-checks.yaml" <<'YAML'
G2:
  name: "設計凍結"
  static:
  ai:
G4:
  name: "実装凍結"
  static:
  ai:
G6:
  name: "RC判定"
  static:
  ai:
YAML
}

write_phase() {
  local proj="$1"
  local drive="$2"
  cat > "$proj/.helix/phase.yaml" <<YAML
phase: L4
sprint:
  drive: ${drive}
gates:
  G1:
    status: passed
  G2:
    status: pending
  G3:
    status: passed
  G4:
    status: pending
  G5:
    status: passed
  G6:
    status: pending
YAML
}

run_gate() {
  local proj="$1"
  local gate="$2"
  local out="$3"
  local err="$4"
  set +e
  HELIX_HOME="$REPO_ROOT" HELIX_PROJECT_ROOT="$proj" "$CLI" "$gate" >"$out" 2>"$err"
  local rc=$?
  set -e
  echo "$rc"
}

count_debt_ids() {
  local file="$1"
  local id="$2"
  local n
  n=$(grep -cE "^[[:space:]]*-[[:space:]]+id:[[:space:]]*${id}[[:space:]]*$" "$file" 2>/dev/null || echo 0)
  echo "${n:-0}"
}

# Case 1: fe 駆動で G2 実行 -> 3項目登録
PROJ1="$TMP_ROOT/proj1"
mkdir -p "$PROJ1"
write_gate_checks "$PROJ1"
write_phase "$PROJ1" "fe"

rc=$(run_gate "$PROJ1" "G2" "$TMP_ROOT/c1.out" "$TMP_ROOT/c1.err")
if [[ "$rc" -eq 0 ]] \
  && [[ -f "$PROJ1/.helix/debt-register.yaml" ]] \
  && grep -q "id: MOCK-DERIVED-CONTRACT" "$PROJ1/.helix/debt-register.yaml" \
  && grep -q "id: MOCK-HARDCODE" "$PROJ1/.helix/debt-register.yaml" \
  && grep -q "id: MOCK-CODE-LEAK" "$PROJ1/.helix/debt-register.yaml"; then
  pass "case1: fe G2 で3項目 auto-enqueue"
else
  fail "case1: fe G2 で3項目 auto-enqueue"
fi

# Case 2: be 駆動で G2 実行 -> 登録されない
PROJ2="$TMP_ROOT/proj2"
mkdir -p "$PROJ2"
write_gate_checks "$PROJ2"
write_phase "$PROJ2" "be"

rc=$(run_gate "$PROJ2" "G2" "$TMP_ROOT/c2.out" "$TMP_ROOT/c2.err")
if [[ "$rc" -eq 0 ]] \
  && [[ ! -f "$PROJ2/.helix/debt-register.yaml" ]]; then
  pass "case2: be G2 では auto-enqueue なし"
else
  fail "case2: be G2 では auto-enqueue なし"
fi

# Case 3: fe 駆動で再度 G2 実行 -> 重複なし（skip）
rc=$(run_gate "$PROJ1" "G2" "$TMP_ROOT/c3.out" "$TMP_ROOT/c3.err")
count_derived=$(count_debt_ids "$PROJ1/.helix/debt-register.yaml" "MOCK-DERIVED-CONTRACT")
count_hardcode=$(count_debt_ids "$PROJ1/.helix/debt-register.yaml" "MOCK-HARDCODE")
count_code_leak=$(count_debt_ids "$PROJ1/.helix/debt-register.yaml" "MOCK-CODE-LEAK")
if [[ "$rc" -eq 0 ]] \
  && [[ "$count_derived" == "1" ]] \
  && [[ "$count_hardcode" == "1" ]] \
  && [[ "$count_code_leak" == "1" ]] \
  && grep -q "\[skip\] id=MOCK-HARDCODE" "$TMP_ROOT/c3.err"; then
  pass "case3: fe G2 再実行で重複なし"
else
  fail "case3: fe G2 再実行で重複なし"
fi

# Case 4: fe 駆動 G4 で MOCK-HARDCODE 未解決 -> fail
PROJ4="$TMP_ROOT/proj4"
mkdir -p "$PROJ4"
write_gate_checks "$PROJ4"
write_phase "$PROJ4" "fe"
cat > "$PROJ4/.helix/debt-register.yaml" <<'YAML'
items:
  - id: MOCK-HARDCODE
    status: open
  - id: MOCK-CODE-LEAK
    status: resolved
YAML

rc=$(run_gate "$PROJ4" "G4" "$TMP_ROOT/c4.out" "$TMP_ROOT/c4.err")
if [[ "$rc" -eq 1 ]] \
  && grep -q "G4 fail: MOCK-HARDCODE が未解決 (fe駆動時は必須)" "$TMP_ROOT/c4.err"; then
  pass "case4: fe G4 で未解決 debt は fail-close"
else
  fail "case4: fe G4 で未解決 debt は fail-close"
fi

# Case 5: fe 駆動 G4 で 2項目 resolved -> この理由では fail しない
PROJ5="$TMP_ROOT/proj5"
mkdir -p "$PROJ5"
write_gate_checks "$PROJ5"
write_phase "$PROJ5" "fe"
cat > "$PROJ5/.helix/debt-register.yaml" <<'YAML'
items:
  - id: MOCK-HARDCODE
    status: resolved
  - id: MOCK-CODE-LEAK
    status: resolved
YAML

rc=$(run_gate "$PROJ5" "G4" "$TMP_ROOT/c5.out" "$TMP_ROOT/c5.err")
if [[ "$rc" -eq 0 ]] \
  && ! grep -q "G4 fail: MOCK-HARDCODE" "$TMP_ROOT/c5.err" \
  && ! grep -q "G4 fail: MOCK-CODE-LEAK" "$TMP_ROOT/c5.err"; then
  pass "case5: fe G4 で2項目解決済みなら debt要因で失敗しない"
else
  fail "case5: fe G4 で2項目解決済みなら debt要因で失敗しない"
fi

echo "All gate auto-enqueue manual tests passed"
