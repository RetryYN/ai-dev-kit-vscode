#!/bin/bash
set -eo pipefail
# H101: Forward フルフロー
# init → G2 pass → G3 pass → G4 dry-run pass

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
YP="$CLI/lib/yaml_parser.py"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT

cd "$DIR"
git init -q && git config user.email "t@t" && git config user.name "T"
echo '{"name":"t","scripts":{"test":"echo pass"}}' > package.json
echo "t" > README.md
git add . && git commit -q -m "init"
export HELIX_PROJECT_ROOT="$DIR"

echo "=== H101: Forward Full Flow ==="

$CLI/helix-init --project-name forward-test >/dev/null 2>&1
mkdir -p docs/design
echo "# L2 Architecture" > docs/design/L2-architecture.md

# G2
set +e
$CLI/helix-gate G2 --static-only >/dev/null 2>&1; g2=$?
set -e
[[ $g2 -eq 0 ]] || { echo "FAIL: G2"; exit 1; }
[[ "$(python3 "$YP" read .helix/phase.yaml gates.G2.status 2>/dev/null)" == "passed" ]] || { echo "FAIL: G2 state"; exit 1; }

# G3
echo "contracts:" > docs/design/L3-api-contract.yaml
set +e
$CLI/helix-gate G3 --static-only >/dev/null 2>&1; g3=$?
set -e
[[ $g3 -eq 0 ]] || { echo "FAIL: G3"; exit 1; }

# G4 dry-run
set +e
$CLI/helix-gate G4 --static-only --dry-run >/dev/null 2>&1; g4=$?
set -e
[[ $g4 -eq 0 ]] || { echo "FAIL: G4 dry-run"; exit 1; }

echo "PASS"
