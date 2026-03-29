#!/bin/bash
set -eo pipefail
# H307: Reverse R0→R4 全前提条件チェーン

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
YP="$CLI/lib/yaml_parser.py"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT
cd "$DIR" && git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "i"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1

echo "=== H307: Reverse Full Prereq Chain ==="

# R0: no prereq
set +e; $CLI/helix-reverse R0 --dry-run >/dev/null 2>&1; r=$?; set -e
[[ $r -eq 0 ]] || { echo "FAIL: R0 should pass"; exit 1; }

# R1: needs RG0
set +e; $CLI/helix-reverse R1 --dry-run >/dev/null 2>&1; r=$?; set -e
[[ $r -ne 0 ]] || { echo "FAIL: R1 should fail (RG0 pending)"; exit 1; }

# R2: needs RG1
python3 "$YP" write .helix/phase.yaml reverse_gates.RG0.status passed 2>/dev/null
set +e; $CLI/helix-reverse R2 --dry-run >/dev/null 2>&1; r=$?; set -e
[[ $r -ne 0 ]] || { echo "FAIL: R2 should fail (RG1 pending)"; exit 1; }

# R3: needs RG2
python3 "$YP" write .helix/phase.yaml reverse_gates.RG1.status passed 2>/dev/null
set +e; $CLI/helix-reverse R3 --dry-run >/dev/null 2>&1; r=$?; set -e
[[ $r -ne 0 ]] || { echo "FAIL: R3 should fail (RG2 pending)"; exit 1; }

# R4: needs RG3
python3 "$YP" write .helix/phase.yaml reverse_gates.RG2.status passed 2>/dev/null
set +e; $CLI/helix-reverse R4 --dry-run >/dev/null 2>&1; r=$?; set -e
[[ $r -ne 0 ]] || { echo "FAIL: R4 should fail (RG3 pending)"; exit 1; }

echo "PASS: R0(ok)→R1(RG0)→R2(RG1)→R3(RG2)→R4(RG3) chain verified"
