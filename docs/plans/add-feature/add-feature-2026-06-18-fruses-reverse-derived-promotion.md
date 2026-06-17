---
plan_id: add-feature-2026-06-18-fruses-reverse-derived-promotion
title: "Action(add-feature): L7 自動化③b — fr_uses reverse(逆参照) を forward edges からの derived index 化 + full-required (DF-P2-FRUSES-PROMOTE)"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L6-functional-design/registry-detector-機能設計.md  # trace: fr_uses_checks (FR-LIB-159/FN-WSC-228) の L6 設計。本 Action は reverse(逆参照)判定を「対向 entry も uses で書き戻す手書き双方向要求」から「forward uses edges からの derived used_by index」へ契約 evolve し、reverse を full-required へ昇格。forward(uses先実在) full-required は C-3a で LANDED 済。
forward_return: "fr_uses_checks の reverse 判定を derived index 化 (used_by を forward uses edges から算出、手書き対向 uses を要求しない) -> missing_reverse_reference(手書き欠落) finding kind を撤廃し reverse_reference_drift(手書き used_by が derived と矛盾した時のみ fire) へ置換 -> collect_fr_uses_full_required_summary を forward+reverse(derived consistency) の blocking-only clean に拡張 -> vg_overview.required_clean.fr_uses_checks の reverse warning 3 件 (FR-LIB-156/157/158 -> FR-LIB-155) が derived で解消 -> automation-gate-map §3.4 に C-3b (fr_uses reverse derived full-required) を記録 -> L7 境界契約に C-3b を current_scope_authorized 追加 (forbidden_now broad flip は不変) -> L6↔L7 G7 pending gate evidence に帰属 (weakness-map W17/W18, DF-P2-FRUSES-PROMOTE close)."
drive: be
status: completed
status_note: "2026-06-18 完遂。Process §4.1 後続着手順③ (W17/W18 ratchet full-required) の per-detector 第2手 = C-3b。ユーザーが AskUserQuestion (2026-06-18) で『右腕 + 残 detector を順に全部』を選択し、当該 scope の forbidden_now を解禁承認。C-3a (fr_uses forward full-required, 09e2b19) の Out に分離されていた DF-P2-FRUSES-PROMOTE を本 Action で close。完遂境界 = fr_uses reverse を derived index 化し full-required 昇格まで。tl-advisor design+PLAN review=approve(条件付き P2/P3 反映)、impl review=approve(P0/P1/P2 なし)。検証=pytest targeted 109 + full 2610 pass + check_fr_uses clean(reverse warning 3→0) + check_vg_overview overall_clean=true(fr_uses full_required warning0) + count 21→22 全 pin 実数22一致 + ドリフト対策 A/B 機能。full pytest で発見した既存 date-rot(test_feedback_loop_snapshot、C-3b 無関係)はユーザー裁定で別 Incident commit に最小修正(PM 直接=Codex API 404 障害)。次=2 commit + gate-driven push。"
current_task_scope: fruses_reverse_derived_promotion
approval_required_before_l7_work: false  # ユーザー AskUserQuestion (2026-06-18) で「右腕+残detectorを順に全部」scope を明示承認
tl_review: approve
ticket_is_completion_evidence: false
created: 2026-06-18
owner: PM
target_l_pairs:
  - "L6↔L7 (単体): fr_uses_checks reverse(逆参照)を derived index 化 (forward uses edges から used_by 算出) + full-required"
  - "vg_overview: required_clean.fr_uses_checks の reverse 次元を derived consistency の blocking-only clean に拡張"
design_change_class: design_or_contract_changed  # finding kind の契約 evolution (missing_reverse_reference 撤廃 -> reverse_reference_drift) + reverse index の derived 化 + vg_overview required_clean reverse 次元拡張。registry schema は片方向 uses が SSoT のまま (used_by は派生であり手書き必須フィールドにしない)。再凍結 scope: L6-L7 (W18/L4-L9 は触れない)。
agent_slots:
  - role: se
    slot_label: "SE — derived used_by index + reverse_reference_drift + full_required summary 拡張 + vg_overview 配線 + pytest（Codex）"
  - role: tl-advisor
    slot_label: "TL — derived reverse semantics / missing_reverse_reference 撤廃の契約妥当性 / 片方向正本維持 / full-required 境界 の adversarial check"
generates:
  - artifact_path: cli/lib/fr_uses_checks.py
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
  - HELIX-workflows/helix-process/automation-gate-map.md
  - cli/lib/fr_uses_checks.py
  - cli/lib/vg_overview.py
---

# Action 自動化③b: fr_uses reverse(逆参照) を derived index 化 + full-required (DF-P2-FRUSES-PROMOTE close)

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md) §4.1 後続 Forward 着手順 **③ W17/W18 ratchet を full-required**（per-detector 昇格の第2手 = **C-3b**）。
> ユーザーが AskUserQuestion（2026-06-18）で「右腕 + 残 detector を順に全部」を選択し、当該 scope の forbidden_now を解禁承認。C-3a（fr_uses forward full-required, `09e2b19`）の §2 Out に分離されていた **DF-P2-FRUSES-PROMOTE** を本 Action で close。

## 1. 目的 / 解く問題
C-3a で fr_uses の **forward（uses 先実在）** は full-scan full-required 化済。残る **reverse（逆参照）** は依然 advisory warning（現 3 件: FR-LIB-156/157/158 が FR-LIB-155 を uses するが、FR-LIB-155 側に逆参照が無い）。

現 `missing_reverse_reference` 判定（[fr_uses_checks.py:102](../../../cli/lib/fr_uses_checks.py)）は **「対向 entry も `uses` で書き戻す」手書き双方向**を要求している。これは TL 指摘の **「手書き双方向正本」= 片方向正本（forward uses）と衝突**するアンチパターン。remediation text 自身も「derived warning として解消計画を持つ」と既に予告している。

→ C-3b = **reverse を forward uses edges からの derived index（used_by）に置換**し、手書き対向 uses を要求しない。これにより 3 warning は「派生で常に充足」となり解消し、reverse 次元を full-required へ昇格できる。

## 2. スコープ
### In（この Action でやる）
- `cli/lib/fr_uses_checks.py`:
  - **derived used_by index 算出**: 全 entry の forward `uses` edges から `used_by_map[target] = {entry | target ∈ uses(entry)}` を計算する純関数を追加（例 `build_reverse_index()` / `collect_fr_uses_reverse_index()`）。これが reverse の SSoT 投影であり、registry に手書き `used_by` を要求しない。
  - **finding kind 契約 evolution**: `missing_reverse_reference`（手書き欠落で fire）を**撤廃**し、`reverse_reference_drift`（registry に**手書き** `used_by` が存在し、それが derived index と矛盾した場合のみ fire）へ置換する。手書き `used_by` が無い現状（= 通常運用）では reverse は derived で常に clean。
  - **full_required summary 拡張**: `collect_fr_uses_full_required_summary()` を forward（uses 先実在 = blocking）に加え reverse（derived consistency = blocking、drift があれば fire）を含めた blocking-only clean に拡張。`clean = blocking_finding_count == 0`。
- `cli/lib/vg_overview.py`: `required_clean.fr_uses_checks` は full_required summary を source に維持（C-3a の配線）。reverse 次元が derived で clean になることで warning 3 → 0。他 detector の required_clean source は不変。
- pytest（TDD）: ① 手書き対向 uses が無くても reverse が derived で clean（現 3 warning 消滅）/ ② 手書き `used_by` が derived と一致 → clean / ③ 手書き `used_by` が derived と矛盾 → `reverse_reference_drift` blocking fire / ④ forward missing-target は従来どおり blocking / ⑤ vg_overview.required_clean.fr_uses_checks が full_required で blocking 0 → clean、warning_count 0。
- automation-gate-map §3.4 に C-3b（fr_uses reverse derived full-required, DF-P2-FRUSES-PROMOTE close）を記録。
- **L7 境界契約 evolution**: C-3b を `current_scope_authorized` に追加。forbidden_now（broad flip）は **不変**。add-feature count 21→22 のリップル同期（audit yaml ×6 + contract py + bats mirror、C-3a `09e2b19` diff を正本テンプレートに +1）。
- **ドリフト対策（ユーザー指示 2026-06-18、§8 正本）**: (A) derived-reverse SSoT 単一化 + drift finding、(B) 境界 count 多点一貫性 drift テスト新設。詳細は §8。

### Out（やらない = forbidden_now / 別 Action）
- 他 3 detector（coding_rule_lint / dependency_cycle / plan_dependency）の full-required 昇格（C-2 advisory 境界遵守、別 Action）。
- broad 一括 flip（forbidden_now、明示承認の別判断）。
- registry schema に手書き `used_by` を**必須フィールド化**する変更（片方向 uses を SSoT 維持。used_by は派生 = 二重正本化 / drift 回避、TL 非推奨）。
- 右腕 G8-G14（別 Action 群、左腕再凍結先行）。

## 3. 受入条件
1. **derived reverse**: reverse index が forward uses edges から算出され、手書き対向 uses を要求しない。現 3 warning（FR-LIB-156/157/158 → FR-LIB-155）が derived で解消（finding 0）。
2. **契約 evolution**: `missing_reverse_reference` 撤廃、`reverse_reference_drift`（手書き used_by ⊕ derived 矛盾時のみ）導入。手書き used_by 無し時は clean。
3. **full-required semantics**: `collect_fr_uses_full_required_summary` が forward + reverse(derived) を blocking-only で clean 判定。
4. **既存非破壊**: forward（uses 先実在）judgement と `collect_fr_uses_gate_summary`（ratchet）の挙動は不変。check_fr_uses standalone は新 kind を反映しつつ exit 挙動互換。
5. **境界契約整合**: C-3b が current_scope_authorized、forbidden_now 不変、count 21→22 リップルが audit yaml + contract py + bats mirror で一貫。
6. **全テスト緑**: 全 pytest + **全 bats**（C-1 教訓: 件数 pin 含む全 bats、fresh-checkout regression に注意）+ contract + `check_vg_overview --gate`（writable clean checkout で）green。overall_clean=true、fr_uses_checks warning_count=0。
7. **ドリフト対策成立（§8）**: (A) reverse は forward `uses` のみを SSoT とし、手書き used_by が混入したら `reverse_reference_drift` が blocking で fire（テストで証明）。(B) 境界 count 多点一貫性 drift テストが新設され、audit yaml ×6 + contract py + bats mirror のいずれか1点でも count がずれたら fail する（意図的ズレを注入したテストで証明）。

## 4. テスト計画
- fr_uses reverse derived pytest（TDD、§2 の ①-⑤）。Codex se が impl と同時に追加。
- 境界契約 contract test（C-3b current_scope_authorized 追加 + count 21→22 + forbidden_now 不変）。
- `helix doctor check_vg_overview --gate --json` が full-required mode で overall_clean=true 維持（writable checkout で再実行）。
- **fresh-checkout regression**: C-3a 教訓 — fr_uses_checks.py / vg_overview.py に跨る impl は fresh tree(committed) で全 import 解決できるよう、helix-doctor-json bats の copy 対象を確認。

## 5. forward_return / 収束
- forward_return: frontmatter の通り。automation-gate-map §3.4 + 境界契約 evolution → L6↔L7 G7 pending gate evidence（weakness-map W17/W18、DF-P2-FRUSES-PROMOTE close）に帰属。
- design_change_class = design_or_contract_changed（finding kind 契約 evolution + reverse derived 化 + vg_overview reverse 次元拡張）。再凍結 scope = L6-L7（W18/L4-L9 不可侵）。[forward-return-discipline](../../../HELIX-workflows/helix-process/forward-return-discipline.md) 適用。

## 6.1 TL review 反映条件（tl-advisor 2026-06-18 = approve 条件付き）
実装が満たすべき条件（P0/P1 なし、全て impl レベル）:
- **P2-1**: `reverse_reference_drift` は registry に `used_by` フィールドが**存在する時のみ**比較する。欠落 = clean。存在して derived と集合不一致 = blocking。`used_by: []` 明示 ⊕ derived 非空 = drift。
- **P2-2**: count drift テストは本 Action 同梱で可（count を +1 する同一変更で guard を入れるのが最小リスク）。ただし pin 箇所は audit yaml だけでなく **Python contract mirror / Bats mirror / reference integrity count** にも波及（`09e2b19` 実測）。`09e2b19` diff をテンプレートに pin 箇所を**機械的に網羅列挙**してからテスト化する。
- **P2-3**: full-required summary の clean = `blocking_finding_count == 0`。blocking に入れるのは `missing_uses_target` と `reverse_reference_drift` のみ（reverse warning は clean に算入しない＝C-3a 整合）。現 registry に `used_by` 0 件 → reverse warning 0 化 + blocking 0 で CI red にならない。
- **P3**: 既存テストは `warning_count == 3` / `missing_reverse_reference` を pin（`test_fr_uses_full_required.py` / `test_fr_uses_checks.py` / `test_vg_overview.py` / `helix-doctor-json.bats`）。これらと fresh-checkout copy 対象を更新する。

## 6. escalation / リスク
- vg_overview required_clean の reverse 次元拡張（CI gate 挙動変化）だが、derived 化で reverse warning は 0 になり、手書き used_by が無い現状では blocking も 0 → CI red にならない。auth/payment/PII/secret/schema 変更ではない。
- **リスク（要 TL 確認）**: finding kind の撤廃（`missing_reverse_reference`）は既存 pytest/bats で件数 pin している箇所を破る可能性 → 全 bats を回す（C-1 教訓）。新 kind `reverse_reference_drift` の発火条件を「手書き used_by が存在し derived と矛盾」に厳格化しないと、derived index 自身を「矛盾」と誤検出して CI red。
- リスク: derived used_by を registry へ書き戻す実装にすると片方向正本が崩れる（二重正本化）→ あくまで算出 projection に留める。
- リスク: count 21→22 リップルの 4 点同期漏れ（bats mirror 追従漏れ）で G-tests BLOCK（過去頻発）→ C-3a `09e2b19` の git diff から pinned 値を網羅抽出して同期。

## 8. ドリフト対策（ユーザー指示 2026-06-18「ドリフトする可能性がありそうだからドリフト対策しておいて」）

本 Action は派生 index と多点 count 同期という、2 種のドリフト源を新たに触る。**ドリフトを prose 規律でなく機械不変条件で閉じる**（HELIX Core §4 自動検出ループ / §0 「原則を文章でなく仕組みで守らせる」）。

### (A) derived-reverse SSoT ドリフト（forward `uses` ↔ reverse `used_by`）
- **構造的防止**: reverse index は forward `uses` edges から**算出のみ**（registry へ書き戻さない）。現状 registry に手書き `used_by` フィールドは存在しない（実測 2026-06-18）ため、SSoT は forward `uses` 一本で、競合源が無く drift は構造的に発生しない。
- **回帰防止 guard**: 将来 registry に手書き `used_by` が混入し derived と矛盾したら `reverse_reference_drift` を **blocking** で fire（full-required で fail-close）。pytest で「手書き used_by ⊕ derived 矛盾 → blocking fire」「手書き無し → clean」を固定。
- **二重正本化の禁止**: used_by を必須フィールド化したり registry に永続化する実装は §2 Out（片方向正本維持）。

### (B) 境界 count 多点同期ドリフト（audit yaml ×6 + contract py + bats mirror）
- **問題**: add-feature count は現状 8〜9 箇所に独立 pin され、同期は手動。過去（C-1/C-2/C-3a）に bats mirror 追従漏れで G-tests BLOCK が頻発。専用 drift guard は不在で、full bats 実行が偶然捕捉していた（実測 2026-06-18）。
- **対策**: `test_core_manifest_drift.py`（manifest⇔setup⇔loader 一致保証）と同型の **count 一貫性 drift テスト**を新設。全 pin 箇所（audit yaml ×6 + contract py + bats mirror）から count を読み、**全一致を assert**。1 点でもズレたら fail。意図的にズレを注入した negative test で guard が効くことを証明。
- **効果**: 以降の Action（C-3c/d, 右腕群）での count ripple 同期漏れを、full bats 偶然捕捉でなく専用テストで即時・局所的に検出（次 Action 以降のドリフト債を恒久的に閉じる）。

> TL 確認事項: (B) の count drift テストを本 Action に含めるか別 Action に分けるか（本 Action が count をまさに +1 するため同梱が自然、と PM 判断）。pin 箇所の網羅（8〜9 箇所）の正確な列挙は impl 時に C-3a `09e2b19` diff から確定。

## 9. 進捗ログ
| 日付 | 内容 | 担当 |
|---|---|---|
| 2026-06-18 | Action 起票（Process §4.1 ③b, DF-P2-FRUSES-PROMOTE close）。ユーザー AskUserQuestion で「右腕+残detectorを順に全部」scope を明示承認。現状実測（reverse warning 3 = FR-LIB-156/157/158→155、現判定は手書き双方向要求 / registry に手書き used_by 無し / count 一貫性 drift テスト不在）。ユーザー追加指示で **§8 ドリフト対策**（A: derived SSoT 単一化+drift finding、B: 境界 count 多点一貫性 drift テスト新設）を組込。 | PM (Opus) |
| 2026-06-18 | tl-advisor 設計+PLAN review = **approve（条件付き）**。derived reverse / missing_reverse_reference 撤廃 / 片方向正本維持を妥当と判定、scope breach 無し。条件（§6.1）: P2-1 reverse_reference_drift は used_by 存在時のみ比較、P2-2 count drift テストは本 Action 同梱可だが pin 箇所（audit yaml + contract mirror + bats mirror + reference integrity count）を `09e2b19` diff から網羅列挙、P2-3 clean=blocking_finding_count==0（blocking=missing_uses_target + reverse_reference_drift のみ）、P3 既存 warning_count==3 pin と fresh-checkout copy 対象更新。count pin 実測完了（`21` が audit yaml ×6 + contract py + bats mirror の多数キーに分散）。次=handover 同期 → Codex se TDD 実装。 | PM (Opus) |
| 2026-06-18 | 実装（Codex se TDD）: `build_reverse_used_by_index`（forward uses からの projection、書き戻し無し）+ `missing_reverse_reference` 撤廃 + `reverse_reference_drift`（used_by 存在時のみ derived と比較、P1 blocking）+ check_fr_uses の blocking={missing_uses_target, reverse_reference_drift}/warning=空。ドリフト対策(B) 新規 `cli/lib/tests/test_boundary_count_drift.py`（ground truth=add-feature-*.md 実数22、全 pin 一致 assert + 1点ズレ negative test）。count 21→22 を audit yaml ×6 + contract py + bats mirror へ網羅同期。automation-gate-map §3.4 + 境界契約 current_scope_authorized に C-3b 追加、forbidden_now 不変。 | Codex se |
| 2026-06-18 | PM 独立検証: pytest 109 passed（targeted 独立再実行）/ check_fr_uses clean（blocking0/warning0/finding0、reverse warning 3→0）/ check_vg_overview overall_clean=true（fr_uses full_required warning0）/ add-feature 実数22と count 一致。**TL impl review = approve（P0/P1/P2 なし）**: derived projection・drift 発火条件・blocking-only clean・count guard が bats mirror 7 pin を実拾い・negative test 在・scope/forbidden_now 不変 を確認。P3=commit 時に新規 PLAN(.md) と新規 test を含める（count 真値に PLAN 自身が含まれるため）。 | PM (Opus) + tl-advisor |
| 2026-06-18 | 全 pytest 回帰スイープ（PM）: **2610 passed / 1 failed**。fail=`test_harness_monitor_unit.py::test_feedback_loop_snapshot`（C-3b 変更を stash しても HEAD で fail = **pre-existing date-rot**、C-3b 無関係）。診断: BASE_NOW=05-17 固定挿入 vs `datetime('now','-30 days')` 実時刻窓、06-16 を越えて rot。tl-advisor 諮問=最小修正(test側)/別 Incident commit/同 push 可。ユーザー裁定=「最小修正して C-3b と同 push」。 | PM (Opus) + tl-advisor |
| 2026-06-18 | date-rot 最小修正を **PM 直接実装**（Codex se が API 404 websocket 障害で失敗→フォールバックも失敗。3行 test 専用・仕様確定済・blocker のため正当な例外）。`test_feedback_loop_snapshot` の date-windowed 2挿入（hook_event.created_at / harness_event.triggered_at）を実時刻相対の窓内へ（never-rot）。検証=該当 1 pass + harness_monitor 全 31 pass。systemic 残は Process §4 DF-DATEROT-BASENOW。status=completed。次=C-3b commit（PLAN+drift test 同梱必須=TL P3）+ date-rot Incident commit → gate-driven push。 | PM (Opus) |
