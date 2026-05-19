---
plan_id: PLAN-090
title: "PLAN-090: PostToolUse continueOnBlock refactor"
layer: L4
status: Draft
created: 2026-05-19
owner: PM
depends_on:
  - PLAN-087
  - PLAN-089
related_docs:
  - docs/plans/PLAN-087-design-doc-web-search-guardrail.md
  - docs/plans/PLAN-089-gate-fail-close-design-doc-web-search-audit.md
  - .claude/settings.json
  - .claude/hooks/posttooluse-design-doc-web-search-revert.sh
  - cli/helix-gate
---

# PLAN-090: PostToolUse continueOnBlock refactor

## 1. メタ情報

- **Plan ID / Status**: PLAN-090 / Draft
- **Created**: 2026-05-19
- **Owner**: PM
- **関連依存**: PLAN-087 / PLAN-089
- **関連 ADR**: なし

## 2. 目的

`PostToolUse` hook で従来の `stderr` + `exit 1` 警告運用（warn-only）を廃止し、Claude Code 2.1.139 で追加された `continueOnBlock` を用いた `exit 2 + JSON decision` へ移行する。これにより、reject reason を Claude が同一ターン内で受け取り、原因を理解して Web 検索等を再実行してリトライできる「active guidance loop」を実現し、過去の self-inflicted revert を含む二重防御の warning 運用を、機能は維持しつつ制御精度に寄せる。

## 3. 背景（W10 pmo-tech-news 調査結果）

- **W10 調査日**: 2026-05-19
- **事実**: Claude Code 2.1.139 にて `PostToolUse` の `continueOnBlock` が公式に追加され、`PostToolUse` の `decision: "block"`（従来は警告表示で完結）が原因を返してターン継続する動作を明示サポート。
  - 参考: Changelog: https://code.claude.com/docs/en/changelog
  - 参考: Hooks reference: https://code.claude.com/docs/en/hooks
- **過去課題との整合**: PLAN-089 の W10 carry で提示された `continueOnBlock` 検討は未着手だったため、W10 での検証価値が高い。
- **制御不一致事例**: Issue #24327 の再現観測では、`PreToolUse` で `exit 2` が原因提示にも関わらずターンが停止する現象が報告され、モデル解釈の一貫性を意識した実行ループ設計が必要な文脈を示した。
  - 参考: https://github.com/anthropics/claude-code/issues/24327

## 4. 業界 standard 参照（Web 検索 3 query 以上）

| クエリ | 参照元 | 参照意図 |
|---|---|---|
| Claude Code 2.1.139 PostToolUse continueOnBlock specification | https://code.claude.com/docs/en/changelog | 2.1.139 の `continueOnBlock` 追加点を公式ログ確認 |
| JSON-based hook response Claude Code | https://code.claude.com/docs/en/hooks | Hook の `decision/block` と `hookSpecificOutput`、トップレベル JSON 制御の仕様を確認 |
| active guidance loop AI agent retry pattern | https://tinyagents.dev/blog/what-is-the-agent-loop | Agent loop（Think→Act→Observe→Repeat）と失敗時の再試行/フィードバックの一般原則を参照 |

### 追加参照（実装/運用観点）

- PostToolUse decision control（公式）: https://code.claude.com/docs/en/hooks
- `continueOnBlock`/`ok: false` の扱い（公式）: https://code.claude.com/docs/en/hooks
- OpenAI Agents SDK retry（再試行制御方針）: https://openai.github.io/openai-agents-js/zh/guides/models/
- LangGraph fault tolerance（エラー制御で再試行方針を分離）: https://docs.langchain.com/oss/python/langgraph/fault-tolerance

## 5. 採用根拠

- **continueOnBlock 採用理由**: `PostToolUse` で block 理由を警告として表示するだけでは、hook が要求する再試行ワークフローに自然接続しづらい。`continueOnBlock: true` は “拒否後に継続” を制御するため、目的に合致。
- **JSON 出力採用理由**: Hook 側の `decision/hookSpecificOutput` を structured に返すことで、`reason` を曖昧な文言で投げるのではなく、次ターンの観測可能な制御情報として扱える。
- **exit 2 化（旧 0/exit 1 の見直し）**: 本 hook の意図は「品質防御に不適合」を検知し、次アクションを誘導することであり、`exit 2`（制御ブロックに相当）へ整理するのが明快。

## 6. 背景条件・制約

- 変更対象は `.claude/settings.json` の PostToolUse 設定（matcher: `posttooluse-design-doc-web-search-revert`）と hook script `.claude/hooks/posttooluse-design-doc-web-search-revert.sh`。
- hook 本体の Bash 互換構造は維持し、出力形式のみ JSON 化。
- この PLAN は実装 1 つのみで、追加スキーマ変更/DB 変更は含まない。

## 7. Phase 構成（S サイズ・3 Sprint 想定）

### Phase 1（Sprint .1、約 30 min）
- `.claude/settings.json` に対して対象 matcher (`PostToolUse` の design-doc-web-search-revert) の settings を `continueOnBlock: true` へ変更。
- 影響対象: 対象 matcher は `PostToolUse` の design-doc-web-search-revert hook のみ。

### Phase 2（Sprint .2、約 1 h）
- `.claude/hooks/posttooluse-design-doc-web-search-revert.sh` の出力を `JSON` 化。
- 既存 `stderr` 文字列を廃止し、`decision/hookSpecificOutput` を中心とした構造化出力へ。
- 結果は `exit 2` で返却。

### Phase 3（Sprint .3、約 30 min）
- smoke test 7 ケースを 9 ケースへ拡張（7ケースを上位方針テストに同梱）。
- 拡張後に PostToolUse 再テストを更新し、`continueOnBlock` 効果をケース化。

## 8. DoD

- settings.json に `continueOnBlock: true` が反映。
- 該当 hook が `JSON` + `decision: "block"` + `exit 2` を返す。
- `smoke test` が 9/9 PASS。
- **Issue #24327** 干渉: 実機では本 refactor 直後に 48h watch し、PostToolUse 由来の待機/停止干渉を確認（または非再現）をエビデンス化。

## 9. 互換性

- Bash 実装は現行構造を維持し、出力整形のみ変更。
- 前方互換性を優先対象外（互換互換レイヤは持たない）。
- フル移行可能なため deprecation 記述は行わない。

## 10. 検証

- 既存 smoke test 7 ケースを 9 ケースへ拡張（`Plan 起票系` / `Plan 既存保護` / `WebSearch 残骸` / `matcher 適用外` / `re-enter` など）
- 検証観点
  - `continueOnBlock` が有効時は warning 停止ではなく continue すること
  - `reason` を JSON で受け取り、Claude 側再試行の誘導材料になっていること
  - 非対象 matcher では既定動作（False Positiveを抑止）が変わらないこと
- 監査:
  - `rg "continueOnBlock|2.1.139|Anthropic|JSON" docs/plans/PLAN-090-posttooluse-continueonblock-refactor.md` は 5 件以上
- 48h watch を経て Issue #24327 干渉がないことを本番想定環境で確認。

## 11. carry / rollback

- Rollback は `.claude/settings.json` から `continueOnBlock` 行を削除し、hook 出力を従来 warn-only（`stderr` + `exit 1`）へ一時復帰。
- マイグレーション追加や backward compat 専用分岐は不要。

## 12. V-model 4 artifact trace

- **設計 artifact**: 本 PLAN（`docs/plans/PLAN-090-...md`）
- **実装 artifact**: `.claude/settings.json` / `.claude/hooks/posttooluse-design-doc-web-search-revert.sh`
- **テスト設計 artifact**: 本 PLAN 内「Phase 3（smoke 9ケース）」を「smoke 拡張仕様」として明示
- **テストコード artifact**: `.claude/hooks/posttooluse-design-doc-web-search-revert.sh` に付随する既存 smoke テスト更新（テスト名・期待値含む）

## 13. 関連 memory feedback（本 session 5 + 過去 3）

- `feedback_design_doc_web_search_required`
- `feedback_codex_parallel_dependency_check`
- `feedback_no_user_ask_tl_advisor_self_drive`
- `feedback_codex_parallel_dependency_check`（関連再掲）
- `feedback 追加ログ（PLAN-089 継続 carry 系）`
- `feedback 追加ログ（自己復旧 pattern）`
