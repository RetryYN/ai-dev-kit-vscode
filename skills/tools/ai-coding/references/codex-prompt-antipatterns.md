> Adapted from codex-plugin-cc (OpenAI, Apache 2.0)

# Codex Prompt Anti-Patterns for HELIX

HELIX運用で再発しやすいプロンプトの失敗パターンを整理した。
各項目は「悪い例」「改善例」「典型発生場面」をセットで示す。

## 使い方

- 実装.1開始前に1回確認し、該当する癖を除去する。
- G2/G3/G4レビュー時は、失敗パターン混入の有無を点検する。
- 1つのrunで複数アンチパターンが重なる場合は、`task` と `structured_output_contract` を先に固定する。

## 1. Vague task framing（タスク定義が曖昧）

HELIXでの典型発生場面:
- ロール: TL/SE
- フェーズ: L4 実装.1a（初動）
- 兆候: 「見ておいて」「なんか変」のような依頼文

Bad:

```text
Take a look at this and let me know what you think.
```

Better:

```xml
<task>
Review this change for material correctness and regression risks.
</task>
```

改善ポイント:
- 対象（change/test/command）を明示する。
- 期待成果（診断/修正/レビュー）を1つに絞る。

## 2. Missing output contract（出力契約なし）

HELIXでの典型発生場面:
- ロール: TL/QA
- フェーズ: G3/G4判定前
- 兆候: 返答が散文になり、判定材料が不足

Bad:

```text
Investigate and report back.
```

Better:

```xml
<structured_output_contract>
Return:
1. root cause
2. evidence
3. smallest safe next step
</structured_output_contract>
```

改善ポイント:
- ゲート判定に必要な項目を番号付きで固定する。
- 「何を返すか」を先に固定してから作業を開始する。

## 3. No follow-through default（追跡実行方針なし）

HELIXでの典型発生場面:
- ロール: SE
- フェーズ: L4 実装.2〜.3
- 兆候: 原因候補を1つ挙げただけで停止

Bad:

```text
Debug this failure.
```

Better:

```xml
<default_follow_through_policy>
Keep going until you have enough evidence to identify the root cause confidently.
</default_follow_through_policy>
```

改善ポイント:
- 途中停止条件を限定する。
- 「十分な証拠」の獲得を完了条件にする。

## 4. Asking for more reasoning instead of a better contract（思考量要求で代替）

HELIXでの典型発生場面:
- ロール: TL/SE
- フェーズ: L2設計レビュー、L4不具合調査
- 兆候: 「もっと深く考えて」だけで品質を上げようとする

Bad:

```text
Think harder and be very smart.
```

Better:

```xml
<verification_loop>
Before finalizing, verify that the answer matches the observed evidence and task requirements.
</verification_loop>
```

改善ポイント:
- 抽象的な努力要求ではなく、検証手順を契約化する。
- 草案提出ではなく、検証済み回答を要求する。

## 5. Mixing unrelated jobs into one run（無関係タスクの混載）

HELIXでの典型発生場面:
- ロール: TL
- フェーズ: L3〜L4の工程圧縮時
- 兆候: レビュー・修正・文書更新・ロードマップを同時依頼

Bad:

```text
Review this diff, fix the bug you find, update the docs, and suggest a roadmap.
```

Better:
- Run review first.
- Run a separate fix prompt if needed.
- Use a third run for docs or roadmap work.

改善ポイント:
- 1 run 1責務を守る。
- 連結する場合は順序を固定（レビュー → 修正 → 文書）。

## 6. Unsupported certainty（根拠不足の断定要求）

HELIXでの典型発生場面:
- ロール: TL/Research/Security
- フェーズ: L2調査、L6障害分析
- 兆候: 観測不能な事象まで「断定」で報告させる

Bad:

```text
Tell me exactly why production failed.
```

Better:

```xml
<grounding_rules>
Ground every claim in the provided context or tool outputs.
If a point is an inference, label it clearly.
</grounding_rules>
```

改善ポイント:
- 事実・推論・不明点を分離して報告する。
- 推測を「事実」として提出しない。

## HELIX向け予防チェック

- `task` が具体的か（対象、目的、完了条件があるか）。
- `structured_output_contract` または `compact_output_contract` があるか。
- 不確実性がある場合に `missing_context_gating` を入れているか。
- レビュー系で `grounding_rules` と `verification_loop` を併用しているか。
- 変更系で `action_safety` を入れ、範囲逸脱を防いでいるか。

## 失敗時のリカバリ手順

1. 既存プロンプトから曖昧語（look, think harder, exactly）を削る。
2. `task` と `structured_output_contract` を先に固定する。
3. レビュー系なら `grounding_rules` と `dig_deeper_nudge` を追加する。
4. 修正系なら `action_safety` と `completeness_contract` を追加する。
5. 再実行後、出力が契約に一致しているか `verification_loop` で確認する。

## 補足

- HELIXのゲート判定を通すには、回答品質より先に出力契約の固定が重要。
- 「うまく書く」より「誤解されない構造化」を優先する。
