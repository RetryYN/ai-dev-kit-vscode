---
plan_id: PLAN-059
title: "PLAN-059（リファクタリング B: skill 解像度監査 + brush up）"
status: completed
created: 2026-05-11
completed: 2026-05-11
author: "PM (Opus)"
priority: medium
size: L
phases_affected: "skills/**/SKILL.md / SKILL_MAP.md"
parent_plan: PLAN-058
acceptance:
  audit_table_generated:
    verification_commands: { command: "test -f docs/audit/skill-resolution-2026-05.md && wc -l docs/audit/skill-resolution-2026-05.md | awk '{print $1}", expected: ">= 100 (全 skill の解像度評価表が生成済)" }
  low_resolution_brushed:
    verification_commands: { command: "low_resolution_count_after - low_resolution_count_before", expected: "減少 (低解像度判定 skill の半数以上を brush up または廃止)" }
finalized: 2026-05-10
---

# PLAN-059: リファクタリング B - skill 解像度監査 + brush up

## §1 背景

ユーザー指示「スキルの解像度が低いもの」を洗い出して brush up または廃止。
106+ スキルを以下の評価軸で分類し、低解像度を改善。

## §2 評価軸 (5 軸)

1. **description 具体性**: 文字数 (< 80 文字 = 低)、抽象的キーワード (「○○関連」「全般」等) 検出
2. **triggers 明示**: SKILL.md frontmatter に triggers 記述があるか
3. **references 充実度**: references/ ディレクトリ + ファイル数
4. **最終更新日**: git log で 6 ヶ月以上更新無し = 低
5. **SKILL_MAP からの整合性**: SKILL_MAP.md で参照されているか、孤立していないか

## §3 解消対象

予想される低解像度 skill (Opus 直感ベース、要監査確認):
- common/* の一部 (refactoring / git / documentation 等、AI base knowledge と重複しがち)
- automation/* の一部 (古い PoC スキル)
- 参照されない skill (孤立)

## §4 Sprint 構成

| Sprint | 内容 | 委譲先 |
|---|---|---|
| W-0 | draft + TL Round 1 + finalize | PM |
| W-1 | 全 106+ SKILL.md を 5 軸でスコアリング (Codex docs 委譲、JSON 出力) | Codex docs |
| W-2 | docs/audit/skill-resolution-2026-05.md 監査表生成 | Codex docs |
| W-3 | 低解像度 skill のうち brush up 対象 (description / triggers / references 追加) | Codex docs |
| W-4 | 低解像度 skill のうち廃止対象 (SKILL_MAP から削除、ファイル削除) | Opus + Codex |
| W-final | 統合検証 + retro + push | Opus |

## §5 Out of Scope

- AI knowledge 重複検証 (PLAN-060)
- 全 skill のフォーマット統一 (別 PLAN)

## §6 リスク

- 廃止判定で孤立判定が誤り、実は使用中だった場合 → grep / ai-coding harness 内呼び出し確認必須
