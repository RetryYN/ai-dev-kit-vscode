> Adapted from codex-plugin-cc (OpenAI, Apache 2.0)

# Codex Prompt Recipes for HELIX

Codex/GPT-5.4向けレシピをHELIX運用（ロール・フェーズ・ゲート）に合わせて再編成した。
各レシピは「最小構成」で使い、不要なブロックは削って運用する。

## 使い分けの前提

- 診断だけで止めない: 修正が必要なら次レシピへ連結する。
- 証跡を残す: G2/G3/G4/G6対象タスクは構造化出力を優先する。
- 1 run 1責務: レビュー・修正・文書更新を混在させない。

## レシピ1: Diagnosis（診断）

HELIX対応ロール: SE / TL / QA
HELIXフェーズ: L4（実装.1〜.2）, L6（再現確認）
推奨用途: テスト失敗、コマンド失敗、挙動不一致の根本原因特定

```xml
<task>
Diagnose why the failing test or command is breaking in this repository.
Use the available repository context and tools to identify the most likely root cause.
</task>

<compact_output_contract>
Return a compact diagnosis with:
1. most likely root cause
2. evidence
3. smallest safe next step
</compact_output_contract>

<default_follow_through_policy>
Keep going until you have enough evidence to identify the root cause confidently.
Only stop to ask questions when a missing detail changes correctness materially.
</default_follow_through_policy>

<verification_loop>
Before finalizing, verify that the proposed root cause matches the observed evidence.
</verification_loop>

<missing_context_gating>
Do not guess missing repository facts.
If required context is absent, state exactly what remains unknown.
</missing_context_gating>
```

## レシピ2: Narrow Fix（最小安全修正）

HELIX対応ロール: SE（主）, TL（レビュー）
HELIXフェーズ: L4（実装.2〜.5）, G4前
推奨用途: 原因確定済みの不具合に対する局所修正

```xml
<task>
Implement the smallest safe fix for the identified issue in this repository.
Preserve existing behavior outside the failing path.
</task>

<structured_output_contract>
Return:
1. summary of the fix
2. touched files
3. verification performed
4. residual risks or follow-ups
</structured_output_contract>

<default_follow_through_policy>
Default to the most reasonable low-risk interpretation and keep going.
</default_follow_through_policy>

<completeness_contract>
Resolve the task fully before stopping.
Do not stop after identifying the issue without applying the fix.
</completeness_contract>

<verification_loop>
Before finalizing, verify that the fix matches the task requirements and that the changed code is coherent.
</verification_loop>

<action_safety>
Keep changes tightly scoped to the stated task.
Avoid unrelated refactors or cleanup.
</action_safety>
```

## レシピ3: Root-Cause Review（根拠付きレビュー）

HELIX対応ロール: TL / QA / Security
HELIXフェーズ: L2（設計レビュー）, L3（契約レビュー）, L4（コードレビュー）, L6（RC前検証）
推奨用途: 変更差分や設計に対する回帰リスク査読

```xml
<task>
Analyze this change for the most likely correctness or regression issues.
Focus on the provided repository context only.
</task>

<structured_output_contract>
Return:
1. findings ordered by severity
2. supporting evidence for each finding
3. brief next steps
</structured_output_contract>

<grounding_rules>
Ground every claim in the repository context or tool outputs.
If a point is an inference, label it clearly.
</grounding_rules>

<dig_deeper_nudge>
Check for second-order failures, empty-state handling, retries, stale state, and rollback paths before finalizing.
</dig_deeper_nudge>

<verification_loop>
Before finalizing, verify that each finding is material and actionable.
</verification_loop>
```

## レシピ4: Research Or Recommendation（調査・推奨）

HELIX対応ロール: Research / TL / Docs
HELIXフェーズ: L2（方針比較）, L3（採用判断材料作成）, L6（運用準備確認）
推奨用途: 技術選定、外部仕様比較、導入方式の推奨

```xml
<task>
Research the available options and recommend the best path for this task.
</task>

<structured_output_contract>
Return:
1. observed facts
2. reasoned recommendation
3. tradeoffs
4. open questions
</structured_output_contract>

<research_mode>
Separate observed facts, reasoned inferences, and open questions.
Prefer breadth first, then go deeper only where the evidence changes the recommendation.
</research_mode>

<citation_rules>
Back important claims with explicit references to the sources you inspected.
Prefer primary sources.
</citation_rules>
```

## レシピ5: Prompt-Patching（プロンプト改善）

HELIX対応ロール: TL / SE / Docs
HELIXフェーズ: L2（運用設計）, L4（実装効率改善）, L6（品質安定化）
推奨用途: 既存プロンプトの失敗モード分析と最小改善

```xml
<task>
Diagnose why this existing prompt is underperforming and propose the smallest high-leverage changes to improve it for Codex or GPT-5.4.
</task>

<structured_output_contract>
Return:
1. failure modes
2. root causes in the current prompt
3. a revised prompt
4. why the revision should work better
</structured_output_contract>

<grounding_rules>
Base your diagnosis on the prompt text and the failure examples provided.
Do not invent failure modes that are not supported by the examples.
</grounding_rules>

<verification_loop>
Before finalizing, make sure the revised prompt resolves the cited failure modes without adding contradictory instructions.
</verification_loop>
```

## helix-codex実行形式（ロール → レシピ → ブロック組合せ）

| ロール | 優先レシピ | ブロック組合せ（最小） |
|---|---|---|
| TL | Root-Cause Review | `task` + `structured_output_contract` + `grounding_rules` + `dig_deeper_nudge` + `verification_loop` |
| TL | Research Or Recommendation | `task` + `structured_output_contract` + `research_mode` + `citation_rules` |
| SE | Diagnosis | `task` + `compact_output_contract` + `default_follow_through_policy` + `missing_context_gating` |
| SE | Narrow Fix | `task` + `action_safety` + `completeness_contract` + `verification_loop` + `structured_output_contract` |
| QA | Root-Cause Review | `task` + `grounding_rules` + `dig_deeper_nudge` + `verification_loop` |
| Security | Root-Cause Review | `task` + `grounding_rules` + `dig_deeper_nudge` + `verification_loop` |
| Research | Research Or Recommendation | `task` + `research_mode` + `citation_rules` + `structured_output_contract` |
| Docs | Prompt-Patching | `task` + `grounding_rules` + `verification_loop` + `structured_output_contract` |

## フェーズ対応（L2-L6）

| フェーズ | 推奨レシピ | 目的 |
|---|---|---|
| L2 | Root-Cause Review / Research Or Recommendation / Prompt-Patching | 設計判断・比較・運用指針の確定 |
| L3 | Root-Cause Review / Research Or Recommendation | API契約や詳細設計の整合確認 |
| L4 | Diagnosis / Narrow Fix / Prompt-Patching | 実装中の診断・修正・反復改善 |
| L5 | Root-Cause Review（UI/会話体験向け） | 表示・導線・説明文の退行検出 |
| L6 | Root-Cause Review / Diagnosis / Research Or Recommendation | RC前の品質確認と運用判断 |

## 連結パターン（実務向け）

- 障害対応: `Diagnosis` → `Narrow Fix` → `Root-Cause Review`
- 技術選定: `Research Or Recommendation` → `Root-Cause Review`
- プロンプト改善: `Prompt-Patching` → `Diagnosis`（再評価）
- G4前最終確認: `Narrow Fix` 完了後に `Root-Cause Review`

## 運用メモ

- 曖昧要件のまま修正を開始しない。`Diagnosis` で前提を固める。
- 変更範囲を守るため、修正系には `action_safety` を残す。
- 報告形式が固定されるほど、ゲート判定の再現性が上がる。
