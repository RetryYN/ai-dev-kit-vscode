---
doc_id: observability-metrics
title: "HELIX 観測・計測機構（発火・トラブル計測と実行ログ）"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# HELIX 観測・計測機構

## 概要

コマンド・スキル・サブエージェントの発火とトラブルを計測し、AI の実行ログを自動取得して、改善（learning-engine.md）へつなぐ観測層。Learning Engine の入力を供給する。

## AI 実行ログの自動取得

Claude Code の hook（libexec）が実行イベントを捕捉し、helix_db へ記録する。

| hook | 捕捉イベント | 記録先 |
|---|---|---|
| helix-session-start | セッション開始 | （セットアップ状態） |
| helix-pre-bash | bash 実行前（harness 経由を強制） | action_logs |
| helix-post-tool-use | Edit / Write 後（変更ファイル抽出） | action_logs / invocation_log |
| codex_post_hook | Codex 実行後 | accuracy_score |
| feedback_hook | ゲート通過後（5軸 Lv1–5） | （feedback） |

AI が何を実行し、何を変更したかが、これらの hook で自動的にログ化される。

## 発火計測

| 対象 | 仕組み | テーブル |
|---|---|---|
| スキル発火 | skill_dispatcher / skill_jsonl_schema | invocation_log |
| コマンド呼び出し | invocation log | invocation_log |
| サブエージェント起動 | agent_mandatory / action 記録 | action_logs |

## トラブル計測

| 対象 | 仕組み | テーブル |
|---|---|---|
| ゲート失敗 | gate_audit_metrics / gate_runs | gate runs |
| 精度低下 | accuracy_score（codex_post_hook） | accuracy_score |
| 予算超過 | budget_events | budget_events |
| recovery 発生 | recovery freshness（doctor） | （recovery log） |
| interrupt 頻度 | interrupt 履歴 | （interrupt） |

## メトリクス集約

helix-bench / dashboard が上記を集約し、メトリクススナップショットを出す。発火回数・トラブル率・精度スコアを一望できる。

## 改善ロジック（learning-engine へ）

計測・ログを Learning Engine（learning-engine.md）が分析し、改善へ回す。

| 入力 | 改善 |
|---|---|
| スキル発火統計 | skill_recommender / skill_review で推薦を調整 |
| トラブル頻度 | 予防ルール（gate / detector）へ昇格 |
| 精度スコア（accuracy_score） | L 単位注入（layer-context-injection）の見直し |
| recovery / interrupt 頻度 | 発生源の工程・モードを特定して対策 |

## 観測 → 改善ループ

```
AI 実行
   → hook（session-start / pre-bash / post-tool-use / codex_post / feedback）で自動ログ
   → 発火計測・トラブル計測（invocation_log / action_logs / gate_runs / accuracy_score / budget_events）
   → helix-bench / dashboard で集約
   → learning_engine が分析 → 改善（推薦調整 / 予防ルール化 / 注入見直し）
   → L 単位注入の更新（layer-context-injection）
   → AI 実行
```

## まとめ

発火・トラブル計測も AI 実行ログの自動取得も、既存資産（libexec hooks、helix_db の invocation_log / action_logs / audit_log / automation_runs / accuracy_score / budget_events、skill_dispatcher、bench / dashboard）で成立する。新規に必要なのは、これらの計測値を learning-engine の改善ロジックへ結線する配線部分のみで、計測・記録の土台はすでに揃っている。
