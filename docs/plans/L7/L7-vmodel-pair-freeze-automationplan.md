---
plan_id: L7-vmodel-pair-freeze-automationplan
title: "L7-vmodel-pair-freeze-automationplan: V-model ペア凍結 (L1↔L14 等) 自動検査フレームワーク構築"
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
    slot_label: "SE — vmodel_pair_freeze.py / helix doctor check 実装"
  - role: qa
    slot_label: "QA — pytest / plan lint / 受入条件検証"
generates:
  - artifact_path: docs/plans/L7/L7-vmodel-pair-freeze-automationplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/vmodel_pair_freeze.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_vmodel_pair_freeze.py
    artifact_type: test
---

## §0 PLAN concept

`L7-drive-agent-l1-l9-state-extplan.md` §11 carry-1 の「各 layer の design ↔ test pair freeze 自動化」を実装で解消する。

- SoT: `HELIX-workflows/helix-process/two-stage-agent-design.md`
- 対象:
  - HELIX V-model ペア凍結 (L1↔L14, L2↔L10, L3↔L12, L4↔L9, L5↔L8, L6↔L7) の存在性を機械検査
  - `advance_layer` や plan lint 進行時に、対応ペアの PLAN 有無を自動確認
  - まず warn-only として段階導入し、fail-close は別 PLAN へ分離

## §1 背景

- 現在、V-model ペア凍結は `CLAUDE.md` / `HELIX_CORE.md` / `SKILL_MAP.md` に記載されるのみで、実機械検査が未整備
- `helix doctor` には plan ADR snapshot 等の機械チェックがあるため、同様のパターンで pair freeze check を追加可能
- 本 PLAN は「検査 API + 既存 doc lint への接続」までの基盤を作る

## §2 scope

1. `cli/lib/vmodel_pair_freeze.py` を新規追加し、以下を実装する  
   - V-model ペア定数 `V_MODEL_PAIRS` を定義 (`L1↔L14` 〜 `L6↔L7`)  
   - `check_pair_freeze(layer, phase)` を実装し `{ok, missing_pair, pair_doc, hints}` を返却  
   - `layer` が対象外・plan path 不在時の hints を返す
2. `cli/lib/tests/test_vmodel_pair_freeze.py` を新規追加し、5+ ケースを追加  
   - 既知ペア存在時は OK  
   - 見つからない場合は missing / hints の期待を検証
3. `helix doctor` への call point を追加  
   - 当該チェックは warn-only 出力（現段階）
   - fail-close 化は carry-1 で別 PLAN

scope 外:

- `helix doctor` fail-close 統合（別 PLAN）
- 実装対象 layer の actual test design 起票自動化（別 PLAN）
- `agent_engine.advance_layer` call site の自動起動（本 PLAN では API のみ、実行部は carry-2）

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | `cli/lib/vmodel_pair_freeze.py` + `cli/lib/tests/test_vmodel_pair_freeze.py`（5 case）を実装 | `pytest` PASS / `py_compile` PASS | completed |
| .2 | `helix doctor` に warn-only check を追加 + bats 対応 | 既存 doctor 動作 + 新規 warn-only 出力 | completed |
| .3 | `docs/plans/L7/L7-drive-agent-l1-l9-state-extplan.md` §11 carry-1 close 準備、integration-map 反映 | `helix plan lint` PASS | completed |

## §4 実装結果

W6-B（Codex SE 並列、settings.json 監視）完遂:
- cli/lib/vmodel_pair_freeze.py 新規 (~80 行): VMODEL_PAIRS 定数 (L1↔L14, L2↔L10, L3↔L12, L4↔L9, L5↔L8, L6↔L7) + get_pair(layer) + check_pair_freeze(layer, project_root)
- cli/lib/tests/test_vmodel_pair_freeze.py 新規 (5/5 PASS)
- cli/helix-doctor 拡張: [V-model pair freeze] section 追加 (warn-only)
- cli/tests/test-helix-doctor-pmo.bats 拡張 (1 test 追加、warn-only 出力確認)

API:
- get_pair('L1') == 'L14' / get_pair('L7') == 'L6' (往復対応)
- get_pair('L0') == None (L0/L11/L13 は pair なし)
- check_pair_freeze(layer, project_root) → {layer, pair, pair_doc_exists, pair_doc_path, status, hint}
- status: 'ok' | 'no_pair' | 'pair_missing'

## §5 検証

- python3 -m pytest cli/lib/tests/test_vmodel_pair_freeze.py -v: 5/5 PASS
- python3 -m py_compile cli/lib/vmodel_pair_freeze.py: PASS
- helix doctor: [V-model pair freeze] △ 11 missing pair docs (warn 出力確認、exit code 0 維持)
- bats cli/tests/test-helix-doctor-pmo.bats: 2/2 PASS（既存 1 + 新規 1）
- git diff --stat .claude/settings.json: 0 差分

### §11 carry

- carry-1: `helix doctor` fail-close 統合（現在は warn-only）
- carry-2: `agent_engine.advance_layer` call site での自動実行（本 PLAN は API/base のみ）
- carry-3: test design doc skeleton の自動展開（別 PLAN）
