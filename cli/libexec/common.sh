# HELIX 共通シェル — helix-* CLI の source 先

if [[ -z "${BASH_VERSION:-}" ]]; then
  echo "[helix] エラー: cli/libexec/common.sh は bash で source してください" >&2
  return 1 2>/dev/null || exit 1
fi

_HELIX_COMMON_LIBEXEC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_HELIX_COMMON_CLI_DIR="$(cd "$_HELIX_COMMON_LIBEXEC_DIR/.." && pwd)"

# 既存の初期化・パス検証関数を正本として再利用する。
source "$_HELIX_COMMON_CLI_DIR/lib/helix-common.sh"

PHASE_YAML="${PHASE_YAML:-$PROJECT_ROOT/.helix/phase.yaml}"
HELIX_DB_PATH="${HELIX_DB_PATH:-$DB_PATH}"
export HELIX_HOME PROJECT_ROOT PHASE_YAML HELIX_DB_PATH

helix_inject_hint() {
  local axis="${1:-}"
  local value="${2:-}"
  if [[ -z "$axis" ]]; then
    echo "[helix] エラー: helix_inject_hint requires axis" >&2
    return 2
  fi

  local normalized
  normalized="$(printf '%s' "$axis" | tr '[:lower:]-' '[:upper:]_' | tr -c 'A-Z0-9_' '_')"
  export "HELIX_${normalized}_HINT=$value"
}

helix_current_sprint() {
  local phase_yaml="${1:-$PHASE_YAML}"
  [[ -f "$phase_yaml" ]] || return 1

  awk '
    /^sprint:/ { in_sprint=1; next }
    /^[^[:space:]#][^:]*:/ { if (in_sprint) exit }
    in_sprint && /^[[:space:]]+current_step:/ {
      value=$2
      gsub(/["'\'']/, "", value)
      if (value != "" && value != "null") {
        print value
        found=1
      }
      exit
    }
    END { if (!found) exit 1 }
  ' "$phase_yaml"
}
