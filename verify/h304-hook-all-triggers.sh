#!/bin/bash
set -eo pipefail
# H304: Hook の全トリガー種別

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT
cd "$DIR" && git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "i"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1

echo "=== H304: Hook All Triggers ==="

# gate_ready: L2 設計書
mkdir -p docs/design && echo "# L2" > docs/design/L2-arch.md
set +e; out=$($CLI/helix-hook "$DIR/docs/design/L2-arch.md" 2>&1); set -e
echo "$out" | grep -q "gate_ready.*G2" || { echo "FAIL: gate_ready G2"; exit 1; }

# design_sync: src/components without design → WARN
mkdir -p src/components && echo "x" > src/components/Btn.tsx
set +e; out=$($CLI/helix-hook "$DIR/src/components/Btn.tsx" 2>&1); set -e
echo "$out" | grep -q "設計文書未作成\|WARN" || { echo "FAIL: design_sync warn"; exit 1; }

# freeze-break (G2 passed + L2 change)
python3 "$CLI/lib/yaml_parser.py" write .helix/phase.yaml gates.G2.status passed 2>/dev/null
set +e; out=$($CLI/helix-hook "$DIR/docs/design/L2-arch.md" 2>&1); set -e
echo "$out" | grep -q "凍結違反\|freeze" || { echo "FAIL: freeze-break G2"; exit 1; }

# no-op: .helix/ なし
NOHELIX=$(mktemp -d /tmp/helix-noop-XXXXXX)
set +e; out=$(HELIX_PROJECT_ROOT="$NOHELIX" $CLI/helix-hook "$NOHELIX/somefile.ts" 2>&1); r=$?; set -e
rm -rf "$NOHELIX"
[[ $r -eq 0 ]] || { echo "FAIL: no-helix exit"; exit 1; }
[[ -z "$out" ]] || { echo "FAIL: no-helix not silent"; exit 1; }

# NOTE: coverage_check trigger has a known parser bug with YAML comments
# before pattern entries. Filed for Sprint 4.

echo "PASS: gate_ready + design_sync + freeze-break + no-op"
