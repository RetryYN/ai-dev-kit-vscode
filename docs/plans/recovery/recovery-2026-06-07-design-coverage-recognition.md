---
plan_id: recovery-2026-06-07-design-coverage-recognition
title: "Action1 (Recovery): design coverage の defer 継続不可を認識訂正し zero-omission=B' を凍結"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-07-whole-source-design-coverage-closure.md
workflow: recovery
kind: recovery
layer: L3
drive: reverse
status: draft
created: 2026-06-07
owner: PM
agent_slots:
  - role: tl-advisor
    slot_label: "TL — defer→zero-omission 方針変更 / L6_required 線引き / B' acceptance の adversarial check"
forward_return: "L3 policy / verification-strategy evidence。touched_layers: [L1, L3]。design_change_class: design_or_contract_changed（zero-omission 定義=新 acceptance を要件/検証戦略に追加）。required_refreeze_pairs: L3↔L12（verification-strategy の acceptance 変更）。refreeze_evidence: §11 recipe に B' 判定を追補。"
generates:
  - artifact_path: docs/v2/L1-requirements/helix-workflows-verification-strategy.md
    artifact_type: markdown_doc
  - artifact_path: docs/v2/L3-requirements/helix-workflows-functional-registry.md
    artifact_type: markdown_doc
dependencies:
  parent: docs/plans/process/process-2026-06-07-whole-source-design-coverage-closure.md
  requires: []
  blocks:
    - docs/plans/reverse/reverse-2026-06-07-coverage-classification.md
---

# Action1 — Recovery recognition（認識訂正）

> Recovery は層でなく横断モード。逸脱起点 = **L3 inventory/coverage classification model の欠落**（既存ソースがどの設計層で被覆されるべきかの分類が無く、DF-WCAUDIT-L6L7-001 を defer したまま「完了」扱いしていた認識ズレ）。

## 1. 認識訂正（recovery-workflow step3: 逸脱起点特定）

- これまで `DF-WCAUDIT-L6L7-001`（設計未定義の残関数）を Phase3 **defer** として deferred finding に記録 = 「設計に既存ソースが未反映」を許容していた。
- goal「抜け漏れ一切禁止」により **defer 継続は不可**。zero-omission を新 acceptance とする方針変更を明示する。

## 2. zero-omission=B' の凍結（acceptance 化）

- verification-strategy §11（whole-coverage audit recipe）に B' 定義と coverage_layer 判定基準を追補:
  - `L6_required` 判定基準を**明文化**（public callable / 独立振る舞い契約 / DbC 必要。これに当たらない infra/glue/workflow doc/template は L5/L4/excluded）。「L6 逃げ」防止のため、L4/L5 被覆時も design_id 必須・excluded は理由必須。
- L3 functional-registry doc（FR-FNREG-01 周辺）に「全 active entry は coverage_layer を持つ」を SSoT 要件として追加。

## 3. acceptance（exit）

- [ ] verification-strategy §11 に B' 定義 + coverage_layer 判定基準（特に L6_required 線引き）が凍結されている。
- [ ] L3 functional-registry doc に「coverage_layer 必須 / unknown=0」が要件化されている。
- [ ] DF-WCAUDIT-L6L7-001 の deferred 状態を「supersede（zero-omission Process へ巻取り）」に更新。
- [ ] L3↔L12（受入）の acceptance 変更を re-freeze evidence として記録。
