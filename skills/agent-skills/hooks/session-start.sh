#!/bin/bash
# agent-skills session start hook
# Injects the using-agent-skills meta-skill into every new session

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$(dirname "$SCRIPT_DIR")/skills"
META_SKILL="$SKILLS_DIR/using-agent-skills/SKILL.md"
HELIX_HOME="$HOME/ai-dev-kit-vscode"

json_escape() {
  local s="$1"
  s=${s//\\/\\\\}
  s=${s//\"/\\\"}
  s=${s//$'\n'/\\n}
  s=${s//$'\r'/\\r}
  s=${s//$'\t'/\\t}
  printf '%s' "$s"
}

if [ -f "$META_SKILL" ]; then
  CONTENT="$(cat "$META_SKILL")"
  MESSAGE="agent-skills loaded. Use the skill discovery flowchart to find the right skill for your task.

$CONTENT"

  if [ -d "$HELIX_HOME" ]; then
    HELIX_VERSION="dev"
    if [ -f "$HELIX_HOME/VERSION" ]; then
      HELIX_VERSION="$(head -n 1 "$HELIX_HOME/VERSION")"
      HELIX_VERSION="${HELIX_VERSION:-dev}"
    fi

    MESSAGE="$MESSAGE

HELIX integration detected:
- HELIX home: $HELIX_HOME
- HELIX version: $HELIX_VERSION
- HELIX CLI commands: helix init / codex / gate / size / sprint / pr / scrum / reverse / skill
- Skill recommendation: use helix skill search '<task>' for auto-suggested skills"
  fi

  ESCAPED_MESSAGE="$(json_escape "$MESSAGE")"
  cat <<EOF
{
  "priority": "IMPORTANT",
  "message": "$ESCAPED_MESSAGE"
}
EOF
else
  echo '{"priority": "INFO", "message": "agent-skills: using-agent-skills meta-skill not found. Skills may still be available individually."}'
fi
