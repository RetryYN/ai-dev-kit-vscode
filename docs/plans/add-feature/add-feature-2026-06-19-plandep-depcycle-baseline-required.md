---
plan_id: add-feature-2026-06-19-plandep-depcycle-baseline-required
title: "Action(add-feature): L7 自動化③d/e — plan_dependency + dependency_cycle を baseline-required 化 (既存債=accepted floor, 新債のみ fail-close)"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L6-functional-design/registry-detector-機能設計.md  # trace: plan_dependency_gate(FR-LIB-158/FN-WSC-227) と dependency_cycle/import_cycle(FR-LIB-157/FN-WSC-226) の L6 設計。本 Action は両 detector を changed-files ratchet から baseline-required(既存 baseline=accepted floor, baseline 超の新債のみ blocking)へ昇格。実債(5循環/49warning)解消は別 Refactor/PLAN に defer。
forward_return: "plan_dependency_gate / import_cycle に baseline-required summary (collect_*_baseline_required_summary: full-scan で baseline 超の findings のみ blocking、clean=新債0、source=baseline_required) を追加 -> plan_validator の blocks 実在 false-positive(実在 phase2 を missing 報告)を root-cause 修正 -> 正しい baseline を accepted floor として確定(false-positive を baseline に吸収しない) -> vg_overview.required_clean.{plan_dependency_gate,dependency_cycle_checks} を baseline-required へ切替 -> 実債解消を DF-P2-EXISTING-CYCLES(Refactor) / DF-P2-PLANDEP-WARNINGS(PLAN編集) に defer(expiry+ticket、Process §4) -> automation-gate-map §3.4 に C-3d/e 記録 -> L7 境界契約に C-3d/e current_scope_authorized 追加(forbidden_now 不変) -> L6↔L7 G7 pending gate evidence に帰属."
drive: be
status: completed
status_note: "2026-06-19 完遂。Process §4.1 ③ per-detector 第4/5手 = C-3d(plan_dependency) / C-3e(dependency_cycle)。ユーザー AskUserQuestion(2026-06-18) で『右腕+残detectorを順に全部』scope 承認 + (2026-06-19) approach=『baseline-required 両方(TL推奨)』を明示裁定。両 detector を changed-files ratchet から baseline-required(既存 baseline=accepted floor, baseline 超の新債のみ blocking)へ昇格。new-1(plan_validator が実在 phase2 を missing 報告する false-positive)は baseline 吸収せず root-cause 修正(path 形式参照の解決バグ)→同クラス false-positive 7件も baseline から除去(追加0、削除のみ)。実債解消(5循環/plan warning)は DF-P2-EXISTING-CYCLES / DF-P2-PLANDEP-WARNINGS に defer。tl-advisor impl review=approve(P0/P1 なし、P3=PM 報告の削除件数13→実7のみ)。検証=pytest 154 / bats 57 / vg_overview overall_clean=true(両 detector mode=baseline_required, blocking0) / count 24→25 同期。"
current_task_scope: plandep_depcycle_baseline_required
approval_required_before_l7_work: false  # ユーザー AskUserQuestion で scope + approach 承認済
tl_review: approve  # impl review (tl-advisor 2026-06-19)=approve。P0/P1 なし。path 解決は実在参照のみ canonicalize(存在しない参照は従来通り does not exist=PLAN-999 回帰保持)、baseline 非吸収、vg_overview shim 妥当、defer ticket 十分。P3(削除件数の PM 報告 13→実7)は実装非影響。
ticket_is_completion_evidence: false
created: 2026-06-19
owner: PM
target_l_pairs:
  - "L6↔L7 (単体): plan_dependency_gate を baseline-required 化 (baseline 超の新債のみ blocking)"
  - "L6↔L7 (単体): import_cycle(dependency_cycle) を baseline-required 化 (baseline 超の新循環のみ blocking)"
  - "vg_overview: required_clean.{plan_dependency_gate, dependency_cycle_checks} を baseline-required mode へ"
design_change_class: design_or_contract_changed  # vg_overview required_clean の評価範囲切替 (changed-files ratchet→baseline-required) + plan_validator false-positive 修正 + 境界契約 evolution。registry schema 不変。再凍結 scope: L6-L7。
agent_slots:
  - role: se
    slot_label: "SE — baseline-required summary 2件 + plan_validator false-positive 修正 + vg_overview 配線 + pytest（Codex）"
  - role: tl-advisor
    slot_label: "TL — baseline-required semantics(新債のみ blocking) / false-positive 修正の正当性 / defer ticket / ratchet との差 の adversarial check"
generates:
  - artifact_path: cli/lib/plan_dependency_gate.py
    artifact_type: code
  - artifact_path: cli/lib/dependency_cycle_checks.py
    artifact_type: code
  - artifact_path: cli/lib/vg_overview.py
    artifact_type: code
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires:
    - docs/plans/add-feature/add-feature-2026-06-18-coding-rule-core-full-required.md
  blocks: []
related_docs:
  - docs/plans/add-feature/add-feature-2026-06-16-c3a-fr-uses-forward-full-required.md
  - HELIX-workflows/helix-process/automation-gate-map.md
  - cli/lib/plan_dependency_gate.py
  - cli/lib/dependency_cycle_checks.py
---

# Action 自動化③d/e: plan_dependency + dependency_cycle を baseline-required 化

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md) §4.1 ③（per-detector 昇格の第4/5手 = **C-3d/C-3e**）。ユーザー AskUserQuestion で scope(「右腕+残detector全部」) + approach(「baseline-required 両方」, TL 推奨)を裁定。残 2 ratchet detector の昇格で §4.1 step3(detector hardening) を完了する。

## 1. 目的 / 解く問題
plan_dependency_gate(finding 50, baseline 49+new1) と dependency_cycle(finding 5, 全 waive) は changed-files ratchet で稼働。C-3a/C-3c の債0 full-required と違い**実債を伴う**。ユーザー裁定 = **baseline-required**: 既存債を accepted floor として可視化したまま残し、**baseline 超の新債のみ full-scan fail-close**。ratchet(changed-files 依存)より強い恒久保証。実債解消(5循環 Refactor / 49warning PLAN 編集)は別 PLAN に defer。

## 2. スコープ
### In
- **plan_validator false-positive 修正**(最優先): plan_validator が **実在する** `add-feature-2026-06-14-pre-l7-gate-hardening-phase2.md`(plan_id 一致)を `blocks` 参照先 "does not exist" と誤報告(new-1)。root-cause(path/cwd/解決ロジック)を特定し**修正**する。**この false-positive を baseline に吸収しない**(昇格直前に新債を正当化=禁止)。
- `cli/lib/plan_dependency_gate.py`: `collect_plan_dependency_baseline_required_summary()` 追加。full-scan で baseline(`plan-dependency-baseline.json`)超の findings のみ blocking、`clean = blocking_finding_count == 0`(新債0)、`source_status=baseline_required`(changed-files 非依存)。false-positive 修正後の正しい全 findings を baseline=accepted floor に確定。既存 ratchet/standalone 不変。
- `cli/lib/dependency_cycle_checks.py`: `collect_import_cycle_baseline_required_summary()` 追加。同様に `import-cycle-baseline.json`(5循環)超の新循環のみ blocking。
- `cli/lib/vg_overview.py`: `required_clean.{plan_dependency_gate, dependency_cycle_checks}` を baseline-required summary へ切替。他 detector 不変。
- pytest(TDD): ① baseline 内の既存債→clean / ② baseline 超の新債(模擬)→blocking / ③ changed-files 非依存 / ④ false-positive 修正の回帰 / ⑤ vg_overview 配線。
- **defer ticket**(Process §4): **DF-P2-EXISTING-CYCLES**(5循環の Refactor 解消, kind=refactor, expiry, forward_return=L7/L8) + **DF-P2-PLANDEP-WARNINGS**(49 dependency warning の PLAN 編集解消, expiry)。baseline expiry 切れ対策の追跡。
- automation-gate-map §3.4 + 総論に C-3d/e 記録。**baseline-required と full-required(C-3a/C-3c) の用語区別**を明記。
- **L7 境界契約 evolution**: C-3d/e を current_scope_authorized 追加。forbidden_now 不変。count 24→25 同期。

### Out（forbidden_now / 別 Action）
- 5 循環の Refactor 破壊 / 49 warning の PLAN 編集解消(DF-P2-* に defer)。
- baseline 超でない既存債の fail-close 化(=既存債を解消扱いにすること)。
- 他 Action / broad flip。

## 3. 受入条件
1. false-positive 修正: plan_validator が実在 phase2 を正しく認識(new-1 が消えるか、root-cause が detector バグなら修正)。**baseline 吸収でない**。
2. baseline-required semantics: 両 summary が baseline 超の新債のみ blocking、clean=新債0。changed-files 非依存。
3. 既存非破壊: ratchet summary / standalone / 他 detector 不変。
4. 命名区別: `baseline_required`(C-3a/C-3c の `full_required` と別 mode 名)。
5. defer ticket: DF-P2-EXISTING-CYCLES / DF-P2-PLANDEP-WARNINGS が Process §4 に expiry + owner 付きで記録。
6. 境界契約整合: C-3d/e current_scope_authorized、forbidden_now 不変、count 24→25 一貫(count-drift green)。
7. 全テスト緑: 全 pytest + 全 bats + check_vg_overview --gate green。

## 4. テスト計画
- baseline-required pytest(§2 ①-⑤、両 detector)。false-positive 修正の回帰 test。境界 contract test(C-3d/e + count 24→25)。

## 5. forward_return / 収束
- frontmatter の通り。defer = DF-P2-EXISTING-CYCLES / DF-P2-PLANDEP-WARNINGS(Process §4、expiry)。design_change_class=design_or_contract_changed、再凍結 scope=L6-L7。[forward-return-discipline](../../../HELIX-workflows/helix-process/forward-return-discipline.md) 適用。

## 6. escalation / リスク
- **TL P1**: false-positive(new-1)を baseline 吸収すると昇格直前に新債を正当化→gate 信頼性低下。**先に root-cause 修正**(§2 最優先)。
- **TL P1**: `full-required` 命名を流用すると C-3a/C-3c の債0 と混同→`baseline-required` に分離。
- **TL P2**: plan_dependency の `kind="other"` が粗い→full-scan block 対象の説明責任。分類精緻化を検討(最小は維持)。
- **TL P3**: baseline expiry → defer ticket 必須(§2)。
- 既存債(5循環/49)の設計劣化は残る(accepted floor)→ defer ticket の expiry+acceptance で管理。auth/payment/PII/secret/schema 変更なし。

## 7. 進捗ログ
| 日付 | 内容 | 担当 |
|---|---|---|
| 2026-06-19 | Action 起票(Process §4.1 ③d/e)。ユーザー approach 裁定=baseline-required 両方。tl-advisor approach 諮問=passed(A推奨、new-1 は baseline 吸収せず root-cause 修正、循環 Refactor は別 PLAN defer、baseline-required 命名分離、user 裁定必須→取得済)。new-1=plan_validator が実在 phase2 を missing 誤報告(false-positive 疑い)。次=Codex se TDD 実装(false-positive root-cause 含む)。 | PM (Opus) + tl-advisor |
| 2026-06-19 | 実装(Codex se TDD)+ PM 独立検証 + TL impl review。`plan_validator` の path 形式参照解決バグを root-cause 修正(`locate_plan_file` が `.md`/`/`/絶対 path を `_resolve_plan_pointer` 経由で解決、`_dependency_ref_matches_plan`/`_canonicalize_dependency_reference` を self-edge/reciprocal/cycle 判定へ適用)→ new-1 消滅 + 同クラス false-positive 7件を baseline から除去(追加0)。`collect_plan_dependency_baseline_required_summary` / `collect_import_cycle_baseline_required_summary`(full-scan, baseline floor 超のみ blocking, clean=新債0, mode/source=baseline_required)+ vg_overview 配線(monkeypatch 後方互換 shim)。PM 検証: pytest 154 / bats 57 / py_compile OK / check_vg_overview overall_clean=true(plan_dep finding42 blocking0, import_cycle finding5 blocking0) / standalone advisory 不変 new_finding=0 / 削除7件参照先は全実在(find 確認) / count 24→25 全 pin 同期。TL impl review=**approve**(P0/P1 なし、P3=削除件数 PM 報告のみ)。次=commit + gate-driven push。 | PM (Opus) + Codex se + tl-advisor |
