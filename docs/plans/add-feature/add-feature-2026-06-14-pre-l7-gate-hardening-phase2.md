---
plan_id: add-feature-2026-06-14-pre-l7-gate-hardening-phase2
title: "Action(add-feature): L7 着手前ゲート硬化 Phase2 (full) — 工程表運用導線 + コーディングルール機械チェック + 依存関係漏れ検出"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L6-functional-design/registry-detector-機能設計.md  # L6 正本: DetectorReport / GatePolicy 契約。新 detector はこの契約に従う
forward_return: "L7 着手の前提となる 3 つの横断ゲート品質を機能一覧で機械的に閉じる。(A) 工程表 l7_worklist の運用導線を doc 化し sprint へ read-only surfacing する = 機能一覧→工程表→PLAN 起票 pipeline を運用上閉じる。(B) コーディングルール registry を実 linter (bash -n/py_compile 既存 + ruff/shellcheck 新規) に baseline→ratchet で接続し enforced 昇格 = コード品質ルールを機械強制に乗せる。(C) plan dependency gate 化 + import 循環 detector + FR 間 uses 双方向リンク check = 依存関係漏れを機械検出する。いずれも L6↔L7 / L4↔L9 pending gate evidence に帰属し、新規は VG-overview required_clean (changed-files ratchet) または CI 段階導入で接続する。"
drive: fullstack
status: completed
current_task_scope: pre_l7_gate_hardening_phase2
approval_required_before_l7_feature_impl: true  # 569 機能の feature 実装は引き続き PARKED。本 Action は L7 を GUARD する横断ゲート硬化のみ
user_unpark_decision: "C (2026-06-14 followup): pre-L7 弱点のフル是正を承認 (工程表運用導線 + ruff/shellcheck doctor+CI 段階配線 + FR 間 uses schema 拡張 + import 循環 detector + plan-dep gate 化)。TL triage では大半 PARKED 推奨だったが、ユーザーが C(フル是正) を明示選択。ただし TL の技術的健全性作法 (ruff/shellcheck は即 CI red にせず baseline→changed-files ratchet で段階導入 / FR uses schema は契約拡張で L4/L6 再凍結 / 自動 backlog 生成はしない=over-build) は full 是正の中でも遵守する。L7 product feature 実装 / DB schema は引き続き PARKED。"
tl_review: approve  # PLAN review=changes_required 2周(P1×5/P2×6/P3)→全反映。impl review=remaining 3件(changed-files入力保証/TODO残骸/baseline debt明示)→Codex se 修正(push_gate に upstream→merge-base→unavailable+reason の changed-files context 注入/TODO削除/DF-P2-EXISTING-CYCLES 記録)→**focused re-review approve(P0/P1なし、true-unavailable skip-clean 残渣は監査可能として許容)**。PM 独立検証: 実 changed-files(16)注入で vg_overview overall_clean=true / 4 ratchet clean(available_nonempty) / cascade なし / L6-L7 anchored 98/98 / pytest 2594 passed+4 skipped
created: 2026-06-14
owner: PM
target_l_pairs:
  - "L6↔L7: 工程表 l7_worklist を sprint 運用導線へ接続し、機能一覧→工程表→PLAN 起票 pipeline を閉じる (WI-A)"
  - "L6↔L7 + CI: コーディングルール registry を bash -n/py_compile/ruff/shellcheck に接続し enforced 昇格 (WI-B)"
  - "L4↔L9 + L6↔L7: 依存関係 (plan dependency / import 循環 / FR 間 uses 双方向) の漏れを機械検出 (WI-C)"
design_change_class: design_or_contract_changed  # 正本 enum (pure_impl / design_or_contract_changed / unknown)。FR 間 uses field 新設 (functional-registry 契約拡張) + coding-rule enforcement 昇格 + CI 契約変更。pure_impl ではない
change_subclass: contract_extension  # design_change_class の細分 (機械 enum 外の補足タグ)
required_refreeze_pairs: ["L6-L7", "L4-L9"]  # forward-return-discipline 再凍結対象 (§7)
agent_slots:
  - role: se
    slot_label: "SE — detector / CI 配線 / registry schema / sprint surfacing / テスト実装 (Codex、TDD テスト先行)"
  - role: tl-advisor
    slot_label: "TL — PLAN review (済予定) + impl review (公開 API/exit 契約 / CI red 安全性 / 再凍結 scope の adversarial check)"
generates:
  - artifact_path: cli/lib/l7_worklist.py
    artifact_type: python_module       # sprint surfacing 連携 (read-only)
  - artifact_path: cli/helix-sprint
    artifact_type: cli_extension       # worklist read-only summary surfacing
  - artifact_path: cli/lib/coding_rule_lint.py
    artifact_type: python_module       # 新: ruff/shellcheck/bash -n/py_compile ラッパ (baseline+ratchet)
  - artifact_path: cli/lib/dependency_cycle_checks.py
    artifact_type: python_module       # 新: import 循環 detector
  - artifact_path: cli/lib/registry_checks.py
    artifact_type: python_module       # FR 間 uses 双方向リンク check 追加
  - artifact_path: cli/config/functional-registry.yaml
    artifact_type: yaml_config         # uses field 拡張 + 自己登録
  - artifact_path: cli/lib/vg_overview.py
    artifact_type: python_module       # 新 detector の required_clean 接続 (ratchet)
  - artifact_path: HELIX-workflows/helix-process/automation-gate-map.md
    artifact_type: doc_update
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires:
    - docs/plans/add-feature/add-feature-2026-06-14-pre-l7-gate-hardening.md  # Phase1 (FN↔UT pair / design_id / l7_worklist 基盤)
  blocks: []
related_docs:
  - docs/plans/process/process-2026-06-08-verification-forward-gate.md
  - docs/plans/add-feature/add-feature-2026-06-14-pre-l7-gate-hardening.md
  - docs/v2/L1-requirements/helix-workflows-verification-strategy.md
  - HELIX-workflows/helix-process/automation-gate-map.md
  - HELIX-workflows/helix-process/forward-return-discipline.md
  - cli/lib/l7_worklist.py
  - cli/lib/coding_rule_checks.py
  - cli/lib/plan_validator.py
  - cli/lib/registry_checks.py
  - cli/lib/vg_overview.py
  - cli/config/functional-registry.yaml
  - cli/config/coding-rule-registry.yaml
---

# L7 着手前ゲート硬化 Phase2 (full) — Action

> ユーザー指示 (2026-06-14 followup)「工程表の定義や使い方は OK か。あとはコーディングルールの機械チェックや依存関係漏れがないようにする」を受けた、L7 を GUARD する横断ゲートの **フル是正** Action。検証ゲート Process ([process-2026-06-08-verification-forward-gate](../process/process-2026-06-08-verification-forward-gate.md)) の品質閉合に当たる。**Phase1** ([add-feature-2026-06-14-pre-l7-gate-hardening](add-feature-2026-06-14-pre-l7-gate-hardening.md)) で FN↔UT pair coverage / design_id 実在 / l7_worklist の **基盤**を作った。本 Phase2 はその運用導線と、コーディングルール・依存関係の機械チェックを完成させる。**569 機能の feature 実装は引き続き PARKED**。

## 1. 背景 / 弱点の実測 (調査済み・実コード確認、pmo-project-explorer ×2 + TL triage)

| # | 弱点 | 実測 (file:line) | 現状の強制レベル |
|---|---|---|---|
| A1 | 工程表 l7_worklist の**使い方フローが未明文** (誰が・いつ・missing_ut をどう backlog/PLAN へ流すか) | automation-gate-map.md:89 / verification-strategy.md:323 に存在記述のみ。運用手順なし | doc gap |
| A2 | `cli/helix-sprint` が l7_worklist を**参照しない** (接続なし) | helix-sprint に worklist/l7_worklist grep 0 件 | 接続なし |
| A3 | 既存「工程表」(ai-harness.md の WBS/task-plan) と l7_worklist (L7 工程表) の**用語衝突** | docs/commands/ai-harness.md:109-135 の「工程表」= task-plan/WBS | 用語混同リスク |
| B1 | コーディングルール registry 14 entry の enforcement が**混在 + linter 未接続** (manual 7/partial 4/enforced 3 だが `linter_tool=null` で実 linter 未配線) | cli/config/coding-rule-registry.yaml (manual: CR-CODE-01/02/03,CR-COMMIT-01/02,CR-FORBID-02/03 / partial: CR-CODE-04/05,CR-COMMIT-05,CR-FORBID-04 / enforced: CR-COMMIT-03/04,CR-FORBID-01) | 混在 (linter_tool 未接続) |
| B2 | check_coding_rule_sot/alignment は **warn-only**、実 linter 呼出ゼロ | cli/lib/coding_rule_checks.py:114 mode="advisory" / helix-doctor:2148,2189 | warn-only |
| B3 | 実態は既存 CI に partial で存在 (registry の linter_tool が過小記録) | .github/workflows/{feature,hotfix,poc,refactor}.yml に py_compile + bash -n 実在。registry は linter_tool=null | registry ↔ 実態 drift |
| C1 | plan_validator の dependency 検証 (型/self-edge/reciprocal/cycle) が **warn-only・push gate 未組込** | cli/lib/plan_validator.py:681 validate_dependencies / :767 detect_dependency_cycle | warn-only |
| C2 | Python/Bash の **import 循環検出が皆無** | cli/lib/ に循環検出コード 0 | なし |
| C3 | **FR 間横依存 (uses/calls 双方向リンク欠落) が未検出** | requirement_drift は縦 trace (L3→L4→L6→code→test) のみ fail-close | なし |

> 縦 trace (requirement_drift) は既に fail-close。本 Action が埋めるのは **運用導線 (A) / コード品質機械強制 (B) / 横方向の依存漏れ (C)**。

## 2. スコープ判断 (C: フル是正、ただし段階導入の作法を遵守)

ユーザーは **C(フル是正)** を選択。TL triage は大半 PARKED 推奨だったため、**TL の技術的健全性作法を full 是正の中に取り込む**ことで「全部やる」と「CI を即壊さない/再凍結を飛ばさない」を両立する。

- **CI red 回避**: ruff/shellcheck/plan-dep gate は**即 required fail-close にしない**。`advisory → baseline 計測 → changed-files ratchet → (将来) full fail-close` の段階導入。新規違反 (changed-files) のみ fail-close、既存違反は baseline waiver。これは検証ゲート方針「green な detector だけ昇格」と整合する。
- **契約拡張は再凍結**: FR 間 uses field は functional-registry 契約拡張 → L4/L6 再凍結 (§7、forward-return-discipline)。
- **over-build 回避**: 工程表→自動 backlog 生成はしない (TL 指摘、前回 PLAN 自動起票と同型)。read-only surfacing + 手動 backlog 化 + negative test に留める。

## 3. 作業項目

### WI-A: 工程表 l7_worklist の運用導線 (doc + read-only 接続)
- **A1 運用フロー doc 化**: automation-gate-map.md / CLAUDE.md (§V2 開発) / sprint guide に「L7 sprint 起票前に PM が `helix doctor check_l7_worklist --json` を走らせ、`missing_ut` 行を sprint backlog または PLAN へ**手動**反映する」フローを明文化。
- **A2 sprint surfacing**: `helix sprint status` (および `.1a` 開始時) に worklist summary (total/anchored/waived/RD/missing_ut の件数) を **read-only 表示**。自動 backlog 生成はしない。
- **A3 用語整理**: ai-harness.md / 関連 doc で「工程表」が WBS/task-plan を指す箇所と l7_worklist (L7 工程表 = FN↔UT 充足 view) を**別概念として区別**する注記。可能なら後者を「L7 worklist / L7 充足ビュー」と表記統一。

### WI-B: コーディングルール機械チェック (registry 整合 + linter 段階配線)
- **B1 registry 実態整合**: 現行実態 (manual 7/partial 4/enforced 3) を退行させず、`linter_tool=null` を実 linter (bash -n/py_compile/ruff/shellcheck) と対応づけて記入。既に partial の CR-CODE-04/05・enforced の CR-COMMIT-03/04/CR-FORBID-01 は維持し、linter_tool 欠落のみ補完する。
- **B2 linter ラッパ新設** `cli/lib/coding_rule_lint.py`: bash -n / py_compile (依存ゼロ・常時実行) を先行配線。ruff (Python) / shellcheck (Bash) は **インストールせず、存在時のみ実行 (graceful skip)**。CI でも install step は追加しない (新規依存・ライセンス・CI 時間の判断を避ける)。
- **B3 baseline + ratchet**: 既存違反を `cli/config/coding-rule-registry-baseline.json` (既存 default 名と統一、coding_rule_checks.py:397) に計測記録。**changed-files** (§4.1 で source 固定) に対してのみ新規違反を fail。doctor は default warn (baseline 込み) / `--gate` 時に changed-files ratchet を fail-close。
- **B4 gate 接続先 (明示)**: `coding_rule_lint` は専用 doctor subcommand `check_coding_rule_lint` を持ち、その結果を **vg_overview.required_clean に changed-files ratchet モードで集約** (新 gate ID は作らず G-vg-overview を硬化)。CI には ruff/shellcheck step を `continue-on-error: true` (advisory) で追加し install はしない。full CI required 化は §8 deferred。
- **B5 enforced 昇格**: ratchet が green な entry のみ `enforcement.status: enforced` へ昇格。残りは partial/manual で正直記録 (退行禁止)。

### WI-C: 依存関係漏れ検出
- **C1 plan dependency gate 化**: `accepted_dependency_warning` waiver schema を新設 → 既存 WARN を baseline 化 → plan_validator dependency を **changed-files ratchet** (§4.1 source) で vg_overview required_clean へ接続。real cycle / missing reciprocal は changed-files の新規分のみ fail-close (既存は baseline waiver)。
- **C2 import 循環 detector** `cli/lib/dependency_cycle_checks.py` (専用 module、`registry_checks` の基盤型を再利用し肥大化させない): cli/lib の Python import グラフ (および Bash source) の循環を検出。false positive 境界 = cli/lib スコープ限定 + 既存循環 baseline。doctor warn → 新規循環のみ fail-close。
- **C3 FR 間 uses 片方向正本 + 逆参照 derived check**: functional-registry に `uses` field (任意配列) を新設 = **片方向の正本** (A が B を uses する宣言)。**専用 module** (`registry_checks` の基盤型再利用) で「uses 先 FR が実在するか」を fail-close 検査。**逆参照整合 (B 側に逆リンクがあるか) は derived check として warning/ratchet** とし、将来 required 化 (§8 deferred)。**契約拡張**のため §7 再凍結。

## 4. 段階導入レベル (各 detector の昇格段階を明示)

| detector | Phase2 着地点 | 将来 (PARKED 後続) |
|---|---|---|
| coding_rule_lint (bash -n/py_compile) | doctor --gate で changed-files fail-close | — |
| coding_rule_lint (ruff/shellcheck) | advisory + baseline + changed-files ratchet (CI continue-on-error) | full fail-close / CI required |
| plan dependency | waiver schema + baseline + changed-files ratchet | full required_clean |
| import 循環 | doctor warn + baseline (新規循環のみ fail-close) | required_clean 昇格 |
| FR 間 uses | doctor warn → uses 先実在を fail-close / 逆参照欠落は derived warning | required_clean 昇格 (逆参照必須化) |

### 4.1 changed-files source の固定 (ratchet 共通入力)
全 ratchet detector (coding_rule_lint / plan dependency / import 循環) は **同一の changed-files source** を使う。push_gate に汎用ヘルパが無い (現状 git diff --name-only は push_gate.py:208 で PLAN 検出のみ) ため、共通ヘルパ `changed_files(upstream)` を新設する:
1. `HELIX_CHANGED_FILES` env (空白/改行区切り) があればそれを優先 (テスト・CI からの注入用)。
2. 無ければ `git diff --name-only <upstream>..HEAD` (upstream = `origin/<branch>`、push_gate の既存 upstream 解決を再利用)。
3. helper は **`source_status` を戻り値に持たせ、valid empty と unavailable を分離**する (ratchet の抜け道を防ぐ):
   - `available_nonempty`: 変更ファイルあり → ratchet 通常判定。
   - `available_empty`: 差分が正しく空 → **clean** でよい。
   - `unavailable`: upstream 未設定/取得失敗 → **clean 相当にせず** `skipped: changed-files unavailable` を skip reason として VG-overview に明示出力 (fail-close もしないが clean とも記録しない)。CI/push gate では `HELIX_CHANGED_FILES` または base ref を**明示解決**して unavailable を起こさない運用とする。
   merge-base / untracked file の揺れは baseline 側で吸収する。

## 5. テスト戦略 (TDD、テスト先行)
- **WI-A**: l7_worklist fixture unit (既存) + `helix sprint status`/`.1a` surfacing の Bats。**自動 backlog を生成しない negative test** を入れる。
- **WI-B**: bash -n/py_compile/ruff/shellcheck ラッパの unit (baseline 内違反は pass / changed-files 新規違反は fail / ツール不在時 graceful skip)。doctor default exit 不変 + `--gate` exit の Bats。
- **WI-C**: plan dependency fixture で「既存 WARN は baseline 化され、新規 real cycle / missing reciprocal **だけ** fail する」を検証 (baseline 内 pass と新規 fail を別 fixture に分離)。import 循環 fixture (循環あり/なし/baseline 内)。FR 間 uses fixture (uses 先実在 OK / uses 先不在 fail / 逆参照欠落は warning に留まる)。
- **ratchet 共通 (§4.1)**: changed-files source が **空/未指定のときは fail でなく明示 skip/advisory** になる test。baseline 内違反 pass と changed-files 新規違反 fail を**同じ fixture に混ぜず別 fixture に分離**。
- **tool 不在 skip の境界**: ruff/shellcheck 不在時の graceful skip が、**bash -n / py_compile の必須検査まで skip しない**ことを検証。
- **gate exit の Bats**: `doctor --gate` が coding_rule_lint / plan dependency の changed-files 新規違反で**実際に非 0**になる Bats。default (非 gate) doctor の exit は不変。
- 全体: pytest + bats フルスイート green、doctor --gate 0 fail、vg_overview overall_clean=true 維持。

## 6. 自己登録 (機能一覧)
新 detector / モジュールを functional-registry に FR-LIB-155.. で自己登録 (coding_rule_lint / dependency_cycle_checks / FR uses check)。design_ids(FN) ↔ test_design_ids(UT) を 1:1 で付与 (Phase1 の fn_ut_pair_coverage で検査される)。

## 7. design_change_class = design_or_contract_changed (change_subclass = contract_extension) / 再凍結 scope (forward-return-discipline)
pure_impl ではない。以下を再凍結する:
- **functional-registry schema** (L3 doc helix-workflows-functional-registry.md): `uses` field 追加 → §1.x schema + AC。
- **coding-rule-registry schema**: enforcement.status の partial/enforced 昇格条件 + linter_tool field。
- **registry-detector-機能設計** (L6): 新 detector (coding_rule_lint / dependency_cycle / FR uses) の DetectorReport 契約。
- **automation-gate-map**: required_clean / ratchet 段階導入の配線記述。
- **新 detector の L6 機能設計 + L7 単体テスト設計** (FN-*/UT-* 追加、whole-source-coverage docs)。
- **verification-strategy** §14: linter 層 / 依存層の機械強制記述。

## 8. deferred findings (本 Action でやらない / PARKED)
- DF-P2-RUFF-CI: ruff/shellcheck の **CI required (full fail-close)** 化 = baseline が安定し changed-files ratchet が回ってから。
- DF-P2-DEPGATE-FULL: plan dependency の **full required_clean** 化 = waiver baseline が clean になってから。
- DF-P2-IMPORTCYCLE-PROMOTE: import 循環 detector の required_clean 昇格。
- DF-P2-FRUSES-PROMOTE: FR 間 uses check の required_clean 昇格 (双方向逆参照の必須化)。
- DF-P2-UNAVAIL-SKIP: changed-files が真に解決不能 (upstream/merge-base 両方不能) な場合、ratchet は `unavailable` で **skip (block しない、reason 付き=監査可能)**。push gate は upstream→merge-base fallback で通常これを起こさない。TL re-review で「監査可能な skip-clean」として許容。完全閉塞 (unavailable も block) は full required 化と併せ PARKED。
- 引き続き PARKED: L7 product feature 実装 / DB schema 拡張。

## 11. 完遂 evidence (LANDED 時に確定)
- **WI-A**: helix-sprint に L7 worklist read-only surfacing (no-write negative test) + CLAUDE.md/ai-harness 用語整理 (L3 工程表 vs L7 worklist)。
- **WI-B**: changed_files (ratchet 共通 source) + coding_rule_lint (bash -n/py_compile 常時 + ruff/shellcheck graceful skip) + baseline + registry linter_tool 補完 (enforcement 退行なし manual7/partial4/enforced3)。
- **WI-C**: dependency_cycle_checks (既存5循環 baseline waive) + plan_dependency_gate (WARN baseline + 新規 cycle/reciprocal fail) + fr_uses_checks (uses 片方向正本)。残骸 cli/lib/{alpha,beta}.py を PM 削除 + import baseline 再生成 (偽6→実5)。
- **Step3 統合**: FR-LIB-155..159 自己登録 (design_ids↔test_design_ids 1:1) + FN/UT-WSC-224..228 + g7 anchor (universe 93→98) + vg_overview required_clean ratchet 配線 (4 detector) + Phase1 PLAN reciprocal。
- **impl review 修正**: push_gate に changed-files context 注入 (upstream→merge-base→unavailable+reason)、TODO 残骸削除。
- **検証**: 実 changed-files(16) で vg_overview overall_clean=true、required_clean 全 clean (registry_design/design_id/fn_ut_pair/ddd_bc/coding_rule_lint/dependency_cycle/plan_dependency/fr_uses/trace/drift)、L6-L7 anchored 98/98 exec_pass 98、pytest 2594 passed/4 skipped、新規 bats 11 pass、push_gate+vg_overview 50 pass、cascade なし。最終 gate = gate-driven push (G-tests 全 + G-vg-overview) で確定。

## 9. forward_return / DB 収束
frontmatter `forward_return` 参照。L6↔L7 (G6/G7) + L4↔L9 pending gate evidence に帰属。新規 fail-close 分は VG-overview required_clean (changed-files ratchet) / CI 段階導入で接続。weakness-forward-integration-map.yaml に W16 (工程表運用導線) / W17 (コーディングルール機械強制) / W18 (依存関係横漏れ) を追加し Forward 帰属させる。

## 10. 実装順序 (完全並列は非推奨・test-first / pair-freeze 厳守 — TL review 反映)
`design_or_contract_changed` (required_refreeze_pairs: L6-L7, L4-L9) のため、**契約・設計・テスト設計の再凍結を実装より先**に置く (forward-return-discipline / TDD テストファースト)。
1. **PLAN 修正 (本 commit、済)**: canonical `design_change_class` / baseline file 名 / changed-files source (§4.1) / gate 接続先 (B4) / `required_refreeze_pairs` を固定。
2. **L4/L6/L7 design・test-design refreeze scaffold (先)**: 新 FR (coding_rule_lint / dependency_cycle / FR uses) の **L4 契約** (functional-registry `uses` schema / coding-rule enforcement schema / DetectorReport 契約) + **L6 機能設計** (FN-*) + **L7 単体テスト設計** (UT-*) を**先に固定** (anchor 確保)。fn_ut_pair_coverage (Phase1) が新 FR の FN↔UT 1:1 を検査できる状態にする。
3. **テスト/fixture 先行 (TDD red)**: §5 の各 fixture・unit/bats を実装本体より先に書き、red を確認する。
4. **WI module 本体実装 (並列可)**: WI-A (l7_worklist surfacing + doc) / WI-B (coding_rule_lint + baseline) / WI-C (dependency_cycle + FR uses module + plan-dep waiver) の新規 module を独立並列で Codex se へ。テストを green にする。
5. **共有ファイル配線 (単一 owner が直列)**: 複数 WI が触る以下を最後に PM (または単一 se) が直列マージ:
   - `cli/lib/vg_overview.py` (required_clean への detector 追加・ratchet モード)
   - `cli/config/functional-registry.yaml` (`uses` field + 自己登録 FR-LIB-155..)
   - `HELIX-workflows/helix-process/automation-gate-map.md` (配線記述)
   - `cli/lib/registry_checks.py` (基盤型のみ。FR uses check は専用 module へ。ここを肥大化させない)
6. **refreeze_evidence 記録 + machine-clean / semantic-pass**: 再凍結証跡を記録し、doctor --gate 0 fail / vg_overview overall_clean=true / fn_ut_pair_coverage clean を確認して閉じる。
