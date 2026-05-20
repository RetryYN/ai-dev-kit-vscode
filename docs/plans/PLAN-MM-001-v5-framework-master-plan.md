---
plan_id: PLAN-MM-001
title: "PLAN-MM-001: V5 framework 親設計プラン (V5 全体構想 + 子 PLAN-091〜099 起票計画 + ADR-021〜032 snapshot 計画)"
layer: L2
kind: design
status: draft
size: L
drive: be
created: 2026-05-20
revised: "2026-05-20 (tl-advisor Round 1 反映: 着手順序訂正 + P1 単一実行正本決定 + drift 明記 + DoD 縮小)"
owner: PM
phases: L0, L1, L2
gates: G0.5, G1, G2
agent_slots:
  - role: pm-advisor
    slot_label: "PM 親設計判断・子 PLAN 整合・最終 finalize"
  - role: tl-advisor
    slot_label: "Adversarial check 反復 (Round N+1 まで)"
  - role: pmo-sonnet
    slot_label: "子 PLAN/ADR 起票委譲 (Layer A→B→C 限定並列)"
generates:
  - artifact_path: docs/plans/PLAN-091-v5-framework-core.md
    artifact_type: design_doc
  - artifact_path: docs/plans/PLAN-092-posttooluse-plan-auto-register.md
    artifact_type: design_doc
  - artifact_path: docs/plans/PLAN-093-plan-drift-detection-curator.md
    artifact_type: design_doc
  - artifact_path: docs/plans/PLAN-100-existing-retrofit-v2-revision.md
    artifact_type: design_doc
  - artifact_path: docs/plans/PLAN-095-poc-scrum-reverse-matrix.md
    artifact_type: design_doc
  - artifact_path: docs/plans/PLAN-096-github-actions-branch-pipeline.md
    artifact_type: design_doc
  - artifact_path: docs/plans/PLAN-097-abstraction-layer-escalation.md
    artifact_type: design_doc
  - artifact_path: docs/plans/PLAN-098-recovery-plan-kind-normalization.md
    artifact_type: design_doc
  - artifact_path: docs/plans/PLAN-099-autonomous-runtime-framework-5layer.md
    artifact_type: design_doc
  - artifact_path: docs/adr/ADR-021-design-doc-web-search-guardrail-snapshot.md
    artifact_type: adr_snapshot
  - artifact_path: docs/adr/ADR-022-todowrite-agent-slot-framework-snapshot.md
    artifact_type: adr_snapshot
  - artifact_path: docs/adr/ADR-023-gate-fail-close-staged-adoption-snapshot.md
    artifact_type: adr_snapshot
  - artifact_path: docs/adr/ADR-024-continueonblock-active-guidance-loop-snapshot.md
    artifact_type: adr_snapshot
  - artifact_path: docs/adr/ADR-025-v5-framework-core-decision.md
    artifact_type: adr_snapshot
  - artifact_path: docs/adr/ADR-026-posttooluse-plan-auto-register-decision.md
    artifact_type: adr_snapshot
  - artifact_path: docs/adr/ADR-027-plan-drift-detection-curator-decision.md
    artifact_type: adr_snapshot
  - artifact_path: docs/adr/ADR-028-poc-scrum-reverse-matrix-decision.md
    artifact_type: adr_snapshot
  - artifact_path: docs/adr/ADR-029-github-actions-branch-pipeline-decision.md
    artifact_type: adr_snapshot
  - artifact_path: docs/adr/ADR-030-abstraction-layer-escalation-decision.md
    artifact_type: adr_snapshot
  - artifact_path: docs/adr/ADR-031-recovery-plan-kind-decision.md
    artifact_type: adr_snapshot
  - artifact_path: docs/adr/ADR-032-autonomous-runtime-framework-decision.md
    artifact_type: adr_snapshot
dependencies:
  parent: null
  requires:
    - PLAN-087-design-doc-web-search-guardrail
    - PLAN-088-todowrite-agent-slot-framework
    - PLAN-089-gate-fail-close-design-doc-web-search-audit
    - PLAN-090-posttooluse-continueonblock-refactor
  blocks:
    - PLAN-091-v5-framework-core
    - PLAN-092-posttooluse-plan-auto-register
    - PLAN-093-plan-drift-detection-curator
    - PLAN-100-existing-retrofit-v2-revision
    - PLAN-095-poc-scrum-reverse-matrix
    - PLAN-096-github-actions-branch-pipeline
    - PLAN-097-abstraction-layer-escalation
    - PLAN-098-recovery-plan-kind-normalization
    - PLAN-099-autonomous-runtime-framework-5layer
related_docs:
  - docs/v2/V5-plan-outlines.md (本 PLAN の起票元素材、17 要素時点で古い、CLAUDE.md が正本)
  - CLAUDE.md §V5 framework 18 要素 (最新正本、PLAN-099 含む)
  - docs/v2/CONCEPT.md (V2 全体構想、PLAN-100 で全面見直し対象)
  - docs/v2/L1-REQUIREMENTS.md (V2 要件、PLAN-100 で見直し対象)
  - docs/v2/L2-MASTER.md (V2 基本設計、§0 line 36 の PLAN↔ADR 範例)
  - helix_github_workflow_rules.md (PLAN-096 起票元素材、root level draft)
  - helix_improvement_plan_draft.md (PLAN-093/097 起票元素材、root level draft)
  - skills/SKILL_MAP.md (PLAN-091/097 の SKILL_MAP 統合対象)
  - helix/HELIX_CORE.md (V-model 4 artifact + subagent + Sprint 標準 source)
related_memories:
  - project_2026_05_20_v5_framework_evolution_recovery (本 session の V5 確立過程)
  - feedback_recovery_plan_kind_missing (PLAN-098 直接 source)
  - feedback_adr_before_plan_violation (PLAN-100 直接 source)
  - feedback_dont_stop_with_carry_remaining (PLAN-098 § session 終了前チェック source)
  - feedback_design_doc_web_search_required (本 PLAN §3 Web 検索 3 query 起票準拠 source、PLAN-087 連動)
acceptance:
  - V5 framework 18 要素 + 3 層構造 + TL v5 round 5 修正条件 (5 重要 + 8 補助 + P0/P1) を子 PLAN 全件に反映完了
  - 子 PLAN 9 件 + ADR 12 件 (021〜024 retrofit + 025〜032 新規) の draft 起票完了 (finalize は別 session、本 session 目標は draft + 契約凍結)
  - frontmatter dependencies chain が PLAN-MM-001 を parent、PLAN-091〜099 を blocks で接続
  - PLAN-091 §単一実行正本決定 で `PLAN = plan_registry / helix job = runnable queue / handover = session continuity / TodoWrite = ephemeral checklist` を凍結 (TL v5 P1)
  - tl-advisor adversarial check (本 PLAN 含む) が passed (changes_required → 反映 → passed の反復で終結)
  - V2 doc (CONCEPT/L1-REQUIREMENTS/L2-MASTER) との整合確認 (PLAN-100 で全面見直し計画明示)
  - デグレ禁止: 既存 PLAN-001〜090 / CLI / hook / DB schema / template は本 session では編集しない (新規 doc 起票のみ)
---

# PLAN-MM-001: V5 framework 親設計プラン (V5 全体構想)

> **kind**: design (cross-layer master plan)
> **layer**: L2 (全体設計フェーズ、子 PLAN-091〜099 を blocks で従える親 hub)
> **drive**: be (CLI / framework 実装中心、UI なし)
> **本 PLAN の役割**: PLAN-091〜099 起票時の frontmatter 語彙・依存関係・整合判断の正本。子 PLAN は本 PLAN を parent に取る。
> **正本宣言**: V5 framework 要素の正本は **CLAUDE.md §V5 framework 18 要素** + 本 PLAN。docs/v2/V5-plan-outlines.md は 17 要素時点の古い素材で、本 PLAN 起票後は要更新 (PLAN-100 retrofit 対象)。

## §0. 本 PLAN の位置付け

本 PLAN は **HELIX V5 framework の親設計プラン**。V5-plan-outlines.md (commit d9401b4、pmo-sonnet 起票) に列挙された 9 子 PLAN + 8 ADR 起票案を構造化し、本 PLAN 自身を parent hub として子 PLAN 群を blocks で従える。

V5 framework は本 session (2026-05-19〜20) の V1→V5 確立過程で出現した「PLAN 規約 (PLAN は self-contained workflow ルール doc)」+ 「V-model layer × drive matrix」+ 「種別正規化 (11 kind)」+ 「PoC = Scrum × Reverse 連携 matrix」+ 「GitHub Actions + ブランチタイプ別パイプライン」+ 「リカバリープラン kind」+ 「自動走行 framework 5-layer」を統合した次世代 HELIX framework。

- TL 5 ラウンド adversarial check 全 passed (v1 bs9wuvqcs / v2 bppaf3fwe / v3 bkac94gnw / v4 baq742e62 / v5 bdnmyhznq)
- ユーザー 12+ turn 訂正 (V1→V5 の各 round で本質的訂正)
- 自動走行 framework 5-layer は turn 14-15 で要素 18 として追加 (claw0 + agent_farm + claude-brain + learn-claude-code 4 OSS シナジー)

本 PLAN 完遂 (子 PLAN 9 件 + ADR 12 件 起票完遂) により、HELIX は V5 framework に基づく実装段階 (PLAN-091 → 092 → 093 ... の順実装) へ進める。

### 正本 drift 注記 (tl-advisor Round 1 指摘反映)

| 文書 | 要素数 | PLAN-099 含む | 状態 |
|---|---|---|---|
| **CLAUDE.md §V5 framework 18 要素** | 18 | ✅ | **最新正本** |
| docs/v2/V5-plan-outlines.md | 17 | ❌ (本文に PLAN-099 outline はあるが「17 要素」と冒頭明記) | **古い、要更新 (PLAN-100 retrofit 対象)** |
| 本 PLAN-MM-001 | 18 | ✅ (子 PLAN として PLAN-099 を blocks に含む) | 起票中 |

起票方針: 各子 PLAN は **CLAUDE.md の 18 要素マッピング** に従って起票し、V5-plan-outlines.md は素材参照に留める。drift 解消は PLAN-100 で V5-plan-outlines.md を 18 要素版に更新 (本 PLAN-MM-001 完遂後の別 session task)。

## §1. 目的

1. V5 framework 9 子 PLAN (PLAN-091〜099) の親設計として、起票時の frontmatter 語彙・依存関係・整合判断を提供する
2. ADR-021〜024 retrofit (PLAN-087〜090 の L2 凍結 snapshot 後追い) と ADR-025〜032 新規起票 (PLAN-091〜099 の L2 凍結 snapshot) を計画する
3. V5 framework 18 要素 + 3 層構造 + TL v5 round 5 修正条件を子 PLAN 全件に反映する
4. V2 doc (CONCEPT / L1-REQUIREMENTS / L2-MASTER) の全面見直し (PLAN-100) を計画化し、V5 framework と既存 V2 構想の整合を保証する
5. 段階導入 5 Phase (warning → matrix 検証 → fail-close → retrofit → Curator 自動化) を子 PLAN 群に分散して機械化する

## §2. 背景

### 2.1 V1→V5 確立過程の要約

| Round | 確立要素 | TL verdict | ユーザー訂正 |
|---|---|---|---|
| v1 | matrix + 種別 | passed (bs9wuvqcs) | layer に L3.5/L4.5 追加 |
| v2 | + 依存 + agent_slots + 自動登録 | passed (bppaf3fwe) | PLAN-091〜093 分割推奨 |
| v3 | + template embed | passed (bkac94gnw) | kind 5 → 11 種拡張 |
| v4 | + V-model TDD + PoC リバース合流 | passed (baq742e62) | ADR/PLAN 分離 (ADR 先・PLAN 後 → 後に「PLAN ⊃ ADR レイヤー併存」へ訂正) |
| **v5** | + 自動走行 framework 18 番要素 | **passed_with_minor_changes** (bdnmyhznq) | C 案先行 PoC + PreCompact decision:block 限定 + statusLine + Stop 役割分担 + claude-brain pattern HELIX 独自再実装 + P0 承認なし task pop 禁止 + P1 単一実行正本決定 |

### 2.2 既存 HELIX 資産との関係

V5 framework は既存 HELIX 資産 (107 skills / 30 CLI roles / SKILL_MAP / HELIX_CORE / V-model 4 artifact / Sprint 標準 / subagent 工程マッピング / readiness と carry rule) を **置換せず拡張** する。

- スキル層 (107 skills): PLAN-097 で抽象化層 3 層 (スキル → ワークフロー → ハーネス) として位置付け維持
- V-model 4 artifact (PLAN-075): PLAN-091 template に組み込んで全 PLAN で必須化
- Sprint 標準 (PLAN-077): PLAN-091 kind 別 template embed の 1 種として吸収
- subagent 工程マッピング (PLAN-076): PLAN-091 agent_slots frontmatter で機械化
- helix.db (v33): PLAN-092 v35 へ拡張 (plan_registry / plan_dependencies / plan_agent_slots 等 10 新規 table)

### 2.3 本 PLAN の motivation (なぜ親設計プランが必要か)

子 PLAN 9 件 + ADR 12 件 = 計 21 doc を **整合の取れた framework として** 起票するには、起票前に「frontmatter 語彙の正本」「依存関係 chain」「段階導入 Phase の分担」「TL v5 修正条件の反映場所」を確定する必要がある。

本 PLAN 不在で子 PLAN を並列起票すると、frontmatter 語彙の drift (kind 名 / layer 表記 / dependencies 構造の不揃い)、ADR snapshot 範囲の重複/抜け、段階導入 Phase の分担混乱が発生する。

本 PLAN は **子 PLAN 起票時の単一 source of truth** として機能する。

## §3. 業界 standard 参照 (Web 検索 3 query ベース、PLAN-087 ガードレール準拠)

| 参照 | source | 引用箇所 |
|---|---|---|
| Architecture Decision Records (ADRs) - Microsoft Azure Well-Architected Framework | https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record | ADR-021〜032 起票方針 (append-only log、supersedes link) |
| ADR best practices (200+ ADR 実績) - AWS Architecture Blog | https://aws.amazon.com/blogs/architecture/master-architecture-decision-records-adrs-best-practices-for-effective-decision-making/ | ADR snapshot 必須化 (V5 要素 11) の根拠 |
| GitHub Spec Kit (Constitution → Specify → Clarify → Plan → Tasks → Implement) | https://github.com/github/spec-kit | V5 framework の段階化 (PLAN = self-contained workflow ルール doc) の業界整合 |
| AWS Kiro IDE (Constitution / Specify / Plan / Tasks / Implement / PR) | https://thebcms.com/blog/spec-driven-development | PLAN-091 kind 別 template embed の業界整合 |
| EARS (Easy Approach to Requirements Syntax) | https://towardsdatascience.com/from-vibe-coding-to-spec-driven-development/ | PLAN-091 受入条件記述方式の参考 (testable / AI-parseable) |
| Feature flag staged rollout (warn-only → fail-close) - Flagsmith | https://www.flagsmith.com/blog/how-to-enhance-phased-rollouts-with-feature-flags | 段階導入 5 Phase (P1 warning → P3 enforce) の業界整合 |
| Progressive delivery (continuous feedback loop) - Cloudflare Flagship | https://www.infoq.com/news/2026/05/cloudflare-flagship-openfeature/ | PLAN-093 Curator の継続フィードバック構造の根拠 |
| 内部 reference: V5-plan-outlines.md | docs/v2/V5-plan-outlines.md (commit d9401b4、17 要素時点で古い) | 子 PLAN 9 件 + ADR 8 件の素材 (要更新) |
| 内部 reference: TL v5 round 5 verdict | CLAUDE.md §TL 5 ラウンド全 passed | 修正条件 5 重要 + 8 補助 + P0/P1 |

## §4. V5 framework 18 要素 (CLAUDE.md §V5 framework 18 要素 から正式化、正本)

| # | 要素 | 担当 子 PLAN |
|---|------|----|
| 1 | PLAN = self-contained workflow ルール doc | PLAN-091 |
| 2 | V-model layer × drive matrix | PLAN-091 |
| 3 | 種別正規化 (11 kind: design / impl / poc / reverse / troubleshoot / refactor / retrofit / research / add-design / add-impl / recovery) | PLAN-091 + PLAN-098 (recovery 専用化) |
| 4 | matrix 外 / kind 不在を helix plan CLI で fail-close | PLAN-091 (P3 enforce 段階) |
| 5 | 生成物 trace (frontmatter `generates`) | PLAN-091 + PLAN-092 (DB 化) |
| 6 | 依存関係 graph (frontmatter `dependencies: requires/parent/blocks`) | PLAN-091 + PLAN-092 (DB 化) |
| 7 | agent slot 割当 (frontmatter `agent_slots`) | PLAN-091 + PLAN-088 連動 |
| 8 | PostToolUse hook で PLAN.md → helix.db 自動登録 | PLAN-092 |
| 9 | PLAN ↔ 設計 doc drift 検出 (helix doctor) | PLAN-093 |
| 10 | 進捗 trace (plan.db sprint_progress) | PLAN-092 (schema) + PLAN-093 (dashboard) |
| 11 | ADR snapshot 必須化 (L2 大局判断あれば) | PLAN-091 (規約) + PLAN-100 (retrofit) |
| 12 | kind 別 workflow template embed (Step 1-N) | PLAN-091 |
| 13 | V-model TDD 駆動 (設計⇔テスト設計 pair freeze + 実装 TDD + QA 追加テスト) | PLAN-091 (template に組み込み) |
| 14 | PoC = Scrum × Reverse 連携 matrix (Scrum 6 type × Reverse 5 type) | PLAN-095 |
| 15 | GitHub 運用ルール統合 (helix_github_workflow_rules.md ベース) | PLAN-096 |
| 16 | helix_improvement_plan_draft.md 6 Phase 統合 | PLAN-093 (Phase 6 Curator) + PLAN-097 (Phase 4 抽象化層) |
| 17 | リカバリープラン kind (recovery) | PLAN-098 |
| 18 | 自動走行 framework 5-layer (PostToolUse / statusLine / PreCompact / SessionStart / heartbeat) | PLAN-099 |

## §5. V5 framework 3 層構造 (Layer A→B→C 着手順序、CLAUDE.md §V5 framework 3 層構造 から正式化)

```
[Layer A] 工程・ドキュメント運用ルール整備
  V5 要素 1-7 + 11-17
  子 PLAN: PLAN-091 (本体) / PLAN-100 (retrofit) / PLAN-095 (PoC matrix) / PLAN-096 (GitHub) / PLAN-097 (抽象化層) / PLAN-098 (recovery)
       ↓
[Layer B] helix.db 型ハーネス整備
  V5 要素 8 + 9 + 10 + 単一実行正本決定 (TL v5 P1)
  子 PLAN: PLAN-092 (PostToolUse + schema v35) / PLAN-093 (drift + Curator)
       ↓
[Layer C] 連携自動化ハーネス
  V5 要素 8 (hook 本体) + 18 (自動走行 5-layer)
  子 PLAN: PLAN-099 (5-layer 自動走行、本 session は document + fixture 方針まで、本実装は別 session)
  ※ PoC C 案 (Layer 4+5) のみ Layer A/B 確定前に並行可
```

**着手順序遵守ルール**:
- 子 PLAN 起票は **PLAN-091 を契約 seed として最優先確定**、その後限定並列 (tl-advisor Round 1 指摘反映)
- 実装段階 (PLAN-091 P3 enforce / PLAN-092 schema v35 / PLAN-099 自動走行 本実装) は Layer A → B → C 順序を遵守
- PLAN-099 PoC C 案 = Layer 4 (SessionStart 履歴注入) + Layer 5 (15min heartbeat) は Layer A/B 確定前に並行 PoC 可 (既存 handover/SessionStart/scheduler 上に作れる)、ただし **本 session は document + fixture 方針まで** (TL v5 round 5 修正条件 + Round 1 指摘)

## §6. 子 PLAN 起票計画 + dependencies graph (tl-advisor Round 1 反映済)

```
PLAN-MM-001 (本 PLAN、parent hub)
    │
    ├── PLAN-091 ↔ ADR-025  framework 本体 (matrix + 種別 + template embed + 単一実行正本決定)
    │   ├── frontmatter 語彙の正本定義 (kind/layer/drive/dependencies/agent_slots/generates)
    │   ├── 段階導入 P1 warning + P2 matrix 検証 + P3 fail-close enforce
    │   ├── TL v5 P0 反映 (承認なし task pop 禁止、queue worker は plan guard 必須)
    │   └── TL v5 P1 反映 (単一実行正本決定: PLAN=plan_registry / helix job=runnable queue / handover=continuity / TodoWrite=ephemeral)
    │
    ├── PLAN-092 ↔ ADR-026  PostToolUse 自動登録 + helix.db v35 schema
    │   ├── plan_registry / plan_dependencies / plan_agent_slots / plan_references / plan_generates / sprint_progress / failure_log / poc_validation_log / refactor_degrade_pattern / hotfix_incident_log (10 新規 table)
    │   └── PLAN-087/089/090 PostToolUse 系列の延長
    │
    ├── PLAN-093 ↔ ADR-027  drift 検出 + 進捗 trace dashboard + Curator
    │   ├── helix doctor 拡張 (check_plan_drift / check_plan_freshness / check_recovery_plan_freshness)
    │   ├── helix dashboard plan-progress 拡張
    │   └── Curator (helix_improvement Phase 6 統合、ルール昇格/降格自動判定)
    │
    ├── PLAN-100 ↔ ADR-021/022/023/024  既存 retrofit + V2 全面見直し (§4 分割、tl-advisor Round 1 反映)
    │   ├── §4.1: ADR-021 (PLAN-087 Web 検索ガードレール snapshot) + 独立 DoD + 双方向 trace
    │   ├── §4.2: ADR-022 (PLAN-088 agent slot framework snapshot) + 独立 DoD + 双方向 trace
    │   ├── §4.3: ADR-023 (PLAN-089 gate fail-close snapshot) + 独立 DoD + 双方向 trace
    │   ├── §4.4: ADR-024 (PLAN-090 continueOnBlock + active guidance loop snapshot) + 独立 DoD + 双方向 trace
    │   ├── §5: PLAN-001〜090 frontmatter 一括 retrofit (kind/layer/drive/generates 追加)
    │   ├── §6: V2 doc (CONCEPT/L1-REQUIREMENTS/L2-MASTER) 全面見直し
    │   └── §7: V5-plan-outlines.md drift 解消 (17 要素 → 18 要素)
    │
    ├── PLAN-095 ↔ ADR-028  PoC = Scrum × Reverse 連携 matrix
    │   ├── Scrum 6 type × Reverse 5 type = 30 cell matrix
    │   ├── helix scrum decide --confirmed --reverse-merge で S4→R0 自動 routing
    │   └── PoC リバース合流 R0-R4 mapping
    │
    ├── PLAN-096 ↔ ADR-029  GitHub Actions + ブランチタイプ別パイプライン
    │   ├── feature.yml / poc.yml / refactor.yml / hotfix.yml
    │   ├── PR template + CODEOWNERS + Conventional Commits 強制
    │   ├── ブランチタイプ ↔ HELIX kind マッピング (feature→impl/design / poc→poc / refactor→refactor/retrofit / hotfix→recovery)
    │   └── 人間承認境界の明記 (CODEOWNERS / branch protection rule 等 repo 運用影響、tl-advisor Round 1 反映)
    │
    ├── PLAN-097 ↔ ADR-030  抽象化層 (スキル/ワークフロー/ハーネス) + エスカレーション
    │   ├── workflows/ (再利用フロー YAML)
    │   ├── harness/ (オーケストレーター)
    │   ├── レビュー注入 3 段階 (agent / council / human)
    │   └── 発火/再失敗回数ベースの昇格降格判定
    │
    ├── PLAN-098 ↔ ADR-031  リカバリープラン kind 正規化
    │   ├── recovery template 7 必須セクション (事故記録 / 議論順序 timeline / 認識訂正履歴 / 中間結論 list / context 再構築 / 再開ポイント / 再発防止)
    │   ├── session 終了前チェックリスト 4 項目 fail-close
    │   └── helix doctor check_recovery_plan_freshness 追加
    │
    └── PLAN-099 ↔ ADR-032  自動走行 framework 5-layer (本 session は document + fixture 方針まで、tl-advisor Round 1 反映)
        ├── Layer 1: PostToolUse(Write|Edit + PLAN.md) → helix job enqueue (task_queue は新設せず既存 helix job/scheduler に enqueue、P0 承認 guard 必須)
        ├── Layer 2: statusLine context % 4 段階監視 (>50% / 30-50% / ≤30% / ≤20%、debounce + hysteresis 必須)
        ├── Layer 3: PreCompact hook で state 永続化 (decision:block は 3 条件 AND 限定: 重要 state 永続化失敗 AND 未保存 L2/L3/ADR AND 一回だけ)
        ├── Layer 4: SessionStart(cleared|compacted) + UserPromptSubmit で関連履歴自動注入 (claude-brain pattern HELIX 独自再実装、transcript_path 参照 + 要約 state + 明示的 retention)
        ├── Layer 5: ScheduleWakeup adaptive heartbeat (通常 15min / 低予算 30min / critical 5min / active task 中無効)
        └── テスト戦略: fake transcript + fake handover + fake carry + fake timer + queue atomic claim + PreCompact one-shot + statusLine threshold hysteresis + hook timeout (本 session の document 段階で全件固定、tl-advisor Round 1 反映)
```

## §7. 段階導入 5 Phase (TL v5 round 5 修正条件 P1 反映済)

| Phase | 内容 | 対象 PLAN | 目安 session | 単一実行正本 |
|-------|------|-----------|------|----|
| P1 | warning 導入 (matrix 外でも続行、警告のみ) | PLAN-091 partial | 1 | TodoWrite (既存) |
| P2 | matrix 検証 + drift 検出 | PLAN-091 + 092 + 093 | 2-3 | TodoWrite + plan_registry (新) |
| P3 | fail-close 強制 (helix plan create で matrix 外 reject) | PLAN-091 enforce | 1 | TodoWrite + plan_registry |
| P4 | retrofit + V2 全面見直し | PLAN-100 (並列 N codex docs) | 2-3 | (継続) |
| P5 | Curator 自動化 + GitHub / 抽象化層 / PoC matrix 統合 + Layer C 本実装 | PLAN-095〜098 + PLAN-099 本実装 | 3-5 | (継続) |

**P1 単一実行正本決定** (TL v5 P1、tl-advisor Round 1 反映):

| 候補 | 用途 | 正本決定 |
|---|---|---|
| `PLAN` (PLAN-NNN.md + plan_registry) | PLAN 定義の単一 source of truth (種別・依存・生成物 trace・段階導入 Phase) | **plan_registry (PLAN-092 新規)** |
| `helix job` / `scheduler` (既存) | runnable execution queue (実行待ち task の atomic claim) | **既存 helix job + scheduler 継続使用、task_queue 新設しない** |
| `handover` (既存 .helix/handover/CURRENT.json) | session continuity (session 跨ぎの状態継承) | **既存 handover 継続使用** |
| `TodoWrite` (Claude Code 内部) | ephemeral checklist (session 内 task tracking、永続化なし) | **既存 TodoWrite 継続使用** |

詳細: PLAN-091 §単一実行正本決定 で確定 (本 PLAN は方針宣言のみ)。

**P0 承認 guard** (TL v5 P0、tl-advisor Round 1 反映):
- queue worker が task を pop する前に必ず Plan Consent / WBS / handover Next Action のいずれかの guard を通す
- 自動 pop は「候補提示」までを default、実行は承認境界を越えない
- 詳細: PLAN-091 §guard + PLAN-099 §Layer 1 で確定

## §8. TL v5 round 5 修正条件 (子 PLAN 反映指示)

CLAUDE.md §TL v5 round 5 修正条件 から、各 子 PLAN への反映指示を整理:

### 5 重要項目

| # | 修正条件 | 反映先 子 PLAN |
|---|---|---|
| 1 | 設計選択 = V5 に統合 / 実装単位は分離 (PLAN-091 と PLAN-099 独立、段階導入) | PLAN-091 + PLAN-099 |
| 2 | PoC 戦略 = C 案 (Layer 4 + Layer 5) を先行 PoC (0.5-1 session) | PLAN-099 §Phase 1 |
| 3 | PreCompact decision:block 限定 (重要 state 永続化失敗 AND 未保存 L2/L3/ADR AND 一回だけ の 3 条件 AND) | PLAN-099 §Layer 3 |
| 4 | statusLine + Stop 役割分担 (Stop 軽量化、statusLine debounce + hysteresis 必須) | PLAN-099 §Layer 1+2 |
| 5 | claude-brain pattern HELIX 独自再実装 (transcript_path 参照 + 要約 state + 明示的 retention、UserPromptSubmit 注入は短い bundle に制限) | PLAN-099 §Layer 4 |

### 8 補助項目

| # | 修正条件 | 反映先 子 PLAN |
|---|---|---|
| 6 | 依存衝突 = PLAN-091 → PLAN-099 正順 (frontmatter dependencies 語彙は PLAN-091 定義)、PoC は並行可 | PLAN-091 + PLAN-099 |
| 7 | PLAN-088 関係 = task_queue 新設なら責務明文化必須 (PLAN 定義 = plan_registry、実行待ち = 既存 helix job/scheduler) | PLAN-091 + PLAN-099 |
| 8 | 15min heartbeat adaptive (通常 15min / 低予算 30min / critical 5min / active task 中無効) | PLAN-099 §Layer 5 |
| 9 | テスト戦略 (fake transcript / fake handover / fake carry を使った hook fixture test 先行) | PLAN-099 §テスト戦略 |
| 10 | Layer 4 snapshot test (SessionStart cleared/compacted + UserPromptSubmit 注入) | PLAN-099 §Phase 1 PoC テスト |
| 11 | Layer 5 fake timer test (5/15/30min + budget low + bg task active + carry 0 no-op 検証) | PLAN-099 §Phase 1 PoC テスト |
| 12 | Layer 1-3 本実装時 (migration idempotent / queue atomic claim / PreCompact one-shot block / statusLine threshold hysteresis / hook timeout) | PLAN-099 §Phase 2 本実装 |
| 13 | 既存 PLAN-081 等の古い hook 設計との docs drift → PLAN-099 起票時に obsolete/superseded 明記 | PLAN-099 §関連 PLAN |

### P0 / P1 指摘 (絶対遵守)

| 区分 | 修正条件 | 反映先 子 PLAN |
|---|---|---|
| **P0** | 承認なし task pop は HELIX discipline 破壊 → queue worker は **必ず plan guard を通す** | PLAN-091 §guard + PLAN-099 §Layer 1 |
| **P1** | task_queue / TodoWrite / helix job / handover が競合 → 単一実行正本決定 (本 PLAN §7 で凍結方針宣言、PLAN-091 で詳細確定) | PLAN-091 §単一実行正本決定 |

### P2 / P3 指摘 (設計時考慮)

| 区分 | 修正条件 | 反映先 子 PLAN |
|---|---|---|
| P2 | hook foreground 処理肥大化 → SessionStart は fail-open、重い sync は background | PLAN-099 §hook 性能 |
| P2 | statusLine warning / heartbeat のノイズ化、重要警告無視リスク | PLAN-099 §threshold 設計 |
| P3 | claude-brain 型履歴保存は secret/PII/ライセンス判断 = 人間確認対象 | PLAN-099 §Layer 4 retention |

## §9. デグレ禁止項目 (本 session 起票範囲外)

本 PLAN + 子 PLAN 9 件 + ADR 12 件 の起票は **新規 doc 作成のみ**。本 session では以下を **編集しない** (デグレ禁止):

- 既存 PLAN-001〜090 docs (PLAN-100 retrofit の実施は別 session)
- 既存 cli/ (helix-plan / helix-codex / helix-claude / helix-doctor / helix-db / helix-job / scheduler / 等の CLI 本体)
- 既存 .claude/hooks/ (PreToolUse / PostToolUse / Stop / SessionStart 等の hook)
- 既存 cli/lib/ (helix_db.py / migrations/ / plan_parser.py / hook 受け側等)
- 既存 cli/templates/ (PLAN/ADR/D-API/D-DB 等の template)
- 既存 helix.db schema (v33 → v35 拡張は PLAN-092 実装時)
- 既存 SKILL_MAP / HELIX_CORE / CLAUDE.md / AGENTS.md (本 session で V5 framework 関連の追記は OK だが、既存規約の削除は禁止)
- 既存 docs/v2/ (CONCEPT/L1-REQUIREMENTS/L2-MASTER の見直しは PLAN-100 で計画化、本 session では編集しない)
- 既存 docs/adr/ADR-001〜020 (本 session で新規追加のみ、既存編集は禁止)
- 既存 helix job / TodoWrite / handover の実装 (task_queue は新設しない) (PLAN-091 で単一実行正本決定を凍結、実装は別 session)

例外:
- `.gitignore` の helix_*.md ignore 追加 (root level draft 副次保護、本 session で済) はデグレに該当しない
- 本 PLAN-MM-001 + 子 PLAN/ADR の新規追加はデグレに該当しない

## §10. DoD (Definition of Done、tl-advisor Round 1 縮小済)

本 PLAN-MM-001 完遂の判定基準 (本 session 目標 = draft 全件 + critical 契約凍結):

1. **子 PLAN 9 件 draft 起票完了**: PLAN-091〜099 が `docs/plans/` 配下に存在し、frontmatter (kind/layer/drive/agent_slots/generates/dependencies/related_*) + 本文 (目的/背景/業界 standard 参照/V5 要素マッピング/Phase 設計/DoD/V-model 4 artifact trace) が記述されている
2. **ADR 12 件 draft 起票完了**: ADR-021〜032 が `docs/adr/` 配下に存在し、frontmatter (Status / Deciders / Supersedes / Related / 業界 standard 参照) + 本文 (Context / Decision / Consequences / Alternatives) が記述されている
3. **frontmatter dependencies chain 整合**: 全子 PLAN が parent: PLAN-MM-001、blocks: (該当する後段 PLAN) で接続されている
4. **V5 framework 18 要素カバレッジ**: 18 要素全件が子 PLAN いずれかで担当宣言されている (§4 表参照)
5. **TL v5 round 5 修正条件反映**: 5 重要 + 8 補助 + P0/P1 が §8 表通り子 PLAN に反映されている
6. **PLAN-091 critical 契約凍結**: 単一実行正本決定 (§7 表) + agent_slots/dependencies/generates frontmatter 語彙 + 段階導入 5 Phase が PLAN-091 内に確定している
7. **tl-advisor adversarial check 反復 + passed**: 本 PLAN + 子 PLAN 9 件全件で tl-advisor review を反復し、最終 passed (changes_required → 反映 → passed) に達している
8. **デグレ確認**: 既存 PLAN-001〜090 / CLI / hook / DB schema / template / SKILL_MAP / HELIX_CORE が編集されていないことを git diff で確認
9. **commit + push**: 起票結果が origin/main に push されている (本 session 完遂条件)

**finalize は本 session 範囲外** (tl-advisor Round 1 反映):
- 子 PLAN finalize (status: draft → confirmed) は別 session
- 子 PLAN 実装 (PLAN-091 P3 enforce / PLAN-092 schema v35 / PLAN-099 本実装 等) は別 session
- V2 全面見直し本体 (PLAN-100 §6) は別 session
- helix doctor check_plan_adr_snapshot fail-close 化は別 session

## §11. V-model 4 artifact trace (本 PLAN の位置付け)

本 PLAN-MM-001 は **設計 artifact (①)** であり、L2 全体設計層の親設計 doc。対応する artifact:

| Artifact | 位置 | 担当 |
|---|---|---|
| ① 設計 | docs/plans/PLAN-MM-001-v5-framework-master-plan.md (本 PLAN) | 本 PLAN |
| ② 実装コード | PLAN-091 §Phase 4 で cli/ 拡張、PLAN-092 §schema、PLAN-099 §hook 等で 子 PLAN が担当 | 各子 PLAN |
| ③ テスト設計 | docs/v2/L4-test-design/PLAN-091-*.md 〜 PLAN-099-*.md (各子 PLAN で別 file 起票、本 session 起票範囲外) | 各子 PLAN 実装段階 |
| ④ テストコード | cli/lib/tests/test_*.py (各子 PLAN 実装時に追加) | 各子 PLAN 実装段階 |

本 PLAN は親設計 doc であり、テスト設計 / テストコードは子 PLAN 実装段階で別 file 化する (V-model 4 artifact 双方向 trace 原則、PLAN-075)。

## §12. session 終了前チェックリスト 4 項目 (PLAN-098 source、本 PLAN 完遂時に適用)

本 PLAN session 終了前に以下 4 項目全充足を確認:

1. ✅ **中間結論が docs に永続化**: 本 PLAN + 子 PLAN 9 件 + ADR 12 件が起票完了 (起票自体が永続化)
2. ✅ **carry 残件明記**: 子 PLAN 実装段階 (PLAN-091 P3 enforce / PLAN-092 schema v35 / PLAN-099 本実装 等) は次 session 以降 carry
3. ✅ **認識訂正 memory feedback 更新**: 本 session で「Tier A/B/D 個別作業は前提誤り、V5 framework 全振りが正」「『吸収』ではなく『前提誤り → 置換』が正」の認識訂正があった → memory feedback に永続化必要 (PLAN 完遂時に更新)
4. ✅ **recovery kind PLAN draft 起票**: 本 PLAN の起票過程自体を recovery 視点で振り返り、必要なら project_2026_05_20_v5_framework_master_plan_drafting.md を memory に追加

→ 4 項目満たさず turn 終了は禁止 (feedback_dont_stop_with_carry_remaining 14h idle 事故防止)。

## §13. 関連 PLAN / ADR / memory

### related_plans (require, 本 PLAN の前提となる既存 PLAN)
- PLAN-087 設計 doc Web 検索ガードレール (本 PLAN の業界 standard 参照 section が PLAN-087 ガードレール準拠で記述されている)
- PLAN-088 TodoWrite × agent slot framework (本 PLAN agent_slots frontmatter の正本)
- PLAN-089 gate fail-close staged adoption (本 PLAN P3 fail-close 段階導入の正本)
- PLAN-090 PostToolUse continueOnBlock + active guidance loop (本 PLAN PoC C 案 Layer 4 の前提)

### related_plans (blocks, 本 PLAN が起票元になる子 PLAN)
- PLAN-091〜099 (9 件、§6 参照)

### related_adrs (本 PLAN が起票計画化する ADR)
- ADR-021 (PLAN-087 retrofit snapshot、PLAN-100 §4.1 で起票)
- ADR-022 (PLAN-088 retrofit snapshot、PLAN-100 §4.2 で起票)
- ADR-023 (PLAN-089 retrofit snapshot、PLAN-100 §4.3 で起票)
- ADR-024 (PLAN-090 retrofit snapshot、PLAN-100 §4.4 で起票)
- ADR-025〜032 (PLAN-091〜099 新規 snapshot、各子 PLAN と同時起票)

### related_memories
- project_2026_05_20_v5_framework_evolution_recovery (V5 確立過程の永続化記録)
- feedback_recovery_plan_kind_missing (PLAN-098 直接 source)
- feedback_adr_before_plan_violation (PLAN-100 ADR-021〜024 retrofit 直接 source、訂正後の正確な原則は「PLAN ⊃ ADR レイヤー併存」)
- feedback_dont_stop_with_carry_remaining (§12 session 終了前チェック source)
- feedback_design_doc_web_search_required (§3 Web 検索 3 query 起票準拠 source、PLAN-087 連動)

---

## Appendix A: 起票順序 (本 session タイムライン、tl-advisor Round 1 反映、限定並列に訂正)

本 PLAN-MM-001 起票後、子 PLAN 9 件 + ADR 12 件を以下の順で起票:

| Wave | 並列起票 | 担当 | 並列数 |
|---|---|---|---|
| W0 (済) | PLAN-MM-001 (本 PLAN) | Opus 直接 | 1 |
| W1 (済) | tl-advisor Round 1 review | Codex tl-advisor (gpt-5.5 high) | 1 |
| **W2 (契約 seed 単独)** | **PLAN-091 + ADR-025** (frontmatter 語彙・依存契約・単一実行正本決定の正本) | **pmo-sonnet 単独** | **1** |
| W3 (限定並列 3) | PLAN-092 + ADR-026 / PLAN-093 + ADR-027 / PLAN-099 + ADR-032 PoC C 案文書 | pmo-sonnet × 3 | 3 |
| W4 (単独) | PLAN-100 + ADR-021/022/023/024 (§4 分割、§5 frontmatter retrofit 計画、§6 V2 見直し計画) | pmo-sonnet 単独 | 1 |
| W5 (限定並列 4) | PLAN-095 + ADR-028 / PLAN-096 + ADR-029 / PLAN-097 + ADR-030 / PLAN-098 + ADR-031 | pmo-sonnet × 4 | 4 |
| W6 | tl-advisor Round 2 review (PLAN-091 中心、契約整合) | Codex tl-advisor | 1 |
| W7 | 修正反映 (changes_required ループ、passed まで反復) | pmo-sonnet (Codex 修正) + Opus (integrate) | N |
| W8 | tl-advisor Round 3 review (全件整合確認) | Codex tl-advisor | 1 |
| W9 | commit + push (single commit、git status clean 確認) | Opus 直接 | 1 |
| W10 | 最終報告 + memory feedback 更新 | Opus 直接 | 1 |

**並列性根拠** (tl-advisor Round 1 反映、PLAN-091 先行 → 限定並列 → PLAN-100 単独):
- W2: PLAN-091 は frontmatter 語彙・dependencies 語彙・単一実行正本決定の **契約 seed**。並列起票すると他子 PLAN が PLAN-091 の語彙を仮定して書き、整合 drift 発生 → 単独起票必須
- W3: PLAN-092 (schema) / PLAN-093 (drift) / PLAN-099 (PoC C 案文書) は PLAN-091 契約を read-only で参照、互いに file 衝突なし → 3 並列
- W4: PLAN-100 は ADR-021〜024 + frontmatter retrofit + V2 見直し計画を一文書に纏める → 単独起票で整合確保
- W5: PLAN-095/096/097/098 は独立トピック (PoC matrix / GitHub / 抽象化層 / recovery)、互いに file 衝突なし → 4 並列

## Appendix B: 起票時の整合チェック観点

各子 PLAN 起票時、pmo-sonnet が以下を満たすこと:

1. frontmatter に `plan_id` / `title` / `layer` / `kind` / `status: draft` / `drive` / `agent_slots` / `generates` / `dependencies` を必須記述
2. `dependencies.parent: PLAN-MM-001` を必須記述 (本 PLAN を hub に接続)
3. `dependencies.requires` に Layer A → B → C の前段 PLAN を記述 (Layer B は Layer A 完遂を require、Layer C は Layer A/B 完遂を require、ただし PLAN-099 PoC C 案は例外で並行 OK)
4. `dependencies.blocks` に Layer A → B → C の後段 PLAN を記述
5. 業界 standard 参照 section に Web 検索 3 query 以上の引用 (PLAN-087 ガードレール準拠)
6. V5 framework 18 要素のうち本 PLAN 担当要素を §担当要素 で明示 (§4 表との整合)
7. V-model 4 artifact trace section (③ テスト設計は別 file の起票計画として記述、本 session 起票範囲外)
8. TL v5 round 5 修正条件 (§8 表) のうち本 PLAN 反映対象を §TL v5 修正条件反映 で明示
9. ADR snapshot (PLAN-091 → ADR-025 等) を同時起票し、ADR ↔ PLAN の双方向 reference を frontmatter `related_adr` + ADR `Related` section で明示
10. デグレ禁止項目 (§9) を侵さない (新規 doc 作成のみ、既存編集禁止)
