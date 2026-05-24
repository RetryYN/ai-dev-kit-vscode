---
plan_id: L7-cli-helix-incident-implplan
title: "L7-cli-helix-incident-implplan: Incident (hotfix) mode CLI 実装"
kind: impl
layer: L7
drive: be
status: completed
created: 2026-05-25
revised: 2026-05-25
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: HELIX-workflows/helix-process/incident-workflow.md
pairs_test_design:
  - HELIX-workflows/helix-process/incident-workflow.md
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE — cli/helix-incident + incident_engine + tests 実装"
  - role: pmo-sonnet
    slot_label: "PMO — 4 artifact trace と workflow 接続確認"
generates:
  - artifact_path: cli/helix-incident
    artifact_type: cli_extension
  - artifact_path: cli/lib/incident_engine.py
    artifact_type: python_module
  - artifact_path: cli/tests/test-helix-incident.bats
    artifact_type: test
  - artifact_path: cli/lib/tests/test_incident_engine.py
    artifact_type: test
dependencies:
  parent: L7-helix-workflows-parent-acceptedplan
  requires: []
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/incident-workflow.md
  - HELIX-workflows/HELIX-process-L0-L14.md
  - cli/helix-recovery
  - cli/helix-retrofit
  - cli/lib/recovery_workflow_engine.py
  - cli/lib/retrofit_engine.py
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: [HELIX-workflows/helix-process/incident-workflow.md](../../../HELIX-workflows/helix-process/incident-workflow.md)
> **対象**: `helix incident` を新規追加し、`detect / triage / hotfix / postmortem / route` の最小 CLI を PoC レベルで実体化する。

Incident workflow 正本の「検出 → トリアージ → 緊急修正 → 収束確認 → 事後昇華」を CLI と state file に落とし込み、hotfix 後の恒久対策を `L1 / L3 / L4-L6 / L8 / L9 / L14` へ明示ルーティングする。`route_engine` への接続は scope 外とし、Incident 側は昇華先の準備情報のみ返す。

## §1 工程表

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | workflow 正本 / 参考 CLI / 既存 tests 読み込み | SE | ✅ done |
| 2 | `cli/helix` dispatcher / help / docs index へ incident 追加 | SE | ✅ done |
| 3 | `cli/helix-incident` wrapper 実装 | SE | ✅ done |
| 4 | `cli/lib/incident_engine.py` 実装 | SE | ✅ done |
| 5 | `cli/lib/tests/test_incident_engine.py` 追加 | SE | ✅ done |
| 6 | `cli/tests/test-helix-incident.bats` 追加 | SE | ✅ done |
| 7 | `bash -n` / `py_compile` / `pytest` / `bats` / `plan lint` / `doctor` / `review` 実行 | SE | ✅ done |

## §2 実装要点

- `detect`: `.helix/incident/CURRENT.json` と incident log を初期化し、本番 / 開発環境から `kind` 初期値を決める
- `triage`: owner / impact / severity / kind を確定し、hotfix 前の分類結果を session に反映する
- `hotfix`: 暫定収束の記録と release ref を保持し、収束後の formalization 判定へ進める
- `postmortem`: timeline と forward formalization を markdown 化する
- `route`: workflow doc §恒久対策接続を CLI 応答に反映し、`L1 / L3 / L4-L6 / L8 / L9 / L14` を返す

## §3 Scope 外

- `route_engine.SIGNAL_TO_MODE` / `VALID_DRIFT_TYPES` への incident 追加
- 新規 skill 作成
- Incident state の helix.db 永続化

## §4 Verification

- `bash -n cli/helix-incident`
- `python3 -m py_compile cli/lib/incident_engine.py`
- `python3 -m pytest cli/lib/tests/test_incident_engine.py -v`
- `bats cli/tests/test-helix-incident.bats`
- `helix plan lint docs/plans/L7/L7-cli-helix-incident-implplan.md`
- `helix doctor`
- `helix review --uncommitted`
