---
plan_id: add-feature-2026-06-20-g12-acceptance-execution-gate
title: "Action(add-feature): 右腕 C-4c — G12 (L3↔L12) acceptance-test execution gate を honest mechanism 化 (g12_subcheck 新設 + AT 既存テスト anchor + gap surface、full close せず deferred 維持)"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md  # trace: L12 受入テスト設計 (AT-01..57 §2、L3 要件 BR/FR/NFR 57件へ trace)。本 Action は G12 execution gate を g9_subcheck パターンで honest mechanism 化。L3 要件の意味/ID universe は不変 (required_refreeze_pairs=L3-L12、L3/L12 本文不改訂)。
forward_return: "g12_subcheck.py を新設 (g9_subcheck 複製。L12 §2 の AT-01..57 inventory + AT-ID anchor map + committed test 実行を集計、SKIP_EXEC 時 structural anchor=CI決定的) -> 既存の実行テストへ正当 anchor できる AT のみ marker 付与 (false anchor 厳禁、新規 AT テストは書かない=L7 product work 別 scope) -> vg_overview に G12 evidence 判定追加 (`_pair_clean(L3-L12) AND coverage100 AND g12.passed` で applicable、現状 gap>0 で approved_deferred 維持、deferred_count 3 不変) -> g12_subcheck が implemented=true/passed=false/gap_count を surface し hand-pinned deferred を機械測定 deferred へ昇格 -> L3↔L12 G12 pending gate evidence に帰属 (right-arm full-flow closure order=3、honest mechanism)。**full closure は AT 不足 (大半が NFR/SLA/運用/環境レベルで自動化不可) のため未達 = 絶対原則 (false closure 禁止) 優先**。"
drive: be
status: completed
status_note: "2026-06-20 完遂(honest mechanism)。Process §4.1 右腕 execution gate closure order=3 = C-4c (G12)。G9 (C-4b) で実証済の honest-mechanism パターンを G12 へ適用。**実測**: L12 §2 の AT-01..57 のうち既存テストで正当 anchor 可能は 5 件、残 52 件は既存に実行テスト無し (大半が NFR/SLA/運用/環境レベル=自動化不可)。L12 §1 自身『実テストコード/実行/環境差異の実吸収は L12 受入テストフェーズで行う』、§4 carry も実環境/OS matrix/並列Codex/migration残量を staging/production 再計測へ defer。**user 裁定=option A (honest mechanism)**: g12_subcheck を構築し既存テストへ正当 anchor のみ、不足は gap surface して honest deferred 維持 (新規テストは書かない)。boundary retarget (g12_subcheck 許可/既存 anchor 許可/新規テスト依然禁止)。検証=full pytest cli/lib/tests 2692 passed(PM 独立再実行) + contract 88 + bats 57/57 + g12_subcheck live(implemented=true/passed=false/anchored=5/missing=52/gap=52) + strict vg deferred_count=3 overall_clean=false(L3-L12=approved_deferred) + false-anchor 検証(5 anchored AT 全て実テスト精読で genuine: AT-17 gate G2 static verdict / AT-29 registry 4-finding / AT-30 glossary drift / AT-50 secret gate clean-pass / AT-53 raw-push+codex require-approved block、偽0)。tl_review=tl-advisor impl review で P0/P1 なし、approve(anchors verified 5/57、ripple のみ remaining=完了)。"
current_task_scope: g12_acceptance_execution_gate_honest_mechanism
approval_required_before_l7_work: false  # 既存 right-arm scope 承認 + 2026-06-20 user AskUserQuestion option A 承認 (G9/G12/G14 全て honest mechanism、既存テスト anchor のみ、新規 product テストは別途承認要)
tl_review: approve  # tl-advisor impl review (2026-06-20)=P0/P1 なし、approve。anchors 5/57 verified genuine、honest deferred (deferred_count=3 不変)。
ticket_is_completion_evidence: false
created: 2026-06-20
owner: PM
target_l_pairs:
  - "L3↔L12 (受入): G12 acceptance-test execution gate を honest mechanism 化。g12_subcheck で AT-01..57 anchor + exec_pass を集計、既存テスト anchor 可能分のみ。full close せず (gap surface)、L3-L12 は approved_deferred 維持"
design_change_class: design_or_contract_changed  # vg_overview の pair status 判定変更 (L3-L12 を hardcoded deferred → g12_subcheck 測定 deferred) + g12_subcheck/doctor route 新設。L3 要件の意味/ID universe/L12 §2 AT は不変、deferred_count も不変。required_refreeze_pairs=[L3-L12] (L3/L12 本文不改訂で mechanism 化のみ)。
required_refreeze_pairs:
  - "L3-L12"
agent_slots:
  - role: se
    slot_label: "SE — g12_subcheck 新設 (g9 複製) + AT-* 既存テスト anchor map (conservative、検証済のみ) + vg_overview L3-L12 g12-gate 化 (gap で deferred 維持) + doctor route + test_g12_subcheck + minimal-tree stub + pytest"
  - role: tl-advisor
    slot_label: "TL — g12 evidence の非 gameable 性 (false anchor 不在) / implemented!=passed / deferred_count 3 非破壊 / G7/G8/G9 回帰非破壊 / honest deferred の正当性 の adversarial check"
generates:
  - artifact_path: cli/lib/g12_subcheck.py
    artifact_type: code
  - artifact_path: cli/lib/vg_overview.py
    artifact_type: code
  - artifact_path: cli/lib/tests/test_g12_subcheck.py
    artifact_type: code
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires:
    - docs/plans/add-feature/add-feature-2026-06-20-g9-system-execution-gate.md
  blocks: []
related_docs:
  - docs/v2/L7-test-design/right-arm-full-flow-closure-plan.yaml
  - docs/v2/L7-test-design/right-arm-execution-gates-adoption.yaml
  - cli/lib/g9_subcheck.py
  - cli/lib/vg_overview.py
---

# Action 右腕 C-4c: G12 (L3↔L12) acceptance-test execution gate を honest mechanism 化

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md) §4.1 右腕 execution gate closure（order=3 = **G12**）。G9 (C-4b) honest mechanism 完遂後の第3手。同パターン適用。

## 1. 目的 / 解く問題
右腕 4 gate は `vg_overview.py` で常に `approved_deferred` ハードコード。G12 (L3↔L12) は L12 §2 の AT-01..57 を実行 anchor して実効化すべき。だが実測で **既存テストで正当 anchor 可能は 5 件のみ**、残 52 件は既存に実行テスト無し（大半が NFR/SLA/運用/環境レベルで自動化不可。L12 §1/§4 も実吸収を L12 受入フェーズ/実環境へ defer）。よって本 Action は **G12 を honest mechanism 化**: g12_subcheck を構築し既存テスト anchor 可能分のみ anchor、不足は `implemented=true/passed=false/gap_count` で機械可視化して **honest deferred 維持**（false closure 回避 = 絶対原則優先）。将来 AT 受入テストが実装されれば自動 close。

## 2. スコープ
### In
- g12_subcheck.py 新設（g9_subcheck 複製）: AT-01..57 inventory + AT-ID anchor map + exec gating。implemented/passed/gap 分離。SKIP_EXEC 時 structural anchor=CI決定的。
- AT-* 既存テスト anchor（conservative、false anchor 厳禁、PM 実テスト精読検証）。
- vg_overview L3-L12 判定: `_pair_clean AND coverage100 AND g12.passed` で applicable、現状 gap>0 で approved_deferred 維持。L3-L12 は semantic_excluded_orphan 無し（直接 AT→L3 trace、g9 より simpler）。
- helix-doctor route + minimal-tree g12 stub（C-3a/4a/G9 lesson）。

### Out（forbidden_now / 別 Action）
- 不足 52 件の新規 AT 受入テスト実装（L7 product work、別途 user 承認要）。
- L3-L12 の full closure / deferred_count 削減。semantic-flip / cov100 単独 pass closure（false closure 禁止）。
- G14 の honest mechanism（C-4d、別 Action）。L3 要件・L12 AT 変更。

## 3. 受入条件
1. g12_subcheck: AT-01..57 inventory + anchor map + exec。`implemented==true`、`passed==false`（gap>0）、`anchored==5`、`missing==52`。SKIP_EXEC structural pass で CI red 回避。
2. anchor は全て既存テストが当該 AT を genuinely 実行+assert（false anchor 0、PM 確認）。
3. vg_overview: L3-L12 は approved_deferred 維持。deferred_count 3 不変 / deferred_gates=[G9,G12,G14] 不変。strict overall_clean=false 維持。
4. G7/G8/G9 回帰非破壊。anti-gaming: AT-ID marker 除去 → unanchored。
5. 全 pytest + 全 bats green（boundary 契約含む）。

## 4. honest deferred の正当性
G12 を full close しないのは絶対原則（false closure 禁止）に整合。gate 機構を本物化し閉じられる分だけ閉じ、不足を機械可視化して honest deferred 維持（tl-advisor passed）。不足 AT を L3-L12 G12 pending gate evidence に帰属（standing roadmap 化しない）。将来 AT 受入テスト実装で g12_subcheck.passed=true → L3-L12 applicable 自動 flip。
