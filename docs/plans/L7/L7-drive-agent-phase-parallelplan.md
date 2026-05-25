---
plan_id: L7-drive-agent-phase-parallelplan
title: "L7-drive-agent-phase-parallelplan: drive-agent Phase 1/2 並列実行を実装で解決"
kind: impl
layer: L7
drive: agent
status: completed
revised: '2026-05-25'
process_layer: L7
parent_design: HELIX-workflows/helix-process/two-stage-agent-design.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - HELIX-workflows/helix-process/two-stage-agent-design.md
    - docs/plans/L7/L7-drive-agent-l1-l9-state-extplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — AgentEngine 改修 / CLI subcommand 実装"
  - role: qa
    slot_label: "QA — pytest / bats / 既存回帰確認"
generates:
  - artifact_path: docs/plans/L7/L7-drive-agent-phase-parallelplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/agent_engine.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_agent_engine.py
    artifact_type: test
  - artifact_path: cli/helix-agent
    artifact_type: cli_extension
---

## §0 PLAN concept

`L7-drive-agent-l1-l9-state-extplan.md` §11 carry-2 を解消し、HELIX W の `drive=agent` で Phase 1（be/fe/db/fullstack）と Phase 2（agent）を並列進行可能とする。

- SoT: `HELIX-workflows/helix-process/two-stage-agent-design.md`
- 対象:
  - `AgentSession.current_phase` を複数同時進行に対応する `active_phases: list[str]` へ移行
  - `start_phase / pause_phase / resume_phase` API 追加
  - `helix agent phase start|pause|resume` subcommand を追加

## §1 背景

- 現状は `phase1 ready → phase2 in_progress → merge → phase3` の順次進行で、Phase 1 / Phase 2 の並列化条件を表現できない
- two-stage-agent-design では各 phase が実質独立で、順序依存が小さい範囲は並列化対象
- 本 PLAN では現状 API と CLI を最小変更で拡張し、merge 必要な Phase 3 依存は既存フローを維持する

## §2 scope

1. `cli/lib/agent_engine.py` / `cli/lib/tests/test_agent_engine.py` を変更して、`AgentSession.current_phase` 廃止へ向けて `active_phases` を導入
   - `start_phase(phase)`  
   - `pause_phase(phase)`  
   - `resume_phase(phase)`  
   - legacy 参照互換として `current_phase` は `active_phases[0]` で表示
2. `cli/helix-agent` を追加変更し、以下 subcommand を追加  
   - `helix agent phase start --phase phase1|phase2|phase3`  
   - `helix agent phase pause --phase phaseN`  
   - `helix agent phase resume --phase phaseN`
3. 既存テストを壊さずに並行開始/一時停止/再開ロジックを 5+ 検証

scope 外:

- Phase 3 と Phase 1/2 の merge 依存最適化（別 PLAN）
- Phase 内 sub-phase の並列化（別 PLAN）
- `AgentSession.current_phase` を完全削除する破壊的改修（別 PLAN）

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | `active_phases` + start/pause/resume API 追加（既存 14 test 保護） | `pytest` 既存 PASS | completed |
| .2 | `helix agent phase` subcommand 追加 + bats 3 cases | `bats` 既存 + 新規 PASS | completed |
| .3 | `docs/plans/L7/L7-drive-agent-l1-l9-state-extplan.md` §11 carry-2 close + integration-map 反映 | `helix plan lint` PASS | completed |

## §4 実装結果

W6-C（Codex SE 並列、settings.json 監視）完遂:
- cli/lib/agent_engine.py: AgentSession.active_phases: list[str] 追加 + start_phase/pause_phase/resume_phase API + current_phase property 化 (legacy compat)
- cli/lib/tests/test_agent_engine.py: 7 test 追加（既存 14 + 新規 7 = 21/21 PASS、回帰 0）
- cli/helix-agent: phase subcommand 追加 (start/pause/resume)
- cli/tests/test-helix-agent.bats: 3 test 追加（既存 7 + 新規 3 = 10/10 PASS）

API:
- start_phase(phase) → active_phases に追加 + status: in_progress
- pause_phase(phase) → active_phases から削除 (status 維持)
- resume_phase(phase) → active_phases に再追加
- current_phase property → active_phases[0] or 'phase1' default
- from_dict legacy compat: active_phases なし → ['phase1'] default 補完

CLI:
- helix agent phase start --phase phase2
- helix agent phase pause --phase phase1
- helix agent phase resume --phase phase1

## §5 検証

- python3 -m pytest cli/lib/tests/test_agent_engine.py -v: 21/21 PASS
- bats cli/tests/test-helix-agent.bats: 10/10 PASS
- python3 -m py_compile cli/lib/agent_engine.py: PASS
- bash -n cli/helix-agent: PASS
- git diff --stat .claude/settings.json: 0 差分

### §11 carry

- carry-1: Phase 3 の merge 必須制約が残るため並列対象外
- carry-2: 各 phase 内の L1-L9 layer 並列は別 PLAN（今 PLAN は phase 並列のみ）
