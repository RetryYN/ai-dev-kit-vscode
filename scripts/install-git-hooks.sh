#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash scripts/install-git-hooks.sh [--copy|--symlink]

Installs HELIX-managed pre-commit and pre-push hooks into the current repository.
Default mode is symlink when possible, otherwise copy.
EOF
}

install_mode="auto"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --copy)
      install_mode="copy"
      ;;
    --symlink)
      install_mode="symlink"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [[ "${CI:-}" == "true" ]]; then
  echo "CI 環境のため hook 配備をスキップ"
  exit 0
fi

if ! repo_root=$(git rev-parse --show-toplevel 2>/dev/null); then
  echo "Not inside a Git repository: $(pwd)" >&2
  exit 1
fi
repo_root=$(CDPATH= cd -- "$repo_root" && pwd)

hooks_dir=$(git -C "$repo_root" rev-parse --git-path hooks)
mkdir -p "$hooks_dir"

install_hook() {
  local name="$1"
  local src="$script_dir/git-hooks/$name"
  local dst="$hooks_dir/$name"
  local mode_used=""
  local backup="$dst.helix.bak"

  if [[ ! -f "$src" ]]; then
    echo "Missing hook source: $src" >&2
    exit 1
  fi

  if [[ -L "$dst" && "$(readlink "$dst")" == "$src" ]]; then
    mode_used="symlink"
  elif [[ -f "$dst" && -f "$src" ]] && cmp -s "$dst" "$src"; then
    mode_used="copy"
  elif [[ -e "$dst" ]]; then
    rm -f "$backup"
    mv "$dst" "$backup"
    echo "backed up existing $name hook to $backup"
  fi

  if [[ -z "$mode_used" ]]; then
    if [[ "$install_mode" != "copy" ]] && ln -sfn "$src" "$dst" 2>/dev/null; then
      mode_used="symlink"
    else
      cp "$src" "$dst"
      mode_used="copy"
    fi
  fi

  chmod +x "$src" "$dst" 2>/dev/null || true
  echo "installed $name via $mode_used -> $dst"
}

install_hook pre-commit
install_hook pre-push
