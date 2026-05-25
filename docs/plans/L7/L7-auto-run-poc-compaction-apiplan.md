---
plan_id: L7-auto-run-poc-compaction-apiplan
title: "L7-auto-run-poc-compaction-apiplan: auto-run compaction API 統合 PoC"
kind: poc
layer: L7
drive: be
status: draft
process_layer: L7
parent_design: HELIX-workflows/helix-process/continuous-run-context-management.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - HELIX-workflows/helix-process/continuous-run-context-management.md
    - docs/plans/L7/L7-auto-run-loop-frameworkplan.md
    - docs/plans/L7/L7-auto-run-poc-session-cleanerplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — 実装"
  - role: qa
    slot_label: "QA — 検証"
  - role: tl-advisor
    slot_label: "TL-Advisor — Review"
generates:
  - artifact_path: docs/plans/L7/L7-auto-run-poc-compaction-apiplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/compaction_adapter.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_compaction_adapter.py
    artifact_type: test
  - artifact_path: verify/auto-run-compaction-poc.sh
    artifact_type: test
---

## §0 PLAN concept

`HELIX-workflows/helix-process/continuous-run-context-management.md` の不足穴 #1「handover 記録後に Codex を terminate し fresh 起動する制御」を Discovery PoC で検証するため、ここでは Claude 内部の compaction API（要約 + context 削減）統合を `kind=poc` で起票する。  
実呼び出しではなく、`fake`/`dry-run` と `verify script` によって D2（PoC 実装）と D3（verify）を閉じ、D4（decide）は本 PLAN 外（Opus/人間判断）とする。

## §1 背景

- `L7-auto-run-loop-frameworkplan` §11 carry-1 により compaction API 統合は「pending_next_phase」として明示済み。
- `L7-auto-run-poc-session-cleanerplan` は fresh restart パターンを扱い、P0 3件を carry し fail-close まで達成した。
- 本 PLAN は compaction API を分離して扱うため、context drift 評価とは混在させず別 PoC とする。
- tl-advisor 助言（`W7`）に従い、`kind=poc` を必須化。実 Claude /compact への前倒し呼び出しは avoid し、fake adapter で先行検証する。

## §2 scope

1. `cli/lib/compaction_adapter.py` を新規作成し、以下を定義する。  
   - `CompactionAdapter` Protocol: `request_compaction` / `get_compaction_status`
   - `FakeCompactionAdapter`: テスト用 fake
   - `DryRunCompactionAdapter`: 実呼び出しなしでの log 出力
2. `cli/lib/tests/test_compaction_adapter.py` を新規作成し、5テストを想定する。  
   - fake adapter の成功系/失敗系
   - dry-run の呼び出し整合
   - drift 推定（carry 状態）
3. `verify/auto-run-compaction-poc.sh` を新規作成し、負荷時に fail-close する3件を確認する。  
   - `carry == 0`
   - compaction unavailable
   - drift > threshold
4. `auto_run_engine.py` の `integrations.compaction_api = active` 接続点更新を起票対象範囲に記載し、実本体は別 wave とする。

scope 外:
- 実 Claude /compact API 呼び出し（PoC confirmed 後、human gate）
- 実 context drift の完全計測（PoC confirmed 後）
- compaction 後の handover state 整合（別 PLAN）
- D4 decide（Opus/人間判断）

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | compaction_adapter.py skeleton + fake/dry-run adapter | dry-run start/status が型レベルで通る | pending |
| .2 | drift estimation API + threshold guard | drift > 0.5 で fail-close 確認 | pending |
| .3 | verify script + auto_run_engine.compaction_api 接続 | pytest + bats + verify 全 PASS | pending |

## §11 carry

- carry-1: 実 Claude /compact API 呼び出し（PoC confirmed 後の人間承認 + 規約確認）
- carry-2: 実 context drift 計測（PoC confirmed 後）
- carry-3: compaction 後の handover state 整合（別 PLAN）
- carry-4: D4 decide（Opus/人間判断、本 PLAN scope 外）
