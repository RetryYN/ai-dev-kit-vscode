---
description: PdM Marketing Innovation — 海外マーケ思想 → 日本版翻案
allowed-tools: Read, Grep, Bash, WebSearch, WebFetch
argument-hint: <翻案対象の海外マーケ思想 / フレームワーク名>
---

# Purpose

`pdm-marketing-innovation` を呼び出し、海外マーケティング思想を日本市場向けの仮説へ翻案する。
企画初期の市場仮説、導線仮説、検証順の整理に使う。

# Inputs

- 引数: `$ARGUMENTS`
- 対象顧客、価格帯、想定導線、競合状況
- 利用できる一次情報や既存の仮説ノート

# Operating Rules

- 技術採用判断はここで断定しない
- KPI を増やしすぎず、検証順と撤退条件を先に決める
- 市場規模や顧客像の確度は明示する
- 出力は YAML に固定し、`cli/templates/plan/innovation-output.yaml.template` の key を守る

# Agent Template

Claude Code セッション内で次を実行する。

```js
Agent({
  subagent_type: "pdm-marketing-innovation",
  description: "海外マーケティング思想の日本市場向け翻案",
  prompt: `対象テーマ: ${ARGUMENTS}

目的:
- 海外マーケティング思想を日本市場向け仮説へ翻案する

実行ルール:
- 日本語で簡潔にまとめる
- 出力は YAML
- 必須 keys: concept_summary, strategic_options, assumptions, l1_inputs, g0_5_mapping, risks, decision_log
- KPI は最小限に絞る
- 技術判断が必要なら pdm-tech-innovation または pdm-innovation-manager にエスカレーションする`
})
```

# Output Contract

- YAML template: `cli/templates/plan/innovation-output.yaml.template`
- `strategic_options` は対象セグメントと検証条件を含める
- `assumptions` は反証条件も書く
- `l1_inputs` は受入条件や検証観点へ変換できる粒度にする
- `decision_log` は採択・保留・見送りの理由を残す

# Checklist

- 顧客仮説が日本市場前提に翻案されている
- 指標が過剰になっていない
- 反証条件と撤退条件がある
- 技術判断を混ぜずに企画入力へ落ちている
