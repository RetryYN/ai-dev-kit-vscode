#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  SCRIPT="$HELIX_ROOT/cli/helix-asset"
  TMP_ROOT="$(mktemp -d)"
  export HELIX_HOME="$TMP_ROOT/helix-home"
  export HELIX_ASSET_DRY_RUN_LOG="$TMP_ROOT/fake-codex.log"
  export PATH="$HELIX_ROOT/cli:$PATH"

  mkdir -p "$HELIX_HOME/cli" "$TMP_ROOT/out"
  cat > "$HELIX_HOME/cli/helix-codex" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

printf 'call\n' >> "${HELIX_ASSET_DRY_RUN_LOG}"

task=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --task)
      task="${2:-}"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

output_path="$(printf '%s\n' "$task" | sed -n "s/.*write the PNG output to '\\([^']*\\)'.*/\\1/p" | tail -n 1)"
if [[ -n "$output_path" ]]; then
  mkdir -p "$(dirname "$output_path")"
  printf 'mock image generated\n' > "$output_path"
fi

printf 'mock image generated\n'
SH
  chmod +x "$HELIX_HOME/cli/helix-codex"
  cd "$HELIX_ROOT"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

assert_preset_listed() {
  local preset="$1"
  [[ "$output" == *"$preset"* ]]
}

@test "helix-asset help shows usage and all presets" {
  run "$SCRIPT" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"使い方: helix asset <preset> [opts]"* ]]
  [[ "$output" == *"--out <path> / --output <path>"* ]]
  assert_preset_listed "banner"
  assert_preset_listed "logo"
  assert_preset_listed "hero"
  assert_preset_listed "card"
  assert_preset_listed "thumb"
  assert_preset_listed "icon"
  assert_preset_listed "bg"
}

@test "helix-asset dry-run with banner skips codex and prints prompt" {
  rm -f "$HELIX_ASSET_DRY_RUN_LOG"

  run "$SCRIPT" banner --dry-run --out "$TMP_ROOT/out/banner.png"
  [ "$status" -eq 0 ]
  [ ! -e "$HELIX_ASSET_DRY_RUN_LOG" ]
  [[ "$output" == *"Generate a 1200x400 banner image"* ]]
  [[ "$output" == *"output: $TMP_ROOT/out/banner.png"* ]]
  [[ "$output" == *"model: gpt-5.4-mini"* ]]
}

@test "helix-asset dry-run via env var skips codex" {
  rm -f "$HELIX_ASSET_DRY_RUN_LOG"

  run env HELIX_ASSET_DRY_RUN=1 "$SCRIPT" card --out "$TMP_ROOT/out/card.png"
  [ "$status" -eq 0 ]
  [ ! -e "$HELIX_ASSET_DRY_RUN_LOG" ]
  [[ "$output" == *"Generate a 800x600 card image"* ]]
  [[ "$output" == *"output: $TMP_ROOT/out/card.png"* ]]
}

@test "helix-asset injects motif into prompt in dry-run" {
  run "$SCRIPT" logo --motif "HELIX" --dry-run --output "$TMP_ROOT/out/logo.png"
  [ "$status" -eq 0 ]
  [[ "$output" == *"Motif: HELIX"* ]]
  [[ "$output" == *"Generate a 512x512 logo image"* ]]
  [[ "$output" == *"output: $TMP_ROOT/out/logo.png"* ]]
}

@test "helix-asset supports all seven presets in dry-run" {
  declare -A expected_sizes=(
    [banner]="1200x400"
    [logo]="512x512"
    [hero]="1920x1080"
    [card]="800x600"
    [thumb]="1200x630"
    [icon]="256x256"
    [bg]="1920x1080"
  )

  for preset in banner logo hero card thumb icon bg; do
    run "$SCRIPT" "$preset" --dry-run --out "$TMP_ROOT/out/$preset.png"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Generate a ${expected_sizes[$preset]}"* ]]
    [[ "$output" == *"output: $TMP_ROOT/out/$preset.png"* ]]
  done
}

@test "helix-asset rejects unknown presets" {
  run "$SCRIPT" spaceship --dry-run
  [ "$status" -eq 1 ]
  [[ "$output" == *"unknown preset: spaceship"* ]]
}

@test "helix-asset rejects motif newline control and oversize input" {
  long_motif="$(printf '%0257d' 0 | tr '0' 'a')"

  run "$SCRIPT" banner --motif $'HEL\nIX' --dry-run
  [ "$status" -eq 1 ]
  [[ "$output" == *"--motif には制御文字を含められません"* ]]

  run "$SCRIPT" banner --motif $'HEL\001IX' --dry-run
  [ "$status" -eq 1 ]
  [[ "$output" == *"--motif には制御文字を含められません"* ]]

  run "$SCRIPT" banner --motif "$long_motif" --dry-run
  [ "$status" -eq 1 ]
  [[ "$output" == *"--motif は 256 文字以内で指定してください"* ]]
}

@test "helix-asset validates output path in dry-run and accepts output alias" {
  target="$TMP_ROOT/out/custom/banner.png"

  run "$SCRIPT" banner --output "$target" --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"output: $target"* ]]
  [[ "$output" == *"Save the result to $target."* ]]

  run "$SCRIPT" banner --out $'bad\npath.png' --dry-run
  [ "$status" -eq 1 ]
  [[ "$output" == *"--out/--output には制御文字を含められません"* ]]
}

@test "helix-asset integration smoke uses fake codex and writes all preset outputs" {
  : > "$HELIX_ASSET_DRY_RUN_LOG"
  presets="banner logo hero card thumb icon bg"
  for preset in $presets; do
    target="$TMP_ROOT/out/$preset.png"
    run "$SCRIPT" "$preset" --motif "HELIX" --out "$target"
    [ "$status" -eq 0 ]
    [[ "$output" == *"mock image generated"* ]]
    [ -f "$target" ]
    [[ "$(cat "$target")" == "mock image generated" ]]
  done

  [ "$(wc -l < "$HELIX_ASSET_DRY_RUN_LOG")" -eq 7 ]
}
