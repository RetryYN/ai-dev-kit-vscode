---
plan_id: add-feature-2026-06-21-g9-system-test-fullclose
title: "Action(add-feature): 右腕 W1 — G9 (L4↔L9) system-test full-close。残 13 ST を genuine に閉じる(existing-link anchor + 新規 system テスト実装)、自動被覆不能な運用指標 ST のみ honest deferred 維持"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md  # L9 §5 ST-* 18件。本 Action は honest-mechanism(g9_subcheck)で測定される deferred を、genuine test を実装して可能な限り閉じる L7 product work。L4 基本設計の意味/ID universe 不変。
forward_return: "L9 §5 ST-* の未 anchor 13件を per-ID 分類(existing-link / new-test / operational-deferred)-> 既存テスト紐付け可能分を genuine anchor + 自動被覆可能分の新規 system テストを実装(anchor-quality lint で genuine 強制)-> g9_subcheck の anchored を増やし missing を operational-deferred のみに収束 -> 被覆不能 ST(運用/率指標)は理由付き honest deferred 維持 -> L4-L9 が full-close 可能なら applicable へ flip(deferred_count 減)、不能なら gap 縮小を機械可視化 -> L4↔L9 G9 pending gate evidence に帰属。"
drive: be
status: draft
status_note: "2026-06-21 起票。ユーザー裁定(AskUserQuestion A=新規テストも書いて最大化)により、g9 honest-mechanism PLAN(add-feature-2026-06-20-g9-system-execution-gate)が carve out した『不足 13 ST の新規 system テスト=L7 product work』を解禁する。前提機構=W0 anchor-quality-lint(no-op/marker-only/skip-xfail を genuine と誤計上させない)。explorer 一次分類(要 se 再確認): existing-link 3(ST-SYS-02/ST-FR-04/ST-NEG-01)、new-test 7(ST-FR-01/02/03/ST-DATA-01/02/ST-NFR-01/ST-IF-04)、operational-deferred 3(ST-NFR-02 auto-deprecation 月次率 / ST-NFR-03 migration 本番系 / ST-NEG-02 外部 AI 召喚 evidence)。TL 助言(run bgdjt2cmh): 一括でなく被覆可能分のみ genuine close、不能は honest deferred 維持が絶対原則(片肺禁止)と整合。被覆不能を report して止める。"
current_task_scope: g9_system_test_fullclose
approval_required_before_l7_work: false  # ユーザー AskUserQuestion(2026-06-21)= A『新規テストも書いて最大化』= L7 product test 実装を明示承認
ticket_is_completion_evidence: false
created: 2026-06-21
owner: PM
target_l_pairs:
  - "L4↔L9 (総合): ST-* 18件を genuine test で可能な限り full-close。anchored を 5 から (5+existing-link+new-test) へ、missing を operational-deferred のみに収束"
design_change_class: pure_impl  # 新規テスト実装 + 既存テスト anchor のみ。L4 基本設計/L9 §5 シナリオ(設計の意味・ID universe)は不変。g9_subcheck の機構も不変(anchored/missing の実数が genuine test 追加で動くだけ)。
required_refreeze_pairs: []  # pure_impl(L4/L9 本文・ID universe 不変、テスト実体化のみ)
agent_slots:
  - role: se
    slot_label: "SE — L9 §5 ST-13 を per-ID 再分類(test-design doc 精読 + 既存テスト grep)-> existing-link を genuine anchor(false anchor 厳禁)-> new-test を genuine 実装(実シナリオ実行+assert、anchor-quality lint pass)-> operational-deferred を g9_subcheck/adoption yaml に理由付き記録 -> 被覆不能は report -> pytest/bats(Codex)"
  - role: tl-advisor
    slot_label: "TL — 各新規テストが当該 ST シナリオを genuine 実行+assert しているか(no-op/over-mock でないか)/ existing-link anchor の妥当性 / operational-deferred 判定の正当性(本当に自動被覆不能か)/ deferred_count 変化の整合 の adversarial check"
generates:
  - artifact_path: cli/lib/g9_subcheck.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_g9_system_scenarios.py
    artifact_type: test
  - artifact_path: docs/v2/L7-test-design/right-arm-execution-gates-adoption.yaml
    artifact_type: doc_update
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires:
    - docs/plans/add-feature/add-feature-2026-06-20-g9-system-execution-gate.md
    - docs/plans/add-feature/add-feature-2026-06-21-anchor-quality-lint.md
  blocks: []
---

# G9 system-test full-close (add-feature Action / 右腕 W1)

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md)。closure-plan order=2 = G9。本 Action は honest-mechanism(g9_subcheck)が測定する deferred を、genuine system テストを実装して可能な限り閉じる L7 product work。前提 = [anchor-quality-lint](add-feature-2026-06-21-anchor-quality-lint.md)。

## 1. 目的
L9 §5 の ST-* 18件中 5件のみ anchored(13 missing)。ユーザー裁定で新規テストを書いて genuine に最大化する。被覆可能な ST を genuine test(既存紐付け or 新規実装)で閉じ、自動被覆不能な運用/率指標 ST のみ honest deferred 維持。anchor gaming(no-op/marker-only)は anchor-quality lint(W0)が機械排除。

## 2. スコープ
### In
- **per-ID 再分類**(se が test-design doc 精読 + 既存テスト grep で確定。explorer 一次分類は目安):
  - existing-link(既存テスト紐付けのみ): ST-SYS-02 / ST-FR-04 / ST-NEG-01(候補。se が genuine 実行+assert を確認できたもののみ anchor)。
  - new-test(新規 system テスト実装): ST-FR-01/02/03(総合フロー横断)/ ST-DATA-01/02(永続化連鎖)/ ST-NFR-01(doctor/scan 実行時間・flaky)/ ST-IF-04(helix.db 永続化境界)。
  - operational-deferred(自動被覆不能=honest deferred 維持): ST-NFR-02(auto-deprecation 月次率)/ ST-NFR-03(migration 本番系・長期運用)/ ST-NEG-02(外部 AI 召喚 evidence 欠落動作)。
- 新規テストは実シナリオを実行し合格基準を assert(anchor-quality lint で genuine 強制)。g9_subcheck の G9_ANCHOR_MAP に anchor 追加。adoption yaml に per-ID 分類 + deferred 理由を記録。

### Out(forbidden_now)
- operational-deferred ST の anchor gaming(率指標を no-op test で偽装)。被覆不能は report。
- L4 基本設計 / L9 §5 シナリオ(設計の意味・ID universe)の変更。
- G12/G14(W2/W3、別 Action)。

## 3. 受入条件
1. existing-link + new-test の ST が genuine anchor(anchor-quality lint pass、PM/TL 精読で no-op/over-mock 不在)。
2. g9_subcheck: anchored = 5 + (genuine 化できた件数)、missing = operational-deferred のみ。各 new-test が実行 pass。
3. operational-deferred ST は g9_subcheck/adoption yaml に理由付きで明示(silent drop しない)。
4. 全 operational-deferred 化が妥当(TL が「本当に自動被覆不能か」を検証)。被覆可能なのに deferred にしない。
5. L4-L9: 全 ST が genuine closed なら applicable flip(deferred_count 減)、operational-deferred 残存なら approved_deferred 維持で gap 縮小を可視化。**overall_clean / import_cycle / plan_dependency 非破壊**。
6. 全 pytest + 全 bats green。

## 4. forward_return
L4↔L9 G9 pending gate evidence へ帰属。pure_impl(L4/L9 本文・ID universe 不変、テスト実体化のみ、required_refreeze_pairs=[])。

## 5. 検証コマンド
- `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_g9_subcheck --json`(anchored/missing 確認)
- `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_anchor_quality --gate --json`(新 anchor genuine)
- `python3 -m pytest cli/lib/tests/test_g9_system_scenarios.py -q`
- `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json`
