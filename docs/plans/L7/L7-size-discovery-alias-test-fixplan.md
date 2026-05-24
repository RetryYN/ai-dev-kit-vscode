---
plan_id: L7-size-discovery-alias-test-fixplan
title: "L7-size-discovery-alias-test-fixplan: size discovery alias test drift fix"
kind: troubleshoot
layer: L7
drive: be
status: completed
created: 2026-05-25
revised: 2026-05-25
owner: SE
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: docs/plans/L7/L7-test-failures-triageplan.md
pairs_test_design:
  - cli/tests/helix-size-drive-auto.bats
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE - discovery alias test fix owner"
  - role: qa
    slot_label: "QA - size alias verification"
generates:
  - artifact_path: docs/plans/L7/L7-size-discovery-alias-test-fixplan.md
    artifact_type: design_doc
  - artifact_path: cli/tests/helix-size-drive-auto.bats
    artifact_type: test
dependencies:
  parent: L7-test-failures-triageplan
  requires:
    - docs/plans/L7/L7-test-failures-triageplan.md
  blocks: []
related_docs:
  - cli/tests/helix-size-drive-auto.bats
  - cli/helix-size
---

## §1 scope

- `scrum` legacy alias の test 期待を `discovery` 正規化へ更新する
- `--drive scrum` では deprecation warning を確認する

## §2 DoD

- `bats cli/tests/helix-size-drive-auto.bats` PASS
- runtime の `scrum` alias 受理は維持し、出力は `discovery` へ正規化される

## §3 実装方針

1. `--uncertain` 系の JSON 期待を `drive/mode=discovery` に更新する
2. auto 判定 stderr は従来どおり残す
3. `--drive scrum` は deprecated stderr を追加確認する
