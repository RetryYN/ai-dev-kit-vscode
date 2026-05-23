---
doc_id: learning-engine
title: "HELIX Learning Engine（ログ学習機構）"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# HELIX Learning Engine（ログ学習機構）

## 概要

スキル発火・トラブル・成功実行のログから学び、recipe（成功パターン）として蓄積・再利用する機構。helix-learn（learning_engine）が担う。analyze_success で成功実行を分析し、save_recipe で pattern_key 付き recipe として保存する。

## 学習の入力

自動登録（db-auto-registration.md）で蓄積されたログを入力にする。

| 入力源 | 内容 |
|---|---|
| 成功実行（analyze_success） | 成功した run の手順 |
| feedback_hook | ゲート通過後の5軸 Lv1–5 フィードバック |
| skill 発火ログ（skill-radar） | どのスキルがいつ発火したか |
| recovery-log | AI 暴走・収束の履歴 |
| interrupt 履歴 | 割り込みの種別・頻度 |
| detector 結果 | drift / 劣化 / 回帰の検出履歴 |

## 学習の処理

- analyze_success で成功 run を分析し、save_recipe で pattern_key 付き recipe として保存する。
- 頻出トラブル（recovery / interrupt / detector fail の繰り返し）をパターン化し、予防ルール（gate / detector）へ昇格させる。

## 学習の出力（フィードバック）

| 出力 | 効果 |
|---|---|
| recipe 再利用 | 成功パターンを次回に適用 |
| スキル推薦改善 | skill-radar の選択精度向上 |
| 予防ルール化 | 頻出トラブルを gate / detector で事前検出 |
| L 単位注入の更新 | layer-context-injection の注入セットを改善 |

## 学習ループ

```
ログ蓄積（db-auto-registration）
   → 学習（analyze_success → save_recipe）
   → 予防ルール化 / 推薦改善
   → L 単位注入の更新（layer-context-injection）
   → 実行
   → ログ蓄積
```

成功は recipe として再利用され、トラブルは予防ルールに変わる。学んだ結果が L 単位の文脈注入に反映されるため、同じ迷い・同じトラブルが繰り返されにくくなる。
