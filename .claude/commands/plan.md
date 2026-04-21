---
description: Break work into small verifiable tasks with acceptance criteria and dependency ordering
---

Invoke the agent-skills:planning-and-task-breakdown skill.

Read the existing spec (SPEC.md or equivalent) and the relevant codebase sections. Then:

1. Enter plan mode — read only, no code changes
2. Identify the dependency graph between components
3. Slice work vertically (one complete path per task, not horizontal layers)
4. Write tasks with acceptance criteria and verification steps
5. Add checkpoints between phases
6. Present the plan for human review

Save the plan to tasks/plan.md and task list to tasks/todo.md.

## HELIX 連携
- HELIX フェーズ: L1 → L3 設計フロー
- HELIX CLI: `helix size` → 規模判定 + フェーズスキップ決定 / `helix pr --dry-run` で PR 骨子生成
- 技術判断の壁打ち: `helix codex --role tl` 経由でレビュー
- 後戻りコスト高の判断: adversarial-review スキルを G2 で発火
