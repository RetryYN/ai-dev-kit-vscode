---
plan_id: process-2026-06-21-ut-tdd-adoption-machine-precision
title: "Process Plan: UT-TDD フォーク採用 — 人間ゲートでなく自動開発精度を上げる機械検出群の逆輸入（分離設計）"
plan_scope: process
workflow_chain: "fork 調査(research-memo, 完了) → 本 Process 確立（orientation: 自動開発精度・人間ゲート不採用・GitHub AI-safe・検証二層成立(定量∧定性)+FE ブラウザ+実行検証 を分離宣言） → GOAL-C-RIGHTARM-FULLCLOSE 着地待ち（add-feature count-pin ripple 回避） → 着地後に add-feature 起票(substance lint: review-guard / red-first-tdd-evidence / descent-provenance / header-count-drift + 定性機械保証: review-evidence-enforce(#4) + FE: fe-browser-verify + AI-safe GitHub: escalation-stale / branch-protection-emit) + audit YAML 件数同期 → detector/workflow 実装(Codex se 委譲) + doctor subcheck 配線 → fail-close 昇格(advisory→required)"
kind: planning
layer: L7
process_layer: L7
drive: be
status: draft
status_note: "2026-06-21 起票。fork 調査→orientation/要件を §1.5-§1.16 に設計。TL adversarial review(changes_required)→§1.17 で P1 minimum に縮約。**ユーザー指示で全面設計見直しを先行・完了(§1.18 + [design-review](../../research/2026-06-21-no-leak-foundation-design-review.md))**: §1.5-§1.17 を 5 cluster で実コード検証 → foundation 3 点が穴と判明(F1 登録自動化不在/F2 gate 時実行 bypass/F3 定性レビュー改ざん可能)、§1.6 の定量∧定性∧実行 AND は現状未成立。§1.7 table を honest 訂正(②強→部分/⑤弱→未実装)。**次 = foundation(F1/F2/F3)の設計確定 → leak-class(F4/F5/F6)**。**F3(review-evidence detector)を LANDED(commit)**: 実装+7UT pass + source_scan allowlist 登録で vg_overview clean(10 passed)。clean landing が F1 をブロック実証した上で(design-review §7: counted add-feature PLAN は GOAL-C 単一 objective audit 破壊 / 新 code は source_scan 未登録で unclean)、**ユーザー指示『整備して進めろ』で GOAL-C 停止下に detector+test+allowlist 登録を commit**。deferred は counted add-feature PLAN の紙のみ(count pin×16 + objective 分類、F1/GOAL-C 後)。allowlist 登録自体が F1 が消すべき税の実例。"
tl_review: changes_required  # ①adoption 優先度=tl-advisor(2026-06-21 decision=passed)「条件付き推奨」。②設計 adversarial review=tl-advisor(2026-06-21 decision=changes_required): AI-TL 自己参照/AND の size 比例化/§1.16 帰属残差/reviewer 校正の外部接地/共有 state 論理 resource contract/退化防止/security・Loop3 別 PLAN を指摘 → §1.17 反映、scope を P1 minimum へ絞る。P0/P1 反映後に再 review 要。
created: 2026-06-21
owner: PM
forward_return: "採用確定 detector を HELIX 既存検出群(anchor_quality / vg_overview / plan_lint / review wrapper)へ統合し、AI 自動開発(Opus 全委譲 + Codex/PMO)の出力精度を機械で締め上げる状態へ収束。最終 = 実装着地の合格が『定量 detector green ∧ 定性 LLM レビュー genuine pass(#4) ∧ (FE なら)ブラウザ検証 pass ∧ 実行 green 証跡 ∧ no-leak 5機構(DB登録完全/設計実装テスト0漏れ/非デグレratchet/依存0漏れ/表記ゆれ0)』の AND になり、その範囲でのみ §1.5 の AI 駆動(人間サインオフ置換)を許す。#7/#1/#3/#4/#6 + FE browser + no-leak(#9 dependency-graph/#5 term-consistency/db-projection-meta) + AI-safe GitHub が doctor subcheck/CI として fail-close 配線。人間チームゲート(UT-TDD #10: CODEOWNERS/PO-TL-QA サインオフ)は HELIX 路線から除外（単独 AI-PM 前提を維持）。"
contains_action_plans: []  # F3 review-evidence detector は実装+test 済(cli/lib/review_evidence_checks.py + 7 UT)。だが formal counted add-feature PLAN は GOAL-C objective close 後へ stage(§1.19: F1 登録 foundation の objective-collision)。staged PLAN 本文 = design-review §7。
agent_slots:
  - role: se
    slot_label: "SE — detector 実装(Codex 委譲): review_guard / red-first frontmatter 検証 / descent provenance / header-count-drift"
  - role: tl-advisor
    slot_label: "TL — #3 descent provenance の gate 契約変更(ADR/adversarial-review)・各 detector の公開API/exit 契約・誤爆境界の adversarial check"
generates:
  - artifact_path: docs/research/ut-tdd-fork-adoption-research-memo.md
    artifact_type: markdown_doc
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - docs/research/ut-tdd-fork-adoption-research-memo.md
  - HELIX-workflows/helix-process/automation-gate-map.md
  - docs/plans/process/process-2026-06-08-verification-forward-gate.md
  - cli/lib/anchor_quality.py
  - cli/lib/tests/test_boundary_count_drift.py
---

# UT-TDD 採用 — 自動開発精度の機械検出群 逆輸入 Process（分離設計）

> ユーザー方針（2026-06-21）「こっちは人間ゲートより自動開発の精度を上げる運用で分離設計してくれ」を受けた Process。UT-TDD（HELIX の TS/Bun フォーク=チーム運用版）から、**人間チームゲートでなく機械検出を逆輸入**し、AI 自動開発（Opus 全委譲 + Codex/PMO）の出力精度を締め上げる。fork 調査の正本は [research-memo](../../research/ut-tdd-fork-adoption-research-memo.md)。

## 1. orientation（設計原則・分離宣言）

1. **人間ゲートは採らない**。UT-TDD の 3 層人間チーム（コア TL/QA/UIUX = 判断）、gate↔人間役割固定（G1/G3/G7/G11=PO、G4/G5/G6=TL）、CODEOWNERS 強制（src→TL / tests→QA / docs→PO）、人間サインオフ gate は **HELIX 路線から除外**。HELIX は単独 AI-PM（Opus 全委譲）前提を維持する。
2. **機械検出で AI 自動開発の精度を上げる**。採用するのは「AI が書いた成果の中身が伴うか」を機械で締める detector 群。レビューの主語も人間でなく AI（tl-advisor / pmo / Codex cross-review）であり、その AI レビューの健全性を機械で守る。
3. **既存系統から分離**。本 Process は verification-forward-gate process（GOAL-C 右腕 full-close）や GOAL-C handover とは別系統。子 Action は本 Process を parent_process にし、件数 ripple と handover 混入を避ける（§5）。
4. **TS 機構を丸ごと移植しない**。TS/Bun 書き換え（ADR-001）・central UI（ADR-005）・Windows PowerShell は移植しない。AST 検査の発想のみ Python `ast` で再現（pytest 解析は `cli/lib/anchor_quality.py` が実証済み）。
5. **GitHub 運用ルールも AI が安全に開発できる形にする**（ユーザー方針 2026-06-21）。AI-safe GitHub = ①AI の git 操作は機械 gate で境界づける（gate-driven push 7 gate、raw-push guard deny）②危険な外向き操作（PR merge / release / tag / force-push / branch protection 適用）は AI 単独不可・人間確認 ③詰まり/失敗状態（stale handover / 右腕 CI fail / 未 close の Forward 逸脱 Issue）を**自動で surface**し silent rot を防ぐ ④AI は authz（branch protection）を**適用せず emit のみ**。①②④の中核は HELIX 既存（[github-operations.md](../../../HELIX-workflows/helix-process/github-operations.md) §2.1/§3.5、raw-push guard、main auto-push 不可）で充足。**不足は③の自動 surface（escalation-stale）と④の emit script** → 本 Process で補う。

## 1.5 AI 駆動境界の不変条件（ユーザー要件 2026-06-21）

> 「要件定義まで済んだら基本的には AI 駆動で進むようになっていないといけない」。本 Process はこれを**検証可能な不変条件**として扱う。

- **人間境界はこの3点のみに置く**: ①上流（L0-L3 = 要件/計画の凍結承認）②高リスク escalation 例外（認証/認可/決済/PII/secret/本番影響/schema migration/破壊的データ操作/外部 API・インフラ）③最終外向き（G11 RC 判定 / G12 受入 / PR-merge-release）。
- **L4 設計 → L9 検証は AI 駆動**: 機械 gate（substance lint #1/#3/#6 + anchor_quality + vg_overview + fn_ut_pair）+ AI-TL レビュー（tl-advisor / pmo / Codex cross-review、その健全性は #7 review-guard が機械保証）で自律前進する。人間 TL の明示サインオフを前進条件にしない。

**現状 gap（pmo-helix-explorer 実証 2026-06-21、要是正）**:
1. **境界が L3 でなく L6 にある**: `skills/tools/ai-coding/references/gate-policy.md` が G4/G5/G6（L4-L6 設計凍結）の判定者に**人間 TL/PM を残す**（gate-policy.md:218/235/248）。→ 要件後すぐ AI 駆動にならない。**是正**: L4-L6 設計凍結の判定者を「人間 TL」から「**AI-TL(tl-advisor) + 機械 substance gate**」へ正式置換。gate-policy 改定 = 中核 policy 変更のため **ADR + adversarial-review 必須**（本 Process スコープ。S/M/L サイジング別の人間 escalation 条件は②に限定して残す）。
2. **空洞 gate（劣化）**: G1/G8/G12/G13/G14 が未実装で機械 block 無し（automation-gate-map §0 既知 drift）。→ 「人間も機械も止めない」通過チェック不在。**是正**: 機械 fail-close で埋める。G8/G9/G12/G14 は [verification-forward-gate process](process-2026-06-08-verification-forward-gate.md)（GOAL-C 右腕 full-close）が担当中 → 重複させず連携。G1（要件凍結）の機械化は本 Process で要否判断。

→ この2点を閉じて初めて「要件後 = AI 駆動（人間境界は①②③のみ）」が機械的に成立する。machine-precision detector 群（#7/#1/#3/#6）は、L4-L6 で人間 TL サインオフを AI-TL+機械トラストに置換するための土台でもある。

## 1.6 検証成立の不変条件（定量×定性 両成立 + FE ブラウザ + 実行検証、ユーザー要件 2026-06-21）

> 「機械ゲートだけだと漏れる。機械ゲートの定量チェックと LLM レビューの定性チェックを両方成立させないといけない。フロントはブラウザの検証が必須。やったっぽいじゃなく検証して確実に。じゃないと存在価値のない実装をして全て破棄することになる」。

AI 駆動（§1.5）が「人間サインオフ無し」で成立するのは、**検証が以下を全て満たす場合に限る**。一つでも欠ければ AI-TL 置換は不可（人間境界に戻す）。

1. **二層成立（定量 AND 定性）= 合格条件**: ①定量（機械 detector: vg_overview / fn_ut_pair / anchor_quality / substance lint #1/#3/#6、fail-close）**かつ** ②定性（LLM レビュー: tl-advisor / cross-agent、worker≠reviewer）。**どちらか単独 green では合格にしない**。HELIX 既存 doctrine（[verification-strategy §10/§11.2](../../v2/L1-requirements/helix-workflows-verification-strategy.md)『`detector_clean(必要条件) AND semantic_gate_pass(十分条件)`』『coverage 100% 単独 pass 禁止』『両者は相互ガードし合う。単独運用はどちらも危険』）を**機械強制まで引き上げる**。
   - **gap（実証 2026-06-21）**: 定性側は evidence schema（§14 semantic_gate）と doctrine はあるが、**「LLM レビューが genuine に行われ合格したか」を機械で保証する detector が不在**（cli/lib に review_evidence subcheck 無し、trace_symmetry / vg_overview のみ）→ TL/PM 任せ＝skip/偽装し得る。**是正 = #4 review_evidence enforcement（worker≠reviewer + review_kind=cross_agent + tests_green_at≤reviewed_at）を P1 昇格**（UT-TDD `review-evidence.ts`）。#7 review-guard（レビュアーが副作用を出さない）と対で「定性が genuine に成立」を機械保証。
2. **FE ブラウザ検証必須**: FE/画面に触れる成果は、**実ブラウザでのレンダリング検証 + visual/a11y を L10 必須 exit** にする。unit/contract テストだけで FE を「完了」にしない。
   - **gap（実証）**: HELIX は infra（`cli/scripts/setup-playwright.sh` / `setup-axe.sh` / [fe-detector-spec](../../../HELIX-workflows/helix-process/fe-detector-spec.md) の visual-regression / a11y-regression / design-token-drift = L10 機能ゲート）を持つが、**L2↔L10 FE detector gate は未実装（verification-strategy §14『残』）** → FE がブラウザ検証なしで通過し得る。**是正 = FE ブラウザ検証（実レンダ + visual + a11y）を機械強制 exit 化**（本 Process スコープ）。
3. **実行検証（theater 禁止）**: 「やったっぽい（trace=ID 紐付けだけ）」を弾き、**実行 green 証跡（test_execution_pass）**を要求。G7 は anchor_quality（no-op / marker-only / skip-xfail を弾く）+ exec-pass で達成済。G8/G9/G12/G14 の exec-pass wiring は [verification-forward-gate process](process-2026-06-08-verification-forward-gate.md)（GOAL-C）で進行中 → 連携。

> 帰結: 「存在価値のない実装の全破棄」を防ぐ＝**実装着地の合格を「定量 detector green ∧ 定性 LLM レビュー genuine pass ∧（FE なら）ブラウザ検証 pass ∧ 実行 green 証跡」の AND** にする。この AND が成立する範囲でのみ §1.5 の AI 駆動（人間サインオフ置換）を許す。

## 1.7 「絶対に漏らさない」5 機構（no-leak 不変条件、ユーザー要件 2026-06-21）

> 「DB への自動登録 / 設計・実装・テストの漏れを絶対に防ぐ / 絶対にデグレさせない / 絶対に依存関係を漏らさない / 絶対に表記ゆれを起こさない」。
> **「絶対」の定義**: 人間の注意力に依存せず **機械 fail-close で silent leak をゼロにする**（漏れは必ず surface し前進を止める）。baseline ratchet で一度閉じた漏れは戻さない。100% の数学的保証ではなく「黙って漏れることが構造的に起きない」を指す。

| # | 機構 | HELIX 現状（実証 2026-06-21） | gap 是正（本 Process） |
|---|---|---|---|
| ① | **DB 自動登録**（code/test/design/PLAN/contract/skill を漏れなく登録） | **部分（§1.18 で訂正）**: PLAN は hook 自動 / score・feedback・handover も hook 自動。**だが design/functional registry は手動 markdown(functional-registry.md) seed + ID のみ、設計定義は未登録**。source_scan_vs_registry(unregistered=0) ratchet はあるが登録が手動＝前段に穴 | **設計見直し対象（§1.18）**: ファイル名自動登録の code/doc/test 拡張 + 設計定義の構造化登録。+ DB projection 完全性 meta-test |
| ② | **設計/実装/テストの漏れ防止** | **部分（[design-review §2](../../research/2026-06-21-no-leak-foundation-design-review.md) 訂正）**: fn_ut_pair/vg_overview/vmodel_pair_freeze は強いが、**期待集合の登録が①で部分手動 → 0 漏れの前提が崩れる**。requirement_drift L7 が gate 外（B-2） | 登録 foundation 確定（F1）後に hardening。逆ピラミッド P0 明示 + descent-obligation #3 |
| ③ | **デグレ絶対防止** | **部分**: changed_files / requirement_drift / 各 baseline（anchor / boundary_count）ratchet | change-impact 推移的回帰 #9（source 変更→依存 module の test 未更新を検出）+ 全 detector baseline 単調減少 ratchet 統一 |
| ④ | **依存関係 漏れ防止** | **部分**: plan_dependencies / plan_dependency_gate(reciprocal requires/blocks) / dependency_cycle_checks（**PLAN 粒度のみ**） | **コード粒度 AST import グラフ**（UT-TDD dependency-drift + ADR-002 dependency-direction auto-map）= module 境界違反・循環をコードレベルで検出 |
| ⑤ | **表記ゆれ 絶対防止** | **未実装（[design-review §2](../../research/2026-06-21-no-leak-foundation-design-review.md) で「弱」より下方訂正）**: 中核 `check_ubiquitous_language` が **spec-only**（concept §12.2 宣言だが実装 0、C-1）/ `grep_pattern` は **dead code**（doc scan 未接続）/ BC 越境は **name-aliased**（C-2）/ rule-drift **不在**（C-3） | **F4**: check_ubiquitous_language 実装（dead grep_pattern を doc scan へ接続）+ BC 越境 aliasing 解消 + rule-drift（adapter marker 一致） |

→ §1.6 の合格 AND に **①〜⑤ の no-leak gate も合流**: 実装着地は「定量 ∧ 定性 ∧ FE ∧ 実行 ∧ **DB 登録完全 ∧ 設計/実装/テスト 0 漏れ ∧ 非デグレ(ratchet) ∧ 依存 0 漏れ ∧ 表記ゆれ 0**」を全て満たして初めて合格。

**design-review 後の honest 訂正（2026-06-21、[全面レビュー](../../research/2026-06-21-no-leak-foundation-design-review.md)）**: ①〜⑤ は当初「①部分/②強/③④部分/⑤弱」と評価したが、実コード検証で **foundation 3 点（F1 登録自動化・F2 gate 時実行証跡・F3 定性レビュー健全性）が部分手動/bypass/改ざん可能**と判明。特に **§1.6 の「定量∧定性∧実行」AND は現状成立していない**（定性 `tl_review=approve` は手書き文字列で改ざん検知不可（D-1）、実行は push gate/CI が `HELIX_DOCTOR_SKIP_EXEC_TESTS=1` で gate 時スキップ（B-1/D-2））。よって「強い①②維持」は撤回し、**foundation（F1/F2/F3）の設計確定を最優先**、その後に leak-class（F4 表記ゆれ / F5 workflow 強制 / F6 依存方向）。詳細・fix 優先順・実装 sequencing は design-review §2-§4。

## 1.8 背骨 = DDD + TDD の機械強制（ユーザー方針 2026-06-21「そのための DDD と TDD だろ」）

§1.6 の二層成立と §1.7 の no-leak 5 機構は、新発明ではなく **DDD と TDD という 2 方法論を「規律頼み」から「機械 fail-close」に変えたもの**。HELIX は両方を既に doctrine として持つ（DDD: [HELIX_CORE §5](../../../helix/HELIX_CORE.md) ユビキタス言語 SSoT / Bounded Context / anti-corruption。TDD: HELIX_CORE §0 テストファースト）が、enforcement が散在。UT-TDD はこれを `ddd-tdd-rules.ts`（domain-boundary / invariant-test-trace / red-first / oracle-strength / integration-gwt / unit-oracle-substance）の**統合 lint** にしていた。HELIX もこの背骨で detector を整理する。

| 方法論 | 何を保証するか | 対応する不変条件 | 機械強制 detector |
|---|---|---|---|
| **TDD**（テストファースト） | 設計→テスト→実装の順、全振る舞いにテスト、回帰即検出、theater 禁止 | ②設計/実装/テスト0漏れ・③デグレ防止・実行検証（§1.6③）| #1 red-first / #2 anchor_quality(oracle) / fn_ut_pair(FN↔UT 1:1) / #3 descent / test_execution_pass / ③ ratchet |
| **DDD**（ユビキタス言語+境界） | 1 用語 1 意味、Bounded Context で責務分離、依存方向の規律、ACL | ⑤表記ゆれ0・④依存0漏れ | ⑤ glossary SSoT + propagation/doc-consistency / ④ dependency-drift(AST)+ADR-002+domain-boundary |
| **両者の意味遵守** | 構造が green でも「DDD/TDD の魂」を守れているか | 定性 LLM レビュー（§1.6①）| #4 review_evidence(cross_agent) — LLM が ubiquitous language 遵守・テストが契約を検証しているかを意味判定 |

→ つまり: **定量 gate = DDD/TDD の構造を機械検証、定性 gate = DDD/TDD の意味（魂）を LLM 検証**。両成立 AND（§1.6）= 「DDD と TDD を構造でも意味でも守った」の機械的定義。①DB 自動登録は、この DDD（登録=モデルの台帳化）と TDD（テスト資産の台帳化）の成果を漏れなく DB へ写す土台。本 Process の detector 群は全て「DDD 強制」か「TDD 強制」のどちらかに分類し、UT-TDD `ddd-tdd-rules` 相当の統合 spine へ寄せる。

## 1.9 登録・列挙層 = 検出の前提（駆動モデル + PLAN 起票 + 工程表、ユーザー方針 2026-06-21）

> 「駆動モデルやプラン起票も工程表も、そもそもこれらを機械的に検出するための機構」。

detector（§1.7/§1.8）は「**期待集合に対する漏れ**」を計算する。その**期待集合を定義しているのが 駆動モデル + PLAN 起票 + 工程表**。これらは検証と別物ではなく、**検出を成立させる登録・列挙機構**。HELIX_CORE §0/§2/§3 の絶対原則そのもの: 「**V-model へ戻さなければ DB コアは動かない**」=「**登録されない作業は trace/drift/coverage の対象にならない＝不可視＝最大の漏れ**」。だから「絶対に漏らさない」の根は、検出器でなく**全作業を登録・列挙に載せること**にある。

| 層 | 役割（何を機械検出可能にするか） | HELIX 機構 | UT-TDD 対応 |
|---|---|---|---|
| **駆動モデル** | 逸脱・既存・障害・探索を含む**全作業を V-model に載せ** `forward_return` で戻す → off-V-model の不可視作業をゼロに | recovery_workflow_engine / workflow_dsl_parser / plan_validator(forward_return・parent_process 検証) / forward-return-discipline | drive-model-passage.ts / drive-db-registration.ts |
| **PLAN 起票** | 各作業単位を frontmatter trace（kind/layer/drive/generates/dependencies/forward_return）で**登録** → 「何を作る/作った」を機械可読化 | plan_registry / plan_lint / plan_validator | impl-plan-trace.ts |
| **工程表/列挙** | 期待成果の**完全集合を列挙**（FN↔UT、成果物）→ 「何が無いか（漏れ）」を計算可能化 | l7_worklist(read-only) / functional_registry / `.helix/task-plan.yaml`(WBS) | roadmap-registry / fr-roadmap-coverage |

→ **保証の構造**: 登録完全（全作業が 駆動モデル経由で PLAN 登録 ∧ 期待集合が工程表に列挙）**∧** 検出ゼロ漏れ（§1.7/§1.8 detector）。**登録を迂回した作業は detector でも捕まらない**＝真の穴。よって no-leak の根 = 登録・列挙層の完全性。

**HELIX gap（実証 2026-06-21）**: 検出層は厚いが、登録完全性の機械強制が弱い 2 点 →
- **impl-plan-trace**（UT-TDD `impl-plan-trace.ts`）: 全 impl が**登録 PLAN に紐づく**（コードが PLAN を迂回して着地していないか）。HELIX は vg_overview(source⊆design) はあるが impl⊆PLAN の専用 detector が弱い。
- **drive-model-passage**（UT-TDD `drive-model-passage.ts` / `drive-db-registration.ts`）: 全駆動 workflow が **passage + forward_return を DB 登録**したことの検証。

**caveat（HELIX 既決、採用しない）**: UT-TDD の **roadmap-registry を「常時目指す roadmap 台帳」として採用しない**（HELIX は 2026-06-08 に 6-phase roadmap 常時追跡を**アンチパターンとして廃止**。CLAUDE.md「退化防止」）。工程表 = **bounded な per-L PLAN 列挙 + read-only l7_worklist**。fr-roadmap-coverage 相当は「過去に定義した期待の被覆チェック」としてのみ可（standing target 台帳にしない）。

## 1.10 ワークフロー機械強制 + 駆動モデル選択式強制（ユーザー方針 2026-06-21）

> 「ワークフローはそのために存在して、ワークフローは機械的に強制されないといけない。駆動モデルの連動も選択式で強制されるべき」。

§1.9 の登録・列挙層は、**ワークフローが機械強制されて初めて非迂回になる**。ワークフロー（L0-L14 Forward + 9 駆動）が advisory だと、work が workflow を迂回 → 登録されない → 不可視 → 漏れ。よって**ワークフロー自体を fail-close で強制**し、**逸脱時の駆動モデル選択・連動を選択式で強制**する。

**要件 A: 工程ワークフロー機械強制（迂回・スキップ不能）**
- 各 L の entry/exit を gate で fail-close: 「前段 exit + 必要入力 + freeze」なしに次段へ入れない／gate pass なしに freeze・前進できない（HELIX「検証=Forward 内在ゲート」= verification-forward-gate process と同一方針）。
- HELIX 機構: entry_helper / deliverable_gate / gate_policy_helper / push_gate。**gap = G1/G8/G12-G14 hollow**（§1.5 gap②）→ stage を gate なしで freeze し得る。完全 fail-close 化は GOAL-C / verification-forward-gate process が担当 → 本 Process は重複させず連携。

**要件 B: 駆動モデル選択式強制（逸脱→選択→連動を強制）**
- 逸脱検出時に、有効な駆動モデル 9 種（Forward/Reverse/Discovery/Scrum/Add-feature/Refactor/Retrofit/Incident/Recovery/Research）の menu から**選択を強制**し、選択した駆動が `workflow_chain` + `forward_return` + Process⊃Action を持つことを検証、無ければ前進を block。連動（例 Discovery→Reverse / Recovery→Reverse / Scrum→Reverse）も **valid-link として強制**（任意連鎖を許さない）。
- HELIX 機構: route_engine / scrum_to_reverse_routing / detection-routing.md / deviation-plan-map.md / plan_validator(process layer)。**gap**:
  1. 逸脱時の **forced selection が convention 寄り**（detector が逸脱を検出 → 実際の drive 選択は人/AI 任せ、post-hoc に plan_validator が検証）。→ **route_engine を advisory から fail-close gate へ**（逸脱検出後、有効 drive PLAN が登録されるまで該当 work を block）。
  2. **drive-model-passage 専用 detector が弱い**（§1.9 で採用済 = 全駆動が passage + forward_return を DB 登録）。
  3. **chain-validity 静的検証が候補止まり**: `deprecated-process-not-parent`（deprecated Process を新 Action の parent にしない、CLAUDE.md 既出候補）+ `workflow_chain` valid-link 検証 → 実装して fail-close。
- 参照: UT-TDD `drive-model-passage.ts` / `scrum-reverse.ts` / `workflow/contracts.ts` / `workflow/readiness.ts`。

→ これで「workflow を迂回した work」「駆動を選ばず逸脱したまま進む work」「無効な駆動連鎖」が**構造的に不可能**になり、§1.9 登録層の非迂回性が担保される。ワークフローは「規律で守る運用ルール」から「迂回不能な機械強制機構」になる。

## 1.11 粒度ペアリング = 機械的 pair-closure の前提（HELIX 既存の強み）

> 「機能一覧も関数レベルや単体テストレベルに、強制と粒度を対にしているのもその理由」。

検出が機械的に閉じるのは、**設計と検証が同じ粒度**のときだけ。機能一覧（functional-registry）を**関数粒度**で列挙し、単体テストを**関数粒度**で対にする（FN↔UT 1:1）から、pair が機械で閉じる。粒度がズレる（module 設計 vs 関数テスト）と対応が閉じず **片肺・カバレッジ薄化 = 漏れ**。これは §1.9 登録・列挙層の「粒度」属性であり、§1.7②（0 漏れ）・§1.8 TDD（fn_ut_pair）が実際に閉じる前提。

| pair | 粒度 | HELIX 強制 |
|---|---|---|
| L6↔L7 | **関数/単体粒度**（DbC: requires/ensures/invariant、関数 1 個 = UT 1 個） | fn_ut_pair_coverage（FN↔UT 1:1）+ registry_design_coverage(unknown/missing/wrong_layer=0) |
| L5↔L8 | module/結合粒度 | MOD-*/IT-*（design_id 必須） |
| L4↔L9 | system/component 粒度 | NFR-*/IF-*/ST-* |

**HELIX 状態 = 強い（gap でなく強み）**: 絶対原則 [HELIX_CORE §1](../../../helix/HELIX_CORE.md)「粒度も対称」「対は同時凍結・片肺を完了にしない」+ [HELIX-process §粒度ペアリング原則](../../../HELIX-workflows/HELIX-process-L0-L14.md)「粒度を粗く書くと機械的に閉じない（特に L6）」+ fn_ut_pair detector。却下解釈 A（全 registry entry を FN/UT 化 = template/workflow まで単体テスト化）は粒度誤りとして明示排除済。これは HELIX_CORE §0「原則を文章でなく仕組みで守らせる」の中核 → 本 Process では **維持・hardening**。UT-TDD 対応（fr-unit-coverage / l6-fr-coverage / ddd-tdd-rules unit-oracle-substance）は確認用で、逆輸入の主目的ではない。

→ 登録（§1.9）も検出（§1.7/§1.8）も**粒度が対称でなければ機械的に閉じない**。だから機能一覧を関数粒度に強制し、設計⇔検証の粒度を対にする = 「絶対に漏らさない」を**粒度の次元**で担保する。

## 1.12 生成的ペイオフ = 分離・強制 → 文脈の機械制御 → 専門スキル注入 → 専門性向上（HELIX 既存の強み）

> 「L 単位や駆動モデルに分離し強制化することでコンテキストを機械的に制御して専門スキルを注入して専門性を上げる機構を内包できる」。

§1.5〜§1.11 の enforcement は「漏らさない（守り）」だけが目的ではない。**L 単位 + 駆動モデルに分離して強制する（§1.10）と「今どこか（current L + drive）」が機械的に確定**する。この確定した position が**生成的ペイオフ**を生む:

```
enforcement(§1.10) が position(L+drive)を確定
  → vmodel-semantics の per-L 注入セットが doc/skill/command/agent/orchestration を一意に決定
    → context_guard(CONTEXT_BUDGET/CONTEXT_PROFILE) が予算内で relevant のみ注入（文脈の機械制御）
      → AI がその L+drive の「専門家」として振る舞う（specialist 化）
        → 専門性向上 + context bloat 削減（無関係 skill/doc を注入しない）
```

つまり: **漏れ防止（no-leak）と専門化（specialization）は同じ背骨（L/駆動 分離 + 強制）から出る** = 1 つの構造の二重利用。enforcement は「漏らさない」と「専門性を上げる」を同時に実現する。

**HELIX 状態 = 強い（gap でなく強み）**:
- [layer-context-injection.md](../../../HELIX-workflows/helix-process/layer-context-injection.md): 注入は helix-context が担い、L 別責任は vmodel-semantics の owner_role が定義。**L 単位の注入セット**（skill 群・推奨 command・orchestration 方式）を vmodel-semantics.yaml の各 layer に定義。
- `cli/lib/context_guard.py`（CONTEXT_BUDGET / CONTEXT_PROFILE、直近 landed）: 予算内で「selected skills / unselected skills+references」を機械制御。
- `skill_recommender` / `skill_dispatcher` / `skill_classifier` / `skill_helix_layer_audit`: スキルを L 別に推挙・配布・監査。`helix skill chain` recommender。
- 本 Process では **維持・hardening**（逆輸入の主目的でない）。UT-TDD `skills/recommend.ts` / `search/index.ts` は確認用。

→ これで設計の全体像が閉じる: **登録（§1.9）→ ワークフロー強制（§1.10）→ position 確定 →（守り）no-leak 検出 ＋（攻め）専門スキル注入 → 専門性向上**。同じ「L/駆動 分離 + 機械強制」構造が、漏れゼロ化と専門性向上の両方を内包する。

## 1.13 自己改善ループ = スキル強制 + パラメータ → 精度測定 → 改善（最終閉合）

> 「スキルの強制をすることでパラメータを仕込めば、発火率とテストの通過率やターン内のレビュー回数でスキル自体の精度が測れる。つまり自己改善のループに持っていける」。

§1.12 でスキルは機械強制で注入される。**enforcement 点が instrumentation 点**なので、パラメータを仕込めば測定データが「ただで」出る。スキル精度を 3 指標で測れる:

| 指標 | 意味 | スキル精度の解釈 |
|---|---|---|
| **発火率** | そのスキルが注入/発火した頻度 | 過少 = 推挙漏れ / 過多 = 注入ノイズ |
| **テスト通過率** | そのスキル発火時の成果の test green 率（特に初回 pass 率） | 高 = 効くスキル |
| **ターン内レビュー回数** | そのスキル発火時に要した review 反復数 | 少 = 一発で質が出る = 効くスキル |

→ **自己改善ループ**: 測定 → スキルと成果の相関（pass 率 / review 数） → improvement-backlog → 効くスキル強化・効かないスキル改訂/退役 → 再測定。これは守り（no-leak）・攻め（specialization）に続く**第3の効用 = 自己改善**で、同じ背骨（L/駆動 分離 + 強制 + 注入）から出る。

**重要（系の自己言及）**: 改善も **V-model へ戻る**（[HELIX_CORE §4](../../../helix/HELIX_CORE.md) 自動検出ループ）。測定で見つかった弱点は **PLAN として登録**され、§1.9/§1.10 の同じ登録/workflow 機械を通って改善される。自己改善は系の外でなく、**系が自分の登録・workflow で自分を改善する**。

**HELIX 状態**: 測定エンジンは**強い**（`learning_engine.py`: action_pass_rate / observation_pass_rate / quality_score、observability_helper / feedback_hook / harness_monitor / learning-engine.md / observability-metrics.md）。**gap 3点**:
1. **per-skill 精度メトリクス**が弱い（HELIX は action/observation 粒度の pass_rate。skill 粒度の「発火率 × 発火時通過率 × review 数」が無い）。
2. **telemetry-closure meta-test 不在**（測定→feedback が実際に wired か検証する仕組みが無い → 測定しても改善に閉じない穴）。UT-TDD `telemetry-closure.ts`（Skill firing parameters / Drive firing-rate / retry detection / Measurement-to-feedback loop / Improvement log を closure 必須要件として meta-test）。
3. **improvement-backlog 不在**（feedback の宛先）。UT-TDD `improvement-backlog.md` + lint。

**是正**: UT-TDD telemetry-closure + skill-evaluation + improvement-backlog を逆輸入。**caveat（HELIX 既決）**: 推測 schema を避け、**enforcement が既に出す telemetry の上に測定を載せる**（永続化要求が観測されてから schema 確定 = CLAUDE.md「DB 拡張は検証ゲートが回り永続化要求が観測されてから」）。発火率/通過率/review 数は既存 session telemetry + skill_dispatcher 発火ログから derive 可能か先に確認してから schema 化。

→ これで設計が完全閉合: **登録 → workflow 強制 → position 確定 →（守り）no-leak ＋（攻め）専門注入 ＋（自己改善）スキル精度測定→改善**。3 効用すべてが同じ「L/駆動 分離 + 機械強制」背骨から出て、改善も V-model へ収束する。

## 1.14 駆動逸脱頻度ループ = 見落とし点の信号（第2の改善ループ）

> 「ベースのフォワード駆動モデルから外れる駆動モデルは、見落としているポイントの数を示している。つまりスキルの強化部分やワークフローの改善部分がここに現れる。ここからも改善ループが派生する」。

Forward = 基準線（理想 path）。**非 Forward 駆動が発火する＝そこに Forward で見落とした点があった**という信号。§1.13（per-skill 精度）とは別の源から派生する**第2の改善ループ**。各駆動の発火は何の見落としを意味するか:

| 駆動発火 | 見落とし（overlooked point） | 改善先 |
|---|---|---|
| **Reverse** | 上流 design/requirement 被覆漏れ（既存コードから設計復元 = 設計が先に無かった） | 設計スキル強化 + Forward L1-L6 工程 |
| **Incident** | 検証漏れ（defect が verification をすり抜け） | テスト/gate 強化（§1.6/§1.7） |
| **Recovery** | guardrail/workflow 漏れ（AI 逸脱を止められず） | workflow 強制強化（§1.10）+ guardrail スキル |
| **Discovery** | 要件明確性漏れ（不確実性が残存） | 要件スキル + L1-L3 工程 |
| **Refactor** | 構造債（設計品質劣化） | 設計品質スキル + DDD 境界（§1.8） |
| **Add-feature / Retrofit** | 初期スコープ/移行設計漏れ | スコープ設計スキル |

**集計指標**: 駆動発火率を **(駆動種別 × L工程 × 領域)** で集計 → クラスタが「どのスキルを強化」「どの工程を改善」を直接指す。**North Star**: 駆動逸脱率が時間とともに**減る** = ハーネス成熟（上流で捕まえ、escape が減る）。増える領域 = その工程/スキルが弱い。

**enforcement との連動（同じ背骨）**: §1.10 が forced drive selection + passage 登録するから、**全逸脱が registered/typed event** = 発火率が「ただで」測れる（§1.13 と同じく enforcement = instrumentation）。改善先は improvement-backlog → PLAN 化 → **Forward 改善**（V-model 収束）→ 次回同種 work が Forward に乗る（逸脱率低下）。

**HELIX 状態**: per-event surface は**強い**（[github-operations §2.1](../../../HELIX-workflows/helix-process/github-operations.md) Forward 逸脱→Issue、Issue↔PLAN、forward_return 追跡、drive 登録 §1.9）。**gap**: drive 発火率の**集計→改善信号化**が無い（raw Issue/PLAN はあるが (種別×工程×領域) 集計・retry/bottleneck 検出が未実装）。**是正**: UT-TDD `telemetry-closure` の Drive firing-rate / retry detection / bottleneck detection を逆輸入（§1.13 の telemetry-closure と同一機構に同居）。caveat: 推測 schema 回避、既存 Issue/PLAN/forward_return 登録から derive。

→ **2つの自己改善ループ**が両方とも enforcement telemetry から派生する: **Loop1（§1.13 per-skill 精度: 発火率×通過率×review数）** + **Loop2（§1.14 駆動逸脱頻度: どこで Forward を外れたか）**。前者は「スキルが効くか」、後者は「どこを見落としたか」。両方 improvement-backlog → V-model 収束。

## 1.15 データベース = 能動的トレース脊椎 + Reverse 資産化（ユーザー方針 2026-06-21）

> 「Reverse は実装とドキュメントの差異を是正して実装を資産にできる。DB は更新履歴を残し、更新有無を判定強制する機構が要る。DB は設計と実装のデグレ防止のため抽象から具体までの流れを保証する。DB から doc 場所を引ければ調査コストが激減。DB が工程表のネクストアクションを提示すれば進捗で迷わない。DB が依存関係を出せば接続漏れが防げる」。

§1.9〜§1.14 の全層は **DB に収束する**: 登録（§1.9）は DB に書き、検出（§1.7）は DB を読み、注入（§1.12）は DB に position を問い、自己改善（§1.13/§1.14）は DB に telemetry を書く。DB は受動的台帳でなく**能動的トレース脊椎**であるべき。**Reverse** は、その脊椎の入口で「実装が doc から乖離した状態」を是正し**資産化**する（impl→design/requirement back-fill）。impl-plan-trace（§1.9）が impl-without-PLAN を検出 → Reverse が back-fill → DB に登録、というループ。Loop2（§1.14）の Reverse 発火＝設計漏れは、ここで資産化されて閉じる。

DB の能動機能（6 capabilities）と HELIX 状態:

| capability | 役割 | HELIX 状態 | gap 是正 |
|---|---|---|---|
| **③ 抽象→具体 trace 保証** | L1→L3→L4-6→code→test の縦鎖を保ち設計/実装デグレ防止 | **強**: requirement_drift（縦トレース）+ vg_overview + trace_symmetry | 維持・hardening |
| **Reverse 資産化** | impl-doc 乖離を是正し登録資産化 | **強**: helix-reverse(R0-R4+rgc) + reverse-workflow | impl-plan-trace と連動（§1.9） |
| **② 更新履歴 + 更新強制** | per-artifact 変更履歴を残し「更新すべき時に更新したか」を判定強制 | **部分**: schema version(v30)/migration/rollback + transition_history + drift_db_diff。per-artifact 更新履歴・更新強制は弱い | 更新履歴 schema + change-impact(§1.7③) と接続した更新強制 |
| **① doc locator** | DB から該当 doc 場所を引く → 調査コスト激減（grep 探索を排す） | **部分**: helix code find(code_catalog) + registry path。doc 統一 locator は部分 | 全 artifact→doc location の統一 query（委譲時の調査コスト削減に直結） |
| **next-action 提示** | position(L+drive+gate) から次アクションを算出提示 | **部分**: handover default_next_action + l7_worklist | DB 能動算出（position → next-action）。進捗迷子の解消 |
| **⑥ 依存出力** | DB から依存を出し接続漏れ防止 | **部分**: plan_dependencies(PLAN 粒度) | コード粒度 dependency 出力（§1.7④ code-dependency-graph と同一） |

**caveat（HELIX 既決、最重要）**: DB の能動機能は**推測 schema で一括構築しない**。CLAUDE.md「DB 拡張は検証ゲートが回り永続化要求が観測されてから schema 確定（推測 schema を避ける）」。§1.9〜§1.14 の enforcement/registration/telemetry が**実際に流れてから**、観測された永続化要求に基づいて段階的に schema 化する。UT-TDD `state-db`（projection-writer / migration / maintenance / drive-registration / index）は projection 再構築の型として参照（db rebuild で再投影、db-projection-coverage/ingestion で完全性）。

→ DB は「登録の宛先」から「**能動的に trace を保証し・次手を示し・依存と doc 場所を引ける脊椎**」へ。Reverse がその脊椎に乖離資産を取り込む。これで「抽象→具体のデグレ防止」「調査コスト削減」「進捗の迷い解消」「接続漏れ防止」が DB 起点で成立する。

## 1.16 帰属の訂正 + 漏れていた機構（ユーザー指摘 2026-06-21）

> 前段で「盲点」として挙げた大半は、本設計が**既に機構として持つ**もの。それを機構と認識せず「視点」として並べたこと自体が、**AI が設計を保持しきれない＝機械強制が必要な証左**（規律でなく仕組みで守らせる = HELIX_CORE §0）。正しい帰属を固定し、真に機構として追加すべきものだけを encode する。

**既存機構が答える（盲点でない、帰属訂正）:**

| 誤って挙げた点 | 実際に答える既存機構 |
|---|---|
| 過剰強制の摩擦 | **駆動モデル** — Forward の硬直から外れる＝駆動が発火する relief valve（§1.10/§1.14）。bypass フラグでなく**駆動へ routing が正**。逸脱頻度は Loop2 が測る |
| 要件の正しさ | **Discovery 駆動** — 仮説→PoC→verify→decide で不確実要件を検証（§1.9 駆動列挙に既存） |
| 時間的劣化 staleness | **依存出力（§1.15⑥）+ change-impact（§1.7③）** — 変更→依存先を伝播更新。依存を出して更新するのが答え |
| 自己マイグレーション | **db_cli version 管理 + migration（§1.15）** — schema/契約変更時の migrate 規律として運用 |
| コールドスタート | **Reverse** — 既存コード onboarding = R0-R4 back-fill（§1.15 資産化） |
| 強制の ROI/比例性 | **helix size** — サイジングで工程 skip。全タスクに全 detector は掛けない（誰もそう言っていない） |

**真に機構として追加（ユーザー指示で encode）:**

1. **LLM レビュアー校正**（→ §1.6/§1.13）: 定性 gate の reviewer 自身の **false-pass / false-fail を実測**し自己改善ループへ入れる（worker だけでなく **reviewer も測る**）。校正データで信頼できない reviewer 構成を是正。
2. **本番 runtime ログ計測を設計に内在化**（→ Loop3、§1.14 拡張）: 納品系に **observability 計測を設計時から埋め込む**（後付けでなく設計内在）。本番の実エラー/実行動/実性能を L13/L14 経由で要件へ還す外部接地ループ。
3. **並行コンフリクトを guardrail + PLAN 起票で吸収**（→ §1.9/§1.10）: serialize_after / file-conflict guardrail + PLAN の allowed_files / dependencies を **共有 state（件数 pin・registry・DB projection 等）にも適用**。boundary_count_drift 衝突はこの未適用が原因 = guardrail/PLAN が shared-state を射程に入れていない穴を塞ぐ。
4. **セキュリティを NFR として設計に内在**（→ §1.6/§1.7）: 脅威（prompt injection via 登録 artifact / supply chain / secret 流出）を **L1 NFR + security gate に当然のものとして含める**（「視点」でなく要件）。

→ 1〜4 は別 detector を増やすのでなく**既存機構（自己改善ループ / L13-14 / guardrail+PLAN / NFR+security gate）の射程を広げる**形で内在化する。

## 1.17 TL adversarial review 反映（changes_required → 修正、2026-06-21）

tl-advisor review（verdict=changes_required、「方向性 approve だが契約が機械的に閉じていない」）を反映。

**P0:**
- **P0-1 AI-TL 自己参照を契約で封じる（§1.5 補強）**: AI-TL に L4-L6 凍結を移譲する条件を gate 契約に明記 — ①**worker ≠ reviewer ≠ calibrator**（別 provider/役割）②**calibrator は固定ベンチに接地**（P1-2）③**高リスク escalation（認証/決済/PII/本番/schema/破壊的/外部API）は人間**④**gate-policy 自体の改定は人間承認**。導入は big-bang fail-close でなく **shadow → advisory → limited required → required** の段階。AI を判断主体化せず、policy・高リスク・校正の anchor は人間/固定ベンチに残す（HELIX_CORE「AI は制約内の実行者」を保つ）。
- **P0-2 AND を gate_profile で比例化（§1.6 補強）**: `定量∧定性∧FE∧実行∧no-leak` を全タスク一律でなく **`gate_profile = size × drive × risk_flags × touched_artifacts` → 各 gate の required/warn/skip** を表で定義。trivial docs 修正は最小 profile（過剰 block 回避）、critical/risk は full AND。helix size は分類器であって gate profile でないため、profile 表を ADR で確定（Sequencing①）。

**P1:**
- **P1-1 §1.16 帰属の残差を明記**: 各既存機構は問題の一部しか解かない — 駆動モデル=Forward 外逸脱に効くが **detector 誤爆/局所コスト**は別 / Discovery=**不確実性が検出された場合のみ** / 依存+change-impact=**変更伝播**で **時間劣化・外部前提失効**は別（staleness sweep は残課題） / db version=**DB schema** に効くが **detector/policy 自己更新の互換性**は別（P1-5） / helix size=**分類器**で gate profile でない（P0-2）。
- **P1-2 reviewer 校正の外部接地（無限後退の有限化）**: calibrator を自己参照にしない契約 — **既知 bad-case replay / seeded benchmark / 過去 incident replay / human spot-audit sampling / reviewer の version+prompt hash 固定 / inter-rater agreement**。校正器の正しさは「固定 golden ベンチ + 人間 sampling」に接地し、LLM で LLM を無限に測らない。
- **P1-3 共有 state を論理 resource として contract 化**: 件数 pin/registry/DB projection は file 衝突でなく **論理 resource 衝突**。`resource_id` + **version/ETag** + **single-writer or optimistic concurrency** + **transaction** + **resource-level serialize** を定義（file-conflict の単純拡張は過剰直列化 or silent overwrite を生む）。
- **P1-4 退化防止の強化**: §3 の Action を常時目標台帳にしない — **P1 minimum scope 明示 / 各 Action に exit condition / P2・P3 は別 backlog 分離 / 期限切れ条件**（§3 改訂）。
- **P1-5 security NFR と runtime Loop3 は別 PLAN（L1/L3 へ戻す）**: 両者は本番 telemetry/PII/secret/env に触れ L1 要件・L3 受入へ戻る。L7 process の一行でなく **独立 PLAN（L1 NFR 追補 + L3 受入）** として切る。

**P2:**
- 「DDD/TDD の魂」→ 機械契約語として **semantic rubric + review checklist + failure examples** に置換（曖昧語を排す）。
- 「絶対に漏らさない」→ 定義（§1.7「機械 fail-close で silent leak ゼロ」）に寄せ **silent-leak fail-close** と表記統一。
- §4 進捗の add-feature 件数を §3 起票表と同期。

**Sequencing（TL 推奨の段階導入を採用、本 Process の scope を絞る）:**
1. **契約だけ先に ADR 化**: `gate_profile`（P0-2）+ `review_evidence`（worker≠reviewer≠calibrator 含む P0-1）。
2. **P1 detector minimum**: review-guard / review-evidence-enforce / red-first / descent-provenance(advisory) の **4 本のみ第一波**（GOAL-C 着地後）。
3. **残りは telemetry 観測後に別 Process/P2 backlog**: shared-state contract / reviewer calibration / Loop3 / DB 能動化 / security NFR / no-leak #9・#5 / 登録層 impl-plan-trace・drive-passage / workflow forced-selection。
4. **AI-TL 置換は段階導入**: shadow → advisory → limited required → required。

→ 本 Process は **P1 minimum（契約 ADR + 4 detector）に scope を絞り**、残りは「観測後に派生」backlog として bounded に保つ（roadmap 台帳化しない）。

## 1.18 設計見直し（プラン起票より先、ユーザー指示 2026-06-21）— 登録 foundation の現状

> 「ファイル名だけで DB 登録されるか？ 設計書定義が登録される仕組みか？ やるべきはプラン起票の前に設計の見直しだ」。

**ADR/プラン起票を停止し、設計を先に見直す**。第一の見直し対象は全アーキテクチャが乗る**登録 foundation（§1.9）**。実コード確認（2026-06-21）の結果、ここは §1.7① で「強い」と評価したより**弱く、部分手動**だった:

| 問い | 現状（実コード、file:line） | 判定 |
|---|---|---|
| **Q1 ファイル名/パスで自動登録か** | db-auto-registration.md は**イベント駆動自動登録を設計**（hook で「人でなくイベントが書く」）。実装は**部分**: PLAN=`.claude/hooks/posttooluse-plan-auto-register.sh` 自動 / score・feedback・handover=hook 自動 / skill catalog rebuild あり。**だが functional/design registry は手動 markdown（`functional-registry.md`）を seed**（functional_registry_seed が SOURCE_DOC を読む）+ 部分 domain scan。**「作成→自動登録」は code/doc/test で未完** | **部分（PLAN自動/設計registry手動）** |
| **Q2 設計書「定義」が登録されるか** | registry_design_coverage は design_id の**存在/trace を検査するが定義の実在証明でない**（「design_id の実 doc 存在は L6/L7 doc + trace_symmetry が担保」）。設計**定義（DbC 契約・FN spec）は L6 doc に在り DB に構造化登録されない**。DB に載るのは**手動 functional-registry.md の ID 行**のみ | **ID のみ手動登録、定義は未登録** |
| Q3 登録漏れ検出 | source_scan_vs_registry(unregistered=0) + registry_design_coverage(design_id_missing/unresolved) は ratchet→fail-close。だが**登録自体が手動 markdown 依存**＝「functional-registry.md に追記し忘れる」漏れは検出の前段で起きる | 検出はあるが登録が手動＝前段に穴 |

**含意（設計上の最重要）**: §1.5-§1.17 の全機構（検出・専門注入・自己改善・DB 脊椎）は**登録が完全・自動である前提**で成立する。登録 foundation が**部分手動**なら、detector は**不完全な期待集合**に漏れを測り、「絶対に漏らさない」が根元で崩れる。**よって plan 起票より設計見直しが先**は正しい。

**設計見直しの第一項目（plan 化の前に設計を確定）**:
1. **ファイル名/パスでの自動登録を code/doc/test に拡張** — 手動 functional-registry.md 依存を排し、作成→自動 projection。db-auto-registration.md の設計意図を実装に追いつかせる。
2. **設計書定義の登録** — design_id だけでなく**定義（DbC 契約・FN spec・MOD/NFR）を構造化して DB に登録**（L6 doc から抽出 or 設計時に DB へ）。「存在/trace」から「定義の登録」へ。
3. これらの設計が固まってから §1.17 Sequencing（契約 ADR → detector）に進む。**登録 foundation 未確定のまま detector を起票しない**。

→ §1.7① の「DB 自動登録=強」評価を **「部分（PLAN 自動 / 設計 registry 手動・ID のみ）」に訂正**。登録 foundation は detector 群より**前に設計を見直す対象**。

**全面設計見直し完了（2026-06-21、ユーザー指示「全面的に見直し」）**: 登録 foundation だけでなく §1.5-§1.17 の全機構を 5 cluster で実コード検証（[no-leak foundation design-review](../../research/2026-06-21-no-leak-foundation-design-review.md)）。メタ結論 = **foundation 3 点が全て穴**:
- **F1 登録**（cluster A）: code_catalog 自動 trigger 不在（手動 rebuild）/ functional-registry 二重手動 markdown / 設計定義未登録（ID prefix 形式チェックのみ）。
- **F2 実行証跡**（cluster B/D）: push gate・CI が `HELIX_DOCTOR_SKIP_EXEC_TESTS=1` で gate 時に実行をスキップ → 「やったっぽい」を弾く前提が gate の瞬間に崩れる。
- **F3 定性レビュー**（cluster D）: `tl_review=approve` が手書き文字列・改ざん検知不可・再レビュー強制なし・semantic_gate は脆い text match。
- **leak-class**: ⑤表記ゆれ中核は spec-only（C-1）、 workflow 駆動強制は post-hoc のみ（cluster E）、依存はコード粒度循環止まり（B-3）。

→ **設計 FIX 優先順**: 第0層 foundation（F1/F2/F3）を先に設計確定 → 第1層 leak-class（F4/F5/F6）。**機械実装は駆動モデルのルールに従う**（Add-feature 駆動、pair_closure 厳守、forward_return 宣言、Codex 委譲、GOAL-C 着地後に add-feature 起票）。詳細 = design-review §3/§4。除外 = 右腕 G9/G12/G14（GOAL-C 担当）。

## 2. スコープ

### In（自動開発精度を上げる機械検出 = 本 Process が扱う）
- **#7 review-guard**（P1）: read-only レビュー subagent（tl-advisor / pmo / review 系）の working-tree 変更を before/after path 増分で検出し fail-close。AI レビューがコードに副作用を出す事故（HELIX 実害 = tl-advisor の index.md 書き戻し）を機械で封鎖。
- **#1 red-first TDD evidence**（P1）: PLAN frontmatter `red_at < green_at <= reviewed_at` 時系列検証で TDD ファーストを実効化。AI 委譲の「テスト後付け」を機械で弾く。
- **#3 descent-obligation provenance**（P1, advisory+baseline 先行）: 範囲展開被覆（`FR-L1-01..50`）と focused 引用を区別。AI が blanket range で「被覆=緑」を偽装する穴を塞ぐ。gate 契約を変えるため ADR/adversarial-review を挟む。
- **#6 header 宣言件数 vs 実数**（P2）: "計N件" header と本文実数の突合（boundary_count_drift を汎化）。AI/人手の件数追従漏れを機械で検出。
- **#4 review_evidence enforcement = 定性の機械保証**（P1、§1.6①の gap 是正、ユーザー方針で昇格）: PLAN frontmatter の `review_evidence` を検証し、`review_kind=cross_agent` を称するのに `worker_model==reviewer_model` または欠落なら fail、`tests_green_at>reviewed_at` なら fail（UT-TDD `review-evidence.ts`）。「定性 LLM レビューが genuine に行われた」を機械で要求 → 定量 green だけで通る穴を塞ぐ。#7 review-guard と対。
- **FE ブラウザ検証 exit**（P1、§1.6②の gap 是正、ユーザー方針）: FE/画面成果の L10 exit に実ブラウザ検証（レンダリング + visual-regression + a11y-regression、既存 `setup-playwright.sh`/`setup-axe.sh`/fe-detector-spec 活用）を機械強制。L2↔L10 pair detector を未実装（§14 残）から enforce へ。unit/contract だけの「FE 完了」を弾く。
- **no-leak 5 機構**（§1.7、ユーザー方針「絶対に漏らさない」）— 弱い③④⑤を機械強制まで引き上げ:
  - ③ デグレ防止: **change-impact 推移的回帰 #9**（source 変更→依存 module の test 未更新を AST import グラフ BFS で検出）+ 全 detector baseline 単調減少 ratchet 統一。
  - ④ 依存漏れ: **コード粒度 dependency-drift #9**（UT-TDD dependency-drift.ts: AST import グラフで module 境界違反・循環 SCC を検出）+ **ADR-002 dependency-direction auto-map**。HELIX の PLAN 粒度 dependency を補完。
  - ⑤ 表記ゆれ: **#5 rule-drift**（adapter 本文整合）+ **doc-consistency / propagation**（concept↔requirements の用語 token parity）+ glossary-delta（用語 SSoT × cross-doc 整合）。
  - ①② は強いので hardening のみ: ① DB projection 完全性 meta-test、② 逆ピラミッド P0 明示。
- **登録・列挙層の完全性**（§1.9、検出の前提を機械強制）— P1:
  - **impl-plan-trace**（UT-TDD `impl-plan-trace.ts`）: 全 impl が登録 PLAN に紐づく（コードが PLAN 起票を迂回して着地していないか）。impl⊆PLAN を機械検証。
  - **drive-model-passage**（UT-TDD `drive-model-passage.ts` / `drive-db-registration.ts`）: 全駆動 workflow が passage + forward_return を DB 登録したことを検証。off-V-model の不可視作業ゼロ化。
  - **不採用**: roadmap-registry（standing roadmap 台帳 = HELIX 既決アンチパターン）。工程表は bounded per-L PLAN 列挙 + read-only l7_worklist のまま。
- **ワークフロー機械強制 + 駆動選択式強制**（§1.10、登録層の非迂回性）— P1:
  - **要件A 工程強制**: entry/exit gate fail-close（G1/G8/G12-G14 hollow 解消は GOAL-C/verification-forward-gate と連携、本 Process は重複させない）。
  - **要件B 駆動選択式強制**: 逸脱検出→**有効 drive menu からの forced selection gate**（route_engine を advisory→fail-close、有効 drive PLAN 登録まで該当 work block）+ **chain-validity 静的検証**（deprecated-process-not-parent + workflow_chain valid-link）。drive-model-passage は §1.9 で採用済。
- **自己改善 2 ループ**（§1.13/§1.14、第3の効用）— P2-P3（段階的、telemetry が流れてから）:
  - **Loop1 per-skill 精度**（§1.13）: 発火率 × 発火時通過率 × ターン内 review 数 を skill 粒度で測定（既存 session telemetry + skill_dispatcher 発火ログから derive 可能か先に確認、推測 schema 回避）。「スキルが効くか」。
  - **Loop2 駆動逸脱頻度**（§1.14）: drive 発火率を (種別×工程×領域) で集計 → 見落とし点 → skill 強化 + workflow 改善。「どこを見落としたか」。既存 Forward逸脱→Issue / 駆動 PLAN / forward_return 登録から derive。North Star = 逸脱率の低下。
  - **telemetry-closure meta-test**（UT-TDD `telemetry-closure.ts`）: 両ループの 測定→feedback→improvement が wired か検証（Skill firing / Drive firing-rate / retry detection / Bottleneck / Measurement-to-feedback / Improvement log）。
  - **improvement-backlog**（UT-TDD `improvement-backlog.md` + lint）: 両ループの feedback 宛先。弱点は PLAN として登録され §1.9/§1.10 経由で改善（V-model 収束）。
- **DB 能動脊椎**（§1.15）— P2-P3（段階的、推測 schema 回避・観測された永続化要求から）:
  - **更新履歴 + 更新強制**: per-artifact 変更履歴 schema + change-impact(§1.7③) 接続の更新強制（更新すべき時に更新したか）。
  - **doc locator 統一**: 全 artifact→doc location の DB query（委譲時の調査コスト削減に直結。helix code find を doc へ拡張）。
  - **next-action 能動算出**: position(L+drive+gate) → 次アクション提示（handover/l7_worklist を DB 算出へ）。
  - 強い ③抽象→具体 trace / Reverse 資産化 は維持・hardening。⑥依存出力は §1.7④ と同一。
- **既存機構の射程拡大**（§1.16、ユーザー指摘で内在化）— P1-P2:
  - **LLM reviewer 校正**: 定性 gate の reviewer の false-pass/false-fail を実測し Loop1（§1.13）へ。worker だけでなく reviewer も測る。
  - **本番 runtime ログ計測（Loop3）**: 納品系に observability を設計内在化、本番実エラー/行動/性能を L13/L14 → 要件へ還す。
  - **並行コンフリクト吸収**: serialize_after/file-conflict guardrail + PLAN allowed_files/dependencies を**共有 state（件数 pin/registry/DB projection）にも適用**（boundary_count_drift 衝突の根治）。
  - **security を NFR 内在**: prompt injection/supply chain/secret を L1 NFR + security gate に当然含める。
- **AI-safe GitHub 運用**（orientation §1.5、ユーザー方針）:
  - **escalation-stale**（UT-TDD `escalation-stale.yml` 由来、P2）: scheduled cron workflow で stale handover / 右腕 CI fail / 未 close の Forward 逸脱 Issue を検出し自動エスカレート（Issue 起票 or 既存 Issue へ通知）。AI 駆動開発が詰まり/失敗を silent に放置するのを機械で surface。HELIX のローカル stale 検出（`cli/lib/handover.py`）を GitHub 面へ拡張。
  - **branch-protection emit-only script**（UT-TDD `setup-branch-protection.sh` 由来、P2）: main 保護設定を**スクリプトとして emit するのみ**で、適用は admin 人間が実行（AI は authz を適用しない）。HELIX は現状ルール宣言のみ → emit script を `helix init` / setup 経路に追加。
  - 既存 AI-safe GitHub 中核（gate-driven push / raw-push guard / 危険外向き操作の人間確認 / Forward逸脱→Issue / CI↔gate）は維持・必要なら hardening。
- 後段候補（本 Process 内で順次評価、価値順）: #11 cost telemetry、#12 tier-router、#13 slot self-heal、#14 gate 自動追加エンジン、#15 enum SSoT（plan_validator 定数 SSoT + drift test、zod 不要）。

### Out（本 Process で扱わない）
- **#10 の人間チームゲート部分**（CODEOWNERS による人間レビュアー強制 / PO-TL-QA サインオフ / gate↔人間役割固定）。orientation §1 により除外。将来 HELIX が複数人運用に拡張する判断が出た時は別 Process で扱う。なお #10 の**自動化・AI-safety 部分（escalation-stale / branch-protection emit-only）は §2 In に採用**（人間ゲートでなく機械 surface / emit のため）。
- **#2 test oracle strength**（重複）: HELIX に `cli/lib/anchor_quality.py` + in-flight [anchor-quality-lint PLAN](../add-feature/add-feature-2026-06-21-anchor-quality-lint.md) が既に実装。新規起票しない。残差（anchor 非依存全走査 / 意味的弱 assert）は必要なら anchor_quality 拡張として後日。
- TS/Bun 書き換え・central UI・Windows PowerShell（orientation §4）。

## 3. 予定 Action PLAN（GOAL-C 着地後に起票 — 件数 ripple 回避）

> **scope 制御（§1.17 P1-4 退化防止 + Sequencing）**: 下表は候補一覧であって常時目標台帳ではない。**本 Process が実際に起票するのは「第一波（P1 minimum）」のみ**。それ以外は **P2/P3 deferred backlog**（enforcement telemetry が観測されてから別 Process 化を判断する候補）として bounded に保つ。各 Action は起票時に **exit condition と期限切れ条件**を付す（未起票候補は roadmap 化しない）。
>
> **foundation-first への精緻化（[design-review](../../research/2026-06-21-no-leak-foundation-design-review.md) §3/§4、2026-06-21）**: 全面設計見直しで **foundation 3 点（F1 登録自動化+設計定義登録 / F2 gate 時実行証跡 / F3 review-evidence 健全性）が他の全機構の前提**と判明 → 第一波を **foundation-first** に並べ替える。F1 が不完全だと detector 母集団が欠け、F2 が弱いと green が theater、F3 が弱いと「定量∧定性」AND が falsifiable。**駆動選択（TL 確定）: F1=Reverse→Add-feature / F2=Add-feature / F3=Add-feature+ADR**。
>
> **第一波（P1 minimum、GOAL-C 着地後に起票）**:
> 0. **foundation（最優先）**: F1（db-auto-registration 乖離の Reverse 記録 → code/doc/test 自動登録 + 設計定義の構造化登録の Add-feature）+ F2（subcheck/vg_overview の gate surface に実行証跡再確認を追加、`exec_pass` の skip 命名分離）+ F3（`review_evidence` ADR: content hash + reviewer identity + commit SHA を含む、design-review §6.3 schema）。
> 1. **契約 ADR ×2**（detector より先）: `gate_profile = size×drive×risk×touched`（§1.17 P0-2）+ `review_evidence`（worker≠reviewer≠calibrator 含む、§1.17 P0-1 = F3）。
> 2. **detector ×4**: `review-guard` / `review-evidence-enforce`(=F3) / `red-first-tdd-evidence` / `descent-provenance`(advisory+baseline 先行)。
> 3. **gate-policy-l4l6-ai-tl** は **ADR + 段階導入（shadow→advisory→limited required→required）**で、第一波では shadow/advisory まで。
> 4. **第1層（foundation 後）**: F4 表記ゆれ（shadow/advisory なら並行設計可、fail-close は F1 後）/ F5 workflow 駆動強制（F1 強依存）/ F6 依存方向。順序は固定不要（design-review §6.6）。
>
> **deferred backlog（telemetry 観測後・別 Process 化候補）**: fe-browser-verify / code-dependency-graph(#9) / term-consistency(#5) / db-projection-meta / impl-plan-trace / drive-model-passage / forced-drive-selection / chain-validity / skill-precision-metrics / telemetry-closure / db-update-history / db-doc-locator-nextaction / reviewer-calibration(外部接地契約 §1.17 P1-2 確定後) / concurrency-guardrail(論理 resource contract §1.17 P1-3 確定後) / **runtime-observability + security-NFR は別 PLAN で L1/L3 へ**（§1.17 P1-5）/ escalation-stale / branch-protection-emit。
>
> 起票時に各 add-feature の `parent_process` を本 Process に設定し、`contains_action_plans` を本 frontmatter に追記して reciprocal を閉じる。

| 予定 plan_id（YYYY-MM-DD は起票日） | 対応 | design_change_class | 統合先 | 備考 |
|---|---|---|---|---|
| add-feature-YYYY-MM-DD-review-guard | #7 | design_or_contract_changed | review wrapper + 新 lib + hook | path 増分 fail-close。初版は内容差分を見ない（誤爆回避） |
| add-feature-YYYY-MM-DD-review-evidence-enforce | #4（定性機械保証, §1.6①） | design_or_contract_changed | 新 detector + plan_lint + push gate | worker≠reviewer + cross_agent + tests_green_at≤reviewed_at。定量 green 単独通過を封鎖 |
| add-feature-YYYY-MM-DD-fe-browser-verify | FE ブラウザ検証（§1.6②） | design_or_contract_changed | fe-detector + L10 exit + playwright/axe | 実レンダ + visual-regression + a11y を L10 必須 exit 機械化。L2↔L10 pair enforce |
| add-feature-YYYY-MM-DD-code-dependency-graph | no-leak ③④（§1.7）: コード AST import グラフ | design_or_contract_changed | 新 detector + ADR-002 auto-map | module 境界違反・循環 SCC + 推移的回帰（依存 module の test 未更新）検出 |
| add-feature-YYYY-MM-DD-term-consistency | no-leak ⑤（§1.7）: 用語 SSoT × cross-doc 整合 | design_or_contract_changed | 新 detector + glossary SSoT | propagation(concept↔requirements token parity) + doc-consistency + glossary-delta。表記ゆれ 0 |
| add-feature-YYYY-MM-DD-db-projection-meta | no-leak ①②（§1.7）hardening | contract_extension | registry meta-test + 逆ピラミッド P0 | DB projection 完全性 meta-test + 逆ピラミッド（impl有 design/test無）P0 明示 |
| add-feature-YYYY-MM-DD-impl-plan-trace | 登録層（§1.9）: impl⊆PLAN | design_or_contract_changed | 新 detector | コードが PLAN 起票を迂回して着地していないか機械検証 |
| add-feature-YYYY-MM-DD-drive-model-passage | 登録層（§1.9）: 駆動通過+forward_return 登録 | design_or_contract_changed | 新 detector + drive registration | off-V-model の不可視作業ゼロ化。roadmap 台帳化はしない |
| add-feature-YYYY-MM-DD-forced-drive-selection | 要件B（§1.10）: 逸脱→drive forced selection | design_or_contract_changed | route_engine fail-close 化 | 逸脱検出後、有効 drive PLAN 登録まで該当 work block |
| add-feature-YYYY-MM-DD-chain-validity | 要件B（§1.10）: 駆動連動の valid-link 強制 | design_or_contract_changed | 静的 check | deprecated-process-not-parent + workflow_chain valid-link fail-close |
| add-feature-YYYY-MM-DD-skill-precision-metrics | 自己改善（§1.13）: per-skill 精度測定 | contract_extension | learning_engine 拡張 + skill_dispatcher 発火ログ | 発火率×通過率×review数 を skill 粒度で。推測 schema 回避（derive 可否先行確認） |
| add-feature-YYYY-MM-DD-telemetry-closure | 自己改善（§1.13/§1.14）: 2ループの測定→feedback→改善 closure | design_or_contract_changed | telemetry-closure meta-test + improvement-backlog | Loop1 skill精度 + Loop2 drive逸脱頻度(種別×工程×領域)。wired 検証 + 弱点を PLAN 化（V-model 収束） |
| add-feature-YYYY-MM-DD-db-update-history | DB 能動脊椎（§1.15）: 更新履歴+更新強制 | design_or_contract_changed | helix_db schema + change-impact 接続 | per-artifact 変更履歴 + 「更新すべき時に更新したか」判定強制。推測 schema 回避 |
| add-feature-YYYY-MM-DD-db-doc-locator-nextaction | DB 能動脊椎（§1.15）: doc locator + next-action | design_or_contract_changed | helix code find 拡張 + handover/worklist DB 算出 | 全 artifact→doc location query（調査コスト↓）+ position→next-action 提示（進捗迷子解消） |
| add-feature-YYYY-MM-DD-reviewer-calibration | §1.16: LLM reviewer 校正 | contract_extension | learning_engine + review_evidence 拡張 | reviewer の false-pass/false-fail 実測→Loop1。worker だけでなく reviewer も測る |
| add-feature-YYYY-MM-DD-concurrency-guardrail | §1.16: 並行コンフリクト吸収 | design_or_contract_changed | guardrail + PLAN allowed_files/deps を共有 state へ | 件数 pin/registry/DB projection の同時更新衝突を guardrail+PLAN で射程化 |
| add-feature-YYYY-MM-DD-runtime-observability | §1.16: 本番 runtime ログ計測(Loop3) | design_or_contract_changed | L1 NFR + L13/L14 + observability 設計内在 | 本番実エラー/行動/性能→要件還元。security NFR(prompt injection/supply chain/secret)も同梱 |
| add-feature-YYYY-MM-DD-red-first-tdd-evidence | #1 | contract_extension | plan_lint / plan_validator / plan_frontmatter | `tdd_evidence: not_applicable` を Bash/手動に許可 |
| add-feature-YYYY-MM-DD-descent-provenance | #3 | design_or_contract_changed | vg_overview 拡張 or 新 detector | ADR/adversarial-review を挟む。advisory+baseline 先行 |
| add-feature-YYYY-MM-DD-header-count-drift | #6 | contract_extension | plan_lint or boundary_count_drift 汎化 | 既存 boundary_count_drift との関係を明示 |
| add-feature-YYYY-MM-DD-escalation-stale | AI-safe GitHub | design_or_contract_changed | `.github/workflows/escalation-stale.yml` + github-operations.md | cron で stale handover/CI fail/未close Forward逸脱 Issue を自動 surface |
| add-feature-YYYY-MM-DD-branch-protection-emit | AI-safe GitHub | contract_extension | setup 経路 + scripts/ + github-operations.md | main 保護を emit-only（適用は admin 人間）。AI は authz 不適用 |
| (ADR + add-feature) gate-policy-l4l6-ai-tl | §1.5 gap①: L4-L6 設計凍結の判定者を人間TL→AI-TL+機械gate へ置換 | design_or_contract_changed | gate-policy.md + automation-gate-map.md | **中核 policy 変更 → ADR + adversarial-review 必須**。人間 escalation は高リスク②に限定 |

## 4. 進捗

| 日付 | 内容 | 担当 |
|---|---|---|
| 2026-06-21 | fork 調査（pmo-sonnet 4 並列 + explorer + tl-advisor）→ research-memo 起票。#2 重複・#10 人間ゲート除外を判定。 | PM |
| 2026-06-21 | ユーザー方針「人間ゲートより自動開発精度・分離設計」→ 本 Process 確立（orientation 宣言）。 | PM |
| 2026-06-21 | TL adversarial review（changes_required）→ §1.17 反映。scope を P1 minimum（契約 ADR×2 + detector×4）へ絞り、残りを deferred backlog 化。 | PM |
| 2026-06-21 | **全面設計見直し（5 cluster 実コード検証）→ [design-review](../../research/2026-06-21-no-leak-foundation-design-review.md) 起票**。foundation 3 点（F1/F2/F3）が穴と判明、§1.7 table honest 訂正。 | PM |
| 2026-06-21 | **design-review の tl-advisor 諮問（changes_required）反映**: 過大表現訂正（A-3 `design_id_existence` 別 detector が doc 実在検査→穴は定義登録に限定 / A-4 存在チェック advisory あり / F2「全く無い」でなく gate surface 再確認なし + `exec_pass` skip 命名危険）。**駆動選択確定: F1=Reverse→Add-feature / F2=Add-feature / F3=Add-feature+ADR**。schema 具体案（review_evidence: content hash + reviewer identity + commit SHA / 実行証跡 artifact）を design-review §6 に固定。**db-auto-registration.md を honest-mark**（`implementation_status: partial` + known_gap + planned_closure、count-pin 非干渉）。 | PM |
| (GOAL-C 着地後) | 第一波起票: gate_profile / review_evidence の ADR ×2 + detector ×4（review-guard / review-evidence-enforce / red-first / descent-provenance advisory）+ audit YAML 件数同期（独立トピック）。 | PM |
| (telemetry 観測後) | deferred backlog を別 Process/P2 で派生判断。AI-TL 置換は shadow→advisory→required で段階導入。 | PM |
| (以降) | detector 実装（Codex se 委譲）+ doctor subcheck 配線 + advisory→required 昇格。 | SE/PM |

## 5. 起票順序制約（最重要）

`cli/lib/tests/test_boundary_count_drift.py` の `_ground_truth_count()` = 全 `docs/plans/add-feature/add-feature-*.md` 数。add-feature を 1 本足すごとに 6 本の audit YAML + Python/Bats contract mirror の "discovered" 件数 pin の再同期が必須（同期しないと G-tests 失敗）。現在その audit YAML 群は **GOAL-C-RIGHTARM-FULLCLOSE（owner=codex, in_progress）**が編集中（M）。

→ **GOAL-C の in-flight 変更が commit された後**に、§3 の 4 本を add-feature PLAN化 + 件数同期を**独立トピック（1 commit=1 topic）**として起票する。本 Process（docs/plans/process/）と research-memo（docs/research/）は add-feature glob に当たらないため、本 commit には影響しない。

## 6. forward_return

採用確定 detector を HELIX 既存検出群（anchor_quality / vg_overview / plan_lint / review wrapper）へ統合し、doctor subcheck として配線。advisory→required 昇格で fail-close 化。これにより「AI 自動開発の出力精度」を機械で締め上げる状態へ収束する。各 detector の forward_return（対 design 層再凍結）は子 add-feature PLAN で [forward-return-discipline](../../../HELIX-workflows/helix-process/forward-return-discipline.md) を適用。
