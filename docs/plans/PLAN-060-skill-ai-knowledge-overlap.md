---
plan_id: PLAN-060
title: "PLAN-060（リファクタリング C: AI knowledge 重複検証 + skill 廃止判定）"
status: finalized
created: 2026-05-11
author: "PM (Opus)"
priority: medium
size: M
phases_affected: "skills/**/SKILL.md / SKILL_MAP.md"
parent_plan: PLAN-058
acceptance:
  overlap_score_table:
    verification_commands: { command: "test -f docs/audit/ai-knowledge-overlap-2026-05.md", expected: "exists (Sonnet/Opus 自己判定の冗長度スコア表生成済)" }
  redundant_skills_removed:
    verification_commands: { command: "before_count - after_count", expected: ">= 5 (HELIX 固有付加価値ゼロと判定された skill を 5 件以上廃止)" }
finalized: 2026-05-10
---

# PLAN-060: リファクタリング C - AI knowledge 重複検証 + skill 廃止判定

## §1 背景

ユーザー指示「AI の知識にあった不要そうなものを洗い出してくれ」。
各 skill を Sonnet 4.6 / Opus 4.7 に問い合わせ、base knowledge で代替可能なものを廃止候補化。

## §2 検証アプローチ

各 SKILL.md を以下の 3 質問で AI に評価:

1. **Q1**: このスキルの内容を base knowledge で answer 可能か? (Yes/No、確信度)
2. **Q2**: HELIX 固有の付加価値 (harness / hook / budget guard / orchestration 統合等) は何か?
3. **Q3**: 廃止した場合、何が失われるか? (具体的シナリオ)

スコア化:
- Q1=Yes (high confidence) かつ Q2 が空 or 抽象的 → 廃止候補
- Q1=Yes だが Q2 で具体的 HELIX 統合 → 維持 + brush up
- Q1=No → 維持 (固有知識)

## §3 解消対象 (予想)

廃止候補のサンプル (要 AI 評価):
- common/coding (基本コーディング tips、AI base 知識で十分)
- common/refactoring (リファクタリング原則、AI base で十分)
- writing/explain (説明文の書き方、AI base で十分)
- automation/* の一部 (古い PoC、現行 helix CLI で代替済)

維持確定:
- workflow/* (HELIX フロー固有)
- tools/ai-coding (HELIX harness 統合)
- integration/agent-design (axis 11 本の独自体系)
- agent-skills/* (addyosmani 由来、HELIX 統合済)

## §4 Sprint 構成

| Sprint | 内容 | 委譲先 |
|---|---|---|
| W-0 | draft + TL Round 1 + finalize | PM |
| W-1 | 全 106+ SKILL.md を Sonnet/Opus に Q1-Q3 自己判定させて JSON 集計 | Codex docs + Sonnet |
| W-2 | docs/audit/ai-knowledge-overlap-2026-05.md 監査表生成 | Codex docs |
| W-3 | 廃止候補レビュー → 廃止決定 → SKILL_MAP / ファイル削除 | Opus + Codex |
| W-final | 統合検証 + retro + push | Opus |

## §5 Out of Scope

- skill 解像度 brush up (PLAN-059)
- 全 skill の rewrite (大型作業、別 PLAN)

## §6 リスク

- AI 自己判定が「knowledge cutoff の違い」で揺れる → 複数モデル合議 (Sonnet 4.6 + Opus 4.7) で signal 強化
- 廃止後にユーザーが実は参照していた場合 → 削除前に PR レビューで確認、git revert で復元可
