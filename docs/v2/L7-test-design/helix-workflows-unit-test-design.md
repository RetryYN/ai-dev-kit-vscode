---
doc_id: L7-test-design-helix-workflows-unit-test
title: HELIX-workflows V2 単体テスト設計
status: draft
owner: QA
process_layer: L7
test_layer: L7
parent_design:
  - docs/v2/L6-functional-design/helix-workflows-function-design.md
pairs_design:
  - docs/v2/L6-functional-design/helix-workflows-function-design.md
related_decision: docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
---

# 単体テスト設計（L6↔L7 ペア）

> 本書は L6 機能設計（`FN-*` / DbC）の **単体粒度**検証を設計する L7 正本。各 `UT-*` は `FN-*` と **1:1 で対**になり（関数 / 公開契約 1 個 = 単体テスト 1 個）、`requires/ensures/invariant` の検証観点を持つ。HELIX-workflows は稼働中システムのため、既存 pytest（`cli/lib/tests/`）を **観測契約として Reverse** し、各 `UT-*` の Reverse 源泉に紐づける。

## 1. 目的と範囲

- **目的**: L6 の各 `FN-*` の DbC（事前 / 事後 / 不変）を単体で検証する設計を与える。
- **範囲**: 観測済 public contract の単体検証。private helper の網羅は L6 と同じく対象外（gap）。
- **対ペア**: L6 機能設計 doc（`parent_design` / `pairs_design` で相互宣言）。

## 2. 単体テスト観点

- **正常系**: `requires` を満たす入力で `ensures` が成立。
- **異常系 / 境界**: `requires` 違反・不正入力で `invariant`（fail-close 等）が保たれる。
- **状態**: state machine（handover / workspace / automation_runs）は許可遷移と禁止遷移を検証。

## 3. 単体テストケース定義（UT-* ↔ L6 機能設計）

各 `UT-*` は対象設計（L6 の `FN-*`）と 1:1 対応。Reverse 源泉に既存 pytest を併記する（全 observed）。本表は UT-* 定義表かつ L6↔L7 双方向対応の正本（detector が test 定義 + coverage 源泉として読む）。

| UT ID | 対象設計 | 検証内容（DbC 観点） | Reverse 源泉 |
|---|---|---|---|
| UT-ROUTE-01 | FN-ROUTE-01 | 正常 signal で RouteResult / 不正 signal で RouteEngineError（fail-close invariant） | `cli/lib/tests/test_route_engine.py` |
| UT-PLAN-01 | FN-PLAN-01 | frontmatter 検証で warning 群を返す（warn-only ensures） | `cli/lib/tests/test_plan_validator.py` |
| UT-HANDOVER-01 | FN-HANDOVER-01 | stale 判定 + 許可 / 禁止 status 遷移（invariant） | `cli/lib/tests/test_handover.py` |
| UT-WS-01 | FN-WS-01 | clean main で merge 成功 / conflict で非適用（invariant） | `cli/lib/tests/test_workspace_manager.py` |
| UT-DB-01 | FN-DB-01 | 接続 / CRUD helper の row 永続化と lock（ensures） | `cli/lib/tests/test_helix_db_v34_v35.py` |
| UT-DB-02 | FN-DB-02 | additive migration で schema_version 更新・backward compat（invariant） | `cli/lib/tests/test_helix_db_v34_v35.py` |
| UT-GUARD-01 | FN-GUARD-01 | 必須 context 欠如で block / 充足で allow | `cli/lib/tests/test_context_guard.py` |
| UT-GUARD-02 | FN-GUARD-02 | raw LLM CLI を block（invariant） | `cli/lib/tests/test_llm_guard.py` |
| UT-GUARD-03 | FN-GUARD-03 | 不許可 role/model を deny（fail-close invariant） | `cli/lib/tests/test_agent_policy_guard.py` |
| UT-HTTP-01 | FN-HTTP-01 | push/pr trigger で automation_runs 記録 + auth 必須 + trace_id（ensures/invariant） | `cli/lib/tests/test_http_api_routes_push_pr.py` |
| UT-AUDIT-01 | FN-AUDIT-01 | audit_log 追記 / run_id 未存在で拒否（requires） | `cli/lib/tests/test_audit_log.py`, `test_audit_validator.py` |
| UT-CATALOG-01 | FN-CATALOG-01 | code_catalog の索引生成（ensures） | `cli/lib/tests/test_code_catalog.py` |
| UT-CONTRACT-01 | FN-CONTRACT-01 | contract_registry 登録 / 照合の整合（ensures） | `cli/lib/tests/test_contract_registry.py` |
| UT-AGENT-01 | FN-AGENT-01 | agent_slots の fire / release / stale 解放（invariant） | `cli/lib/tests/test_agent_slots_unit.py` |

## 4. 合格基準（G7 単体）

- 全 `FN-*`（14）が 1 つ以上の `UT-*` で trace され、`UT-*` は対応 `FN-*` を参照する（detector で L6↔L7 coverage 100% / uncovered 0 / orphan 0 / missing-pair 0 / balance 1.0）。
- Reverse 源泉の pytest が green を維持する（`python3 -m pytest cli/lib/tests/ -q`）。

## 5. 未検出リスク（gap）

- L6 の 14 `FN-*` は観測済 public contract に限る。未観測 public 関数の単体テスト設計は L6 拡張に追随して追加する。
- DbC のうち実装 / 既存テストから推定できない intent は仮説であり、PO 確認で確定する。

## 6. 自己検証チェックリスト

- [ ] `python3 cli/lib/trace_symmetry.py --json` で L6-L7 が missing-pair 0 / coverage 100% / orphan 0 / balance 1.0。
- [ ] 全 `UT-*`（14）が対応 `FN-*` を参照（orphan なし）。
- [ ] Reverse 源泉ファイルが実在する。
