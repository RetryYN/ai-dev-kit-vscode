---
plan_id: add-feature-2026-06-16-c3a-fr-uses-forward-full-required
title: "Action(add-feature): L7 自動化③a — fr_uses forward(uses先実在) を full-scan required 化 (narrow per-detector flip)"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L6-functional-design/registry-detector-機能設計.md  # trace: fr_uses_checks (FR-LIB-159/FN-WSC-228) の L6 設計。本 Action は forward 判定の評価範囲を changed-files ratchet→full-scan に上げ、vg_overview required_clean を full-required mode へ切替。reverse(逆参照)required 化は含まない(別 Action DF-P2-FRUSES-PROMOTE)。
forward_return: "fr_uses_checks に full-required summary (collect_fr_uses_full_required_summary: full-scan forward=uses先実在 を blocking_finding_count==0 で clean 判定、reverse warning は clean に算入しない) を追加 -> vg_overview.required_clean.fr_uses_checks を changed-files ratchet から full-required mode へ切替 -> automation-gate-map §3.4 に C-3a (fr_uses forward full-required, reverse は DF-P2-FRUSES-PROMOTE へ分離) を記録 -> L7 境界契約に C-3a を current_scope_authorized 追加 (forbidden_now #5 broad flip は不変、文言で forward-only/reverse 非含有を明記) -> L6↔L7 G7 pending gate evidence に帰属 (weakness-map W17/W18)."
drive: be
status: completed
status_note: "2026-06-16 完遂。Process §4.1 後続着手順③a。ユーザーが AskUserQuestion で『C-3a: detector 1件 full-required 昇格 (TL推奨)』を明示承認 (forbidden_now broad flip ではなく narrow per-detector flip)。TL design 諮問=approve/semantics A (forward-only)。完遂境界 = fr_uses forward(uses先実在) のみ full-scan required 化 (現 changed-files ratchet→full-scan)。reverse(逆参照)required 化・他 detector の flip・broad 一括 flip は禁止 (依然 forbidden_now / 別 Action)。検証=vg_overview gate overall_clean=true (fr_uses_checks={mode:full_required, clean:true, blocking:0, finding:3, warning:3}) + 全 pytest 2606 passed (1=test_pr_gate_imports_push_gate_module の concurrency flake, 単独 2/2 pass=並行 bats との pyc race で C-3a 無関係) + 全 bats 796 0-fail + contract 88 + bats mirror 57 + new fr_uses pytest 4/4。"
current_task_scope: c3a_fr_uses_forward_full_required
approval_required_before_l7_work: false  # ユーザー AskUserQuestion で C-3a 明示承認済 (narrow per-detector flip)
tl_review: approve  # design 諮問(2026-06-16)=approve/semantics A (P2=blocking-only clean 別集計必須=反映済, P1=reverse混入=scope breach→§2 Out で分離)。impl review(tl-advisor, 2026-06-16)=approve(条件なし, P0/P1/P2 なし, P3=fr_uses_checks docstring drift→反映済)。bats fresh-checkout regression (helix-doctor-json test 22: vg_overview が fr_uses_checks の新関数を import するが fresh tree に未 copy→ImportError) を全 bats が捕捉→test に fr_uses_checks.py copy 追加で修正。受入条件 1-5 全充足 → status=completed / tl_review=approve。
ticket_is_completion_evidence: false
created: 2026-06-16
owner: PM
target_l_pairs:
  - "L6↔L7 (単体): fr_uses_checks forward(uses先実在) を full-scan で required 化 (changed-files ratchet→full-required)"
  - "vg_overview: required_clean.fr_uses_checks を full-required mode へ切替 (blocking-only clean)"
design_change_class: design_or_contract_changed  # vg_overview required_clean の評価範囲切替 (ratchet→full-required) + latest_user_boundary (current_scope_authorized に C-3a 追加) の境界契約 evolution。schema/API 変更ではない。fr_uses の registry schema は片方向 uses のまま不変。再凍結 scope: L6-L7 (W18/L4-L9 は触れない)。
agent_slots:
  - role: se
    slot_label: "SE — collect_fr_uses_full_required_summary + vg_overview 配線 + pytest（Codex）"
  - role: tl-advisor
    slot_label: "TL — full-required semantics (blocking-only clean) / narrow flip 境界 / 他 detector 非波及 の adversarial check"
generates:
  - artifact_path: cli/lib/fr_uses_checks.py
    artifact_type: code
  - artifact_path: cli/lib/vg_overview.py
    artifact_type: code
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires: []
  blocks: []
related_docs:
  - docs/plans/add-feature/add-feature-2026-06-15-c2-ruff-shellcheck-advisory.md
  - docs/plans/add-feature/add-feature-2026-06-15-w1-narrow-failclose-promotion.md
  - HELIX-workflows/helix-process/automation-gate-map.md
  - cli/lib/fr_uses_checks.py
  - cli/lib/vg_overview.py
---

# Action 自動化③a: fr_uses forward(uses先実在) を full-scan required 化

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md) §4.1 後続 Forward 着手順 **③ W17/W18 ratchet を full-required**（per-detector 昇格の第1手 = **C-3a**）。
> ユーザーが AskUserQuestion（2026-06-16）で「C-3a: detector 1件 full-required 昇格 (TL推奨)」を明示承認（forbidden_now の **broad 一括 flip ではなく narrow per-detector flip** を解禁）。C-1（W1 narrow fail-close）/ C-2（ruff/shellcheck advisory）は LANDED 済（4eb9244 / 5367c2c）。

## 1. 目的 / 解く問題
Phase2 で新設した 4 ratchet detector（coding_rule_lint / dependency_cycle / plan_dependency / fr_uses）は **changed-files ratchet（新規違反のみ block）** で稼働中。full-required（全件 fail-close）化は deferred（DF-P2-*）。

TL 推奨 = **per-detector で最小債から昇格**。実測した full-scan 実債:
- coding_rule_lint: 0 だが ruff/shellcheck を含み full-required 化 = ruff/shellcheck required 化 → **C-2 advisory 境界 / forbidden_now #4 と衝突**（不適）。
- dependency_cycle: 実循環 5 件 = code refactor 要。
- plan_dependency: warning 49 件 = PLAN 大量編集。
- **fr_uses: full-scan blocking=0 / reverse warning=3。forward(uses先実在)は既に fail-close で clean。** → 最小・最安全（YAML 契約面のみ・C-2 非衝突）。

→ C-3a = **fr_uses の forward(uses先実在)判定を changed-files ratchet から full-scan required 化**する。「存在しない FR を参照できない」を全件 fail-close で保証する。

## 2. スコープ
### In（この Action でやる = semantics A）
- `cli/lib/fr_uses_checks.py` に **`collect_fr_uses_full_required_summary()`** を追加: full-scan で forward(uses先実在=blocking)を評価し、**`blocking_finding_count == 0` を clean** とする（reverse warning は clean 判定に算入しない）。`source_status` は full-scan なので changed-files availability に依存しない。既存 `collect_fr_uses_gate_summary`（ratchet）は壊さない。
- `cli/lib/vg_overview.py` の `required_clean.fr_uses_checks` を `collect_fr_uses_gate_summary`（ratchet）から **新 full-required summary** へ切替。
- pytest（TDD）: ① full-scan forward に missing-target があれば fail / ② reverse warning 3 件だけなら pass / ③ changed-files source unavailable に依存しない / ④ vg_overview.required_clean.fr_uses_checks が full-required mode で blocking 0 → clean。
- automation-gate-map §3.4 に C-3a（fr_uses forward full-required, reverse は DF-P2-FRUSES-PROMOTE へ分離）を記録。
- **L7 境界契約 evolution**: C-3a を `current_scope_authorized` に追加（文言 = 「C-3a = fr_uses forward target-existence full-scan required only。reverse required 化は含まない」）。forbidden_now 5 項目（#5 broad flip）は **不変**（narrow ≠ broad）。add-feature count 20→21 のリップル同期。

### Out（やらない = forbidden_now / 別 Action）
- **reverse(逆参照)required 化**（DF-P2-FRUSES-PROMOTE。契約 semantics 変更 = scope breach、別 Action / 再凍結。derived 算出で解消する場合も別 refactor）。
- 他 3 detector（coding_rule_lint / dependency_cycle / plan_dependency）の full-required 昇格（別 C-3b/c/d）。
- broad 一括 flip（forbidden_now #5、明示承認の別判断）。
- registry schema への `used_by` フィールド新設 / 手動 back-edge（片方向正本維持、二重正本化 = drift 回避、TL 非推奨）。

## 3. 受入条件
1. **full-required semantics A**: `collect_fr_uses_full_required_summary` が full-scan forward を blocking-only で clean 判定（reverse warning を clean に算入しない）。現状 blocking=0 で clean。
2. **vg_overview 切替**: `required_clean.fr_uses_checks` が full-required summary を source にし、changed-files unavailable override に依存しない。他 3 detector の required_clean source は不変。
3. **既存非破壊**: `collect_fr_uses_gate_summary`（ratchet）と check_fr_uses standalone の挙動は不変。
4. **境界契約整合**: C-3a が current_scope_authorized（forward-only 明記）、forbidden_now 5 項目不変、count 20→21 リップルが audit yaml + contract py + bats mirror で一貫。
5. **全テスト緑**: 全 pytest + **全 bats**（C-1 教訓: 件数 pin 含む全 bats）+ contract + `check_vg_overview --gate`（writable clean checkout で）green。

## 4. テスト計画
- fr_uses logic pytest（TDD、§2 の ①-④）。Codex se が impl と同時に追加。
- 境界契約 contract test（C-3a current_scope_authorized 追加 + count 20→21 + forbidden_now 5 不変）。
- `helix doctor check_vg_overview --gate --json` が full-required mode で overall_clean を維持（writable checkout で再実行 = TL 残リスク）。

## 5. forward_return / 収束
- forward_return: frontmatter の通り。automation-gate-map §3.4 + 境界契約 evolution → L6↔L7 G7 pending gate evidence（weakness-map W17/W18）に帰属。
- design_change_class = design_or_contract_changed（vg_overview 評価範囲切替 + boundary contract evolution）。再凍結 scope = L6-L7（W18/L4-L9 不可侵）。[forward-return-discipline](../../../HELIX-workflows/helix-process/forward-return-discipline.md) 適用。

## 6. escalation / リスク
- vg_overview required_clean の評価範囲切替（CI gate 挙動変化）だが、現状 blocking=0 で clean のため CI red にならない。auth/payment/PII/secret/schema 変更ではない。
- **リスク（TL P2）**: full-required を `check_fr_uses.clean`（reverse warning 込みで false）で実装すると A のつもりで CI red → **blocking-only clean の別集計が必須**。§2 + pytest で機械防止。
- リスク: reverse required 化を混ぜると scope breach（TL P1）→ §2 Out で明示分離、boundary 文言で forward-only 固定。

## 7. 進捗ログ
| 日付 | 内容 | 担当 |
|---|---|---|
| 2026-06-16 | Action 起票（Process §4.1 ③a）。ユーザー AskUserQuestion で C-3a 明示承認。scoping 実測（fr_uses=最小債: forward blocking 0 / reverse warning 3）。tl-advisor design 諮問=approve/semantics A（forward-only full-required、blocking-only clean 別集計必須、reverse required 化は scope breach=別 Action、境界文言で forward-only 明記）。 | PM (Opus) |
| 2026-06-16 | 実装（Codex se）: `collect_fr_uses_full_required_summary`（full-scan forward, clean=blocking_finding_count==0, reverse warning 非算入, changed-files 非依存）+ `_fr_uses_required_clean_summary` wrapper（既存 test の monkeypatch surface 維持、非 monkeypatch 時 full_required）+ vg_overview の required_clean.fr_uses_checks を full_required へ切替（他 3 detector 不変）+ new pytest 4。境界 evolution（PM）: add-feature count 20→21 を audit yaml ×6 + contract py + bats mirror で同期、deferred-feature-coverage に c3a entry（current_scope_authorized, forward-only/reverse非含有 明記）、automation-gate-map §3.4 + Process に C-3a 記録。forbidden_now 5 項目不変（narrow≠broad）。 | PM (Opus) + Codex se |
| 2026-06-16 | PM 独立検証 + TL impl review。vg_overview gate overall_clean=true（fr_uses_checks: mode=full_required, clean=true, blocking=0, finding=3, warning=3）。全 pytest 2606 passed（1=test_pr_gate_imports_push_gate_module の concurrency flake: 並行 bats の pyc compile と copytree race、単独 2/2 pass で C-3a 無関係）+ 全 bats **796 0-fail** + contract 88 + bats mirror 57 + new fr_uses 4/4。**bats fresh-checkout regression を全 bats が捕捉**: helix-doctor-json test 22（check_vg_overview --gate project-state independent）が vg_overview の `collect_fr_uses_full_required_summary` import を committed fr_uses_checks.py（未 copy）で解決できず ImportError → test に fr_uses_checks.py copy 追加で修正（C-1 教訓「全 bats を回す」が機能）。TL impl review（tl-advisor）= **approve**（条件なし、P3 docstring drift→反映済）。status=completed / tl_review=approve。次=atomic commit + gate-driven push。 | PM (Opus) |
