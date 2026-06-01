---
doc_id: L3-detailed-design-deprecated-notice
title: "⚠️ DEPRECATED: docs/v2/L3-detailed-design/ (旧世代 L3 詳細設計、参照禁止)"
status: deprecated
deprecated_on: 2026-06-02
owner: PM
process_layer: L3
---

# ⚠️ DEPRECATED — docs/v2/L3-detailed-design/

> **このディレクトリ配下 (D-API / D-DB / D-CONTRACT / exit-validation の全ファイル) は旧世代 (2026-05-16〜18) の L3 詳細設計中間物であり、現行 HELIX V2 体系では参照禁止。**

## 経緯

本ディレクトリは V2 完全移行前の旧 sprint 体系 (PLAN-070 / PLAN-071 / PLAN-084、Phase 3〜4.5) に紐づく設計中間物である。命名 (`-draft-v0.1`)・帰属 PLAN・作成日 (2026-05-16〜18) のいずれも旧世代を示す。現行の正本は以下に置き換わっている:

- **L3 要件定義の正本** → [docs/v2/L3-requirements/](../L3-requirements/) (業務要件 / 機能要件 / 非機能要件 / functional-registry)
- **L4 基本設計の正本** → [docs/v2/L4-basic-design/](../L4-basic-design/) (方式設計 / 機能構成設計 / データ設計 / 外部IF設計)
- **L5 詳細設計の正本** → [docs/v2/L5-detailed-design/](../L5-detailed-design/)

> 注: ディレクトリ名は `L3-detailed-design` だが、内容は本来 **L5 詳細設計** 相当 (API / DB / contract の詳細)。命名自体が drift であり、現行体系では L5 が正本。

## 処分方針 (tl-advisor 2026-06-02 Q4 裁定)

- **本 goal (L0-L3 見直し + L4 完遂) の範囲**: deprecated 宣言 + 参照禁止 marker (本ファイル) + 後続 Retrofit 起票まで。
- **archive 物理移動は別 Retrofit**: `docs/archive/` への退避は、旧 D-API/D-DB/D-CONTRACT の内容 (特に schema 定義・endpoint contract) が現行 L5 詳細設計 doc に吸収済みかを確認した後に実施する。吸収前の即時退避は旧知識の喪失リスクがあるため行わない。
- 起票 Retrofit PLAN: [docs/plans/retrofit/retrofit-2026-06-02-l3-detailed-design-archive.md](../../plans/retrofit/retrofit-2026-06-02-l3-detailed-design-archive.md)

## 参照する場合

設計判断・実装の根拠にしてはならない。歴史的経緯の確認のみを目的とし、現行正本 (上記) を必ず参照すること。
