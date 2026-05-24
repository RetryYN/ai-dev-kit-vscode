---
plan_id: L7-route-engine-4mode-extplan
title: "L7-route-engine-4mode-extplan: route_engine SIGNAL_TO_MODE へ新 4 mode を接続"
kind: impl
layer: L7
drive: be
status: completed
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: cli/lib/route_engine.py
pairs_test_design:
  - cli/tests/test-route-engine-4mode-integration.bats
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 4 mode 入口判定と carry 優先度の確認"
  - role: tl-advisor
    slot_label: "TL — signal/drift_type → mode 契約の adversarial review"
  - role: se
    slot_label: "SE — route_engine.py / pytest / bats / PLAN 実装"
  - role: pmo-sonnet
    slot_label: "PMO — workflow doc / ADR-042 / PLAN trace の整合確認"
generates:
  - artifact_path: cli/lib/route_engine.py
    artifact_type: python_module
  - artifact_path: cli/tests/test-route-engine-4mode-integration.bats
    artifact_type: test
created: 2026-05-25
revised: 2026-05-25
owner: PM
related_docs:
  - HELIX-workflows/helix-process/incident-workflow.md
  - HELIX-workflows/helix-process/scrum-workflow.md
  - HELIX-workflows/helix-process/add-feature-workflow.md
  - HELIX-workflows/helix-process/recovery-workflow.md
  - docs/adr/ADR-042-recommended-command-machine-vs-display-decision.md
  - cli/lib/tests/test_route_engine.py
  - cli/tests/test-route-engine-c8-integration.bats
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本コード**: `cli/lib/route_engine.py`
> **正本 workflow**: Incident / Scrum / Add-feature / Recovery の各 workflow doc

本 PLAN は route_engine に 4 新 mode (`scrum_agile` / `incident` / `add_feature` / `recovery`) を additive に接続し、signal / drift_type の両入口から `RecommendedCommandV1` を返せるようにする。

## §1 scope

- `SIGNAL_TO_MODE` に 4 mode の shortcut signal を追加する
- `VALID_DRIFT_TYPES` に `production_incident` / `agent_runaway` / `feature_addition` / `user_feedback_iteration` を追加する
- `drift --drift-type <new_type>` から 4 mode へ分岐できるようにする
- `recommended_command` を各 mode CLI へ接続する
- `cli/lib/tests/test_route_engine.py` に unit 回帰を追加する
- `cli/tests/test-route-engine-4mode-integration.bats` を新規追加する

scope 外:

- 既存 mode の値変更
- 既存 signal / drift_type の削除
- 4 mode 各 CLI 本体の仕様変更

## §2 実装判断

### §2.1 新 signal 群

| mode | shortcut signal | shortcut drift_type |
|---|---|---|
| `scrum_agile` | `user_feedback_iteration`, `requirement_continuous_refinement` | `user_feedback_iteration` |
| `incident` | `production_incident`, `hotfix_required` | `production_incident` |
| `add_feature` | `feature_addition`, `scope_extension` | `feature_addition` |
| `recovery` | `agent_runaway`, `context_exhaustion` | `agent_runaway` |

### §2.2 RecommendedCommandV1

`recommended_command` は ADR-042 に従い `schema_version` / `command` / `args` / `safety` を返す。

本 repo の CLI 実装を SoT とし、各 mode の接続先は以下とする:

| mode | command | args 方針 |
|---|---|---|
| `scrum_agile` | `helix scrum-agile init` | `{}` |
| `incident` | `helix incident detect` | `incident_id` / `summary` / `severity` / `env` を補う |
| `add_feature` | `helix add-feature add-design` | `feature` / `summary` / `requires_plan` を補う |
| `recovery` | `helix recovery start` | `plan_id` / `reopen_point` を補う |

> 注: TASK_INPUT では `helix recovery init` と書かれているが、2026-05-25 時点の repo 実装 (`cli/lib/recovery_workflow_engine.py`) は `start` が正本であり、この PLAN でも `start` を採用する。

## §3 スプリント

| Sprint | 内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | existing SoT / workflow / ADR 読み込み | 新 signal / drift_type / command 契約確定 | completed |
| .2 | failing test 追加 | pytest / bats の追加ケースが未実装状態で fail する | completed |
| .3 | route_engine.py 実装 | 新 4 mode が additive に接続される | completed |
| .4 | 機械チェックとテスト | py_compile / pytest / bats / plan lint / doctor 実施 | completed |
| .5 | セルフレビューと完了更新 | PLAN status を completed に更新 | completed |

## §4 DoD

- 4 mode mapping が route_engine.py に追加されている
- 既存 pytest 回帰を壊さず、新規 pytest 4 件以上が PASS する
- 新規 bats 4 ケースが PASS する
- ADR-042 schema 形状が維持される
- PLAN status が `draft` から `completed` へ更新される

## §5 検証コマンド

```bash
python3 -m py_compile cli/lib/route_engine.py
python3 -m pytest cli/lib/tests/test_route_engine.py -v
bash -n cli/tests/test-route-engine-4mode-integration.bats
bats cli/tests/test-route-engine-4mode-integration.bats
HOME=/home/tenni ./cli/helix plan lint docs/plans/L7/L7-route-engine-4mode-extplan.md
HOME=/home/tenni ./cli/helix doctor
HOME=/home/tenni ./cli/helix review --uncommitted
```
