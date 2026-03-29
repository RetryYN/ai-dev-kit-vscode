#!/bin/bash
set -eo pipefail
# 検証: yaml_parser.py が読み書き・dotpath（G1.5含む）・ネスト作成を正しく処理するか
# 受入条件: read/write/dump が正常動作、G1.5 キーが読める、新規ネストキーが作成される

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
YP="$HELIX_HOME/cli/lib/yaml_parser.py"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT

echo "=== 008: yaml-parser ==="

# テスト用 YAML
cat > "$DIR/test.yaml" << 'EOF'
project: test
gates:
  G1: { status: pending }
  G1.5: { status: skipped }
  G2: { status: passed, date: 2026-03-30 }
EOF

# read
val=$(python3 "$YP" read "$DIR/test.yaml" "project")
[[ "$val" == "test" ]] || { echo "FAIL: read project (got: $val)"; exit 1; }

# read nested
val=$(python3 "$YP" read "$DIR/test.yaml" "gates.G2.status")
[[ "$val" == "passed" ]] || { echo "FAIL: read G2 status (got: $val)"; exit 1; }

# read G1.5 (dotpath with dot in key)
val=$(python3 "$YP" read "$DIR/test.yaml" "gates.G1.5.status")
[[ "$val" == "skipped" ]] || { echo "FAIL: read G1.5 (got: $val)"; exit 1; }

# write
python3 "$YP" write "$DIR/test.yaml" "gates.G3.status" "passed"
val=$(python3 "$YP" read "$DIR/test.yaml" "gates.G3.status")
[[ "$val" == "passed" ]] || { echo "FAIL: write G3 (got: $val)"; exit 1; }

# write nested new key
python3 "$YP" write "$DIR/test.yaml" "sprint.current_step" ".1a"
val=$(python3 "$YP" read "$DIR/test.yaml" "sprint.current_step")
[[ "$val" == ".1a" ]] || { echo "FAIL: write nested new key (got: $val)"; exit 1; }

# dump (JSON output)
python3 "$YP" dump "$DIR/test.yaml" | python3 -c "import sys,json; json.load(sys.stdin)" || { echo "FAIL: dump invalid JSON"; exit 1; }

echo "PASS"
