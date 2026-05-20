# ADR-022: TodoWrite × agent slot framework 採用

## Status

Proposed (2026-05-20、後追い snapshot — PLAN-088 実装済の L2 凍結)

> **後追い snapshot 注記**: PLAN-088 は 2026-05-19 に起票済み (実装は一部 carry)。本 ADR は PLAN ⊃ ADR レイヤー併存ルールに基づき、L2 大局判断 snapshot として後追い起票する。

## Deciders

- PM (Opus、yoshiyuki0907yn@gmail.com)
- PO (yoshiyuki0907yn@gmail.com)

## Supersedes

なし (新規 ADR)

## Related

- PLAN-088-todowrite-agent-slot-framework (実装 PLAN、本 ADR が L2 凍結する)
- PLAN-100-existing-retrofit-v2-revision (retrofit master、§4.2 に本 ADR の context 記載)
- ADR-025-v5-framework-core-decision (V5 framework 本体、要素 #7 agent_slots 割当ルール)
- PLAN-091-v5-framework-core (§5.5 agent_slots 定義、本 ADR の upstream)
- PLAN-076-subagent-process-mapping (subagent 工程マッピング、本 ADR の前提)

## 業界 standard 参照

| 参照 | Source URL | 本 ADR での引用箇所 |
|---|---|---|
| CrewAI Core Concepts — Agent roles & specialization | https://docs.crewai.com/core-concepts/Agents/ | agent slot の role-specialized 設計パターン (agent type prefix による可観測化) |
| OpenAI Swarm (multi-agent coordination) | https://github.com/openai/swarm | 並列 agent 実行の WIP 可視化・上限管理パターン |
| AWS Step Functions (task token, agent state tracking) | https://docs.aws.amazon.com/step-functions/latest/dg/concepts-tasks.html | in_progress 重複検知・agent state DB 集計の業界整合 |
| HELIX PLAN-076 (subagent 工程マッピング) | docs/plans/PLAN-076-subagent-process-mapping.md | mandatory / on-demand 2 分類 + helix.db audit の前提 |
| GitHub Actions job concurrency (cancel-in-progress) | https://docs.github.com/en/actions/using-jobs/using-concurrency | 並列上限 8 の強制と concurrency group 管理の業界整合 |

---

## Context

### 問題の発端

HELIX 運用において、並列実行時の agent 間の可観測性が不足していた:

1. **TodoWrite content の agent 不明問題**: TodoWrite item がどの agent (Opus / Codex / pmo-sonnet 等) によって処理されているか、content を見ただけでは判定不能
2. **in_progress 重複リスク**: 複数 agent が同じ TodoWrite item を `in_progress` に遷移させる競合リスク
3. **並列 8 上限の追跡不能**: HELIX の並列実行上限 8 が守られているかを機械的に確認する手段がない
4. **helix.db agent_type 未記録**: helix.db の invocation_log / automation_runs 等に agent_type フィールドがなく、事後の統計集計で「誰が何件処理したか」が不明

### 背景となる既存運用

- `.claude/hooks/pretooluse-agent-guard.sh`: PMO/PdM 12 種の agent を fail-close で管理するが、TodoWrite の content は対象外
- PLAN-076 (subagent 工程マッピング): mandatory (10 種) / on-demand (4 種) の 2 分類は確立済みだが、実行時の可観測化機構がない
- 本 session (2026-05-19) での 8 並列達成試行で「どの agent がどの item を担当しているか」の追跡が困難と判明

---

## Decision

**TodoWrite の content 先頭に `[agent_type]` prefix を機械的に必須化し、並列実行時の agent slot を可観測化する。**

具体的な実装:
1. **`[agent_type]` prefix 規約の確立**: `[opus]` / `[pmo-sonnet]` / `[codex-tl]` / `[codex-se]` / `[codex-pg]` 等、PLAN-091 §5.5 agent_slots の slot 値を TodoWrite content 先頭に付与
2. **PreToolUse hook** (`.claude/hooks/pretooluse-todowrite-prefix-check.sh`): TodoWrite tool 呼び出し時に content の prefix 有無を確認 → 不在なら warn (Phase 1) → fail-close (Phase 2)
3. **helix.db v34 拡張** (`todo_entries` table 新設): content / agent_type / status / created_at / updated_at を記録し、agent_type 別 WIP 集計を可能化
4. **CLI 拡張** (`cli/helix-todo`): `helix todo list --agent pmo-sonnet` / `helix todo stats --by-agent` で agent 別統計表示
5. **段階導入**: Phase 1 (warn-only, PLAN-088 起票段階) → Phase 2 (fail-close 化) → Phase 3 (helix.db v34 連携)

---

## Consequences

### Positive

- TodoWrite item の担当 agent が content から即座に判定可能
- in_progress 重複を早期検知し、並列衝突リスクを削減できる
- 並列 8 上限の遵守を機械的に確認できる基盤が整う
- helix.db に agent_type が蓄積され、後から「session あたりの agent 別稼働状況」を統計化できる

### Negative

- 既存 TodoWrite の content 書き換えが必要 (retrofit が発生)
- prefix を付け忘れた TodoWrite は fail-close Phase 2 以降で block される
- agent_type prefix の運用負荷が増える (手動入力ミスのリスク)

---

## Alternatives

### A案 (棄却): ツール側 (Claude Code) での agent 識別

- 採用しない理由: Claude Code の TodoWrite は agent_type を metadata として提供していない。Claude Code API の拡張を待つのは timeline 不定

### B案 (棄却): 別ファイル (agent_log.yaml) での可観測化

- 採用しない理由: TodoWrite と別ファイルの二重管理になり、整合維持が困難。「TodoWrite content 自体に情報を持つ」のが最も確認コストが低い

### C案 (部分採用): 段階的 fail-close (本 ADR の実装方針)

- 採用済み: Phase 1 warn-only → Phase 2 fail-close の段階移行が PLAN-088 §Phase 計画に組み込まれている

---

## Implementation Status

**一部実装 (2026-05-19)**: PLAN-088 は起票済み (commit を含む wave 3 で実装開始)。本 ADR は L2 凍結 snapshot として後追い起票 (2026-05-20)。

| Phase | 実装内容 | 状態 |
|---|---|---|
| Phase 0 (設計) | PLAN-088 起票 + 本 ADR L2 凍結 snapshot | 完了 (本 ADR) |
| Phase 1 (warn) | pretooluse-todowrite-prefix-check.sh (warn-only) | PLAN-088 carry |
| Phase 2 (fail-close) | hook fail-close 化 | 別 session carry |
| Phase 3 (DB) | helix.db v34 todo_entries + CLI | 別 session carry |

**本 ADR 起票後**: PLAN-088 frontmatter への `related_adr: [ADR-022]` 追加は PLAN-100 Phase 2 (別 session) で実施する。
