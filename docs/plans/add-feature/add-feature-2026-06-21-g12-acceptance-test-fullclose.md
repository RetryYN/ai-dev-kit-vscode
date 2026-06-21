---
plan_id: add-feature-2026-06-21-g12-acceptance-test-fullclose
title: "Action(add-feature): 右腕 W2 — G12 (L3↔L12) acceptance-test full-close。残 52 AT を可能な限り genuine に閉じる(existing-link anchor + 新規 acceptance テスト実装)、運用/月次指標 AT は honest deferred 維持"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md  # L12 AT-01..57。honest-mechanism(g12_subcheck)が測定する deferred を genuine acceptance テストで可能な限り閉じる L7 product work。L3 要件の意味/ID universe 不変。
forward_return: "L12 AT-* の未 anchor 52件を per-ID 分類(existing-link / new-test / operational-deferred)-> 既存 detector/CLI テスト紐付け可能分を genuine anchor + 自動被覆可能分の新規 acceptance テストを実装(anchor-quality lint で genuine 強制)-> g12_subcheck の anchored を増やす -> 性能/OS matrix/月次運用/migration 残量など被覆不能 AT は理由付き honest deferred 維持 -> L3-L12 の gap 縮小を機械可視化(genuine full-close 上限 ~60-65%、残は deferred)-> L3↔L12 G12 pending gate evidence に帰属。"
drive: be
status: draft
status_note: "2026-06-21 起票。ユーザー裁定(AskUserQuestion A=新規テストも書いて最大化)により g12 honest-mechanism PLAN が carve out した新規 acceptance テスト=L7 product work を解禁。前提=W0 anchor-quality-lint。explorer 一次分類(要 se 確定): existing-link ~8-10(AT-01/03/05/24/25/51/52 等 既存 detector/CLI テスト紐付け)、new-test ~25-30(AT-06/07/08/10/13-16/18/19/21/26-28/34-37/46-49 等)、operational-deferred ~14-17(AT-31/32/33/38-45 等 月次率/外部環境)。TL 助言(run bgdjt2cmh): 全 57 即時 close は非現実的、被覆可能分のみ genuine close。genuine full-close 上限 ~60-65%。被覆不能は report。"
current_task_scope: g12_acceptance_test_fullclose
approval_required_before_l7_work: false  # ユーザー AskUserQuestion(2026-06-21)= A『新規テストも書いて最大化』
ticket_is_completion_evidence: false
created: 2026-06-21
owner: PM
target_l_pairs:
  - "L3↔L12 (受入): AT-* 57件を genuine acceptance テストで可能な限り full-close(上限 ~60-65%)。anchored を 5 から増やし、運用/月次指標は honest deferred 維持"
design_change_class: pure_impl  # 新規 acceptance テスト実装 + 既存テスト anchor のみ。L3 要件 / L12 AT シナリオ(設計の意味・ID universe)不変。g12_subcheck 機構不変。
required_refreeze_pairs: []  # pure_impl
agent_slots:
  - role: se
    slot_label: "SE — L12 AT-52 を per-ID 分類(test-design doc 精読 + 既存テスト grep)-> existing-link を genuine anchor -> new-test を genuine 実装(実 acceptance シナリオ実行+assert、anchor-quality lint pass)-> operational-deferred を理由付き記録 -> 被覆不能 report -> pytest/bats(Codex、件数多いため batch 分割可)"
  - role: tl-advisor
    slot_label: "TL — 各新規 acceptance テストが当該 AT を genuine 実行+assert しているか / existing-link 妥当性 / operational-deferred(性能/月次/外部環境)の被覆不能判定の正当性 / deferred_count 整合 の adversarial check"
generates:
  - artifact_path: cli/lib/g12_subcheck.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_g12_acceptance_scenarios.py
    artifact_type: test
  - artifact_path: docs/v2/L7-test-design/right-arm-execution-gates-adoption.yaml
    artifact_type: doc_update
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires:
    - docs/plans/add-feature/add-feature-2026-06-20-g12-acceptance-execution-gate.md
    - docs/plans/add-feature/add-feature-2026-06-21-anchor-quality-lint.md
  blocks: []
---

# G12 acceptance-test full-close (add-feature Action / 右腕 W2)

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md)。closure-plan order=3 = G12。honest-mechanism(g12_subcheck)が測定する deferred を genuine acceptance テストで可能な限り閉じる L7 product work。前提 = [anchor-quality-lint](add-feature-2026-06-21-anchor-quality-lint.md)。W1(G9)着地後に着手(vg_overview/subcheck 共有編集のため直列)。

## 1. 目的
L12 AT-* 57件中 5件のみ anchored(52 missing)。被覆可能な AT を genuine acceptance テストで閉じ、性能/OS matrix/月次運用/migration 残量など自動被覆不能な AT のみ honest deferred 維持。anchor gaming は anchor-quality lint(W0)が機械排除。

## 2. スコープ
### In
- **per-ID 分類**(se が確定。explorer 一次分類は目安):
  - existing-link ~8-10(AT-01 plan_registry / AT-03 drift routing / AT-05 pair 欠落 lint / AT-24 dependency graph / AT-25 doctor 横断 / AT-51 settings regen / AT-52 agent block 等、既存 detector/CLI テスト紐付け)。
  - new-test ~25-30(AT-06/07/08/10/13-16/18/19/21/26-28/34-37/46-49 等、既存 CLI への assertion 追加で被覆可能)。
  - operational-deferred ~14-17(AT-31 起動率 99.9% / AT-32 DB 破損 0 / AT-33 session 中断 SLA / AT-38-45 NFR-OP 月次週次監視指標 等、自動テスト被覆不能)。
- 新規テストは実 acceptance シナリオを実行し合格基準を assert。g12_subcheck の G12_ANCHOR_MAP に anchor 追加。adoption yaml に per-ID 分類 + deferred 理由。

### Out(forbidden_now)
- operational-deferred AT の anchor gaming(率指標/監視を no-op で偽装)。被覆不能は report。
- L3 要件 / L12 AT シナリオ(設計の意味・ID universe)の変更。
- G9/G14(別 Action)。

## 3. 受入条件
1. existing-link + new-test の AT が genuine anchor(anchor-quality lint pass、TL/PM 精読で no-op/over-mock 不在)。
2. g12_subcheck: anchored 増加、missing = operational-deferred のみ。各 new-test 実行 pass。
3. operational-deferred AT は理由付きで明示(silent drop しない)。被覆可能なのに deferred にしない(TL 検証)。
4. L3-L12: operational-deferred 残存のため approved_deferred 維持で gap 縮小を可視化(genuine full-close 上限 ~60-65%)。overall_clean/import_cycle/plan_dependency 非破壊。
5. 全 pytest + 全 bats green。

## 4. forward_return
L3↔L12 G12 pending gate evidence へ帰属。pure_impl(L3/L12 本文・ID universe 不変、required_refreeze_pairs=[])。

## 5. 検証コマンド
- `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_g12_subcheck --json`
- `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_anchor_quality --gate --json`
- `python3 -m pytest cli/lib/tests/test_g12_acceptance_scenarios.py -q`
- `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json`
