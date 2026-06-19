---
plan_id: add-feature-2026-06-19-g8-integration-execution-gate
title: "Action(add-feature): 右腕 C-4a — G8 (L5↔L8) integration-test execution gate closure (g8_subcheck 新設 + L8 gap3件 observed 昇格 + vg_overview L5-L8 deferred 条件付き解除)"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L8-test-design/L5-detailed-design-結合テスト設計.md  # trace: L8 結合テスト設計 (IT-* 21件、L5 MOD/IF/IP/DB 21設計 ID と双方向 trace)。本 Action は右腕 G8 execution gate を g7_subcheck パターン (案A: g8_subcheck 新設) で閉じ、L5-L8 を approved_deferred から条件付き (anchor + exec_pass) で外す。L5 詳細設計の意味/ID universe/DB schema は不変 (required_refreeze_pairs=L5-L8、L5 本文不改訂)。
forward_return: "g8_subcheck.py を新設 (g7_subcheck パターン複製。L8 doc の IT-* 21件 inventory + IT-ID anchor map + committed integration-test 実行を集計、HELIX_DOCTOR_SKIP_EXEC_TESTS=1 時は structural anchor を pass 扱い=CI fresh-checkout 安全) -> L8 結合テスト設計の gap3件 (IT-MOD-06/IT-DB-03/IT-DB-05) に結合テストを実装し observed 昇格 (L8 doc gap→observed 改訂、L5 本文不変) -> vg_overview に G8 evidence 判定を追加し、`trace_clean(L5-L8) AND g8.anchored==IT_total AND g8.missing==0 AND g8.unanchored==0 AND g8.exec_pass==g8.anchored` で L5-L8 を deferred から外す (cov100%単独 pass 禁止、G7 と同 AND 構造) -> helix-doctor に g8 route 追加 -> strict-full-flow の deferred_count 4→3 / deferred_gates=[G9,G12,G14] pin を test_vg_overview / helix-doctor-json.bats / 境界契約で更新 -> L5↔L8 semantic re-freeze 証跡 (L5 unchanged + L8 observed昇格 + trace_symmetry clean + TL semantic-pass) を記録 -> L5↔L8 G8 pending gate evidence に帰属 (right-arm full-flow closure order=1)."
drive: be
status: completed
status_note: "2026-06-19 完遂。Process §4.1 右腕 execution gate closure 第1手 = C-4a (G8, order=1)。g8_subcheck 新設 (path::IT-ID anchor + word-boundary needle + exec gating で execute_g7_tests=False 時 structural anchor=CI決定的) + gap3件(IT-MOD-06/IT-DB-03/IT-DB-05)結合テスト observed昇格 + vg_overview L5-L8 を anchor AND exec_pass で deferred 解除 (G9/G12/G14 deferred 維持) + deferred_count 4→3 ripple (TL分類: live/active ledger→3, historical/negative据置) + **boundary evolution(ユーザー裁定=右腕G8-G14順次解禁、限定解禁: current_allowed_work=右腕gate限定, forbidden_now=product L7維持, right_arm_execution_work_allowed_from_handover=true/product_l7_work_allowed_from_handover=false)**。tl-advisor design諮問+ripple戦略+boundary framing+impl review(changes_required: P0 anchor gameable/P1 flag broad/P2 gate条件)→修正→**re-review=approve**。PM anti-gaming実証(マーカー除去→clean False/anchored20)。検証=pytest 138/112+88 + bats84 (env無)/check_vg_overview overall_clean=true deferred=3/strict deferred=[G9,G12,G14]。残P3(substring anchor→word-boundary化)はdeferred follow-up。"
current_task_scope: g8_integration_execution_gate
approval_required_before_l7_work: false  # ユーザー AskUserQuestion で右腕 scope 承認済
tl_review: approve  # impl review (tl-advisor 2026-06-19)=changes_required (P0 anchor gameable/P1 flag broad/P2 gate条件)→修正→re-review=approve。boundary over-unlock なし(product L7 block維持確認)。P3 substring anchor hardening は optional deferred。
ticket_is_completion_evidence: false
created: 2026-06-19
owner: PM
target_l_pairs:
  - "L5↔L8 (結合): G8 integration-test execution gate を closure。g8_subcheck で IT-* 21件 anchor + exec_pass を集計し、vg_overview の L5-L8 approved_deferred を条件付き解除"
design_change_class: design_or_contract_changed  # vg_overview の pair status 判定変更 (L5-L8 deferred 条件付き解除) + L8 test-design gap→observed 改訂 + g8_subcheck/doctor route 新設。L5 詳細設計の意味/ID universe/DB schema は不変。required_refreeze_pairs=[L5-L8] (forward-return-discipline、L5 本文不改訂で semantic re-freeze 証跡を記録)。
required_refreeze_pairs:
  - "L5-L8"
agent_slots:
  - role: se
    slot_label: "SE — g8_subcheck 新設 (G7 パターン複製) + IT gap3件 結合テスト実装 + IT-* anchor map + vg_overview L5-L8 条件付き解除 + doctor route + pin 更新 + pytest/bats（Codex）"
  - role: tl-advisor
    slot_label: "TL — g8 evidence の非 gameable 性 (anchor AND exec_pass) / CI fresh-checkout 安全性 / L5-L8 refreeze 証跡 / G9-G14 deferred 非破壊 / G7 回帰非破壊 の adversarial check"
generates:
  - artifact_path: cli/lib/g8_subcheck.py
    artifact_type: code
  - artifact_path: cli/lib/vg_overview.py
    artifact_type: code
  - artifact_path: docs/v2/L8-test-design/L5-detailed-design-結合テスト設計.md
    artifact_type: doc
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires:
    - docs/plans/add-feature/add-feature-2026-06-19-plandep-depcycle-baseline-required.md
  blocks: []
related_docs:
  - docs/v2/L7-test-design/right-arm-full-flow-closure-plan.yaml
  - docs/v2/L7-test-design/right-arm-execution-gates-単体テスト設計.md
  - docs/plans/add-feature/add-feature-2026-06-10-full-flow-remaining-guards.md
  - cli/lib/g7_subcheck.py
  - cli/lib/vg_overview.py
---

# Action 右腕 C-4a: G8 (L5↔L8) integration-test execution gate closure

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md) §4.1 右腕 execution gate closure（order=1 = **G8**）。detector hardening (C-3a/b/c/d/e) 完遂後、右腕 4 gate (G8/G9/G12/G14) の最初。ユーザー「右腕+残detector全部」scope 承認 + tl-advisor design 諮問=条件付き推奨。closure-plan 正本 = [right-arm-full-flow-closure-plan.yaml](../../v2/L7-test-design/right-arm-full-flow-closure-plan.yaml) order=1。

## 1. 目的 / 解く問題
右腕 4 gate は `vg_overview.py:36-78` の `DEFERRED_PAIR_EXECUTION_GATES` で常に `approved_deferred` とハードコード。G8 (L5↔L8) は 4 gate で最小（IT-* 21件中 18 observed 済、gap 3件のみ）。本 Action は **G8 execution evidence を読む判定ロジックを実装**し、anchor + execution pass が揃った時に L5-L8 を deferred から外す。これで右腕の最初の execution gate を「Forward 内在ゲート」として実効化する（cov100%単独 pass は禁止、G7 と同じ anchor AND exec_pass）。

## 2. スコープ
### In
- **g8_subcheck.py 新設**（evidence=案A、`g7_subcheck.py` パターン複製）: L8 結合テスト設計 doc の IT-* 21件 inventory + IT-ID anchor map（IT-* → test file/function）+ committed integration-test 実行を集計。`anchored / missing / unanchored / exec_pass / IT_total` を返す。`HELIX_DOCTOR_SKIP_EXEC_TESTS=1` 時は structural anchor を pass 扱い（CI fresh-checkout 永続 red 回避、G7 と同挙動）。**G7 の UT inventory に IT-* を混入させない**（案B 却下）。
- **L8 gap3件の結合テスト実装 + observed 昇格**: IT-MOD-06（Catalog/Trace: code_catalog/contract_registry 索引整合、`helix code`/`helix entry` 経路）/ IT-DB-03（Trace Catalog: code_index↔links↔contract_entries 関係整合）/ IT-DB-05（Requirements/Quality: req_*_map/verify_runs trace 整合）。`docs/v2/L8-test-design/L5-detailed-design-結合テスト設計.md` の当該 3 行を gap→observed に改訂（**L5 本文は不変**）。
- **vg_overview の L5-L8 条件付き解除**: `trace_clean(L5-L8) AND g8.anchored==IT_total AND g8.missing==0 AND g8.unanchored==0 AND g8.exec_pass==g8.anchored` が真の時のみ L5-L8 を `approved_deferred` から外し clean に。偽なら deferred 維持（evidence 不足を隠さない）。**G9/G12/G14 の deferred は不変**。
- **helix-doctor route**: `check_g8_subcheck`（standalone）追加。`check_vg_overview` が g8 evidence を読む配線。
- **pin 更新**: strict-full-flow の `deferred_count` 4→3 / `deferred_gates=[G9,G12,G14]` を `test_vg_overview.py` / `helix-doctor-json.bats` / 境界契約で更新。default `check_vg_overview --gate` は L6 focus green を維持。
- **L5↔L8 semantic re-freeze 証跡**: 「L5 unchanged + L8 observed昇格 + trace_symmetry(L5-L8) clean + TL semantic-pass」を記録（forward-return-discipline、required_refreeze_pairs=[L5-L8]）。
- **境界 count 25→26 同期**（audit yaml×6 + contract py + bats mirror）+ 境界契約に C-4a current_scope_authorized 追加（forbidden_now 不変）。

### Out（forbidden_now / 別 Action）
- G9/G12/G14 の deferred 解除（C-4b/c/d、別 Action）。
- strict-full-flow を default gate に昇格（forbidden_now / broad flip）。
- L5 詳細設計の MOD/DB 意味・ID universe・DB schema 変更（出たら設計変更として差戻し）。
- g7_subcheck の汎用 `execution_anchor_subcheck` 抽出（blast radius 大、今回は複製寄り）。

## 3. 受入条件
1. g8_subcheck: IT-* 21件 inventory + anchor map + exec を集計、`anchored==IT_total(21) AND missing==0 AND unanchored==0 AND exec_pass==anchored`。SKIP_EXEC 時 structural pass で CI red 回避。G7 UT inventory 非混入。
2. gap3件 observed 昇格: IT-MOD-06/IT-DB-03/IT-DB-05 の結合テストが実装され green、L8 doc が observed に改訂、trace_symmetry(L5-L8) coverage 100%/uncovered0/orphan0 維持。
3. vg_overview: 上記 AND 条件で L5-L8 が deferred→clean。条件未達なら deferred 維持。G9/G12/G14 deferred 不変、overall_clean=true 維持。cov100%単独 pass 不可。
4. CI fresh-checkout 安全: evidence は committed tree から解決、`HELIX_DOCTOR_SKIP_EXEC_TESTS=1` で structural pass。fresh-checkout bats が g8_subcheck の新 import を解決できる（依存漏れなし）。
5. 既存非破壊: G7 closure（anchored 98/98 exec_pass98）回帰なし。default check_vg_overview --gate green。
6. 境界契約整合: C-4a current_scope_authorized、forbidden_now 不変、count 25→26 一貫（count-drift green）。
7. 全テスト緑: 全 pytest + 全 bats + check_vg_overview --gate green + 対象 integration test（skip なし実行 pass）。

## 4. テスト計画
- g8_subcheck pytest（inventory/anchor/missing/unanchored/exec_pass/SKIP_EXEC structural pass、G7 非混入）。
- gap3件の結合テスト本体（IT-MOD-06/IT-DB-03/IT-DB-05）。
- vg_overview pytest（L5-L8 条件付き解除: 達成時 clean / 未達時 deferred 維持 / G9-G14 deferred 不変 / G7 回帰）。
- 境界 contract test（C-4a + count 25→26 + deferred_count 4→3）+ bats mirror。
- fresh-checkout bats 回帰（新 import 解決、C-1/C-3a 教訓）。

## 5. forward_return / 収束
- frontmatter の通り。design_change_class=design_or_contract_changed、required_refreeze_pairs=[L5-L8]。[forward-return-discipline](../../../HELIX-workflows/helix-process/forward-return-discipline.md) 適用（L5 本文不改訂で semantic re-freeze 証跡を記録）。closure-plan.yaml order=1 を参照（evidence source にはしない=order/acceptance/rollback の正本）。L5↔L8 G8 pending gate evidence に帰属。

## 6. escalation / リスク
- **TL P0（design 諮問で確定）**: pure_impl 不可、required_refreeze_pairs=[L5-L8]。evidence=案A（g8_subcheck）。pass=anchor AND exec_pass。CI fresh-checkout は committed tree + SKIP_EXEC structural pass。
- **差戻し条件**: L5 MOD/DB 意味変更 / DB schema / D-DB/D-CONTRACT / .helix DB evidence 必須化が必要になったら G8 Action でなく設計変更として PM/TL へ差戻し。
- リスク: fresh-checkout bats の g8_subcheck 依存漏れ（C-1/C-3a 教訓 = fresh tree に全 files-under-test を copy）。G7 UT inventory への IT-* 混入（案B 却下、pytest で機械防止）。pin 更新漏れ（deferred_count 4→3 / count 25→26 を git diff から網羅抽出）。auth/payment/PII/secret/schema 変更なし。

## 7. 進捗ログ
| 日付 | 内容 | 担当 |
|---|---|---|
| 2026-06-19 | Action 起票（Process §4.1 右腕 order=1 = C-4a/G8）。pmo-project-explorer scope 調査（右腕 4 pair 現状 / G8 最小 / gap3件 / 既存 scaffolding）→ tl-advisor design 諮問=条件付き推奨（design_change_class / required_refreeze_pairs=[L5-L8] / evidence 案A g8_subcheck / pass anchor AND exec_pass / CI fresh-checkout 安全 / parked PLAN 非activate / G9-G14 不変 / 差戻し条件）。次=Codex se TDD 実装。 | PM (Opus) + pmo-project-explorer + tl-advisor |
| 2026-06-19 | Codex se 実装（16 ファイル）: g8_subcheck 新設 + gap3件 結合テスト + vg_overview L5-L8 条件付き解除 + doctor route + 多数 pin 更新 + c4a 境界 entry。**allowed_files 拡張（PM 承認）**: G8 closure で strict deferred_count が 4→3 になる ripple が当初想定より広く、`right-arm-execution-gates-adoption.yaml`（current_deferred_count）/ `feedback-loop-adoption-audit.yaml`（strict_vg_deferred_count + gates）/ `test_harness_monitor_unit.py` / `test-helix-harness-feedback-loop.bats` を allowed_files に追加（deferred gate 列挙の整合）。負 test（test_vg_overview.py:928 = g8 exec_pass 不完全で G8 非closure）は 4 据置（=正）。PM が adoption yaml count + contract bats:7717 を先行 sync、残ripを Codex se follow-up へ。 | PM (Opus) + Codex se |
| 2026-06-19 | **gate G-tests fresh-checkout regression 1件を修正** (gate が捕捉、targeted run の穴): `test_fr_uses_full_required.py::test_collect_vg_overview_uses_full_required_fr_uses_summary` が minimal tmp-tree で collect_vg_overview を呼ぶが、G8 で vg_overview が `collect_g8_subcheck`(L8 doc 読込) を新たに呼ぶため tmp-tree に L8 doc 無く FileNotFoundError。**他 detector 同様 collect_g8_subcheck の clean stub monkeypatch を追加**(C-3a fresh-checkout lesson の再適用)。他に同種リスク無し(test_helix_l0_l14_flow_contract の vg 呼び出しは REPO_ROOT 使用)。修正後 file 4 passed。次=amend + gate 再 push。 | PM (Opus) |
| 2026-06-19 | **完遂**: g8 exec gating fix (execute_g7_tests=False 時 structural anchor=決定的) で残2 pytest fail 解消 → tl-advisor impl review=changes_required (P0 anchor file-level=gameable / P1 l7_work_allowed_from_handover broad / P2 gate条件) → Codex se 修正 (P0: anchor を path::IT-ID + word-boundary needle + 全21 IT に test マーカー + anti-gaming negative test / P1: flag を right_arm_*/product_l7_* 分割 / P2: gate条件を clean式) → **PM anti-gaming 独立実証** (# IT-MOD-06 除去→clean False/anchored20、復元→21) → **tl-advisor re-review=approve** (P0/P1/P2 解消、boundary over-unlock なし、残P3 substring照合の word-boundary化は optional deferred)。検証=pytest 138/112+88 + bats84 (env無) / check_g8_subcheck anchored21 exec21 clean / check_vg_overview overall_clean=true deferred=3 / strict deferred=[G9,G12,G14] L5-L8 applicable。次=commit + gate-driven push。**deferred follow-up: P3 (_existing_anchor_paths の needle 照合を re.search word-boundary 化、substring false-positive 防止)**。 | PM (Opus) + Codex se + tl-advisor |
| 2026-06-19 | **boundary machinery 抵触 → ユーザー裁定取得**。G8 closure が機械強制 `latest_user_boundary`（full-objective-gap-status.yaml:42-53）に抵触（`l7_requested_now: false` / current_allowed_work=L1-L6+pre-L7 / forbidden_now=L7 product feature impl）= /goal「L7完全実装」+「右腕全部」承認より前の stale 状態。tl-advisor boundary-evolution framing 諮問=条件付き推奨（右腕 gate closure は forbidden の "L7 product feature/coverage" と別カテゴリ＝維持可、current_allowed_work に右腕 gate 限定文言追加、`l7_requested_now: true` 単独は product L7 誤読＝scope 限定必須、user 裁定要）。**AskUserQuestion=「右腕 G8-G14 順次解禁（推奨）」承認**。→ boundary を限定解禁へ evolve（current_allowed_work += 右腕 execution-gate closure 順次/bounded/deferred_pair 除去のみ、forbidden_now は product L7 維持 + product挙動/schema/D-CONTRACT/gate実装=完了誤認 追加）。replicated 4 site（full-objective-gap-status.yaml + l1-l6-double-check-coverage.yaml + contract py + bats mirror）+ interlocking flag 同期。 | PM (Opus) + tl-advisor + ユーザー裁定 |
| 2026-06-19 | **ripple blast radius が design-review scope 超過 → tl-advisor 戦略諮問（2回目）=条件付き推奨（分類して bounded expansion で完遂、SSoT refactor は別 PLAN defer）**。`deferred_count=4` が ~12 site（active ledger・current test-design contract・tests）に hand-pin。TL 分類: ①live-coupled / active ledger（goal-completion-audit / full-flow-activation-ledger / ci-gate-surface-audit / full-objective-gap-status 残）→3（`goal_complete_allowed=false` 維持）②frozen/current test-design contract（deferred-gate-adoption / right-arm-execution-gates 単体テスト設計）→ current expected=3 + pre-G8 baseline 隔離 + refreeze 証跡 ③historical/dated（2026-06-09-l0-l6-focus-audit.md）→4 据置 ④negative fixture（test_vg_overview:928）→4 据置。**L7 test-design contract sync の refreeze**: required_refreeze_pairs=[L5-L8] で L5↔L8 semantic は十分、L7 adoption/test-contract の current expected 改訂は本 PLAN の allowed_files 拡張 + 本 closure の observed 更新として帰属（pre-G8 baseline 隔離で履歴非破壊）。**SSoT 違反は DF-P2-DEFERRED-COUNT-DERIVE（Process §4）に defer**（deferred_count を live VG から derive、G9-G14 前後で別 refactor PLAN 起票）。ユーザー諮問不要（authorized scope + TL 解決済）。次=Codex se に TL 分類で bounded sync 完遂。 | PM (Opus) + tl-advisor |
