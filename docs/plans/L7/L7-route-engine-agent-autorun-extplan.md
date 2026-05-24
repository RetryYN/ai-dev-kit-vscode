---
plan_id: L7-route-engine-agent-autorun-extplan
title: "L7-route-engine-agent-autorun-extplan: route_engine SIGNAL_TO_MODE に drive=agent / auto-run を接続"
kind: impl
layer: L7
drive: be
status: completed
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: cli/lib/route_engine.py
pairs_test_design:
  - cli/tests/test-route-engine-agent-autorun-integration.bats
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE — route_engine.py / pytest / bats / PLAN 実装"
generates:
  - artifact_path: docs/plans/L7/L7-route-engine-agent-autorun-extplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/route_engine.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_route_engine.py
    artifact_type: test
  - artifact_path: cli/tests/test-route-engine-agent-autorun-integration.bats
    artifact_type: test
created: 2026-05-25
revised: 2026-05-25
owner: PM
related_docs:
  - HELIX-workflows/helix-process/two-stage-agent-design.md
  - docs/adr/ADR-042-recommended-command-machine-vs-display-decision.md
  - docs/plans/L7/L7-auto-run-loop-frameworkplan.md
  - docs/plans/L7/L7-route-engine-4mode-extplan.md
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本コード**: `cli/lib/route_engine.py`

本 PLAN は route_engine の最後の carry である `drive=agent` と `auto-run` を additive に接続し、shortcut signal / drift_type / `RecommendedCommandV1` を既存契約を壊さず追加する。

## §1 scope

- `SIGNAL_TO_MODE` に `drive_agent` / `auto_run` 接続用 shortcut signal を追加する
- `VALID_DRIFT_TYPES` に `ai_agent_construction` / `long_running_task` を追加する
- `drift --drift-type <new_type>` から `drive_agent` / `auto_run` へ分岐できるようにする
- `recommended_command` を `helix agent init` / `helix auto-run start` に接続する
- `cli/lib/tests/test_route_engine.py` に unit 回帰を追加する
- `cli/tests/test-route-engine-agent-autorun-integration.bats` を新規追加する

scope 外:

- 既存 signal / drift_type / mode の削除や変更
- `cli/helix-agent` / `cli/helix-auto-run` 本体仕様の変更
- auto-run framework や HELIX W workflow 自体の拡張

## §2 実装判断

### §2.1 signal / drift_type

| mode | shortcut signal | shortcut drift_type |
|---|---|---|
| `drive_agent` | `ai_agent_construction`, `agent_design_required` | `ai_agent_construction` |
| `auto_run` | `long_running_task`, `context_exhaustion_predicted` | `long_running_task` |

### §2.2 RecommendedCommandV1

`recommended_command` は ADR-042 に従い `schema_version` / `command` / `args` / `safety` を返す。

| mode | command | args 方針 |
|---|---|---|
| `drive_agent` | `helix agent init` | `agent_id` / `summary` / `phase1_drive` を placeholder で補う |
| `auto_run` | `helix auto-run start` | `plan_id` / `duration_minutes` を placeholder で補う |

## §3 スプリント

| Sprint | 内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | existing SoT / workflow / ADR 読み込み | signal / drift_type / command 契約確定 | completed |
| .2 | failing test 追加 | pytest / bats の追加ケースが未実装状態で fail する | completed |
| .3 | route_engine.py 実装 | 2 mode が additive に接続される | completed |
| .4 | 機械チェックとテスト | py_compile / pytest / bats / plan lint / doctor / review 実施 | completed |
| .5 | セルフレビューと完了更新 | PLAN status を completed に更新 | completed |

## §4 DoD

- 2 mode mapping が route_engine.py に追加されている
- 既存 pytest 回帰を壊さず、新規 pytest 4 件以上が PASS する
- 新規 bats が PASS する
- ADR-042 schema 形状が維持される
- PLAN status が `draft` から `completed` へ更新される

## §5 検証コマンド

```bash
python3 -m py_compile cli/lib/route_engine.py
python3 -m pytest cli/lib/tests/test_route_engine.py -v
bash -n cli/tests/test-route-engine-agent-autorun-integration.bats
bats cli/tests/test-route-engine-agent-autorun-integration.bats
HOME=/home/tenni ./cli/helix plan lint docs/plans/L7/L7-route-engine-agent-autorun-extplan.md
HOME=/home/tenni ./cli/helix doctor
HOME=/home/tenni ./cli/helix review --uncommitted
```
