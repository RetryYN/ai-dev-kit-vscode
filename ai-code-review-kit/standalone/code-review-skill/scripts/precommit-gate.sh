#!/usr/bin/env bash
#
# precommit-gate.sh
# 6段階コードレビューの Stage 1 (Format) / Stage 2 (Lint) を commit 前に強制するゲート。
# 「PR にすら到達させない層」をローカルで固めることで、レビュアーの定型指摘時間をゼロにする。
#
# 設計方針:
#   - Stage 1 (Format) と Stage 2 (Lint) を明確に分離する。
#     Format = 見た目の規約（壊れても動く）/ Lint = 意味の規約（壊れたら動かない）。
#     pre-commit が重くなった時に「どちらを外すか」を判断できるように分けてある。
#   - 検出されたツールだけを実行する（存在しないツールはスキップ）。
#   - ステージ済みファイルのみを対象にする。
#   - 1つでも失敗したら commit を中止する（exit 1）。
#
# 導入方法:
#   1. このファイルをリポジトリの .git/hooks/pre-commit にコピーし実行権限を付与する。
#        cp scripts/precommit-gate.sh .git/hooks/pre-commit
#        chmod +x .git/hooks/pre-commit
#   2. または husky / pre-commit framework から呼び出す。
#
# 環境変数:
#   SKIP_FORMAT=1   Format チェックをスキップ
#   SKIP_LINT=1     Lint チェックをスキップ
#   AUTO_FORMAT=1   整形ツールで自動修正し、修正結果を再ステージする

set -uo pipefail

# ------------------------------------------------------------------
# 共通ユーティリティ
# ------------------------------------------------------------------

RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[0;33m'
BOLD=$'\033[1m'
RESET=$'\033[0m'

EXIT_CODE=0

log_stage() { printf '\n%s== %s ==%s\n' "$BOLD" "$1" "$RESET"; }
log_ok()    { printf '%s  ✓ %s%s\n' "$GREEN" "$1" "$RESET"; }
log_warn()  { printf '%s  ! %s%s\n' "$YELLOW" "$1" "$RESET"; }
log_err()   { printf '%s  ✗ %s%s\n' "$RED" "$1" "$RESET"; EXIT_CODE=1; }

has_cmd() { command -v "$1" >/dev/null 2>&1; }

# ステージ済みファイルを拡張子でフィルタして返す。
# $1: grep 用の拡張子パターン（例: '\.(js|jsx|ts|tsx)$'）
staged_files() {
  git diff --cached --name-only --diff-filter=ACM | grep -E "$1" || true
}

# 自動整形後に再ステージする。
restage() {
  if [[ "${AUTO_FORMAT:-0}" == "1" ]]; then
    git add "$@" 2>/dev/null || true
  fi
}

# ------------------------------------------------------------------
# Stage 1: Format（見た目の規約 / 100% AI / ブロッキング）
# ------------------------------------------------------------------

run_format_stage() {
  log_stage "Stage 1: Format"

  local ran=0

  # --- Prettier (JS/TS/CSS/JSON/MD など) ---
  local prettier_targets
  prettier_targets="$(staged_files '\.(js|jsx|ts|tsx|css|scss|json|md|yaml|yml|html|vue)$')"
  if [[ -n "$prettier_targets" ]] && has_cmd npx; then
    ran=1
    if [[ "${AUTO_FORMAT:-0}" == "1" ]]; then
      echo "$prettier_targets" | xargs npx prettier --write --ignore-unknown
      # shellcheck disable=SC2046
      restage $(echo "$prettier_targets")
      log_ok "Prettier: 自動整形して再ステージしました"
    else
      if echo "$prettier_targets" | xargs npx prettier --check --ignore-unknown; then
        log_ok "Prettier: 整形済み"
      else
        log_err "Prettier: 未整形のファイルがあります（AUTO_FORMAT=1 で自動修正可）"
      fi
    fi
  fi

  # --- gofmt (Go) ---
  local go_targets
  go_targets="$(staged_files '\.go$')"
  if [[ -n "$go_targets" ]] && has_cmd gofmt; then
    ran=1
    local unformatted
    unformatted="$(echo "$go_targets" | xargs gofmt -l)"
    if [[ -z "$unformatted" ]]; then
      log_ok "gofmt: 整形済み"
    else
      if [[ "${AUTO_FORMAT:-0}" == "1" ]]; then
        echo "$go_targets" | xargs gofmt -w
        # shellcheck disable=SC2046
        restage $(echo "$go_targets")
        log_ok "gofmt: 自動整形して再ステージしました"
      else
        log_err "gofmt: 未整形のファイルがあります:"$'\n'"$unformatted"
      fi
    fi
  fi

  # --- black (Python) ---
  local py_targets
  py_targets="$(staged_files '\.py$')"
  if [[ -n "$py_targets" ]] && has_cmd black; then
    ran=1
    if [[ "${AUTO_FORMAT:-0}" == "1" ]]; then
      echo "$py_targets" | xargs black
      # shellcheck disable=SC2046
      restage $(echo "$py_targets")
      log_ok "black: 自動整形して再ステージしました"
    else
      if echo "$py_targets" | xargs black --check --quiet; then
        log_ok "black: 整形済み"
      else
        log_err "black: 未整形のファイルがあります（AUTO_FORMAT=1 で自動修正可）"
      fi
    fi
  fi

  [[ "$ran" == "0" ]] && log_warn "Format ツールが見つからないか対象ファイルがありません（スキップ）"
}

# ------------------------------------------------------------------
# Stage 2: Lint（意味の規約 / 100% AI / ブロッキング）
# ------------------------------------------------------------------

run_lint_stage() {
  log_stage "Stage 2: Lint"

  local ran=0

  # --- ESLint (JS/TS) ---
  local eslint_targets
  eslint_targets="$(staged_files '\.(js|jsx|ts|tsx|vue)$')"
  if [[ -n "$eslint_targets" ]] && has_cmd npx; then
    ran=1
    if echo "$eslint_targets" | xargs npx eslint --max-warnings=0; then
      log_ok "ESLint: 問題なし"
    else
      log_err "ESLint: エラーまたは警告があります"
    fi
  fi

  # --- Ruff (Python) ---
  local py_targets
  py_targets="$(staged_files '\.py$')"
  if [[ -n "$py_targets" ]] && has_cmd ruff; then
    ran=1
    if echo "$py_targets" | xargs ruff check; then
      log_ok "Ruff: 問題なし"
    else
      log_err "Ruff: エラーがあります"
    fi
  fi

  # --- mypy (Python 型チェック) ---
  if [[ -n "$py_targets" ]] && has_cmd mypy; then
    ran=1
    if echo "$py_targets" | xargs mypy --no-error-summary; then
      log_ok "mypy: 型エラーなし"
    else
      log_err "mypy: 型エラーがあります"
    fi
  fi

  # --- tsc (TypeScript 型チェック / プロジェクト全体) ---
  local ts_targets
  ts_targets="$(staged_files '\.(ts|tsx)$')"
  if [[ -n "$ts_targets" ]] && has_cmd npx && [[ -f "tsconfig.json" ]]; then
    ran=1
    if npx tsc --noEmit; then
      log_ok "tsc: 型エラーなし"
    else
      log_err "tsc: 型エラーがあります"
    fi
  fi

  # --- go vet (Go) ---
  local go_targets
  go_targets="$(staged_files '\.go$')"
  if [[ -n "$go_targets" ]] && has_cmd go; then
    ran=1
    if go vet ./... ; then
      log_ok "go vet: 問題なし"
    else
      log_err "go vet: 問題があります"
    fi
  fi

  [[ "$ran" == "0" ]] && log_warn "Lint ツールが見つからないか対象ファイルがありません（スキップ）"
}

# ------------------------------------------------------------------
# メイン
# ------------------------------------------------------------------

main() {
  printf '%s6段階レビュー Stage 1-2 ゲート%s\n' "$BOLD" "$RESET"

  if [[ "${SKIP_FORMAT:-0}" == "1" ]]; then
    log_warn "SKIP_FORMAT=1 のため Stage 1 をスキップ"
  else
    run_format_stage
  fi

  if [[ "${SKIP_LINT:-0}" == "1" ]]; then
    log_warn "SKIP_LINT=1 のため Stage 2 をスキップ"
  else
    run_lint_stage
  fi

  echo
  if [[ "$EXIT_CODE" -ne 0 ]]; then
    printf '%s%sコミット中止: Stage 1-2 のゲートを通過していません。%s\n' "$BOLD" "$RED" "$RESET"
    printf '修正後に再度コミットしてください（自動整形: AUTO_FORMAT=1 git commit ...）。\n'
  else
    printf '%s%sStage 1-2 通過。Stage 3 以降（AIレビュー・人間レビュー）へ。%s\n' "$BOLD" "$GREEN" "$RESET"
  fi

  exit "$EXIT_CODE"
}

main "$@"
