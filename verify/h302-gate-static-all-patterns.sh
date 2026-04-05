#!/bin/bash
set -eo pipefail
# H302: G2/G3 static checks pass/fail with correct file states

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
YP="$CLI/lib/yaml_parser.py"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT
cd "$DIR" && git init -q && git config user.email "t@t" && git config user.name "T"
echo '{"name":"t"}' > package.json && echo "t" > README.md && git add . && git commit -q -m "i"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1
cp "$CLI/templates/gate-checks.yaml" .helix/gate-checks.yaml
rm -f .helix/runtime/index.json .helix/state/deliverables.json

echo "=== H302: Gate Static All Patterns ==="

# G2 no design → fail
python3 "$YP" write .helix/phase.yaml gates.G1.status passed 2>/dev/null
set +e; $CLI/helix-gate G2 --static-only >/dev/null 2>&1; r=$?; set -e
[[ $r -ne 0 ]] || { echo "FAIL: G2 no design should fail"; exit 1; }

# G2 with design → pass
mkdir -p docs/design && printf '# L2 設計書\n## セキュリティ設計\nSTRIDE 脅威分析\n## スコープ\n対象外: なし\nREQ-F-001\n' > docs/design/L2-arch.md
set +e; $CLI/helix-gate G2 --static-only >/dev/null 2>&1; r=$?; set -e
[[ $r -eq 0 ]] || { echo "FAIL: G2 with design should pass"; exit 1; }

# G3 no contract → fail
set +e; $CLI/helix-gate G3 --static-only >/dev/null 2>&1; r=$?; set -e
[[ $r -ne 0 ]] || { echo "FAIL: G3 no contract should fail"; exit 1; }

# G3 with contract → pass
printf 'contracts:\n# テスト設計\nTC-001: test\n# エラーハンドリング\nError Code: 400\n# トレーサビリティ\nF-001 → A-001\n' > docs/design/L3-api-contract.yaml
set +e; $CLI/helix-gate G3 --static-only >/dev/null 2>&1; r=$?; set -e
[[ $r -eq 0 ]] || { echo "FAIL: G3 with contract should pass"; exit 1; }

echo "PASS: G2 no/yes, G3 no/yes all correct"
