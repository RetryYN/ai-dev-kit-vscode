#!/bin/bash
set -eo pipefail
# H205: G2→G7 の全ゲート前提条件チェーンが正しく機能するか

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
YP="$CLI/lib/yaml_parser.py"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT

cd "$DIR"
git init -q && git config user.email "t@t" && git config user.name "T"
echo '{"name":"t"}' > package.json
echo "t" > README.md && git add . && git commit -q -m "init"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1
cp "$CLI/templates/gate-checks.yaml" .helix/gate-checks.yaml
rm -f .helix/runtime/index.json .helix/state/deliverables.json

echo "=== H205: Gate Cascade Integrity ==="

# G2 → G1 前提（G1 を事前に pass）
mkdir -p docs/design && printf '# L2 設計書\n## セキュリティ設計\nSTRIDE 脅威分析\n## スコープ\n対象外: なし\nREQ-F-001\n' > docs/design/L2-arch.md
python3 "$YP" write .helix/phase.yaml gates.G1.status passed 2>/dev/null
set +e; $CLI/helix-gate G2 --static-only >/dev/null 2>&1; g2=$?; set -e
[[ $g2 -eq 0 ]] || { echo "FAIL: G2 should pass (G1 passed)"; exit 1; }

# G3 → G2 必須（G2 passed なので OK）
printf 'contracts:\n# テスト設計\nTC-001: test\n# エラーハンドリング\nError Code: 400\n# トレーサビリティ\nF-001 → A-001\n' > docs/design/L3-api-contract.yaml
set +e; $CLI/helix-gate G3 --static-only >/dev/null 2>&1; g3=$?; set -e
[[ $g3 -eq 0 ]] || { echo "FAIL: G3 should pass (G2 passed)"; exit 1; }

# G4 → G3 必須（G3 passed なので OK、dry-run で static スキップ）
set +e; $CLI/helix-gate G4 --static-only --dry-run >/dev/null 2>&1; g4=$?; set -e
[[ $g4 -eq 0 ]] || { echo "FAIL: G4 dry-run should pass (G3 passed)"; exit 1; }

# G5 → G4 必須だが G4 は dry-run のみなので pending → fail
python3 "$YP" write .helix/phase.yaml gates.G4.status pending 2>/dev/null
set +e; out=$($CLI/helix-gate G5 --static-only --dry-run 2>&1); g5=$?; set -e
[[ $g5 -ne 0 ]] || { echo "FAIL: G5 should fail (G4 pending)"; exit 1; }

# G6 → G4 必須
python3 "$YP" write .helix/phase.yaml gates.G4.status pending 2>/dev/null
set +e; out=$($CLI/helix-gate G6 --static-only --dry-run 2>&1); g6=$?; set -e
[[ $g6 -ne 0 ]] || { echo "FAIL: G6 should fail (G4 pending)"; exit 1; }

# G7 → G6 必須
python3 "$YP" write .helix/phase.yaml gates.G6.status pending 2>/dev/null
set +e; out=$($CLI/helix-gate G7 --static-only --dry-run 2>&1); g7=$?; set -e
[[ $g7 -ne 0 ]] || { echo "FAIL: G7 should fail (G6 pending)"; exit 1; }

# 全 chain pass: G4→G5→G6→G7
python3 "$YP" write .helix/phase.yaml gates.G4.status passed 2>/dev/null
set +e; $CLI/helix-gate G5 --static-only --dry-run >/dev/null 2>&1; g5ok=$?; set -e
[[ $g5ok -eq 0 ]] || { echo "FAIL: G5 should pass (G4 passed)"; exit 1; }

echo "PASS: G2(G1)→G3(G2)→G4(G3)→G5(G4)→G6(G4)→G7(G6) chain verified"
