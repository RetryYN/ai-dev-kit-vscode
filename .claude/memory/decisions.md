# Decisions

## Active

- HELIX の Codex 実装委譲は `helix codex` を正規入口にする。
- Claude Code の Bash 実行では `helix-pre-bash` が raw `codex exec` / raw `claude` を検知し、証跡なしの実行を deny する。
- context / memory の整合性確認は `helix context check` を正規入口にする。

## Decision Log

- 2026-05-04: raw LLM CLI 実行ガードと context guard を追加。prompt 指示だけではなく PreToolUse / wrapper / check command で強制導線を補強する方針にした。
