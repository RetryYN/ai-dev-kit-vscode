---
description: Conduct a five-axis code review — correctness, readability, architecture, security, performance
---

Invoke the agent-skills:code-review-and-quality skill.

Review the current changes (staged or recent commits) across all five axes:

1. **Correctness** — Does it match the spec? Edge cases handled? Tests adequate?
2. **Readability** — Clear names? Straightforward logic? Well-organized?
3. **Architecture** — Follows existing patterns? Clean boundaries? Right abstraction level?
4. **Security** — Input validated? Secrets safe? Auth checked? (Use security-and-hardening skill)
5. **Performance** — No N+1 queries? No unbounded ops? (Use performance-optimization skill)

Categorize findings as Critical, Important, or Suggestion.
Output a structured review with specific file:line references and fix recommendations.

## HELIX 連携
- HELIX フェーズ: G2 設計凍結 / G4 実装凍結 / G6 RC 判定
- HELIX CLI: `helix review --uncommitted` で Codex 自動レビュー / `helix gate G4` でゲート判定
- 設計批判: adversarial-review スキル (G2 必須条件時)
- セキュリティ: security-and-hardening スキル併用
