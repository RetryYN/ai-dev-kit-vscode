#!/usr/bin/env bash

# Source from bats setup() to mark TMP_ROOT as HELIX-managed
helix_bats_mark() {
  local target="${1:-$TMP_ROOT}"
  if [[ -d "$target" ]]; then
    echo 'helix-bats-managed' > "$target/.bats-helix-marker" 2>/dev/null || true
  fi
}
