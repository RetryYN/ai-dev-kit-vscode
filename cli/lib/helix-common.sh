# helix-common.sh - 共通初期化
export HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
SCRIPT_DIR="$HELIX_HOME/cli"
PROJECT_ROOT="${HELIX_PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
HELIX_DIR="$PROJECT_ROOT/.helix"
CONFIG_FILE="$HELIX_DIR/config.yaml"
YAML_PARSER="$SCRIPT_DIR/lib/yaml_parser.py"
DB_PY="$SCRIPT_DIR/lib/helix_db.py"
DB_PATH="$HELIX_DIR/helix.db"

# --- Exit codes ---
EXIT_SUCCESS=0
EXIT_CHECK_FAILED=1      # ゲート/チェック失敗（想定内）
EXIT_INPUT_ERROR=2       # 入力/設定エラー
EXIT_PREREQ_ERROR=3      # 前提条件未達
EXIT_INTERNAL_ERROR=127  # 内部エラー
