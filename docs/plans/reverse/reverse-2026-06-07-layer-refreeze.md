---
plan_id: reverse-2026-06-07-layer-refreeze
title: "Action4 (Reverse/forward_refreeze): L6_required を FN/UT 1:1 拡張 + L5/L4_required を既存pair接続 + 再凍結"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-07-whole-source-design-coverage-closure.md
workflow: reverse
kind: reverse
layer: L6
drive: be
status: completed
tl_review: approve  # 親 Process の TL impl re-review approve に内包 (zero-omission gate)
created: 2026-06-07
owner: PM
agent_slots:
  - role: tl-advisor
    slot_label: "TL — FN/UT 粒度 / 再凍結 pair / balance_ratio / refreeze_decision の adversarial check"
  - role: se
    slot_label: "SE — L6 FN-* / L7 UT-* 追補 + trace_symmetry 再計測の補助（Codex）"
forward_return: "required_refreeze_pairs（Action3 分類後に実測確定）。touched_layers: Action3 の coverage_layer 分布で決まる（L6_required→[L6,L7] / L5_required→[L5,L8] / L4_required→[L4,L9]）。design_change_class: design_or_contract_changed（FN/UT universe 拡張）。refreeze_evidence: trace_symmetry L6_required FN↔UT balance_ratio≥1.0 + 各 pair detector green + §11.5 refreeze_decision。"
generates:
  - artifact_path: docs/v2/L6-functional-design/helix-workflows-function-design.md
    artifact_type: markdown_doc
  - artifact_path: docs/v2/L7-test-design/helix-workflows-unit-test-design.md
    artifact_type: markdown_doc
dependencies:
  parent: docs/plans/process/process-2026-06-07-whole-source-design-coverage-closure.md
  requires:
    - docs/plans/reverse/reverse-2026-06-07-coverage-classification.md
  blocks: []
---

# Action4 — Reverse / forward_refreeze: layer-specific refreeze

> スコープは Action3 の分類結果（L6_required/L5_required/L4_required の実数）で**データ駆動的に確定**する。全 557 を FN/UT 化しない（B'、A 却下）。

## 1. L6_required → FN-* + UT-* 1:1 拡張

- Action3 で L6_required に分類された entry（実数は分類後確定）について L6 機能設計 FN-* を追加し、対の L7 単体テスト設計 UT-* を 1:1 で追加。
- 粒度ペアリング原則: 関数1個 = FN 1個 = UT 1個。DbC（requires/ensures/invariant）を各 FN に付与。
- 既存 33 FN-* と重複しないこと（既存被覆分は再利用、design_ids で接続）。

## 2. L5_required / L4_required → 既存 pair 接続

- L5_required: MOD-*（L5 詳細設計）/ IT-*（L8 結合テスト設計）へ design_ids 接続。不足あれば追補。
- L4_required: NFR-* / IF-* / ST-*（L4↔L9）へ接続。不足あれば追補。
- excluded_with_reason: 上位設計 ID への接続のみ（新規 FN/UT 不要）。

## 3. 再凍結（required_refreeze_pairs）

- 影響を受けた pair を forward-return-discipline R1-R5 に従い再凍結（片肺禁止）。
- L6↔L7 は hard 再凍結（FN universe 拡張 = design_change 確定、pure_impl 申告不可）。
- §11.5 refreeze_decision yaml で各 pair の detector 指標 + semantic gate verdict + approvers を記録。

## 4. acceptance（exit = Process zero-omission 宣言の最終条件）

- [ ] L6_required 全 entry に FN-* + UT-* 1:1（trace_symmetry balance_ratio≥1.0、orphan=0）。
- [ ] L5_required/L4_required 全 entry が既存 pair へ design_ids 接続済。
- [ ] registry_design_coverage detector: unknown=0 / missing=0 / wrong_layer=0。
- [ ] 影響 pair すべてが re-freeze（detector green + semantic gate pass）。
- [ ] `check_functional_registry` を ratchet→fail-close 昇格、doctor 0-fail 維持。
- [ ] Process exit gate: `detector_clean AND semantic_gate_pass` 成立 → zero-omission 宣言。
