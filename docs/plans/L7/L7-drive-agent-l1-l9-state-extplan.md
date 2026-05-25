---
plan_id: L7-drive-agent-l1-l9-state-extplan
title: "L7-drive-agent-l1-l9-state-extplan: carry-2 解消のための L1-L9 state 粒度拡張"
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
    - docs/plans/L7/L7-drive-agent-cli-connectplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — AgentSession / AgentEngine 改修"
  - role: qa
    slot_label: "QA — 単体・CLI テストの受入確認"
generates:
  - artifact_path: docs/plans/L7/L7-drive-agent-l1-l9-state-extplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/agent_engine.py
    artifact_type: python_module
  - artifact_path: cli/helix-agent
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-agent.bats
    artifact_type: test
  - artifact_path: cli/lib/tests/test_agent_engine.py
    artifact_type: test
---

## §0 PLAN concept

`L7-drive-agent-cli-connectplan.md` の carry-2（HELIX W 各 phase 内での L1-L9 詳細 state 管理）を実装で解消する。

対象:
- SoT: `HELIX-workflows/helix-process/two-stage-agent-design.md`
- 設計ターゲット: Phase 1/2 の各 layer 進捗を CLI から追跡できるようにする
- 運用対象: `cli/lib/agent_engine.py`, `cli/helix-agent`

## §1 背景

- 現状の `AgentSession.phase1/phase2/phase3` は 7 field（label / drive / plan_id / status / summary / started_at / completed_at）のみで、L1-L9 の進捗を layer 粒度で記録できない。
- HELIX W（two-stage-agent-design）では Phase 1/2 がそれぞれ L1-L9 を完遂し、Phase 3 が L10-L14 を完遂する設計である。
- `carry-2` は未解決のまま残っているため、CLI からどの layer が未完了かを確認できず、carry クローズできない。

## §2 scope

1. `AgentSession` 拡張
   - `phase1.current_layer: str | None`（L1-L9、未開始なら None）
   - `phase1.layer_history: list[dict]`（`{layer: str, entered_at: iso, completed_at: iso|None}`）
   - `phase2` も同様に追加
   - `phase3` は `PHASE3_LAYERS = L10-L14` を対象とする同一構造
2. `AgentEngine` 拡張
   - `advance_layer(*, phase: 'phase1'|'phase2'|'phase3', layer: str, status: 'entered'|'completed') -> AgentSession` を追加
   - 許可外 layer の指定時は `AgentEngineError`（exit 2）
   - `status='entered'` で `current_layer` を更新し、`layer_history` に新規エントリ追加
   - `status='completed'` で直近エントリに `completed_at` を追記
3. `cli/helix-agent` 拡張
   - `helix agent layer --phase phase1 --layer L4 --status entered|completed` を追加
   - 出力に `current_layer` と `layer_history` 最新 3 件の summary を表示

scope 外:
- 各 layer の design doc / test design pair freeze 自動化（別 PLAN）
- ChartPM / WBS 連携（別 PLAN）
- Phase 1/2 並列実行（別 PLAN）

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | `AgentSession.current_layer` / `layer_history` 追加 + `advance_layer` API 追加 | `python3 -m pytest cli/lib/tests/test_agent_engine.py` で既存 PASS 維持 | completed |
| .2 | `helix agent layer` subcommand 追加 + bats 新規 test 3 件（entered / completed / 不正 layer 拒否） | `bats cli/tests/test-helix-agent.bats` で新規 PASS | completed |
| .3 | `integration-map` drift 解消 + carry-2 close（`L7-drive-agent-cli-connectplan.md` §11 carry-2 を resolved） | `helix plan lint` / `helix doctor` PASS | completed |

## §4 実装結果

W4-B + W4-C 並列で完遂:
- W4-B: `cli/lib/agent_engine.py` 拡張（+186 行） + `cli/lib/tests/test_agent_engine.py`（既存 9 → 14 test、5 件追加で 14/14 PASS）
- W4-C: `cli/helix-agent` layer subcommand 追加 + `cli/tests/test-helix-agent.bats`（既存 4 → 7 test、3 件追加で 7/7 PASS）

API 追加:
- `AgentSession.phase[N].current_layer: str | None`
- `AgentSession.phase[N].layer_history: list[dict]`
- `AgentEngine.advance_layer(phase, layer, status)`
- `CLI: helix agent layer --phase phaseN --layer LN --status entered|completed [--json]`

挙動:
- `status='entered'` で `current_layer` 更新 + `layer_history` 新規 entry append。前 entry が未完了なら auto complete
- `status='completed'` で layer_history 最新 entry に `completed_at` 設定
- 不正な layer / phase / status / completed mismatch は `AgentEngineError exit 2`（fail-close）
- phase 1 / 2 は `PHASE1_LAYERS`（L1-L9）、phase 3 は `PHASE3_LAYERS`（L10-L14）

## §5 検証

- `python3 -m pytest cli/lib/tests/test_agent_engine.py -v`: 14/14 PASS（既存 9 + 新規 5、回帰 0）
- `bats cli/tests/test-helix-agent.bats`: 7/7 PASS（既存 4 + 新規 3）
- `python3 -m py_compile cli/lib/agent_engine.py`: PASS
- `bash -n cli/helix-agent`: PASS
- `helix plan lint docs/plans/L7/L7-drive-agent-l1-l9-state-extplan.md`: PASS

### §11 carry

- carry-1: 各 layer の design ↔ test pair freeze 自動化（V-model 強化、別 PLAN）
- carry-2: Phase 1/2 並列実行（現状は順次のみ、別 PLAN）
