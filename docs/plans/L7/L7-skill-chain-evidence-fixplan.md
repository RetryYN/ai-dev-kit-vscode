---
plan_id: L7-skill-chain-evidence-fixplan
title: "L7-skill-chain-evidence-fixplan: skill chain evidence write fix"
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
  - cli/tests/test-helix-skill.bats
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE - skill chain evidence fix owner"
  - role: qa
    slot_label: "QA - skill chain verification"
generates:
  - artifact_path: docs/plans/L7/L7-skill-chain-evidence-fixplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/skill_recommender.py
    artifact_type: code
  - artifact_path: cli/tests/test-helix-skill.bats
    artifact_type: test
dependencies:
  parent: L7-test-failures-triageplan
  requires:
    - docs/plans/L7/L7-test-failures-triageplan.md
  blocks: []
related_docs:
  - cli/tests/test-helix-skill.bats
  - cli/lib/skill_recommender.py
  - cli/lib/llm_classifier_base.py
---

## §1 scope

- `helix skill chain` で recommender prompt が巨大な場合でも安定実行できるようにする
- recommender 実行完了に伴う `entries.axis=evidence` 記録を回復させる

## §2 DoD

- `bats cli/tests/test-helix-skill.bats` PASS
- `helix skill chain "test"` で evidence row が 1 件以上記録される

## §3 実装方針

1. recommender の Codex 呼び出しを `--task` 直渡しから `--task-file` に変更する
2. ARG_MAX 依存の失敗を避ける
3. 既存の classifier evidence insert 契約は維持する
