---
plan_id: reverse-2026-06-07-coverage-classification
title: "Action3 (Reverse): coverage_layer schema 追補 + 全active entry分類(unknown=0) + registry_design_coverage detector 新設"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-07-whole-source-design-coverage-closure.md
workflow: reverse
kind: reverse
layer: L3
drive: reverse
status: completed
created: 2026-06-07
owner: PM
agent_slots:
  - role: tl-advisor
    slot_label: "TL — coverage_layer 分類妥当性 / schema 契約 / detector 契約 の semantic gate"
  - role: pmo-sonnet
    slot_label: "PMO — 540 active entry の coverage_layer 判定根拠抽出（domain 別 read-heavy）"
  - role: se
    slot_label: "SE — registry_design_coverage_checks.py + doctor 接続 + test の実装（Codex、TDD）"
forward_return: "L3 schema 凍結 + 参照設計層 L4/L5/L6。touched_layers: [L3, L4, L5, L6]。design_change_class: design_or_contract_changed（registry schema 拡張 + 全 entry 分類）。required_refreeze_pairs: Action4 で実測（L6_required→L6↔L7 等）。refreeze_evidence: registry_design_coverage detector unknown=0。"
generates:
  - artifact_path: cli/config/functional-registry.yaml
    artifact_type: yaml_config
  - artifact_path: cli/lib/registry_design_coverage_checks.py
    artifact_type: python_module
  - artifact_path: docs/v2/L3-requirements/helix-workflows-functional-registry.md
    artifact_type: markdown_doc
  - artifact_path: docs/v2/L6-functional-design/registry-detector-機能設計.md
    artifact_type: markdown_doc
dependencies:
  parent: docs/plans/process/process-2026-06-07-whole-source-design-coverage-closure.md
  requires:
    - docs/plans/recovery/recovery-2026-06-07-design-coverage-recognition.md
    - docs/plans/reverse/reverse-2026-06-07-l3-registry-closure.md
  blocks:
    - docs/plans/reverse/reverse-2026-06-07-layer-refreeze.md
---

# Action3 — Reverse: coverage classification + detector

## 1. schema 追補（L3 registry 契約拡張）

各 registry entry に field 追加:
- `coverage_layer`: enum `{L6_required, L5_required, L4_required, excluded_with_reason}`
- `design_ids`: list[str]（被覆する設計要素 ID。L6_required→FN-*、L5_required→MOD-*/IT-*、L4_required→NFR-*/IF-*/ST-*）
- `excluded_reason`: str（coverage_layer=excluded_with_reason のとき必須。上位設計 ID も design_ids に必須）

L3 functional-registry doc に schema を SSoT 化。L6 registry-detector 機能設計に detector 契約（DbC: requires/ensures/invariant）を追加。

## 2. 全 active entry（540）分類（unknown=0）

判定基準（Action1 で凍結した B'）:
- **L6_required**: public callable / 独立した振る舞い契約 / DbC 必要（例: guard verdict, validator, db CRUD）
- **L5_required**: module 境界 / 結合 / data flow / 内部 process（例: engine, manager, routing）
- **L4_required**: workflow / architecture / NFR / command family / system interaction（例: helix-* CLI family, workflow doc）
- **excluded_with_reason**: private glue / 生成物 / static template / skill doc（design_id + 理由必須）

読み取り補助は pmo-sonnet 委譲（domain 別に判定根拠抽出）。最終判定は PM、妥当性は TL semantic gate。

## 3. registry_design_coverage detector 新設（Codex, TDD）

`cli/lib/registry_design_coverage_checks.py`:
- 全 active entry に coverage_layer が存在（unknown=0）
- design_ids 非空（excluded も上位 ID 必須）、参照 ID が設計 doc に実在
- coverage_layer と design_id prefix の整合（L6_required↔FN-*, L5↔MOD/IT, L4↔NFR/IF/ST）= wrong_layer 検出
- baseline payload + helix doctor 接続（warn-only で開始、Action4 後 ratchet）

## 4. acceptance（exit）

- [ ] registry schema に coverage_layer/design_ids/excluded_reason が追加され L3 SSoT 化。
- [ ] 540 active entry すべてに coverage_layer（unknown=0）。
- [ ] registry_design_coverage detector: unknown=0 / design_id missing=0 / wrong_layer=0。
- [ ] L6_required entry の実数が確定（→ Action4 の FN/UT 拡張母数）。
- [ ] detector TDD（テスト先行）green、helix doctor に warn-only 接続。
- [ ] TL semantic gate: 分類妥当性 approve。
