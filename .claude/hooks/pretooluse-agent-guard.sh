#!/usr/bin/env bash
# Claude Code PreToolUse hook (matcher=Agent) — subagent guard
#
# CLAUDE.md v2.2 (2026-05-15 改訂) の Agent tool ルールを fail-close で強制:
# 1. subagent_type が PMO + PdM 12 種許可リスト内であること
# 2. tool_input.model が明示指定されていること (haiku / sonnet / opus)
# 3. subagent definition (.claude/agents/<name>.md) の effort frontmatter
#    定義状態を warn (block しない、optional 推奨)
#
# 設計: 既存 pretooluse-agent-fire.sh (記録専用) と並列で動かす想定。
#       本 hook が先 (block 可能)、fire が後 (記録、blockOnFailure: false)。
#
# Exit codes:
#   0 — pass
#   2 — block (Claude Code が tool 呼び出しを抑止)
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT" || exit 0

input=$(cat 2>/dev/null || echo "{}")

# tool_name 抽出
tool_name=$(printf '%s' "$input" | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get("tool_name", ""))
except Exception:
    print("")
' 2>/dev/null || echo "")

# Agent tool 以外は通過
[[ "$tool_name" != "Agent" ]] && exit 0

# subagent_type + model 抽出 (改行区切りで安全に)
extracted=$(printf '%s' "$input" | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
    ti = d.get("tool_input", {}) or {}
    st = (ti.get("subagent_type") or "").strip()
    m = (ti.get("model") or "").strip()
    print(st)
    print(m or "_NONE_")
except Exception:
    print("")
    print("_NONE_")
' 2>/dev/null || printf "\n_NONE_\n")

subagent_type=$(printf '%s' "$extracted" | sed -n '1p')
model=$(printf '%s' "$extracted" | sed -n '2p')

# 許可リスト (PMO 9 + PdM 3 = 12 件)
ALLOW_LIST=(
  "pmo-sonnet" "pmo-haiku"
  "pmo-helix-explorer" "pmo-helix-scout"
  "pmo-project-explorer" "pmo-project-scout"
  "pmo-tech-docs" "pmo-tech-fork" "pmo-tech-news"
  "pdm-tech-innovation" "pdm-marketing-innovation" "pdm-innovation-manager"
)
allow_str="${ALLOW_LIST[*]}"

# subagent_type 不在 (= Claude Code default の general-purpose 等) は block
if [[ -z "$subagent_type" ]]; then
  cat >&2 <<EOF
[helix-guard] BLOCK: Agent tool 呼び出しに subagent_type が指定されていません。
CLAUDE.md v2.2 ルール「Agent tool は PMO + PdM 限定許可」により、
subagent_type 未指定 (= general-purpose 等の default 経路) は禁止です。

許可された subagent_type:
  ${allow_str}

代替:
  - 軽量タスク → Opus / Sonnet 直接対応
  - 実装系 → helix codex --role <role> --task "..."

ロックを bypass する正当理由がある場合は HELIX_ALLOW_RAW_AGENT=1 を
明示し、その理由を会話または final report に記録してください。
EOF
  if [[ "${HELIX_ALLOW_RAW_AGENT:-0}" == "1" ]]; then
    echo "[helix-guard] WARN: HELIX_ALLOW_RAW_AGENT=1 で bypass。理由を evidence に残してください。" >&2
    exit 0
  fi
  exit 2
fi

# 許可リスト判定
allowed=false
for a in "${ALLOW_LIST[@]}"; do
  if [[ "$subagent_type" == "$a" ]]; then
    allowed=true
    break
  fi
done

if ! $allowed; then
  cat >&2 <<EOF
[helix-guard] BLOCK: subagent_type=${subagent_type} は許可リスト外です。
CLAUDE.md v2.2 (2026-05-15 改訂) により、Agent tool は PMO + PdM 12 種のみ許可。

許可された subagent_type:
  ${allow_str}

禁止理由:
  be-api / be-logic / db-schema / qa-test / security-audit / code-reviewer /
  devops-deploy / general-purpose / Explore / Plan 等は Opus 直接 or Codex 委譲で対応する規約。

代替:
  - 設計・実装 → helix codex --role <tl|se|pe|qa|security|dba|devops|docs|research|legacy|perf> --task "..."
  - PMO 系 → Agent({subagent_type: "pmo-sonnet"}, ...)  (許可)

ロックを bypass する正当理由がある場合は HELIX_ALLOW_RAW_AGENT=1 を
明示し、その理由を会話または final report に記録してください。
EOF
  if [[ "${HELIX_ALLOW_RAW_AGENT:-0}" == "1" ]]; then
    echo "[helix-guard] WARN: HELIX_ALLOW_RAW_AGENT=1 で bypass。理由を evidence に残してください (subagent_type=${subagent_type})。" >&2
    exit 0
  fi
  exit 2
fi

# model 指定チェック (許可リスト内でも model 必須)
if [[ "$model" == "_NONE_" || -z "$model" ]]; then
  cat >&2 <<EOF
[helix-guard] BLOCK: subagent_type=${subagent_type} 呼び出しに model 指定がありません。
CLAUDE.md ルール「禁止: Agent tool を model 指定なしで呼ぶこと」。

許可される model:
  haiku / sonnet / opus

正しい呼び出し例:
  Agent({
    subagent_type: "${subagent_type}",
    model: "sonnet",
    description: "...",
    prompt: "..."
  })

ロックを bypass する正当理由がある場合は HELIX_ALLOW_RAW_AGENT=1 を
明示し、その理由を会話または final report に記録してください。
EOF
  if [[ "${HELIX_ALLOW_RAW_AGENT:-0}" == "1" ]]; then
    echo "[helix-guard] WARN: HELIX_ALLOW_RAW_AGENT=1 で model 未指定を bypass。理由を evidence に残してください。" >&2
    exit 0
  fi
  exit 2
fi

# effort frontmatter チェック (warn のみ、block しない)
agent_md=".claude/agents/${subagent_type}.md"
if [[ -f "$agent_md" ]]; then
  effort=$(python3 -c "
import re
with open('$agent_md') as f:
    content = f.read()
m = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
if not m:
    print('_NONE_')
else:
    fm = m.group(1)
    em = re.search(r'^effort:\s*(\S+)', fm, re.MULTILINE)
    print(em.group(1) if em else '_NONE_')
" 2>/dev/null || echo "_NONE_")

  if [[ "$effort" == "_NONE_" ]]; then
    cat >&2 <<EOF
[helix-guard] WARN: subagent_type=${subagent_type} の definition (${agent_md}) に
effort frontmatter が未定義です。
推奨値: high (be-api / be-logic / code-reviewer / db-schema / devops-deploy /
security-audit) または medium (qa-test / legacy / perf)。
警告のみ、block しません。
EOF
  fi
fi

exit 0
