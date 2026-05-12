---
doc_id: V2-CONCEPT
title: "プロジェクト管理型実行ハーネスシステム「ヘリックス開発」企画書"
status: draft
created: 2026-05-13
author: "PM (Opus) + Sonnet 4.6"
purpose: V2 全体設計の上流ゴール (V-model 強化 / DB 適合度向上 / 集大成) を明文化
next_doc: docs/v2/MASTER.md
predecessor: PLAN-001〜PLAN-068 (累積 PLAN 群、V1 = 現行 HELIX)
---

# プロジェクト管理型実行ハーネスシステム「ヘリックス開発」企画書

> 本文書は **既存ソースに意味を attach した形** で記述する。各項目には起源 PLAN / 実装ファイル / SKILL / memory への参照を併記する。

## §0 システム名

**HELIX 開発** = プロジェクト管理 + 実行ハーネス の融合体。

- 起源: [CLAUDE.md](../../CLAUDE.md) §概要 + [skills/SKILL_MAP.md](../../skills/SKILL_MAP.md)
- スコープ: 3 問題 (スパゲッティ化 / 契約漏れ / 設計デグレ) を **helix.db を制御中心とする 5 層 + 2 段** で構造的に防止し、AI エージェントを伴う開発を **プロジェクト管理型に実行** する

## §1 Vision

```
ソフトウェア開発の 3 重い問題 を構造的に解消する
  × AI エージェント時代の開発を harness で精密制御する
  × プロジェクト管理を機械検証可能な schema レベルで強制する
  = HELIX 開発
```

- 起源: 2026-05-13 セッションでユーザー発言「これがプロジェクト管理型実行ハーネスシステム『ヘリックス開発』の全容」
- 競合不在の領域: GitHub Copilot / Cursor (層 2 のみ) / LangChain (層 2+3 一部) / Jira (層 1 のみ) / TDD framework (層 5 のみ) — HELIX は **5 層 + 中央 DB で全方向統合**

## §2 解決対象: 3 つの重い問題

### [問題 1] コードのスパゲッティ化
- **意味**: 責務分散 / 重複 / refactor 怠慢の蓄積
- **検知装置**: [detector axis-09 (refactor opportunity)](../../cli/lib/detectors/axis_09_refactor.py) / [axis-03 (real duplicate)](../../cli/lib/detectors/axis_03_dup.py) / [axis-12 (connection deficiency)](../../cli/lib/detectors/axis_12_connection.py)
- **データ源**: `code_index` table (3-bucket taxonomy、PLAN-013) + `code_edges` (PLAN-063 W-2pre)

### [問題 2] 契約漏れ
- **意味**: 設計と実装と test の整合性破綻
- **検知装置**: [axis-12 (connection)](../../cli/lib/detectors/axis_12_connection.py) / [axis-11 (regression)](../../cli/lib/detectors/axis_11_regression.py) / [axis-07 (doc drift)](../../cli/lib/detectors/axis_07_doc_drift.py)
- **データ源**: `contract_entries` (PLAN-063 W-2pre、schema_hash + breaking_change_flag) + `design_review` (PLAN-065 W-2) + `test_design_entries` (PLAN-065 W-2)
- **CLI**: `cli/helix gate G<N> --pair-check <layer>` (PLAN-065 W-5 = commit 1c92bcf)

### [問題 3] 企画・設計デグレ
- **意味**: PLAN finalize 後の暗黙改変、retro 未実施
- **検知装置**: [axis-08 (plan integrity)](../../cli/lib/detectors/axis_08_plan_integrity.py) / [axis-07 (doc drift)](../../cli/lib/detectors/axis_07_doc_drift.py) / [axis-05 (plan debt loop)](../../cli/lib/detectors/axis_05_plan_debt.py)
- **データ源**: `plans` (PLAN-022) + `routing_decisions` (PLAN-024、carry/debt) + retro log
- **ゲート**: G0.5 企画突合ゲート (`skills/tools/ai-coding/references/gate-policy.md`)

→ 3 問題はすべて **helix.db への自動 record + detector + gate fail-close** で構造的防止。これ全体が **V-model 強化が成立する前提**。

## §3 制御中心: helix.db (v20、計 18+ table)

| 役割 | 主要 table | 起源 PLAN |
|---|---|---|
| 計画管理 | `plans`, `plan_tasks`, `routing_decisions` | PLAN-022 / PLAN-024 |
| 工程管理 | `gates`, `sprints`, `phase_gate_runs`, `retro` | PLAN-001 / PLAN-009 |
| 契約管理 | `contract_entries`, `code_edges` | PLAN-063 W-2pre (commit 80231ab) |
| コード管理 | `code_index` (3-bucket: coverage_eligible/private_helper/excluded) | PLAN-011 / 012 / 013 |
| 検証管理 | `test_baseline`, `test_design_entries`, `design_review` | PLAN-065 W-2 (commit ce98892、v20) |
| 観測管理 | `invocation_log`, `detector_runs`, `observe_*`, `accuracy_score` | PLAN-063 W-1a / W-1b / W-1c |
| Agent 統括 | `skill_usage`, `routing_decisions`, handover state | PLAN-022 / PLAN-023 |
| 操作 audit | `audit_decisions`, `deferred-findings.yaml` | PLAN-027 / PLAN-013 |
| 版数管理 | `schema_version` | helix_db.py:230 (CURRENT_SCHEMA_VERSION=20) |

実装: [cli/lib/helix_db.py](../../cli/lib/helix_db.py) (`_migrate_v1_to_v2` 〜 `_migrate_v19_to_v20`)

## §4 5 層構造 + 中央 DB

### 層 1: プロジェクト管理層 (PM + **PMO**)

#### PM (Opus、チャットのみ)
- **責務**: 工程管理 / 優先度判断 / 実装承認 / 統合 / エスカレーション判断
- **制約**: 実装禁止 (委譲のみ) — [feedback_pm_no_implementation_no_subagent.md](../../../.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_pm_no_implementation_no_subagent.md)
- **CLI 経路**: なし (Opus 自身がチャット)

#### PMO (PM 単独不足を補う層、追加 introduction)

**PMO 導入の歴史**:
- 起点: [project_helix_orchestration_v2.md](../../../.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/project_helix_orchestration_v2.md) (2026-05-08)
- 課題: PM (Opus) が長文 Read / 多 Grep / docs audit / **コスト管理** で context と token を浪費、bottleneck 化
- 解決: PMO Sonnet / PMO Haiku 新設 (read-only audit + 軽 docs write)
- 規約: PM だけで難判断確定させない → [pm-advisor](../../cli/roles/pm-advisor.conf) (Opus 4.7) 召喚

**PMO の責務 (PM 単独責務から委譲された機能)**:
| 機能 | 実装 |
|---|---|
| 構造化チェック (read-only audit) | [cli/roles/pmo-sonnet.conf](../../cli/roles/pmo-sonnet.conf) |
| **エージェントのコスト管理** (Codex / Opus / Sonnet / Haiku 残量) | [cli/helix-budget](../../cli/helix-budget) + [feedback_pmo_fallback_threshold_weekly.md](../../../.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_pmo_fallback_threshold_weekly.md) |
| ドキュメント整合性 audit | PMO Sonnet (`docs/**` read-only) |
| Agent 委譲判定の補助 | [skill_dispatcher.py](../../cli/lib/skill_dispatcher.py) + recommender (gpt-5.4-mini) |
| 軽 read-write タスク (docs 限定) | [cli/roles/pmo-haiku.conf](../../cli/roles/pmo-haiku.conf) (allow_paths=docs/**) |
| PM 級難判断アドバイス | [cli/roles/pm-advisor.conf](../../cli/roles/pm-advisor.conf) (Opus 4.7、read-only) |

**PMO 導入は HELIX の成熟過程**: 組織が拡大すると PM 単独 → PM+PMO に必ず分化する。HELIX も同パターン。

### 層 2: HELIX オーケストレーション (実装精度向上)

**Multi-LLM 制御**:
- **主要エージェント** ([cli/config/models.yaml](../../cli/config/models.yaml) 正本):
  - PM = `claude-opus-4-7`
  - TL = `gpt-5.5`
  - SE = `gpt-5.4`
  - PG = `gpt-5.3-codex-spark` / `gpt-5.3-codex`
  - 専門ロール: QA / Security / DBA / DevOps / Docs / Research / Legacy / Perf / FE / classifier / effort-classifier
- **サブエージェント**: PMO Sonnet / PMO Haiku / recommender / pm-advisor / tl-advisor (impl-sonnet, PLAN-067 系で導入)
- **委譲機構**: [cli/helix-codex](../../cli/helix-codex) / [cli/helix-claude](../../cli/helix-claude) (役割注入 + 共通マップ + コスト guard)
- **handover protocol**: [cli/helix-handover](../../cli/helix-handover) + `.helix/handover/CURRENT.json` (PM↔TL セッション跨ぎ)
- **vendor 切替 trace**: `routing_decisions` table (PLAN-024)

### 層 3: コマンド群 (短縮化)

実行効率を上げる CLI 群:
- [cli/helix](../../cli/helix) ルーター + 60+ サブコマンド
- slash commands ([.claude/commands/](../../.claude/commands/))
- hooks ([.claude/hooks/](../../.claude/hooks/) PreToolUse / SessionStart / PostToolUse)
- 代表: [cli/helix-doctor](../../cli/helix-doctor) (整合性 audit) / [cli/helix-budget](../../cli/helix-budget) (コスト) / [cli/helix-detect](../../cli/helix-detect) (analytics、PLAN-063 W-2)

### 層 4: スキル群 (判断迷い解消)

LLM が判断に迷わないための reference:
- 102+ SKILL.md ([skills/SKILL_MAP.md](../../skills/SKILL_MAP.md))
- catalog: [cli/lib/skill_catalog.py](../../cli/lib/skill_catalog.py) + recommender ([skill_recommender.py](../../cli/lib/skill_recommender.py)、gpt-5.4-mini、1h キャッシュ)
- 中核 SKILL:
  - [workflow/api-contract](../../skills/workflow/api-contract/SKILL.md) — 契約設計
  - [integration/agent-design](../../skills/integration/agent-design/SKILL.md) — 11 axis、L2/L3 設計
  - [integration/agent-cost-design](../../skills/integration/agent-cost-design/SKILL.md) — Phase 0-5 コスト確定 (2026-05-13 統合、本セッションで追加)
  - [integration/agent-teams](../../skills/integration/agent-teams/SKILL.md) — multi-agent 協調
  - [workflow/verification](../../skills/workflow/verification/SKILL.md) — Spec 駆動検証
  - [workflow/adversarial-review](../../skills/workflow/adversarial-review/SKILL.md) — クリティカルレビュー

### 層 5: 検証ツール群 (未確定要素検証)

実装前 / 実装中 / 実装後の検証:
- `verify/*.sh` (Scrum S3 検証スクリプト、毎回全実行で regression 蓄積)
- detector 14 軸 ([cli/lib/detectors/axis_01_dead.py](../../cli/lib/detectors/axis_01_dead.py) 〜 [axis_14_orchestration.py](../../cli/lib/detectors/axis_14_orchestration.py)) — PLAN-063 W-3〜W-10 完了 (stub 0)
- gate runner 連動 ([cli/helix-gate](../../cli/helix-gate)、PLAN-063 W-11 で G2/G4/G6 auto-run)
- [cli/helix-scrum](../../cli/helix-scrum) (S0-S4 仮説検証)
- pair-check CLI ([cli/helix-gate](../../cli/helix-gate) `--pair-check <layer>`、PLAN-065 W-5、commit 1c92bcf)
- characterization tests (Reverse R1 で利用)

## §5 2段設計モデル

```
段 1: Product (実装本体、deliverable)
   ├─ Automation-SEO (本セッションで参照、v2/backend, v2/frontend, v2/plugin)
   ├─ 今後 HELIX で管理する全 product
   └─ BE/FE/DB/Fullstack drive で作る具体的なコード

段 2: HELIX = プロジェクト管理型実行ハーネス (全容)
   ├─ 層 1 PM/PMO
   ├─ 層 2 Orchestration (Agent Transformation サブ層を含む)
   ├─ 層 3 Command
   ├─ 層 4 Skill
   ├─ 層 5 Verify
   └─ 中央 helix.db
```

- 起源: 2026-05-13 セッションで [agent-design SKILL](../../skills/integration/agent-design/SKILL.md) の「型 = 要素定義 + フレーム化」還元式と「前段制約 / 後段責務」概念をシステム全体に拡張
- 重要発見: **HELIX 全体が段 2**。「Agent Transformation Layer」は段 2 内サブ層であって独立段ではない
- 段 1 は agent agnostic (HELIX schema 化を経て、初めて段 2 が制御可能)

### 2 段の関係を schema 化 (V2 で導入予定)

```sql
CREATE TABLE managed_products (
  id INTEGER PRIMARY KEY,
  product_name TEXT NOT NULL,
  product_path TEXT NOT NULL,
  drive TEXT,
  mode TEXT,
  helix_version INTEGER,
  registered_at TEXT NOT NULL
);
```

HELIX 自身を HELIX で管理する **dogfood** も同 schema で扱える。

## §6 V-model 強化 = 段 2 の能力強化集大成 = DB 適合度向上

### V-model の構造 ([PLAN-065 §2.5](../plans/PLAN-065-qa-strictness.md) で導入)

```
左脚 (設計)                  右脚 (検証)
─────────────────────       ─────────────────────
planning             ←→     operational (運用 KPI)
requirement          ←→     acceptance (受入)
architecture         ←→     system_integration
detailed             ←→     integration
functional           ←→     unit
        ↓                          ↑
        └─[L4 code review apex]────┘
          (実装 + test 両 review、dual-target)
```

### 2 軸検査

| 軸 | 内容 | 実装 |
|---|---|---|
| **縦レビュー** | 同脚内の上位 → 下位 layer 連鎖 (粒度落ち検知) | `design_review.review_axis='vertical'` (PLAN-065 W-2) |
| **横レビュー** | 同 phase 設計 ↔ test 1:1 対応 | `design_review.review_axis='horizontal'` |

各 gate (G1-G11) は **縦 + 横 両方 passed** で通過。実装: [cli/helix-gate](../../cli/helix-gate) `--pair-check <layer> --plan-id <id>` (PLAN-065 W-5)。

### 4 layer chain traceability

```
contract_entries (設計、5 design_level、PLAN-063 W-2pre + PLAN-065 W-2)
       ↓
code_index (実装 symbol、PLAN-011/012/013)
       ↓  [L4 code review apex で交差]
test_design_entries (test 設計、5 test_level、PLAN-065 W-2)
       ↓
test_baseline (test 実行結果 + coverage、PLAN-065 W-2)
```

各 PLAN ごとに 4 層全部埋まる率 = **V-model 整合度スコア = QA 健全性 KPI**。

### V-model 強化 = DB 適合度向上

V-model 強化の本質 = **helix.db に蓄積される設計・実装・検証 metadata の整合性を schema レベルで強制**。

DB 適合度が上がる ⇒ 3 問題の検知率が上がる ⇒ 構造的防止が機能する。
本 V2 整理の core 目的は **DB 適合度向上 = V-model 強化** の構造改革。

## §7 多軸 matrix (Mode × Drive × Layer)

| 軸 | 値 | 段 | 出典 |
|---|---|---|---|
| **Mode** | Forward / Reverse / Scrum | 段 1・段 2 共通 | [SKILL_MAP §HELIX Reverse](../../skills/SKILL_MAP.md) / [§HELIX Scrum](../../skills/SKILL_MAP.md) |
| **Drive** | BE / FE / DB / Fullstack | 段 1 | [SKILL_MAP §駆動タイプ](../../skills/SKILL_MAP.md) |
| **Design Layer** | planning / requirement / architecture / detailed / functional | 5 値固定 | PLAN-065 §2.5 |
| **Test Layer** | operational / acceptance / system_int / integration / unit | 5 値固定 | PLAN-065 §2.5 |
| **Agent 直交 (cost / 非決定性 / vendor)** | 段 2 のみ | 直交軸 | [agent-design SKILL](../../skills/integration/agent-design/SKILL.md) 11 axis |

**設計方針**:
- enum (5 design / 5 test) は **固定**、移行コスト最小化 (PLAN-065 既存 schema 維持)
- semantic は **`cli/config/vmodel-semantics.yaml` で drive 別外部化** (V2 で新規)
- `contract_entries` / `test_design_entries` / `design_review` に **drive 列追加** (V2 で migration v21)
- Agent 軸は段 2 のみに存在 (段 1 は agent agnostic)

## §8 Mode 別の特殊性

### Forward HELIX (L0-L11)
- 標準 V-model
- 4 drive × 5 layer × 5 test layer
- Fullstack は Phase A (BE ∥ FE) → Phase B (L4.5 結合) の 2 段
- 起源: [SKILL_MAP §オーケストレーションフロー](../../skills/SKILL_MAP.md)

### Reverse HELIX (R0-R4 + RGC)
- 既存コードからの設計復元 (5 type matrix: code / design / upgrade / normalization / fullback)
- R0 Evidence ↔ characterization test
- R1 Observed Contracts ↔ contract validation
- R2 As-Is Design ↔ design conformance
- R3 Intent Hypotheses ↔ hypothesis validation
- R4 Gap Routing ↔ gap closure
- RGC ↔ closure validation
- 実装: [cli/helix-reverse](../../cli/helix-reverse) + [workflow/reverse-r0〜r4 + rgc SKILL](../../skills/workflow/) (PLAN-040 系)

### Scrum (S0-S4)
- 仮説検証駆動
- S0 Backlog → S1 Plan → S2 PoC → S3 Verify (verify/*.sh) → S4 Decide → Forward HELIX 接続
- 実装: [cli/helix-scrum](../../cli/helix-scrum) (PLAN-022 系)

## §9 Drive 別の特殊性 (Base System 段 1)

### BE drive (標準、HELIX default)
- API 設計 + module 構造
- 標準 V-model

### FE drive (mock 駆動、**現在弱点**)
- mock + state-events.md で architecture layer
- mock → 本実装 promotion (layer migration)
- L5 visual refinement 必須 (G5 ゲート)
- test: visual regression / playwright / axe a11y / snapshot
- **弱点詳細**:
  - V-model layer 紐付け薄 (FE contract type 不在: component_props / state_events / visual_token / a11y / screen_transition)
  - 専用 detector 不足 (mock_to_impl_promotion / design_token_drift / a11y_regression が無い)
  - 専用 command 不足 (visual-diff / a11y / playwright wrapper が無い)
  - FE 専用 agent 停止 (CLAUDE.md 明記、TL + PMO + QA 集中) — 関連: [project/ui](../../skills/project/ui/SKILL.md) / [mock-driven-development](../../skills/agent-skills/mock-driven-development/) (PLAN-022 系で導入)
- 関連 SKILL: [common/visual-design](../../skills/common/visual-design/SKILL.md) / [design-tools/web-system](../../skills/design-tools/web-system/SKILL.md) / [agent-skills/frontend-ui-engineering](../../skills/agent-skills/frontend-ui-engineering/SKILL.md)

### DB drive
- ER 図 + 正規化 + migration が dominant
- schema integrity / migration test / query perf
- layer 偏り (schema 厚、その他薄)
- 関連 SKILL: [project/db](../../skills/project/db/SKILL.md)

### Fullstack drive
- Phase A: BE ∥ FE (各々独立 V-model)
- Phase B: L4.5 結合 (新 drive 'fullstack' で結合 V-model)
- contract test + E2E user journey
- 起源: [SKILL_MAP §駆動タイプ別 L2〜L11](../../skills/SKILL_MAP.md)

## §10 Agent Transformation サブ層 (段 2 内)

主要エージェント (Multi-LLM) を制御するための段 2 内サブ層。

```
段 2 (HELIX) 内のサブ層
   ├─ Tool Registry         ← helix-* CLI を agent から呼ぶ
   ├─ Analysis Infra        ← code_index / contract / detector の JSON 出力
   ├─ Agent Orchestration   ← PM / TL / SE / PG / 専門ロール
   ├─ LLM Router            ← multi-vendor (Claude / Codex / Sonnet / Haiku) 切替
   ├─ Cost Guard            ← helix budget + 各 conf
   └─ Structured Output     ← schema-validated tool return
```

**Agent 直交 3 軸** (Agent 設計特有):
1. **コスト軸** — [agent-cost-design SKILL Phase 0-5](../../skills/integration/agent-cost-design/SKILL.md) + [helix budget](../../cli/helix-budget) + 1.2 倍上振れ係数固定
2. **非決定性軸** — output pattern match / drift detection (PLAN-068 候補で対応予定)
3. **マルチベンダー軸** — vendor 切替 / fallback policy ([routing_decisions](../../cli/lib/helix_db.py) table、[agent-cost-design references/multi-vendor.md](../../skills/integration/agent-cost-design/references/multi-vendor.md))

**参考実装**: Automation-SEO `v2/backend/app/services/{base_agent, llm_router_service, agent_registry, cost_guard_service, agents/*}` — HELIX で作られた段 1 product 内の段 2 模倣サブ層 (24 agent + BaseAgent abstract + multi-LLM Router + cost guard)。

## §11 集大成スタンス: 蓄積知見の formalize (V1 → V2)

### HELIX V1 で既に存在する 12+ capability

| 蓄積知見 | 起源 PLAN / 実装 | V2 での扱い |
|---|---|---|
| V-model schema + pair-check CLI | PLAN-065 W-1〜W-5 (commit 45a9b98 / ce98892 / 1c92bcf) | drive 列拡張 + ER/process map 統合 |
| 14 detector + gate runner 連動 | PLAN-063 W-3〜W-11 (本セッションで完了) | FE 弱点 detector 追加 |
| 契約 extractor (Python AST / SQL / YAML) | PLAN-063 W-2pre (commit 80231ab) | drive 別 contract type 拡張 |
| handover protocol | PLAN-022 系 / [cli/helix-handover](../../cli/helix-handover) | 維持 + V2 で statemap 化 |
| skill 推挙 (gpt-5.4-mini) | PLAN-022 / PLAN-023 (commit 2aa96bf〜303d9d6) | V-model layer × drive tag 付与 |
| Reverse mode (R0-R4 + RGC) | PLAN-040 系 / [reverse-r0〜rgc SKILL](../../skills/workflow/) | mode 軸として V-model 統合 |
| Scrum mode (S0-S4) | [helix scrum](../../cli/helix-scrum) | 同上 |
| Agent design 11 axis | [integration/agent-design](../../skills/integration/agent-design/SKILL.md) (PLAN-024 Sprint 2) | 段 2 Agent Transformation の正本 reference |
| Agent cost design Phase 0-5 | [integration/agent-cost-design](../../skills/integration/agent-cost-design/SKILL.md) (本セッション統合) | PM/PMO 層のコスト管理に直結 |
| Multi-LLM routing | [cli/helix-codex](../../cli/helix-codex) / [helix-claude](../../cli/helix-claude) / [routing_decisions](../../cli/lib/helix_db.py) | 段 2 LLM Router 集約 |
| code_index 3-bucket taxonomy | PLAN-013 (commit b12cc10) | V2 で `managed_products` link 追加 |
| skill catalog + recommender | PLAN-022/023 + [skill_dispatcher.py](../../cli/lib/skill_dispatcher.py) | V-model layer に紐付け |
| PMO 導入 | [project_helix_orchestration_v2.md](../../../.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/project_helix_orchestration_v2.md) (2026-05-08) | V2 で正本化 (本企画書 §4 層 1) |

→ V2 = これらを **5 層 × 3 問題 マトリクスに再 align + V-model multi-axis + FE 弱点補強 + DB 適合度向上**。

### V2 = 上流から組み上げる (集大成 vs incremental patch)

```
[V1 (PLAN-001〜068 累積)] = 現状、incremental patch の集積、一部未実装 carry
                ↓ 集大成 audit (Phase A)
[V2 (docs/v2/)]         = 上流から coherent な architecture、DB 適合度高
```

V1 の PLAN markdown は削除せず参照可能な history として保持。V2 が canonical となる。

## §12 V1 → V2 移行戦略

| 旧 (V1) | 新 (V2) | 移行方針 |
|---|---|---|
| PLAN-001〜068 累積 (一部未実装 carry) | docs/v2/ Phase A〜I に統合 | Phase G (Legacy Import) で 1 件ずつ吸収 |
| helix.db v20 (incremental migration) | helix.db v21 (V2 一括 migration、drive 列 + 新 table) | 後方互換、Phase C で実装 |
| 5 層が散在実装 | 5 層が schema 強制、role conf を class 化 | Phase D (Orchestration) |
| PM 単独運用 (memory feedback で痛みあり) | **PM + PMO** (cost / audit / 補助 を分離) | 既導入、V2 で正本化 |
| Agent Transformation 暗黙 | Phase D で明示 (BaseAgent / LLM Router / Cost Guard / OpenAPI fragments) | Phase D |
| FE 弱点 | Phase F で構造強化 | 専用 detector / command / contract type 追加 |
| 集大成 = 概念のみ | Phase A audit で正本化 | docs/v2/A-audit/ |

## §13 Automation-SEO との関係

Automation-SEO ([git@github.com:RetryYN/Automation-SEO.git](https://github.com/RetryYN/Automation-SEO)) は **HELIX で作られた段 1 Product の参考実装**:

| Automation-SEO の構造 | HELIX 側の対応 |
|---|---|
| `v2/backend/app/services/` (40+ services) | 段 1 業務 logic (LLM 不在) |
| `v2/backend/app/services/agents/` (24 agent: Step A/B/C/Maintenance/Crosscut) | 段 2 内 Agent Orchestration サブ層 |
| `v2/backend/app/services/base_agent.py` (`__init_subclass__` 強制) | HELIX role conf を class 化する V2 目標 |
| `v2/backend/app/services/llm_router_service.py` | [cli/helix-codex](../../cli/helix-codex) / [helix-claude](../../cli/helix-claude) 統合先 |
| `v2/backend/app/services/agent_registry.py` | role 一覧の DB 化 (V2 で `agent_registry` table 追加) |
| `v2/backend/app/services/cost_guard_service.py` | [cli/helix-budget](../../cli/helix-budget) + agent-cost-design SKILL の実装側 |
| `v2/contracts/fragments/openapi.fragment-*.json` | `contract_entries` を fragment 単位で OpenAPI 出力 (V2 Phase D) |
| `v2/backend/app/workers/` (cron-like) | V2 Phase H (Automation) の参考 |

**重要**: Automation-SEO は **HELIX で作られた成果物**、HELIX 自身ではない。HELIX が Automation-SEO を制御する関係 (段 2 → 段 1)。V2 で Automation-SEO の pattern を逆方向 (段 1 → 段 2 への教訓) として吸収する。

## §14 次の段階

### docs/v2/MASTER.md 着手
本企画書 (CONCEPT.md) を base に、master plan を起こす。MASTER.md には:
- §1 V2 全体方針 + Phase A〜I の outline + 入出力 + dependency
- §2 各 Phase の担当層 + 委譲先 ([cli/ROLE_MAP.md](../../cli/ROLE_MAP.md) 参照)
- §3 V1 → V2 移行 timeline + Phase G Legacy Import 対応表
- §4 集大成 audit (Phase A) の指針
- §5 完了判定基準 (V-model 整合度スコア / DB 適合度 / FE 強化完了 / dogfood 確認)

### Phase A (集大成 audit) を最初の dispatch に
- `legacy-plans-carry.md` — PLAN-001〜068 未実装 carry 棚卸し ([helix plan list](../../cli/helix-plan) + `.helix/audit/deferred-findings.yaml`)
- `capability-matrix.md` — 5 層 × 3 問題 現状 mapping ([helix code stats](../../cli/helix-code) + [skill list](../../cli/helix-skill) + [helix detect list](../../cli/helix-detect))
- `fe-weakness-analysis.md` — FE 弱点炙り出し
- `accumulated-knowledge.md` — 12+ 蓄積知見の正本化

## §15 設計者目線でのコメント

- **HELIX の独自性**: 5 層 + 中央 DB + 2 段設計 + V-model + multi-mode + multi-drive を統合した方法論 + harness は **単一競合がない**
- **DB 適合度が key driver**: V-model 強化の本質は schema enforcement、それが上がれば 3 問題の検知率も上がる
- **PMO 導入は HELIX の成熟度を示す**: 組織が拡大時に PM 単独 → PM+PMO に分化する成熟過程と同じ
- **dogfood 重視**: HELIX で HELIX 自身を開発できることが究極の validation
- **集大成 = 知見蓄積の formalize**: 散在のままでは agent / human のどちらも迷う、schema 化で迷いを構造的に消す
- **既存 source の意味付け**: 本企画書のように既存ファイル / PLAN / SKILL / memory への参照 attach は **V-model 縦軸 traceability** そのもの

## §16 既存機能 役割定義カタログ — 「HELIX とは？」を機能 inventory で答える

> 本セクションは既存の HELIX 機能を **「何のためにあるか (= 役割定義)」** で網羅する。各機能が 5 層 × 段 1/段 2 の中でどう位置するか明示することで、**HELIX 開発 とは何か** が機能 inventory から自明になる。

### §16.1 層 1 (PM / PMO) 機能 役割定義

| 機能 | 出典 | 役割定義 (= 何のためにあるか) |
|---|---|---|
| **PM (Opus、チャット)** | [cli/config/models.yaml](../../cli/config/models.yaml) `pm: claude-opus-4-7` | 大局判断・統合・委譲指示。実装禁止 |
| **pm-advisor** | [cli/roles/pm-advisor.conf](../../cli/roles/pm-advisor.conf) (Opus 4.7、read-only) | PM 級難判断の adversarial advice (本セッションで追加) |
| **PMO Sonnet** | [cli/roles/pmo-sonnet.conf](../../cli/roles/pmo-sonnet.conf) | 構造化 audit / docs 整合性 / 判断補助 (read-only) |
| **PMO Haiku** | [cli/roles/pmo-haiku.conf](../../cli/roles/pmo-haiku.conf) | 軽 docs 修正 / Web 検索 (docs/** read-write) |
| **helix budget** | [cli/helix-budget](../../cli/helix-budget) | **エージェントのコスト残量監視** (Opus / Codex / Sonnet / Haiku、PMO 担当領域) |
| **helix plan** | [cli/helix-plan](../../cli/helix-plan) | PLAN draft / review / finalize / lint / import / reset (PM の工程管理 CLI) |
| **helix sprint** | [cli/helix-sprint](../../cli/helix-sprint) | L4 マイクロスプリント管理 (.1a→.1b→.2→.3→.4→.5) |
| **helix gate** | [cli/helix-gate](../../cli/helix-gate) | G0.5-G11 / RG0-RGC ゲート判定 + `--pair-check` (V-model 縦/横 review) |
| **helix retro** | [cli/helix-retro](../../cli/helix-retro) | ミニレトロ (G2/G4/L8 で実施) |
| **helix handover** | [cli/helix-handover](../../cli/helix-handover) | PM↔TL セッション跨ぎ state (`.helix/handover/CURRENT.json`) |
| **helix size** | [cli/helix-size](../../cli/helix-size) | タスクサイジング (S/M/L) + フェーズスキップ判定 + drive 判定 |
| **helix pr** | [cli/helix-pr](../../cli/helix-pr) | gate 結果から PR 自動生成 |
| **ROLE_MAP.md** | [cli/ROLE_MAP.md](../../cli/ROLE_MAP.md) | role 定義正本 (17 ロール) |
| **models.yaml** | [cli/config/models.yaml](../../cli/config/models.yaml) | role → model mapping 正本 (実装が正、ドキュメント追従) |

### §16.2 層 2 (HELIX オーケストレーション) 機能 役割定義

| 機能 | 出典 | 役割定義 |
|---|---|---|
| **helix-codex** | [cli/helix-codex](../../cli/helix-codex) | Codex 委譲 launcher (役割注入 + 共通 SKILL マップ + コスト guard + `--consent` mode) |
| **helix-claude** | [cli/helix-claude](../../cli/helix-claude) | Claude 委譲 launcher (PMO / Advisor / impl-sonnet 経路) |
| **TL (gpt-5.5)** | [cli/roles/tl.conf](../../cli/roles/tl.conf) | 設計・レビュー・デバッグ (effort=high) |
| **SE (gpt-5.4)** | [cli/roles/se.conf](../../cli/roles/se.conf) | 契約・高度実装・リファクタリング (effort=high) |
| **PG (gpt-5.3-codex-spark)** | [cli/roles/pg.conf](../../cli/roles/pg.conf) | 速度重視単機能実装 (effort=low-medium) |
| **QA (5.5)** | [cli/roles/qa.conf](../../cli/roles/qa.conf) | テスト戦略 + テスト critique (PLAN-065 W-1 で `--reviewer qa` 対応) |
| **Security (5.3)** | [cli/roles/security.conf](../../cli/roles/security.conf) | OWASP / 認証認可 / 秘密情報 / 依存脆弱性 (PLAN-066 候補) |
| **DBA / DevOps / Perf** | [cli/roles/](../../cli/roles/) | DB / インフラ / 性能 |
| **Docs (5.4)** | [cli/roles/docs.conf](../../cli/roles/docs.conf) | ドキュメント本文起草 (>100 行) |
| **Research (5.4)** | [cli/roles/research.conf](../../cli/roles/research.conf) | 大規模コード精読 / スキャン |
| **Legacy / FE** | [cli/roles/](../../cli/roles/) | レガシー / FE 設計支援 |
| **tl-advisor** | [cli/roles/tl-advisor.conf](../../cli/roles/tl-advisor.conf) (本セッション追加) | TL 級難判断アドバイス (read-only) |
| **impl-sonnet** | [cli/roles/impl-sonnet.conf](../../cli/roles/impl-sonnet.conf) | Codex 上限到達時の Sonnet 実装代替 |
| **classifier / recommender / effort-classifier** | gpt-5.4-mini | タスク分類 / skill 推挙 / 工数判定 |
| **routing_decisions** | helix.db (PLAN-024) | vendor / model / role 切替 trace |
| **invocation_log** | helix.db (PLAN-063 W-1a) | LLM 呼び出し全履歴 + cost 集計基盤 |
| **handover protocol** | `.helix/handover/CURRENT.json` (PLAN-029 系) | PM↔TL セッション跨ぎ statemap |

### §16.3 層 3 (コマンド群) 機能 役割定義

| 機能 | 出典 | 役割定義 |
|---|---|---|
| **helix init** | [cli/helix-init](../../cli/helix-init) | プロジェクト初期化 (.helix/ + CLAUDE.md + .gitignore) |
| **helix code** | [cli/helix-code](../../cli/helix-code) | code_index 操作 (build / find / show / stats / dup / list) |
| **helix detect** | [cli/helix-detect](../../cli/helix-detect) | 14 detector 実行 + dashboard (PLAN-063) |
| **helix doctor** | [cli/helix-doctor](../../cli/helix-doctor) | 整合性 audit (models.yaml ↔ ROLE_MAP ↔ CLAUDE.md drift) |
| **helix skill** | [cli/helix-skill](../../cli/helix-skill) | skill list / show / search / use / chain / stats / catalog rebuild |
| **helix scrum** | [cli/helix-scrum](../../cli/helix-scrum) | Scrum mode (S0-S4 仮説検証) |
| **helix reverse** | [cli/helix-reverse](../../cli/helix-reverse) | Reverse mode (R0-R4 + RGC、5 type matrix) |
| **helix asset** | [cli/helix-asset](../../cli/helix-asset) | 画像生成 preset 7 種 (banner/logo/hero/card/thumb/icon/bg、PLAN-064) |
| **helix matrix** | [cli/helix-matrix](../../cli/helix-matrix) | 工程マトリクス管理 |
| **helix test** | [cli/helix-test](../../cli/helix-test) | shell + pytest + bats 統合実行 |
| **helix review** | [cli/helix-review](../../cli/helix-review) | uncommitted 差分レビュー (Codex 経由) |
| **helix log** | [cli/helix-log](../../cli/helix-log) | invocation_log 可視化 |
| **helix log report** | 同上 | event log report 出力 |
| **helix team** | [cli/helix-team](../../cli/helix-team) | 複数 role 協調実行 |
| **helix verify** | [cli/helix-verify](../../cli/helix-verify) | verify/*.sh 一括実行 |
| **slash commands** | [.claude/commands/](../../.claude/commands/) | /ship / /code-simplify / /build / /test / /spec / /sdd-review / /sdd-plan / etc. (Claude Code 統合) |
| **hooks** | [.claude/hooks/](../../.claude/hooks/) | PreToolUse / SessionStart / PostToolUse (event-driven 制御) |

### §16.4 層 4 (スキル群) 機能 役割定義

> 102+ SKILL は [skills/SKILL_MAP.md](../../skills/SKILL_MAP.md) を正本とする。本表は **代表 SKILL の役割定義** のみ。

#### workflow/ (HELIX 工程の正本)

| SKILL | 役割定義 |
|---|---|
| [project-management](../../skills/workflow/project-management/SKILL.md) | PM 工程管理の正本 |
| [estimation](../../skills/workflow/estimation/SKILL.md) | 開発工数見積もり (story points) |
| [requirements-handover](../../skills/workflow/requirements-handover/SKILL.md) | 要件引継ぎ |
| [design-doc](../../skills/workflow/design-doc/SKILL.md) | 設計文書起草 |
| [api-contract](../../skills/workflow/api-contract/SKILL.md) | API 契約定義 (V-model architecture/detailed) |
| [dependency-map](../../skills/workflow/dependency-map/SKILL.md) | 依存マップ |
| [verification](../../skills/workflow/verification/SKILL.md) | Spec 駆動検証 (V-model 全 layer) |
| [adversarial-review](../../skills/workflow/adversarial-review/SKILL.md) | クリティカルレビュー (G2/G4 で発火) |
| [reverse-r0〜r4 / rgc](../../skills/workflow/) | Reverse HELIX 各 phase |
| [research / poc / gate-planning / threat-model / etc.](../../skills/workflow/) | 27 SKILL (2026-04-17 追加) |

#### common/ (横断 SKILL)

| SKILL | 役割定義 |
|---|---|
| [visual-design](../../skills/common/visual-design/SKILL.md) | ビジュアル設計 (FE drive 中心) |
| [code-review](../../skills/common/code-review/SKILL.md) | コードレビュー (L4 apex で発火) |
| [security](../../skills/common/security/SKILL.md) | セキュリティ対策 |
| [testing](../../skills/common/testing/SKILL.md) | テスト書き方 (L4 実装時) |
| [performance / error-fix / refactoring / etc.](../../skills/common/) | 12 SKILL |

#### integration/ (エージェント設計の正本)

| SKILL | 役割定義 |
|---|---|
| [agent-design](../../skills/integration/agent-design/SKILL.md) | LLM agent 11 axis 設計判断 (型 = 要素定義 + フレーム化) |
| [agent-teams](../../skills/integration/agent-teams/SKILL.md) | multi-agent 協調 |
| [agent-cost-design](../../skills/integration/agent-cost-design/SKILL.md) | **エージェント構築前のコスト確定** (Phase 0-5、本セッションで統合) |

#### tools/ (HELIX 制御 SKILL)

| SKILL | 役割定義 |
|---|---|
| [ai-coding](../../skills/tools/ai-coding/SKILL.md) | HELIX 運用正本 (workflow-core.md / gate-policy.md) |
| [ide-tools / web-search / ai-search](../../skills/tools/) | tool 別運用 |

#### agent-skills/ (addyosmani 由来 + HELIX 独自)

| SKILL | 役割定義 |
|---|---|
| [spec-driven-development](../../skills/agent-skills/spec-driven-development/) | 仕様駆動 (LLM 限定なし) |
| [mock-driven-development](../../skills/agent-skills/mock-driven-development/) | FE drive 駆動の核心 |
| [helix-scrum](../../skills/agent-skills/helix-scrum/) | Scrum mode 拡張 |
| その他 22 SKILL | addyosmani 由来 19 + HELIX 独自 3 |

### §16.5 層 5 (検証ツール群) 機能 役割定義

#### Detector 14 軸 (PLAN-063 完了、stub 0)

| Axis | ファイル | gate | 役割定義 |
|---|---|---|---|
| axis-01 | [axis_01_dead.py](../../cli/lib/detectors/axis_01_dead.py) | G4 | dead code drift (vulture + code_index 突合) |
| axis-02 | [axis_02_coverage.py](../../cli/lib/detectors/axis_02_coverage.py) | G4 | coverage erosion (前回比悪化検知) |
| axis-03 | [axis_03_dup.py](../../cli/lib/detectors/axis_03_dup.py) | G4 | real duplicate (AST jaccard ≥ 0.85) |
| axis-04 | [axis_04_skill_decay.py](../../cli/lib/detectors/axis_04_skill_decay.py) | - | skill resolution decay (usage 0 件 + failing skill) |
| axis-05 | [axis_05_plan_debt.py](../../cli/lib/detectors/axis_05_plan_debt.py) | G6 | plan debt loop (recurring carry + 累積増加) |
| axis-06 | [axis_06_naming.py](../../cli/lib/detectors/axis_06_naming.py) | G2 | naming confusion (Levenshtein 類似 + case 混在 + 廃止 skill 名) |
| axis-07 | [axis_07_doc_drift.py](../../cli/lib/detectors/axis_07_doc_drift.py) | G2 | doc expression drift (CLAUDE/AGENTS/SKILL_MAP/models cross-check) |
| axis-08 | [axis_08_plan_integrity.py](../../cli/lib/detectors/axis_08_plan_integrity.py) | G6 | plan-retro integrity (finalized + commit 突合) |
| axis-09 | [axis_09_refactor.py](../../cli/lib/detectors/axis_09_refactor.py) | G4 | refactoring opportunity (god file + arg explosion + refactor carry) |
| axis-10 | [axis_10_relation_graph.py](../../cli/lib/detectors/axis_10_relation_graph.py) | - | relation graph (全 detector + code_edges + contract + hook、mermaid 出力) |
| axis-11 | [axis_11_regression.py](../../cli/lib/detectors/axis_11_regression.py) | G6 | regression (PASS→FAIL flaky 判定 + schema_hash 変化 + silent_error) |
| axis-12 | [axis_12_connection.py](../../cli/lib/detectors/axis_12_connection.py) | G2 | connection deficiency (broken import / hook orphan / cli drift / trigger orphan) |
| axis-13 | [axis_13_model_skill.py](../../cli/lib/detectors/axis_13_model_skill.py) | - | model & skill analytics (A〜F 6 観点) |
| axis-14 | [axis_14_orchestration.py](../../cli/lib/detectors/axis_14_orchestration.py) | G4 | orchestration integrity (pm_direct_edit / scope_violation / handover_stale / role_breach) |

#### その他検証ツール

| 機能 | 出典 | 役割定義 |
|---|---|---|
| **pair-check CLI** | [cli/helix-gate](../../cli/helix-gate) `--pair-check` | V-model 縦/横 review 機械検証 (PLAN-065 W-5) |
| **skip annotation linter** | [cli/lib/skip_annotation_linter.py](../../cli/lib/skip_annotation_linter.py) | HELIX-SKIP フォーマット強制 (PLAN-065 W-3) |
| **verify/*.sh** | プロジェクト固有 | Scrum S3 検証 / 毎回全実行で regression 蓄積 |
| **session-start dashboard** | [cli/lib/session_start_helpers.py](../../cli/lib/session_start_helpers.py) | セッション開始時に 14 detector 最新 verdict 表示 (PLAN-063 W-11) |
| **bats / pytest 統合** | [cli/helix-test](../../cli/helix-test) | shell + Python テスト統合 |

### §16.6 helix.db テーブル 役割定義 (現 v20、計 18+)

| Table | 起源 | 役割定義 |
|---|---|---|
| `schema_version` | PLAN-001 | DB スキーマ版数管理 |
| `plans` | PLAN-022 | PLAN frontmatter + status (draft/reviewed/finalized) |
| `plan_tasks` | PLAN-022 | PLAN 内タスク詳細 |
| `routing_decisions` | PLAN-024 | model / role / vendor 切替判断記録 |
| `gates` / `phase_gate_runs` | PLAN-009 | gate 通過判定履歴 |
| `sprints` / `sprint_metrics` | PLAN-029 | Sprint 状態 + KPI |
| `retro` | PLAN-002 | ミニレトロ記録 |
| `code_index` | PLAN-011/012/013 | コード symbol catalog (3-bucket taxonomy) |
| `code_edges` | PLAN-063 W-2pre | call graph (caller → callee) |
| `contract_entries` | PLAN-063 W-2pre | 契約 registry (Python AST / SQL / YAML 抽出) |
| `detector_runs` | PLAN-063 W-1a | 14 detector 実行履歴 |
| `invocation_log` | PLAN-063 W-1a | LLM 呼び出し全履歴 + redaction |
| `skill_usage` | PLAN-022 | skill 利用統計 + outcome |
| `accuracy_score` | PLAN-009 | 検証精度スコア |
| `observe_*` | PLAN-009 系 | 観測データ |
| `audit_decisions` | PLAN-013 | 操作 audit |
| `test_baseline` | **PLAN-065 W-2** | テスト実行 baseline + flaky 判定 |
| `test_design_entries` | **PLAN-065 W-2** | テスト設計 (V-model 5 test_level + paired_design_level) |
| `design_review` | **PLAN-065 W-2** | 設計 review 縦/横 record (pair-check 入力源) |
| `entries` / `links` | PLAN-027 | らせん式 entries/links 基盤 |

### §16.7 Gate 役割定義 (12 + Reverse 6)

| Gate | 担当 | 役割定義 |
|---|---|---|
| **G0.5** | PM | 企画突合ゲート (企画書 ↔ L1 反映率) |
| **G1** | PM+PO | 要件完了ゲート |
| **G1.5** | TL+PM | PoC ゲート (条件付) |
| **G1R** | TL/自動 | 事前調査ゲート (条件付) |
| **G2** | TL+PM | 設計凍結ゲート (adversarial-review + ミニレトロ + セキュリティ①) |
| **G3** | TL+PM | 実装着手ゲート (API/Schema Freeze + 事前調査) |
| **G4** | TL+PM | 実装凍結ゲート (セキュリティ② + ミニレトロ + L4 code review apex) |
| **G5** | TL+PM | デザイン凍結ゲート (UI なし skip 可、FE 必須) |
| **G6** | PM+TL+PO | RC 判定ゲート (セキュリティ③) |
| **G6.5 / G6.7 / G6.9** | TL | Pre-Release 静的/動的/直前 |
| **G7** | 自動/PM | 安定性ゲート (セキュリティ④) |
| **G9 / G10 / G11** | 自動/PM | Run 工程 (デプロイ / 観測 / 運用学習) |
| **RG0〜RG3 / RGC** | TL / PM+PO | Reverse 6 ゲート |

### §16.8 Mode / Drive 役割定義

| 軸 | 値 | 役割定義 (= どんな状況で使うか) |
|---|---|---|
| **Mode: Forward** | L0-L11 | 標準開発、要件確定済 |
| **Mode: Reverse** | R0-R4 + RGC | 既存コードの設計復元 (5 type: code/design/upgrade/normalization/fullback) |
| **Mode: Scrum** | S0-S4 | 仮説検証、要件未確定 |
| **Drive: BE** | デフォルト | API / ロジック / SaaS 業務系 |
| **Drive: FE** | mock 駆動 | LP / EC / Dashboard / UX 重視 |
| **Drive: DB** | スキーマ駆動 | マスタ管理 / ERP / データ基盤 |
| **Drive: Fullstack** | Twin Track | SaaS / EC / Dashboard + API (Phase A ∥ B) |
| **Drive: Agent** | tool 駆動 (現在は段 2 として再定義) | AI アプリ / 自動化 / ワークフロー |

### §16.9 「HELIX とは？」が機能 inventory から見える形

```
HELIX 開発 = {
    層 1 PM/PMO 機能 (§16.1)         ← 14 機能
  + 層 2 Orchestration 機能 (§16.2)  ← 18 機能
  + 層 3 Command 機能 (§16.3)        ← 18 コマンド + slash + hooks
  + 層 4 Skill 機能 (§16.4)          ← 102+ SKILL
  + 層 5 Verify 機能 (§16.5)         ← 14 detector + 5 検証ツール
  + 中央 helix.db (§16.6)            ← 18+ table
} で
{
    Gate (§16.7)                    ← 12 forward + 6 reverse
  × Mode (§16.8)                    ← Forward / Reverse / Scrum
  × Drive (§16.8)                   ← BE / FE / DB / Fullstack
} を制御し
{
    3 つの重い問題 (§2)              ← スパゲッティ / 契約漏れ / 設計デグレ
} を構造的に防止する。

→ V-model 強化 (§6) = この全体の DB 適合度を schema レベルで底上げする集大成作業
→ V2 (§12) = 上記散在を上流から coherent に再構築 + FE 弱点補強
```

→ **HELIX 開発 とは「これらの機能群で構成される `プロジェクト管理型実行ハーネス』** という機能 inventory ベースの答えが本セクションから得られる。

## §17 用語集

| 用語 | 定義 | 出典 |
|---|---|---|
| HELIX 開発 | 本システム名。プロジェクト管理型実行ハーネス | 本企画書 §0 |
| 段 1 | Product (実装本体、deliverable) | 本企画書 §5、起源 agent-design SKILL |
| 段 2 | HELIX (制御 framework) | 同上 |
| 5 層 | PM/PMO / Orchestration / Command / Skill / Verify | 本企画書 §4 |
| 3 問題 | コードスパゲッティ化 / 契約漏れ / 企画・設計デグレ | 本企画書 §2 |
| DB 適合度 | helix.db schema に蓄積される metadata の整合性 | 本企画書 §6 |
| V-model 強化 | 段 2 (HELIX) 内の設計 ↔ 検証 pairing schema 強化 | PLAN-065 §2.5 |
| 縦/横 review | 同脚内 layer 連鎖 / 同 phase 設計 ↔ test 1:1 | 同上 |
| 4 layer chain | contract → code → test_design → test_baseline | 同上 |
| V-model 整合度 | 4 layer chain が埋まる率 | 同上 |
| 集大成 | V1 累積知見を V2 で formalize する作業 | 本企画書 §11 |
| dogfood | HELIX 自身を HELIX で管理する | 本企画書 §15 |
| drive | BE / FE / DB / Fullstack (段 1 の主要 axis) | SKILL_MAP §駆動タイプ |
| mode | Forward / Reverse / Scrum | SKILL_MAP §HELIX Reverse / §HELIX Scrum |
| Agent 直交 3 軸 | cost / 非決定性 / vendor (段 2 のみ) | agent-design SKILL 11 axis + agent-cost-design SKILL |
| PMO | Project Management Office、PM 単独不足を補う層 (cost / audit / 補助) | project_helix_orchestration_v2.md (2026-05-08) |

---

**承認**: PM (Opus / Sonnet 4.6) ____________
**次ステップ**: docs/v2/MASTER.md 起票
