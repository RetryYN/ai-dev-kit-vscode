#!/bin/bash
set -eo pipefail
# H201: cli/roles 配下の全ロール dry-run がスキル注入+モデル選択+共通ドキュメント付きで正しく動くか

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"

echo "=== H201: Codex Role Dispatch ==="

ROLES=(tl se pg fe qa security dba devops docs research legacy perf)
EXPECTED_MODELS=(gpt-5.4 gpt-5.3-codex gpt-5.3-codex-spark gpt-5.4 gpt-5.4 gpt-5.4 gpt-5.3-codex gpt-5.3-codex gpt-5.3-codex-spark gpt-5.4 gpt-5.4 gpt-5.4)

for i in "${!ROLES[@]}"; do
  role="${ROLES[$i]}"
  expected_model="${EXPECTED_MODELS[$i]}"
  set +e
  out=$($CLI/helix-codex --role "$role" --task "test" --dry-run 2>&1)
  exit_code=$?
  set -e

  [[ $exit_code -eq 0 ]] || { echo "FAIL: $role dry-run exit=$exit_code"; exit 1; }
  echo "$out" | grep -q "Model:.*$expected_model" || { echo "FAIL: $role model (expected $expected_model)"; echo "$out" | grep Model; exit 1; }
  echo "$out" | grep -q "ROLE_MAP" || { echo "FAIL: $role missing ROLE_MAP.md"; exit 1; }
  echo "$out" | grep -q "Skills:" || { echo "FAIL: $role missing skills"; exit 1; }
done

# 不正ロール
set +e
$CLI/helix-codex --role invalid --task "test" --dry-run >/dev/null 2>&1
invalid_exit=$?
set -e
[[ $invalid_exit -ne 0 ]] || { echo "FAIL: invalid role should fail"; exit 1; }

# パストラバーサル
set +e
$CLI/helix-codex --role "../etc/passwd" --task "test" --dry-run >/dev/null 2>&1
trav_exit=$?
set -e
[[ $trav_exit -ne 0 ]] || { echo "FAIL: traversal should fail"; exit 1; }

echo "PASS: all roles + invalid + traversal"
