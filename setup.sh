#!/bin/bash
# setup.sh — HELIX フレームワーク ワンライナーセットアップ
#
# Usage:
#   bash ~/ai-dev-kit-vscode/setup.sh              # インストール
#   bash ~/ai-dev-kit-vscode/setup.sh --uninstall   # アンインストール
#
# クローン後に1回実行すれば Claude Code + Codex CLI の設定が完了する。

set -euo pipefail

# --- 定数 ---
HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLAUDE_DIR="$HOME/.claude"
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
CLAUDE_SETTINGS="$CLAUDE_DIR/settings.json"
MERGE_SCRIPT="$HELIX_HOME/cli/lib/merge_settings.py"
CODEX_BIN="${CODEX_BIN:-$(command -v codex 2>/dev/null || echo "")}"

IMPORT_SKILL="@~/ai-dev-kit-vscode/skills/SKILL_MAP.md"
IMPORT_CORE="@~/ai-dev-kit-vscode/helix/HELIX_CORE.md"

# --- ヘルパー ---
ok=0; skip=0; warn=0; fail=0

_ok()   { echo "  [OK]   $1"; ok=$((ok+1)); }
_skip() { echo "  [SKIP] $1"; skip=$((skip+1)); }
_warn() { echo "  [WARN] $1"; warn=$((warn+1)); }
_fail() { echo "  [FAIL] $1"; fail=$((fail+1)); }

# --- 依存チェック ---
check_deps() {
    echo "=== Dependency Check ==="

    # bash 4+
    if [[ "${BASH_VERSINFO[0]}" -ge 4 ]]; then
        _ok "bash ${BASH_VERSION}"
    else
        _fail "bash 4.0+ required (found ${BASH_VERSION})"
    fi

    # python3
    if command -v python3 &>/dev/null; then
        local pyver
        pyver=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        _ok "python3 $pyver"
    else
        _fail "python3 not found — install Python 3.6+"
    fi

    # git
    if command -v git &>/dev/null; then
        _ok "git $(git --version | cut -d' ' -f3)"
    else
        _fail "git not found"
    fi

    # sqlite3 CLI (optional)
    if command -v sqlite3 &>/dev/null; then
        _ok "sqlite3 CLI"
    else
        _warn "sqlite3 CLI not found — helix debug requires it"
    fi

    # codex (optional)
    if [[ -n "$CODEX_BIN" ]]; then
        _ok "codex CLI ($CODEX_BIN)"
    else
        _warn "codex CLI not found — Codex delegation will be unavailable"
    fi

    echo ""
}

# --- CLAUDE.md セットアップ ---
setup_claude_md() {
    echo "=== ~/.claude/CLAUDE.md ==="

    mkdir -p "$CLAUDE_DIR"

    if [[ ! -f "$CLAUDE_MD" ]]; then
        cat > "$CLAUDE_MD" <<EOF
# Global Settings

$IMPORT_SKILL
$IMPORT_CORE
EOF
        _ok "Created $CLAUDE_MD"
        return
    fi

    # 既存ファイルに追記（重複チェック）
    local added=0
    if ! grep -qF "$IMPORT_SKILL" "$CLAUDE_MD"; then
        echo "" >> "$CLAUDE_MD"
        echo "$IMPORT_SKILL" >> "$CLAUDE_MD"
        added=$((added+1))
    fi
    if ! grep -qF "$IMPORT_CORE" "$CLAUDE_MD"; then
        echo "$IMPORT_CORE" >> "$CLAUDE_MD"
        added=$((added+1))
    fi

    if [[ $added -gt 0 ]]; then
        _ok "Added $added import(s) to $CLAUDE_MD"
    else
        _skip "Imports already present in $CLAUDE_MD"
    fi

    echo ""
}

# --- settings.json セットアップ ---
setup_settings() {
    echo "=== ~/.claude/settings.json ==="

    mkdir -p "$CLAUDE_DIR"

    # バックアップ
    if [[ -f "$CLAUDE_SETTINGS" ]]; then
        cp "$CLAUDE_SETTINGS" "${CLAUDE_SETTINGS}.bak"
        _ok "Backup → ${CLAUDE_SETTINGS}.bak"
    fi

    # マージ（merge_settings.py の終了コード: 0=変更あり, 1=変更なし）
    if python3 "$MERGE_SCRIPT" "$CLAUDE_SETTINGS"; then
        _ok "HELIX hooks merged into $CLAUDE_SETTINGS"
    else
        _skip "HELIX hooks already present in $CLAUDE_SETTINGS"
    fi

    echo ""
}

# --- シェル PATH セットアップ ---
setup_shell_path() {
    echo "=== Shell PATH ==="

    local path_line="export PATH=\"\$HOME/ai-dev-kit-vscode/cli:\$PATH\""
    local marker="ai-dev-kit-vscode/cli"
    local added=false

    for rcfile in "$HOME/.bashrc" "$HOME/.zshrc"; do
        if [[ ! -f "$rcfile" ]]; then
            continue
        fi

        if grep -qF "$marker" "$rcfile"; then
            _skip "PATH already in $(basename "$rcfile")"
        else
            echo "" >> "$rcfile"
            echo "# HELIX Framework" >> "$rcfile"
            echo "$path_line" >> "$rcfile"
            _ok "PATH added to $(basename "$rcfile")"
            added=true
        fi
    done

    # bashrc も zshrc も無い場合は bashrc を作る
    if [[ ! -f "$HOME/.bashrc" ]] && [[ ! -f "$HOME/.zshrc" ]]; then
        echo "# HELIX Framework" > "$HOME/.bashrc"
        echo "$path_line" >> "$HOME/.bashrc"
        _ok "Created .bashrc with PATH"
        added=true
    fi

    if [[ "$added" == true ]]; then
        _warn "Run 'source ~/.bashrc' or restart shell to apply"
    fi

    echo ""
}

# --- Codex CLI セットアップ ---
setup_codex() {
    echo "=== Codex CLI ==="

    if [[ -z "$CODEX_BIN" ]]; then
        _skip "Codex CLI not found, skipping"
        echo ""
        return
    fi

    # symlink
    if bash "$HELIX_HOME/helix/sync-codex-skills.sh" 2>/dev/null; then
        _ok "Skill symlinks synced"
    else
        _warn "sync-codex-skills.sh failed"
    fi

    # AGENTS.md
    local agents_md="$HOME/.codex/AGENTS.md"
    local agents_example="$HELIX_HOME/helix/AGENTS.md.example"
    if [[ ! -f "$agents_md" ]] && [[ -f "$agents_example" ]]; then
        mkdir -p "$HOME/.codex"
        cp "$agents_example" "$agents_md"
        _ok "Copied AGENTS.md → $agents_md"
    else
        _skip "AGENTS.md already exists or template not found"
    fi

    echo ""
}

# --- アンインストール ---
uninstall() {
    echo "=== HELIX Uninstall ==="

    # CLAUDE.md から @import 行を削除
    if [[ -f "$CLAUDE_MD" ]]; then
        local tmp="${CLAUDE_MD}.tmp"
        grep -vF "ai-dev-kit-vscode" "$CLAUDE_MD" > "$tmp" || true
        mv "$tmp" "$CLAUDE_MD"
        _ok "Removed HELIX imports from $CLAUDE_MD"
    else
        _skip "$CLAUDE_MD not found"
    fi

    # settings.json から HELIX hooks を除去
    if [[ -f "$CLAUDE_SETTINGS" ]]; then
        cp "$CLAUDE_SETTINGS" "${CLAUDE_SETTINGS}.bak"
        if python3 "$MERGE_SCRIPT" "$CLAUDE_SETTINGS" --remove; then
            _ok "Removed HELIX hooks from $CLAUDE_SETTINGS"
        else
            _skip "No HELIX hooks found in $CLAUDE_SETTINGS"
        fi
    else
        _skip "$CLAUDE_SETTINGS not found"
    fi

    # Shell PATH
    for rcfile in "$HOME/.bashrc" "$HOME/.zshrc"; do
        if [[ -f "$rcfile" ]] && grep -qF "ai-dev-kit-vscode/cli" "$rcfile"; then
            local tmp="${rcfile}.tmp"
            grep -vF "ai-dev-kit-vscode/cli" "$rcfile" | grep -v "^# HELIX Framework$" > "$tmp" || true
            mv "$tmp" "$rcfile"
            _ok "Removed PATH from $(basename "$rcfile")"
        fi
    done

    # Codex symlinks
    local codex_skills="$HOME/.codex/skills"
    if [[ -d "$codex_skills" ]]; then
        find "$codex_skills" -maxdepth 1 -type l -name "helix-*" -delete 2>/dev/null
        _ok "Removed Codex skill symlinks"
    else
        _skip "Codex skills directory not found"
    fi

    echo ""
    echo "HELIX uninstalled. Repository is still at $HELIX_HOME"
    echo ""
}

# --- サマリー ---
summary() {
    echo "=== Summary ==="
    echo ""

    if [[ $fail -gt 0 ]]; then
        echo "  Setup completed with errors ($fail failure(s))."
        echo "  Fix the issues above and re-run: bash $HELIX_HOME/setup.sh"
    else
        echo "  HELIX setup complete!"
        echo "    Claude Code: ready (hooks installed)"
        if [[ -n "$CODEX_BIN" ]]; then
            echo "    Codex CLI:   ready"
        else
            echo "    Codex CLI:   not installed (skipped)"
        fi
        echo ""
        echo "  Run 'helix init' in any project to get started."
    fi

    echo ""
}

# --- メイン ---
main() {
    echo ""
    echo "  HELIX Framework Setup"
    echo "  ====================="
    echo ""

    if [[ "${1:-}" == "--uninstall" ]]; then
        uninstall
        summary
        exit 0
    fi

    if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
        echo "Usage: bash $HELIX_HOME/setup.sh [--uninstall]"
        echo ""
        echo "  --uninstall   Remove HELIX hooks and imports"
        echo "  --help        Show this help"
        exit 0
    fi

    check_deps

    # 必須依存が欠けていたら中断
    if [[ $fail -gt 0 ]]; then
        echo "Required dependencies missing. Aborting."
        exit 1
    fi

    setup_claude_md
    setup_settings
    setup_shell_path
    setup_codex
    summary
}

main "$@"
