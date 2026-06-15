---
plan_id: add-feature-2026-06-15-w1-narrow-failclose-promotion
title: "Action(add-feature): L7 自動化① — W1 狭い fail-close 昇格 (requirement_drift / g7_subcheck standalone --gate)"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L6-functional-design/registry-detector-機能設計.md  # L6 正本: GatePolicy / DetectorReport 契約 (standalone --gate exit semantics を追補)
forward_return: "automation-gate-map §3.2 に standalone detector の --gate fail-close 契約を記録 (contract_extension; L6 registry-detector GatePolicy 状態機械の公開 exit semantics は不変 = 既存 fail_close exit を standalone CLI surface へ適用するのみ、TL 裁定で L6/L4 全面再凍結は不要) -> L7 standalone `check_requirement_drift --gate` / `check_g7_subcheck --gate` の fail-close 実装 (exit 1 on blocking findings) -> 単体実行 evidence (bats + pytest) -> L6↔L7 G7 pending gate evidence に帰属 (weakness-map W1)."
drive: be
status: completed
status_note: "2026-06-15 完遂。Process §4.1 後続着手順①（自動化先頭=W1 狭い fail-close 昇格）の個別 Action。ユーザー /goal「L7 の実装完遂」で着手。授権スコープ = 狭い flip のみ（broad flip は forbidden_now=対象外）。完遂境界 = standalone --gate subcommand 2件の fail-close + テスト固定。CI job / push_gate / vg_overview aggregate は不変。境界契約 4点同期（audit yaml ×6 + python contract + bats mirror）で新 add-feature ticket の count を反映（guard 非弱体化: forbidden_now 5 / tickets 11 / l7_work_allowed=false 維持）。"
current_task_scope: w1_narrow_failclose_standalone_subcommands
approval_required_before_l7_work: false  # 狭い flip は Process §4.1 で授権済 (broad flip のみ明示承認要)
tl_review: approve  # design 諮問(tl-advisor, 2026-06-15)=passed/条件付き推奨(P0なし) + 境界 evolution 諮問=passed + impl review(tl-advisor, 2026-06-15)=approve(P0/P1/P2なし)。P3×2: help文言追従[対応済 cli/helix-doctor:141] / generates exhaustive[progress log §8 記録]。PM 検証=pytest 2603/0・bats(json22/mirror57/contract88)・doctor --gate smoke 全exit0・product混入なし。
ticket_is_completion_evidence: false
created: 2026-06-15
owner: PM
target_l_pairs:
  - "L6↔L7 (単体): standalone detector subcommand の advisory(--gate exit0 固定)→fail-close(blocking findings で exit1) 化"
  - "automation-gate-map: standalone --gate fail-close 化を enforcement 段階に記録 (aggregate VG-overview は既配線、本 Action は standalone surface のギャップを閉じる)"
design_change_class: contract_extension  # standalone subcommand に --gate exit1 振る舞いを追加。pure_impl ではない。再凍結 scope(TL裁定/軽量): registry-detector-機能設計(GatePolicy standalone exit 契約) + 対応 L7 test design + automation-gate-map。public default / --json / aggregate exit は不変。
agent_slots:
  - role: se
    slot_label: "SE — helix-doctor standalone --gate exit 契約 + テスト実装（Codex, TDD）"
  - role: tl-advisor
    slot_label: "TL — fail-close 判定基準(blocking_clean vs clean) / 公開API exit 互換 / broad flip 不混入 の adversarial check"
generates:
  - artifact_path: cli/helix-doctor
    artifact_type: cli_extension
  - artifact_path: HELIX-workflows/helix-process/automation-gate-map.md
    artifact_type: doc_update
  - artifact_path: cli/lib/tests/test_requirement_drift.py
    artifact_type: test
  - artifact_path: cli/lib/tests/test_g7_subcheck.py
    artifact_type: test
  - artifact_path: cli/tests/helix-doctor-json.bats
    artifact_type: test
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires: []
  blocks: []
related_docs:
  - docs/plans/add-feature/add-feature-2026-06-08-detector-failclose-ci-gate.md
  - docs/v2/L1-requirements/helix-workflows-verification-strategy.md
  - HELIX-workflows/helix-process/automation-gate-map.md
---

# Action 自動化①: W1 狭い fail-close 昇格（standalone detector --gate）

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md) §4.1 後続 Forward 着手順（確定 2026-06-15）の **①自動化（先頭）= W1 狭い fail-close 昇格**。
> 先行 Action [detector-failclose-ci-gate](add-feature-2026-06-08-detector-failclose-ci-gate.md)（completed）が aggregate `check_vg_overview --gate` を fail-close + CI 配線まで完遂した。本 Action は、その aggregate に内包されつつ **standalone subcommand では未だ advisory(exit0 固定)** に残っている 2 detector surface の `--gate` 契約ギャップを閉じる。

## 1. 目的 / 解く問題

TL tl-advisor 実測（2026-06-15）で、W1 の 3 detector surface の現状は:

| surface | aggregate (`check_vg_overview --gate`) | standalone (`check_<name> --gate`) |
|---|---|---|
| vg_overview | ✅ fail-close 済（`overall_clean=false`→exit1、CI/push 配線済） | ✅ 済 |
| requirement_drift | ✅ VG-overview.required_clean 経由で fail-close 済 | ❌ **常に exit 0（advisory）** |
| g7_subcheck | ✅ VG-overview.pair_status["L6-L7"] 経由で fail-close 済 | ❌ **常に exit 0（advisory）** |

→ aggregate では既に効いているが、**standalone `helix doctor check_requirement_drift --gate` / `check_g7_subcheck --gate` を直接叩くと dirty でも exit 0** という「advisory が gate を騙る」latent ギャップが残る。これは pre-L7 gate-hardening が潰してきた「exit0 固定の vacuous gate」と同種。本 Action はこの standalone surface のギャップを閉じ、3 detector すべてが `--gate` 契約を honest に守る状態にする（defense-in-depth）。

## 2. スコープ

### In（この Action でやる）
- `cli/helix-doctor` の `check_requirement_drift --gate`: **blocking findings > 0 で exit 1**。判定は `report["blocking_clean"]` / `blocking_findings == 0`（TL P2: `clean` だと semantic/stale 等 advisory まで fail-close する → 不可）。
- `cli/helix-doctor` の `check_g7_subcheck --gate`: **missing / unanchored / exec mismatch > 0 で exit 1**。`HELIX_DOCTOR_SKIP_EXEC_TESTS=1` 環境では anchor のみで判定（TL P2: 実テスト実行を gate に混ぜない）。
- L6 `registry-detector-機能設計.md`（GatePolicy）に standalone detector の `--gate` exit 契約（blocking 判定基準）を軽量追補。
- `automation-gate-map.md` に standalone --gate fail-close 化を enforcement 段階として記録。
- テスト固定（bats + pytest、テストファースト）。

### Out（この Action でやらない = forbidden_now / 別 Action）
- **broad flip**（`forbidden_now`、明示承認 entry 要）: 他 detector の required 化 / `--strict-full-flow` 強制 / VG-overview required_clean 全体の strict 化 / W17/W18 ratchet full-required / ruff・shellcheck required / 右腕 G8/G9/G12/G14 fail-close / DB state 採用。
- **CI job 変更**: `detector-gate` は現行 `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --gate --json` のまま。standalone 2件を CI に**増やさない**（TL: aggregate を authoritative surface に保つ。standalone は直接実行/将来利用向けの契約 honest 化）。
- **push_gate 変更**: 新 gate ID 不要。`G-vg-overview` が既に 3 detector dirty を block 済（TL）。
- **default `helix doctor` / `--json` payload**: 不変（公開 API 互換）。
- ruff/shellcheck advisory（C-2 / 別 Action）、W17/W18 full-required（C-3）、右腕 execution gate（C-4 / W2）、HELIX DB（後工程）。

## 3. 設計（WHAT）

### 3.1 standalone --gate exit 契約
- `check_requirement_drift --gate`: 通常出力は不変。末尾で `blocking_findings == 0`（= `blocking_clean`）なら exit 0、`> 0` なら exit 1。advisory（semantic_label_mismatch / stale_freeze 等）は exit に影響しない。
- `check_g7_subcheck --gate`: 通常出力不変。`missing == 0 and unanchored == 0 and exec mismatch == 0` なら exit 0、いずれか `> 0` で exit 1。`HELIX_DOCTOR_SKIP_EXEC_TESTS=1` 時は exec_pass を anchor 充足で代替（CI/fresh checkout 安全）。
- `--gate` 無し（default）: 従来どおり exit 0（advisory）。`--json` payload は両モードとも不変（exit code のみ変化）。

### 3.2 broad flip 非混入の保証（forbidden_now 境界の機械固定）
- standalone 2 subcommand の exit 条件追加に限定。`check_vg_overview --gate` / CI YAML / push_gate は diff に含めない。
- regression test: default `check_*`（--gate 無し）が昇格前後で exit 0 不変。`--strict-full-flow` が CI に未混入（既存 contract test 維持）。

## 4. 受入条件
1. **standalone fail-close**: `check_requirement_drift --gate --json` が blocking dirty fixture で exit 1 / clean で exit 0。`check_g7_subcheck --gate --json` が missing/unanchored/exec-mismatch fixture で exit 1 / clean で exit 0。
2. **公開 API 非破壊**: default（--gate 無し）の exit code / stdout / `--json` payload が不変。`--gate` の `--json` payload も非破壊（exit code のみ変化）。
3. **broad 非混入**: `check_vg_overview --gate` / `detector-gate` CI job / push_gate に diff なし（standalone 2件のみ変更）。requirement_drift gate 判定が `clean` でなく `blocking_clean` であること（advisory で fail-close しない negative test）。
4. **現状 green 維持**: 現在の tree で 3 surface すべて clean → `--gate` exit 0（CI / push を即 red にしない）。
5. **fresh checkout 安全**: g7_subcheck の `--gate` は `HELIX_DOCTOR_SKIP_EXEC_TESTS=1` で project-state 非依存（過去 DF-FCCI の .helix 依存永続 red を踏まない）。
6. **既存全テスト緑**: pytest（contract / push_gate / vg_overview / g7_subcheck）+ bats 回帰が緑。fn_ut_pair_coverage / design_id_existence / VG-overview detector が引き続き clean。

## 5. テスト計画（テストファースト）
- bats `cli/tests/helix-doctor-json.bats`: ① `check_requirement_drift --gate` clean=exit0 / ② 同 --gate 無し=exit0 / ③ blocking dirty fixture で --gate=exit1 / ④ `check_g7_subcheck --gate` clean=exit0 / ⑤ --gate 無し=exit0 / ⑥ missing/unanchored fixture で --gate=exit1 / ⑦ `HELIX_DOCTOR_SKIP_EXEC_TESTS=1` で fresh checkout 相当でも --gate=exit0（project-state 非依存ガード）。
- pytest `cli/lib/tests/`: requirement_drift gate 判定が `blocking_clean`（advisory のみの report は exit0 = negative test）/ g7_subcheck gate 判定（missing/unanchored/exec mismatch）。
- **default 非破壊 snapshot**: default `check_requirement_drift` / `check_g7_subcheck` の stdout / `--json` が昇格前後で不変。
- **bats ミラー count sync**: helix-doctor-json bats の件数を Python 契約と同期（前 session の sync 漏れ G-tests BLOCK 再発防止）。

## 6. forward_return / 収束
- forward_return: frontmatter の通り。automation-gate-map §3.2 に standalone --gate fail-close 契約を記録 → L7 実装 → 単体実行 evidence → **L6↔L7 G7 pending gate evidence**（weakness-map W1）に帰属。
- design_change_class = contract_extension（pure_impl ではない）。対 design = **automation-gate-map（enforcement spec）を同時更新**。L6 registry-detector GatePolicy 状態機械（advisory→ratchet→fail_close の decide/promote）は不変＝公開 exit semantics を変えず既存 fail_close exit を standalone surface へ適用するのみ。TL 裁定（境界 evolution 諮問 2026-06-15）で L6/L4 全面再凍結は不要。再凍結 scope は軽量（default/--json/aggregate exit は不変）。[forward-return-discipline](../../../HELIX-workflows/helix-process/forward-return-discipline.md) 適用。

## 7. escalation / リスク
- exit code 契約の追加（standalone `--gate`）→ D-CONTRACT 視座。ただし default / --json / aggregate は不変、振る舞い追加は Process §4.1 で授権済の狭い flip。auth/payment/PII/secret/schema 変更ではない。
- リスク: requirement_drift gate を `clean` で判定すると advisory で fail-close → CI/push noise。受入 §3 + §5 negative test で機械防止。
- リスク: g7 gate に実テスト実行を混ぜると CI timeout/flake。`HELIX_DOCTOR_SKIP_EXEC_TESTS=1` 固定で防止。

## 8. 進捗ログ
| 日付 | 内容 | 担当 |
|---|---|---|
| 2026-06-15 | Action 起票（Process §4.1 ①自動化=W1 狭い fail-close 昇格）。先行 tl-advisor 設計諮問=passed/条件付き推奨（P0なし、P1×2=broad/strict 除外・P2×2=blocking_clean/exec-skip・P3=表示文言）。standalone 2 subcommand の --gate fail-close + テスト固定の設計確定。実装を Codex se（TDD）へ委譲予定。 | PM (Opus) |
| 2026-06-15 | **Codex se 実装着地**（cli/helix-doctor: check_g7_subcheck --gate=missing/unanchored/exec mismatch で exit1, check_requirement_drift --gate=`blocking_clean`=false で exit1。vg_overview handler/ci.yml/push_gate 不変）+ 新規テスト（pytest test_requirement_drift/test_g7_subcheck, bats helix-doctor-json 5件）。PM 独立検証で **L7 境界ガード（test_helix_l0_l14_flow_contract）抵触を検出**（add-feature plan 18→19 / handover Next Action drift=pre-existing）。 | PM (Opus) + Codex se |
| 2026-06-15 | **境界契約 evolution を TL 諮問（黙って書き換えず）= passed**: 解釈(a)§4.1 ゲート自動化シーケンス完遂（L7 product は forbidden 維持）、C-1 を `current_scope_authorized_w1_narrow_failclose_promotion` 枠（ticket 11 に混ぜない）、forbidden_now 5 保全、AskUser 不要（guard を動かさず授権作業を反映）。**境界契約 4点同期**: audit yaml ×6（add-feature 18→19 / out-of 7→8 / path_like_refs 1378→1379 / direct_file_refs 1369→1370 / boundary_context_refs 278→279, deferred-feature に C-1 追加）+ python contract test + bats mirror。handover Next Action を resync（required 4 + forbidden 5 + suppression 2 token + C-1 明記）。 | PM (Opus) + tl-advisor |
| 2026-06-15 | **PM 独立検証 全 green**: pytest 2603 passed/0 failed・bats(helix-doctor-json 22/22, contract mirror 57/57, python contract 88/88)・doctor --gate smoke 全 exit0（current tree clean=CI red なし）・product 混入なし（diff allowlist 内）・plan_lint/validator clean。**TL impl review=approve（P0/P1/P2 なし）**。P3×2: ①help 文言追従（cli/helix-doctor:141 を standalone 拡張へ更新=対応済, bats 非破壊確認）②generates exhaustiveness（境界 sync の audit yaml/mirror test は guard bookkeeping のため generates に列挙せず本 progress log で記録=非ブロッカー, TL 同意）。 | PM (Opus) + tl-advisor |
| 2026-06-15 | **gate-driven push 1回目=BLOCKED（PM 検証漏れを gate が捕捉）**: G-tests で `test-requirement-drift.bats` の pytest 件数 pin（"17 passed"）が、Codex の新規 test 2件追加で実 19 と不一致 → fail。他 7 gate（G-review/G-vg-overview 含む）は全 green。**修正**: bats を "19 passed" へ同期（g7 は count-pin bats なし・contract mirror は gate で pass 済を確認）。lesson=PM 独立検証で全 bats を回さず一部のみ実行したのが穴（gate は全 bats を回す）。修正を commit に amend し再 push。 | PM (Opus) |
