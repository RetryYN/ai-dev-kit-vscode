---
plan_id: refactor-2026-06-20-g8-anchor-wordboundary
title: "Refactor: g8_subcheck _existing_anchor_paths を word-boundary anchor match 化 (G8 IT anchor evidence の substring false-positive 防御的 hardening、DF-P2 P3 micro)"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: refactor
kind: refactor
layer: L7
process_layer: L7
parent_design: docs/v2/L6-functional-design/registry-detector-機能設計.md  # trace: g8_subcheck は FR-LIB 系 detector (G8 L5-L8 integration-test execution gate)。本 micro は anchor 判定の matching 方式 (substring→word-boundary) のみ変更し、G8 gate clean 判定 / anchored 件数 / vg public JSON schema を不変に保つ。
forward_return: "g8_subcheck._existing_anchor_paths の anchor needle 判定を substring (`needle not in text`) から word-boundary regex (`re.search(r'\\b'+re.escape(needle)+r'\\b', text)`) に置換し、G8 IT anchor evidence が将来の長い ID (例 IT-DB-030) に substring false-positive しないよう防御的に hardening する。現状 max IT-DB-05 で active collision はなく、振る舞いは G8 anchored 21/21・clean 判定・vg public schema いずれも不変 (pure_impl)。TDD で reject (substring-only 非成立) / accept (word-boundary 成立) test を追加。L5-L8 (G8) pair design の再凍結なし。L7 へ forward_return。"
drive: be
status: completed
status_note: "2026-06-20 完遂。C-4a G8 closure (7c473e0) で導入した g8_subcheck の anchor 判定が plain substring (`needle not in text`) であり、将来 IT-ID が長くなると短い needle が長い ID を誤マッチし得る latent false-positive を防御的に解消。Codex se が TDD で word-boundary regex 化 + reject/accept test 2件追加 (本体 1 行変更)。PM 検証: pytest test_g8_subcheck + test_vg_overview 22/22 pass / g8 anchored 21/21 維持 / default overall_clean=True (gate semantics 不変) / full contract pytest 88 passed / bats contract 57/57。境界 contract は landed 済 DERIVE から本 P3 タスクへ per-task retarget (PM-owned governance、product L7 不変)。TL impl review=changes_required (P0/P2/P3 なし、P1=scope 証跡不足: handover allowed_files が 2 g8 files only 明記なのに commit が境界 retarget 3 contract files も touch) → TL 推奨 option 2 (PM-owned boundary retarget + full 5-file commit scope を handover Next Action / CURRENT.json files.pending / contract test assert に記録) で解消 → TL re-review approve (over-scope でない、D-API/DB/product-CONTRACT 変更なし、governance boundary contract のみ)。"
current_task_scope: g8_anchor_wordboundary
approval_required_before_l7_work: false  # 右腕 execution-gate evidence hardening。latest_user_boundary.current_allowed_work (sequential right-arm gate closure) と right_arm_execution_work_allowed_from_handover:True の範囲内、product L7 不変。ユーザー goal「①〜③まですべて対応」(2026-06-20) で着手裁定。
tl_review: approve  # impl review (tl-advisor gpt-5.5) = changes_required (P0/P2/P3 なし、P1=scope 証跡不足) → TL 推奨 option 2 (PM-owned boundary retarget + 5-file commit scope を handover/contract に記録) で解消 → re-review approve (over-scope でない、D-API/DB/product-CONTRACT 変更なし、governance boundary contract のみ)。
ticket_is_completion_evidence: false
created: 2026-06-20
owner: PM
target_l_pairs:
  - "L7 (refactor): g8_subcheck _existing_anchor_paths の anchor matching を substring→word-boundary 化 (G8 IT anchor evidence の reliability hardening、G8 gate 判定不変)"
design_change_class: pure_impl  # G8 gate clean 判定 / anchored 件数 / vg public JSON schema いずれも不変。anchor matching を substring から word-boundary に正す detector 内部 hardening。L5-L8 (G8) pair design 変更なし、再凍結 scope なし。
agent_slots:
  - role: se
    slot_label: "SE — _existing_anchor_paths を word-boundary regex 化 + reject/accept TDD test（Codex、完了）"
  - role: tl-advisor
    slot_label: "TL — anchor regex が現行 21 IT anchor を壊さないか / re.escape 妥当性 / TDD 非 vacuous / 境界 retarget over-scope でないか の adversarial check（完了: changes_required→option2→re-review approve）"
generates:
  - artifact_path: cli/lib/g8_subcheck.py
    artifact_type: code
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires:
    - docs/plans/add-feature/add-feature-2026-06-19-g8-integration-execution-gate.md
  blocks: []
related_docs:
  - docs/plans/process/process-2026-06-08-verification-forward-gate.md
  - docs/plans/refactor/refactor-2026-06-20-deferred-count-derive.md
  - cli/lib/g8_subcheck.py
---

# Refactor: g8_subcheck _existing_anchor_paths を word-boundary anchor match 化 (DF-P2 P3 micro)

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md)。C-4a G8 closure ([7c473e0](#)) の follow-up micro。[DERIVE refactor](refactor-2026-06-20-deferred-count-derive.md) §59 が「P3 (g8_subcheck `_existing_anchor_paths` word-boundary 化) は別 micro commit」と先行宣言済み。ユーザー goal「①〜③まですべて対応」(2026-06-20) の ① に相当。

## 1. 目的 / 解く問題
G8 (L5-L8 integration-test execution gate) の detector `g8_subcheck` は、`G8_ANCHOR_MAP` の `path::IT-ID` spec に対し test file 本文に needle (IT-ID) が存在するかで anchor 成立を判定する。判定が plain substring (`needle not in text`) のため、将来 IT-ID が長くなった場合に短い needle が長い ID を誤マッチする latent false-positive がある (例: needle `IT-DB-03` が `IT-DB-030` を含有判定)。現状 max は `IT-DB-05` で active collision はないが、anchor evidence の信頼性を将来に渡って担保するための防御的 hardening。

## 2. スコープ
### In
- `cli/lib/g8_subcheck.py` `_existing_anchor_paths`: anchor needle 判定を `if needle not in text:` から word-boundary 判定 `if re.search(r"\b" + re.escape(needle) + r"\b", text) is None:` へ置換 (`re` は既存 import)。`re.escape` で `-` を含む ID を literal 化。末尾が word 文字に続く長い ID には非マッチ、空白/改行/`|`/行末が続く単独 ID にはマッチ。
- `cli/lib/tests/test_g8_subcheck.py`: TDD で 2 test 追加 — `_rejects_substring_only_match` (`IT-DB-030` のみの fixture に needle `IT-DB-03` が不成立 = 空 list) / `_accepts_word_boundary_match` (`IT-DB-03 |` fixture で成立)。

### Out (不変)
- **G8 gate 判定 (clean = anchored==it_total ∧ missing0 ∧ unanchored0 ∧ exec_pass==anchored)・anchored 件数 (21/21)・vg_overview の L5-L8 applicable flip・vg public JSON schema は不変** (pure_impl)。
- L5-L8 (G8) pair design・L5 結合テスト設計 doc の再凍結なし。
- `G8_ANCHOR_MAP` の 27 spec / 21 IT 内容は不変。

### 付随 (PM-owned governance、別責務だが同一 commit)
- 境界 contract per-task retarget: landed 済 DERIVE から本 P3 タスクへ handover boundary を移す。`docs/v2/audit/2026-06-12-full-objective-gap-status.yaml` (`required_current_user_boundary_contains` tokens) + `cli/lib/tests/test_helix_l0_l14_flow_contract.py` + `cli/tests/test-helix-l0-l14-flow-contract.bats` (tokens / task.title pin / files.pending pin) を P3 値へ。`.helix/handover/CURRENT.md` / `CURRENT.json` を `helix handover dump` で P3 へ再生成 (5-file commit scope を明示)。forbidden product-L7 / `product_l7_work_allowed_from_handover:False` / `current_allowed_work` (sequential right-arm gate closure) は不変。

## 3. 検証
- `python3 -m pytest cli/lib/tests/test_g8_subcheck.py cli/lib/tests/test_vg_overview.py -q` → 22/22 pass。
- g8 live: anchored 21/21, missing 0, unanchored 0 (回帰なし)。
- `collect_vg_overview(strict_full_flow=False)` overall_clean=True (gate semantics 不変)。
- `python3 -m pytest cli/lib/tests/test_helix_l0_l14_flow_contract.py -q` → 88 passed (境界 retarget 整合)。
- `bats cli/tests/test-helix-l0-l14-flow-contract.bats` → 57/57 pass。

## 4. TL review
- impl review (tl-advisor, gpt-5.5): verdict=changes_required。P0/P2/P3 なし (code 妥当、21 anchor 無破壊、regex 境界挙動・re.escape 正、TDD 非 vacuous)。P1 [Blocking]=scope 証跡不足。
- 解消: TL 推奨 option 2 (PM-owned boundary retarget + 5-file commit scope を handover Next Action / CURRENT.json files.pending / contract assert に記録)。
- re-review (tl-advisor, gpt-5.5): **verdict=approve**。over-scope でない、D-API/DB/product-CONTRACT 変更なし、governance boundary contract のみ、git diff = 5 authorized files。

## 5. forward_return
pure_impl の detector hardening。G8 gate semantics 不変ゆえ L5-L8 pair design の再凍結なし。L7 へ forward_return し、HELIX DB trace (FR-LIB g8_subcheck) の管理下を維持。次は ② G9 (L4-L9 system-test execution gate) closure。
