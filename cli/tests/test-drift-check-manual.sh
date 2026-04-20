#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/home/tenni/ai-dev-kit-vscode"
CLI="$REPO_ROOT/cli/helix-drift-check"
TMP_ROOT="$(mktemp -d)"
PROJ="$TMP_ROOT/proj"
FAKE_BIN="$TMP_ROOT/bin"

pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1" >&2; return 1; }

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

mkdir -p "$PROJ/.helix" "$FAKE_BIN"

cat > "$FAKE_BIN/jq" <<'JQEOF'
#!/usr/bin/env bash
set -euo pipefail
id=""
file=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -c)
      shift
      ;;
    --arg)
      if [[ "${2:-}" == "id" ]]; then
        id="${3:-}"
      fi
      shift 3
      ;;
    *)
      file="$1"
      shift
      ;;
  esac
done

if [[ -n "$id" ]] && [[ -f "$file" ]] && grep -q '"id"[[:space:]]*:[[:space:]]*"'"$id"'"' "$file"; then
  echo "{\"id\":\"$id\",\"layer\":\"L6\"}"
fi
JQEOF
chmod +x "$FAKE_BIN/jq"

# case 1: generic else branch
mkdir -p "$PROJ/docs/features/auth/D-PERF"
printf 'performance spec\n' > "$PROJ/docs/features/auth/D-PERF/custom.md"
cat > "$PROJ/.helix/index.json" <<'JSONEOF'
{
  "rules": {
    "deliverables": [
      { "id": "D-PERF", "layer": "L6" }
    ]
  }
}
JSONEOF

if PATH="$FAKE_BIN:$PATH" HELIX_HOME="$REPO_ROOT" HELIX_PROJECT_ROOT="$PROJ" "$CLI" "$PROJ/docs/features/auth/D-PERF/custom.md" >"$TMP_ROOT/c1.out" 2>"$TMP_ROOT/c1.err" \
  && grep -q '\[drift-check\] generic deliverable change: D-PERF' "$TMP_ROOT/c1.err"; then
  pass "generic D-PERF drift message"
else
  fail "generic D-PERF drift message"
fi

# case 2: D-API branch
mkdir -p "$PROJ/docs/features/auth/D-API"
printf 'openapi: 3.0.0\n' > "$PROJ/docs/features/auth/D-API/contract.yaml"

if HELIX_HOME="$REPO_ROOT" HELIX_PROJECT_ROOT="$PROJ" "$CLI" "$PROJ/docs/features/auth/D-API/contract.yaml" >"$TMP_ROOT/c2.out" 2>"$TMP_ROOT/c2.err" \
  && grep -q '\[helix-drift\] D-API 変更検出:' "$TMP_ROOT/c2.out"; then
  pass "D-API branch still works"
else
  fail "D-API branch still works"
fi

# case 3: missing index.json warning + exit 0
mkdir -p "$PROJ/docs/features/auth/D-AUDIT"
printf 'audit note\n' > "$PROJ/docs/features/auth/D-AUDIT/custom.md"
rm -f "$PROJ/.helix/index.json"

if HELIX_HOME="$REPO_ROOT" HELIX_PROJECT_ROOT="$PROJ" "$CLI" "$PROJ/docs/features/auth/D-AUDIT/custom.md" >"$TMP_ROOT/c3.out" 2>"$TMP_ROOT/c3.err" \
  && grep -q '\[drift-check\] WARN: missing index.json' "$TMP_ROOT/c3.err"; then
  pass "missing index warning with exit 0"
else
  fail "missing index warning with exit 0"
fi

echo "All manual drift-check tests passed"
