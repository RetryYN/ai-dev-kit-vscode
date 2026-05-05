# Decisions

## Active

- HELIX の Codex 実装委譲は `helix codex` を正規入口にする。
- Claude Code の Bash 実行では `helix-pre-bash` が raw `codex exec` / raw `claude` を検知し、証跡なしの実行を deny する。
- Claude Code の WebSearch / WebFetch 実行では `helix-pre-research` を正規 guard にし、role / task mismatch を deny する。
- context / memory の整合性確認は `helix context check` を正規入口にする。
- L サイズの guard / workflow 変更は PLAN finalized と gate evidence なしに実装完了扱いにしない。

## Decision Log

- 2026-05-04: raw LLM CLI 実行ガードと context guard を追加。prompt 指示だけではなく PreToolUse / wrapper / check command で強制導線を補強する方針にした。
- 2026-05-05: PLAN-017 を retroactively finalized。draft のまま実装 commit されたことを process violation として記録し、DoD / memory / regression verification で閉じる。
- 2026-05-05: PLAN-018 を T2 LLM Guard の retroactive source of truth として追加。raw LLM / research / agent policy / context guard を code + hook で強制し、G2/G3/G4 dry-run evidence を記録する。
- 2026-05-05: `helix-gate` static runner は `bash -o pipefail -c` で実行する。`! rg ... | head` 系 absence check の false-fail を防ぐため。
