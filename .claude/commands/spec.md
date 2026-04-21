---
description: Start spec-driven development — write a structured specification before writing code
---

Invoke the agent-skills:spec-driven-development skill.

Begin by understanding what the user wants to build. Ask clarifying questions about:
1. The objective and target users
2. Core features and acceptance criteria
3. Tech stack preferences and constraints
4. Known boundaries (what to always do, ask first about, and never do)

Then generate a structured spec covering all six core areas: objective, commands, project structure, code style, testing strategy, and boundaries.

Save the spec as SPEC.md in the project root and confirm with the user before proceeding.

## HELIX 連携
- HELIX フェーズ: L1 要件定義 / L3 詳細設計
- HELIX CLI: `helix init` でプロジェクト初期化 → `helix size` で駆動タイプ判定 (be/fe/fullstack/db/agent/scrum)
- 仕様未確定の場合: `helix scrum init` → helix-scrum スキルに切替
- システム規模の見積もり: system-design-sizing スキルを併用
