---
plan_id: refactor-2026-06-20-deferred-count-derive
title: "Refactor: 右腕 deferred_count/deferred_gates の hand-pin SSoT 違反を live VG derive 化 (current/live のみ、履歴/負/target は pin 維持) — G9-G14 手 sync 地獄の解消"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: refactor
kind: refactor
layer: L7
process_layer: L7
parent_design: docs/v2/L6-functional-design/registry-detector-機能設計.md  # trace: vg_overview の full_flow_execution 判定 (FR-LIB 系)。本 Refactor は gate semantics / vg public JSON schema を不変に保ち、current/live deferred 状態の count 出所を hand-pin から live VG derive へ置換するのみ。
forward_return: "live SSoT helper (例 live_strict_deferred_pairs(root): collect_vg_overview(strict_full_flow=True, execute_g7_tests=False) から現在未完 deferred pair を返す) を 1 箇所に新設 -> current/live mirror (goal-completion-audit.strict_full_flow_status / full-objective-gap-status.right_arm_execution_boundaries / ci-gate-surface-audit.strict_full_flow / feedback-loop-adoption-audit.current_capabilities / integration・bats の current expected G9/G12/G14) を derive 参照へ置換 -> static gate catalog (G8/G9/G12/G14 plan_id/target/受入条件)・履歴 snapshot (captured_snapshot/pre-G8 baseline/G8 closed record/closure-plan target deferred_count:0/dated audit)・負 fixture (test_vg_overview g8 incomplete deferred_count==4/harness fake payload) は pin 維持 -> drift test は doc/current mirror ⇔ live のみ (production command と production helper の同一値比較=vacuous は禁止) -> gate 判定 (G8 closure 条件 / semantic orphan) と vg public JSON schema は不変 -> 振る舞い不変 Refactor として L7 へ forward_return。P3 (g8_subcheck word-boundary anchor) は別 micro commit。"
drive: be
status: completed
status_note: "2026-06-20 完遂。G8 closure で deferred_count=4 が ~12 site hand-pin (SSoT 違反) → 1 gate 閉じるのに全 site 手 sync (Codex 5回 block) と判明。G9/G12/G14 で 3 回再発するため、ユーザー AskUserQuestion (2026-06-19) で『derive refactor を先行 (TL推奨)』を裁定。live SSoT helper live_strict_deferred_pairs() 新設、current/live mirror (goal-completion-audit/ci-gate-surface-audit/feedback-loop-adoption-audit/full-objective-gap-status right-arm) を doc⇔live drift 照合へ、履歴/負/target/static catalog は pin 維持。振る舞い不変 (G8 applicable / G9-G14 deferred / deferred_count=3 / vg JSON schema 不変)。Codex se 実装 → sort-key bug (lexical→numeric) PM 検出→Codex 修正 → TL impl review approve (P2 容認/P3 count-pin 復元) → 全 pytest 2666 passed / contract bats 57/57 / live=[G9,G12,G14]。"
current_task_scope: deferred_count_derive
approval_required_before_l7_work: false  # ユーザー AskUserQuestion で derive refactor 先行を裁定
tl_review: approve
ticket_is_completion_evidence: false
created: 2026-06-20
owner: PM
target_l_pairs:
  - "L7 (refactor): right-arm current/live deferred_count/deferred_gates を live VG derive 化 (振る舞い=gate 判定不変、count 出所のみ変更)"
design_change_class: design_or_contract_changed  # gate 判定 / vg public JSON schema は不変だが、audit/test mirror の count 表現 (hand-pin→derived) を変える。振る舞い不変 Refactor。L-pair design 変更なし (infrastructure refactor)。再凍結 scope: なし (gate semantics 不変、TL 条件)。
agent_slots:
  - role: se
    slot_label: "SE — live SSoT helper + current mirror derive 置換 + drift test (doc⇔live) + 履歴/負/target pin 維持 + pytest/bats（Codex）"
  - role: tl-advisor
    slot_label: "TL — derive が vacuous test 化していないか / 履歴・負・target が pin 維持か / gate semantics・vg schema 不変か / drift 検出力が残るか の adversarial check"
generates:
  - artifact_path: cli/lib/vg_overview.py
    artifact_type: code
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires:
    - docs/plans/add-feature/add-feature-2026-06-19-g8-integration-execution-gate.md
  blocks: []
related_docs:
  - docs/plans/process/process-2026-06-08-verification-forward-gate.md
  - cli/lib/vg_overview.py
---

# Refactor: 右腕 deferred_count/deferred_gates の live VG derive 化

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md) §4 DF-P2-DEFERRED-COUNT-DERIVE。G8 closure (C-4a) で露呈した hand-pin SSoT 違反を、G9 着手前に解消する。ユーザー AskUserQuestion (2026-06-19)=derive refactor 先行裁定。tl-advisor scope 諮問=条件付き推奨。

## 1. 目的 / 解く問題
右腕 gate の「現在 deferred な数/集合」(`deferred_count` / `deferred_gates`) が ~12 site に hand-pin され cross-consistency test で相互強制 = SSoT 違反。G8 closure で 1 gate 閉じるのに全 site 手 sync が必要 (Codex 5 回 block)。G9/G12/G14 で 3 回再発する。**current/live 状態だけを live VG (`check_vg_overview --strict-full-flow`) から derive** し、hand-pin を SSoT 1 箇所 + 参照に置換して手 sync 地獄を消す。**履歴・負テスト・目標値は pin 維持** (監査履歴と drift 検出力を壊さない)。

## 2. スコープ
### In (derive 化 = current/live mirror)
- **live SSoT helper 新設**: `live_strict_deferred_pairs(root)` 等。`collect_vg_overview(strict_full_flow=True, execute_g7_tests=False)` の `full_flow_execution.deferred_pairs` を source に、現在未完 deferred pair (現状 G9/G12/G14) を返す。
- **current mirror を derive 参照へ**: `goal-completion-audit.strict_full_flow_status` / `full-objective-gap-status.right_arm_execution_boundaries` (current deferred 数/集合) / `ci-gate-surface-audit.local_gate_surface.strict_full_flow` / `feedback-loop-adoption-audit.current_capabilities` / integration・bats の current expected (G9/G12/G14)。docs は `current_*` に `derived_from: strict_vg_overview` + `last_verified_command` を持たせ test が live 一致確認。
- **drift test 再構成**: `doc/current mirror ⇔ live` のみ照合 (production command と production helper の同一値比較=vacuous は禁止)。
### Out (pin 維持 / 別)
- 履歴・監査 snapshot: `captured_snapshot` / pre-G8 baseline / G8 closed record / closure-plan target `deferred_count: 0` / dated audit (2026-06-09 等)。
- 負テスト/fixture: `test_vg_overview.py` の G8 incomplete `deferred_count==4` / harness unit の fake payload。
- static gate catalog: G8/G9/G12/G14 の plan_id/target/受入条件/adoption states/non-goals (契約記録として pin)。
- **gate 判定 (G8 closure 条件 / G9 semantic orphan) と vg public JSON schema は不変**。
- P3 (g8_subcheck `_existing_anchor_paths` word-boundary 化) は別 micro commit (リスク種別が違う)。

## 3. 受入条件
1. live SSoT helper 1 箇所、current mirror が derive 参照。手 sync 不要に。
2. 履歴/負/target/static catalog は pin 維持 (監査履歴・drift 検出力保全)。
3. drift test が doc/mirror⇔live で有効 (vacuous でない=pin を消して live==live にしない)。
4. gate semantics 不変: G8 は applicable のまま、G9/G12/G14 deferred のまま、deferred_count=3、overall_clean 不変。vg public JSON schema 不変。
5. blast radius は docs/test mirror に限定 (10-14 site)。超過なら中断し報告。
6. 全テスト緑 (全 pytest + 全 bats + check_vg_overview)。

## 4. テスト計画
- live SSoT helper の unit test。current mirror の derive⇔live drift test。gate semantics 不変の回帰 (G8 applicable / G9-G14 deferred / deferred_count=3)。負 fixture/履歴 pin が不変であること。

## 5. forward_return / 収束
- frontmatter の通り。振る舞い不変 Refactor → L7 forward_return。design_change_class=design_or_contract_changed (count 表現変更、gate semantics 不変、再凍結 scope なし)。[forward-return-discipline](../../../HELIX-workflows/helix-process/forward-return-discipline.md) 適用。

## 6. escalation / リスク
- **TL P1**: 全部 derive で vacuous test 化 → current/live のみ derive、履歴/負は pin。
- **中断条件**: 作業が docs/test mirror を超えて gate semantics / vg schema に及ぶ、または blast radius が 14 site を大きく超える → 中断し G9 を bounded hand sync で先に進める判断を PM へ。
- auth/payment/PII/secret/schema 変更なし。gate 判定不変ゆえ CI red リスク低。

## 7. 進捗ログ
| 日付 | 内容 | 担当 |
|---|---|---|
| 2026-06-20 | Refactor 起票 (DF-P2-DEFERRED-COUNT-DERIVE)。G8 closure の hand-pin 地獄 (Codex 5 回 block) を受け、ユーザー裁定=derive 先行。tl-advisor scope 諮問=条件付き推奨 (current/live のみ derive、履歴/負/target pin、SSoT helper + static catalog + drift test doc⇔live、gate semantics/vg schema 不変、1 PR、blast 10-14 site)。次=Codex se 実装。 | PM (Opus) + tl-advisor |
| 2026-06-20 | Codex se 実装完遂。live SSoT helper `live_strict_deferred_pairs()` 新設 (vg_overview.py)、current mirror 4 site を doc⇔live drift 照合へ、`derived_from`/`last_verified_command` 注記追加、handover_boundary_contract を derive タスクへ retarget。PM 検証で **sort-key bug** 検出 (gate_id 文字列ソート→lexical [G12,G14,G9]、doc/closure-plan の numeric [G9,G12,G14] と不一致でフル pytest 4 失敗) → Codex se が numeric 化 (`int(str(gate_id)[1:])`) で修正。 | PM (Opus) + Codex se |
| 2026-06-20 | TL impl review = **approve** (P0/P1 なし)。所見: derive は doc payload⇔live helper の別ソース比較で vacuous でない / 履歴・負 (deferred_count==4) ・target (==0) ・static catalog pin 維持 / gate semantics・vg JSON schema 不変 / sort key 安全。P2 (right-arm-execution-gates-adoption.yaml current_deferred_count は frozen-contract pin、live-drift test 有り) = 容認。P3 (bats smoke count pin `88 passed` 弱化) = Codex se が復元。 | TL (tl-advisor) + PM |
| 2026-06-20 | **完遂**。PM 独立検証: 全 pytest **2666 passed / 4 skipped** (env なし authoritative) / contract bats **57/57** / 単一ファイル 88 passed / `check_vg_overview` default overall_clean=true・L5-L8 applicable / strict deferred_count=3・[G9,G12,G14] / live helper=[G9,G12,G14]。境界 governance: contract retarget は live handover と整合・product L7 forbidden 不変・Codex overstep なし。status=completed, tl_review=approve → commit → gate-driven push。 | PM (Opus) |
