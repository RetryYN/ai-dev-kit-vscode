#!/usr/bin/env bash
# A0 Discovery: candidate file inventory + metadata collection.
# This script is intentionally non-destructive.

set -euo pipefail

project_root() {
  printf '%s\n' "${HELIX_PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
}

describe() {
  echo "A0 Discovery: candidate file inventory and metadata collection"
}

verify() {
  command -v gitleaks >/dev/null 2>&1
}

install() {
  echo "A0 discovery is install-free (uses git + standard tools)"
  return 0
}

repair() {
  echo "A0 discovery is stateless; repair not applicable"
  return 3
}

_timestamp() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

_epoch() {
  date +%s
}

_script_hash() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$0" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$0" | awk '{print $1}'
  else
    echo "sha256-unavailable"
  fi
}

_head_sha() {
  git rev-parse HEAD 2>/dev/null || echo "no-git"
}

discover() {
  local root epoch output_path raw_path raw_dir gitleaks_summary report_path
  root="$(project_root)"
  epoch="$(_epoch)"
  output_path="${1:-$root/.helix/audit/inventory-summary-${epoch}.log}"
  raw_path="${2:-${HOME}/.helix/quarantine/inventory-run-${epoch}.log}"
  raw_dir="$(dirname "$raw_path")"

  mkdir -p "$(dirname "$output_path")" "$raw_dir"
  chmod 700 "$raw_dir" 2>/dev/null || true

  (
    cd "$root"
    {
      echo "## inventory-run"
      echo "head_sha: $(_head_sha)"
      echo "script_hash: $(_script_hash)"
      echo "started_at: $(_timestamp)"
      echo ""
      echo "## tracked files (git ls-files)"
      git ls-files 2>/dev/null | head -1000
      echo ""
      echo "## untracked (excluding .gitignore)"
      git ls-files --others --exclude-standard 2>/dev/null | head -200
    } >"$raw_path"
  )
  chmod 600 "$raw_path" 2>/dev/null || true

  gitleaks_summary="gitleaks unavailable"
  if command -v gitleaks >/dev/null 2>&1; then
    report_path="${raw_dir}/gitleaks-report-${epoch}.json"
    set +e
    gitleaks_summary=$(
      cd "$root" &&
        gitleaks detect --no-banner --redact --report-format json --report-path "$report_path" 2>&1 |
          tail -10
    )
    local gitleaks_rc=$?
    set -e
    chmod 600 "$report_path" 2>/dev/null || true
    if [[ -z "$gitleaks_summary" ]]; then
      if [[ $gitleaks_rc -eq 0 ]]; then
        gitleaks_summary="no leaks detected"
      else
        gitleaks_summary="gitleaks exited with status ${gitleaks_rc}"
      fi
    fi
  fi

  (
    cd "$root"
    {
      echo "## inventory-summary"
      echo "head_sha: $(_head_sha)"
      echo "tracked_count: $(git ls-files 2>/dev/null | wc -l | tr -d ' ')"
      echo "untracked_count: $(git ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')"
      echo "gitleaks_summary: $(printf '%s\n' "$gitleaks_summary" | head -3 | tr '\n' ' ' | sed 's/[[:space:]]*$//')"
      echo "completed_at: $(_timestamp)"
    } >"$output_path"
  )

  echo "raw: $raw_path"
  echo "summary: $output_path"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  case "${1:-}" in
    verify) verify; exit $? ;;
    install) install; exit $? ;;
    repair) repair; exit $? ;;
    describe) describe; exit 0 ;;
    discover) shift; discover "$@" ;;
    *) echo "Usage: $0 {verify|install|repair|describe|discover [output_path] [raw_path]}" >&2; exit 2 ;;
  esac
fi
