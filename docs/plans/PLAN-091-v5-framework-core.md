---
plan_id: PLAN-091
title: "PLAN-091: V5 framework 本体 (matrix + 種別正規化 + template embed + 単一実行正本決定)"
layer: cross
kind: impl
status: draft
size: L
drive: be
created: 2026-05-20
revised: "2026-05-20 (tl-advisor Round 3 反映: revised quote + agent_slots opus→pm-advisor)"
owner: PM
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize・P0 承認境界管理"
  - role: pmo-sonnet
    slot_label: "PMO — ドキュメントチェック・整合確認・draft 起票支援"
  - role: tl-advisor
    slot_label: "TL adversarial check — G2/G3 凍結判定・design review"
  - role: se
    slot_label: "SE — CLI 拡張実装: helix-plan / helix-doctor / helix-sprint 拡張"
  - role: docs
    slot_label: "Docs — template embed 起草、kind 別 template 12 種生成"
generates:
  - artifact_path: cli/helix-plan
    artifact_type: cli_extension
  - artifact_path: cli/templates/plan/design/template.md
    artifact_type: template
  - artifact_path: cli/templates/plan/impl/template.md
    artifact_type: template
  - artifact_path: cli/templates/plan/poc/template.md
    artifact_type: template
  - artifact_path: cli/templates/plan/reverse/template.md
    artifact_type: template
  - artifact_path: cli/templates/plan/troubleshoot/template.md
    artifact_type: template
  - artifact_path: cli/templates/plan/refactor/template.md
    artifact_type: template
  - artifact_path: cli/templates/plan/retrofit/template.md
    artifact_type: template
  - artifact_path: cli/templates/plan/research/template.md
    artifact_type: template
  - artifact_path: cli/templates/plan/add-design/template.md
    artifact_type: template
  - artifact_path: cli/templates/plan/add-impl/template.md
    artifact_type: template
  - artifact_path: cli/templates/plan/recovery/template.md
    artifact_type: template
  - artifact_path: cli/lib/plan_validator.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_plan_validator.py
    artifact_type: test
  - artifact_path: .claude/hooks/posttooluse-plan-auto-register.sh
    artifact_type: hook
  - artifact_path: docs/adr/ADR-025-v5-framework-core-decision.md
    artifact_type: adr_snapshot
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-087-design-doc-web-search-guardrail
    - PLAN-088-todowrite-agent-slot-framework
    - PLAN-089-gate-fail-close-design-doc-web-search-audit
    - PLAN-090-posttooluse-continueonblock-refactor
    - PLAN-MM-001
  blocks:
    - PLAN-092-posttooluse-plan-auto-register
    - PLAN-093-plan-drift-detection-curator
    - PLAN-100-existing-retrofit-v2-revision
    - PLAN-095-poc-scrum-reverse-matrix
    - PLAN-096-github-actions-branch-pipeline
    - PLAN-097-abstraction-layer-escalation
    - PLAN-098-recovery-plan-kind-normalization
    - PLAN-099-autonomous-runtime-framework-5layer
related_adr:
  - ADR-025-v5-framework-core-decision
related_docs:
  - docs/plans/PLAN-MM-001-v5-framework-master-plan.md
  - CLAUDE.md §V5 framework 18 要素
  - CLAUDE.md §V5 framework 3 層構造
  - CLAUDE.md §TL v5 round 5 修正条件
  - docs/v2/V5-plan-outlines.md (17 要素時点の旧素材)
  - skills/SKILL_MAP.md
  - helix/HELIX_CORE.md
  - cli/ROLE_MAP.md (agent_slots.role enum の正本)
---

# PLAN-091: V5 framework 本体 (matrix + 種別正規化 + template embed + 単一実行正本決定)

> **kind**: impl (Layer A 工程ルール整備の中核、他子 PLAN の frontmatter 語彙正本)
> **layer**: cross (L0-L11 全層に影響)
> **drive**: be (CLI / framework 実装中心、UI なし)
> **契約 seed**: 本 PLAN は PLAN-092〜099 が参照する frontmatter 語彙・依存構造・単一実行正本の正本定義。
> **本 PLAN 完遂の前提**: PLAN-MM-001 親設計 + PLAN-087/088/089/090 の既存実装 (前段)。
> **本 PLAN 完遂後に着手可能**: PLAN-092〜099 (全子 PLAN、本 PLAN の語彙を参照)。

---

## §0. 本 PLAN の位置付け (契約 seed)

本 PLAN は **V5 framework の契約 seed**。PLAN-092〜099 を起票・実装する際に参照する frontmatter 語彙 (kind / layer / workflow_phase / drive / dependencies / agent_slots / generates) を正本として定義し、V5 18 要素のうち Layer A (工程・ドキュメント運用ルール整備) に帰属する要素 (#1〜#7, #11〜#13) の実装設計を確定する。

PLAN-MM-001 §6 の依存グラフで「PLAN-091 を契約 seed として最優先確定」と宣言されたとおり、本 PLAN が未確定のまま他子 PLAN を並列起票すると frontmatter 語彙の drift が発生する。

### 本 PLAN が担当する V5 18 要素

| V5 # | 要素 | 本 PLAN 担当範囲 |
|---|---|---|
| #1 | PLAN = self-contained workflow ルール doc | §4 定義確定 |
| #2 | V-model layer × drive matrix | §5 matrix 正本 |
| #3 | 種別正規化 11 kind | §5 kind 定義 |
| #4 | matrix 外 / kind 不在を fail-close | §9 段階導入 P3 |
| #5 | generates trace | §5 generates 定義 |
| #6 | dependencies graph | §5 dependencies 定義 |
| #7 | agent_slots 割当 | §5 agent_slots 定義 |
| #11 | ADR snapshot 必須化 | §7 ルール定義 |
| #12 | kind 別 workflow template embed | §8 template 設計 |
| #13 | V-model TDD 駆動 | §10 設計 |

要素 #8〜#10 (PostToolUse / drift / 進捗) は PLAN-092/093 (Layer B)、要素 #14〜#18 は PLAN-095〜099 (Layer A 残 + Layer C) が担当。

---

## §1. 目的

1. PLAN frontmatter の語彙 (kind / layer / workflow_phase / drive / dependencies / agent_slots / generates) を V5 framework 正本として定義し、全子 PLAN の基盤とする
2. V-model layer (L0-L11、L3.5/L4.5 含む) × drive (9 種) の matrix を確立し、PLAN が matrix 内に収まるかを機械検証可能にする
3. Reverse (R0-R4) / Scrum (S0-S4) は `workflow_phase` 別フィールドで表現し、layer は L 系 15 種 + cross に限定する (§5.2 / §5.X 参照)
4. 種別 (kind) を 11 種に正規化し、各 kind に応じた workflow template を embed する
5. 単一実行正本を決定し、PLAN / helix job / handover / TodoWrite の競合を解消する (TL v5 P1)
6. 承認なし task pop を禁止する P0 guard を設計に組み込む (TL v5 P0)
7. 段階導入 5 Phase (P1 warning → P5 Curator) を本 PLAN 内で P1〜P3 を担当し、P4〜P5 は後段 PLAN に委譲する
8. V-model TDD 駆動 (設計⇔テスト設計 pair freeze) を kind 別 template に組み込む

---

## §2. 背景と採用根拠

### 2.1 現状の問題

HELIX 運用において PLAN doc の frontmatter が存在せず、以下の問題が発生していた:

| 問題 | 具体的影響 |
|---|---|
| kind 不在 | どの種別の作業か機械判定不能、工程テンプレート適用不可 |
| layer 不在 | どのフェーズの成果物か追跡不能、V-model 対応付け不可 |
| drive 不在 | be/fe/fullstack 等の駆動タイプが PLAN から読み取れない |
| workflow_phase 不在 | R0-R4 / S0-S4 を layer に混在させ validator 矛盾が発生 |
| generates 不在 | 成果物から PLAN への逆引き不可、drift 検出不能 (PLAN-093 前提) |
| dependencies 不在 | PLAN 間の依存関係が文書化されず、並列投入時の衝突リスク管理不可 |
| agent_slots 不在 | どのモデルが担当するか不明、並列実行の可観測性ゼロ |

### 2.2 V1→V5 確立過程 (PLAN-MM-001 §2.1 参照)

TL 5 ラウンドの adversarial check と 12+ turn のユーザー訂正を経て V5 が確定。本 PLAN は v5 passed_with_minor_changes (bdnmyhznq) の修正条件 (Critical 3 + Important 6 + Minor 3) を全件反映した改訂版。

### 2.3 Layer A 先行の必然性

PLAN-MM-001 §5 の 3 層構造 (Layer A → B → C) が定義するとおり、Layer B (helix.db schema v35、PLAN-092) と Layer C (自動走行 hook、PLAN-099) は Layer A の語彙・規約が確定してから着手する。本 PLAN は Layer A の最重要 doc として他全子 PLAN に先行する。

---

## §3. 業界 standard 参照 (Web 検索 3 query ベース、PLAN-087 ガードレール準拠)

PLAN-MM-001 §3 の Sources を継承し、本 PLAN 固有の参照を追加する。

| 参照 | Source URL | 本 PLAN での引用箇所 |
|---|---|---|
| GitHub Spec-Kit (Constitution → Specify → Clarify → Plan → Tasks → Implement) | https://github.com/github/spec-kit | §4 PLAN = self-contained doc の業界整合 (spec → plan → tasks の 3 層分離) |
| AWS Kiro IDE Spec-Driven Development | https://thebcms.com/blog/spec-driven-development | §8 kind 別 template embed の業界整合 (kind 単位の workflow step 埋め込み) |
| ADR best practices — AWS Architecture Blog | https://aws.amazon.com/blogs/architecture/master-architecture-decision-records-adrs-best-practices-for-effective-decision-making/ | §7 ADR snapshot 必須化の業界根拠 (append-only log、PLAN tree 内 L2 凍結) |
| Microsoft Azure Well-Architected ADR | https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record | §7 ADR の Supersedes/Related フィールド設計の根拠 |
| Flagsmith: Feature flags staged rollout | https://www.flagsmith.com/blog/how-to-enhance-phased-rollouts-with-feature-flags | §9 段階導入 5 Phase (P1 warn-only → P3 fail-close) の業界整合 |
| OpenFeature / Cloudflare Flagship progressive delivery | https://www.infoq.com/news/2026/05/cloudflare-flagship-openfeature/ | §9 P2 matrix 検証 + P3 fail-close の段階遷移設計の根拠 |
| CrewAI Core Concepts — Agent roles & specialization | https://docs.crewai.com/core-concepts/Agents/ | §5 agent_slots 定義の業界整合 (role-specialized agent slot 設計) |
| EARS Requirements Syntax (testable, AI-parseable) | https://towardsdatascience.com/from-vibe-coding-to-spec-driven-development/ | §12 DoD 受入条件の記述方式参考 |

---

## §4. PLAN = self-contained workflow ルール doc (V5 要素 #1 正本定義)

### 4.1 定義

V5 における PLAN とは、**1 トピックの implementation tree (L0〜L11 全範囲を内包可能な self-contained doc)** であり、以下の条件を満たす:

1. **自己完結**: PLAN を単独で読んだだけで、目的・背景・受入条件・実装計画・担当 agent・生成物が把握できる
2. **永続化**: TodoWrite (ephemeral) の代替として、session 跨ぎで継続する工程記録として機能する
3. **implementation tree**: L1 確定 (要件) → L2 凍結 (ADR snapshot、任意) → L3 詳細 → L4 Sprint の全層を 1 PLAN doc に包含できる
4. **機械可読 frontmatter**: kind / layer / workflow_phase / drive / generates / dependencies / agent_slots を frontmatter に持ち、CLI (helix plan lint --v5) と DB (plan_registry、PLAN-092) が自動解析できる

### 4.2 PLAN と他 artifact の関係

```
PLAN doc (本 PLAN が定義する形式)
  ├── §目的/背景         ← L1 要件定義に対応 (L1 PLAN)
  ├── §業界 standard 参照 ← PLAN-087 ガードレール準拠 (必須)
  ├── ADR-NNN (L2 snapshot) ← PLAN tree 内の L2 大局判断あれば別 file で並設
  ├── §実装設計           ← L3 詳細設計に対応 (L3 PLAN)
  └── §Phase/Sprint 計画  ← L4 実装計画に対応 (L4 PLAN)
```

### 4.3 PLAN 種別と TodoWrite の役割分担

| ツール | 用途 | 永続性 | 機械可読 |
|---|---|---|---|
| PLAN doc | トピック単位の工程計画・設計・受入条件 | 永続 (git) | ✅ (frontmatter) |
| TodoWrite | session 内 ephemeral checklist | 非永続 (session 限り) | 部分的 |
| helix job | runnable execution queue | 永続 (helix.db) | ✅ |
| handover | session continuity | 永続 (.helix/handover/) | ✅ |

---

## §5. frontmatter 語彙の正本定義 (V5 要素 #2〜#7)

本セクションは PLAN-092〜099 が参照する語彙の **唯一の正本**。変更は本 PLAN 改訂 + ADR-025 更新を経ること。

### 5.1 kind — 11 種 (V5 要素 #3)

| kind | 定義 | 典型的な layer | 典型的な drive |
|---|---|---|---|
| `design` | 全体設計・アーキテクチャ設計 doc の起票 | L1, L2 | be, fullstack, agent |
| `impl` | 機能実装 (CLI / hook / lib / schema 等) | L3, L4 | be, db, fe |
| `poc` | 仮説検証 (PoC、Scrum 連携) | L3, cross | scrum, poc |
| `reverse` | 既存コード / 設計からの逆引き | cross | reverse |
| `troubleshoot` | バグ解析・障害対応 | L4, L6, L9 | be, fullstack |
| `refactor` | 機能変更なしの内部改善 | L4 | be, db |
| `retrofit` | 既存 doc / code を新規約に合わせる更新 | cross | be |
| `research` | 技術調査・ADR 判断材料収集 | L1, L2, cross | be, agent |
| `add-design` | 既存設計への追補 (既存 PLAN の設計拡張) | L2, L3 | be, fullstack |
| `add-impl` | 既存実装への追加機能実装 | L4 | be, fe |
| `recovery` | session 断絶・議論脱線・認識ずれからの再開 | cross | troubleshoot |

**禁止**: kind を上記 11 種以外で記述すること。不明な場合は `research` または `troubleshoot` を選ぶ。

**注意**: `poc` / `reverse` kind を使う場合、Scrum (S0-S4) / Reverse (R0-R4) の詳細フェーズは `workflow_phase` フィールドに記述する (§5.X 参照)。layer は `cross` を使い、S0-S4 / R0-R4 を layer に直接書かない。

### 5.2 layer — 15 種 (V5 要素 #2 の layer 軸)

layer フィールドは **L 系 14 種 + cross の計 15 種のみ** を許可する。Reverse (R0-R4) / Scrum (S0-S4) は §5.X の `workflow_phase` フィールドを使うこと。

| layer 値 | 対応する HELIX フェーズ | 補足 |
|---|---|---|
| `L0` | 事前準備 (dev-setup / 調査前作業) | SKILL_MAP に明示的 L0 なし、pre-work 専用 |
| `L1` | 要件定義 | 受入テスト設計を含む |
| `L2` | 全体設計 (アーキテクチャ / ADR) | 総合テスト設計を含む |
| `L3` | 詳細設計 (D-API / D-DB / D-CONTRACT) | 結合テスト設計を含む |
| `L3.5` | 機能設計 (endpoint / 関数 schema レベル) | 単体テスト設計の pair 相手 |
| `L4` | 実装 (Sprint .1〜.5) | 単体/結合テスト実装 |
| `L4.5` | 結合テスト集中フェーズ | L4 Sprint 完了後、L5 前 |
| `L5` | Visual Refinement (FE 駆動のみ必須) | |
| `L6` | 統合検証 (E2E / 性能 / セキュリティ) | |
| `L7` | デプロイ (staging → 本番) | |
| `L8` | 受入 (PO 最終承認) | |
| `L9` | デプロイ検証 (smoke test / 監視初期確認) | |
| `L10` | 観測 (SLO/SLI / アラート) | |
| `L11` | 運用学習 (postmortem / 改善施策) | |
| `cross` | 複数 layer にまたがる (framework / 運用ルール等) | |

**validator 強制**: `layer` は上記 15 種のみ有効。`R0` / `R1` / `S0` 等を layer に書くと lint エラー (P3 以降 fail-close)。

### 5.3 drive — 9 種 (V5 要素 #2 の drive 軸)

SKILL_MAP の駆動タイプ分類に準拠する。

| drive 値 | 起点 | 分類 | 対応 SKILL_MAP |
|---|---|---|---|
| `be` | API / ロジック (デフォルト) | 主要 4 | §主要 4 パターン |
| `fe` | デザイン / UX / モック駆動 | 主要 4 | §主要 4 パターン |
| `fullstack` | BE + FE 同時 (Twin Track) | 主要 4 | §主要 4 パターン |
| `scrum` | 仮説検証 (要件不確実) | 主要 4 | §主要 4 パターン |
| `db` | スキーマ / データモデル起点 | エッジケース 2 | §エッジケース |
| `agent` | ツール / プロンプト / AI workflow | エッジケース 2 | §エッジケース |
| `reverse` | 既存コード → 設計復元 | その他 3 | §Phase R |
| `poc` | PoC 特化 (仮説検証前段) | その他 3 | V5 要素 #14 |
| `troubleshoot` | 障害対応 / バグ解析起点 | その他 3 | V5 要素 #17 |

**SKILL_MAP との整合**: be / fe / fullstack / scrum は SKILL_MAP §主要 4 パターン、db / agent は§エッジケース 2、reverse / poc / troubleshoot は V5 追加の その他 3。

### 5.4 dependencies — 構造定義 (V5 要素 #6)

```yaml
dependencies:
  parent: PLAN-NNN           # 親 PLAN (ひとつ、なければ null)
  requires:                  # 前段として完遂必要な PLAN ID list
    - PLAN-NNN-slug
  blocks:                    # 本 PLAN 完遂後に着手可能になる PLAN ID list
    - PLAN-NNN-slug
```

**validator rule — 3 件必須**:

1. **cycle detection**: `requires` と `blocks` の間で循環参照が発生してはならない。PLAN-093 §helix doctor が `check_plan_cycle` で自動検出する (Phase 2 以降)。
2. **reciprocal consistency**: PLAN-A.blocks に PLAN-B があれば、PLAN-B.requires に PLAN-A が含まれること。片方向記述はリント警告 (Phase 2 以降 warn、Phase 3 以降 fail-close)。
3. **self-edge 禁止**: `requires` に自 PLAN ID (PLAN-091.requires に PLAN-091 など) を含めてはならない。validator が即 exit 2 で reject する。

**blocks フィールドの位置付け**: `requires` から自動算出可能な派生値とも言えるが、Phase 2 以降は reciprocal lint で二重記述の一致を強制するため、明示記述を推奨する。

**命名規約**: PLAN ID は `PLAN-NNN-slug` 形式 (NNN は 3 桁ゼロ埋め、slug はケバブケース)。

### 5.5 agent_slots — 割当定義 (V5 要素 #7)

PLAN が想定する担当 agent を列挙する。PLAN-088 (TodoWrite × agent slot) と連動し、実行時に slot 化される。

**構造**:

```yaml
agent_slots:
  - role: <ROLE_MAP の 30 種から選択>    # 必須、validator が enum 強制
    slot_label: "表示名 (任意説明)"       # 任意、表示用メモ
```

**role は cli/ROLE_MAP.md の 30 種のみ有効** (モデル名は frontmatter に書かない、cli/config/models.yaml 参照):

| role 値 | ROLE_MAP 担当 | 主な担当 |
|---|---|---|
| `tl` | gpt-5.5 高 | 設計・技術判断・レビュー・ゲート判定 |
| `se` | gpt-5.4 高 | 高度実装・リファクタリング・契約 |
| `pg` | gpt-5.3-codex-spark (PE) | 単機能速度重視実装 |
| `fe` | gpt-5.4 高 | UI実装・スタイリング |
| `qa` | gpt-5.4 高 | テスト設計・テスト実装・品質ゲート |
| `security` | gpt-5.4 | セキュリティ監査・脆弱性診断 |
| `dba` | gpt-5.3-codex | DB スキーマ設計・マイグレーション |
| `devops` | gpt-5.3-codex | デプロイ・インフラ・CI/CD |
| `docs` | gpt-5.3-codex-spark | ドキュメント本文起草 |
| `research` | gpt-5.4 | 技術調査・先行事例 |
| `legacy` | gpt-5.4 | レガシー分析・Reverse HELIX |
| `perf` | gpt-5.4 | パフォーマンス計測・最適化 |
| `classifier` | gpt-5.4-mini | タスク分類・ロール判定 |
| `recommender` | gpt-5.4-mini | スキル自動推挙 |
| `effort-classifier` | gpt-5.4-mini | 工数・難易度・規模の分類補助 |
| `pmo-sonnet` | claude-sonnet-4-6 | PMO — 状況把握・ドキュメントチェック |
| `pmo-haiku` | claude-haiku-4-5 | PMO 軽作業 — Web 検索・docs 系 |
| `pdm-tech-innovation` | claude-opus-4-7 | 海外技術思想翻案 |
| `pdm-marketing-innovation` | claude-opus-4-7 | 海外マーケ思想翻案 |
| `pdm-innovation-manager` | claude-opus-4-7 | PdM 統合判断 |
| `impl-sonnet` | claude-sonnet-4-6 | write-enabled 実装 (Codex 上限時代替) |
| `pm-advisor` | claude-opus-4-7 (read-only) | PM 級難判断アドバイザー |
| `tl-advisor` | gpt-5.5 (read-only) | TL 級設計アドバイザー |
| `pmo-helix-explorer` | claude-sonnet-4-6 | HELIX 内資産詳細探索 |
| `pmo-helix-scout` | claude-haiku-4-5 | HELIX 内軽量検索 |
| `pmo-project-explorer` | claude-sonnet-4-6 | project 内資産詳細探索 |
| `pmo-project-scout` | claude-haiku-4-5 | project 内軽量検索 |
| `pmo-tech-docs` | claude-sonnet-4-6 | 設計手法・概念の外部精読 |
| `pmo-tech-fork` | claude-sonnet-4-6 | OSS/plugin 探索・転用判断 |
| `pmo-tech-news` | claude-sonnet-4-6 | 最新 Tech 動向 sweep |

**禁止**:
- role フィールドにモデル名 (gpt-5.5 等) を直接記述すること
- ROLE_MAP に存在しない独自 slot 名 (codex-tl / codex-se 等) を使うこと

### 5.6 generates — 生成物 trace 定義 (V5 要素 #5)

```yaml
generates:
  - artifact_path: path/to/file.py       # git root からの相対パス
    artifact_type: python_module          # 種別 (下記参照)
```

**artifact_type 種別 — 16 種 (11 既存 + 5 追加)**:

| artifact_type 値 | 説明 |
|---|---|
| `cli_extension` | helix-* CLI スクリプト拡張 |
| `python_module` | cli/lib/ の Python helper |
| `bash_script` | cli/ の bash スクリプト |
| `template` | cli/templates/ の markdown template |
| `migration` | cli/lib/migrations/v*.py DB migration |
| `test` | cli/lib/tests/test_*.py テストコード |
| `adr_snapshot` | docs/adr/ADR-NNN-*.md |
| `design_doc` | docs/plans/ or docs/v2/ の設計 doc |
| `github_workflow` | .github/workflows/*.yml |
| `github_config` | .github/CODEOWNERS, pull_request_template.md 等 |
| `skill` | skills/**/*.md |
| `hook` | .claude/hooks/*.sh (Claude Code hook スクリプト) |
| `test_design` | docs/v2/L4-test-design/*.md (テスト設計 doc) |
| `command_doc` | docs/commands/*.md (CLI 利用導線 doc) |
| `runbook` | docs/runbook/*.md (運用手順書) |
| `workflow_config` | .github/workflows/*.yml または workflows/*.yaml |

**注意**: `github_workflow` と `workflow_config` は重複する場合があるが、GitHub Actions 専用は `github_workflow`、その他ワークフロー設定は `workflow_config` で区別する。

### 5.X workflow_phase — Reverse / Scrum 詳細フェーズ (V5 追加フィールド)

`poc` / `reverse` kind で Scrum (S0-S4) または Reverse (R0-R4) の詳細フェーズを記述する場合に使用する任意フィールド。`layer: cross` と組み合わせる。

```yaml
workflow_phase: S0   # S0|S1|S2|S3|S4|R0|R1|R2|R3|R4 のいずれか
```

| 許可値 | 対応フェーズ |
|---|---|
| `S0` | Scrum — Backlog 構築 |
| `S1` | Scrum — Sprint Plan |
| `S2` | Scrum — PoC 実装 |
| `S3` | Scrum — Verify |
| `S4` | Scrum — Decide |
| `R0` | Reverse — Evidence Acquisition |
| `R1` | Reverse — Observed Contracts |
| `R2` | Reverse — As-Is Design |
| `R3` | Reverse — Intent Hypotheses |
| `R4` | Reverse — Gap & Routing |

**使用例**:

```yaml
kind: poc
layer: cross
drive: scrum
workflow_phase: S2   # Scrum PoC 実装フェーズ
```

```yaml
kind: reverse
layer: cross
drive: reverse
workflow_phase: R2   # As-Is Design フェーズ
```

**禁止**: `layer` フィールドに S0-S4 / R0-R4 を直接書くこと。validator が exit 2 で reject する (Phase 3 以降)。

---

## §6. 単一実行正本決定 (TL v5 P1、CRITICAL)

TL v5 round 5 の P1 指摘「task_queue / TodoWrite / helix job / handover が競合する恐れ → 単一の実行正本を決める」に対する設計上の回答を本 PLAN で凍結する。

### 6.1 四者の役割分担 (確定)

| 候補 | 役割 | 正本決定 | 変更禁止 |
|---|---|---|---|
| **PLAN (plan_registry)** | PLAN 定義の単一 source of truth (種別・依存・生成物 trace・受入条件・設計) | `plan_registry` テーブル (PLAN-092 新規) | ✅ |
| **helix job / scheduler** | runnable execution queue (実行待ち task の atomic claim) | **既存 helix job + scheduler を継続使用、task_queue 新設しない** | ✅ |
| **handover (.helix/handover/)** | session continuity (session 跨ぎの状態継承・Next Action) | **既存 handover 継続使用** | ✅ |
| **TodoWrite** | ephemeral checklist (session 内 task tracking、非永続) | **既存 TodoWrite 継続使用、PLAN への昇格条件を別定義** | ✅ |

### 6.2 task_queue 新設禁止の根拠

PLAN-088 §1.1 が定義する「PLAN から runnable work item queue 化」のニーズは、**既存 helix job/scheduler を介して満たす**。task_queue を新設すると:
- helix job / handover / task_queue の三者が競合し「どこが正本か」問題が再発する
- PLAN-088 = 「誰が担当 (agent slot)、WIP 可視化」、helix job = 「実行 queue の atomic claim」として責務が重複する
- PLAN-099 §Layer 1 の「PLAN.md Write → task_queue auto-enqueue」設計も、`helix job enqueue` への enqueue に読み替える

**変更手続き**: この決定を変更する場合は ADR-025 の改訂 + tl-advisor adversarial check が必須。

### 6.3 TodoWrite から PLAN への昇格条件

TodoWrite item が以下のいずれかを満たす場合、PLAN doc として永続化する:

1. session を跨いで継続する予定 (次 session carry)
2. 他 PLAN の dependency になる
3. 実装コードを生成する (generates に artifact が入る)
4. kind が `recovery` (session 断絶リカバリー) に該当する

---

## §7. ADR snapshot 必須化ルール (V5 要素 #11)

### 7.1 ADR snapshot が必要な条件

PLAN tree 内 (PLAN の §背景 / §設計 / §採用根拠) に以下のいずれかが含まれる場合、対応する ADR snapshot を同時起票する:

| 条件 | ADR snapshot 起票要否 |
|---|---|
| 新 framework / パターン採用判断 | ✅ 必須 |
| fail-close 化 / advisory → fail-close 段階遷移 | ✅ 必須 |
| 外部新仕様の採用 (SDK / API / ツール) | ✅ 必須 |
| 既存方針の転換 (e.g. PRAGMA → schema_version) | ✅ 必須 |
| 既存 framework の大規模変更 | ✅ 必須 |
| bug fix / refactor (機能変更なし) | ❌ 不要 |
| 既存 ADR で凍結済み方針の実装 | ❌ 不要 |
| 既存 framework 内 Phase 拡張 (新方針なし) | ❌ 不要 |

### 7.2 PLAN ⊃ ADR レイヤー併存のルール

ADR は PLAN の「前置き」でも「後付け」でもなく、PLAN tree の L2 大局判断 snapshot として **同時起票・双方向 reference** で管理する:

```
PLAN-NNN.md (implementation tree)
  ├── §背景       ← L1 要件
  ├── §設計       ← L3 詳細
  └── §ADR ref    ← "本 PLAN の L2 凍結: ADR-NNN-*.md §Decision を参照"

ADR-NNN.md (L2 snapshot)
  ├── ## Related  ← "Related: PLAN-NNN (実装 tree)"
  └── ## Context  ← PLAN tree の何を凍結したか
```

### 7.3 違反検出

PLAN tree 内に L2 大局判断が含まれるのに ADR snapshot が不在の場合、PLAN-093 §helix doctor が `check_plan_adr_snapshot` で検出する。Phase 3 以降は fail-close 化予定。

---

## §8. kind 別 workflow template embed (V5 要素 #12)

本 PLAN の generates に列挙した 11 種の template (cli/templates/plan/{kind}/template.md) が定義する標準 Step。

**重要**: 各 template から `commit` step を削除する。委譲 Codex は `git add / commit / push` を行わない (CLAUDE.md §委譲 Codex のコミット禁止)。各 template の最終 step は「変更ファイル列挙 + テスト実行 + review evidence 報告」とし、commit は **PM / TL 統合工程** (template 外の別工程) として扱う。

### 8.1 design template (L1-L2 向け)

```
Step 1: 既存関連 doc Read (PLAN-MM-001 / CONCEPT / ADR 等)
Step 2: 業界 standard 参照 (WebSearch 3 query 以上)
Step 3: 設計案起草 (pmo-sonnet または docs role 委譲)
Step 4: tl-advisor adversarial check (changes_required → 反映 → passed)
Step 5: ADR snapshot 起票 (L2 大局判断あれば)
Step 6: 双方向 reference 確立 (PLAN ↔ ADR、PLAN ↔ generates)
Step 7: 変更ファイル列挙 + DoD 確認 + review evidence 報告
```

### 8.2 impl template (L3-L4 向け)

```
Step 1: Entry 条件確認 (前段 PLAN 完遂 + dependency 確認)
Step 2: helix code find / pmo-project-scout で既存資産確認
Step 3: 機能設計 (L3.5 → 単体テスト設計 pair freeze)
Step 4: 実装 (Codex 委譲、helix job enqueue 経由)
Step 5: 機械チェック (py_compile / bash -n / shellcheck / markdownlint)
Step 6: テスト起動 (単体 → 結合 → 全回帰)
Step 7: pmo-sonnet review + tl-advisor (G4 時)
Step 8: 変更ファイル列挙 + DoD 確認 + review evidence 報告
```

### 8.3 poc template (Scrum S0-S4 向け)

```
Step 1: Scrum backlog 構築 (仮説 / 検証質問 / 成功条件)
Step 2: workflow_phase: S0 を frontmatter に設定
Step 3: Reverse type 決定 (Scrum × Reverse matrix、PLAN-095 参照)
Step 4: PoC 実装 (Codex 委譲、verify/ スクリプト化)
Step 5: 全検証スクリプト実行 (helix scrum verify)
Step 6: decide (confirmed / rejected / pivot)
Step 7: confirmed の場合 → Reverse R0 routing (PLAN-095 参照)
Step 8: 変更ファイル列挙 + DoD 確認 + review evidence 報告
```

### 8.4 reverse template (R0-R4 向け)

```
Step R0: Evidence Acquisition (コード + DB + 設定 + 運用実態の証拠収集)
         workflow_phase: R0 を frontmatter に設定
Step R1: Observed Contracts (API/DB/型の機械抽出 + characterization tests)
Step R2: As-Is Design (アーキテクチャ復元 + ADR 推定)
Step R3: Intent Hypotheses (要件仮説 + PO 検証)
Step R4: Gap & Routing (差分集約 → Forward HELIX に接続)
Step Final: 変更ファイル列挙 + DoD 確認 + review evidence 報告
```

### 8.5 troubleshoot template (障害対応向け)

```
Step 1: 事象記録 (発生時刻 / 症状 / 影響範囲)
Step 2: 仮説列挙 (原因候補 3 件以上)
Step 3: 証拠収集 (ログ / DB state / git log)
Step 4: 根本原因特定 (tl-advisor 相談可)
Step 5: 修正実施 (Codex 委譲 または Opus 直接)
Step 6: 回帰確認 (全テスト)
Step 7: 再発防止 (helix doctor / hook 強化)
Step 8: recovery kind PLAN で記録 (session 断絶 / 認識ずれも含む)
Step 9: 変更ファイル列挙 + DoD 確認 + review evidence 報告
```

### 8.6 refactor template (機能変更なし改善向け)

```
Step 1: refactor 対象の特定 (degrade test が存在することを確認)
Step 2: helix code find で既存資産確認
Step 3: 変更前テスト全通過確認
Step 4: refactor 実施 (Codex 委譲)
Step 5: 変更後テスト全通過確認 (degrade なし)
Step 6: pmo-sonnet review
Step 7: 変更ファイル列挙 + DoD 確認 + review evidence 報告
```

### 8.7 retrofit template (既存規約への合わせ込み向け)

```
Step 1: retrofit 対象一覧の抽出 (pmo-sonnet / helix doctor)
Step 2: retrofit ルールの確認 (対象 ADR / PLAN の正本)
Step 3: 並列 retrofit 実施 (docs role × N 並列)
Step 4: 整合確認 (pmo-sonnet review)
Step 5: helix doctor check 全通過
Step 6: 変更ファイル列挙 + DoD 確認 + review evidence 報告
```

### 8.8 research template (技術調査向け)

```
Step 1: 調査質問の定義 (何を明らかにしたいか)
Step 2: 業界 standard 参照 (WebSearch 3 query 以上、PLAN-087 準拠)
Step 3: pmo-tech-docs / pmo-tech-fork で外部資産精読
Step 4: 調査結果の構造化 (課題 / 選択肢 / 推奨案)
Step 5: tl-advisor adversarial check (必要な場合)
Step 6: ADR snapshot 起票 (大局判断あれば)
Step 7: PLAN / CLAUDE.md / memory feedback に永続化
Step 8: 変更ファイル列挙 + DoD 確認 + review evidence 報告
```

### 8.9 add-design template (既存設計への追補向け)

```
Step 1: 追補対象の既存設計 doc Read
Step 2: 追補内容の定義 (どの section に何を追加するか)
Step 3: 業界 standard 参照 (WebSearch 1 query 以上)
Step 4: draft 起草 (pmo-sonnet または docs role)
Step 5: tl-advisor adversarial check (L2 大局判断あれば)
Step 6: ADR snapshot 起票 (大局判断あれば)
Step 7: 既存設計 doc との双方向 reference 確立
Step 8: 変更ファイル列挙 + DoD 確認 + review evidence 報告
```

### 8.10 add-impl template (既存実装への追加機能向け)

```
Step 1: 既存実装の Read (対象ファイル / 依存)
Step 2: 追加機能の設計 (L3.5 機能設計 → 単体テスト設計 pair freeze)
Step 3: 実装 (Codex 委譲)
Step 4: 機械チェック + テスト
Step 5: 既存テスト回帰確認 (degrade なし)
Step 6: 変更ファイル列挙 + DoD 確認 + review evidence 報告
```

### 8.11 recovery template (session 断絶リカバリー向け、PLAN-098 詳細)

```
Step 1: 事故記録 (何が起きたか: session 断絶 / 議論脱線 / 認識ずれ)
Step 2: 議論順序 timeline (いつ何を議論したか)
Step 3: 認識訂正履歴 (V1→...→Vn の遷移と各訂正理由)
Step 4: 中間結論 list (確定済み / 未確定 / 破棄済みを 3 列で管理)
Step 5: context 再構築チェックリスト (次 session 開始前に確認すべき 5 項目)
Step 6: 再開ポイント (どこから再開するか、前提条件)
Step 7: 再発防止策 (session 終了前チェックリスト 4 項目 fail-close)
Step 8: 変更ファイル列挙 + DoD 確認 + review evidence 報告
```

---

## §9. 段階導入 5 Phase (V5 要素 #4、本 PLAN が P1〜P3 を担当)

| Phase | 内容 | 本 PLAN 担当 | 単一実行正本 (§6 参照) |
|---|---|---|---|
| **P1** | warning 導入: matrix 外 PLAN でも続行、警告のみ表示 | ✅ 本 PLAN §CLI | TodoWrite (既存) |
| **P2** | matrix 検証: helix plan lint --v5 + drift 検出 (PLAN-093) | ✅ 本 PLAN §CLI (skeleton) + PLAN-092/093 (実装) | TodoWrite + plan_registry (新) |
| **P3** | fail-close 強制: helix plan draft で matrix 外 reject | ✅ 本 PLAN §CLI (design)、実装は PLAN-091 実装 session | TodoWrite + plan_registry |
| P4 | retrofit: PLAN-001〜090 frontmatter 一括拡張 | PLAN-100 | (継続) |
| P5 | Curator 自動化 + GitHub + 抽象化層 + PoC matrix 統合 | PLAN-093/095/096/097 | (継続) |

### 9.1 P1 警告の設計

`helix plan lint --v5 --plan-id PLAN-NNN` が以下を検出した場合に stderr に警告 (exit 0、続行可):
- `kind` が 11 種に含まれない
- `layer` が 15 種に含まれない、または R0-R4 / S0-S4 が layer に書かれている
- `drive` が 9 種に含まれない
- `agent_slots[].role` が ROLE_MAP 30 種に含まれない
- `dependencies.parent` が存在しない (PLAN-MM-001 以外の root PLAN は例外)
- `generates` が空

### 9.2 P3 fail-close の設計 (Phase 3 以降)

`helix plan draft --kind <kind> --layer <layer> --drive <drive>` が matrix 外の組み合わせを渡された場合 exit 2 で reject。P3 以前は warning のみ (exit 0)。

**matrix 外の典型例** (後段 PLAN の設計時に追補):
- `kind: impl, layer: L1` (L1 は design / research が正当)
- `kind: design, layer: L4` (L4 は impl が正当)
- `kind: poc, drive: be` (poc は scrum / poc drive が正当)
- `layer: R0` (R0-R4 は workflow_phase で表現、layer には書かない)
- `layer: S0` (S0-S4 は workflow_phase で表現、layer には書かない)

---

## §10. V-model TDD 駆動 (V5 要素 #13)

### 10.1 設計⇔テスト設計 pair freeze

PLAN-075 (V-model 4 artifact 双方向 trace) の原則を種別 template に組み込む:

| PLAN layer | 設計 artifact (①) | 対応するテスト設計 artifact (③) |
|---|---|---|
| L1 要件定義 | PLAN §要件 / §受入条件 | 受入テスト設計 doc (別 file) |
| L2 全体設計 | PLAN §設計 / ADR snapshot | 総合テスト設計 doc (別 file) |
| L3 詳細設計 | D-API / D-DB / D-CONTRACT | 結合テスト設計 doc (別 file) |
| L3.5 機能設計 | endpoint / 関数 schema | 単体テスト設計 doc (別 file) |

**pair freeze ルール**: L3.5 機能設計が完了した時点で、対応する単体テスト設計 doc が存在しなければ L4 実装に進まない (G3 ゲートで確認)。

### 10.2 QA 追加テストの位置付け (V-model 補足)

L4 実装完了後に qa role が追加する regression / exploratory / edge-case テストは、既存の設計 (L3 結合テスト設計 / L3.5 単体テスト設計) を **置換しない追加レイヤー** として扱う:

| テスト種別 | 担当 | 設計 doc | タイミング |
|---|---|---|---|
| 単体テスト | impl / qa | L3.5 テスト設計 | L4 Sprint 内 |
| 結合テスト | impl / qa | L3 テスト設計 | L4.5 |
| QA 追加テスト (regression / exploratory / edge-case) | qa | 別途 L6 テスト設計 doc | L6 統合検証 |
| 総合テスト (E2E) | qa / devops | L2 テスト設計 | L6 |

**禁止**: QA 追加テストを L3.5 単体テスト設計や L3 結合テスト設計の内容と統合すること (V-model 4 artifact 違反)。

### 10.3 impl template への組み込み

§8.2 の impl template Step 3 が L3.5 機能設計 + 単体テスト設計 pair freeze を含む。

```yaml
# impl kind PLAN の frontmatter 追加フィールド (任意)
test_design_docs:
  - docs/v2/L4-test-design/PLAN-NNN-unit-test-design.md
  - docs/v2/L4-test-design/PLAN-NNN-integration-test-design.md
```

---

## §11. CLI 拡張案 (既存 helix-plan 互換)

本 PLAN の generates に含まれる `cli/helix-plan` 拡張の設計意図。実装は PLAN-091 実装 session (別 session) にて se role が担当。

**既存 helix plan サブコマンド**: draft / review / finalize / reset / list / status / lint / import

**V5 拡張方針 (既存 alias 拡張 + 新 subcommand 追加)**:

```bash
# --- 既存 subcommand 拡張 (互換維持) ---

# PLAN 新規作成 (既存 draft の拡張: --kind / --layer / --drive / --parent を追加)
helix plan draft --title "タイトル" \
  --kind impl --layer L4 --drive be \
  --parent PLAN-091

# PLAN frontmatter 検証 (既存 lint の V5 mode: --v5 フラグで matrix + agent_slots + workflow_phase 検証追加)
helix plan lint docs/plans/PLAN-091-v5-framework-core.md --v5
# alias: helix plan validate --plan-id PLAN-091 → helix plan lint --v5 に転送

# PLAN 詳細表示 (既存 status の拡張: --frontmatter フラグで frontmatter YAML を表示)
helix plan status --id PLAN-091 --frontmatter

# --- 新規 subcommand (既存と衝突なし) ---

# dependencies chain 確認
helix plan deps PLAN-091 --depth 2

# generates 一覧 (成果物から PLAN への逆引き)
helix plan generates --artifact-path cli/helix-plan
```

**旧命名との対応 (互換 alias)**:

| 旧命名 (Round 1 設計) | 新命名 (既存互換) | 備考 |
|---|---|---|
| `helix plan create` | `helix plan draft --kind X --layer Y --drive Z` | 既存 draft の拡張 |
| `helix plan validate` | `helix plan lint --v5` | 既存 lint の V5 mode |
| `helix plan show` | `helix plan status --frontmatter` | 既存 status の拡張 |
| `helix plan deps` | `helix plan deps` (新規) | 衝突なし |
| `helix plan generates` | `helix plan generates` (新規) | 衝突なし |

### 11.1 plan_validator.py の責務

`cli/lib/plan_validator.py` (本 PLAN generates に含まれる) が担う検証:

1. frontmatter 必須フィールド (plan_id / title / kind / layer / drive / status) の存在確認
2. kind が 11 種の有効値か確認
3. layer が 15 種の有効値か確認 + R0-R4 / S0-S4 の誤用を検出 (exit 2)
4. drive が 9 種の有効値か確認
5. workflow_phase が定義済み 10 値のいずれかか確認 (任意フィールド)
6. agent_slots[].role が ROLE_MAP 30 種の有効値か確認
7. dependencies の cycle detection
8. dependencies の reciprocal consistency (PLAN-A.blocks に PLAN-B → PLAN-B.requires に PLAN-A)
9. dependencies の self-edge 禁止 (自 PLAN ID を requires に含まない)
10. generates の artifact_type が 16 種の有効値か確認
11. ADR snapshot 必要性の判定 (L2 大局判断キーワード検出 → warn)

---

## §12. P0 guard 設計 (TL v5 P0 遵守、CRITICAL)

承認なし task pop は HELIX discipline 破壊 (TL v5 P0 絶対遵守)。

### 12.1 実行許可の 3 条件 (OR、いずれか 1 つで許可)

queue worker が `helix job` から task を pop する前に、以下の **3 条件のいずれかが満たされている**ことを fail-close で確認する:

| 条件 | 判定方法 | 備考 |
|---|---|---|
| **explicit_consent** | ユーザーの明示承認 (OK / 実装して / proceed 等の発言) | 最強の許可 |
| **current_wbs_match** | 作業対象が L3 工程表 / task-plan.yaml の現在行に一致 | WBS 承認済み前提 |
| **handover_next_action_match** | handover Next Action に明示記載された task | session 継続前提 |

**注意**: `plan_valid` (helix plan lint --v5 通過) は **前提条件** であり実行許可ではない。plan_valid = true かつ 3 条件のいずれかが満たされない job は dispatch しない。

### 12.2 job payload 必須フィールド (PLAN-092 schema 設計への前提)

V5 P0 guard を実装するため、job payload に以下のフィールドを追加する (PLAN-092 で schema 設計):

```json
{
  "authorization_ref": "handover:CURRENT.json#next_action[2]",
  "authorized_by": "explicit_consent",
  "approved_at": "2026-05-20T10:00:00Z",
  "source_plan_id": "PLAN-091"
}
```

| フィールド | 説明 |
|---|---|
| `authorization_ref` | 許可の根拠 (handover path / WBS ID / consent_timestamp) |
| `authorized_by` | 3 条件のどれで許可されたか (explicit_consent / wbs_match / handover_match) |
| `approved_at` | 許可取得の timestamp |
| `source_plan_id` | 実行の根拠となる PLAN ID |

### 12.3 worker の reject 動作

上記 3 条件のいずれも満たさない job は:
- `helix job pop` が exit 2 で reject
- stderr に「P0 guard: authorization_ref が未設定、承認を取得してから再実行」を出力
- job status を `pending` のまま保持 (キューから取り除かない)

### 12.4 P0 guard の段階導入

| Phase | P0 guard 動作 |
|---|---|
| P1 | 警告のみ (authorization_ref 不在でも warn + 続行) |
| P2 | authorization_ref 必須、authorized_by 検証 |
| P3 以降 | fail-close (3 条件未満で exit 2 reject) |

---

## §13. テスト戦略 (本 PLAN 実装段階)

実装 session (PLAN-091 実装 session) で必要なテスト一覧。

### 13.1 plan_validator.py unit test (pytest)

```python
# cli/lib/tests/test_plan_validator.py で実装

# frontmatter parse
- test_parse_valid_frontmatter
- test_missing_required_field_raises

# kind / layer / drive enum 強制
- test_invalid_kind_returns_error
- test_invalid_layer_returns_error
- test_invalid_drive_returns_error

# layer に R0-R4 / S0-S4 を書いた場合のエラー
- test_layer_scrum_phase_rejected   # layer: S0 → exit 2
- test_layer_reverse_phase_rejected # layer: R2 → exit 2

# workflow_phase 検証
- test_valid_workflow_phase_s0_to_s4
- test_valid_workflow_phase_r0_to_r4
- test_invalid_workflow_phase_rejected

# agent_slots ROLE_MAP 30 種 enum 強制
- test_agent_slots_role_valid_30_roles
- test_agent_slots_role_invalid_raises  # codex-tl 等独自 slug → エラー

# generates artifact_type 16 種 enum 強制
- test_generates_artifact_type_all_16_valid
- test_generates_artifact_type_invalid_raises

# dependencies 検証
- test_cycle_detection  # A requires B, B requires A → error
- test_reciprocal_consistency  # A.blocks=[B], B.requires に A なし → warn
- test_self_edge_forbidden  # A.requires=[A] → exit 2

# P0 guard 回帰テスト (job_queue 側、fake payload)
- test_p0_guard_plan_valid_only_insufficient   # plan_valid=true だけでは dispatch 不可
- test_p0_guard_explicit_consent_passes        # explicit_consent → dispatch OK
- test_p0_guard_wbs_match_passes               # wbs_match → dispatch OK
- test_p0_guard_handover_match_passes          # handover_match → dispatch OK
- test_p0_guard_no_authorization_rejects       # 3 条件なし → exit 2
```

### 13.2 Bats テスト (helix plan コマンド)

```bash
# cli/tests/ で実装

# 既存互換維持
- test_plan_draft_existing_compat       # 既存 draft オプション動作保証
- test_plan_status_existing_compat      # 既存 status 動作保証
- test_plan_lint_existing_compat        # 既存 lint 動作保証 (--v5 なし)

# V5 拡張機能
- test_plan_draft_with_kind_layer_drive  # --kind impl --layer L4 --drive be
- test_plan_lint_v5_valid               # --v5 で valid PLAN → exit 0
- test_plan_lint_v5_invalid_kind        # --v5 で kind 不正 → exit 1 + warn
- test_plan_lint_v5_invalid_layer_r0    # --v5 で layer: R0 → exit 2
- test_plan_lint_v5_invalid_agent_slot  # --v5 で agent_slot に codex-tl → exit 1
- test_plan_status_frontmatter          # --frontmatter フラグ動作
- test_plan_deps_depth                  # deps --depth 2

# matrix fail-close (P3)
- test_plan_draft_matrix_outside_exit2  # kind: impl + layer: L1 → exit 2 (P3 以降)
- test_plan_id_alias                    # --id / --plan-id alias 確認
```

---

## §14. DoD (Definition of Done)

本 PLAN 完遂 (draft 起票段階) の判定基準:

1. **frontmatter 完備**: plan_id / title / kind / layer / drive / status / agent_slots / generates / dependencies / related_adr / related_docs が全て記述されている
2. **§5 語彙正本確定**: kind 11 種 / layer 15 種 / workflow_phase 10 値 / drive 9 種 / dependencies 構造 (cycle + reciprocal + self-edge) / agent_slots (ROLE_MAP 30 種 enum) / generates (16 種 artifact_type) が定義されている
3. **§6 単一実行正本凍結**: PLAN = plan_registry / helix job = runnable queue / handover = continuity / TodoWrite = ephemeral の 4 者分担が確定している
4. **§7 ADR snapshot ルール確定**: 必要条件 / PLAN ⊃ ADR レイヤー併存 / 違反検出方針が記述されている
5. **§8 template 11 種 Step 定義**: 11 kind 全件の標準 Step が記述されており、commit step を含まない
6. **§9 段階導入 P1〜P3 設計確定**: warning 内容 / fail-close 条件 / matrix 外典型例 (R0-R4 / S0-S4 の layer 誤用含む) が記述されている
7. **§10 V-model TDD 組み込み**: pair freeze ルール / QA 追加テストの独立レイヤー / impl template への反映が記述されている
8. **§12 P0 guard 設計確定**: 3 条件 (explicit_consent / wbs_match / handover_match) + job payload 必須フィールド + reject 動作 + 段階導入が記述されている
9. **§13 テスト戦略確定**: plan_validator.py unit test 一覧 / Bats テスト一覧 / P0 guard 回帰テストが記述されている
10. **ADR-025 同時起票**: docs/adr/ADR-025-v5-framework-core-decision.md が存在し、双方向 reference が確立されている
11. **Web 検索 3 query 以上**: §3 業界 standard 参照に Sources URL が記述されている

**実装 DoD** (別 session、本 PLAN の実装段階):
- `cli/helix-plan` に lint --v5 / draft (拡張) / status --frontmatter / deps / generates サブコマンドが実装されている
- `cli/lib/plan_validator.py` が §11.1 の 11 件の検証を実装している
- `cli/lib/tests/test_plan_validator.py` が §13.1 の全 case をカバーしている
- `cli/templates/plan/{kind}/template.md` 11 種が存在している
- pytest + bats 全回帰 PASS

---

## §15. V-model 4 artifact trace (本 PLAN の artifact 構造)

本 PLAN は **設計 artifact (①)** として機能する。4 artifact の対応:

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 (本 file) | docs/plans/PLAN-091-v5-framework-core.md |
| ② 実装コード | 未着手 (別 session) | cli/helix-plan / cli/lib/plan_validator.py 等 |
| ③ テスト設計 | 未起票 (別 session) | docs/v2/L4-test-design/PLAN-091-unit-test-design.md (予定) |
| ④ テストコード | 未着手 (別 session) | cli/lib/tests/test_plan_validator.py 等 |

**双方向 reference**:
- 本 PLAN → ADR-025: `related_adr: [ADR-025-v5-framework-core-decision]`
- ADR-025 → 本 PLAN: `Related: PLAN-091 (本設計 tree の実装 PLAN)`
- 本 PLAN → generates: 各 artifact_path に listed
- 実装コード (別 session) → 本 PLAN: docstring に `# 契約: PLAN-091 §5 frontmatter 語彙正本` 明示 (予定)

---

## §16. 関連 PLAN / ADR / memory

### 16.1 前段 PLAN (requires)
- [PLAN-087](PLAN-087-design-doc-web-search-guardrail.md): 本 PLAN §3 の WebSearch 3 query 義務の根拠
- [PLAN-088](PLAN-088-todowrite-agent-slot-framework.md): 本 PLAN §5.5 agent_slots の前提 (TodoWrite × agent slot)
- [PLAN-089](PLAN-089-gate-fail-close-design-doc-web-search-audit.md): 本 PLAN §9 段階導入 P3 fail-close 設計の前提
- [PLAN-090](PLAN-090-posttooluse-continueonblock-refactor.md): 本 PLAN §7 ADR snapshot ルールの PostToolUse 接続の前提
- [PLAN-MM-001](PLAN-MM-001-v5-framework-master-plan.md): 親設計、本 PLAN の正本宣言

### 16.2 後段 PLAN (blocks)
- PLAN-092: 本 PLAN §5 の語彙を frontmatter 受け側として DB 化 + §12 P0 guard の schema 実装
- PLAN-093: 本 PLAN §7.3 の `check_plan_adr_snapshot` を実装
- PLAN-100: 本 PLAN §5 の語彙を PLAN-001〜090 に retrofit
- PLAN-095〜099: 本 PLAN §5 語彙を参照して各トピックを展開

### 16.3 関連 ADR
- [ADR-025](../adr/ADR-025-v5-framework-core-decision.md): 本 PLAN の L2 大局判断 snapshot (同時起票)

### 16.4 関連 memory (再起動時参照順)
- `project_2026_05_20_v5_framework_evolution_recovery`: V5 確立過程の全記録
- `feedback_adr_before_plan_violation`: PLAN ⊃ ADR レイヤー併存 (§7 の根拠)
- `feedback_design_doc_web_search_required`: §3 WebSearch 義務 (PLAN-087 準拠)
- `feedback_dont_stop_with_carry_remaining`: session 終了前チェックリスト
