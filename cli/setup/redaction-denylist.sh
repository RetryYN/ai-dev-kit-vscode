#!/usr/bin/env bash
set -euo pipefail

project_root() {
  printf '%s\n' "${HELIX_PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
}

denylist_path() {
  printf '%s/.helix/audit/redaction-denylist.example.yaml\n' "$(project_root)"
}

template() {
  cat <<'EOF'
# HELIX redaction denylist example.
# Keep this file free of real project secrets. Put project-local values in
# .helix/audit/redaction-denylist.local.yaml, which must remain ignored.
patterns:
  - name: generic_password
    regex: "(?i)password"
  - name: generic_api_key
    regex: "(?i)api[_-]?key"
  - name: generic_token
    regex: "(?i)token"
  - name: authorization_header
    regex: "(?i)authorization"
EOF
}

describe() {
  echo "Create PLAN-002 redaction denylist example for audit preflight"
}

verify() {
  local file
  file="$(denylist_path)"
  if [[ -f "$file" ]]; then
    echo "redaction denylist example exists: $file"
    return 0
  fi
  echo "redaction denylist example missing: $file" >&2
  return 1
}

install() {
  local file
  file="$(denylist_path)"
  if [[ -f "$file" ]]; then
    echo "redaction denylist example already exists: $file"
    return 0
  fi
  mkdir -p "$(dirname "$file")"
  template >"$file"
  chmod 0644 "$file"
  echo "created redaction denylist example: $file"
  return 0
}

repair() {
  if verify >/dev/null 2>&1; then
    echo "redaction denylist repair not needed"
    return 3
  fi
  install
}
