#!/usr/bin/env bash
set -euo pipefail

project_root() {
  printf '%s\n' "${HELIX_PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
}

gitignore_path() {
  printf '%s/.gitignore\n' "$(project_root)"
}

required_entries() {
  cat <<'EOF'
# HELIX audit preflight artifacts
!**/.helix/audit/
!**/.helix/audit/redaction-denylist.example.yaml
**/.helix/audit/redaction-denylist.local.yaml
**/.helix/audit/inventory-run-*.log
**/.helix/audit/runs/
**/.helix/audit/runs/**
EOF
}

describe() {
  echo "Ensure .gitignore protects HELIX audit runtime artifacts"
}

missing_entries() {
  local file
  file="$(gitignore_path)"
  while IFS= read -r entry; do
    [[ -z "$entry" ]] && continue
    if [[ ! -f "$file" ]] || ! grep -Fxq "$entry" "$file"; then
      printf '%s\n' "$entry"
    fi
  done < <(required_entries)
}

verify() {
  local missing
  missing="$(missing_entries)"
  if [[ -z "$missing" ]]; then
    echo ".gitignore contains HELIX audit preflight entries"
    return 0
  fi
  echo "missing .gitignore entries:" >&2
  printf '%s\n' "$missing" >&2
  return 1
}

install() {
  local file missing
  file="$(gitignore_path)"
  missing="$(missing_entries)"
  if [[ -z "$missing" ]]; then
    echo ".gitignore already contains HELIX audit preflight entries"
    return 0
  fi
  mkdir -p "$(dirname "$file")"
  touch "$file"
  {
    printf '\n'
    printf '%s\n' "$missing"
  } >>"$file"
  echo "updated .gitignore with HELIX audit preflight entries"
  return 0
}

repair() {
  if verify >/dev/null 2>&1; then
    echo ".gitignore repair not needed"
    return 3
  fi
  install
}
