---
id: D-API-SEP-cutover-gate5
plan: PLAN-084
layer: L3
status: draft
created: 2026-05-18
phase: 4.C.2
implementation_files:
  - cli/lib/cutover_orchestrator.py
  - cli/lib/tests/test_cutover_orchestrator_unit.py
references:
  - docs/v2/L3-detailed-design/D-API/D-API-SEP-phase4b-addendum.md
  - docs/adr/ADR-018-db-separation-and-event-sourcing.md
  - docs/v2/L4-test-design/PLAN-084-integration-test-design.md
---

# PLAN-084 Phase 4.C.2: cutover orchestrator + gate 5 設計

# @helix:index id=cutover-gate5.design domain=docs summary=PLAN-084 gate 5 cutover preflight and PO approval design

本書は PLAN-084 Phase 4.C.2 の gate 5 実装参照であり、`ADR-020` 正式起票前の
cutover 判定・承認・rollback 条件を凍結する。live cutover 実行は PO 承認 carry とし、
この段階では code path と runbook 境界だけを確定する。

## 1. 対象

- 実装ファイル: `cli/lib/cutover_orchestrator.py`
- 単体テスト: `cli/lib/tests/test_cutover_orchestrator_unit.py`
- 上位設計: `ADR-018 §Decision.5`, `D-API-SEP-phase4b-addendum.md`

## 2. Gate 5 Entry / Exit

### Entry 条件

1. gate 2 dual-write mismatch gate が PASS していること
2. gate 3 shadow replay が PASS していること
3. mismatch count が 0 件であること
4. gate 4 projector lag stabilization が PASS していること
5. PO 承認 token (`PO-APPROVED-...`) が発行済みであること

### Exit 条件

1. `cutover_preflight()` が `ready=True` を返すこと
2. `cutover_execute(confirm_token=...)` が token を検証し、未承認 token を reject すること
3. 本コードパスでは live cutover を走らせず、`po_carry_required` を返すこと
4. 本番 runbook 側で旧 `helix.db` tombstone/drop と rollback window を扱えること

## 3. API 契約

### 3.1 `CutoverPreflightResult`

```python
@dataclass(frozen=True)
class CutoverPreflightResult:
    ready: bool
    blockers: list[str]
    dual_write_health: dict
    replay_completed: bool
```

- `ready`: gate 5 entry 条件を満たすときのみ `True`
- `blockers`: fail-close 理由
- `dual_write_health`: dual-write 健全性と mismatch 件数の要約
- `replay_completed`: shadow replay 完了フラグ

### 3.2 `cutover_preflight()`

責務:

1. dual-write 健全性 probe を読む
2. mismatch count probe を読む
3. shadow replay 完了 probe を読む
4. gate 5 blocker を集約し `CutoverPreflightResult` を返す

blocker ルール:

- `dual_write_unhealthy`
- `dual_write_mismatch_count_unavailable`
- `dual_write_mismatch_detected:<count>`
- `shadow_replay_incomplete`

### 3.3 `cutover_execute(confirm_token=...)`

責務:

1. `confirm_token` を必須検証する
2. `cutover_preflight()` が `ready=False` の場合は fail-close する
3. preflight 通過後も、この実装段階では live cutover を走らせない
4. PO/PM が本番 runbook で引き継げる payload を返す

token ルール:

- prefix: `PO-APPROVED-`
- 空文字・prefix のみ・別 prefix は `ValueError`

返却 payload:

- `status: "po_carry_required"`
- `executed: false`
- `rollback_window_days: 7`
- `preflight`: `CutoverPreflightResult` の辞書化結果

## 4. PO 承認手続き

1. PM が gate 2-4 の証跡を収集する
2. PO が cutover window と rollback owner を承認する
3. `PO-APPROVED-YYYY-MM-DD[-suffix]` token を発行する
4. `cutover_execute(confirm_token=...)` で token を検証する
5. 本番 runbook が live cutover を実行する

## 5. Rollback Trigger

以下のいずれかで gate 6 rollback 判定へ戻す。

- mismatch count が 1 件以上に再発
- shadow replay の再検証で drift が出る
- projector lag が重大 anomaly に達する
- cutover 後 7 日以内に data loss / projector down > 1h を検知する
- PO が cutover window を revoke する

## 6. 実装境界

- `cutover_orchestrator.py` は判定と承認検証のみを担当する
- 実 DB tombstone/drop は実装しない
- live cutover hook は未接続をデフォルトとし、ローカル test では副作用を起こさない
- `ADR-020` で phase.yaml 併存/廃止判断を正式化するまでは、本書を implementation reference とする

## 7. Verification Trace

| Case ID | 対象 | 検証 |
|---|---|---|
| CT-001 | preflight happy path | dual-write healthy + mismatch 0 + replay 完了で `ready=True` |
| CT-002 | preflight fail-close | unhealthy / mismatch / replay 未完了を blocker 化 |
| CT-003 | execute token validation | token 不正時に `ValueError` |
| CT-004 | execute gate block | preflight 未達時に `RuntimeError` |
| CT-005 | carry payload | hook 未接続時に `po_carry_required` を返す |

結合テスト対応:

- `PLAN-084-integration-test-design.md` §2.4 `I-MIGRATION-010〜011`
- `PLAN-084-integration-test-design.md` §2.5 `I-MIGRATION-012`

## 8. Formalization Carry

- `ADR-020` 起票時に本書の gate 5/6 手順を正式採用する
- 必要なら `docs/v2/L4-test-design/` 配下へ cutover orchestrator 専用 case を昇格する
