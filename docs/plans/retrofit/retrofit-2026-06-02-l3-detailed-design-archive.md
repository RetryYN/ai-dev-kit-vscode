---
plan_id: retrofit-2026-06-02-l3-detailed-design-archive
title: "Retrofit: docs/v2/L3-detailed-design/ 旧世代 doc の L5 吸収確認 + archive 退避"
kind: retrofit
layer: L5
drive: be
status: draft
created: 2026-06-02
owner: PM
forward_return: "Retrofit → Forward L5 詳細設計 — 旧 doc 内容 (D-API/D-DB/D-CONTRACT schema・endpoint contract) が現行 L5 正本に吸収済か確認後、docs/archive/ へ退避し L5 正本へ一本化"
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・archive 可否の最終判断"
  - role: pmo-sonnet
    slot_label: "PMO — 旧 doc 内容と L5 正本の吸収状況 diff"
generates:
  - artifact_path: docs/v2/L3-detailed-design/DEPRECATED.md
    artifact_type: markdown_doc
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - docs/v2/L3-detailed-design/DEPRECATED.md
  - docs/v2/L5-detailed-design/
---

# Retrofit Plan: docs/v2/L3-detailed-design/ 旧世代 doc の archive

> `plan_scope: process`（駆動 = Retrofit 行程）。本 PLAN は L0-L3 見直し session (2026-06-02) で検出した drift の **後続処分**を登録する。本 session では deprecated 宣言 + 参照禁止 marker までを完了し、archive 物理移動は本 Retrofit で別途扱う（tl-advisor 2026-06-02 Q4 裁定: 即時退避は旧知識喪失リスク）。

## §1 目的
`docs/v2/L3-detailed-design/` (D-API / D-DB / D-CONTRACT / exit-validation 計 14 file、PLAN-070/071/084 旧 sprint、2026-05-16〜18) を、現行 L5 詳細設計正本へ吸収確認した上で `docs/archive/` へ退避し、drift 源を解消する。

## §2 背景
- ディレクトリ名は `L3-detailed-design` だが内容は本来 **L5 詳細設計** 相当 = 命名自体が drift。
- 現行正本 = [docs/v2/L5-detailed-design/](../../v2/L5-detailed-design/)。旧 doc と内容が大半被る。
- 即時削除/退避は、L5 に未吸収の schema/contract 知識を失うリスクがある。

## §3 実装計画 (段階 rollout)
1. **吸収確認**: 旧 D-DB schema 定義・D-API/D-API-CARRY endpoint contract が現行 L5 doc に反映済かを pmo-sonnet で diff。
2. **未吸収抽出**: 未吸収の設計知識を L5 正本へ back-port (別 Forward L5 作業として接続)。
3. **archive 退避**: 吸収確認後、`docs/v2/L3-detailed-design/` → `docs/archive/` へ移動 (DEPRECATED.md は退避先に同梱)。
4. **参照 scan**: 退避前に repo 全体で当該 path 参照を grep し、生きた参照があれば現行正本へ張替。

## §4 受入条件 / DoD
- 14 file それぞれ「L5 吸収済 / 未吸収 (→ back-port)」が記録されている。
- 未吸収知識が L5 正本へ反映され、Forward L5 へ接続されている。
- `docs/v2/L3-detailed-design/` への生きた参照が 0 件。
- archive 退避完了、`helix doctor` の document drift warn が当該分減少。

## §5 forward_return (Forward 接続先)
Retrofit → **Forward L5 詳細設計**。吸収・back-port 完了をもって L5 正本へ収束し、HELIX DB の document trace 管理対象とする。

## §6 関連
- 起点 marker: [docs/v2/L3-detailed-design/DEPRECATED.md](../../v2/L3-detailed-design/DEPRECATED.md)
- 現行正本: [docs/v2/L5-detailed-design/](../../v2/L5-detailed-design/)
