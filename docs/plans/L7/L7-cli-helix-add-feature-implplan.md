---
plan_id: L7-cli-helix-add-feature-implplan
title: "L7-cli-helix-add-feature-implplan: Add-feature mode CLI 実体化"
kind: impl
layer: L7
drive: be
status: completed
created: 2026-05-25
revised: 2026-05-25
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: HELIX-workflows/helix-process/add-feature-workflow.md
pairs_test_design:
  - HELIX-workflows/helix-process/add-feature-workflow.md
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE — cli/helix-add-feature + add_feature_engine + tests 実装"
  - role: pmo-sonnet
    slot_label: "PMO — workflow 接続と 4 artifact trace 確認"
generates:
  - artifact_path: cli/helix-add-feature
    artifact_type: cli_extension
  - artifact_path: cli/lib/add_feature_engine.py
    artifact_type: python_module
  - artifact_path: cli/tests/test-helix-add-feature.bats
    artifact_type: test
  - artifact_path: cli/lib/tests/test_add_feature_engine.py
    artifact_type: test
dependencies:
  parent: L7-helix-workflows-parent-acceptedplan
  requires: []
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/add-feature-workflow.md
  - HELIX-workflows/HELIX-process-L0-L14.md
  - docs/commands/index.md
  - cli/helix
  - cli/lib/command_catalog.py
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: [HELIX-workflows/helix-process/add-feature-workflow.md](../../../HELIX-workflows/helix-process/add-feature-workflow.md)
> **対象**: `helix add-feature` を新規追加し、既存システムへの差分追補フローを `add-design / add-impl / route` 中心の最小 CLI として実体化する。

Add-feature workflow 正本が定義する「影響範囲特定 → 追加設計 → 追加実装 → 既存テスト影響確認 → Vモデル体系へ統合」を、PoC レベルの state 管理と Forward 接続案内に落とし込む。`route_engine` への mode 追加は scope 外とし、`add-feature` 単体で追補状態と接続先レイヤを保持する。

## §1 工程表

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | workflow 正本 / 参考 CLI / 既存 tests 読み込み | SE | ✅ done |
| 2 | `cli/helix` dispatcher / help / docs index へ `add-feature` 追加 | SE | ✅ done |
| 3 | `cli/helix-add-feature` wrapper 実装 | SE | ✅ done |
| 4 | `cli/lib/add_feature_engine.py` 実装 (`add-design` / `add-impl` / `status` / `route`) | SE | ✅ done |
| 5 | `cli/lib/tests/test_add_feature_engine.py` 追加 | SE | ✅ done |
| 6 | `cli/tests/test-helix-add-feature.bats` 追加 | SE | ✅ done |
| 7 | `bash -n` / `py_compile` / `pytest` / `bats` / `plan lint` / `doctor` / `review` 実行 | SE | ✅ done |

## §2 実装要点

- `add-design`: 既存 design PLAN への追補開始を `.helix/add-feature/CURRENT.json` と markdown log に記録し、必要時のみ L1/L3 追補を route に含める
- `add-impl`: 既存 impl PLAN への追補内容、対象 module、追加 test を同 session に記録する
- `status`: 現在の add-feature session を表示し、設計追補と実装追補の紐づきを確認できるようにする
- `route`: workflow doc の「Vモデル体系へ統合」を CLI 応答に反映し、`L4 / L5 / L6 / L7 / L8 / L9` と optional `L1 / L3` を返す

## §3 Scope 外

- `route_engine.SIGNAL_TO_MODE` / `VALID_DRIFT_TYPES` への `add_feature` 追加
- skill 数 drift fix
- 既存 SKILL の修正
- add-feature state の helix.db 永続化

## §4 Verification

- `bash -n cli/helix-add-feature`
- `python3 -m py_compile cli/lib/add_feature_engine.py`
- `python3 -m pytest cli/lib/tests/test_add_feature_engine.py -v`
- `bats cli/tests/test-helix-add-feature.bats`
- `helix plan lint docs/plans/L7/L7-cli-helix-add-feature-implplan.md`
- `helix doctor`
- `helix review --uncommitted`
