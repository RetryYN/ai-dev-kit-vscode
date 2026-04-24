#!/bin/bash
set -euo pipefail

REMOTE="upstream"
REMOTE_REF=""
AUTO_YES=false
PATHSPEC="skills/agent-skills/**/SKILL.md"
RISK_PATTERN='^\+[^+].*(system:|ignore previous|run bash|bash -c|curl .*\| *sh|rm -rf|developer message|tool call|sudo )'

usage() {
  echo "Usage: scripts/review-upstream-sync.sh [--remote <name>] [--ref <ref>] [--yes]"
  echo ""
  echo "Fetch upstream changes, show SKILL.md diffs, warn on risky prompt text, and pause before merge."
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote)
      REMOTE="$2"
      shift 2
      ;;
    --ref)
      REMOTE_REF="$2"
      shift 2
      ;;
    --yes)
      AUTO_YES=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "[review-upstream-sync] git worktree ではありません" >&2
  exit 1
fi

if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
  echo "[review-upstream-sync] remote が見つかりません: $REMOTE" >&2
  exit 1
fi

fetch_args=("$REMOTE")
if [[ -n "$REMOTE_REF" ]]; then
  fetch_args+=("$REMOTE_REF")
fi

echo "[review-upstream-sync] fetch: ${fetch_args[*]}" >&2
git fetch "${fetch_args[@]}"

diff_output="$(git diff --color=always HEAD..FETCH_HEAD -- "$PATHSPEC" || true)"
plain_diff="$(git diff HEAD..FETCH_HEAD -- "$PATHSPEC" || true)"

if [[ -n "$diff_output" ]]; then
  printf '%s\n' "$diff_output"
else
  echo "[review-upstream-sync] skills/agent-skills の SKILL.md 差分はありません"
fi

risk_hits="$(printf '%s\n' "$plain_diff" | grep -Ein "$RISK_PATTERN" || true)"
if [[ -n "$risk_hits" ]]; then
  echo "[review-upstream-sync] WARN: prompt injection 痕跡の可能性を検出しました" >&2
  printf '%s\n' "$risk_hits" >&2
fi

if [[ "$AUTO_YES" != true ]]; then
  echo "[review-upstream-sync] PAUSE: diff を人間が確認するまで merge しません" >&2
  echo "[review-upstream-sync] 続行する場合は --yes を付けて再実行してください" >&2
  exit 2
fi

git merge --ff-only FETCH_HEAD
echo "[review-upstream-sync] FETCH_HEAD をマージしました"
