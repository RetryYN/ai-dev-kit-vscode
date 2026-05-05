# HELIX Project Memory

このファイルはセッション開始時に読む短い共有メモリ。詳細は隣接ファイルへ分離し、ここは先頭 200 行以内に保つ。

## Current Guardrails

- raw `codex exec` は `helix codex` 経由、raw `claude` は `helix claude --dry-run` 経由に寄せる。例外時は対象別の `HELIX_ALLOW_RAW_*` / `HELIX_RAW_*_REASON=<理由>` を同じ Bash command に含め、evidence に残す。
- `helix context check` は AGENTS / CLAUDE / hook / memory の強制導線を検査する。
- 自動生成される `.claude/agent-memory/` は個人・エージェント runtime memory として Git 追跡しない。

## Open Memory Files

- `decisions.md`: 決定事項
- `constraints.md`: 制約条件
- `rejected-approaches.md`: 却下済みアプローチ
