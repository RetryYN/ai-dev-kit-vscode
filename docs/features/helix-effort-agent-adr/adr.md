# ADR-007: Claude Code Agent tool への effort/thinking budget 伝搬

**Feature**: helix-effort-agent-adr
**Date**: 2026-05-06
**Status**: Draft (2026-05-06 起票、PLAN-022 W-P2-3)

---

## Context

ADR-006 で Phase A (Claude subagent の effort field) は「警告フック限定の部分実装」と認められた。背景は以下の通り。

1. `.claude/agents/*.md` frontmatter の `effort: high/medium` は HELIX 独自拡張である
2. Claude Code 公式仕様 (name/description/tools/model/memory/maxTurns) は `effort` を解釈しない
3. `cli/lib/skill_dispatcher.py` の `_warn_s_task_high_effort_agent()` は警告のみを行う
4. Claude Code の Agent tool 呼び出し時、subagent の thinking budget は親 (Opus) 設定が継承される
5. その結果、`fe-design` (effort:high) と `fe-test` (effort:medium) は現状同じ thinking で動作する

このため、Phase A の frontmatter だけでは effort の意図を実運用へ反映できない。ADR-007 では、Claude Code Agent tool への effort / thinking budget 伝搬をどう代替するかを検討する。

## Decision

### Option A: prompt inject 方式

Agent tool 呼び出し時の prompt 冒頭に「effort:high のため詳細な深い分析を行え」「effort:medium のため標準的な思考で進めよ」を HELIX 側で注入する。Claude API の extended thinking は使えないが、prompt engineering で behavior を寄せる。

利点: 実装コストが低く、Claude Code 公式 API の変更を待たずに進められる。

欠点: thinking budget の厳密制御はできず、token 消費のみ増える可能性がある。

### Option B: 公式 extended thinking API 待ち

Claude API の extended_thinking (`/v1/messages` の thinking パラメータ) が Claude Code SDK 経由で Agent tool 呼び出しに伝わる仕様を Anthropic に要望し、それまでは effort field を docs 用メタとして残す。

利点: 公式整合であり、将来的に最も確実である。

欠点: 仕様化の時期が不明で、HELIX 側で即時にできることがない。

### Option C: HELIX 独自 wrapper 経路

Agent tool を直接呼ばず、`helix invoke-agent --name fe-design --task "..."` のような wrapper を経由し、wrapper 内で effort → API パラメータ変換を行う。

利点: 制御を HELIX 側に集約できる。

欠点: Claude Code 公式 Agent tool との二重メンテになり、利用者の学習コストも増える。

### 推奨案

執筆時点では **Option A を推奨**する。Option B は外的依存で待ち時間が不確実であり、Option C は二重メンテの負担が大きく現実的でないためである。なお、Draft 段階であり最終決定は別途行う。

## Consequences

- Option A 採用時は `cli/lib/skill_dispatcher.py` に prompt inject ロジックを追加する想定となる
- Phase A の警告フックは現状維持とし、既存の誤指定検知は継続する
- ADR-006 から本 ADR への明示的リンクを追加し、循環参照を避ける

## Open Questions

1. prompt inject の具体的文言をどう分岐するか
2. Claude API extended_thinking が SDK 経由で渡る仕様の調査をいつ実施するか
3. `effort=medium` と未指定の差別化基準をどう定義するか

## Related

- [ADR-006 (Phase A/B 共存)](/home/tenni/ai-dev-kit-vscode/docs/features/helix-budget-autothinking/D-ADR/adr.md) - 本 ADR は ADR-006 の Phase A 制約を解消する代替検討
- PLAN-022 (HELIX オーケストレーション層実機能化) - 上位計画
- [docs/features/helix-budget-autothinking/D-ADR/adr.md](/home/tenni/ai-dev-kit-vscode/docs/features/helix-budget-autothinking/D-ADR/adr.md) - ADR-006 本体
