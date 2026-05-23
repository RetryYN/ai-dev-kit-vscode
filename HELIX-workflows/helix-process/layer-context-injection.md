---
doc_id: layer-context-injection
title: "L 単位 文脈注入機構"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# L 単位 文脈注入機構

## 概要

各 L（工程）に、専門スキル・ワークフロー・サブエージェント・コマンド・オーケストレーション方式を注入し、AI の判断の迷いを消す機構。L に入ると選択空間が「その工程で使うもの」に絞られ、AI は一から判断せず、注入された定義に沿って実行する。

## 注入する5要素

すべて既存部品で構成される。

| 注入要素 | 既存部品 | 効果 |
|---|---|---|
| スキル | skill_catalog / skill-radar | 工程に専門性を持たせる |
| ワークフロー | L 工程ファイル（L0–L14）＋ モードワークフロー | 手順を固定し迷わせない |
| サブエージェント | agent_mandatory.list_mandatory_for_phase（MANDATORY_SUBAGENTS） | L 別の必須 role を提示 |
| コマンド | command_catalog | L 別の推奨コマンドを提示 |
| オーケストレーション | helix-matrix / agent_slots / axis-14-orchestration-integrity | 協調方式を制御・検証 |

注入は helix-context が担い、L 別の責任は vmodel-semantics の owner_role が定義する。

## AI の判断の迷いを消す原理

```
L に入る
   → helix-context が L の文脈を注入
   → スキル（専門性）+ ワークフロー（手順）+ 必須 agent + 推奨 command + orchestration 方式
   → AI の選択空間が「この工程で使うもの」に絞られる
   → AI は一から判断せず、注入された選択肢から実行する
```

選択肢を事前に絞ることが、迷いを消す。AI は「何を使うか」を毎回考える代わりに、L に紐づいた定義を使う。これは「AI 判断を減らし機械側に寄せる」方針（automation-gate-map.md）の、入力側の実装にあたる。

## L 単位の注入セット（定義場所）

vmodel-semantics.yaml の各 layer に、注入セットを定義する（owner_role / detector は既存、ここに skill 群・推奨 command・orchestration 方式を加える）。

| layer（工程） | owner_role | 必須 agent | スキル群 | 推奨 command | orchestration |
|---|---|---|---|---|---|
| planning（L0–L1） | PM | pm-advisor | 企画・要求系 | plan / size | 単線（PM 主導） |
| requirement（L3） | PM / TL | pm-advisor / tl-advisor | 要件系 | plan / gate | Claude 判断主体 |
| architecture（L4） | TL | tl-advisor | 設計系 | gate / detect | Claude 判断 → Codex 実装 |
| detailed（L5） | TL / SE | tl-advisor / se | 詳細設計系 | gate / db | Claude 判断 → Codex 実装 |
| functional（L6–L7） | SE | se / qa | 実装・テスト系 | test / verify | Codex 実装 → QA 検証 |
| FE（L2 / L10） | fe | fe | design-tools 系 | （FE detector） | Claude 設計 → 実装 |

## オーケストレーション方式の制御

- agent_slots（PLAN）で、誰がどの役割を担うかを宣言する。
- Claude Code（判断）/ Codex（実装）の二軸を L 別に割り当てる。
- axis-14-orchestration-integrity が、宣言した協調方式と実際の整合を検証する。
- helix-matrix で協調マトリクスを compile・制御する。

## 効果

- L 単位で専門性・手順・agent・command・方式が注入され、AI の選択の迷いが消える。
- 横断機構（cross-cutting-mechanisms.md）や検出連携（detection-routing.md）と整合し、L 文脈に応じた自動化が一貫する。
- どの工程でも「この L では何を使い、誰が、どう協調するか」が事前に定まるため、AI の独断専行の余地が縮まり、Recovery の発動頻度も下がる。
