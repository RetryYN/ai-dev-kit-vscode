#!/bin/bash
set -eo pipefail
# H304: Hook の全トリガー種別（パーサー修正後）

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT
cd "$DIR" && git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "i"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1
$CLI/helix-matrix add-feature user-auth --drive be >/dev/null 2>&1

echo "=== H304: Hook All Triggers ==="

# gate_ready (matrix path)
mkdir -p docs/features/user-auth/D-ARCH && echo "# L2" > docs/features/user-auth/D-ARCH/architecture.md
set +e; out=$(HELIX_GUARD=off $CLI/helix-hook "$DIR/docs/features/user-auth/D-ARCH/architecture.md" 2>&1); set -e
echo "$out" | grep -q "gate_ready.*G2" || { echo "FAIL: gate_ready G2"; exit 1; }

# design_sync WARN
mkdir -p src/features/user-auth/D-IMPL/nested && echo "x" > src/features/user-auth/D-IMPL/nested/impl.ts
set +e; out=$(HELIX_GUARD=off $CLI/helix-hook "$DIR/src/features/user-auth/D-IMPL/nested/impl.ts" 2>&1); set -e
echo "$out" | grep -q "設計文書未作成\|WARN" || { echo "FAIL: design_sync"; exit 1; }

# freeze-break
python3 "$CLI/lib/yaml_parser.py" write .helix/phase.yaml gates.G3.status passed >/dev/null 2>&1 || true
mkdir -p docs/features/user-auth/D-API && echo "contracts: []" > docs/features/user-auth/D-API/api-contract.yaml
set +e; out=$(HELIX_GUARD=off $CLI/helix-hook "$DIR/docs/features/user-auth/D-API/api-contract.yaml" 2>&1); set -e
echo "$out" | grep -q "凍結違反" || { echo "FAIL: freeze-break"; exit 1; }

# no-op
NOHELIX=$(mktemp -d /tmp/helix-noop-XXXXXX)
set +e; out=$(HELIX_PROJECT_ROOT="$NOHELIX" $CLI/helix-hook "$NOHELIX/f.ts" 2>&1); r=$?; set -e
rm -rf "$NOHELIX"
[[ $r -eq 0 && -z "$out" ]] || { echo "FAIL: no-op"; exit 1; }

echo "PASS: gate_ready + design_sync + freeze-break + no-op"
