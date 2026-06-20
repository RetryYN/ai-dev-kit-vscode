---
plan_id: refactor-2026-06-21-derive-not-pin-audit-counts
title: "Refactor: audit 派生カウントの derive-not-pin 化 + pytest↔bats 二重 hardcode 解消 (drift 検出器を drift 発生源にしている SSoT 違反の是正、精度+速度)"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: refactor
kind: refactor
layer: L7
process_layer: L7
parent_design: docs/v2/L6-functional-design/registry-detector-機能設計.md  # trace: audit/contract test 群 (test_helix_l0_l14_flow_contract.py + bats mirror) は L1-L6 ratification 検証の detector。本 refactor は「期待値の供給方法」を hardcode→derive に正すのみで、検出する drift の種類・非 gameable 性・gate 判定を不変に保つ。
forward_return: "contract/audit test が派生カウント (例 path_like_refs_checked) を test code 内に hardcode するのをやめ、source-of-truth scan から actual を算出して `yaml_snapshot == computed_actual` を assert する derive 方式へ置換する。これにより PLAN を1本足すたびに 18箇所 (yaml 4 + pytest 2 + bats 3 ×複数 count) を手で同期する ripple を解消し、検出器自身が最大の drift 発生源になっている SSoT 違反を是正する。振る舞い (検出する drift の種類・非 gameable 性・overall_clean 判定) は不変。L7 へ forward_return。"
drive: be
status: finalized
status_note: "2026-06-21 起票・finalized。ユーザー指示「精度と速度が上がるのはさっさとやって」(設計批判=audit 派生カウントの dual/triple-pin は SSoT 違反、という PM 診断への go)。実測根拠: path_like_refs_checked という1つの派生カウントが 6ファイル18箇所に hardcode (audit yaml 4 + test_helix_l0_l14_flow_contract.py + bats mirror)、contract test は pytest 14,534行 + bats 9,400行 ≈ 24k行の2言語完全二重化、audit yaml は 21本。正しい pattern は本 session の B (threshold derive) と boundary_count_drift._ground_truth_excluded_count() で既に実証済 = それを contract test 全体に段階展開。【進捗】Stage1=reference-integrity family を derive-not-pin (独立再計算 _reference_integrity_independent_counts + yaml snapshot 照合 + tmp 入力 fake-drift test、literal 20箇所撤去) 完了、TL impl review=approve_with_nits (P0/P1/P2 なし、P3=bats '89 passed' pin は Stage2 へ)。Stage2 (pytest↔bats 二重化解消 + bats count-pin を exit/schema smoke 化) と他 family slice は後続 (waves 後に Stage3 yaml 統廃合)。本 session は最優先ユーザー goal A (右腕 waves) を優先するため、reference-integrity slice 着地後に waves へ pivot、残 slice は follow-up。"
current_task_scope: derive_not_pin_audit_counts
approval_required_before_l7_work: false  # test harness (B tier) の refactor。product L7 feature 実装ではない (CLAUDE.md「実装コード=Codex 委譲」に従い Codex se 実行、PM は PLAN/検証)。ユーザー go (2026-06-21) で着手。
tl_review: approve  # approach review (tl-advisor) = approach_with_changes (独立再計算/bats smoke 維持/yaml=snapshot/Stage3 分離/vertical slice 条件、§8 に反映)。Stage1 impl review (tl-advisor) = approve_with_nits (P0/P1/P2 なし、P3=bats '89 passed' pin→Stage2)。PM 独立検証: 91 passed (contract 89+boundary 2) / drift test genuine 1 passed / 1394・1385 literal 撤去 / bats reference_integrity smoke 残存。
ticket_is_completion_evidence: false
created: 2026-06-21
owner: PM
design_change_class: pure_impl  # 検出する drift の種類・非 gameable 性・gate (overall_clean) 判定・public JSON schema いずれも不変。期待値の「供給方法」を test code hardcode から source-of-truth derive に正す内部 refactor。L1-L6 ratification の検証 semantics 不変、設計層の再凍結 scope なし。各 stage で deliberate-drift test (意図的に1件 drift を注入→test が fail する) で非 gameable 保全を証明する。
target_l_pairs:
  - "L7 (refactor): contract/audit test の派生カウントを derive 化 + pytest↔bats 二重 hardcode 解消 (検出 semantics 不変)"
generates:
  - artifact_path: cli/lib/tests/test_helix_l0_l14_flow_contract.py
    artifact_type: test
  - artifact_path: cli/tests/test-helix-l0-l14-flow-contract.bats
    artifact_type: test
---

## 1. 問題 (実測)

drift を防ぐはずの検出器が、最大の drift 発生源になっている (SSoT 違反)。

- **派生カウントの multi-pin**: repo を scan して算出される1つのカウント (例 `path_like_refs_checked`) が **6ファイル18箇所** に hardcode — audit yaml 4本 (reference-integrity / double-check / objective / ratification-index) + `cli/lib/tests/test_helix_l0_l14_flow_contract.py` (2) + `cli/tests/test-helix-l0-l14-flow-contract.bats` (3)。`direct_file_refs_checked` / `discovered` / `excluded` 等も同様。
- **pytest↔bats 完全二重化**: contract test = pytest **14,534行** + bats **9,400行** ≈ **24k行**、同じ assertion を2言語で二度書き。
- **audit yaml 21本**: 凍結カウント snapshot の塊。
- **帰結**: ① add-feature PLAN を1本足すと 18箇所に波及 → reconciliation 往復 (本 session で Codex が複数回往復)。② pin が散在し波及範囲が読めない → 「怖いから全テスト実行」圧。精度 (drift 誤検出/見逃し) と速度 (同期コスト/全テスト圧) の両方を毀損。

## 2. あるべき設計 (本 session で既に実証済の pattern を展開)

- **B (threshold derive)**: magic `0.70` を撤去し `floor(1 - reserve/total)` に **導出** = SSoT 化。✓
- **boundary_count_drift._ground_truth_excluded_count()**: ground truth を **導出**し非 gameable に assert。✓
- **本 refactor = この derive pattern を contract test 全体へ展開する**。

原則: **数字は1箇所だけ (yaml = 人間向け snapshot)。test は数字を持たず、source-of-truth scan から actual を算出して `yaml == computed_actual` を assert する。** これで yaml と test の手動同期が消え、検出 (drift があれば computed_actual がずれて test fail) は強化される。

## 3. スコープ

### In (stage 制、各 stage 完結で commit/push)
- **Stage 1 — derive-not-pin (pytest)**: `test_helix_l0_l14_flow_contract.py` の派生カウント hardcode (`== <整数literal>`) を、対応 checker の `computed_actual` に対する assert へ置換。加えて `yaml_snapshot == computed_actual` を **1箇所** で assert (yaml の honesty を保証)。test code 内の整数 literal カウントを撤去。
- **Stage 2 — pytest↔bats 二重化解消**: bats mirror が再 hardcode しているカウント assertion を、python checker の JSON 出力に対する assert へ寄せる (single source = python 算出) か、pytest が既に被覆する count 再 pin を撤去し bats は shell-integration smoke に限定。どちらにするかは Stage 2 の tl 判断で確定。
- **Stage 3 (任意・要評価)**: 21本 audit yaml のうち、算出値の snapshot しか持たず reconciliation コストのみ生むものを統廃合 (人間向け snapshot として残す価値があるものは残す)。Stage 1/2 完了後に要否を再判定 (over-engineering 回避)。
- **非 gameable 保全 (全 stage 必須)**: 各 stage で deliberate-drift test = 意図的に1件 drift (fake ref 追加等) を注入すると test が fail することを証明。derive 化で検出が弱くならないことを機械で担保。

### Out (forbidden / 別 PLAN)
- 検出する drift の **種類・gate 判定 (overall_clean)・public JSON schema** の変更 (pure_impl 厳守)。
- audit が検証している L1-L6 ratification の **意味** の変更。
- product L7 feature 実装、右腕 waves (G9/G12/G14) — 別 PLAN。
- functional-registry への anchor_quality.py 登録 (別 micro、allowlist 既存)。

## 4. 受入条件
1. `test_helix_l0_l14_flow_contract.py` に派生カウントの整数 literal hardcode が残らない (derive 化)。`grep` で literal pin が無いこと。
2. 各派生カウントは `yaml == computed_actual` を1箇所で assert (yaml honesty 保証、二重 pin 解消)。
3. **非 gameable 保全**: deliberate-drift 注入で contract test が fail (各 stage で実証)。
4. pytest↔bats の同一カウント二重 hardcode が解消 (Stage 2)。
5. 振る舞い不変: `helix doctor check_vg_overview --gate --json` の overall_clean / required_clean key set / 検出 finding 種類が refactor 前後で不変。
6. add-feature PLAN を1本足す回帰シナリオで、手動同期が **0箇所** (or yaml snapshot 1箇所のみ) で済むことを実証。
7. 全 pytest + 全 bats green (landing は gate-push G-tests で1回)。

## 5. forward_return
L6↔L7 G7 pending gate evidence へ帰属 (registry-detector 機能設計の検証実装 hardening)。検出 semantics 不変のため設計層再凍結なし (pure_impl)。

## 6. 検証コマンド
- `python3 -m pytest cli/lib/tests/test_helix_l0_l14_flow_contract.py cli/lib/tests/test_boundary_count_drift.py -q`
- `bats cli/tests/test-helix-l0-l14-flow-contract.bats`
- deliberate-drift: 一時的に fake ref を1件足して contract test が fail することを確認 (各 stage)
- `helix doctor check_vg_overview --gate --json` の refactor 前後 diff (overall_clean / required_clean 不変)

## 7. agent_slots
- role: tl-advisor — approach adversarial check (derive 方式が非 gameable を保つか / pytest↔bats 統合方式 / staging / pure_impl 妥当性)
- role: se — Stage 1 derive 化 (Codex、iterate to green + deliberate-drift 実証)
- role: se — Stage 2 pytest↔bats 統合 (Codex)

## 8. TL approach conditions (approach_with_changes、execute 時 反映必須)
tl-advisor approach review = approach_with_changes。以下を満たすこと:
1. **独立再計算 (最重要)**: `computed_actual` は checker JSON の再利用ではなく **test-local の独立 scan** で算出する (checker と test が同じ抽出バグを共有して green になる silent failure を防ぐ)。既存の良形 = test_helix_l0_l14_flow_contract.py:7599 の `len(structured_refs)` 型。production helper を import して使うなら別途 metamorphic/fixture test を足す。
2. **bats smoke 維持**: bats は count mirror を撤去してよいが、CLI/pytest 起動・`PYTHONPATH`・exit status・JSON/schema の最低限 smoke は残す (shell-level 保証を失わない)。
3. **yaml は残す**: `yaml == independent_actual` の yaml は人間向け **audit snapshot** として残す (SSoT とは呼ばない。真の source = repo scan / audit bundle / manifest 実体)。pure derive (yaml 削除) は Stage 3+ の別 PLAN。
4. **pure_impl は Stage 1/2 のみ**: Stage 3 (audit yaml 統廃合) は public audit artifact の形を変えるため別 design_change_class 判定 = 別 PLAN に分離。
5. **derived_count vs semantic constant を先に分類**: literal を機械的に全撤去しない。派生カウント (scan で算出) と意味固定値 (semantic contract constant) を分類してから derive 対象を確定。
6. **vertical slice 実行**: 一括でなく reference-integrity など **1 family ずつ** 縦に derive 化 (24k行一括は危険)。Stage 3 は waves 後。
7. **fake drift は実入力改変で**: deliberate-drift 実証は monkeypatch だけでなく tmp fixture / 一時入力改変で extractor 漏れも検出する形にする。
