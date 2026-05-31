#!/bin/bash
# setup.sh — HELIX フレームワーク ワンライナーセットアップ
#
# Usage:
#   bash /path/to/ai-dev-kit-vscode/setup.sh               # インストール
#   bash /path/to/ai-dev-kit-vscode/setup.sh --uninstall   # アンインストール
#
# クローン後に1回実行すれば Claude Code + Codex CLI の設定が完了する。

set -euo pipefail

# --- 定数 ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELIX_HOME="${HELIX_HOME:-$SCRIPT_DIR}"
HELIX_CORE_LINK="$HOME/.helix/core"
CLAUDE_DIR="$HOME/.claude"
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
CLAUDE_SETTINGS="$CLAUDE_DIR/settings.json"
MERGE_SCRIPT="$HELIX_HOME/cli/lib/merge_settings.py"
CODEX_BIN="${CODEX_BIN:-$(command -v codex 2>/dev/null || echo "")}"
CODEX_DIR="$HOME/.codex"
CODEX_AGENTS="$CODEX_DIR/AGENTS.md"
CODEX_CONFIG="$CODEX_DIR/config.toml"
CODEX_HELIX_COMMENT="# HELIX: サンドボックス内に LANG/LC_ALL を継承（Windows/WSL 文字化け対策）"

ok=0; skip=0; warn=0; fail=0

_ok()   { echo "  [OK]   $1"; ok=$((ok+1)); }
_skip() { echo "  [SKIP] $1"; skip=$((skip+1)); }
_warn() { echo "  [WARN] $1"; warn=$((warn+1)); }
_fail() { echo "  [FAIL] $1"; fail=$((fail+1)); }

CORE_MANIFEST="$HELIX_HOME/helix/core-manifest.tsv"
CORE_IMPORTS=()
LEGACY_CLAUDE_IMPORTS=(
    "@~/ai-dev-kit-vscode/skills/SKILL_MAP.md"
    "@~/ai-dev-kit-vscode/helix/HELIX_CORE.md"
)

load_core_imports() {
    CORE_IMPORTS=()

    if [[ ! -r "$CORE_MANIFEST" ]]; then
        _fail "core manifest not found or unreadable: $CORE_MANIFEST"
        return 1
    fi

    local line scope import_path extra
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "${line//[[:space:]]/}" ]] && continue
        [[ "$line" =~ ^[[:space:]]*# ]] && continue

        IFS=$'\t' read -r scope import_path extra <<< "$line"
        if [[ -z "$scope" || -z "$import_path" || -n "$extra" ]]; then
            _fail "invalid core manifest row: $line"
            return 1
        fi

        if [[ "$scope" == "common" || "$scope" == "claude" ]]; then
            CORE_IMPORTS+=("$import_path")
        fi
    done < "$CORE_MANIFEST"

    if [[ "${#CORE_IMPORTS[@]}" -eq 0 ]]; then
        _fail "core manifest produced no Claude imports: $CORE_MANIFEST"
        return 1
    fi

    return 0
}

if ! load_core_imports; then
    if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
        exit 1
    fi
    return 1
fi

# --- ~/.helix/core symlink セットアップ ---
setup_helix_core_symlink() {
    echo "=== ~/.helix/core ==="

    mkdir -p "$HOME/.helix"

    if [[ -L "$HELIX_CORE_LINK" ]]; then
        local current_target
        local expected_target
        expected_target="$(cd "$HELIX_HOME" && pwd -P)"
        if current_target="$(cd "$HELIX_CORE_LINK" 2>/dev/null && pwd -P)"; then
            if [[ "$current_target" == "$expected_target" ]]; then
                _skip "~/.helix/core already points to $expected_target"
            else
                _warn "~/.helix/core points to $current_target (expected $expected_target); leaving unchanged"
            fi
        else
            _warn "~/.helix/core is a broken symlink; leaving unchanged"
        fi
    elif [[ -e "$HELIX_CORE_LINK" ]]; then
        _warn "~/.helix/core exists and is not a symlink; leaving unchanged"
    else
        ln -s "$HELIX_HOME" "$HELIX_CORE_LINK"
        _ok "Created ~/.helix/core → $HELIX_HOME"
    fi

    echo ""
}

# --- ~/.claude/agents symlink セットアップ ---
setup_claude_agents_symlink() {
    echo "=== ~/.claude/agents ==="

    local target="$HOME/.helix/core/.claude/agents"
    local link="$CLAUDE_DIR/agents"
    local expected_target
    local current_target

    mkdir -p "$CLAUDE_DIR"
    expected_target="$(cd "$target" 2>/dev/null && pwd -P || true)"

    if [[ ! -e "$link" ]] && [[ ! -L "$link" ]]; then
        ln -s "$target" "$link"
        _ok "Created ~/.claude/agents → $target"
    elif [[ -L "$link" ]]; then
        if [[ -n "$expected_target" ]] && current_target="$(cd "$link" 2>/dev/null && pwd -P)"; then
            if [[ "$current_target" == "$expected_target" ]]; then
                _skip "~/.claude/agents already points to $expected_target"
            else
                _warn "~/.claude/agents points to $current_target (expected $expected_target); leaving unchanged"
            fi
        else
            _warn "~/.claude/agents is a broken or unresolved symlink; leaving unchanged"
        fi
    elif [[ -d "$link" ]]; then
        if [[ -z "$(find "$link" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
            rmdir "$link"
            ln -s "$target" "$link"
            _ok "Replaced empty ~/.claude/agents directory with symlink to $target"
        else
            _warn "~/.claude/agents is a non-empty directory; leaving unchanged and requiring manual migration"
        fi
    else
        _warn "~/.claude/agents exists and is not a directory symlink; leaving unchanged"
    fi

    echo ""
}

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
        {
            echo "# Global Settings"
            echo ""
            local import_line
            for import_line in "${CORE_IMPORTS[@]}"; do
                echo "$import_line"
            done
        } > "$CLAUDE_MD"
        _ok "Created $CLAUDE_MD"
        return
    fi

    local tmp="${CLAUDE_MD}.tmp"
    local removed=0
    # 旧 import を除去してから既存ファイルに追記（重複チェック）
    cp "$CLAUDE_MD" "$tmp"
    local legacy_import
    for legacy_import in "${LEGACY_CLAUDE_IMPORTS[@]}"; do
        local matches
        matches=$(grep -cF "$legacy_import" "$tmp" || true)
        if [[ "$matches" -gt 0 ]]; then
            grep -vF "$legacy_import" "$tmp" > "${tmp}.next" || true
            mv "${tmp}.next" "$tmp"
            removed=$((removed + matches))
        fi
    done

    if [[ $removed -gt 0 ]]; then
        mv "$tmp" "$CLAUDE_MD"
        _ok "Removed $removed legacy import(s) from $CLAUDE_MD"
    else
        rm -f "$tmp"
    fi

    local added=0
    local import_line
    for import_line in "${CORE_IMPORTS[@]}"; do
        if ! grep -qF "$import_line" "$CLAUDE_MD"; then
            if [[ $added -eq 0 ]]; then
                echo "" >> "$CLAUDE_MD"
            fi
            echo "$import_line" >> "$CLAUDE_MD"
            added=$((added+1))
        fi
    done

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

    # マージ（merge_settings.py の終了コード: 0=変更あり, 1=変更なし, 3=失敗）
    set +e
    local merge_output
    merge_output="$(python3 "$MERGE_SCRIPT" "$CLAUDE_SETTINGS" 2>&1)"
    local merge_rc=$?
    set -e
    case "$merge_rc" in
        0)
            _ok "HELIX hooks merged into $CLAUDE_SETTINGS"
            ;;
        1)
            _skip "HELIX hooks already present in $CLAUDE_SETTINGS"
            ;;
        *)
            [[ -n "$merge_output" ]] && echo "$merge_output" >&2
            _fail "HELIX hooks merge failed for $CLAUDE_SETTINGS"
            ;;
    esac

    echo ""
}

# --- シェル PATH セットアップ ---
setup_shell_path() {
    echo "=== Shell PATH ==="

    local path_line="export PATH=\"$HELIX_HOME/cli:\$PATH\""
    local legacy_path_line="export PATH=\"\$HOME/ai-dev-kit-vscode/cli:\$PATH\""
    local marker="$HELIX_HOME/cli"
    local added=false

    for rcfile in "$HOME/.bashrc" "$HOME/.zshrc"; do
        if [[ ! -f "$rcfile" ]]; then
            continue
        fi

        if grep -qF "$path_line" "$rcfile"; then
            _skip "PATH already in $(basename "$rcfile")"
        elif grep -qF "$legacy_path_line" "$rcfile"; then
            local tmp="${rcfile}.tmp"
            sed "s|$(printf '%s\n' "$legacy_path_line" | sed 's/[.[\*^$()+?{}|/]/\\&/g')|$path_line|" "$rcfile" > "$tmp"
            mv "$tmp" "$rcfile"
            _ok "PATH updated in $(basename "$rcfile")"
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
    local agents_example="$HELIX_HOME/helix/AGENTS.md.example"
    if [[ ! -f "$CODEX_AGENTS" ]] && [[ -f "$agents_example" ]]; then
        mkdir -p "$CODEX_DIR"
        cp "$agents_example" "$CODEX_AGENTS"
        _ok "Copied AGENTS.md → $CODEX_AGENTS"
    else
        _skip "AGENTS.md already exists or template not found"
    fi

    # config.toml
    if [[ ! -f "$CODEX_CONFIG" ]]; then
        mkdir -p "$CODEX_DIR"
        cat > "$CODEX_CONFIG" <<EOF
$CODEX_HELIX_COMMENT
[shell_environment_policy]
inherit = "all"
EOF
        _ok "Created $CODEX_CONFIG with HELIX defaults"
    elif grep -qE '^[[:space:]]*\[shell_environment_policy\][[:space:]]*$' "$CODEX_CONFIG"; then
        _skip "shell_environment_policy already exists in config.toml"
    else
        if [[ -s "$CODEX_CONFIG" ]]; then
            echo "" >> "$CODEX_CONFIG"
        fi
        cat >> "$CODEX_CONFIG" <<EOF
$CODEX_HELIX_COMMENT
[shell_environment_policy]
inherit = "all"
EOF
        _ok "Added shell_environment_policy to config.toml"
    fi

    echo ""
}

# --- アンインストール ---
uninstall() {
    echo "=== HELIX Uninstall ==="

    # CLAUDE.md から @import 行を削除
    if [[ -f "$CLAUDE_MD" ]]; then
        local tmp="${CLAUDE_MD}.tmp"
        cp "$CLAUDE_MD" "$tmp"
        local import_line
        for import_line in "${CORE_IMPORTS[@]}" "${LEGACY_CLAUDE_IMPORTS[@]}"; do
            grep -vF "$import_line" "$tmp" > "${tmp}.next" || true
            mv "${tmp}.next" "$tmp"
        done
        mv "$tmp" "$CLAUDE_MD"
        _ok "Removed HELIX imports from $CLAUDE_MD"
    else
        _skip "$CLAUDE_MD not found"
    fi

    # ~/.helix/core symlink
    if [[ -L "$HELIX_CORE_LINK" ]]; then
        rm "$HELIX_CORE_LINK"
        _ok "Removed ~/.helix/core symlink"
    elif [[ -e "$HELIX_CORE_LINK" ]]; then
        _skip "~/.helix/core exists and is not a symlink"
    else
        _skip "~/.helix/core not found"
    fi

    # ~/.claude/agents symlink
    local claude_agents_link="$CLAUDE_DIR/agents"
    if [[ -L "$claude_agents_link" ]]; then
        rm "$claude_agents_link"
        _ok "Removed ~/.claude/agents symlink"
    elif [[ -e "$claude_agents_link" ]]; then
        _skip "~/.claude/agents exists and is not a symlink"
    else
        _skip "~/.claude/agents not found"
    fi

    # settings.json から HELIX hooks を除去
    if [[ -f "$CLAUDE_SETTINGS" ]]; then
        cp "$CLAUDE_SETTINGS" "${CLAUDE_SETTINGS}.bak"
        set +e
        local remove_output
        remove_output="$(python3 "$MERGE_SCRIPT" "$CLAUDE_SETTINGS" --remove 2>&1)"
        local remove_rc=$?
        set -e
        case "$remove_rc" in
            0)
                _ok "Removed HELIX hooks from $CLAUDE_SETTINGS"
                ;;
            1)
                _skip "No HELIX hooks found in $CLAUDE_SETTINGS"
                ;;
            *)
                [[ -n "$remove_output" ]] && echo "$remove_output" >&2
                _fail "HELIX hooks removal failed for $CLAUDE_SETTINGS"
                ;;
        esac
    else
        _skip "$CLAUDE_SETTINGS not found"
    fi

    # Shell PATH
    local path_line="export PATH=\"$HELIX_HOME/cli:\$PATH\""
    local legacy_path_line="export PATH=\"\$HOME/ai-dev-kit-vscode/cli:\$PATH\""
    for rcfile in "$HOME/.bashrc" "$HOME/.zshrc"; do
        if [[ -f "$rcfile" ]] && { grep -qF "$path_line" "$rcfile" || grep -qF "$legacy_path_line" "$rcfile"; }; then
            local tmp="${rcfile}.tmp"
            grep -vF "$path_line" "$rcfile" | grep -vF "$legacy_path_line" | grep -v "^# HELIX Framework$" > "$tmp" || true
            mv "$tmp" "$rcfile"
            _ok "Removed PATH from $(basename "$rcfile")"
        fi
    done

    # Codex config.toml
    if [[ -f "$CODEX_CONFIG" ]]; then
        local tmp="${CODEX_CONFIG}.tmp"
        sed '/^# HELIX:/{N;/\n\[shell_environment_policy\]$/{N;/\ninherit = "all"$/d;};}' "$CODEX_CONFIG" \
            | sed '/^# HELIX:/d' > "$tmp"

        if cmp -s "$CODEX_CONFIG" "$tmp"; then
            rm -f "$tmp"
            _skip "No HELIX entries found in $CODEX_CONFIG"
        else
            mv "$tmp" "$CODEX_CONFIG"
            _ok "Removed HELIX entries from $CODEX_CONFIG"
        fi
    else
        _skip "$CODEX_CONFIG not found"
    fi

    # Codex symlinks
    local codex_skills="$CODEX_DIR/skills"
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
        return 1
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
    return 0
}

# --- メイン ---
main() {
    echo ""
    echo "  HELIX Framework Setup"
    echo "  ====================="
    echo ""

    if [[ "${1:-}" == "--uninstall" ]]; then
        uninstall
        if summary; then
            exit 0
        fi
        exit 1
    fi

    if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
        echo "Usage: bash $SCRIPT_DIR/setup.sh [--uninstall]"
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

    setup_helix_core_symlink
    setup_claude_agents_symlink
    setup_claude_md
    setup_settings
    setup_shell_path
    setup_codex
    summary
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
