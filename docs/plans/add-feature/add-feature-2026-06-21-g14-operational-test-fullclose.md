---
plan_id: add-feature-2026-06-21-g14-operational-test-fullclose
title: "Action(add-feature): 右腕 W3 — G14 (L1↔L14) operational-test 自動被覆可能分の close。observable な OT を genuine に閉じ、月次/週次/率指標 OT は honest deferred 維持(設計意図と整合)"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L14-test-design/helix-workflows-operational-test-design.md  # L14 OT-01..20。設計書 §1 自身が『実テスト化は L7+/運用フェーズ』と留保。自動被覆可能な OT のみ genuine close、運用指標は honest deferred が設計意図。
forward_return: "L14 OT-* の未 anchor 19件を per-ID 分類 -> observable(自動被覆可能)な OT を genuine operational テストで実装/anchor(anchor-quality lint で genuine 強制)-> g14_subcheck の anchored を増やす -> 月次/週次/運用成功率/audit 完走率など被覆不能 OT は理由付き honest deferred 維持(設計意図と整合、full-close を目指さない)-> L1-L14 の gap 縮小を機械可視化 -> L1↔L14 G14 pending gate evidence に帰属。"
drive: be
status: draft
status_note: "2026-06-21 起票。ユーザー裁定(AskUserQuestion A=新規テストも書いて最大化)。ただし G14 は L14 設計書 §1 自身が『実テスト・監視 rule の実体化は L7 以降と運用フェーズ』と留保しており、OT の大半(月次/週次/率指標/lineage coverage)は単体・総合テストで閉じると anchor gaming になる。TL 助言(run bgdjt2cmh): G14 full-close は原則非現実的、observable な OT のみ genuine close + 残は monitoring/runbook evidence 待ち。explorer 一次分類: existing-link 1(OT-04 mode_transition event)、new-test ~5(OT-03/06/07/11/12)、operational-deferred ~13(OT-01/02/05/08-10/13-19 月次週次率指標、OT-18 は TL 既 demoted)。"
current_task_scope: g14_operational_test_close
approval_required_before_l7_work: false  # ユーザー AskUserQuestion(2026-06-21)= A『新規テストも書いて最大化』
ticket_is_completion_evidence: false
created: 2026-06-21
owner: PM
target_l_pairs:
  - "L1↔L14 (運用学習): OT-* 20件のうち observable な OT を genuine close、月次/週次/率指標 OT は honest deferred 維持(設計意図と整合)"
design_change_class: pure_impl  # 自動被覆可能 OT の新規テスト実装 + 既存 anchor のみ。L1 要件 / L14 OT シナリオ(設計の意味・ID universe)不変。g14_subcheck 機構不変。
required_refreeze_pairs: []  # pure_impl
agent_slots:
  - role: se
    slot_label: "SE — L14 OT-19 を per-ID 分類(observable / monitoring-only)-> observable な OT を genuine 実装/anchor(anchor-quality lint pass)-> 月次/週次/率指標 OT を理由付き honest deferred 記録 -> 被覆不能 report -> pytest/bats(Codex)"
  - role: tl-advisor
    slot_label: "TL — observable OT の genuine 性 / 月次率指標を no-op test で偽装していないか(G14 は gaming リスク最大)/ honest deferred が L14 設計意図(運用フェーズ実体化)と整合するか の adversarial check"
generates:
  - artifact_path: cli/lib/g14_subcheck.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_g14_operational_scenarios.py
    artifact_type: test
  - artifact_path: docs/v2/L7-test-design/right-arm-execution-gates-adoption.yaml
    artifact_type: doc_update
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires:
    - docs/plans/add-feature/add-feature-2026-06-20-g14-operational-learning-gate.md
    - docs/plans/add-feature/add-feature-2026-06-21-anchor-quality-lint.md
  blocks: []
---

# G14 operational-test close (add-feature Action / 右腕 W3)

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md)。closure-plan order=4 = G14。前提 = [anchor-quality-lint](add-feature-2026-06-21-anchor-quality-lint.md)。W2(G12)着地後に着手(直列)。

## 1. 目的
L14 OT-* 20件中 1件のみ anchored(19 missing)。**G14 は L14 設計書 §1 自身が『実テスト化は L7+/運用フェーズ』と留保**しており、OT の大半は月次/週次/運用成功率/audit 完走率で、単体・総合テストで閉じると anchor gaming になる。よって本 Action は **observable(自動被覆可能)な OT のみ genuine close**し、運用指標 OT は理由付き honest deferred 維持(これが設計意図と整合)。「最大化」= gaming せずに閉じられる分を漏れなく閉じる、の意。

## 2. スコープ
### In
- **per-ID 分類**(se 確定):
  - existing-link 1(OT-04 mode_transition event 登録、既存 closure event assert 紐付け候補)。
  - new-test ~5(OT-03 drift 週次検知の自動実行 assertion / OT-06 impact-range query 応答 / OT-07 skill injection 適用率 / OT-11 doc-reviewer 召喚率 / OT-12 ratchet guard commit hook、いずれも observable かつ自動被覆可能なもののみ)。
  - operational-deferred ~13(OT-01/02/05/08-10/13-19 月次週次率指標・運用計測・外部採用展開、OT-18 CLI 起動率は TL 既 demoted)。
- observable OT は実シナリオ実行+assert。g14_subcheck の G14_ANCHOR_MAP に anchor 追加。adoption yaml に per-ID 分類 + deferred 理由。

### Out(forbidden_now)
- 月次/週次/率指標 OT を no-op/固定値 test で anchor(gaming = P0、G14 は最大リスク)。被覆不能は report。
- L1 要件 / L14 OT シナリオ(設計の意味・ID universe)の変更。
- G9/G12(別 Action)。

## 3. 受入条件
1. observable OT のみ genuine anchor(anchor-quality lint pass、TL が gaming 不在を精読確認)。
2. g14_subcheck: anchored = 1 + observable genuine 件数、missing = operational-deferred。各 new-test 実行 pass。
3. operational-deferred OT は理由付きで明示し、L14 設計意図(運用フェーズ実体化)との整合を記録。
4. L1-L14: 大半 operational-deferred のため approved_deferred 維持で gap 縮小を可視化。overall_clean/import_cycle/plan_dependency 非破壊。
5. 全 pytest + 全 bats green。

## 4. forward_return
L1↔L14 G14 pending gate evidence へ帰属。pure_impl(L1/L14 本文・ID universe 不変、required_refreeze_pairs=[])。

## 5. 検証コマンド
- `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_g14_subcheck --json`
- `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_anchor_quality --gate --json`
- `python3 -m pytest cli/lib/tests/test_g14_operational_scenarios.py -q`
- `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json`
