---
plan_id: add-feature-2026-06-20-g14-operational-learning-gate
title: "Action(add-feature): 右腕 C-4d — G14 (L1↔L14) operational-learning execution gate を honest mechanism 化 (g14_subcheck 新設 + OT 既存テスト anchor + gap surface、full close せず deferred 維持)"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L14-test-design/helix-workflows-operational-test-design.md  # trace: L14 運用テスト設計 (OT-01..20 §2、L1 要求へ trace)。本 Action は G14 execution gate を g9/g12_subcheck パターンで honest mechanism 化。L1 要求の意味/ID universe は不変 (required_refreeze_pairs=L1-L14、L1/L14 本文不改訂)。
forward_return: "g14_subcheck.py を新設 (g12_subcheck 複製。L14 §2 の OT-01..20 inventory + OT-ID anchor map + committed test 実行を集計、SKIP_EXEC 時 structural anchor=CI決定的) -> 既存の実行テストへ正当 anchor できる OT のみ marker 付与 (false anchor 厳禁、新規 OT テスト/運用学習 feedback loop 実装は L7 product work 別 scope=TL P5 で同一モデルに押し込まない) -> vg_overview に G14 evidence 判定追加 (`_pair_clean(L1-L14) AND coverage100 AND g14.passed` で applicable、現状 gap>0 で approved_deferred 維持、deferred_count 3 不変) -> g14_subcheck が implemented=true/passed=false/gap_count を surface -> L1↔L14 G14 pending gate evidence に帰属 (right-arm full-flow closure order=4=最終、honest mechanism)。**full closure は OT 不足 (運用/SLA/feedback-loop レベルで自動化不可) + feedback-loop closure 未達のため未達 = 絶対原則 (false closure 禁止) 優先**。"
drive: be
status: completed
status_note: "2026-06-20 完遂(honest mechanism)。Process §4.1 右腕 execution gate closure order=4=最終 = C-4d (G14)。G9/G12 で実証済の honest-mechanism パターンを G14 へ適用。**実測**: L14 §2 の OT-01..20 のうち既存テストで正当 anchor 可能は 1 件、残 19 件は既存に実行テスト無し (運用/SLA/feedback-loop レベル=自動化不可)。**feedback-loop closure (events/metrics/feedback adoption) は g14_subcheck に押し込まず別 deferred concern として維持 (TL P5)**。**user 裁定=option A (honest mechanism)**: g14_subcheck を構築し既存テストへ正当 anchor のみ、不足は gap surface して honest deferred 維持 (新規テスト/feedback-loop 実装は書かない)。boundary retarget (g14_subcheck 許可/既存 anchor 許可/新規テスト依然禁止)。検証=full pytest cli/lib/tests 2704 passed(PM 独立再実行) + contract 88 + bats 57/57 + g14_subcheck live(implemented=true/passed=false/anchored=1/20[OT-20]/missing=19/gap=19) + strict vg deferred_count=3 overall_clean=false(L1-L14=approved_deferred) + OT-20 genuine 検証(test-handover.bats handover dump→CURRENT.json/md 生成 + test-helix-stop-hook-wiring.bats stop-hook 更新で中断 session 再開可能性を実行+assert、PM 実テスト精読)。tl_review=tl-advisor impl review で OT-18 を demote 勧告(NFR-AV-01 月次起動成功率=SLA/監視シナリオで routing テストは rate 測定せず)→demote 対応(anchored 2→1/20、全 pin 1/20 同期)→re-review で 1/20 sync 後 approve。"
current_task_scope: g14_operational_learning_execution_gate_honest_mechanism
approval_required_before_l7_work: false  # 既存 right-arm scope 承認 + 2026-06-20 user AskUserQuestion option A 承認 (G9/G12/G14 全て honest mechanism、既存テスト anchor のみ、新規 product テスト/feedback-loop 実装は別途承認要)
tl_review: approve  # tl-advisor impl review (2026-06-20)=OT-18 demote 勧告→対応(anchored 1/20)→1/20 sync 後 approve。OT-20 genuine、honest deferred (deferred_count=3 不変)。
ticket_is_completion_evidence: false
created: 2026-06-20
owner: PM
target_l_pairs:
  - "L1↔L14 (運用): G14 operational-learning execution gate を honest mechanism 化。g14_subcheck で OT-01..20 anchor + exec_pass を集計、既存テスト anchor 可能分のみ。full close せず (gap surface)、L1-L14 は approved_deferred 維持"
design_change_class: design_or_contract_changed  # vg_overview の pair status 判定変更 (L1-L14 を hardcoded deferred → g14_subcheck 測定 deferred) + g14_subcheck/doctor route 新設。L1 要求の意味/ID universe/L14 §2 OT は不変、deferred_count も不変。required_refreeze_pairs=[L1-L14] (L1/L14 本文不改訂で mechanism 化のみ)。
required_refreeze_pairs:
  - "L1-L14"
agent_slots:
  - role: se
    slot_label: "SE — g14_subcheck 新設 (g12 複製) + OT-* 既存テスト anchor map (conservative、検証済のみ) + vg_overview L1-L14 g14-gate 化 (gap で deferred 維持) + doctor route + test_g14_subcheck + minimal-tree stub + pytest。feedback-loop は g14_subcheck に押し込まない (TL P5)"
  - role: tl-advisor
    slot_label: "TL — g14 evidence の非 gameable 性 (false anchor 不在) / implemented!=passed / feedback-loop を別 concern に維持 / deferred_count 3 非破壊 / G7/G8/G9/G12 回帰非破壊 / honest deferred の正当性 の adversarial check"
generates:
  - artifact_path: cli/lib/g14_subcheck.py
    artifact_type: code
  - artifact_path: cli/lib/vg_overview.py
    artifact_type: code
  - artifact_path: cli/lib/tests/test_g14_subcheck.py
    artifact_type: code
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires:
    - docs/plans/add-feature/add-feature-2026-06-20-g12-acceptance-execution-gate.md
  blocks: []
related_docs:
  - docs/v2/L7-test-design/right-arm-execution-gates-adoption.yaml
  - cli/lib/g12_subcheck.py
  - cli/lib/vg_overview.py
---

# Action 右腕 C-4d: G14 (L1↔L14) operational-learning execution gate を honest mechanism 化

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md) §4.1 右腕 execution gate closure（order=4=**最終** = **G14**）。G9/G12 honest mechanism 完遂後の最終手。同パターン適用。

## 1. 目的 / 解く問題
右腕 4 gate の最後。G14 (L1↔L14) は L14 §2 の OT-01..20 を実行 anchor して実効化すべき。だが実測で **既存テストで正当 anchor 可能は 1 件のみ**、残 19 件は既存に実行テスト無し（運用/SLA/feedback-loop レベルで自動化不可）。本 Action は **G14 を honest mechanism 化**: g14_subcheck を構築し既存テスト anchor 可能分のみ anchor、不足は `implemented=true/passed=false/gap_count` で機械可視化して **honest deferred 維持**（false closure 回避 = 絶対原則優先）。**運用学習 feedback-loop closure (events/metrics/feedback adoption) は g14_subcheck に押し込まず別 deferred concern として維持**（TL P5）。

## 2. スコープ
### In
- g14_subcheck.py 新設（g12_subcheck 複製）: OT-01..20 inventory + OT-ID anchor map + exec gating。implemented/passed/gap 分離。
- OT-* 既存テスト anchor（conservative、false anchor 厳禁、PM 実テスト精読検証）。
- vg_overview L1-L14 判定: `_pair_clean AND coverage100 AND g14.passed` で applicable、現状 gap>0 で approved_deferred 維持。
- helix-doctor route + minimal-tree g14 stub。

### Out（forbidden_now / 別 Action）
- 不足 19 件の新規 OT 運用テスト実装 + feedback-loop closure 実装（L7 product work、別途 user 承認要。TL P5: 同一モデルに押し込まない）。
- L1-L14 の full closure / deferred_count 削減。semantic-flip / cov100 単独 pass closure。L1 要求・L14 OT 変更。

## 3. 受入条件
1. g14_subcheck: OT-01..20 inventory + anchor map + exec。`implemented==true`、`passed==false`（gap>0）、`anchored==1`、`missing==19`。SKIP_EXEC structural pass で CI red 回避。
2. anchor は全て既存テストが当該 OT を genuinely 実行+assert（false anchor 0、PM 確認）。
3. vg_overview: L1-L14 は approved_deferred 維持。deferred_count 3 不変。strict overall_clean=false 維持。
4. G7/G8/G9/G12 回帰非破壊。anti-gaming: OT-ID marker 除去 → unanchored。feedback-loop は別 concern 維持。
5. 全 pytest + 全 bats green（boundary 契約含む）。

## 4. honest deferred + 右腕 4 gate 完結
G14 を full close しないのは絶対原則（false closure 禁止）に整合。これで右腕 4 gate (G8 closed / G9・G12・G14 honest mechanism deferred) すべてが「本物の gate」として実効化され、deferred_count=3 は機械測定 deferred（hand-pin でない）になる。将来 ST/AT/OT 実行テスト + feedback-loop が実装されれば各 g*_subcheck.passed=true → 該当 pair applicable 自動 flip。
