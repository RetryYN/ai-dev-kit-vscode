---
plan_id: add-feature-2026-06-14-pre-l7-gate-hardening
title: "Action(add-feature): L7 着手前ゲート硬化 — FN↔UT pair coverage + design_id 実在 + L7 worklist checker + DDD ratchet"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L6-functional-design/registry-detector-機能設計.md  # L6 正本: DetectorReport / GatePolicy 契約。新 detector はこの契約に従う
forward_return: "L6↔L7 pair_closure の test_design 層 (機能設計 FN ↔ 単体テスト設計 UT の 1:1) を機能一覧で機械的に閉じ、design_id 実在・L7 worklist 網羅を fail-close で保証する。pair_closure = design + test_design(本 Action) + test_code_anchor(g7_subcheck 既存) + test_execution_pass(既存) + trace_symmetry + semantic_gate。L6↔L7 G6/G7 pending gate evidence に帰属し、VG-overview required_clean 経由で G-vg-overview に接続する。"
drive: be
status: completed
current_task_scope: pre_l7_gate_hardening
approval_required_before_l7_feature_impl: true  # 569 機能の feature 実装は引き続き PARKED。本 Action は L7 を GUARD するゲート硬化のみ (ユーザー明示指示 2026-06-14「L7 に行く前に弱点を徹底的に潰す」)
user_unpark_decision: "A (2026-06-14 followup /goal): pre-L7 ゲート硬化の fail-close + detector 自己被覆 L7 test-design + gate-hardening detector unit test を unpark 承認。L7 product feature 実装 / CI 配線 / DB schema / broad W1 fail-close flip は引き続き PARKED。前 session 設置の機械境界ガード (test_helix_l0_l14_flow_contract.py) は本承認で正当に更新する。"
tl_review: approve  # 設計諮問=changes_required→反映。境界衝突諮問=overstep判定→ユーザー裁定A(unpark)取得。impl review=changes_required(P1=fn_ut_pair が L7 test-design doc inventory 未検査/P2=design_id_existence 任意出現)→Codex se TDD で修正(ut_not_in_l7_design finding 追加/構造限定)→**re-review approve(P0/P1/P2なし、P3軽微)**。PM 独立検証: pytest 2565 passed/bats 774/doctor --gate 32-0/vg overall_clean=true g7 93/93
created: 2026-06-14
owner: PM
target_l_pairs:
  - "L6↔L7 (単体): 機能設計 FN ↔ 単体テスト設計 UT の 1:1 を機能一覧 (functional-registry.yaml) に表現し網羅検査する = 機能設計↔単体テスト対を機械で閉じる"
  - "L6↔L7: design_id (FN-*) が L6 設計 doc に実在するかを fail-close 検査する"
  - "automation-gate-map: 新 detector を VG-overview required_clean に接続 = 新 gate ID を作らず既存 G-vg-overview を硬化"
design_change_class: contract_extension  # 新 field (test_design_ids) + 新 detector (fn_ut_pair_coverage) + DDD check の fail-close 昇格。pure_impl ではない。再凍結 scope: registry-detector-機能設計(DetectorReport/GatePolicy) + functional-registry schema(L3 doc) + 新 detector の L6 機能設計/L7 単体テスト設計 + ddd-registry 設計 + automation-gate-map
agent_slots:
  - role: se
    slot_label: "SE — detector / registry field / vg_overview 配線 / テスト実装 (Codex、TDD テスト先行)"
  - role: tl-advisor
    slot_label: "TL — 設計諮問 (済) + impl review (公開API/exit 契約 / fail-close 安全性 / 再凍結 scope の adversarial check)"
generates:
  - artifact_path: cli/lib/fn_ut_pair_coverage_checks.py
    artifact_type: python_module
  - artifact_path: cli/lib/vg_overview.py
    artifact_type: python_module
  - artifact_path: cli/config/functional-registry.yaml
    artifact_type: yaml_config
  - artifact_path: docs/v2/L6-functional-design/registry-detector-機能設計.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/automation-gate-map.md
    artifact_type: doc_update
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires: []
  blocks:
    - docs/plans/add-feature/add-feature-2026-06-14-pre-l7-gate-hardening-phase2.md
related_docs:
  - docs/plans/process/process-2026-06-08-verification-forward-gate.md
  - docs/v2/L1-requirements/helix-workflows-verification-strategy.md
  - HELIX-workflows/helix-process/automation-gate-map.md
  - HELIX-workflows/helix-process/forward-return-discipline.md
  - cli/lib/vg_overview.py
  - cli/lib/g7_subcheck.py
  - cli/config/functional-registry.yaml
---

# L7 着手前ゲート硬化 — Action

> ユーザー指示 (2026-06-14)「TDD と DDD の弱手を是正する。L7 工程表 / 機能一覧対応 / PLAN 起票 / 実装漏れ是正の仕組みを確認し弱点があれば是正。L7 に行く前に弱点を徹底的に潰す」を受けた、L7 を GUARD する検証ゲートの硬化 Action。検証ゲート Process ([process-2026-06-08-verification-forward-gate](../process/process-2026-06-08-verification-forward-gate.md)) の `pair_closure.test_design` 層の閉合に当たる。**569 機能の feature 実装は引き続き PARKED**。

## 1. 背景 / 弱点の実測 (調査済み・実コード確認)

L7 着手前に、機能一覧 → 工程表 → PLAN 起票 → 実装漏れ検出 の pipeline と TDD/DDD 強制の弱点を実コードで監査した。

| # | 弱点 | 実測 | 強制レベル |
|---|---|---|---|
| T1 | L6↔L7 ペアの核心「機能設計 FN ↔ 単体テスト UT 1:1」が機能一覧に**表現されていない** | L6_required 68 entry 全てに `design_ids`(FN-*) はあるが `test_design_ids`(UT-*) は 0 | 機械なし |
| T2 | FN→UT 網羅性 detector が**不在** | anchor map UT 88 ↔ registry FN 88 の対応を検査するコードなし。FN に対応する UT が欠けても素通り | 機械なし |
| W4 | `design_id`(FN-*) が L6 設計 doc に**実在するか未検査** | prefix 整合のみ。実 section 存在は別問題 | 機械なし |
| W1 | 機能一覧由来の「L7 で何を実装すべきか」worklist が**不在** | `design_sprint_entries` テーブル rows=0、sprint は registry 非参照 | 機械なし |
| D1 | DDD 3 check が **warn-only** (push を止めない) | doctor で WARN++、push gate 非搭載。bc_anti_corruption / bc_mode_coverage は findings=0 (clean) | warn-only |
| D2 | concept.md ↔ ddd-registry の **row mismatch** | §12.1 Glossary=20行 vs registry 19語、§14.1 BC=11行 vs registry 10件。glossary は別途 7 P3 implementation_gap | warn-only (素通り) |

over-build と判定し**やらない** (TL 諮問、deferred finding として §6 に記録): T3 (test-first 時系列強制) / D3 (用語 grep scan) / W3 (PLAN 自動起票・DB 拡張)。右腕 G8/G9/G12/G14 は別 PLAN。

## 2. work items (TDD: テスト先行)

### WI-1 (P0 = T1+T2): FN↔UT pair coverage
- `functional-registry.yaml` の L6_required entry に **新 field `test_design_ids`** (UT-*) を追加。`design_ids` は FN 専用に保つ (registry_design_coverage の責務を濁さない)。命名規約 `FN-XXX-NN ↔ UT-XXX-NN` を anchor map / L7 test-design doc で検証して populate。
- 新 detector `cli/lib/fn_ut_pair_coverage_checks.py`: 「registry FN set」「registry UT set (test_design_ids)」「L7 test-design doc UT set」「g7-test-anchor-map UT set」を突合し `missing_ut` / `orphan_ut` / `unanchored_ut` / `duplicate` を検出。
- `vg_overview.py` の `required_clean` に `fn_ut_pair_coverage` を追加 → `overall_clean` → G-vg-overview で fail-close (新 gate ID 不要)。
- **既知の L7 実装債 (FN はあるが UT 未実装) は `approved_deferred` waiver として明示記録** (右腕 pair と同じ扱い)。gate は「構造破綻 (orphan/duplicate/unanchored) なし」+「新規 unwaived missing なし」で fail-close。= 既存債で red-block せず、**新規デグレ (UT 無し FN 追加 / リンク破壊) を止める**。

### WI-2 (P0 = W4): design_id 実 doc 実在検査
- L6_required の `design_ids`(FN-*) が L6 設計 doc に section として実在するかを検査 (`registry_design_coverage_checks.py` 厳格化 or 薄い resolver)。L6_required のみ fail-close、L4/L5 成果物実在は P1 (deferred)。

### WI-3 (P0-light = W1): registry 由来 L7 worklist checker
- `functional-registry.yaml` から L7 worklist (= L6_required で UT 未 anchor の FN 一覧) を**決定論的に生成・比較する read-only checker**。**DB 拡張・PLAN 自動起票はしない**。これが「機能一覧に対応する工程表」の実体 = registry が SSoT、worklist は派生ビュー。

### WI-4 (P1 = D1+D2): DDD ratchet
- D2: concept.md §12.1/§14.1 と ddd-registry の row mismatch を解消 (data fix)。
- D1: clean かつ低 FP の `bc_anti_corruption` / `bc_mode_coverage` のみ fail-close 昇格 (automation-gate-map)。`glossary_coverage` は findings 解消後 (deferred)。

### WI-5: 新 detector の自己登録 (dogfooding closure)
- 新 detector (`fn_ut_pair_coverage_checks.py` 等) を `functional-registry.yaml` に FR エントリ登録 + FN-* (L6 機能設計) + UT-* (L7 単体テスト設計) + anchor 登録。= 自分が作る検出器も機能一覧に閉じる (FR-LIB-148/UT-RDC-01 の前例に倣う)。

## 3. 受入条件 (合格基準・先に固定)

- WI-1: `fn_ut_pair_coverage` detector の pytest が**先に赤** (missing FN / orphan UT / unanchored UT / duplicate の fixture) → 実装で緑。`test_design_ids` populate 後、`helix doctor check_vg_overview --json` で `required_clean.fn_ut_pair_coverage.clean=true` (既存債は waiver 計上)。
- WI-2: design_id 実在 detector の pytest 赤→緑。L6_required FN の実 doc section 不在を検出。
- WI-3: worklist checker の pytest 赤→緑。registry から決定論生成、手動 worklist との diff 検出。
- WI-4: row mismatch 解消後 `glossary_coverage` の count finding 消滅。bc 2 check fail-close 昇格後も doctor `--gate` exit 0 (clean のため)。
- 全体: `python3 -m pytest cli/lib/tests/ -q` green / `cli/helix test --no-pytest --bats-only` green / `helix doctor --gate` fail=0 / VG-overview `overall_clean=true` 維持 (既存 88/88 退化なし) / plan lint PASS。

## 4. forward_return / 再凍結 scope (forward-return-discipline 適用)

`design_change_class=contract_extension` のため pure_impl ではなく、対の設計層を再凍結する:
- `docs/v2/L6-functional-design/registry-detector-機能設計.md` (DetectorReport/GatePolicy に新 detector を追記)
- `functional-registry.yaml` schema (新 field `test_design_ids` の意味定義 → L3 `helix-workflows-functional-registry.md` に追記)
- 新 detector の L6 機能設計 (FN-*) + L7 単体テスト設計 (UT-*)
- `ddd-registry` 設計 (D1 昇格の根拠) + `automation-gate-map.md` (fail-close 配線の正本)

戻し先 = L6↔L7 G6/G7 pending gate evidence。VG-overview required_clean で機械的に観測可能になった時点で closure。

## 5. 進捗

| 日付 | 内容 | 担当 |
|---|---|---|
| 2026-06-14 | 弱点監査 (実コード) + TL 設計諮問 (changes_required: P0=T1/T2/W4/W1-light, P1=D1/D2, over-build=T3/D3/W3) + 本 Action PLAN 起票 | PM (Opus) + TL |
| 2026-06-14 | WI-1 (fn_ut_pair_coverage + test_design_ids + VG-overview 接続 + 自己登録) / WI-2 (design_id_existence fail-close) / WI-3 (l7_worklist read-only) / WI-4 (DDD bc-2-check fail-close) を Codex se TDD 実装。PM 独立検証 (gaming でないこと確認、回帰 green)。設計 re-freeze (L6 §3.2 / L3 §1.7 / WSC docs FN-WSC-219..223↔UT-WSC-219..223 / automation-gate-map / verification-strategy)。vg_overview overall_clean=true, g7 88→93 整合。 | PM (Opus) + Codex se |
| 2026-06-14 | **境界衝突検出**: full pytest で test_helix_l0_l14_flow_contract.py 3件 fail。前 session 設置の機械境界ガードが『create L7 test-design artifacts / unit-test implementation / promote fail-close gates』を禁止しており、本作業が該当。**TL 諮問 = overstep 判定 (中間路ありだが要ユーザー裁定)** → **ユーザー裁定 A (unpark 承認)**。契約 (test + audit yaml 8件) + handover を『新承認による pre-L7 ゲート硬化 unpark』へ正当更新 (L7 product/CI/DB/broad-W1-flip は PARKED 維持、still-PARKED 6項目を forbidden に保持)。bats ミラー (test-helix-l0-l14-flow-contract.bats / helix-doctor-json.bats g7 88→93) も同期。 | PM (Opus) + Codex se + TL + User |
| 2026-06-14 | **TL impl review = changes_required** (P0なし / P1=fn_ut_pair が anchor map のみ見て L7 test-design doc inventory 未検査=gaming vector / P2=design_id_existence が任意出現で通る) → Codex se TDD 修正 (P1: load_ut_inventory で L7 doc inventory 突合 + ut_not_in_l7_design finding / P2: heading・table row 構造限定) → **re-review approve (P0/P1/P2なし、P3軽微)**。**最終検証 green**: full pytest 2565 passed/0 failed、full bats 774/0、doctor --gate 32 pass/0 fail/104 warn、vg_overview overall_clean=true g7 93/93。**完了**。 | PM (Opus) + Codex se + TL |

## 6. deferred finding (floating debt 化させない = §0 絶対原則)

- **DF-PREL7-T3**: test-first 時系列の機械強制。Git 履歴・生成時刻依存で費用対効果低 (TL P2)。→ L7 実装手順 + review evidence で扱う。帰属 = L6↔L7 G7 (手順規律)。
- **DF-PREL7-D3**: Forward 正本 doc への他 context 固有用語の未変換混入の grep scan。FP 高い (TL P2)。→ semantic / doc-review ratchet から将来着手。帰属 = DDD anti-corruption。
- **DF-PREL7-W3**: 機能一覧 → PLAN 自動起票・`design_sprint_entries` DB 活用。「観測前 DB 拡張禁止」と衝突 (TL over-build)。→ 手動 PLAN + WI-3 worklist checker で正当化。永続化要求が観測されてから schema 確定。
- **DF-PREL7-W4B**: L4/L5 成果物実在検査。P0 は L6_required FN のみ。→ 右腕 pair 検証と合わせて P1。
- **DF-PREL7-D1B**: `glossary_coverage` の fail-close 昇格。7 P3 implementation_gap (gate/balance_ratio/NSM/guardrail/trace/drift/ADR) 解消後。
- 右腕 G8/G9/G12/G14 execution gate: 別 PLAN (L7 後)。
