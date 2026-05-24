---
plan_id: L7-drive-agent-cli-connectplan
title: "L7-drive-agent-cli-connectplan: two-stage-agent-design Stage2 の CLI 起動 roadmap"
kind: design
layer: L7
drive: agent
status: completed
process_layer: L7
parent_design: HELIX-workflows/helix-process/two-stage-agent-design.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - HELIX-workflows/helix-process/integration-map.md
    - HELIX-workflows/helix-process/HELIX-process-L0-L14.md
  blocks: []
agent_slots:
  - role: tl-advisor
    slot_label: "TL — drive=agent CLI 連携仕様の最終整備"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN 構造と SoT 整合性のチェック"
generates:
  - artifact_path: docs/plans/L7/L7-drive-agent-cli-connectplan.md
    artifact_type: design_doc
  - artifact_path: cli/helix-agent
    artifact_type: cli_extension
  - artifact_path: cli/lib/agent_engine.py
    artifact_type: python_module
  - artifact_path: cli/tests/test-helix-agent.bats
    artifact_type: test
  - artifact_path: cli/lib/tests/test_agent_engine.py
    artifact_type: test
---

## §0 PLAN concept

HELIX Workflows two-stage-agent-design の Stage 2（agent）を `helix agent` から起動可能にし、Phase 1/2/3 の routing を HELIX CLI に接続する。

対象:
- SoT: `HELIX-workflows/helix-process/two-stage-agent-design.md`
- 目的: `helix agent` 系の起動経路を実装し、HELIX W の開始点を CLI に追加する
- スコープ: `cli/helix-agent` / `cli/lib/agent_engine.py` / `vmodel-semantics` / tests / docs の同期

## §1 背景

- V2 で既存 9 mode CLI は完了しているが、`drive=agent` の orchestration は未接続。
- two-stage-agent-design は文書として存在する一方、helix CLI からの直接起動テンプレート・運用ルートが未確定。
- 既存 `helix-agent` は slot/audit 系のみであり、HELIX W の phase state 管理と route は未実装だった。
- 本 PLAN で HELIX W の state engine と `helix agent init/stage1/stage2/merge/route` を実装し、route_engine 接続は carry に残す。

## §2 scope

1. `cli/helix-agent` に `init / stage1 / stage2 / merge / route` を追加する。
2. `cli/lib/agent_engine.py` で `.helix/agent/CURRENT.json` と Phase 1/2/3 route を管理する。
3. `cli/config/vmodel-semantics.yaml` に `agent` drive を追加し、Phase 2 の注入契約を定義する。
4. `cli/tests/test-helix-agent.bats` と `cli/lib/tests/test_agent_engine.py` で最小 PASS を固定する。
5. `docs/commands/index.md` と `integration-map.md` を実装状態へ同期する。

scope 外:
- route_engine から `drive=agent` を自動提案する接続
- HELIX W 各 phase 内での L1-L9 詳細 state 管理

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | SoT/依存再確認と既存 `helix-agent` 差分把握 | additive 拡張方針を確定 | completed |
| .2 | `agent_engine.py` と `helix-agent` workflow subcommand 実装 | Phase 1/2/3 state を `CURRENT.json` で保持できる | completed |
| .3 | semantics / docs / tests 同期 | `agent` drive と command index が一致し、最小回帰が通る | completed |

## §4 実装結果

- `helix agent init/stage1/stage2/merge/route` を追加し、既存 slot/audit subcommand は維持した。
- `cli/lib/agent_engine.py` を新設し、Phase 1 (`be|fe|db|fullstack`) / Phase 2 (`agent`) / Phase 3 (`L10-L14 merge`) の route を管理した。
- `cli/config/vmodel-semantics.yaml` に `agent` drive を追加し、HELIX W Phase 2 の注入契約を定義した。
- `docs/commands/index.md` と `integration-map.md` を実装状態へ同期した。

## §5 検証

- `bash -n cli/helix-agent`
- `python3 -m py_compile cli/lib/agent_engine.py`
- `python3 -m pytest cli/lib/tests/test_agent_engine.py -v`
- `bats cli/tests/test-helix-agent.bats`
- `helix plan lint docs/plans/L7/L7-drive-agent-cli-connectplan.md`
- `helix doctor`

## §11 carry

- carry-1: route_engine から `drive=agent` を直接提案する接続は別 PLAN で扱う
- carry-2: HELIX W 各 phase 内のより詳細な state 管理（L1-L9 粒度）は後続で拡張する
