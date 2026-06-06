---
plan_id: reverse-2026-06-07-l3-registry-closure
title: "Action2 (Reverse): L3 registry closure — 未登録8件登録 + invalid trace44件解消 + 母数SSoT是正"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-07-whole-source-design-coverage-closure.md
workflow: reverse
kind: reverse
layer: L3
drive: reverse
status: completed
tl_review: approve  # 親 Process の TL impl re-review approve に内包 (zero-omission gate)
created: 2026-06-07
owner: PM
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — 44 invalid trace の要件 ID 割当の read-heavy 補助（機能内容から l1_fr/l3_fr 候補抽出）"
  - role: se
    slot_label: "SE — functional-registry.yaml 編集 + check 回帰テストの実装（Codex）"
forward_return: "L3（functional-registry SSoT 凍結）。touched_layers: [L3]。design_change_class: design_or_contract_changed（registry entry 追加 + trace 接続）。required_refreeze_pairs: なし（L3 台帳 closure、設計層 ID 不変）。refreeze_evidence: check_functional_registry clean baseline（unregistered=0 / invalid_fr_trace=0）。"
generates:
  - artifact_path: cli/config/functional-registry.yaml
    artifact_type: yaml_config
  - artifact_path: docs/v2/L3-requirements/helix-workflows-functional-registry.md
    artifact_type: markdown_doc
dependencies:
  parent: docs/plans/process/process-2026-06-07-whole-source-design-coverage-closure.md
  requires: []
  blocks:
    - docs/plans/reverse/reverse-2026-06-07-coverage-classification.md
---

# Action2 — Reverse: L3 registry closure

## 1. segment1: 未登録 asset 8 件を registry へ登録

| path | domain |
|---|---|
| HELIX-workflows/helix-process/document-topology.md | workflow |
| HELIX-workflows/helix-process/forward-return-discipline.md | workflow |
| HELIX-workflows/helix-process/github-operations.md | workflow |
| HELIX-workflows/helix-process/plan-model.md | workflow |
| HELIX-workflows/helix-process/planning-to-requirements-transition.md | workflow |
| HELIX-workflows/helix-process/workflow-self-evaluation.md | workflow |
| cli/templates/plan/v2/L02-ui-design-template.md | template |
| cli/templates/plan/v2/L06-function-design-template.md | template |

各 entry に id/name/domain/description/l1_fr/l3_fr/code_paths/status を付与（l1_fr/l3_fr は適切な要件 ID へ接続、空にしない）。

## 2. segment2: invalid_fr_trace 44 件の l1_fr/l3_fr 接続

l1_fr と l3_fr が両方空の 44 entry に、各 entry の機能から適切な L1 FR / L3 FR を割当:
- CLI(4): FR-CLI-006, 019, 074, 075
- SKILL(29): FR-SKILL-003,011,012,015,043,047,052,055,056,057,058,071,074,077,079,083,084,089,091,092,093,094,096,097,098,099,101,116,119
- WORKFLOW(3): FR-WORKFLOW-011, 027, 038
- TEMPLATE(8): FR-TEMPLATE-025,026,027,028,029,030,031,083

> 割当は機能内容に基づく judgment。読み取り補助は pmo-sonnet 委譲可。割当先 ID は実在を grep verify。

## 3. 母数 SSoT 是正 + 検出器盲点評価

- registry 実数 = **557**（CLAUDE.md/memory の「548」を是正）。`check_fr_sot_alignment` の md_count_mismatch / md_name_set_mismatch（helix-workflows-functional-registry.md）を解消（yaml⇔md 件数/名前集合一致）。
- `cli/libexec/`(9) が DEFAULT_SCAN_TARGETS に無い盲点を評価 → source なら scan target 追加 or excluded 明記。

## 4. acceptance（exit）

- [ ] `python3 cli/lib/functional_registry_checks.py` → unregistered_asset=0。
- [ ] invalid_fr_trace=0（44 件すべて l1_fr/l3_fr 非空・ID 実在）。
- [ ] `check_fr_sot_alignment`=0（yaml 557 ⇔ md 一致）。
- [ ] clean baseline payload を記録（`build_functional_registry_baseline_payload`）→ 後続 ratchet の起点。
- [ ] pytest（functional_registry_checks 関連）green。
