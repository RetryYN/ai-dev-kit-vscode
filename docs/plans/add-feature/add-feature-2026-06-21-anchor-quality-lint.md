---
plan_id: add-feature-2026-06-21-anchor-quality-lint
title: "Action(add-feature): anchor-quality lint 新設 — 右腕 execution gate の anchor が no-op/marker-only/skip-xfail を genuine と誤計上しないよう機械検証 (gaming 防止、full-close 前提機構)"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L7-test-design/right-arm-full-flow-closure-plan.yaml  # 右腕 full-flow closure の TL 既定 sequence。本 Action は closure 前提として anchor の非 gameable 性を機械化する(W0)。
forward_return: "anchor の genuine 性検証を機械化 -> cli/lib/anchor_quality.py 新設(test file + needle から、囲む test 本体が実 assert を持つか/no-op(assert True, bare pass)/marker-only(comment のみ)/skip-xfail-only を判定)-> g7/g8/g9/g12/g14 _subcheck の anchor 計上を anchor_quality genuine 限定に -> helix doctor check_anchor_quality(standalone)で weak anchor を P0/P1 surface -> 既存 anchor の非退行確認 -> L6↔L7 G7 / 右腕 pending gate evidence に帰属。"
drive: be
status: completed
tl_review: approve  # tl-advisor 再 review (foundation reject→修正後、rollout 06:06:51) = approve。P1-a(残存0.70)/P1-b(anchor_quality を required_clean へ fail-close)/P2(denylist drift test) 全解消、P0/P1/P2 なし。PM 独立検証: targeted 136 passed / full 2723 passed / bats 57/57 / 非gameable test 2件 genuine。
status_note: "2026-06-21 起票。ユーザー裁定(AskUserQuestion A)= 『新規テストも書いて最大化』により右腕 G9/G12/G14 へ新規テストを大量 anchor する。TL 助言(tl-advisor, run bgdjt2cmh, P1)= 現 subcheck は no-op assert の意味検査が弱く、anchor marker のみ/`assert True`/skip-xfail-only を genuine と機械排除できない。full-close 前にこの anchor-quality lint を入れる価値が高い。本 W0 を G9/G12/G14 新規テスト wave(W1-W3)の前提機構として先行 land する。"
current_task_scope: anchor_quality_lint
approval_required_before_l7_work: false  # ユーザー AskUserQuestion(2026-06-21)= A『新規テストも書いて最大化』承認。本 W0 はその前提機構。
ticket_is_completion_evidence: false
created: 2026-06-21
owner: PM
target_l_pairs:
  - "L6↔L7 / 右腕 (L4-L9 / L3-L12 / L1-L14): anchor の genuine 性を機械検証し、subcheck の anchored 計上を non-gameable に"
design_change_class: design_or_contract_changed  # subcheck の anchor 計上判定に anchor_quality genuine 条件を追加(weak anchor は計上しない)+ doctor check 新設。各 L 設計の意味・ID universe は不変、計上の厳格化のみ。
required_refreeze_pairs:
  - "L6-L7"
agent_slots:
  - role: se
    slot_label: "SE — anchor_quality.py 新設(pytest/bats 両対応の genuine 判定)+ g7/g8/g9/g12/g14 _subcheck の anchor 計上を genuine 限定に + helix doctor check_anchor_quality route + test_anchor_quality.py(genuine/no-op/marker-only/skip-xfail の正負例)+ 既存 anchor 非退行検証(Codex)"
  - role: tl-advisor
    slot_label: "TL — genuine 判定の網羅性(no-op/marker-only/skip-xfail/output 未検証 bats を漏れなく weak 判定するか)/ false-negative(genuine を weak 誤判定)が既存 G7/G8/G9 anchor を退行させないか / subcheck 計上変更の非破壊性 の adversarial check"
generates:
  - artifact_path: cli/lib/anchor_quality.py
    artifact_type: python_module
  - artifact_path: cli/lib/g9_subcheck.py
    artifact_type: python_module
  - artifact_path: cli/lib/g12_subcheck.py
    artifact_type: python_module
  - artifact_path: cli/lib/g14_subcheck.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_anchor_quality.py
    artifact_type: test
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires:
    - docs/plans/add-feature/add-feature-2026-06-20-g9-system-execution-gate.md
  blocks: []  # W1-W3(G9/G12/G14 fullclose)は各自の requires で本 W0 を参照(dangling 回避)
---

# anchor-quality lint (add-feature Action / 右腕 full-close W0)

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md)。closure-plan 正本 = [right-arm-full-flow-closure-plan.yaml](../../v2/L7-test-design/right-arm-full-flow-closure-plan.yaml)。本 Action は右腕 full-close(W1-W3 で新規テストを大量 anchor)の **前提機構(W0)**。

## 1. 目的 / 解く問題
ユーザー裁定により G9/G12/G14 へ新規テストを大量 anchor する(W1-W3)。現 subcheck の `_existing_anchor_paths` は「test file が存在し、needle(ID)が word-boundary で本文にある」かしか見ず、**囲む test 本体が実 assert を持つかを検査しない**(TL P1)。このままだと `assert True` / bare `pass` / コメントだけの marker-only / `@pytest.mark.skip`・`xfail`-only / `run` 後に status/output を検証しない bats を genuine anchor と誤計上できる = anchor gaming(絶対原則 P0 違反)。新規テストを大量に足す前に、anchor の genuine 性を**機械検証**する lint を入れる。

## 2. スコープ
### In
- **cli/lib/anchor_quality.py 新設**: `assess_anchor(test_path, needle) -> {genuine: bool, reason: str}` を提供。
  - pytest: needle を含む test 関数本体を抽出し、(a) skip/xfail デコレータのみで body が実行されない、(b) body が `pass` のみ、(c) 実 assert ゼロ、(d) 全 assert が trivial(`assert True`/`assert 1`/`assert not False`)、(e) needle が関数外コメントのみ(marker-only)を **weak** と判定。1 つでも非 trivial な assert / 例外検証 / `pytest.raises` があれば genuine。
  - bats: needle を含む `@test` ブロックを抽出し、`run` のみで `$status`/`$output`/`assert_*`/`[ ... ]` 検証が無い、`skip` のみ、body 空を weak 判定。実 assertion があれば genuine。
- **subcheck 統合**: g7(あれば)/g9/g12/g14 の `_existing_anchor_paths`(または anchored 計上箇所)で、anchor を `assess_anchor(...).genuine` が真の場合のみ計上。weak anchor は `unanchored` 側へ(理由を surface)。**g8 も対象に含めるか**は TL 判定(g8 は IT anchor、対称性のため含める方針だが既存退行を最優先で確認)。
- **helix doctor check_anchor_quality**(standalone): 全 subcheck の ANCHOR_MAP を走査し、weak anchor を `severity=P0`(genuine と誤計上していた既存 anchor)/`P1`(新規 marker-only)で列挙。`--gate` で fail-close。
- **test_anchor_quality.py**: genuine(実 assert)/no-op(`assert True`)/bare-pass/marker-only/skip-only/xfail-only/bats-run-without-check の正負例で判定を実証。意図的 weak fixture を置き weak 判定されることを assert(非 gameable 性の証跡)。

### Out(forbidden_now / 別 Action)
- 新規 ST/AT/OT テストの実装(W1-W3、別 Action)。
- 既存 anchor が weak と判明した場合の**テスト書き直し**(検出が本 Action scope。修正は対象 wave で genuine 化)。
- 各 L 設計 doc の意味・ID universe 変更。

## 3. 受入条件
1. `anchor_quality.assess_anchor` が pytest/bats の genuine/weak を正しく判定(test_anchor_quality の正負例 green)。
2. subcheck 統合後、**既存 G7/G8/G9/G12/G14 の現 anchor(5/5/1 等)が全て genuine 判定で非退行**(anchored 計数が減らない)。減る場合は weak anchor を発見した証跡として report し、当該 anchor を W1-W3 で genuine 化する対象として記録(silent に消さない)。
3. `helix doctor check_anchor_quality --gate` が weak ゼロで PASS(現状)。意図的に no-op anchor を仕込むと FAIL する(非 gameable 性実証)。
4. deferred_count / vg_overview の現状(右腕 deferred 維持)を破壊しない。
5. 全 pytest + 全 bats green。

## 4. forward_return
L6↔L7 G7 / 右腕 pending gate evidence へ帰属。required_refreeze_pairs=[L6-L7](anchor 計上の厳格化 = 検証機構の semantic re-freeze、各 L 本文不変)。本 W0 完了が W1-W3(G9/G12/G14 新規テスト)の前提。

## 5. 検証コマンド
- `python3 -m pytest cli/lib/tests/test_anchor_quality.py -q`
- `python3 -m pytest cli/lib/tests/test_g9_subcheck.py cli/lib/tests/test_g12_subcheck.py cli/lib/tests/test_g14_subcheck.py -q`
- `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_anchor_quality --gate --json`
- `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json`(deferred_count 非破壊確認)
- `python3 -m pytest cli/lib/tests/ -q` + 全 bats
