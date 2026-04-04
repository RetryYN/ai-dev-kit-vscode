# helix-common.sh - 共通初期化
export HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
SCRIPT_DIR="$HELIX_HOME/cli"
PROJECT_ROOT="${HELIX_PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
HELIX_DIR="$PROJECT_ROOT/.helix"
YAML_PARSER="$SCRIPT_DIR/lib/yaml_parser.py"
DB_PY="$SCRIPT_DIR/lib/helix_db.py"
DB_PATH="$HELIX_DIR/helix.db"
