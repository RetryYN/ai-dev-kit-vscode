---
description: PdM Innovation Synthesize — Tech / Marketing 統合
allowed-tools: Read, Grep, Bash, WebSearch, WebFetch
argument-hint: <tech-output.yaml> <marketing-output.yaml> [統合指示]
---

# Purpose

`pdm-innovation-manager` を呼び出し、tech / marketing の 2 つの YAML 出力を統合する。
G0.5 の企画突合へ渡す最終方向性と L1 入力候補の固定を担当する。

# Inputs

- 第 1 引数: tech 側 YAML path
- 第 2 引数: marketing 側 YAML path
- 任意の追加文脈: 統合指示、優先したい制約、社内事情

# Operating Rules

- まず 2 PdM の出力差分を読む
- 矛盾を放置せず、解消方針か保留理由を明示する
- 最終判断前に `tl-advisor` へ 1 回だけ adversarial check を取る
- 出力は YAML に固定し、`cli/templates/plan/innovation-output.yaml.template` の key を守る

# Agent Template

Claude Code セッション内で次を実行する。

```js
Agent({
  subagent_type: "pdm-innovation-manager",
  description: "Tech / Marketing 統合による新方向性策定",
  prompt: `入力:
- tech_output: <第1引数>
- marketing_output: <第2引数>
- 追加指示: <第3引数以降があれば記載>

目的:
- 2 つの PdM 出力を統合し、L1 接続可能な企画入力へ変換する

実行ルール:
- 日本語で簡潔にまとめる
- 出力は YAML
- 必須 keys: concept_summary, strategic_options, assumptions, l1_inputs, g0_5_mapping, risks, decision_log
- 矛盾は strategic_options / risks / decision_log に分離する
- 最終判断前に tl-advisor を 1 回だけ呼ぶ`
})
```

# Output Contract

- YAML template: `cli/templates/plan/innovation-output.yaml.template`
- `strategic_options` は優先順位を持たせる
- `g0_5_mapping` は企画仮説から L1 への橋渡しを明示する
- `decision_log` は統合理由と代替案を残す

# Checklist

- 2 つの入力 YAML の差分が整理されている
- 検証順序がある
- 採択 / 保留 / 見送りが区別されている
- L1 チームが即利用できる粒度まで落ちている
