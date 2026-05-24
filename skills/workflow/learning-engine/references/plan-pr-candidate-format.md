> 目的: 学習結果を PLAN draft または PR candidate に変換する共通フォーマットを定義する

# PLAN / PR Candidate Format

## PLAN Draft Candidate

```yaml
candidate_type: plan
title: "L7-<topic>-plan"
source_pattern_key: regression:dependency:missing-contract
problem:
  summary: 契約漏れと依存漏れが同時に再発する
  evidence:
    - detector axis-07 fail
    - detector axis-12 fail
    - G9 feedback
proposal:
  target_layer: L4-L9
  scope:
    - docs
    - tests
    - workflow
  non_goals:
    - detector 直接変更
    - 本番設定変更
handoff:
  owner_role: tl
  review_required: true
```

## PR Candidate

```yaml
candidate_type: pr
title: "docs: tighten workflow verification handoff"
source_pattern_key: recovery:runaway:repeat
change_summary:
  - update existing runbook
  - add review checklist
  - clarify escalation note
evidence:
  - recovery-log 3 cases
  - G11 RC feedback
review_gate:
  required: true
  command: helix review --uncommitted
```

## 変換ルール

- 直接コード修正よりも、まず candidate 化を優先する
- detector や gate の変更提案は `review_required: true` を必須にする
- owner_role は TL または PM を基本にし、いきなり実装担当へ直行させない

## 昇格基準

- 同一 `pattern_key` が複数回観測された
- 再発コストが高い
- 学習結果を 1 回の PLAN または 1 本の PR に閉じ込められる
