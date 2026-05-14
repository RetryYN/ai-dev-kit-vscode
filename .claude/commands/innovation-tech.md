---
description: PdM Tech Innovation — 海外技術思想 → 日本版翻案
allowed-tools: Read, Grep, Bash, WebSearch, WebFetch
argument-hint: <翻案対象の海外技術思想 / フレームワーク名>
---

# Purpose

`pdm-tech-innovation` を呼び出し、海外技術思想を日本向けの新規プロダクト企画へ翻案する。
この slash command は G0.5 前後の比較材料づくりを想定する。

# Inputs

- 引数: `$ARGUMENTS`
- 企画の狙い、対象顧客、制約、短期 KPI
- 既存の競合調査や社内メモがあれば同時に読む

# Operating Rules

- 直接実装へ進めず、企画判断に必要な材料へ落とす
- 技術原文をそのまま輸入しない
- ライセンス、契約、後戻りコストに不確実性があれば `tl-advisor` へ 1 回だけ確認する
- 出力は YAML に固定し、`cli/templates/plan/innovation-output.yaml.template` の key を守る

# Agent Template

Claude Code セッション内で次を実行する。

```js
Agent({
  subagent_type: "pdm-tech-innovation",
  description: "海外技術思想の日本版翻案",
  prompt: `対象テーマ: ${ARGUMENTS}

目的:
- 海外技術思想を日本向けのプロダクト企画判断へ翻案する

実行ルール:
- 日本語で簡潔にまとめる
- 出力は YAML
- 必須 keys: concept_summary, strategic_options, assumptions, l1_inputs, g0_5_mapping, risks, decision_log
- 必要なら pmo-tech-docs の一次情報補助を使う
- 最終方向性の断定は pdm-innovation-manager に委譲する`
})
```

# Output Contract

- YAML template: `cli/templates/plan/innovation-output.yaml.template`
- `strategic_options` では採用条件と反対論を併記する
- `assumptions` は検証方法まで含める
- `l1_inputs` は要件化チームがそのまま分解できる粒度で書く
- `decision_log` は判断理由と撤退条件を残す

# Checklist

- 技術原点と日本の運用制約が切り分けられている
- 採用条件が曖昧な断定になっていない
- L1 へ引き継ぐ入力候補が明示されている
- 高リスク項目が `risks` に逃げず、必要な前提条件と結びついている
