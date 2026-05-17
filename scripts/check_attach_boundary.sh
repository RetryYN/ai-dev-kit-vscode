#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash scripts/check_attach_boundary.sh [--scope <path>]

Searches for ATTACH DATABASE under cli/ and fails on non-allowlisted hits.
EOF
}

SCOPE="cli"
ALLOWLIST_REGEX='(^|[./])cli/lib/compatibility_adapter\.py:'
PATTERN='ATTACH[[:space:]]+DATABASE'

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope)
      [[ $# -ge 2 ]] || {
        echo "Error: --scope requires a value" >&2
        usage >&2
        exit 2
      }
      SCOPE="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -e "$SCOPE" ]]; then
  echo "Error: scope not found: $SCOPE" >&2
  exit 2
fi

matches="$(grep -rniE --binary-files=without-match "$PATTERN" "$SCOPE" 2>/dev/null || true)"
violations=""
if [[ -n "$matches" ]]; then
  violations="$(printf '%s\n' "$matches" | grep -Ev "$ALLOWLIST_REGEX" || true)"
fi

if [[ -n "$violations" ]]; then
  echo "ATTACH DATABASE boundary violation detected:" >&2
  printf '%s\n' "$violations" >&2
  exit 1
fi

exit 0
