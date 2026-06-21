# UT-TDD Agent Harness フォーク 採用候補調査 research-memo (2026-06-21)

> Research workflow (kind=research) の research-memo。HELIX の TypeScript/Bun フォーク
> 「UT-TDD Agent Harness」を調査し、HELIX 本体へ逆輸入する価値のある差分を洗い出す。
> 入力資産: `UT-TDD_AGENT-HARNESS-main.zip`（repo root の untracked、`/tmp/ut-tdd-extract/` に展開して精読）。
> forward_return: 採用確定分は detector ごとに add-feature PLAN へ接続（§5）。

## 0. 調査概要

- **目的**: UT-TDD フォークの中に、HELIX（Bash/Python + SQLite、Claude+Codex 専用、単独 AI-PM 運用）より優れている / 採用余地のある機構を特定する。
- **評価軸**: ①価値（HELIX の既知痛点への効き）②移植容易性（Bash/Python+SQLite への落とし込み難度）③重複（HELIX 既存資産との被り）④HELIX-fit リスク（単独 AI-PM 前提との整合 / TS 固有機構の Python 劣化）。
- **対象の正体**: UT-TDD は **HELIX 自体の TS/Bun フォーク**（`docs/migration/helix-fork-completion-plan.md`、AGENTS.md「The HELIX vendor snapshot has been removed now that the fork is complete」で確認）。コア概念（V-model L0-L14 / 駆動モデル / harness.db projection / pair-freeze / Forward 収束）は HELIX 由来でほぼ同一。差分は **(a) チーム運用への振り直し**と **(b) TypeScript Compiler API の AST 解析による「中身」検査の機械化**に集中。
- **規模**: TS 28.6K LOC / Vitest 85 ファイル / lint 58 モジュール / V-model doc 一式 / ADR 7 本。
- **調査体制**: pmo-sonnet 4 並列（team orchestration / substance lint / runtime・provider・telemetry / governance・concept）+ pmo-helix-explorer 1（HELIX 規約・既存資産突合）+ tl-advisor 1（採用優先度の技術判断）。
- **公平性の注記**: UT-TDD は HELIX 子孫のため、vg_overview / fn_ut_pair_coverage / G-review / agent-guard / forward-return-discipline / recovery / Stop-hook handover 等は**両者共通の基盤**。本 memo で「HELIX に無し」と記すのは、その基盤上で UT-TDD が**追加・精緻化した差分**に限る。

## 0.1 採用 orientation（ユーザー方針 2026-06-21）

> 「こっちは人間ゲートより自動開発の精度を上げる運用で分離設計してくれ」

- HELIX は UT-TDD の**人間チームゲート運用（#10: CODEOWNERS / PO-TL-QA サインオフ / gate↔人間役割固定）を採らない**。単独 AI-PM（Opus 全委譲）前提を維持。
- 採用するのは「AI が書いた成果の中身が伴うか」を機械で締める detector 群（#7/#1/#3/#6 等）。レビューの主語も AI（tl-advisor / pmo / Codex cross-review）で、その AI レビューの健全性を機械で守る。
- 逆輸入は verification-forward-gate process / GOAL-C handover から**分離した専用 Process** で進める = [process-2026-06-21-ut-tdd-adoption-machine-precision](../plans/process/process-2026-06-21-ut-tdd-adoption-machine-precision.md)。本 memo はその Process の research-memo（正本）。
- **検証は「定量∧定性」両成立 + FE ブラウザ + 実行検証**（ユーザー方針 2026-06-21「機械ゲートだけだと漏れる」）: AI 駆動の合格条件を `定量 detector green ∧ 定性 LLM レビュー genuine pass ∧ (FEなら)ブラウザ検証 pass ∧ 実行 green 証跡` の AND にする。HELIX doctrine（verification-strategy §10『単独運用はどちらも危険』）を機械強制まで引き上げる。詳細・gap 是正は [Process §1.6](../plans/process/process-2026-06-21-ut-tdd-adoption-machine-precision.md)。これに伴い **#4 review_evidence enforcement（定性の機械保証）を P1 昇格**、**FE ブラウザ検証 exit を採用**。
- **「絶対に漏らさない」5 機構**（ユーザー方針 2026-06-21）: ①DB 自動登録 ②設計/実装/テスト 0 漏れ ③絶対デグレなし ④依存 0 漏れ ⑤表記ゆれ 0。HELIX 現状実証 = ①②強 / ③④部分 / ⑤弱。合格 AND に合流。弱い③④⑤を UT-TDD 機構（change-impact 推移的回帰 #9 / コード AST dependency-drift #9 + ADR-002 / propagation・doc-consistency・glossary-delta ⑤ + #5 rule-drift）で機械強制まで引き上げ。「絶対」= 機械 fail-close で silent leak ゼロ + baseline ratchet で非後退。詳細 = [Process §1.7](../plans/process/process-2026-06-21-ut-tdd-adoption-machine-precision.md)。これに伴い **#5 rule-drift / #9 change-set・dependency を P1-P2 昇格**。
- **背骨 = DDD + TDD の機械強制**（ユーザー方針 2026-06-21「そのための DDD と TDD だろ」）: 二層成立 + no-leak は全て **TDD（②③+実行検証+#1/#2/fn_ut_pair）か DDD（④⑤+境界）の機械強制**に分類できる。定性レビュー(#4)は「DDD/TDD の魂（ユビキタス言語遵守・テストが契約を検証）」の LLM 意味判定。HELIX は両 doctrine を既に持つ（HELIX_CORE §5 DDD / §0 TDD）が enforcement 散在 → UT-TDD `ddd-tdd-rules.ts` 相当の統合 spine へ寄せる。詳細 = [Process §1.8](../plans/process/process-2026-06-21-ut-tdd-adoption-machine-precision.md)。

## 1. 採用候補ランキング（価値 × 容易性、TL 判断 + orientation 反映後）

| # | 項目 | HELIX 現状 | 採否判定 | 優先 |
|---|---|---|---|---|
| 7 | **review-guard**（read-only レビュー subagent の working-tree 変更を before/after path 差分で検出） | 手動 git diff（tl-advisor 副作用の実害あり） | **採用** | P1 |
| 1 | **red-first TDD evidence**（`red_at < green_at <= reviewed_at` 時系列検証） | 無し | **採用** | P1 |
| 3 | **descent-obligation provenance**（`FR-L1-01..50` 範囲展開被覆を focused 引用と区別） | vg_overview は ID 数のみ | **採用（advisory+baseline 先行）** | P1 |
| 6 | **header 宣言件数 vs 実数 自動突合**（"計N件" 検証） | boundary_count_drift は audit YAML pin に限定 | **採用（汎化）** | P2 |
| 2 | **test oracle strength**（弱アサーション AST 検出） | **既に anchor_quality.py で実装済み** | **不採用（重複）** | — |
| 4 | **worker≠reviewer model 静的検証 + tests_green_at≤reviewed_at = 定性の機械保証** | G-review は approve フラグのみ。semantic_gate は doctrine のみで detector 不在 | **採用（P1 昇格）** | P1 |
| 5 | **rule-drift + doc-consistency/propagation/glossary-delta = 表記ゆれ防止(no-leak⑤)** | core-manifest drift のみ。cross-doc 用語整合は弱い | **採用（P2 昇格）** | P2 |
| 9 | **change-set 推移的回帰 + コード AST dependency-drift = デグレ/依存漏れ防止(no-leak③④)** | PLAN 粒度 dependency のみ。コード import グラフ無し | **採用（P1-P2 昇格）** | P1-P2 |
| 10 | チーム運用モデル（人間 TL/QA/PO × gate 紐づけ + CODEOWNERS + escalation-stale） | 単独 AI-PM 前提 | **部分採用のみ** | P3 |
| 11 | token/cost telemetry（provider JSONL からコスト集計） | budget.py / session_telemetry あり | 中優先（substance lint の後） | P3 |
| 12 | 決定論モデル選択 + tier-router（worker は T0 に throw で到達不可） | allowlist guard のみ | enum SSoT 整備後 | P3 |
| 13 | forced-stop / slot self-heal（SessionStart で全 session 走査・dangling 後追い） | agent_slots あり・手動 release | 改善余地（dry-run/advisory 先行） | P3 |
| 14 | gate 自動追加エンジン（frontmatter 形状マッチで全 doc にルール型自動適用） | doc 毎に detector 手書き | 後段（#1/#2/#3/#6 確立後に抽象化） | P3 |
| 15 | enum SSoT（コンパイル時 drift 根絶） | validator enum 二重管理 drift 常習 | 採用（zod 不要、plan_validator 定数 SSoT + drift test） | P3 |

## 2. 採用確定（P1/P2）の詳細

### #7 review-guard — P1（強く推奨）
- **UT-TDD 実装**: `src/runtime/review-guard.ts`。read-only ロール（tl/qa/uiux/reviewer/security/audit/code-reviewer 等 9 種）のレビュー前後で working-tree の変更パス集合を取り、`readOnly && mutatedPaths.length>0` を violation、staged∩変更を suspect として surface。pure 関数（git/fs は hook shim 側）。IMP-137（off-task レビュー subagent がファイルを直接変更しコミット混入した実障害）の再発防止。
- **HELIX 痛点**: memory `feedback_tl_advisor_index_md_side_effect`（tl-advisor が docs/adr/index.md を書き戻す）。現状は「review-only role 投入後は必ず git diff」と手運用。
- **HELIX 移植**: advisor 系 / `helix review` wrapper で before/after の `git status --porcelain` を取り、**path 増分**があれば fail-close。既存 dirty tree が多いセッションで内容差分まで見ると誤爆 → 初版は path 増分検出に限定（TL 注記）。

### #1 red-first TDD evidence — P1
- **UT-TDD 実装**: `src/lint/ddd-tdd-rules.ts:317-343`。`tdd_red_required: true` かつ status=confirmed の PLAN に `red_at`/`green_at` が無い、または `red_at > green_at` で fail。`Date.parse()` で時系列比較。
- **HELIX 痛点**: TDD ファースト規律（CLAUDE.md「テストファースト」）の実効化機構が無い。
- **HELIX 移植**: `plan_frontmatter` / `plan_lint` / `plan_validator` に時刻検証を追加。契約案 `red_at < green_at <= reviewed_at`（ISO 8601）。欠落は新規 PLAN のみ fail、既存は baseline/deferred。Bash/手動検証タスクは `tdd_evidence: not_applicable` + reason/owner/expiry を許す（TL 注記）。

### #3 descent-obligation provenance — P1（advisory+baseline 先行）
- **UT-TDD 実装**: `src/lint/descent-obligation.ts:259-279`。`documentTraceKeyProvenance()` が同一 FR の引用を「範囲展開（`FR-L1-01..50`）のみ」か「単独引用含み」かを Map で区別し、全 L7 被覆がレンジ由来なら thin-coverage advisory（`descent-obligation.ts:644-666`）。AST ではなく Markdown/YAML parser + ID range expander で実装。
- **HELIX 痛点**: vg_overview は ID 数・anchor 数を集約するが、範囲展開と focused 引用の区別が弱く、blanket range で「緑」になり得る（"被覆≠中身" の穴）。
- **HELIX 移植**: vg_overview 拡張 or 新規 detector。`FR-L1-01..50` を obligation 展開し focused quote を `citation_only` に分離。既存 docs の表記揺れが多いため初期導入は **advisory + baseline**。TL 注記: gate 契約を変えるため ADR か adversarial-review を挟む。

### #6 header 宣言件数 vs 実数 — P2（汎化）
- **UT-TDD 実装**: `src/lint/fr-registry-audit.ts:122-130`。「計48件 / P0:X / P1:Y / P2:Z」の header 宣言を正規表現抽出し実数と突合。
- **HELIX 現状**: `cli/lib/tests/test_boundary_count_drift.py` が存在するが、対象は **audit YAML の add-feature 件数 pin に限定**（`_ground_truth_count()` = add-feature ファイル数）。汎用的な「doc header 宣言件数 vs 本文実数」lint は無い。memory に「ヘッダー数値追従漏れ」「audit bundle count ripple → 4点同期」が頻出。
- **HELIX 移植**: functional-registry §2 summary（"計574件"）、FR registry の件数行などへ汎化。marker 限定で日本語自然文の誤爆を回避（TL 注記）。既存 boundary_count_drift との関係を明示し、汎化 or 併設を設計時判断。

## 3. 不採用 / 部分採用の判断記録

- **#2 test oracle strength = 不採用（重複）**: HELIX には既に [cli/lib/anchor_quality.py](../../cli/lib/anchor_quality.py)（459 行、Python `ast` 使用）+ in-flight PLAN [add-feature-2026-06-21-anchor-quality-lint.md](../plans/add-feature/add-feature-2026-06-21-anchor-quality-lint.md) があり、`assert True`/trivial assert/no-assert/pass-only/skip-xfail/bats run-without-checks を検出済み。UT-TDD の oracle strength と検出領域が一致。**新規起票は重複**。残差は「anchor 非依存の全テストファイル走査」「意味的弱 assert（`len(result)>0`/`any()` 等の non-trivial だが弱いもの）」のみで marginal → 必要なら anchor_quality 拡張として後日検討（独立 PLAN にしない）。
- **#10 チーム運用モデル = 分割判定**（ユーザー方針 2026-06-21 で確定）:
  - **人間ゲート部分 = 不採用**: 3 層人間チーム（コア TL/QA/UIUX = 判断）、gate↔人間役割固定（G1/G3/G7/G11=PO、G4/G5/G6=TL）、CODEOWNERS による人間レビュアー強制（src→TL / tests→QA / docs→PO）は HELIX 路線外（単独 AI-PM 前提を維持）。
  - **AI-safety 自動化部分 = 採用**（「GitHub 運用も AI が安全に開発できるように」）: **escalation-stale**（cron で stale handover / 右腕 CI 失敗 / 未 close の Forward 逸脱 Issue を自動 surface → silent rot 防止、P2）、**branch-protection emit-only script**（main 保護を emit のみ、適用は admin 人間 = AI は authz 不適用、P2）。HELIX 現状調査: escalation-stale は未実装（stale 検出は `cli/lib/handover.py` にローカルのみ）、branch-protection script も未実装（ルール宣言のみ）。既存 AI-safe 中核（gate-driven push 7 gate / raw-push guard / main auto-push 不可 / 危険外向き操作の人間確認 / Forward逸脱→Issue / CI↔gate）は充足済みで維持。これらは [process-2026-06-21-ut-tdd-adoption-machine-precision §2](../plans/process/process-2026-06-21-ut-tdd-adoption-machine-precision.md) の In に取り込み。
- **#14 gate 自動追加エンジン = 後段**: frontmatter 形状マッチで全 doc にルール型（pair-exists / trace-bidir / count-matches / id-format / dup-id …）を自動適用する強力機構だが後戻りコスト大。先に #1/#3/#6 を手書き detector として確立してから抽象化を検討。

## 4. 移植しないもの（フォーク選択であって機能ではない）

- **TS/Bun への書き換え自体（ADR-001）**: HELIX は Bash/Python+SQLite に commit 済み。ただし **AST 検査の発想は Python `ast` で再現する**（pytest 解析は anchor_quality が実証済み。Bats は AST が無いため構造 regex + assertion pattern で近似）。
- **central Web UI（ADR-005）**: 別プロダクト級の表面。将来構想として記録のみ。
- **Windows-first PowerShell entrypoint**: HELIX は Linux/WSL 運用のため不要。

## 5. forward_return（add-feature 接続）

採用確定分を detector ごとに add-feature PLAN（kind=impl, **parent_process=[process-2026-06-21-ut-tdd-adoption-machine-precision](../plans/process/process-2026-06-21-ut-tdd-adoption-machine-precision.md)**）へ起票する。verification-forward-gate process / GOAL-C handover からは分離する（orientation §0.1）。

| 起票予定 PLAN | 内容 | design_change_class | 備考 |
|---|---|---|---|
| add-feature-YYYY-MM-DD-review-guard | #7 review-guard（path 増分 fail-close） | design_or_contract_changed | hook wrapper + 新 lib + test |
| add-feature-YYYY-MM-DD-red-first-tdd-evidence | #1 red_at/green_at/reviewed_at 契約 + plan_lint 検証 | contract_extension | frontmatter 契約拡張 |
| add-feature-YYYY-MM-DD-descent-provenance | #3 範囲展開 vs focused 引用 provenance（advisory+baseline） | design_or_contract_changed | ADR/adversarial-review を挟む |
| add-feature-YYYY-MM-DD-header-count-drift | #6 header 宣言件数 vs 実数 汎化 | contract_extension | boundary_count_drift との関係明示 |
| add-feature-YYYY-MM-DD-escalation-stale | AI-safe GitHub: cron で stale handover/CI fail/未close Forward逸脱 Issue を自動 surface | design_or_contract_changed | `.github/workflows/escalation-stale.yml` 新設 |
| add-feature-YYYY-MM-DD-branch-protection-emit | AI-safe GitHub: main 保護 emit-only（適用は admin 人間、AI は authz 不適用） | contract_extension | setup 経路 + scripts/ |

> **起票上の順序制約（重要）**: add-feature PLAN を 1 本でも `docs/plans/add-feature/` に追加すると、`test_boundary_count_drift.py` の `_ground_truth_count()`（= 全 add-feature ファイル数）が増え、6 本の audit YAML + Python/Bats contract mirror の "discovered" 件数 pin の**再同期が必須**になる（同期しないと G-tests 失敗）。現在その audit YAML 群は **GOAL-C-RIGHTARM-FULLCLOSE（owner=codex, in_progress）**が M で編集中。クリーンに起票するには、**GOAL-C の in-flight 変更が commit されてから** add-feature PLAN + 件数同期を**独立トピック**として起票する（1 commit=1 topic / handover 規律 = Next Action 外ファイルの混入回避）。

## 6. evidence

- 抽出元: `/tmp/ut-tdd-extract/UT-TDD_AGENT-HARNESS-main/`（zip 展開）。主要参照: `src/lint/`（descent-obligation.ts / ddd-tdd-rules.ts / review-evidence.ts / fr-registry-audit.ts / oracle-test-trace.ts / rule-drift.ts）、`src/runtime/`（review-guard.ts / detect.ts / adapter.ts / forced-stop.ts / agent-slots.ts）、`src/team/`（launch-policy.ts / model-policy.ts / run.ts）、`src/task/tier-router.ts`、`docs/governance/`（concept_v3.1 / ai-dev-team-concept_v1.1 / ai-dev-team-operations_v1.1 / gate-design.md）、`docs/adr/ADR-001..007`、`ai-agent-harness-directory-reference.md`。
- HELIX 既存資産突合: `cli/lib/anchor_quality.py`、`cli/lib/tests/test_boundary_count_drift.py`、`cli/lib/vg_overview.py`、`cli/lib/context_guard.py`、`cli/lib/plan_lint.py`、`cli/lib/g7_subcheck.py`、`cli/lib/agent_slots.py`、`cli/lib/budget.py`。
- TL 判断: `helix codex --role tl-advisor`（2026-06-21、decision=passed）。総合「条件付き推奨 — TS AST を丸ごと移植せず HELIX 既存 detector に追加する形が妥当」。
