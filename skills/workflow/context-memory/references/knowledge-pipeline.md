# ナレッジ蓄積パイプライン

> 出典: v-model-reference-cycle-v2.md §ナレッジ蓄積フロー

## 収集タイミング

| タイミング | 収集内容 | 自動/手動 |
|------------|----------|-----------|
| エラー解決後 | 原因・解決策・回避策 | 自動（解決パターン検出） |
| 手戻り発生時 | 見積もり誤りの原因・実際の複雑さ | 自動 |
| 検証パス時 | 成功パターン・有効だったアプローチ | 自動 |
| T5達成時 | 品質達成に寄与した要因 | 自動 |
| 人間指摘時 | 指摘内容・改善点 | 手動（重要度高） |
| 新規ライブラリ導入時 | 使い方・ハマりポイント・ベストプラクティス | 半自動 |

## 分類体系

| カテゴリ | サブカテゴリ | 用途 |
|----------|-------------|------|
| error_patterns | runtime_errors, build_errors, test_failures, integration_issues | エラー再発防止 |
| solution_patterns | debugging_techniques, performance_fixes, security_patches, refactoring_patterns | 解決策の再利用 |
| architecture_decisions | tech_selection, tradeoff_analysis, scaling_strategies | 設計指針 |
| domain_knowledge | business_rules, edge_cases, regulatory_requirements | 業務理解 |
| tooling | cli_tips, ide_shortcuts, library_gotchas | 効率化 |

### タグ定義

| タグ軸 | 値 |
|--------|-----|
| severity | critical / major / minor / info |
| reusability | project_specific / cross_project / universal |
| confidence | proven / experimental / deprecated |

## 重要度判定基準

ナレッジを記録すべきかの判定:
```
記録する条件（AND）:
  1. 同じエラー/パターンが過去に記録されていない
  2. 解決に3ターン以上かかった

例外（即記録）:
  - 人間からの指摘 → severity=critical, confidence=proven で即保存
```

## ケーススタディテンプレート

```yaml
id: CASE-{連番}
title: "問題の1行要約"
category: "{カテゴリ}.{サブカテゴリ}"
tags:
  severity: critical/major/minor/info
  reusability: project_specific/cross_project/universal
  confidence: proven/experimental

context:     # いつ・どこで
  project: ""
  task_id: ""
  tech_stack: []

problem:     # 何が起きたか
  症状: ""
  影響範囲: ""

solution:    # どう解決したか
  approach: ""
  verification: ""

lessons:     # 何を学んだか
  - ""

applicability:  # いつ使えるか
  when_to_apply: []
  contraindications: []
```

## スキル化判定

蓄積されたナレッジをスキルに昇格させる基準:
```
条件（AND）:
  1. 同一カテゴリに3件以上のケースが蓄積
  2. reusability が cross_project 以上
  3. confidence が proven
→ パターン抽出 → スキル候補として提案
```
