#!/usr/bin/env bash
set -euo pipefail

describe() {
  echo "Verify gitleaks is installed for PLAN-002 audit preflight"
}

verify() {
  if command -v gitleaks >/dev/null 2>&1; then
    gitleaks version
    return 0
  fi
  echo "gitleaks is not installed. Install gitleaks >= 8.18 before running audit preflight." >&2
  echo "Install examples: brew install gitleaks | apt install gitleaks | https://github.com/gitleaks/gitleaks/releases" >&2
  return 1
}

install() {
  if verify >/dev/null 2>&1; then
    echo "gitleaks already installed"
    return 0
  fi
  echo "Manual install required for gitleaks >= 8.18:" >&2
  echo "  macOS: brew install gitleaks" >&2
  echo "  Debian/Ubuntu: apt install gitleaks, or use the upstream release binary" >&2
  echo "  Upstream: https://github.com/gitleaks/gitleaks/releases" >&2
  return 1
}

repair() {
  install
}
