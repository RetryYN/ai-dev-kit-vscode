---
plan_id: PHASE-4-READINESS-2026-05-22
title: "Phase 4 V2 doc 全面見直し 着手前 readiness report (8 並列 pdm + pmo 総動員 wave 結果)"
kind: research
layer: cross
drive: be
status: finalized
size: M
created: 2026-05-22
owner: PM
related_plans:
  - PLAN-100-existing-retrofit-v2-revision
related_memories:
  - project_2026_05_22_plan100_phase2_session_pickup
---

# Phase 4 V2 doc 全面見直し 着手前 readiness report

**日付**: 2026-05-22
**契機**: ユーザー指示「V2全面見直しにあたって既存資産の再整理とWeb検索リサーチやpdmたちとpmoたちを総動員するのをおすすめする」
**baseline**: commit 803fc08 (Phase 3 P1-P4 retrofit + pre-Phase-4 cleanup 完遂、99/99 PLAN validator PASS)

## §1. 動員した subagent (8 並列 + 1 統合)

| # | subagent | model | role | output |
|---|---|---|---|---|
| 1 | pdm-tech-innovation | Opus | 海外技術思想 → V5 拡張案 | 5 領域 (DORA/IDP/AI-Augmented/Event Sourcing/ADR) + V5 要素 #19-#23 + FR-V5-19〜23 |
| 2 | pdm-marketing-innovation | Opus | 海外マーケ思想 → 採用ストーリー | JTBD 5 user / NSM / Bowling pin / Activation / Progressive disclosure + FR-V5-MK01-05 |
| 3 | pdm-innovation-manager | Opus | tech + marketing 統合 + tl-advisor adversarial check | 採用判定 (#22 採用 P0、#19/#20/#23 部分採用 P1-P2、#21 不採用) |
| 4 | pmo-helix-explorer | Sonnet | HELIX framework 内資産探索 | 主要 doc 11 件 + skill 107 件 + cli 45+ subcmd + hook 16 件 + drift 11 件 |
| 5 | pmo-project-explorer | Sonnet | project 内 V2 doc + V5-era 資産探索 | 詳細 inventory (output 91KB、要約のみ採用) |
| 6 | pmo-tech-docs | Sonnet | 設計手法 5 領域 (DDD/ADR/Workflow/Plugin/Observability) | MADR 2.1.2 / Event Sourcing upcasting / DMN / Anthropic Skill / GenAI Semantic Conventions |
| 7 | pmo-tech-fork | Sonnet | OSS 7 領域評価 | top 5 採用 (spec-kit / networkx / alembic 思想 / pre-commit / LangGraph) + 不採用 3 件 (Backstage / Temporal / Airflow) |
| 8 | pmo-tech-news | Sonnet | 最新 Tech 動向 5 領域 | Claude Code v2.1.140-146 / GPT-5.5 + 5.2-codex / Cursor 3.4 / OWASP LLM Top 10 2026 / Stripe rubyfmt |

## §2. tech 5 拡張案 (#19-#23) と採用判定

pdm-innovation-manager + tl-advisor adversarial check (session 019e4b85) で判定:

| 要素 | 内容 | 判定 | Phase 4 実装先 |
|---|---|---|---|
| **#22 ADR Decision Graph Registry** | MADR 4.0 拡張 + `helix adr graph` CLI、ADR 間 Supersedes/Extends/Conflicts を frontmatter で機械可視化 | **採用 P0** | **新規 PLAN-101 + ADR-033 起票** |
| #19 DORA mirror-and-multiplier guard | PLAN-093 Curator 拡張、rework rate + change failure rate 自動計測 | 部分採用 P1 | PLAN-093 scoped extension (Phase 5) |
| #20 Multi-agent topology declaration | PLAN-091 agent_slots に topology field (planner-worker/chain/graph) 追加 | 部分採用 P1 | PLAN-091 frontmatter schema 拡張 (Phase 4 後段) |
| #23 Axon DCB-style retroactive migration | PLAN-084 dual-write + projection rebuild の形式化 | 部分採用 P2 | PLAN-093 documentation only (Phase 5) |
| #21 IDP export (Backstage/Port 互換) | `helix portal export` CLI で PLAN/ADR/sprint_progress を YAML 出力 | **不採用** | — (internal dev tool に過剰、60% maintenance overhead) |

**tl-advisor 判定**:
- 軸 A (simplicity): WARN — 5 件同時拡張は概念過多。**#22 のみ Phase 4 採用が妥当**
- 軸 B (体系衝突): WARN — #19/#23→PLAN-093、#20→PLAN-091 で吸収可。PLAN-094 空白管理が P2 リスク
- 軸 C (marketing 適用): PASS — SaaS funnel 不適だが NSM/counter-metric は internal quality metric として妥当
- 最大リスク: 説明概念増加 → CLI/ゲート/文書/ADR 責務境界曖昧化 (P1)

## §3. marketing 思想の HELIX 翻訳 (technical metric 化)

pdm-marketing-innovation 提案を **internal dev tool に適合する技術指標** へ翻訳:

| marketing 概念 | HELIX 翻訳 |
|---|---|
| NSM "carry consumed per session" | helix.db `session_carry_metric` table + `helix metrics nsm` CLI |
| counter-metric pair | validator failure 率 / ADR snapshot 不在率 / WebSearch 0 query design doc 率 (全て helix.db 計測可能) |
| Bowling pin (Pin 1-5) | 内部 onboarding 順序、CLAUDE.md / SessionStart hook の運用語彙限定 |
| Aha moment (5 分以内 carry 1 件消化) | `helix doctor --adoption-stage` で計測、Activation moment 定義 |
| Progressive disclosure (Layer 1-3) | SessionStart hook + session_count 判定で V5 18+ 要素を段階的 disclose |

**不採用 (HELIX に過剰な SaaS template)**: paywall / billing / freemium / viral loop / referral / NPS survey / A/B test。

## §4. 設計手法 5 領域 採用判定 (pmo-tech-docs)

| 領域 | 採用判定 | 反映先 |
|---|---|---|
| **Event Sourcing upcasting** | 採用 | PLAN-084 §4 addendum |
| **MADR 2.1.2 準拠 (Decision Drivers / Considered Options / Pros/Cons)** | 採用 | PLAN-091 §7 template 更新 + PLAN-101 (要素 #22 と直結) |
| DMN Decision Table 可視化 | 採用 | PLAN-095 + CONCEPT.md §V5 |
| **Anthropic Skill open standard** | 採用 | SKILL_MAP.md §正本宣言に注記 |
| **GenAI Semantic Conventions (OTel v1.37+)** | 採用 P1 | PLAN-080 metric 定義 + FR-V5-19 (新規) |
| Wide Events + semantic SLO | 採用 P2 | CONCEPT.md §V5 observability 原則 |

**不採用**: Camunda/BPMN UI / log4brains 導入 / Temporal durable execution 実装 / Crypto-shredding / Composio MCP 統合。

## §5. OSS 採用候補 (pmo-tech-fork) top 5

| # | OSS | license | HELIX 統合方法 | 対応 PLAN |
|---|---|---|---|---|
| 1 | **github/spec-kit** (92.4k) | MIT | CONCEPT.md §2 に "Spec-Plan-Tasks 3 層は L1→L2→L3 に対応" 業界 standard 引用 | PLAN-091 §2 template |
| 2 | **networkx** (14k+) | BSD-3 | `nx.simple_cycles()` で PLAN-092 cli/lib/plan_dependencies.py の cycle detection を 1 行化 | PLAN-092 §7 |
| 3 | **alembic batch migration 思想** | MIT | SQLite ALTER TABLE 制約回避 (RECREATE TABLE pattern) を helix.db migration 標準手法として明文化 | PLAN-085 / PLAN-100 §5 |
| 4 | **pre-commit manifest schema** | MIT | hook manifest 形式 (id/name/entry/language/types) を HELIX subagent 定義 frontmatter 整備 参考 | PLAN-076 |
| 5 | **LangGraph StateGraph** | MIT | Layer 1 task_queue dispatch の FSM 設計で `conditional_edges` pattern を思想引用 | PLAN-099 ADR-032 |

**不採用**: Backstage (Web UI 必須、CLI-first 原則と相容れず) / Temporal (Go/Java バイナリ依存) / Apache Airflow (バッチ Data pipeline 特化)。

## §6. 最新 Tech 動向 top 5 反映候補 (pmo-tech-news)

| # | 動向 | HELIX 統合方法 | 対応 PLAN |
|---|---|---|---|
| 1 | Claude Code v2.1.141 PostToolUse 8-block 上限 | `.claude/hooks/` コメント + PLAN-099 §5 carry note | PLAN-099 Phase 3 polish |
| 2 | Claude Code v2.1.145 Stop hook `background_tasks` フィールド | PLAN-099 Layer 3 (PreCompact state 永続化) で helix.db carry 保存に利用 | PLAN-099 Layer 3 設計更新 |
| 3 | **MCP tool poisoning 対策 (OWASP LLM Top 10 2026)** | `pretooluse-agent-guard.sh` に MCP tool call allowlist チェック追加 | 新規 PLAN-087 Phase 4 |
| 4 | GPT-5.2-Codex migration 性能向上 | `helix codex --role se` で PLAN-084 Phase 4.B cutover sprint に 5.2-codex 明示指定 option | PLAN-084 Phase 4.B carry |
| 5 | Cursor 競合比較 (audit log + multi-repo cloud agent) | V2 CONCEPT.md §差別化 に "V-model traceability + helix.db audit" を Cursor Audit Log と対比明記 | PLAN-100 Phase 4 §2 |

## §7. HELIX framework 内資産 整理 (pmo-helix-explorer)

### 7.1 主要 doc の V5 反映 drift

| doc | 行数 | V5 反映状況 | drift |
|---|---|---|---|
| HELIX_CORE.md | 267 | Sprint Plan / subagent 工程 反映済 | V5 framework 3 層構造への明示参照なし |
| SKILL_MAP.md | 491 | Sprint / subagent 反映済 | cli/ROLE_MAP.md 整合は別途確認要 |
| CLAUDE.md | 424 | V5 18 要素 + Layer A→B→C フル記述 | Phase 4 で V2 doc へ転記必要 |
| AGENTS.md | 148 | V5 / PLAN-091 への参照なし | 軽微 drift |
| CODEX_TL_MODE.md | 253 | helix plan/sprint/handover CLI 運用記述 | V5 framework 参照なし |

### 7.2 docs/v2 file 状態

| file | 行数 | V5 反映 |
|---|---|---|
| CONCEPT.md | 409 | §5 Phase 構成 / §3 V2 軸記述完備、**V5 framework 18 要素 / PLAN-091〜099 参照なし** |
| L1-REQUIREMENTS.md | 814 | FR-INV/VD/V/DB-EXT 等充実、**FR-V5-01〜18 全欠** |
| L2-MASTER.md | 1895 | §0 line 36 範例は PLAN-084↔ADR-018/019 のまま、**§12 M-09〜M-12 内容未記入** |
| V5-plan-outlines.md | 411 | **冒頭「17 要素」表記 (18 要素が正本)、「8 PLAN」「7 ADR」(9 PLAN / 8 ADR へ更新要)** |

### 7.3 drift 11 件 (Phase 4 で同時解消推奨)

1. V5-plan-outlines.md 「17 要素」→ 18 (or 19) 要素
2. L1-REQUIREMENTS.md §11 FR 件数 74 → 80
3. L1-REQUIREMENTS.md NFR-03 v30 → v35
4. L2-MASTER.md §0 line 36 PLAN-084 範例に PLAN-MM-001↔PLAN-091〜099 追記
5. L2-MASTER.md §12 M-09〜M-12 内容空欄解消
6. CONCEPT.md §9 PLAN-065/063 → PLAN-091〜099 置換
7. CONCEPT.md AC-12 pytest 1138+ / bats 433+ → 1820+ / 509+ 更新
8. CONCEPT.md §5 Phase 構成に Phase K (V5 framework 統合) 追加
9. `helix-plan-cmds/retrofit.sh` 不在 (PLAN-100 Phase 3 で追加予定だが未実装)
10. `.claude/settings.json` PreCompact hook 未登録 (Layer 3 gap)
11. AGENTS.md V5 framework 記述ゼロ

## §8. Phase 4 着手 final roadmap

PLAN-100 §6 を以下 4 wave で実行:

### Wave 1 (必須、1 session): CONCEPT.md V5 section 追加

- §V5 framework 統合 section 追加 (18 要素 + 3 層構造 + 要素 #22 ADR graph)
- §5 Phase 構成に Phase K (V5 framework 統合) 追加
- §9 資産表 PLAN-065/063 → PLAN-091〜099 置換
- AC-12 pytest/bats 実績値更新 (1820+ / 509+)
- §V5 観測性 section (Wide Events + GenAI Semantic Conventions)
- §V5 差別化軸 (V-model traceability + helix.db audit、Cursor 対比)

### Wave 2 (必須、1 session): L1-REQUIREMENTS FR-V5 追加

確定 FR list (P0/P1/P2 別):
- **P0 (Phase 4 同時実装)**: FR-V5-22 (ADR Decision Graph)
- **P1 (Phase 5 carry)**:
  - FR-V5-19 (Curator は rework rate / change failure rate を計測)
  - FR-V5-20 (PLAN frontmatter agent_slots は topology field を持つ)
  - FR-V5-MK01 (helix.db に NSM 指標 + counter-metric 3 種を記録)
  - FR-V5-MK02 (SessionStart hook は session_count に応じて Layer 1-3 disclose)
- **§11 FR 件数 74 → 80 (FR-V5-22 + MK01-02 + 19 + 20 = 計 +5)**
- **NFR-03 v30 → v35 修正**
- **AC-18〜24 追加** (PLAN-100 §6.2 Sprint 0 補完で確定)

### Wave 3 (必須、1 session): L2-MASTER §0 範例拡張 + V5-plan-outlines 19 要素版

- L2-MASTER §0 line 36 範例追加: PLAN-MM-001↔PLAN-091〜099 (PLAN-084 範例と並べる)
- L2-MASTER §12 M-09〜M-12 内容追記 (commit 877845a / PLAN-091 根拠)
- V5-plan-outlines.md: 17 → 19 要素版 (#22 ADR graph 追加、#19/#20/#23 scoped extension 注記)
- V5-plan-outlines.md: 「8 PLAN / 7 ADR」→「9 PLAN / 8 ADR」+ PLAN-101 / ADR-033 起票案追加

### Wave 4 (推奨、Wave 3 と並走可能): drift 補完

- HELIX_CORE.md V5 3 層構造参照 1 行追加
- AGENTS.md V5 / Sprint 8 ステップ参照追加
- `.claude/settings.json` PreCompact hook 登録 (Layer 3 gap)
- SKILL_MAP.md §正本宣言に Anthropic Skill open standard 注記

### Wave 5 (Phase 4 並行、新規 PLAN 起票): PLAN-101 + ADR-033

- PLAN-101: ADR Decision Graph Registry (MADR 4.0 拡張、`helix adr graph` CLI 実装)
- ADR-033: PLAN-101 の L2 snapshot

## §9. tl-advisor 推奨に基づく Phase 4 着手原則

1. **段階採用**: 5 拡張要素を一括で V5 18→23 化せず、Phase 4 は **#22 のみ採用 (19 要素版)**。
2. **scoped extension**: #19/#20/#23 は既存 PLAN-091/093 拡張で吸収、新規 PLAN を増やさない。
3. **marketing 翻訳**: NSM / counter-metric / Bowling pin / Aha moment は internal technical metric に翻訳して採用、SaaS 語彙そのままは不採用。
4. **simplicity 維持**: CLI/ゲート/文書/ADR の責務境界を保つ。説明概念過多は HELIX discipline 破壊。
5. **risks 監視**: PLAN-094 空白管理 (P2)、metric の目的化 (P2)、IDP 外部互換コスト (撤退条件) を定期チェック。

## §10. Phase 4 着手 baseline 確定

- 本 report (commit 後の hash) を Phase 4 全 wave の参照 baseline とする
- PLAN-100 §6 を本 report 内容で update (次 commit で実施)
- Wave 1〜5 を順次 (一部並行) 着手、各 wave 完遂時に handover update + memory feedback 永続化

---

## Sources (各 subagent report 内引用 URL の代表)

### pdm-tech-innovation (15 URL)
- DORA 2025 Report (Plandek / Faros) / SPACE 2025 Edition (LinearB / DX Research) / arxiv 2511.20955 (SPACEX paper)
- Gartner 2025 IDP Market Guide / Port 2025 State Report / Tasrie 比較 / Infisical
- Cognition Devin / MetaGPT / AgentCoord (arxiv 2404.11943) / AgentNet (2504.00587)
- Axon 5.1 / EventStoreDB 24.10 / Marten / DDD 2026
- MADR 4.0.0 / Startupbricks 2025 ADR guide / adr.github.io

### pdm-marketing-innovation (15 URL)
- Reforge PLG (5 articles) / JTBD theory (jobstobedone.org / GoPractice / Re-Wired Group)
- North Star Metric (Growth Method / Sean Ellis / Rachitsky Atlas / Userpilot)
- Crossing the Chasm (Eifler / Sendbird / hashnode) / Activation (Reforge × 2 / Artisan)
- User Onboarding 2025 (Guidejar)

### pmo-tech-docs (10 URL)
- Azure Event Sourcing Pattern / Marten / Axon Event Sourcing
- adr.github.io / adr-tooling / Camunda 8 Workflow Patterns
- Arcade.dev Agent Skills vs Tools / Greptime Agent Observability 2025
- Honeycomb AI Observability + DORA 2025 / Datadog DORA Metrics

### pmo-tech-fork (20 URL)
- github/spec-kit / sphinx-needs / networkx / dependency-cruiser / madge
- pre-commit / lefthook / husky / alembic / dbmate / atlas / Flyway
- Prefect / dagster / Temporal / Airflow / Backstage / Port / Cortex
- LangGraph / AutoGen / CrewAI / LlamaIndex
- Choosing the Right Schema Migration Tool / Top Workflow Orchestration Tools / AI Agent Frameworks 2026

### pmo-tech-news (11 URL)
- Claude Code CHANGELOG / ClaudeLog / Releasebot
- OpenAI Codex Changelog / GPT-5.5 introduction / Cursor changelog / Devin vs Cursor
- OWASP LLM01 解説 / AI Agent Security 2026 / arxiv 2506.08837 (Dual-LLM Architecture)
- Stripe Engineering Blog / Vercel Engineering Blog
