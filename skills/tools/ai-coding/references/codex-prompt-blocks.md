> Adapted from codex-plugin-cc (OpenAI, Apache 2.0)

# Codex Prompt Blocks for HELIX

HELIX運用向けに、Codex/GPT-5.4向けのプロンプトブロックを再整理したリファレンス。
XMLブロック自体は英語のまま利用し、周辺ガイドのみ日本語で運用する。

## 使い方の原則

- すべてを毎回入れない。タスクに必要な最小セットを選ぶ。
- 競合する指示は混在させない（例: 詳細出力と極小出力を同時要求しない）。
- フェーズとロールに合わせて、証跡重視か速度重視かを切り替える。

## ブロック一覧（HELIX適応版）

### 1. `task`

HELIXでの用途: 全ロール共通。L2-L6の全フェーズで必須。

```xml
<task>
Describe the concrete job, the relevant repository or failure context, and the expected end state.
</task>
```

### 2. `structured_output_contract`

HELIXでの用途: TL/SE/QA。G2/G3/G4/G6向けの判定・報告フォーマット固定。

```xml
<structured_output_contract>
Return exactly the requested output shape and nothing else.
Keep the answer compact.
Put the highest-value findings or decisions first.
</structured_output_contract>
```

### 3. `compact_output_contract`

HELIXでの用途: TL/SE。短い調査報告、一次診断、差分要約（L4実装中間報告）。

```xml
<compact_output_contract>
Keep the final answer compact and structured.
Do not include long scene-setting or repeated recap.
</compact_output_contract>
```

### 4. `default_follow_through_policy`

HELIXでの用途: SE主導のL4実装で有効。軽微な不確実性を自己解決し、停止を減らす。

```xml
<default_follow_through_policy>
Default to the most reasonable low-risk interpretation and keep going.
Only stop to ask questions when a missing detail changes correctness, safety, or an irreversible action.
</default_follow_through_policy>
```

### 5. `completeness_contract`

HELIXでの用途: TL/SE。実装.2〜.5で「原因特定だけで止まる」事故を防ぐ。

```xml
<completeness_contract>
Resolve the task fully before stopping.
Do not stop at the first plausible answer.
Check whether there are follow-on fixes, edge cases, or cleanup needed for a correct result.
</completeness_contract>
```

### 6. `verification_loop`

HELIXでの用途: TL/QA。G4/G6での検証品質を底上げ。レビュー・修正後の再確認に必須。

```xml
<verification_loop>
Before finalizing, verify the result against the task requirements and the changed files or tool outputs.
If a check fails, revise the answer instead of reporting the first draft.
</verification_loop>
```

### 7. `missing_context_gating`

HELIXでの用途: TL/Research/SE。未読ファイル推測や仕様推測を防止（L2/L3/L4で有効）。

```xml
<missing_context_gating>
Do not guess missing repository facts.
If required context is absent, retrieve it with tools or state exactly what remains unknown.
</missing_context_gating>
```

### 8. `grounding_rules`

HELIXでの用途: TL/QA/Security。根拠なき断定を防止し、レビュー指摘の再現性を上げる。

```xml
<grounding_rules>
Ground every claim in the provided context or your tool outputs.
Do not present inferences as facts.
If a point is a hypothesis, label it clearly.
</grounding_rules>
```

### 9. `citation_rules`

HELIXでの用途: TL/Research/Docs。外部調査、規約確認、比較評価の一次ソース明示。

```xml
<citation_rules>
Back important claims with citations or explicit references to the source material you inspected.
Prefer primary sources.
</citation_rules>
```

### 10. `action_safety`

HELIXでの用途: SE/DBA/DevOps/Security。影響範囲拡大を抑え、不可逆操作前の明示を強制。

```xml
<action_safety>
Keep changes tightly scoped to the stated task.
Avoid unrelated refactors, renames, or cleanup unless they are required for correctness.
Call out any risky or irreversible action before taking it.
</action_safety>
```

### 11. `tool_persistence_rules`

HELIXでの用途: TL/SE。調査不足での早期結論を防ぎ、必要十分な証拠収集を継続する。

```xml
<tool_persistence_rules>
Keep using tools until you have enough evidence to finish the task confidently.
Do not abandon the workflow after a partial read when another targeted check would change the answer.
</tool_persistence_rules>
```

### 12. `research_mode`

HELIXでの用途: Research/TL。L1R・L2の調査系タスクで、事実・推論・未解決を分離する。

```xml
<research_mode>
Separate observed facts, reasoned inferences, and open questions.
Prefer breadth first, then go deeper only where the evidence changes the recommendation.
</research_mode>
```

### 13. `dig_deeper_nudge`

HELIXでの用途: TL/QA/Security。レビュー時の二次障害探索（空状態、再試行、ロールバック）に有効。

```xml
<dig_deeper_nudge>
After you find the first plausible issue, check for second-order failures, empty-state behavior, retries, stale state, and rollback paths before you finalize.
</dig_deeper_nudge>
```

## ブロック選択ガイド（タスクタイプ別）

| タスクタイプ | 推奨ブロック組合せ |
|---|---|
| レビュー | `task` + `grounding_rules` + `dig_deeper_nudge` + `structured_output_contract` |
| 不具合診断 | `task` + `missing_context_gating` + `default_follow_through_policy` + `verification_loop` |
| 最小修正 | `task` + `action_safety` + `completeness_contract` + `verification_loop` + `structured_output_contract` |
| 大規模調査 | `task` + `research_mode` + `citation_rules` + `tool_persistence_rules` + `structured_output_contract` |
| 外部情報比較 | `task` + `citation_rules` + `grounding_rules` + `research_mode` |
| セキュリティ監査 | `task` + `grounding_rules` + `dig_deeper_nudge` + `action_safety` + `verification_loop` |
| API契約レビュー | `task` + `grounding_rules` + `verification_loop` + `structured_output_contract` |
| DB変更提案 | `task` + `action_safety` + `missing_context_gating` + `verification_loop` |
| 実装計画作成 | `task` + `structured_output_contract` + `completeness_contract` |
| Prompt改善 | `task` + `grounding_rules` + `verification_loop` + `structured_output_contract` |
| 仕様不明タスク | `task` + `missing_context_gating` + `compact_output_contract` |

## ロール別ミニ推奨セット

- TL: `task` + `structured_output_contract` + `grounding_rules` + `verification_loop`
- SE: `task` + `default_follow_through_policy` + `action_safety` + `completeness_contract`
- QA: `task` + `grounding_rules` + `dig_deeper_nudge` + `verification_loop`
- Security: `task` + `grounding_rules` + `action_safety` + `dig_deeper_nudge`
- Research: `task` + `research_mode` + `citation_rules` + `tool_persistence_rules`

## 運用メモ

- G2/G3/G4などゲート判定があるタスクでは `structured_output_contract` を優先する。
- 推測で埋める癖が出る場面では `missing_context_gating` を必ず入れる。
- レビュー品質の底上げには `dig_deeper_nudge` と `verification_loop` の同時利用が有効。
- 変更範囲が広がりやすいタスクは `action_safety` を先頭付近に置く。
