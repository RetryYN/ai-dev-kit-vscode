---
plan_id: add-feature-2026-06-18-coding-rule-core-full-required
title: "Action(add-feature): L7 自動化③c — coding_rule_lint の core(bash-n/py_compile) を full-scan required 化 (optional=ruff/shellcheck は advisory 据置, C-2 境界遵守)"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L6-functional-design/registry-detector-機能設計.md  # trace: coding_rule_lint (FR-LIB-155/FN-WSC-225) の L6 設計。本 Action は core ルール(bash-n/py_compile)を full-scan required 化し、optional(ruff/shellcheck)は required path に混入させない(C-2 advisory 境界)。
forward_return: "coding_rule_lint に core-only full-required summary (collect_coding_rule_lint_full_required_summary: full-scan で bash_n/py_compile 違反を blocking 評価、clean=blocking_finding_count==0、ruff/shellcheck は blocking に算入しない) を追加 -> vg_overview.required_clean.coding_rule_lint を changed-files ratchet から core full-required へ切替 -> automation-gate-map §3.4 に C-3c を記録 -> L7 境界契約に C-3c を current_scope_authorized 追加 (forbidden_now broad flip / external tool required 化は不変) -> L6↔L7 G7 pending gate evidence に帰属 (weakness-map W16/W17)."
drive: be
status: completed
status_note: "2026-06-18 完遂。Process §4.1 ③ per-detector 第3手 = C-3c。coding_rule_lint の core(bash-n/py_compile) のみ full-scan required 化、optional(ruff/shellcheck)は advisory 据置(C-2 境界、required path 非混入=CORE_REQUIRED_TOOLS={bash_n,py_compile})。実測 full-scan core 違反 0(685本全 valid)ゆえ CI red にならない。tl-advisor impl review=approve(P0/P1/P2 なし、P3 doc 総論 wording→PM 修正済)。検証=pytest 107、standalone clean、vg_overview overall_clean=true(mode=core_full_required, blocking0)、count 24 同期。"
current_task_scope: coding_rule_core_full_required
approval_required_before_l7_work: false  # ユーザー AskUserQuestion (2026-06-18) で scope 承認済
tl_review: approve  # impl review (tl-advisor 2026-06-18)=approve。P0/P1/P2 なし、P3(automation-gate-map 総論 wording)は PM 修正で closure。
ticket_is_completion_evidence: false
created: 2026-06-18
owner: PM
target_l_pairs:
  - "L6↔L7 (単体): coding_rule_lint core(bash-n/py_compile) を full-scan required 化 (changed-files ratchet→core full-required)"
  - "vg_overview: required_clean.coding_rule_lint を core full-required mode へ (blocking=bash_n/py_compile のみ、ruff/shellcheck 非算入)"
design_change_class: design_or_contract_changed  # vg_overview required_clean の評価範囲切替 (ratchet→core full-required) + 境界契約 evolution。registry schema 不変、external tool は required path に入れない。再凍結 scope: L6-L7。
agent_slots:
  - role: se
    slot_label: "SE — collect_coding_rule_lint_full_required_summary(core only) + vg_overview 配線 + pytest（Codex）"
  - role: tl-advisor
    slot_label: "TL — core/optional 境界(ruff/shellcheck 非混入) / blocking-only clean / narrow flip の adversarial check"
generates:
  - artifact_path: cli/lib/coding_rule_lint.py
    artifact_type: code
  - artifact_path: cli/lib/vg_overview.py
    artifact_type: code
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires:
    - docs/plans/add-feature/add-feature-2026-06-16-c3a-fr-uses-forward-full-required.md
  blocks: []
related_docs:
  - docs/plans/add-feature/add-feature-2026-06-16-c3a-fr-uses-forward-full-required.md
  - docs/plans/add-feature/add-feature-2026-06-15-c2-ruff-shellcheck-advisory.md
  - HELIX-workflows/helix-process/automation-gate-map.md
  - cli/lib/coding_rule_lint.py
---

# Action 自動化③c: coding_rule_lint core(bash-n/py_compile) を full-scan required 化

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md) §4.1 ③（per-detector 昇格の第3手 = **C-3c**）。ユーザー AskUserQuestion (2026-06-18) で「右腕 + 残 detector を順に全部」scope を承認。C-3a(fr_uses fwd)/C-3b(fr_uses rev) に続く detector 昇格。

## 1. 目的 / 解く問題
coding_rule_lint は core(bash-n/py_compile) と optional(ruff/shellcheck, which-guard で graceful skip) を分離済だが、changed-files ratchet で稼働中。**core ルールは外部ツール不要で常時実行可能**かつ実測で full-scan 違反 0（685本=bash195+py490 全 syntactically valid）。→ core を full-scan full-required 化し「全 bash/py が構文的に妥当」を全件 fail-close で保証する。optional(ruff/shellcheck) は外部ツール依存ゆえ C-2 advisory CI job のまま（required path 非混入）。

## 2. スコープ
### In
- `cli/lib/coding_rule_lint.py` に **`collect_coding_rule_lint_full_required_summary()`** を追加: `collect_violations` を full-scan し、**core(tool∈{bash_n, py_compile}) の違反のみ blocking** に評価、`clean = blocking_finding_count == 0`。ruff/shellcheck の違反は blocking に算入しない。`source_status` は full-scan ゆえ changed-files 非依存。既存 `collect_coding_rule_lint_gate_summary`(ratchet) / `evaluate_coding_rule_lint` は不変。
- `cli/lib/vg_overview.py` の `required_clean.coding_rule_lint` を ratchet から **core full-required summary** へ切替。
- pytest(TDD): ① full-scan core 違反があれば fail / ② ruff/shellcheck の違反(模擬)は blocking に算入しない / ③ changed-files 非依存 / ④ vg_overview.required_clean.coding_rule_lint が core full-required で blocking 0 → clean。
- automation-gate-map §3.4 に C-3c 記録。
- **L7 境界契約 evolution**: C-3c を current_scope_authorized 追加(文言=「core bash-n/py_compile full-scan required only。ruff/shellcheck required 化は含まない」)。forbidden_now(broad flip / external tool required 化)不変。count 23→24 同期(audit yaml×6 + contract py + bats mirror、`aeb7013`/`e216c95` テンプレに +1)。

### Out（forbidden_now / 別 Action）
- ruff/shellcheck を required/blocking path に入れる（C-2 advisory 境界 / forbidden_now 抵触、別判断）。
- 他 detector(dependency_cycle/plan_dependency)の昇格(別 Action)。
- broad 一括 flip。

## 3. 受入条件
1. core full-required: `collect_coding_rule_lint_full_required_summary` が full-scan core(bash_n/py_compile) を blocking-only clean 判定。現状 0 で clean。
2. optional 非混入: ruff/shellcheck 違反は blocking/clean 判定に算入しない（C-2 境界）。
3. 既存非破壊: ratchet summary / evaluate / standalone 挙動不変。
4. 境界契約整合: C-3c current_scope_authorized、forbidden_now 不変、count 23→24 が audit yaml + contract py + bats mirror で一貫(count-drift green)。
5. 全テスト緑: 全 pytest + 全 bats + `check_vg_overview --gate` green。

## 4. テスト計画
- coding_rule_lint core full-required pytest(TDD §2 ①-④)。
- 境界契約 contract test(C-3c + count 23→24)。

## 5. forward_return / 収束
- frontmatter の通り。automation-gate-map §3.4 + 境界契約 → L6↔L7 G7 pending gate evidence(weakness-map W16/W17)。design_change_class=design_or_contract_changed、再凍結 scope=L6-L7。[forward-return-discipline](../../../HELIX-workflows/helix-process/forward-return-discipline.md) 適用。

## 6. escalation / リスク
- full-scan core 違反 0 ゆえ CI red にならない。auth/payment/PII/secret/schema 変更なし。
- リスク: ruff/shellcheck を blocking に誤算入すると C-2 境界破り(外部ツール required 化)→ §2/pytest で機械防止。
- リスク: count 23→24 の 4 点同期漏れ → `aeb7013`/`e216c95` の git diff から pinned 値網羅抽出。

## 7. 進捗ログ
| 日付 | 内容 | 担当 |
|---|---|---|
| 2026-06-18 | Action 起票(Process §4.1 ③c)。scope 承認済。実測: full-scan core 違反 0(685本全 valid)→ full-required 安全。core/optional 分離は既存。次=Codex se TDD 実装。 | PM (Opus) |
| 2026-06-18 | 実装(Codex se TDD)+ PM 検証 + TL impl review。`collect_coding_rule_lint_full_required_summary`(blocking=CORE_REQUIRED_TOOLS={bash_n,py_compile} のみ、ruff/shellcheck は warning 非算入、clean=blocking==0、mode=core_full_required)+ vg_overview required_clean 切替。pytest 107 / standalone clean / vg_overview overall_clean=true / count 23→24 同期。TL impl review=**approve**(P0/P1/P2 なし、P3 automation-gate-map 総論 wording を PM 修正)。次=commit + gate-driven push。 | PM (Opus) + Codex se + tl-advisor |
