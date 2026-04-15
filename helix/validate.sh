#!/usr/bin/env bash
# HELIX セルフバリデーション — フレームワーク整合性チェック
# Usage: bash ~/ai-dev-kit-vscode/helix/validate.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$ROOT/skills"
ERRORS=0

red()   { printf '\033[0;31m%s\033[0m\n' "$1"; }
green() { printf '\033[0;32m%s\033[0m\n' "$1"; }
warn()  { printf '\033[0;33m%s\033[0m\n' "$1"; }

fail() { red "FAIL: $1"; ERRORS=$((ERRORS + 1)); }
pass() { green "PASS: $1"; }

echo "=== HELIX Self-Validation ==="
echo "Root: $ROOT"
echo ""

# 1. スキル数カウント
echo "--- 1. Skill Count ---"
ACTUAL_COUNT=$(find "$SKILLS_DIR" -name "SKILL.md" -not -path "*/archive/*" | wc -l | tr -d ' ')
README_COUNT=$(grep -oP '\d+ スキル' "$ROOT/README.md" | head -1 | grep -oP '\d+')
SKILLMAP_COUNT=$(grep -oP '（\K\d+(?=\s*スキル(?:\s*\+\s*Wave[^）]*)?）)' "$SKILLS_DIR/SKILL_MAP.md" | head -1)

if [ "$ACTUAL_COUNT" = "$README_COUNT" ]; then
  pass "README skill count matches ($ACTUAL_COUNT)"
else
  fail "README says $README_COUNT skills, found $ACTUAL_COUNT"
fi

if [ "$ACTUAL_COUNT" = "$SKILLMAP_COUNT" ]; then
  pass "SKILL_MAP skill count matches ($ACTUAL_COUNT)"
else
  fail "SKILL_MAP says $SKILLMAP_COUNT skills, found $ACTUAL_COUNT"
fi

# 2. SKILL.md metadata 必須フィールド
echo ""
echo "--- 2. Metadata Validation ---"
MISSING_META=0
while IFS= read -r skill_file; do
  for field in "name:" "description:" "helix_layer:"; do
    if ! grep -q "$field" "$skill_file"; then
      fail "$skill_file: missing $field"
      MISSING_META=$((MISSING_META + 1))
    fi
  done
done < <(find "$SKILLS_DIR" -name "SKILL.md" -not -path "*/archive/*")

if [ "$MISSING_META" -eq 0 ]; then
  pass "All SKILL.md files have required metadata"
fi

# 3. 廃止語検出
echo ""
echo "--- 3. Deprecated Term Detection ---"
DEPRECATED_TERMS=("orchestrator" "architecture" "vscode-plugins")
for term in "${DEPRECATED_TERMS[@]}"; do
  HITS=$(rg -n --glob '*.md' --glob '!SKILL_MAP.md' --glob '!**/archive/**' "$term" "$SKILLS_DIR" \
    2>/dev/null \
    | grep -v "architecture_decisions\|architecture:\|architectural\|architecture_identified\|architecture_style\|Architecture Decision\|information-architecture\|Information Architecture\|style:" \
    || true)
  if [ -n "$HITS" ]; then
    fail "Deprecated term '$term' found:"
    echo "$HITS" | head -5
  else
    pass "No deprecated term '$term'"
  fi
done

# codex as skill name (not as tool name)
CODEX_HITS=$(rg -n --glob '*.md' --glob '!SKILL_MAP.md' --glob '!**/archive/**' "\bcodex\b" "$SKILLS_DIR" \
  2>/dev/null \
  | grep -iv "codex exec\|codex review\|codex 5\.\|codex cli\|codex_\|codex系\|Codex（\|gpt-5\.\|codex: true\|codex-skills\|sync-codex\|\.codex/" \
  || true)
if [ -n "$CODEX_HITS" ]; then
  warn "Potential deprecated 'codex' as skill name (review manually):"
  echo "$CODEX_HITS" | head -5
else
  pass "No deprecated 'codex' as skill name"
fi

# 4. 相互参照整合性（references/ 内のファイル参照）
echo ""
echo "--- 4. Cross-Reference Integrity ---"
REF_DIR="$SKILLS_DIR/tools/ai-coding/references"
BROKEN_REFS=0

# Check references to other files within references/
for ref_file in "$REF_DIR"/*.md; do
  # Extract file references like `references/xxx.md` or `xxx.md`
  while IFS= read -r referenced; do
    # Skip naming convention templates (YYYY-MM-DD-*.md)
    if echo "$referenced" | grep -qP '^YYYY-'; then
      continue
    fi
    # Skip generic markdown terms that are not actual file references
    # (SKILL.md は「スキル本体ファイル」の一般名詞、CLAUDE.md も HELIX 全体の設定ファイル名)
    case "$referenced" in
      SKILL.md|CLAUDE.md|README.md|AGENTS.md|DESIGN.md|DESIGNER.md) continue ;;
    esac
    ref_path="$REF_DIR/$referenced"
    if [ ! -f "$ref_path" ]; then
      # Try relative to skills/
      ref_path2="$SKILLS_DIR/$referenced"
      if [ ! -f "$ref_path2" ]; then
        fail "$(basename "$ref_file"): references '$referenced' — not found"
        BROKEN_REFS=$((BROKEN_REFS + 1))
      fi
    fi
  done < <(grep -oP '`(?:references/)?(\w[\w-]+\.md)`' "$ref_file" | grep -oP '\w[\w-]+\.md' | sort -u)
done

if [ "$BROKEN_REFS" -eq 0 ]; then
  pass "All cross-references resolve"
fi

# 5. カテゴリ別スキル数の整合性
echo ""
echo "--- 5. Category Count Validation ---"
declare -A EXPECTED_COUNTS=(
  ["common"]=12
  ["workflow"]=18
  ["project"]=3
  ["advanced"]=6
  ["tools"]=2
  ["integration"]=1
)

for category in "${!EXPECTED_COUNTS[@]}"; do
  expected="${EXPECTED_COUNTS[$category]}"
  actual=$(find "$SKILLS_DIR/$category" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$actual" = "$expected" ]; then
    pass "$category/: $actual skills"
  else
    fail "$category/: expected $expected, found $actual"
  fi
done

# Summary
echo ""
echo "=== Summary ==="
if [ "$ERRORS" -eq 0 ]; then
  green "All checks passed!"
else
  red "$ERRORS error(s) found"
fi

exit "$ERRORS"
