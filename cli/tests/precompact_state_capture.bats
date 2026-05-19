#!/usr/bin/env bats
# Tests for .claude/hooks/precompact-state-capture.sh
# PreCompact hook PoC (V5 framework 18 要素 Layer 3)
#
# TL v5 round 5 指摘遵守: decision:block 使わず capture のみ、fail-open

HOOK_SCRIPT="${BATS_TEST_DIRNAME}/../../.claude/hooks/precompact-state-capture.sh"

setup() {
    # 各テストごとに独立した tmp project root を作る
    TMP_ROOT=$(mktemp -d)
    export HELIX_PROJECT_ROOT="$TMP_ROOT"
    mkdir -p "$TMP_ROOT/.helix"
    mkdir -p "$TMP_ROOT/cli"
    # dummy helix CLI (handover update を no-op で受ける)
    cat > "$TMP_ROOT/cli/helix" <<'STUB'
#!/usr/bin/env bash
exit 0
STUB
    chmod +x "$TMP_ROOT/cli/helix"
}

teardown() {
    rm -rf "$TMP_ROOT"
}

@test "matcher=auto: systemMessage 出力 + exit 0" {
    input='{"session_id":"abc123def456","matcher":"auto","transcript_path":"/tmp/fake.jsonl"}'
    run bash -c "echo '$input' | $HOOK_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"PreCompact auto"* ]]
    [[ "$output" == *"abc123de"* ]]  # session_id_short
    [[ "$output" == *"systemMessage"* ]]
}

@test "matcher=manual: systemMessage 出力 + exit 0" {
    input='{"session_id":"xyz789","matcher":"manual","transcript_path":"/tmp/fake.jsonl"}'
    run bash -c "echo '$input' | $HOOK_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"PreCompact manual"* ]]
    [[ "$output" == *"systemMessage"* ]]
}

@test "jq 不在環境: fail-open で exit 0 + systemMessage 出力" {
    # PATH から jq を除外
    input='{"session_id":"zzz","matcher":"auto","transcript_path":""}'
    run bash -c "PATH=/usr/local/bin:/usr/bin:/bin echo '$input' | env -i PATH=/usr/bin:/bin $HOOK_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"systemMessage"* ]]
}

@test "空入力: fail-open で exit 0" {
    run bash -c "echo '' | $HOOK_SCRIPT"
    [ "$status" -eq 0 ]
    # session_id=unknown, matcher=unknown でも systemMessage を出す
    [[ "$output" == *"systemMessage"* ]]
}

@test "壊れた JSON: fail-open で exit 0" {
    input='not a json {{{'
    run bash -c "echo '$input' | $HOOK_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"systemMessage"* ]]
}

@test "project_root 不明 (HELIX_PROJECT_ROOT 不在 + git 外): exit 0 silent" {
    # HELIX_PROJECT_ROOT を unset、git 不在ディレクトリで実行
    OUTSIDE_DIR=$(mktemp -d)
    cd "$OUTSIDE_DIR"
    input='{"session_id":"a","matcher":"auto","transcript_path":""}'
    run env -u HELIX_PROJECT_ROOT bash -c "cd $OUTSIDE_DIR && echo '$input' | $HOOK_SCRIPT"
    [ "$status" -eq 0 ]
    # systemMessage 出さず silent exit (project root 不明 = early return)
    rm -rf "$OUTSIDE_DIR"
}
