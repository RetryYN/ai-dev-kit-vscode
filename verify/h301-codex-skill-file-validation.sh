#!/bin/bash
set -eo pipefail
# H301: cli/roles 配下の全ロール .conf のスキル・共通ドキュメントが実在するか

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
ROLES_DIR="$CLI/roles"
SKILLS_DIR="$HELIX_HOME/skills"

echo "=== H301: Codex Skill File Validation ==="

for conf in "$ROLES_DIR"/*.conf; do
  role=$(basename "$conf" .conf)
  # skills
  in_skills=false
  while IFS= read -r line; do
    [[ "$line" == "skills=(" ]] && in_skills=true && continue
    [[ "$in_skills" == true && "$line" == ")" ]] && break
    if [[ "$in_skills" == true ]]; then
      skill=$(echo "$line" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
      [[ -z "$skill" ]] && continue
      [[ -f "$SKILLS_DIR/$skill/SKILL.md" ]] || { echo "FAIL: $role → $skill/SKILL.md not found"; exit 1; }
    fi
  done < "$conf"
  # common_docs
  in_docs=false
  while IFS= read -r line; do
    [[ "$line" == "common_docs=(" ]] && in_docs=true && continue
    [[ "$in_docs" == true && "$line" == ")" ]] && break
    if [[ "$in_docs" == true ]]; then
      doc=$(echo "$line" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
      [[ -z "$doc" ]] && continue
      [[ -f "$HELIX_HOME/$doc" ]] || { echo "FAIL: $role → $doc not found"; exit 1; }
    fi
  done < "$conf"
done
echo "PASS: all roles' skills and docs exist"
