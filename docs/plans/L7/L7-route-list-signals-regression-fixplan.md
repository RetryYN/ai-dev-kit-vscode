---
plan_id: L7-route-list-signals-regression-fixplan
title: "L7-route-list-signals-regression-fixplan: route list-signals contract drift fix"
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
  - cli/tests/helix-route.bats
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE - route list-signals regression fix owner"
  - role: qa
    slot_label: "QA - route contract verification"
generates:
  - artifact_path: docs/plans/L7/L7-route-list-signals-regression-fixplan.md
    artifact_type: design_doc
  - artifact_path: cli/tests/helix-route.bats
    artifact_type: test
dependencies:
  parent: L7-test-failures-triageplan
  requires:
    - docs/plans/L7/L7-test-failures-triageplan.md
  blocks: []
related_docs:
  - cli/tests/helix-route.bats
  - cli/lib/route_engine.py
---

## §1 scope

- `helix route list-signals` の legacy 固定件数期待を現行契約へ更新する
- 9 mode 拡張後も brittle にならないよう、text 出力と `--json` 出力の整合を確認する

## §2 DoD

- `bats cli/tests/helix-route.bats` PASS
- `bats cli/tests/test-route-engine-c8-integration.bats` PASS
- `bats cli/tests/test-route-engine-4mode-integration.bats` PASS

## §3 実装方針

1. fixed line count assertion を除去する
2. 代表 signal と alias の存在は維持する
3. text 行数と JSON 件数の一致、alias 件数 1 件を検証する
