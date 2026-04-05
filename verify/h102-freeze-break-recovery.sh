#!/bin/bash
set -eo pipefail
# H102: freeze-break → invalidated → recovery → re-passed

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
YP="$CLI/lib/yaml_parser.py"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT

cd "$DIR"
git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "init"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1

echo "=== H102: Freeze-break Recovery ==="

mkdir -p docs/design src/api
printf '# L2 設計書\n## セキュリティ設計\nSTRIDE 脅威分析\n## スコープ\n対象外: なし\nREQ-F-001\n' > docs/design/L2-arch.md
python3 "$YP" write .helix/phase.yaml gates.G2.status passed 2>/dev/null
python3 "$YP" write .helix/phase.yaml gates.G3.status passed 2>/dev/null
python3 "$YP" write .helix/phase.yaml gates.G4.status passed 2>/dev/null

# freeze-break
echo "change" > src/api/new.ts
set +e; $CLI/helix-hook "$DIR/src/api/new.ts" >/dev/null 2>&1; set -e

g4=$(python3 "$YP" read .helix/phase.yaml gates.G4.status 2>/dev/null)
[[ "$g4" == "invalidated" ]] || { echo "FAIL: G4 not invalidated ($g4)"; exit 1; }

# recovery
python3 "$YP" write .helix/phase.yaml gates.G3.status passed 2>/dev/null
python3 "$YP" write .helix/phase.yaml gates.G4.status passed 2>/dev/null
g4=$(python3 "$YP" read .helix/phase.yaml gates.G4.status 2>/dev/null)
[[ "$g4" == "passed" ]] || { echo "FAIL: recovery failed ($g4)"; exit 1; }

echo "PASS"
