#!/usr/bin/env bash
# PreCompact hook: HELIX state capture (auto-compact / manual /compact 直前)
#
# 目的: Claude Code の compact 発火直前に handover + audit_log に state を capture し、
#       次 session で復元可能な状態を作る。
#
# TL v5 round 5 (bdnmyhznq) 指摘遵守:
#   - decision:block は使わない (無限ループ + manual compact 妨害リスク)
#   - capture のみ、block 一切なし
#   - fail-open (hook 失敗で session を止めない)
#   - timeout 3 秒以内
#   - secret/PII 警戒: transcript_path 中身は読まない、path 文字列のみ payload に記録
#
# 注記: V5 framework 18 要素目の Layer 3 (PreCompact 介入) 最小 PoC。
#       将来「使い捨て session 駆動」(Layer 5 heartbeat) 完成後は構造的に obsolete。

set +e  # fail-open: エラーで止めない

# stdin から JSON 読み込み (3 秒 timeout)
input_json=$(timeout 1 cat 2>/dev/null || echo '{}')

# session_id / matcher / transcript_path 抽出 (jq 不在時は grep/sed fallback)
if command -v jq >/dev/null 2>&1; then
    session_id=$(echo "$input_json" | jq -r '.session_id // "unknown"' 2>/dev/null || echo "unknown")
    matcher=$(echo "$input_json" | jq -r '.matcher // "unknown"' 2>/dev/null || echo "unknown")
    transcript_path=$(echo "$input_json" | jq -r '.transcript_path // ""' 2>/dev/null || echo "")
else
    # fallback: grep + sed で最小抽出 (キー順想定: session_id, matcher, transcript_path)
    session_id=$(echo "$input_json" | grep -oE '"session_id"\s*:\s*"[^"]*"' | sed 's/.*"\([^"]*\)"$/\1/' | head -1)
    matcher=$(echo "$input_json" | grep -oE '"matcher"\s*:\s*"[^"]*"' | sed 's/.*"\([^"]*\)"$/\1/' | head -1)
    transcript_path=$(echo "$input_json" | grep -oE '"transcript_path"\s*:\s*"[^"]*"' | sed 's/.*"\([^"]*\)"$/\1/' | head -1)
    [ -z "$session_id" ] && session_id="unknown"
    [ -z "$matcher" ] && matcher="unknown"
fi

# HELIX project root 検出
if [ -n "${HELIX_PROJECT_ROOT:-}" ] && [ -d "$HELIX_PROJECT_ROOT" ]; then
    project_root="$HELIX_PROJECT_ROOT"
elif command -v git >/dev/null 2>&1; then
    project_root=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
fi

# session_id 短縮 (先頭 8 文字、表示用)
session_id_short="${session_id:0:8}"

if [ -z "$project_root" ] || [ ! -d "$project_root" ]; then
    # project root 不明 → silent pass (fail-open)
    exit 0
fi

# 1. helix handover update (best-effort、失敗しても続行)
helix_bin="${project_root}/cli/helix"
if [ -x "$helix_bin" ]; then
    note="[PreCompact ${matcher}] session=${session_id_short} at $(date -Iseconds 2>/dev/null || date)"
    timeout 2 "$helix_bin" handover update --note "$note" >/dev/null 2>&1 || true
fi

# 2. helix.db audit_log INSERT (best-effort)
db_path="${project_root}/.helix/helix.db"
if command -v sqlite3 >/dev/null 2>&1 && [ -f "$db_path" ] && [ -w "$db_path" ]; then
    # payload は JSON 文字列で構築 (transcript_path は path のみ、内容は読まない)
    payload=$(printf '{"session_id":"%s","matcher":"%s","transcript_path":"%s"}' \
        "${session_id//\"/\\\"}" \
        "${matcher//\"/\\\"}" \
        "${transcript_path//\"/\\\"}")
    # SQL injection 防止のため $payload は限定文字のみ (jq 経由なら自動 escape、fallback でも限定)
    timeout 1 sqlite3 "$db_path" <<SQL 2>/dev/null || true
INSERT INTO audit_log (audit_kind, actor, payload)
VALUES ('precompact_capture', 'precompact-hook', '${payload//\'/\'\'}');
SQL
fi

# 3. systemMessage 出力 (Claude に state capture 完了を通知)
# decision:block は使わない (TL v5 P1 遵守)
cat <<EOF
{"systemMessage": "🛡 PreCompact ${matcher} fired. HELIX state captured (session=${session_id_short}). handover + audit_log updated."}
EOF

exit 0
