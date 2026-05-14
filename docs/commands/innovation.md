# helix innovation

## 概要

`helix innovation` は、PdM Innovation 系 subagent を起動するための prompt を生成する補助 CLI です。
対象はプロダクト企画 phase の G0.5 前後で、tech / marketing / synthesize / team の 4 導線を持ちます。

現時点では dispatcher 未登録のため、本タスク範囲では `cli/helix-innovation` を直接呼びます。

## 書式

```text
cli/helix-innovation <subcommand> [options]
```

Subcommands:

- `tech --task "..."`  
  `pdm-tech-innovation` 向け prompt を生成する
- `marketing --task "..."`  
  `pdm-marketing-innovation` 向け prompt を生成する
- `synthesize --task "..." --tech-output PATH --marketing-output PATH`  
  `pdm-innovation-manager` 向け prompt を生成する
- `team --task "..." [--definition PATH]`  
  innovation team 定義を使った orchestration prompt を生成する

共通で `--execute` を指定できますが、CLI から Agent tool を直接呼び出さず、Claude Code セッション内での推奨実行を強調するだけです。

## 前提

- `cli/templates/plan/innovation-output.yaml.template` が出力契約の正本
- tech / marketing / manager の subagent 定義が `.claude/agents/` に存在すること
- team 実行は `cli/templates/teams/innovation-team.yaml` を参照すること

## tech

```bash
cli/helix-innovation tech --task "Stripe Engineering を日本向けに翻案"
```

- 目的: 海外技術思想を日本向けの企画判断に翻案する
- 推奨 subagent: `pdm-tech-innovation`
- 出力契約: YAML (`concept_summary`, `strategic_options`, `assumptions`, `l1_inputs`, `g0_5_mapping`, `risks`, `decision_log`)

## marketing

```bash
cli/helix-innovation marketing --task "PLG を国内 B2B SaaS に翻案"
```

- 目的: 海外マーケ思想を日本市場向けの仮説へ翻案する
- 推奨 subagent: `pdm-marketing-innovation`
- 出力契約: tech と同じ YAML template を使う

## synthesize

```bash
cli/helix-innovation synthesize \
  --task "2 PdM 出力を統合" \
  --tech-output docs/innovation/tech.yaml \
  --marketing-output docs/innovation/marketing.yaml
```

- 目的: 2 つの YAML 出力を比較し、`pdm-innovation-manager` へ統合させる
- 必須入力:
  - `--tech-output`
  - `--marketing-output`
- 補助方針: 最終判断前に `tl-advisor` を 1 回だけ挟む想定

## team

```bash
cli/helix-innovation team --task "新規プロダクト企画の方向性を整理"
```

- 目的: 3 PdM + 関連 PMO の段取りをまとめて提示する
- 参照定義: `cli/templates/teams/innovation-team.yaml`
- 推奨実行: `helix team run --definition cli/templates/teams/innovation-team.yaml`

## 出力契約

出力 YAML は `cli/templates/plan/innovation-output.yaml.template` に揃えます。
最低限次の keys が必要です。

- `concept_summary`
- `strategic_options`
- `assumptions`
- `l1_inputs`
- `g0_5_mapping`
- `risks`
- `decision_log`

この形式に揃えておくと、G0.5 の企画突合から L1 要件入力への変換がしやすくなります。

## 利用例

新規プロダクト企画の開始時に、まず tech / marketing を別々に走らせ、YAML を保存します。
その後 `synthesize` で統合し、必要なら `team` 導線で一括オーケストレーションへ切り替えます。

## 関連コマンド

- `helix claude` — Claude Code 向け prompt harness
- `helix team` — team yaml を使った複数 role 実行
- `helix research` — 企画前提の調査テーマ生成
