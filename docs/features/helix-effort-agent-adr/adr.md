# ADR-007: Claude Code Agent tool への effort/thinking budget 伝搬

**Feature**: helix-effort-agent-adr
**Date**: 2026-05-06
**Status**: Accepted (2026-05-06 起票・同日 Decision 確定、PLAN-022 W-P2-3 → PLAN-023 W-3a/W-4)

---

## Context

ADR-006 で Phase A (Claude native subagent の effort field) は「警告フック限定の部分実装」と認められた。背景は以下の通り。

1. `.claude/agents/*.md` frontmatter の `effort: high/medium` は HELIX 独自拡張である
2. Claude Code 公式仕様 (name/description/tools/model/memory/maxTurns) は `effort` を解釈しない
3. `cli/lib/skill_dispatcher.py` の `_warn_s_task_high_effort_agent()` は警告のみを行う
4. Claude Code の Agent tool 呼び出し時、subagent の thinking budget は親 (Opus) 設定が継承される
5. その結果、旧 FE 専用 native subagent 群でも effort 差を実運用へ十分反映できなかった

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

Agent tool を直接呼ばず、`helix claude --role pmo --model sonnet --task "..."` のような wrapper を経由し、wrapper 内で effort → API パラメータ変換を行う。

利点: 制御を HELIX 側に集約できる。

欠点: Claude Code 公式 Agent tool との二重メンテになり、利用者の学習コストも増える。

### 確定 (2026-05-06)

**Option A (prompt inject) を採用**する。Option B は外的依存で待ち時間が不確実であり、Option C は二重メンテの負担が大きく現実的でないためである。実装は PLAN-023 W-3a として `cli/lib/skill_dispatcher.py` の `is_claude_native=True` 経路 (行 397-418) に effort prefix と Skill Context Bundle を inject する形で行う。

## Consequences

- `cli/lib/skill_dispatcher.py` に `_effort_prefix()` 関数を新設し、`dispatch()` の `is_claude_native=True` 経路で `_load_agent_effort()` の戻り値を hint に prefix として inject する (PLAN-023 W-3a)
- Phase A の警告フック (`_warn_s_task_high_effort_agent()`) は現状維持とし、既存の S × high 誤指定検知は継続する
- effort 値ごとの prefix 文言:
  - `high`: 「[effort=high] このタスクは詳細な深い分析・厳密な仕様確認を要する。表層的な対応を避け、依存関係や副作用を必ず確認すること。」
  - `medium`: 「[effort=medium] 標準的な精度で進めること。」
  - `low`: 「[effort=low] このタスクは軽量・自明系。簡潔・最小限で進め、過剰な分析を避けること。」
  - 未定義 / 空: prefix なし (退行なし)
- ADR-006 から本 ADR への明示的リンクを追加し、循環参照を避ける
- Bypass: 環境変数 `HELIX_DISABLE_EFFORT_INJECT=1` で機能 OFF (バックアウト用)

## Open Questions (将来 carry)

1. Claude API `extended_thinking` が SDK 経由で渡る仕様化のタイミング (Q3 2026 目処の再評価)。仕様化されれば Option A から Option B へマイグレーション検討
2. prompt prefix 文言の効果計測 (Sonnet 行動傾向が effort で実際に変化するかの A/B 評価) — `helix skill stats` の hit_rate と合わせ運用 1 ヶ月後にレビュー

## Related

- [ADR-006 (Phase A/B 共存)](/home/tenni/ai-dev-kit-vscode/docs/features/helix-budget-autothinking/D-ADR/adr.md) - 本 ADR は ADR-006 の Phase A 制約を解消する代替検討
- PLAN-022 (HELIX オーケストレーション層実機能化) - 上位計画
- PLAN-023 (PLAN-022 残課題 3 件の同時解消) - 本 ADR の Decision を実装する PLAN
- [docs/features/helix-budget-autothinking/D-ADR/adr.md](/home/tenni/ai-dev-kit-vscode/docs/features/helix-budget-autothinking/D-ADR/adr.md) - ADR-006 本体
