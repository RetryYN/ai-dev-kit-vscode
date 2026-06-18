---
doc_id: automation-gate-map
title: Vモデル自動化・ゲートマップ
status: accepted
accepted_date: 2026-05-24
created: 2026-05-24
updated: 2026-06-08
owner: PM
parent: ../HELIX-process-L0-L14.md
integration_target:
  docs_path: docs/architecture
  category: 管理・自動化基盤
---

# Vモデル自動化・ゲートマップ

## 概要

新Vモデル（L0–L14）の自動化・ゲート**配線正本**。検証はロードマップの Phase として常時目指すものでなく、**Forward V-model に内在する検証サイクル＝ゲート**として機能させる（各 L の凍結/前進は検証閉合をゲートで通す）。各 layer に detector が紐づき、各ゲートは決定論的 static + detector で判定する。AI判断は中身の評価のみ。

> 本書 = **detector ↔ gate / push / CI の配線と enforcement phase**。役割分担: 原則・L/G 対応 → [HELIX-process-L0-L14](../HELIX-process-L0-L14.md)／判定式・evidence schema → [verification-strategy §14](../../docs/v2/L1-requirements/helix-workflows-verification-strategy.md)／readiness 正本 → [gate-policy](../../skills/tools/ai-coding/references/gate-policy.md)／static adapter（派生・正本でない）→ `gate-checks.yaml`／push 前 orchestration → `cli/lib/push_gate.py`。

## 0. ゲート体系と V-model L 対応（公開 ID 維持・L exit 整合）

公開 gate ID `G0.5/G1〜G14`（+ sub-gate）は**維持**し、意味を「対応 L の exit gate」に固定する（番号を作り直すと既存 PLAN/handover/CI/利用者 docs が壊れる）。内部実装は安定 key（`VG-L0x-exit` / `VG-Lxx-pair-Lyy` / `VG-overview-pre-push`）を持つ。

> **G0 の扱い（TL P2 反映）**: `G0` は独立した fail-close gate ID **ではなく** L0 企画の **entry marker**。最初の決定論ゲートは **G0.5（企画突合）**。gate-policy / gate-checks / 本書 §1 は G0.5 始まりで一致させる（§1 表の `L0 | G0 / G0.5` は「entry marker G0 + 突合ゲート G0.5」の意）。

> **既知 drift（是正対象、2026-06-08 検出）**: [gate-policy.md](../../skills/tools/ai-coding/references/gate-policy.md) は G0-G14（+sub）full set を readiness table に持つが、実行される `gate-checks.yaml`（template）は **G0/G1/G1.5/G8/G11.5/G12/G13/G14 が欠落**。policy ↔ 実装の乖離。本書の補完対象 = 欠落ゲートの static + detector 配線。旧 `G6.5/G6.7/G6.9` は L 整合 ID への alias として deprecated 計画。

## 1. Forward 全段階ゲート（G0–G14、L exit）

| L（工程） | gate | 種別 | exit が要求する検証閉合 | 束ねる detector/check | 現 enforce | 目標 |
|---|---|---|---|---|---|---|
| L0 企画 | G0 / G0.5 | entry/突合 | 企画書・要件・受入条件の存在、TODO 残存なし | 企画突合 static | fail-close(G0.5) | 維持 |
| L1 要求 | G1 | 左腕 freeze | L1 要求凍結 + **対 L14 運用テスト設計** + L1↔L14 trace(pre) | requirement_drift / trace_symmetry(L1-L14) | **未実装(欠落)** | ratchet→fc |
| L2 画面 | G2 | 左腕 freeze | L2 画面/設計凍結 + **対 L10 UX/FE 検証設計** + L2↔L10 trace(pre) | FE detector(axis-15-19 未実装) / trace_symmetry(L2-L10 未) | advisory/skip | waiver schema |
| L3 要件 | G3 | 左腕 freeze | L3 要件凍結 + **対 L12 受入テスト設計** + requirement_drift | trace_symmetry(L3-L12) / requirement_drift | proxy(grep) | detector 化 |
| L4 基本設計 | G4 | 左腕 freeze | L4 凍結 + **対 L9 総合テスト設計** + L4↔L9 trace(pre) | trace_symmetry(L4-L9) | advisory | ratchet→fc |
| L5 詳細設計 | G5 | 左腕 freeze | L5 凍結 + **対 L8 結合テスト設計** + L5↔L8 trace(pre) | trace_symmetry(L5-L8) | advisory | ratchet→fc |
| L6 機能設計 | G6 | 左腕 freeze | L6 凍結 + **対 L7 単体テスト設計** + L6↔L7 trace(pre) + FN↔UT 1:1 + FN-* 実 doc 実在 | trace_symmetry(L6-L7) / registry_design_coverage / **fn_ut_pair_coverage** / **design_id_existence** | fn_ut_pair/design_id=**fail-close** / 他 advisory | **MVP fail-close** |
| L7 実装 | **G7** | 右腕 execution | **UT-ID test code anchor + test_execution_pass** + L6↔L7 trace(post) + semantic | UT anchor subcheck(新) / pytest・bats 実行 / trace_symmetry | proxy | **MVP fail-close** |
| L8 結合 | G8 | 右腕 execution | 結合テスト anchor + 実行 pass + L5↔L8 trace(post) + semantic | IT anchor / 結合テスト実行 | **未実装(欠落)** | ratchet |
| L9 総合 | G9 | 右腕 execution | 総合テスト anchor + 実行 pass + L4↔L9 trace(post) + semantic（orphan は semantic gate） | ST anchor / 総合テスト実行 | proxy | ratchet |
| L10 UX | G10 | 右腕 execution | UX 検証実行 + L2↔L10 closure | FE visual/a11y(未) | advisory/skip | waiver |
| L11 レビュー | G11 | 横断 | drift 解消 + RC 判定（要件巻取り・全 pair 俯瞰） | requirement_drift / VG-overview | proxy | fail-close |
| L12 受入 | G12 | 右腕 execution | 受入テスト anchor + 実行 pass + L3↔L12 closure | AT anchor / 受入テスト実行 | **未実装(欠落)** | ratchet |
| L13 運用検証 | G13 | 運用 | canary / smoke / 初期運用 gate | デプロイ後検証 | **未実装(欠落)** | 後続 |
| L14 運用学習 | G14 | 右腕 execution | 運用検証 + L1↔L14 closure（運用テスト実施） | OT 実行 / 運用観測 | **未実装(欠落)** | 後続 |

- **左腕 freeze gate（G1-G6）**: `design + test_design + trace_symmetry(pre-execution)` まで要求。
- **右腕 execution gate（G7-G14 の対）**: `test_code_anchor + test_execution_pass + trace_symmetry(post-execution) + semantic_gate` まで要求。
- coverage 100% 単独 pass は禁止（例: L4↔L9 は cov100% でも ST→TV→L4 の `semantic_excluded_orphan=18` と balance0.67 を semantic gate evidence として確認する）。

## 2. pair-closure ゲート（6 pair、検証実体）

各 pair は `pair_closure = design + test_design + test_code_anchor + test_execution_pass + trace_symmetry + semantic_gate` の AND（判定式正本 = verification-strategy §14）。

| pair | 左腕 freeze | 右腕 execution | detector | 現状 |
|---|---|---|---|---|
| L6↔L7 単体 | G6 | **G7** | trace_symmetry(L6-L7) + UT anchor + pytest/bats | 設計 balanced(FN88↔UT88)、検証実行 anchor 31/88（**MVP で閉じる**） |
| L5↔L8 結合 | G5 | G8 | trace_symmetry(L5-L8) + IT 実行 | gap=IT-MOD-06/IT-DB-03/05（DF-WCAUDIT-L5L8-001） |
| L4↔L9 総合 | G4 | G9 | trace_symmetry(L4-L9) + ST 実行 | cov100% / missing0 / orphan0 / semantic_excluded_orphan18。DF-WCAUDIT-L4L9-001 の detector over-report は解消済み、残は G9 ST 実行 gate |
| L3↔L12 受入 | G3 | G12 | trace_symmetry(L3-L12) + AT 実行 | trace green、G12 実行 gate 未実装 |
| L2↔L10 UX | G2 | G10 | FE detector(axis-15-19 未) | UI absent / 未実装 → `not_applicable`/`ui_absent` waiver schema 必須。HELIX-workflows 自身は `docs/v2/L2-screen-design/helix-workflows-ui-absent-waiver.md` |
| L1↔L14 運用 | G1 | G14 | trace_symmetry(L1-L14) + OT 実行 | trace green、G1/G14 gate 未実装 |

- **trace_symmetry の pair**: 現状 `PAIR_LAYERS` は L1-L14/L3-L12/L4-L9/L5-L8/L6-L7 の **5 pair**。**L2-L10 が欠落**（FE detector 未実装と連動）→ 補完対象（waiver schema で skip 野放しを防ぐ）。

## 3. 横断ゲート（要件ずれ drift / 全体俯瞰 overview）

段階ゲート・pair ゲートに加え、**横断で常時 fail-close 化する 2 ゲート**を新設する。

### 3.1 要件ずれゲート（requirement_drift、新規 detector）
- 責務 = ID 対称性（trace_symmetry の領域）でなく **縦・意味 trace**。よって `trace_symmetry` 拡張でなく**別 detector `cli/lib/requirement_drift.py`**。
- 入力: L1/L3 requirement docs、L4-L6 design ID/frontmatter、functional-registry、code anchor/docstring/test anchor。
- 出力: `missing_downstream` / `orphan_design` / `orphan_code` / `semantic_label_mismatch` / `stale_freeze` / `waived_with_reason`。
- fail-close 対象 gate: G3 / G4 / G6 / G7 / G11 / pre-push。
- 意義: 「L1 FR → L3 FR → L4-L6 設計 → L7 code → test」が時間でずれる（要件ずれ）のを止める経路（現状ゼロ）。

### 3.2 全体俯瞰ゲート（VG-overview、新規 aggregator）
- freeze 前・push 前に**必須**で通す横断ゲート（workflow でなく Forward gate activity）。
- 判定 (`required_clean` 全 clean): `registry_design_coverage`（whole-source⊆design）+ `source_scan_vs_registry` + `registry_trace_complete` + `requirement_drift` + **`fn_ut_pair_coverage`**（FN↔UT 1:1 網羅）+ **`design_id_existence`**（FN-* の L6 doc 実在）+ **`ddd_bc_coverage`**（DDD bc 2 check）+ **`coding_rule_lint`** / **`dependency_cycle_checks`** / **`plan_dependency_gate`** / **`fr_uses_checks`**（pre-L7 Phase2、changed-files ratchet）+ `trace_symmetry all applicable pairs clean/semantically-accepted` + `未承認 P0/P1 deferred finding = 0`（PM 承認なき限り）。
- 配線: `helix doctor --gate` / `push_gate.py` の `G-vg-overview` から呼ぶ共通 runner。
- **standalone --gate fail-close（W1 狭い flip、§4.1 ①、2026-06-15）**: aggregate `G-vg-overview` だけでなく、個別 detector subcommand も `--gate` で fail-close させる（standalone surface が exit0 固定で gate を騙る latent ギャップを閉じる）。`check_requirement_drift --gate`（`blocking_clean`=false で exit 1。advisory=semantic_label_mismatch/stale_freeze では落とさない）/ `check_g7_subcheck --gate`（missing/unanchored/exec mismatch で exit 1。`HELIX_DOCTOR_SKIP_EXEC_TESTS=1` で project-state 非依存=CI fresh checkout 安全）/ `check_vg_overview --gate`（既存）。default（`--gate` 無し）・`--json` payload は不変（exit code のみ変化）。**CI `detector-gate` job は aggregate `check_vg_overview --gate` のみ**（standalone を CI に増やさない＝aggregate を authoritative surface に保つ）。正本 = [add-feature-2026-06-15-w1-narrow-failclose-promotion](../../docs/plans/add-feature/add-feature-2026-06-15-w1-narrow-failclose-promotion.md)。**broad flip（W1 全 advisory 一括 fail-close / 他 detector required 化 / strict-full-flow）は forbidden_now**（明示承認 entry 要）。

### 3.3 test_design 層 detector（pre-L7 ゲート硬化、2026-06-14）
- `pair_closure = design + test_design + test_code_anchor + test_execution_pass + ...` のうち **test_design 層（機能設計 FN ↔ 単体テスト UT 1:1）** を機械化（従来 g7_subcheck の anchor/exec_pass より手前の層）。
- `fn_ut_pair_coverage`（FN-WSC-221）/ `design_id_existence`（FN-WSC-222）: `required_clean` 経由で **fail-close**。既知債は `fn_ut_pair_waivers` / `design_id_existence_waivers`（approved_deferred）で吸収し**新規デグレのみ block**（既存 L7 実装債で CI red 化しない）。
- `l7_worklist`（FN-WSC-223）: **read-only 工程表 view**（fail-close にしない）。registry 由来で「L7 で何を実装すべきか」を決定論生成。`helix doctor check_l7_worklist --json`。RD-UT-* は `separate_inventory`。
- DDD ratchet（`ddd_bc_coverage`）の昇格詳細は §5 enforcement phase を正本とする（本節では再宣言しない）。
- 正本: [add-feature-2026-06-14-pre-l7-gate-hardening](../../docs/plans/add-feature/add-feature-2026-06-14-pre-l7-gate-hardening.md) / L3 schema [functional-registry §1.7](../../docs/v2/L3-requirements/helix-workflows-functional-registry.md) / L6 [registry-detector §3.2](../../docs/v2/L6-functional-design/registry-detector-機能設計.md)。

### 3.4 コードルール / 依存関係 ratchet detector（pre-L7 ゲート硬化 Phase2、2026-06-14）
- **共通入力**: `changed_files(upstream)`（FR-LIB-155）が `source_status = available_nonempty | available_empty | unavailable` を返す。ratchet は `available_nonempty` の changed files 上の baseline 外（新規）違反のみ block。`available_empty`=clean、`unavailable`=skip（block しない。push/CI では `HELIX_CHANGED_FILES` / base ref を明示し unavailable を起こさない運用）。
- `coding_rule_lint`（FR-LIB-156 / FN-WSC-225）: bash -n / py_compile を常時、ruff / shellcheck は存在時のみ（install しない graceful skip）。baseline = `coding-rule-registry-baseline.json`。**core(bash_n/py_compile) は C-3c で `required_clean` の full-scan full-required（全件 fail-close）へ昇格**、optional(ruff/shellcheck) は advisory のまま required path 非算入（C-2 境界）。`evaluate_coding_rule_lint`(changed-files ratchet)は standalone 用に維持。registry の `linter_tool` と対応（CR-CODE-01→bash_n/shellcheck, CR-CODE-05→py_compile/ruff）。
- `dependency_cycle_checks`（FR-LIB-157 / FN-WSC-226）: cli/lib import 循環。既存 5 循環は `import-cycle-baseline.json` で waive、新規循環のみ fail-close（既存債は隠蔽でなく ratchet 起点。解消は Refactor で別途）。
- `plan_dependency_gate`（FR-LIB-158 / FN-WSC-227）: `plan_validator` の dependency 検証（型/self-edge/reciprocal/cycle）の ratchet wrapper。`accepted_dependency_warning` を `plan-dependency-baseline.json` で waive、changed-plan の新規 real cycle / missing reciprocal のみ fail-close。
- `fr_uses_checks`（FR-LIB-159 / FN-WSC-228）: functional-registry `uses` field（片方向正本）の uses 先実在と、forward `uses` から derived した reverse `used_by` consistency を検証する。**forward(uses先実在)は C-3a、reverse(derived drift) は C-3b で full-required へ昇格済**。
- 段階: `dependency_cycle_checks` / `plan_dependency_gate` は **changed-files ratchet（新規違反のみ block）**。`fr_uses_checks` は **C-3a/C-3b で forward + reverse(derived drift only) の full-required（全件 fail-close）**、`coding_rule_lint` は **C-3c で core(bash_n/py_compile) の full-required** へ昇格済（optional ruff/shellcheck は C-2 advisory 据置）。残（dependency_cycle / plan_dependency）の full required 化 / CI required 化は deferred（weakness-map DF-P2-*）。
- **fr_uses forward の full-required 昇格（C-3a、§4.1 ③a、2026-06-16、ユーザー承認の narrow per-detector flip）**: `vg_overview.required_clean.fr_uses_checks` の source を changed-files ratchet（`collect_fr_uses_gate_summary`）から **full-scan full-required（`collect_fr_uses_full_required_summary`）** へ切替。forward=uses先実在の全件 fail-close。changed-files availability に依存しない。これは forbidden_now #5「broad advisory→fail-close flip of W1 detectors」に**抵触しない**（narrow per-detector flip、forward-only）。境界契約 `current_scope_authorized` に C-3a 追加済（forbidden_now 5 項目は不変）。正本 = [add-feature-2026-06-16-c3a-fr-uses-forward-full-required](../../docs/plans/add-feature/add-feature-2026-06-16-c3a-fr-uses-forward-full-required.md)。
- **fr_uses reverse の derived full-required 昇格（C-3b、§4.1 ③b、2026-06-18、ユーザー承認の narrow per-detector flip）**: reverse は registry へ手書き back-edge を要求せず、forward `uses` から `used_by` を derived projection として算出する。`missing_reverse_reference` は撤廃し、registry entry に **手書き `used_by` が存在する場合のみ** derived と比較して `reverse_reference_drift` を blocking finding とする。`used_by` 欠落は clean、`clean = blocking_finding_count == 0`、blocking は `missing_uses_target` と `reverse_reference_drift` のみ。これも forbidden_now #5 に**抵触しない**（narrow per-detector flip、broad flip 不含）。境界契約 `current_scope_authorized` に C-3b 追加済。正本 = [add-feature-2026-06-18-fruses-reverse-derived-promotion](../../docs/plans/add-feature/add-feature-2026-06-18-fruses-reverse-derived-promotion.md)。
- **coding_rule_lint core の full-required 昇格（C-3c、§4.1 ③c、2026-06-18、ユーザー承認の narrow per-detector flip）**: `coding_rule_lint` は core(`bash_n` / `py_compile`) と optional(`ruff` / `shellcheck`) を分離し、`collect_coding_rule_lint_full_required_summary` で **full-scan core 違反のみ blocking** に評価する。`clean = blocking_finding_count == 0`、`source_status=full_required`。optional の `ruff` / `shellcheck` は advisory のまま **blocking / required path に算入しない**（C-2 境界維持、external tool required 化を禁止）。`vg_overview.required_clean.coding_rule_lint` は changed-files ratchet からこの core-only full-required source へ切替。これも forbidden_now #5 に**抵触しない**（narrow per-detector flip、broad flip 不含）。境界契約 `current_scope_authorized` に C-3c 追加済。正本 = [add-feature-2026-06-18-coding-rule-core-full-required](../../docs/plans/add-feature/add-feature-2026-06-18-coding-rule-core-full-required.md)。
- **ruff/shellcheck の CI 実行（C-2、§4.1 ②、2026-06-15、ユーザー承認の advisory-only 外部 tool 実行）**: 専用 job `ruff-shellcheck-advisory`（`continue-on-error: true`、Required 非対象、`needs:` なし、`helix doctor check_coding_rule_lint --json` 経由）で CI 実行する。ruff = job 内 `pip install` / shellcheck = job 内 `apt install`、**`requirements-dev.txt` には ruff を入れない**（test/detector-gate の dev install へ波及して advisory 境界が崩れるのを防ぐ）。`--gate` を付けず detector-gate / doctor --gate / push gate へ fail-close 接続しない。**required 化 / fail-close 化は依然 forbidden_now**（明示承認 entry）。境界契約 `latest_user_boundary.forbidden_now` #4 は「install/execute external tools outside approved C-2 ruff/shellcheck advisory CI job or as required/fail-close gate」に精緻化済。正本 = [add-feature-2026-06-15-c2-ruff-shellcheck-advisory](../../docs/plans/add-feature/add-feature-2026-06-15-c2-ruff-shellcheck-advisory.md)。
- 正本: [add-feature-2026-06-14-pre-l7-gate-hardening-phase2](../../docs/plans/add-feature/add-feature-2026-06-14-pre-l7-gate-hardening-phase2.md)。

## 4. layer × detector（工程別の自動検証）

`vmodel-semantics.yaml` で各 layer の design 側・test 側に detector が紐づく（現状 advisory、§5 で段階昇格）。

| layer（対応工程） | design 側 detector | test 側 detector |
|---|---|---|
| planning（L0–L1） | axis-08 plan-integrity / axis-14 orchestration | axis-11 regression / axis-14 |
| requirement（L3） | axis-07 contract-drift / axis-08 / axis-12 connection | axis-09 test-quality / axis-11 |
| architecture（L4） | axis-02 coverage-erosion / axis-07 / axis-10 relation-graph | axis-09 / axis-11 / axis-12 |
| detailed（L5） | axis-06 naming / axis-07 / axis-12 | axis-02 / axis-09 / axis-11 |
| functional（L6） | axis-01 dead-code / axis-02 / axis-09 refactor | axis-02 |
| FE（L2 / L10） | axis-15 mock-promotion / axis-19 state-transition-drift | axis-16 design-token / axis-17 a11y / axis-18 visual |

axis-01〜14 は実装済み（**いずれも advisory / push 未接続**）。axis-15〜19（FE）は未実装（fe-detector-spec.md）。verification 実体 detector（`trace_symmetry` / `registry_design_coverage` / `requirement_drift`(新) / `VG-overview`(新)）はこの軸群と別系統で、§2/§3 の pair/横断ゲートに紐づく。

## 5. enforcement 段階（advisory → ratchet → fail-close）

- **advisory**（現状）: detector は計測・warn のみ、exit 0、push 非ブロック。
- **ratchet**: 既存 findings は許容、**新規違反のみ block**（baseline 比較）。green 化途上の detector の段階。
- **fail-close**: 昇格 set の violation で exit 1 / CI red / push block。**今 green な分のみ昇格**（CI 即 red 回避）。

**MVP（ユーザー確定、TL P1 反映で 2 段順序を厳守）**:
- **MVP-A（計測 + closure 先行、advisory のみ）**: G7 subcheck（UT-ID test code anchor + test_execution_pass）を**実装**し、L6↔L7 の anchor を **31/88 → 88/88 に closure**（trace_symmetry(L6-L7) clean / registry_design_coverage clean を維持）。この段階は **advisory（exit 0）専用**、fail-close も ratchet block もしない（ratchet は次段以降）。
- **MVP-B（green 証跡確認後に fail-close flip）**: MVP-A で `helix doctor --gate`（G7 + VG-overview-pre-push）が**実走 exit 0（全 anchor 閉・全 detector green）**を証明してから、fail-close へ flip。2026-06-09 Codex で `helix doctor --gate` と `helix push --gate` の `G-vg-overview` 接続は完了し、2026-06-14 に `.github/workflows/ci.yml` の `detector-gate` job から `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --gate --json` を Required check 向け surface として配線した（全体 `helix doctor --gate` は `.helix/` project-state に依存し fresh checkout で常時 red になるため、CI は vg_overview.overall_clean のみを fail-close 評価する subcommand 形式を使う）。L2-L10 は explicit `ui_absent` waiver を VG-overview が読む。strict full-flow / right-arm gate は carry。
- **着手前提**: anchor が 31/88 のまま G7 を fail-close 化すると CI 即 red（「今 green な分のみ昇格」原則に反する）。必ず A→B の順。

**次段**: G8/G9/G12/G14 を ratchet → requirement_drift fail-close → 全 pair strict（G9 ST 実行 gate、L5-L8 deferred 等の既知 gap 解消後、`--strict-vmodel-pair-freeze` 系）。

DDD ratchet は `check_bc_anti_corruption` / `check_bc_mode_coverage` の 2 check を `G-vg-overview` の `required_clean.ddd_bc_coverage` に接続し、green の間は fail-close とする。
`glossary_coverage` は implementation_gap 7 件が残るため warn-only を維持し、`required_clean` へは接続しない。

**push 接続**: `cli/lib/push_gate.py` は個別 detector を持たず、VG-overview 共通 runner を `G-vg-overview` として呼ぶ。default `helix doctor` の出力・exit code は不変（公開 API 非破壊）、`--gate` のみ VG-overview pre-push を fail-close 評価する。

## 6. ゲート（決定論的 static チェック、派生 adapter）

`gate-checks.yaml`（template + project）の static はシェルコマンド（exit 0 = pass）。**正本でなく `GatePolicy`/`DetectorReport` からの派生 adapter（matrix compile 生成物）として扱う**。巨大 shell を足し込まず、`helix-gate` / `helix doctor --gate` / `push_gate` が同一 runner を使う構造へ寄せる。

| ゲート | static チェック例 |
|---|---|
| G0.5 | 企画突合（企画書/D-REQ-F/D-ACC 存在・TODO 残存なし・解像度） |
| G2 | plan_schema.py g2-check / 設計書 TODO / ADR 代替案 |
| G4 | helix-gate-api-check |
| G5 | visual-checks（desktop / tablet / mobile.png） |
| G3 / G6 / G7 / G9 | 各 static シェルコマンド群（**proxy grep → §2/§3 detector へ移行**） |

いずれも fail-close。`helix-gate --static-only` で AI を呼ばずに実行できる。

## 7. 機械 vs AI の境界

| 機械（static / detector） | AI（ai-only） |
|---|---|
| detector 判定、成果物存在、trace 整合、test 実行 pass | 設計の良し悪し |
| schema、命名、依存充足、anchor 充足 | 要件の解釈・抽出 |
| 数値品質（カバレッジ、コントラスト比、差分率） | semantic gate（orphan/excluded 妥当性）・レビュー判断 |

Scrum を除く全モードは、入口分類（size / drive / kind）が決まれば、機械側だけで工程を進行・検証できる。semantic gate のみ AI/人が担う（verification-strategy §11.2 / §14）。

## 8. 退化防止

ゲートは **Forward の通過条件**であって独立タスク台帳ではない。未完作業は新 Phase/ロードマップでなく「該当 L-pair の failed/pending gate evidence + deferred finding」に帰属させる。「常時目指すロードマップ」への再肥大化を構造的に防ぐ。

実効化の static check 候補（TL P3、後続実装）:
- `deprecated Process を新 Action の parent_process にしない`（plan_validator 拡張）。
- `process-scope PLAN の新規起票時に既存 Forward L-pair gate evidence への帰属を要求`（roadmap 的 umbrella の再生成を block）。
- `contains_action_plans が deprecated process を指さない`。
