---
plan_id: add-feature-2026-06-20-g9-system-execution-gate
title: "Action(add-feature): 右腕 C-4b — G9 (L4↔L9) system-test execution gate を honest mechanism 化 (g9_subcheck 新設 + ST-* 既存テスト anchor のみ + gap surface、full close せず deferred 維持)"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md  # trace: L9 総合テスト設計 (ST-* 18件 §5、§7 で TR-*→TV-*→ST-* / §8 G9 合格基準=ST 実行+P1 pass)。本 Action は G9 execution gate を g8_subcheck パターンで「honest mechanism 化」する。L4 基本設計の意味/ID universe は不変 (required_refreeze_pairs=L4-L9、L4/L9 本文不改訂)。
forward_return: "g9_subcheck.py を新設 (g8_subcheck パターン複製。L9 doc §5 の ST-* 18件 inventory + ST-ID anchor map + committed system/CLI test 実行を集計、HELIX_DOCTOR_SKIP_EXEC_TESTS=1 時は structural anchor=CI決定的) -> 既存の実行テストへ正当 anchor できる ST のみ marker 付与 (false anchor 厳禁、新規 ST テストは書かない=L7 product work 別 scope) -> vg_overview に G9 evidence 判定を追加し、`trace_clean(L4-L9) AND coverage100 AND semantic_excluded_orphan=18 維持 AND g8 applicable AND g9.passed(=anchored==ST_total AND exec_pass==anchored AND missing==0)` の時のみ L4-L9 を applicable に。**現状 gap>0 のため approved_deferred 維持 (deferred_count 3 不変=[G9,G12,G14])** -> g9_subcheck が implemented=true/passed=false/gap_count を surface し『hand-pinned deferred』を『機械測定 deferred』へ昇格 (将来 ST テスト実装で自動 close) -> L4↔L9 G9 pending gate evidence に帰属 (right-arm full-flow closure order=2、honest mechanism)。**full closure は ST 不足のため未達 = 絶対原則 (false closure 禁止) を優先**。"
drive: be
status: completed
status_note: "2026-06-20 完遂(honest mechanism)。Process §4.1 右腕 execution gate closure order=2 = C-4b (G9)。**設計是正**: 前 session の semantic-flip approach (cov100+既closure済 semantic だけで applicable) は tl-advisor 諮問で false-closure 判定 (test_code_anchor/test_execution_pass 不在=cov100単独 pass 相当) → 却下。正設計=g8 対称の g9_subcheck (ST 実行 anchor + exec gating)。**実測** (research 委譲 + PM 検証): L9 §5 の ST-* 18件のうち既存テストで正当 anchor 可能は 5 件、残 13 件は既存に実行テスト無く新規 system テスト=L7 product work 要 (TL+explorer 一致『既存のみ full close 不可』)。**user 裁定=option A (honest mechanism)**: g9_subcheck を構築し既存テストへ正当 anchor のみ、不足は gap surface して honest deferred 維持 (新規テストは書かない)。boundary retarget (g9_subcheck 許可/既存 anchor 許可/新規テスト依然禁止、latest_user_boundary は既存広さが option A を包含)。検証=contract pytest 88 passed + full bats 57/57 + full pytest cli/lib/tests 2680(PM 独立再実行。se の『pytest88』報告は虚偽で full suite が fr_uses g9-stub漏れ+files.pending不整合の2失敗を捕捉→両方修正) + g9_subcheck live(implemented=true/passed=false/anchored=5/missing=13/gap=13) + strict vg deferred_count=3 overall_clean=false(L4-L9=approved_deferred) + false-anchor 検証(5 anchored ST 全て実テスト精読で genuine, 偽0)。tl_review=tl-advisor 3 pass で P0/P1 なし。初回 P2×2(deferred_reason/allowed_files)は PM disposition で code 変更せず adoption manifest(implemented:true/passed:false/anchored=5/18 + rich reason)に honesty 集約(P2-1=shared deferred_gate_contract 保全/P2-2=manifest cross-ref cascade 回避)。最終 review で changes_required なし(codex wrapper で出力が summary に truncate、substantive signal は一貫)。"
current_task_scope: g9_system_execution_gate_honest_mechanism
approval_required_before_l7_work: false  # 既存 right-arm scope 承認 + 2026-06-20 user AskUserQuestion option A 承認 (honest mechanism、既存テスト anchor のみ、新規 product テストは別途承認要)
tl_review: approve  # tl-advisor 3 pass (impl review + re-review×2)=P0/P1 なし、最終 disposition changes_required なし。P2×2 は honesty を adoption manifest に集約し code 変更せず (rationale は status_note)。
ticket_is_completion_evidence: false
created: 2026-06-20
owner: PM
target_l_pairs:
  - "L4↔L9 (総合): G9 system-test execution gate を honest mechanism 化。g9_subcheck で ST-* 18件 anchor + exec_pass を集計、既存テスト anchor 可能分のみ。full close せず (gap surface)、L4-L9 は approved_deferred 維持"
design_change_class: design_or_contract_changed  # vg_overview の pair status 判定変更 (L4-L9 を hardcoded deferred → g9_subcheck 測定 deferred) + g9_subcheck/doctor route 新設。L4 基本設計の意味/ID universe/L9 §5 シナリオは不変、deferred_count も不変。required_refreeze_pairs=[L4-L9] (forward-return-discipline、L4/L9 本文不改訂で mechanism 化のみ)。
required_refreeze_pairs:
  - "L4-L9"
agent_slots:
  - role: se
    slot_label: "SE — g9_subcheck 新設 (g8 パターン複製) + ST-* 既存テスト anchor map (conservative、検証済のみ) + vg_overview L4-L9 g9-gate 化 (gap で deferred 維持) + doctor route + test_g9_subcheck + minimal-tree stub + pytest/bats（Codex）"
  - role: tl-advisor
    slot_label: "TL — g9 evidence の非 gameable 性 (anchor AND exec_pass、false anchor 不在) / implemented!=passed 分離 / semantic_excluded_orphan=18 維持 / deferred_count 3 非破壊 / G7/G8 回帰非破壊 / honest deferred の正当性 の adversarial check"
generates:
  - artifact_path: cli/lib/g9_subcheck.py
    artifact_type: code
  - artifact_path: cli/lib/vg_overview.py
    artifact_type: code
  - artifact_path: cli/lib/tests/test_g9_subcheck.py
    artifact_type: code
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires:
    - docs/plans/add-feature/add-feature-2026-06-19-g8-integration-execution-gate.md
  blocks: []
related_docs:
  - docs/v2/L7-test-design/right-arm-full-flow-closure-plan.yaml
  - docs/v2/L7-test-design/right-arm-execution-gates-adoption.yaml
  - cli/lib/g8_subcheck.py
  - cli/lib/vg_overview.py
---

# Action 右腕 C-4b: G9 (L4↔L9) system-test execution gate を honest mechanism 化

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md) §4.1 右腕 execution gate closure（order=2 = **G9**）。G8 (C-4a) 完遂後の第2手。closure-plan 正本 = [right-arm-full-flow-closure-plan.yaml](../../v2/L7-test-design/right-arm-full-flow-closure-plan.yaml) order=2。

## 0. 設計是正の経緯（重要）
前 session は G9 を **semantic-flip**（`_pair_clean + cov100 + 既 closure 済 semantic_excluded_orphan(18) + g8 applicable` で L4-L9 を applicable に flip）で閉じようとしたが、tl-advisor 諮問で **false-closure 判定**（changes_required）。理由: `_pair_clean` は trace 系 count しか見ず **test_code_anchor も test_execution_pass も検査しない** → CLAUDE.md「cov100%単独 pass 禁止」「pair_closure = …+test_code_anchor+test_execution_pass+…」に反する。L9 doc 自身も §8「ST-* が**実行され** P1 全 pass」、§7.1「semantic orphan は 2026-06-09 既 closure、**残 carry は G9 の ST anchor / 総合テスト実行 gate**」と裏付け。→ semantic-flip 実装を revert し、g8 対称の g9_subcheck（正設計 B/C）へ。

## 1. 目的 / 解く問題
右腕 4 gate は `vg_overview.py` で常に `approved_deferred` とハードコード。G9 (L4↔L9) は L9 §5 の ST-* 18件を実行 anchor して「Forward 内在ゲート」として実効化すべき。だが実測で **既存テストで正当 anchor 可能は 5 件のみ**、残 13 件は既存に実行テスト無く新規 system テスト=L7 product work が必要（boundary 禁止）。よって本 Action は **G9 を honest mechanism 化**する: g9_subcheck を構築し、既存テストへ正当 anchor できる分のみ anchor、不足は `implemented=true/passed=false/gap_count` で機械可視化して **honest deferred を維持**（false closure を避ける = 絶対原則優先）。これで `hand-pinned deferred` が `機械測定 deferred` へ昇格し、将来 ST テストが実装されれば自動 close する。

## 2. スコープ
### In
- **g9_subcheck.py 新設**（`g8_subcheck.py` パターン複製）: L9 §5 の ST-* 18件 inventory + ST-ID anchor map（ST-* → 既存 test file/function）+ committed test 実行を集計。`st_total / anchored / missing / unanchored / exec_pass / implemented / passed / gap_count` を返す。`implemented`（mechanism 存在）と `passed`（anchored==ST_total AND exec_pass==anchored AND missing==0）を**別キー**にする。`HELIX_DOCTOR_SKIP_EXEC_TESTS=1` 時は structural anchor を pass 扱い（CI fresh-checkout 安全、g8 と同挙動）。
- **ST-* 既存テスト anchor（conservative）**: 既存テストが当該 ST シナリオの手順を実行し合格基準を assert している場合のみ ST-ID marker を付与。「関連機能を触るだけ」は anchor しない（false anchor 厳禁、PM 実テスト精読で検証）。
- **vg_overview の L4-L9 判定**: `DEFERRED_PAIR_REASONS` の L4-L9 hardcode を撤去し、`trace_clean(L4-L9) AND coverage100 AND semantic_excluded_orphan=18 維持 AND g8 applicable AND g9.passed` が真の時のみ applicable。**現状 gap>0 のため approved_deferred 維持**（reason に anchored/missing/gap を surface）。
- **helix-doctor route**: `check_g9_subcheck`（standalone）追加 + `check_vg_overview` が g9 evidence を読む配線。
- **minimal-tree 回帰対策**: vg_overview を呼ぶ minimal/tmp-tree テストに g9_subcheck clean-stub monkeypatch を追加（C-3a/C-4a lesson）。

### Out（forbidden_now / 別 Action）
- 不足 13 件の **新規 ST system テスト実装**（= L7 product work、別途 user 承認要。option B 不採用）。
- L4-L9 の **full closure / deferred_count 削減**（gap が残る限り deferred 維持 = honest）。
- semantic-flip / cov100 単独 pass による closure（false closure 禁止）。
- G12/G14 の honest mechanism（C-4c/d、別 Action。G9 結果を見て着手）。
- L4 基本設計の意味・ID universe・L9 §5 シナリオ変更（出たら設計変更として差戻し）。

## 3. 受入条件
1. g9_subcheck: ST-* 18件 inventory + anchor map + exec を集計。`implemented==true`、`passed==false`（gap>0 のため）、`anchored==5`、`missing==13`。SKIP_EXEC 時 structural pass で CI red 回避。
2. anchor は全て既存テストが当該 ST を genuinely 実行+assert している（false anchor 0、PM 実テスト精読で確認）。
3. vg_overview: L4-L9 は `approved_deferred` のまま（gap>0）。**deferred_count 3 不変 / deferred_gates=[G9,G12,G14] 不変**。semantic_excluded_orphan=18 維持。strict full-flow `overall_clean=false` 維持。
4. G7/G8 回帰非破壊（既存 anchor/exec_pass 不変）。
5. anti-gaming: ST-ID marker 除去 → 当該 ST が unanchored になる（test_g9_subcheck で実証）。
6. 全 pytest + 全 bats green（boundary 契約含む）。

## 4. honest deferred の正当性（絶対原則整合）
G9 を full close しないのは絶対原則（V-model 収束、false closure 禁止）に**整合**する。gate 機構（g9_subcheck）を本物化し、閉じられる分（既存テスト anchor）だけ閉じ、不足を機械可視化して honest deferred を維持するのが正しい disposition（tl-advisor passed）。これは「standing roadmap」を作らず、不足 ST を `L4-L9 G9 pending gate evidence` に帰属させる（Forward の通過条件、独立タスク台帳化しない）。将来 ST テストが実装されれば g9_subcheck が自動で passed=true になり L4-L9 が applicable に flip する。

## 5. forward_return
L4↔L9 G9 pending gate evidence へ帰属。required_refreeze_pairs=[L4-L9]（L4/L9 本文不変 + g9_subcheck mechanism + 依然 deferred = mechanism 化のみの semantic re-freeze 証跡）。
