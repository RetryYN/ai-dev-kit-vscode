#!/bin/bash
# sync-codex-skills.sh — HELIX スキルを ~/.codex/skills/ にシンボリックリンク
#
# Usage: bash ~/ai-dev-kit-vscode/helix/sync-codex-skills.sh
#
# - 既存の helix-* リンクを削除してから再作成（冪等）
# - .system/ ディレクトリには触れない

set -euo pipefail

SKILLS_SRC="$HOME/ai-dev-kit-vscode/skills"
CODEX_SKILLS="$HOME/.codex/skills"

mkdir -p "$CODEX_SKILLS"

# 既存の helix- プレフィックスリンクを削除（冪等）
find "$CODEX_SKILLS" -maxdepth 1 -type l -name "helix-*" -delete

count=0

for category in common workflow project advanced tools integration; do
  dir="$SKILLS_SRC/$category"
  [ -d "$dir" ] || continue
  for skill_dir in "$dir"/*/; do
    [ -f "$skill_dir/SKILL.md" ] || continue
    name=$(basename "$skill_dir")
    ln -s "$skill_dir" "$CODEX_SKILLS/helix-$name"
    count=$((count + 1))
  done
done

echo "Synced $count HELIX skills to $CODEX_SKILLS (prefix: helix-)"
echo "Restart Codex to pick up new skills."
