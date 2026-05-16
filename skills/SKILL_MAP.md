# HELIX Skill Map

## 正本宣言

- **正本**: SKILL_MAP.md + 各 SKILL.md + ツール設定（`~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md`）
- **手順正本**: `skills/tools/ai-coding/references/workflow-core.md` + `skills/tools/ai-coding/references/gate-policy.md`
- **矛盾時**: 実装 > アーカイブ資料（`docs/archive/`）

## モデル割当（真実は `cli/config/models.yaml`）

| ロール | モデル | thinking |
|--------|--------|--------|
| PM | Opus (Claude Code) | — |
| PMO Sonnet | claude-sonnet-4-6 | medium |
| PMO Haiku | claude-haiku-4-5-20251001 | low |
| TL | gpt-5.5 | high |
| SE | gpt-5.4 | high |
| PE | gpt-5.3-codex-spark / gpt-5.3-codex | low-medium |

## CLI ロール補足（30）

- CLI ロール数は 30 件: `tl`, `se`, `pg`, `qa`, `security`, `dba`, `devops`, `docs`, `research`, `legacy`, `perf`, `fe`, `recommender`, `classifier`, `effort-classifier`, `pmo-sonnet`, `pmo-haiku`, `pdm-tech-innovation`, `pdm-marketing-innovation`, `pdm-innovation-manager`, `impl-sonnet`, `pm-advisor`, `tl-advisor`, `pmo-helix-explorer`, `pmo-helix-scout`, `pmo-project-explorer`, `pmo-project-scout`, `pmo-tech-docs`, `pmo-tech-fork`, `pmo-tech-news`
- `classifier`: タスク記述を分類し、適切なロールや処理系への振り分けを補助する軽量分類ロール
- `recommender`: スキル候補を JSON で返す軽量推挙ロール（`helix skill search` の中核）
- `effort-classifier`: 工数・難易度・規模を分類して見積もりや実行方針の初期判定を補助するロール
- `pmo-helix-explorer`: HELIX framework 内資産詳細探索（skills/templates/cli/docs）
- `pmo-helix-scout`: HELIX 内軽量検索・候補列挙（1 hop 目）
- `pmo-project-explorer`: プロジェクト内資産詳細探索（code/docs/config）
- `pmo-project-scout`: プロジェクト内軽量検索・候補列挙（1 hop 目）
- `pmo-tech-docs`: 設計手法・概念の外部精読
- `pmo-tech-fork`: OSS/plugin 探索・転用判断
- `pmo-tech-news`: 最新 Tech 動向 sweep（週次想定）

## 参考正本（ADR / PLAN）

- `docs/adr/ADR-014-roles-config-format.md`
- `docs/adr/ADR-015-helix-v2-orchestration.md`
- `docs/plans/PLAN-028-helix-v2-orchestration.md`

## 4フェーズ思想

```
Phase 1: 計画（ドキュメント・テスト駆動）  L1 → L2 → L3
Phase 2: 実装（マイクロスプリント）          L4
Phase 3: 仕上げ（デザイン駆動）             L5 → L6 → L7 → L8
Phase 4: Run（本番運用確認）                L9 → L10 → L11

Phase R: リバース（既存コード→設計復元）   R0 → R1 → R2 → R3 → R4 → Forward → RGC（閉塞検証）
```

## オーケストレーションフロー

```
【企画】人間が要件提示
  ↓ → requirements-handover, estimation
L1  要件定義（要件構造化 + 受入条件定義 + ★受入テスト設計）
  ↓ G0.5 企画突合ゲート       [PM]       ★企画書の全項目が L1 に反映されているか
  ↓ G1   要件完了ゲート         [PM+PO]
  ↓ G1.5 PoC ゲート            [TL+PM]    条件付き
  ↓ G1R  事前調査ゲート         [自動/TL]  条件付き
  ↓ → design-doc, api, db, security, visual-design（方針）
L2  全体設計（方針・アーキテクチャ・visual方針・ADR + ★総合テスト設計）
  ↓ G2   設計凍結ゲート         [TL+PM]    ★adversarial-review ★ミニレトロ ★セキュリティ① ★V-model 総合テスト設計
  ↓ → api-contract, dependency-map, estimation §8-10
L3  詳細設計 + API契約 + テスト設計 + 工程表（★結合テスト設計 + ★機能設計 + ★単体テスト設計）
  ↓ G3   実装着手ゲート         [TL+PM]    ★API/Schema Freeze ★事前調査 ★V-model 結合/単体テスト設計
  ↓ → ai-coding §4
L4  実装（マイクロスプリント: .1a→.1b→.2→.3→.4→.5）★単体/結合テスト実装
  ↓ G4   実装凍結ゲート         [TL+PM]    ★セキュリティ② ★ミニレトロ ★V-model テスト実装網羅 (単体 + 結合)
  ↓ → visual-design
L5  Visual Refinement（DESIGNER.md 駆動）
  ↓ G5   デザイン凍結ゲート     [TL+PM]    UIなしskip可
G5 デザイン凍結ゲート:
  前提条件: ①information / ②layout / ③ux の三点セット (L2 visual-design) が完成していること
  UIなし: スキップ可
  ↓ → verification, testing, quality-lv5
L6  統合検証（E2E・性能・セキュリティ・運用準備）
  ↓ G6   RC判定ゲート（Release Candidate）  [PM+TL+PO]  ★セキュリティ③
  ↓ G6.5 Pre-Release 静的検証     [TL]       ★template/破壊変更チェック
  ↓ G6.7 Pre-Release 動的検証     [TL]       ★E2E/perf/security
  ↓ G6.9 Pre-Release 本番直前確認 [TL+PM]    ★rollback/monitoring/on-call
  ↓ → deploy, infrastructure, observability-sre
L7  デプロイ（staging → 本番 → watch）
  ↓ G7   安定性ゲート          [自動/PM]    ★セキュリティ④
  ↓ → verification §14
L8  受入（受入、ゲート無: 要件 ↔ 最終成果物の突合 → PO最終承認）★ミニレトロ
  ↓ L9  デプロイ検証（staging 本番）
  ↓ G9   デプロイ安定性ゲート    [自動/PM]    fail-close
  ↓ L10 観測（SLO/SLI watch）
  ↓ G10  観測完了ゲート         [PM]        fail-close
  ↓ L11 運用学習（運用改善）
  ↓ G11  運用学習完了ゲート     [PM]        fail-close
```

**ゲート詳細・セキュリティ・遷移ルール** → `skills/tools/ai-coding/references/gate-policy.md` 参照

### HELIX Reverse（既存コードからの逆引き設計）

```
【既存コード】設計書なし・テストなしのシステム
  ↓ → reverse-analysis, legacy
R0  Evidence Acquisition（コード+DB+設定+運用実態の証拠収集）
  ↓ RG0  証拠網羅ゲート           [TL]
  ↓ → api-contract, verification
R1  Observed Contracts（API/DB/型の機械抽出 + characterization tests）
  ↓ RG1  契約検証ゲート           [TL]
  ↓ → design-doc, adversarial-review
R2  As-Is Design（アーキテクチャ復元 + ADR推定）
  ↓ RG2  設計検証ゲート           [TL + adversarial-review]
R3  Intent Hypotheses（要件仮説 + PO検証）
  ↓ RG3  仮説検証ゲート           [PM+PO+TL]
R4  Gap & Routing（差分集約 → Forward HELIX に接続）
  ↓
Forward HELIX（Gap種別で L1/L2/L3/L4 に振り分け）
```

#### Reverse type matrix

| Type | 起点 | R0 | R1 | R2 | R3 | R4 | RGC |
|------|------|----|----|----|----|----|-----|
| code | レガシーコード | 証拠収集 | 契約抽出 | 設計復元 | 仮説検証 | Gap → Forward | 閉塞検証 |
| design | デザイン資産 | 資産収集 | skip | DAG/順序 | PO 検証 | Forward routing | 閉塞検証 |
| upgrade | 既存 system + 新版 | version diff | 影響分析 | 設計差分 | risk 評価 | Forward routing | upgrade RGC skip |
| normalization | 設計 drift | drift 検出 | skip | normalize 設計 | PO 確認 | Forward routing | 閉塞検証 |
| fullback | 実装完遂後 | 実装証拠 | 文書 gap 抽出 | alignment 設計 | 文書 PO 確認 | Forward routing | 閉塞検証 |

#### Reverse type notes

- code: 既存コード・DB・設定・運用実態を起点に、観測契約から設計と意図を復元する。R1 の契約抽出が中核で、既存 code 型の標準経路は維持する。
- design: デザイン資産起点。R1 の既存コード契約抽出は行わず skip し、R2 で DAG/実装順を起こして R3 で PO 検証へ進む。
- upgrade: 既存版と新版の差分が起点。R0 で version diff を取り、R2 で設計差分、R4 で Forward 案件を決める。gap closure は upgrade 完了として Forward 側で評価するため RGC は skip。
- normalization: 設計 drift の正規化が起点。R1 は skip し、R2 で normalize 設計、R3 で PO 確認、R4 で Forward routing に接続する。
- fullback: 実装完遂後の文書整合が起点。R0 で実装証拠、R1 で文書 gap、R2 で alignment 設計、R3 で文書 PO 確認、R4 で closure routing を行う。

**Reverse ゲート詳細** → `skills/tools/ai-coding/references/gate-policy.md §Reverse ゲート` 参照
**Reverse フロー詳細** → `workflow/reverse-analysis/SKILL.md` 参照

### HELIX Scrum（検証駆動 / 要件未確定時）

```
【仮説・要件不確実】実現可能性不明・PoC 要・技術検証必要
  ↓ helix size --uncertain → scrum 判定 / または helix scrum init を直接起動
S0  Backlog 構築（仮説一覧 + 検証質問 + 成功条件）
  ↓ helix scrum backlog add
S1  Sprint Plan（ゴール + 対象仮説選定）
  ↓ helix scrum plan
S2  PoC 実装（Codex に委譲、verify/ スクリプト化）
  ↓ helix scrum poc --hypothesis H001
S3  Verify（全検証スクリプト実行 → リグレッション蓄積）
  ↓ helix scrum verify
S4  Decide（confirmed / rejected / pivot）
  ↓ helix scrum decide --hypothesis H001 --confirmed
  ↓
Forward HELIX（確定仮説を L1 要件に昇格 → helix size で fe/be/fullstack 再判定）
```

**Scrum モードの特徴**:
- Forward HELIX のフェーズ進行 (L1-L11) は走らない。`.helix/scrum/` 配下で独立管理
- verify/*.sh は毎回全実行 → リグレッション検出
- `decide --confirmed` で Forward HELIX に接続
- `db` / `agent` エッジケースでも「仮説検証フェーズ」として scrum 前段利用可能

## readiness と carry rule

PLAN-004 v5 連動として、L1-L11 の entry/exit に readiness 条件を含める。

- P0: gate stop（即修正）
- P1: gate stop OR carry（PM承認）
- P2: 次 L 開始まで or debt として `.helix/audit/deferred-findings.yaml` へ carry
- P3: 任意 carry

deferred-finding は accuracy_score に反映し、G1-G11 の評価算定に加算（減点）する。  
（重みは既定の deferred レベル係数を参照）

## タスクサイジング

3軸の**最大サイズ**を採用:

| 軸 | S | M | L |
|----|---|---|---|
| ファイル数 | 1-3 | 4-10 | 11+ |
| 変更行数 | ~100 | 101-500 | 501+ |
| API/DB変更 | なし | 片方 | 両方 |

## 駆動タイプ

`helix size --drive <type>` で明示指定、または `--ui/--api/--db/--uncertain` フラグで自動判定。L2〜L5 の中身とゲート判定基準が変わる。

### 主要 4 パターン (通常はこの 4 択)

| 駆動タイプ | 起点 | 典型プロジェクト |
|-----------|------|----------------|
| **be**（デフォルト） | API/ロジック | 業務系、解析系、SaaS バックエンド |
| **fe** | デザイン/UX → モック駆動 | LP、EC、ダッシュボード、UX重視プロダクト |
| **scrum** | 仮説検証（要件不確実） | PoC、新規事業、技術検証、リサーチ系 |
| **fullstack** | BE+FE同時（Twin Track） | SaaS、EC、ダッシュボード + API |

### エッジケース (特殊起点)

| 駆動タイプ | 起点 | 典型プロジェクト |
|-----------|------|----------------|
| **db** | スキーマ/データモデル | マスタ管理、ERP、データ基盤 |
| **agent** | ツール/プロンプト | AI アプリ、自動化、ワークフロー |

### 自動判定ロジック (`helix size` のフラグベース)

```
--uncertain あり                   → scrum (Phase S / 検証駆動)
--ui + (--api or --db) あり        → fullstack (Twin Track)
--ui のみ                          → fe (モック駆動)
--api or --db あり                 → be
フラグなし                         → be (デフォルト)
```

明示 `--drive <type>` 指定は常に最優先。`db` / `agent` は明示指定のみ。

### 駆動タイプ別 L2〜L11

| フェーズ | be | fe | db | fullstack | agent |
|---------|----|----|----|-----------|----|
| L2 設計 | API設計・アーキテクチャ・ADR | **モック駆動設計**（方針+トークン+`mock.html`+`state-events.md`） | ER図・スキーマ設計 | BE方針+FE方針（**mock含む**）+接続契約方針（同時策定） | ツール定義・プロンプト設計 |
| L3 詳細 | API契約+DB+工程表 | TL が `state-events.md` から **API契約導出**+DB+工程表 | マイグレーション+API契約+工程表 | D-API+D-UI+D-CONTRACT+D-DB+D-STATE+**mock**+工程表 | ツール契約+統合テスト設計+工程表 |
| L4 実装順 | ロジック→API→FE | BE（契約ベース）∥ FE（**モック→本実装昇格**）→ 統合 | スキーマ→CRUD→API→FE | Phase A: BE Sprint ∥ FE Sprint（**mockを起点**）→ Phase B: L4.5結合 | ツール→オーケストレーション→UI |
| L5 重み | 薄い（表示確認） | **厚い**（デザイン駆動） | 薄い（管理画面確認） | 標準（結合後にVisual Refinement） | 会話UI/デモ確認 |
| L9 Run-1（デプロイ検証） | 標準 | 標準 | 薄い | 標準 | 薄い |
| L10 Run-2（観測） | 薄い | 標準 | 薄い | 標準 | 薄い |
| L11 Run-3（運用学習） | 標準 | 標準 | 薄い | 標準 | 標準 |
| G2 凍結 | API設計凍結 | **モック凍結**（UX承認 + MOCK-* auto-enqueue 発火） | スキーマ凍結 | 接続契約方針凍結（BE+FE+Contract三点セット） + MOCK-* auto-enqueue | ツール定義凍結 |
| G3 着手 | API/Schema Freeze | **モック+API/Schema Freeze** | Migration Freeze | API/Schema/UI/Contract全凍結 | Tool Contract Freeze |
| G4 追加条件 | — | **MOCK-HARDCODE + MOCK-CODE-LEAK resolved 必須** | — | 同左（fe同等） | — |
| G6 追加条件 | — | **MOCK-DERIVED-CONTRACT resolved 必須** | — | 同左（fe同等） | — |

auto-thinking は opt-in flag、default は role conf の `codex_thinking`。

> **UI / fullstack の詳細フロー**（L2 ステップ内訳 / TL 契約導出手順 / モック由来 debt ライフサイクル / 責務分担表 / アンチパターン）→ `skills/project/ui/references` 配下を参照

### L5 要否の判定

| 駆動タイプ | L5 必要条件 |
|-----------|------------|
| be | `--ui` 有りのときのみ |
| fe | **常に必要**（FE駆動の核心） |
| db | `--ui` 有りのときのみ |
| fullstack | **常に必要**（結合後の Visual Refinement） |
| agent | **常に必要**（会話UI/デモ） |

## フェーズスキップ決定木

駆動タイプで L5 の要否が変わる（上記参照）。それ以外の判定ロジックは共通:

```
├─ S（小規模）
│   ├─ バグ修正 / リファクタ / ドキュメント → L4 のみ
│   ├─ 新規小機能 / 新モジュール → L1 → L2 → L3 → L4 → (L5) → L6
│   └─ UI変更 → L2 → L3 → L4 → L5 → L6
│   ※ S案件の L1/L3 は最小版: 目的+受入条件+タスクリスト
│   ※ 新機能は S でも L1（要件定義）を飛ばさない
├─ M（中規模）
│   ├─ 新機能/新モジュール → L1 → フルフロー
│   ├─ API/DB変更あり → L1 → L2 → L3 → L4 → (L5) → L6 → L7 → L8
│   ├─ API/DB変更なし + L5要 → L1 → L2 → L3 → L4 → L5 → L6 → L7 → L8
│   │   G1.5/G1R skip可、G3会議省略可
│   └─ バグ修正/リファクタ → L2 → L3 → L4 → (L5) → L6 → L7 → L8
└─ L（大規模）
    ├─ L5要 → フルフロー
    └─ L5不要 → フルフロー（L5/G5 skip）
```

(L5) = 駆動タイプの L5 要否判定に従う

Run 工程（L9-L11）の適用可否:
- 本番運用あり: G9-G11 を必須適用
- PoC / 検証寄り: 本番影響がなければ Run は skip 可

fullstack 追加条件:
- L4 は Phase A（BE Sprint ∥ FE Sprint）→ Phase B（L4.5 結合）
- L5 は常に必要（結合後の Visual Refinement）

**セキュリティゲート強制条件** → `skills/tools/ai-coding/references/gate-policy.md §セキュリティゲート強制条件` 参照

## スキル群配置（107スキル）

パス: `skills/{カテゴリ}/{スキル名}/SKILL.md`
詳細 I/O → `orchestration-workflow.md` / 遷移条件 → `layer-interface.md`（共に `skills/tools/ai-coding/references/`）

| カテゴリ | スキル |
|---------|--------|
| workflow/ | project-management, dev-policy, estimation, requirements-handover, compliance, design-doc, api-contract, dependency-map, quality-lv5, deploy, dev-setup, incident, observability-sre, postmortem, verification, adversarial-review, context-memory, reverse-analysis, **research**, **poc**, **gate-planning**, **schedule-wbs**, **threat-model**, **runbook**, **debt-register**, **reverse-r0**, **reverse-r1**, **reverse-r2**, **reverse-r3**, **reverse-r4**, **reverse-rgc** |
| common/ | visual-design, design, coding, refactoring, documentation, security, testing, error-fix, performance, code-review, infrastructure, git |
| project/ | ui, api, db |
| advanced/ | tech-selection, i18n, external-api, ai-integration, migration, legacy, **tech-innovation**, **marketing-innovation**, **innovation-mgr** |
| tools/ | ai-coding, ide-tools, **web-search**, **ai-search** |
| integration/ | agent-teams, **agent-design**, **agent-cost-design** |
| writing/ | japanese, explain, story, presentation, social |
| design-tools/ | diagram, web-system, pptx, graphic, character |
| automation/ | site-mapping, browser-script, flow-optimize, scheduler, job-queue, lock, init-setup, observability |
| **agent-skills/** | idea-refine, spec-driven-development, planning-and-task-breakdown, incremental-implementation, test-driven-development, context-engineering, source-driven-development, frontend-ui-engineering, api-and-interface-design, browser-testing-with-devtools, debugging-and-error-recovery, code-review-and-quality, security-and-hardening, performance-optimization, ci-cd-and-automation, deprecation-and-migration, documentation-and-adrs, shipping-and-launch, using-agent-skills, **system-design-sizing**, **technical-writing**, **mock-driven-development**, **helix-scrum** |

**2026-04-17 追加分** (20スキル):
- workflow/: research (G1R)・poc (G1.5)・gate-planning (G0.5/G1.5)・schedule-wbs (L3)・threat-model (G2)・runbook (L6)・debt-register (G4)・reverse-r0〜r4 + reverse-rgc (R0-R4 + RGC)
- project/: ui/design-doc を経由する経路を継続し、FE 系サブエージェント個別運用は v2 方針で停止
- tools/: web-search (native WebSearch + WebFetch)・ai-search (Haiku 4.5 委譲)

**2026-04-22 追加分** (25スキル、agent-skills/ カテゴリ新設):
- 上流由来 19 (addyosmani/agent-skills MIT、日本語化済): idea-refine / spec-driven-development / planning-and-task-breakdown / incremental-implementation / test-driven-development / context-engineering / source-driven-development / frontend-ui-engineering / api-and-interface-design / browser-testing-with-devtools / debugging-and-error-recovery / code-review-and-quality / security-and-hardening / performance-optimization / ci-cd-and-automation / deprecation-and-migration / documentation-and-adrs / shipping-and-launch / using-agent-skills (メタ)
- HELIX 独自 4: system-design-sizing (donnemartin/system-design-primer MIT 根拠)・technical-writing (Google Tech Writing CC-BY 根拠)・mock-driven-development (FE 駆動核心)・helix-scrum (S0-S4 仮説検証)
- 除外 3 (本体 workflow/ に既存): adversarial-review / debt-register / reverse-analysis
- 付随: .claude-plugin/ (marketplace 配布用)・.claude/commands/ 7 本 (slash commands)・addyosmani/agent-skills 由来の 3 役（code-reviewer / security-audit / qa-test）は .claude/agents/ に統合（現在の .claude/agents/ は 19 エージェント構成: be-api / be-logic / code-reviewer / db-schema / devops-deploy / qa-test / security-audit / pmo-sonnet / pmo-haiku / pdm-tech-innovation / pdm-marketing-innovation / pdm-innovation-manager / pmo-helix-explorer / pmo-helix-scout / pmo-project-explorer / pmo-project-scout / pmo-tech-docs / pmo-tech-fork / pmo-tech-news）・agent-skills/references/ 5 checklist・agent-skills/hooks/ (session-start)
- 統合ガイド: docs/agent-skills/README.md・docs/agent-skills/skill-anatomy.md

既存 `workflow/reverse-analysis` は各 reverse-r* へのルーターに縮小。既存 `project/ui` は UI 参照インデックスとして残存。

**2026-05-08 追加分** (1スキル、ユーザー自作):
- integration/: **agent-design** (AIエージェント設計の判断軸 11 本 = 要素・骨格・思考指定・出力指定・スキーマ・前段制約・後段責務の連鎖、`型 = 要素定義 + フレーム化` の還元式と縛りの 3 階層を中核とする L2/L3 設計概論)

**2026-05-13 追加分** (1スキル、ユーザー自作):
- integration/: **agent-cost-design** (AIエージェント構築のコスト予算・ガードレール確定スキル。8 references = multi-vendor / fallback-policy / retry-design / flow-design / cost-estimation / test-budget / guardrail-impl / budget-monitoring を Phase 0-5 順序で参照。1.2 倍上振れ係数固定、80% 到達で追加予算申請、ハードリミットはラッパー層実装が中核原則。L1/L2/L3 エージェント設計の前段必須)

### 責務境界クリア化（テスト・検証・品質系の使い分け）

3スキルが近接領域だが層が異なる。発火順に整理:

| スキル | フェーズ | 役割 |
|--------|---------|------|
| `common/testing` | **L4** 実装時 | テストケース作成・テストテンプレート (unit/integration/E2E の書き方) |
| `workflow/quality-lv5` | **L6** 統合検証 | テスト品質を Lv1-5 で評価・テストピラミッド比率・カバレッジ目標の判定 |
| `workflow/verification` | **all** (L1〜L11 + R0-R4 + RGC) | Spec駆動検証・L8-L11 仕様/運用突合・Reverse RG0-RG3/RGC ゲート検証基盤 |

使い分けルール:
- **テストを書く**: `common/testing` のみ参照
- **テスト品質の合否判定**: `workflow/quality-lv5` (G4/G6 ゲート時)
- **成果物 ↔ 要件の突合検証**: `workflow/verification` (L1 受入条件 / L8 受入 / Reverse ゲート)

### 責務境界クリア化 (AIエージェント設計系の使い分け)

近接する 4 スキルがあるが層が異なる。**判断に迷ったときに開く reference** という共通機能を持つので境界を明示:

| スキル | 守備範囲 | 利用タイミング |
|--------|---------|---------------|
| `integration/agent-cost-design` | **エージェント着手前のコスト予算・ガードレール確定** (生成フロー / マルチベンダー / コスト見積 / 予算監視) | L1 受領直後〜L2 設計前。**設計・実装に着手する前に必ず** 通る前段ゲート |
| `integration/agent-design` | **個別 LLM agent / task** の structural design (要素・骨格・前段制約・後段責務) | L2 ADR / L3 D-API / L4 実装で **判断に迷ったとき** 該当 axis を開く |
| `integration/agent-teams` | **複数 agent の協調・分業** | agent-design で個別設計後、複数 agent をチーム化するとき |
| `agent-skills/spec-driven-development` | **仕様駆動開発全般** (LLM 限定なし) | spec → 実装の上位プロセス。agent-design はその LLM 特化版 |

使い分けルール:
- **エージェント構築タスク受領 → 着手前**: `integration/agent-cost-design` (Phase 0-5 でコスト/予算/ガードレール確定が最優先)
- **個別 LLM agent の設計判断で迷う**: `integration/agent-design` (axis 11 本から該当を引く)
- **複数 agent の協調設計**: `integration/agent-teams`
- **LLM agent 以外も含む仕様駆動**: `agent-skills/spec-driven-development`
- **D-API / D-CONTRACT の HELIX 正本**: `workflow/api-contract` (agent-design axis 07 から接続)

エージェント構築の標準フロー: **agent-cost-design (前段) → agent-design (個別構造) → agent-teams (協調)**。コストガードを通さずに structural design へ進まない。

### 既存スキル強化メモ（description 更新）

```yaml
common/security:
  description: セキュリティ対策で環境別設定ガイド・認証認可実装パターン・脆弱性対策チェックリストとOWASP検証手順・秘密情報スキャン・AI生成コード品質チェックを提供
common/error-fix:
  description: エラー修正で体系的デバッグ手順・失敗パターンレジストリ運用・危険コマンドガードを提供
common/visual-design:
  description: ビジュアル設計原則・AI品質チェックに加え、DESIGN.md 9セクション形式ブランド参照（JP24件+EN10件）・IA/モーション/UXパターン/a11y/データViz論を references/ で提供
design-tools/web-system:
  description: shadcn/uiデザインシステム構築に加え、デザイントークン3層設計・スケール策定プロセス・DESIGN.md形式のD-VIS-ARCH適用手順を references/ で提供
workflow/observability-sre:
  description: SLO/SLI設計・構造化ログ・ダッシュボード・AIエージェントメトリクスに加え、リアルタイム監視設計とD-OBSテンプレートを提供
workflow/verification:
  description: L1〜V-L6検証に加えて、D-API/D-CONTRACT/D-DB起点のSpec駆動検証とL8仕様突合チェックを提供
tools/ai-coding:
  description: AIコーディング運用に加えて、GitHub ActionsでのCI/CDエージェント統合パターンを提供
integration/agent-teams:
  description: 複数エージェント協調運用に加えて、n8n/Dify発想のビジュアルワークフロー設計を提供
automation/site-mapping:
  description: Crawl4AI中心のサイト構造抽出に加えて、Firecrawl代替クローラーの使い分けと安全運用を提供
common/performance:
  description: パフォーマンス最適化指針に加えてAIセッション記録/再生と学習連携の運用手順を提供
writing/explain:
  description: 4部構成テンプレートに加えてEEATベースのコンテンツ品質監査チェックを提供
writing/social:
  description: SNS投稿テンプレートに加えてGEO（生成エンジン最適化）の設計指針を提供
automation/browser-script:
  description: Playwright記録からのE2E化に加えてaxe-coreによるアクセシビリティ自動検証を提供
```

## V-model 4 artifact 双方向 trace (2026-05-17 確立 / 訂正)

詳細は `helix/HELIX_CORE.md §設計⇔テスト対応`。

要点:
- 4 artifact は **別文書**: ① 設計 / ② 実装コード / ③ テスト設計 / ④ テストコード
- 各 artifact は **双方向 reference** で対応関係を明示 (設計⇔テスト設計、設計⇔実装、テスト設計⇔テストコード)
- L2 → 総合テスト設計、L3 → 結合テスト設計、機能設計 → 単体テスト設計、L1 → 受入テスト設計
- 2 つ以上を 1 文書に統合することは V-model 違反 (例: D-API EXT 内にテスト設計埋め込み)
- G2/G3/G4 ゲートで 4 artifact 揃いを確認 (PLAN-075 Phase 5 で自動 lint 化予定)

## 工程別 subagent 起動マップ (PLAN-076、2026-05-17 確立)

詳細は `helix/HELIX_CORE.md §工程別 subagent 起動マップ`。

要点:
- subagent 14 種を 2 分類: **mandatory by phase (10 種)** + **on-demand by judgment (4 種)**
- mandatory は工程必須、`helix agent fire-mandatory --phase Lx` で一括投入、helix.db で audit
- on-demand は free will、`helix agent suggest` で候補提示
- G2/G3/G4 ゲートで mandatory 呼び出し audit (PLAN-076 Phase 5 で fail-close)

## Sprint Plan 標準構造 (PLAN-077、2026-05-17 確立)

詳細は `helix/HELIX_CORE.md §Sprint Plan 標準構造`。

要点:
- L4 実装中の Sprint Plan が標準 8 ステップに固定化される
- **mandatory in sprint**: 機械チェック (py_compile / lint) + テスト起動 (該当 test / 全回帰) + レビュー (セルフ / pmo-sonnet)
- **on-demand in sprint**: security audit / perf test / tl-advisor 等
- Sprint Exit 前に mandatory 全通過必須、`helix sprint complete --auto-check` で機械化

## メンテナンス指針

1. スキル追加時: SKILL_MAP.md を更新。500行超 → references/ に分割
2. 重複防止: 追加前に既存スキルとの重複確認
3. 廃止済みスキル名: architecture / orchestrator / codex / vscode-plugins → **スキル名としての参照**禁止（ツール名 `helix review`・メタデータ `codex: true`・YAML キー `architecture:` は正当な用法）。検出: `rg -wn "orchestrator" skills/ --glob '!SKILL_MAP.md'`
4. metadata.helix_layer 必須。description は具体的用途を記載（「〇〇関連」禁止）

## 自動推挙システム（gpt-5.4-mini）

全 107 スキル + 121 references を LLM マッチングで自動推挙する CLI を搭載。

```bash
helix skill list [--layer L2] [--category common] [--json]
helix skill show <skill-id> [--with-content]
helix skill catalog rebuild             # SKILL.md frontmatter + references 冒頭 blockquote を parse
helix skill search "<task>" [-n 5]      # Codex gpt-5.4-mini で推挙
helix skill use <id> --task "..." [--dry-run] [--agent NAME] [--references PATHS]
helix skill chain "<task>" [-n 1]       # search → use の一気通貫
helix skill stats [--days 30]           # 使用統計（skill_usage テーブル）
helix budget
helix recipe <learn|promote|discover|list>  # learn/promote/discover は deprecated
helix handover resume
```

### 推挙の仕組み
- catalog: `.helix/cache/skill-catalog.json`（SKILL.md frontmatter + references 冒頭 `> 目的:` blockquote を機械抽出）
- エンジン: `gpt-5.4-mini` (`cli/roles/recommender.conf`、thinking=low)
- プロンプト: `cli/templates/prompts/skill-search.md`（9種の agent 決定マッピング含む）
- キャッシュ: `.helix/cache/recommendations/<sha256>.json` で 1 時間保存
- 使用履歴: `helix.db` (v5) の `skill_usage` テーブル

### 委譲の自動化
`helix skill use` は recommender が選んだ agent へ委譲する:
- `tl` / `se` / `pe` / `qa` / `security` / `dba` / `devops` / `docs` / `research` / `legacy` / `perf` は Codex ロール（`helix codex --role X --task "<bundle>\n\n<task>"` で自動実行）
- PMO 系は `helix claude --role pmo` 系へ委譲し、FE 設計は TL→PM チェック後に PMO 経由の整合運用へ回す

### 実装ファイル
- `cli/lib/skill_catalog.py` — catalog 生成・読み込み（SKILL.md + references parser）
- `cli/lib/skill_recommender.py` — Codex 呼び出し・キャッシュ
- `cli/lib/skill_dispatcher.py` — context bundle 作成・委譲・DB 記録・stats
- `cli/helix-skill` — bash ディスパッチャ (list/show/catalog/search/use/chain/stats)
- `cli/roles/recommender.conf` — gpt-5.4-mini ロール定義
- `cli/templates/prompts/skill-search.md` — LLM プロンプトテンプレート

## コードインデックス（PLAN-011 + PLAN-012 + PLAN-013）

既存コードに `# @helix:index ...` メタデータを付与し、検索・重複検知・統計を可能にする `helix code` 系 CLI。skill catalog と同じ枠組みをコード資産へ拡張する。

```bash
helix code build                                        # 全 tracked files を走査し catalog を再構築
helix code find "<query>" [-n 5]                        # gpt-5.4-mini で流用候補を探索
helix code show <id>                                    # path / line / metadata を表示
helix code dup [--threshold 0.85] [--domain <name>]     # 同一 domain 内の重複候補を検出
helix code stats [--by domain|since]                    # domain / since / bucket / uncovered 別の集計
helix code stats --uncovered [--scope core5|cli-lib|all] [--bucket coverage_eligible|private_helper|excluded|all] [--seed-candidate true|false|all] [--seed-promotable true|false|all] [--fail-under N] # PLAN-012/013
helix code list [--domain <name>] [--json]              # entry 一覧
```

メタデータ規約:
- Python: `# @helix:index id=code-catalog.parse-frontmatter domain=cli/lib summary=YAML frontmatterをdictに展開`
- bash: `# @helix:index id=helix-code.build domain=cli summary=code-catalogを再構築`

関連 PLAN: PLAN-011（catalog skeleton） + PLAN-012（coverage gate） + PLAN-013（taxonomy）

3-bucket taxonomy 概要:
- coverage_eligible: 公開 symbol、coverage gate の母集団（core5 は 80% gate）
- private_helper: 非公開 symbol（`_` 始まり）、PoC seed 候補
- excluded: `setup.sh` / `skills/agent-skills/hooks/*.sh` / `verify/*.sh` の固定 3 pattern
- non_indexable_paths: `tests/*.py` / `fixture/*` / `generated/*` / `vendor/*`（bucket 分類前 pre-filter）
- helix.db schema: v14 → v15（`bucket` / `symbol_line` を追加）

PLAN-013 運用フロー（L1-L11 追跡）:
- L4 entry: `helix code find` / `helix code stats --uncovered --bucket coverage_eligible` で既存資産を確認
- L4 implementation: 新規 public symbol は `coverage_eligible`、`_` 始まり helper は `private_helper` に分類
- L4 build: `helix code build` で catalog を再生成し `bucket` / `symbol_line` / metadata を自動付与
- G4: `helix code stats --scope core5 --bucket coverage_eligible --fail-under 80` を実施して coverage gate
