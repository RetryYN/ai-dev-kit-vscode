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
  HITS=$(rg -n --glob 'SKILL.md' --glob '!**/archive/**' "^name:[[:space:]]*$term$|^name:[[:space:]]*.*/$term$" "$SKILLS_DIR" 2>/dev/null || true)
  if [ -n "$HITS" ]; then
    fail "Deprecated skill name '$term' found:"
    echo "$HITS" | head -5
  else
    pass "No deprecated skill name '$term'"
  fi
done

# codex as skill name (not as tool name)
CODEX_HITS=$(rg -n --glob '*.md' --glob '!SKILL_MAP.md' --glob '!**/archive/**' "\bcodex\b" "$SKILLS_DIR" \
  2>/dev/null \
  | grep -iv "codex exec\|helix codex\|helix review\|codex 5\.\|codex cli\|codex_\|codex系\|Codex（\|gpt-5\.\|codex: true\|codex-skills\|codex-plugin-cc\|codex-review\|sync-codex\|\.codex/" \
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
      SKILL.md|CLAUDE.md|README.md|AGENTS.md|DESIGN.md|DESIGNER.md|state-events.md) continue ;;
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
  ["workflow"]=31
  ["project"]=8
  ["advanced"]=6
  ["tools"]=4
  ["integration"]=1
  ["writing"]=5
  ["design-tools"]=5
  ["automation"]=8
  ["agent-skills"]=25
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

# 6. 正本系 Markdown のローカルリンク整合性
echo ""
echo "--- 6. Markdown Link Validation ---"
LINK_ERRORS=0
LINK_TARGETS=(
  "$ROOT/README.md"
  "$ROOT/CLAUDE.md"
  "$ROOT/AGENTS.md"
  "$ROOT/docs/adr"
  "$ROOT/docs/backlog"
  "$ROOT/docs/commands"
  "$ROOT/docs/design"
  "$ROOT/docs/requirements"
  "$ROOT/docs/roadmap"
  "$ROOT/docs/specs"
  "$ROOT/docs/quickstart.md"
  "$ROOT/docs/security-guidelines.md"
  "$ROOT/docs/setup-guide.md"
)

while IFS= read -r md_file; do
  md_dir="$(dirname "$md_file")"
  while IFS= read -r target; do
    target="${target#<}"
    target="${target%>}"
    target="${target%%[[:space:]]\"*}"

    if [[ "$target" == http://* || "$target" == https://* || "$target" == mailto:* || "$target" == app://* || "$target" == plugin://* || "$target" == \#* || "$target" == javascript:* || "$target" == *://* ]]; then
      continue
    fi

    target="${target%%#*}"
    target="${target%%\?*}"
    [ -z "$target" ] && continue

    # Runtime artifacts are generated per project/session and are not stable repo docs.
    if [[ "$target" == .helix/* || "$target" == /.helix/* ]]; then
      continue
    fi

    if [[ "$target" == /* ]]; then
      candidate="$ROOT$target"
    else
      candidate="$md_dir/$target"
    fi

    if [ ! -e "$candidate" ]; then
      fail "${md_file#$ROOT/}: broken link '$target'"
      LINK_ERRORS=$((LINK_ERRORS + 1))
    fi
  done < <(perl -ne 'while(/!?\[[^\]]+\]\(([^)]+)\)/g){print "$1\n"}' "$md_file")
done < <(
  for target in "${LINK_TARGETS[@]}"; do
    if [ -f "$target" ]; then
      printf '%s\n' "$target"
    elif [ -d "$target" ]; then
      find "$target" -name '*.md' -not -path '*/archive/*'
    fi
  done | sort -u
)

if [ "$LINK_ERRORS" -eq 0 ]; then
  pass "Core markdown local links resolve"
fi

# 7. Active docs の unresolved placeholder 検出
echo ""
echo "--- 7. Active Docs Placeholder Validation ---"
PLACEHOLDER_ERRORS=0
while IFS= read -r doc_file; do
  hits=$(rg -n -P 'TODO|FIXME|TBD|要確認|未定(?!義)' "$doc_file" 2>/dev/null || true)
  if [ -n "$hits" ]; then
    fail "${doc_file#$ROOT/}: unresolved placeholder found"
    echo "$hits" | head -5
    PLACEHOLDER_ERRORS=$((PLACEHOLDER_ERRORS + 1))
  fi
done < <(
  find "$ROOT/docs" -name '*.md' \
    -not -path "$ROOT/docs/archive/*" \
    -not -path "$ROOT/docs/plans/*" \
    -not -path "$ROOT/docs/proposals/*" \
    -not -path "$ROOT/docs/agent-skills/*"
)

if [ "$PLACEHOLDER_ERRORS" -eq 0 ]; then
  pass "Active docs have no unresolved TODO/FIXME/TBD markers"
fi

# 8. コマンド route/help/docs 同期検証
echo ""
echo "--- 8. Command Catalog Validation ---"
if "$ROOT/cli/helix" commands check >/tmp/helix-command-catalog-check.log 2>&1; then
  pass "Command route/help/docs catalog is consistent"
else
  fail "Command route/help/docs catalog mismatch"
  cat /tmp/helix-command-catalog-check.log
fi

# Summary
echo ""
echo "=== Summary ==="
if [ "$ERRORS" -eq 0 ]; then
  green "All checks passed!"
else
  red "$ERRORS error(s) found"
fi

exit "$ERRORS"
