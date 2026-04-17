# HELIX Skill Map

## 正本宣言

- **正本**: SKILL_MAP.md + 各 SKILL.md + ツール設定（`~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md`）
- **手順正本**: `tools/ai-coding/references/workflow-core.md` + `tools/ai-coding/references/gate-policy.md`
- **矛盾時**: 実装 > アーカイブ資料（`docs/archive/`）

## 3フェーズ思想

```
Phase 1: 計画（ドキュメント・テスト駆動）  L1 → L2 → L3
Phase 2: 実装（マイクロスプリント）          L4
Phase 3: 仕上げ（デザイン駆動）             L5 → L6 → L7 → L8

Phase R: リバース（既存コード→設計復元）   R0 → R1 → R2 → R3 → R4 → Forward → RGC（閉塞検証）
```

## オーケストレーションフロー

```
【企画】人間が要件提示
  ↓ → requirements-handover, estimation
L1  要件定義（要件構造化 + 受入条件定義）
  ↓ G0.5 企画突合ゲート       [PM]       ★企画書の全項目が L1 に反映されているか
  ↓ G1   要件完了ゲート         [PM+PO]
  ↓ G1.5 PoC ゲート            [TL+PM]    条件付き
  ↓ G1R  事前調査ゲート         [自動/TL]  条件付き
  ↓ → design-doc, api, db, security, visual-design（方針）
L2  全体設計（方針・アーキテクチャ・visual方針・ADR）
  ↓ G2   設計凍結ゲート         [TL+PM]    ★adversarial-review ★ミニレトロ ★セキュリティ①
  ↓ → api-contract, dependency-map, estimation §8-10
L3  詳細設計 + API契約 + テスト設計 + 工程表
  ↓ G3   実装着手ゲート         [TL+PM]    ★API/Schema Freeze ★事前調査
  ↓ → ai-coding §4
L4  実装（マイクロスプリント: .1a→.1b→.2→.3→.4→.5）
  ↓ G4   実装凍結ゲート         [TL+PM]    ★セキュリティ② ★ミニレトロ
  ↓ → visual-design
L5  Visual Refinement（DESIGNER.md 駆動）
  ↓ G5   デザイン凍結ゲート     [TL+PM]    UIなしskip可
  ↓ → verification, testing, quality-lv5
L6  統合検証（E2E・性能・セキュリティ・運用準備）
  ↓ G6   RC判定ゲート（Release Candidate）  [PM+TL+PO]  ★セキュリティ③
  ↓ → deploy, infrastructure, observability-sre
L7  デプロイ（staging → 本番 → watch）
  ↓ G7   安定性ゲート          [自動/PM]    ★セキュリティ④
  ↓ → verification §14
L8  受入（要件 ↔ 最終成果物の突合 → PO最終承認）★ミニレトロ
```

**ゲート詳細・セキュリティ・遷移ルール** → `tools/ai-coding/references/gate-policy.md` 参照

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

**Reverse ゲート詳細** → `tools/ai-coding/references/gate-policy.md §Reverse ゲート` 参照
**Reverse フロー詳細** → `workflow/reverse-analysis/SKILL.md` 参照

## タスクサイジング

3軸の**最大サイズ**を採用:

| 軸 | S | M | L |
|----|---|---|---|
| ファイル数 | 1-3 | 4-10 | 11+ |
| 変更行数 | ~100 | 101-500 | 501+ |
| API/DB変更 | なし | 片方 | 両方 |

## 駆動タイプ

`helix size --drive <type>` で指定。L2〜L5 の中身とゲート判定基準が変わる。

| 駆動タイプ | 起点 | 典型プロジェクト |
|-----------|------|----------------|
| **be**（デフォルト） | API/ロジック | 業務系、解析系、SaaS バックエンド |
| **fe** | デザイン/UX | LP、EC、ダッシュボード |
| **db** | スキーマ/データモデル | マスタ管理、ERP、データ基盤 |
| **fullstack** | BE+FE同時 | SaaS、EC、ダッシュボード + API |
| **agent** | ツール/プロンプト | AI アプリ、自動化、ワークフロー |

### 駆動タイプ別 L2〜L5

| フェーズ | be | fe | db | fullstack | agent |
|---------|----|----|----|-----------|----|
| L2 設計 | API設計・アーキテクチャ・ADR | Visual方針・コンポーネント設計 | ER図・スキーマ設計 | BE方針+FE方針+接続契約方針（同時策定） | ツール定義・プロンプト設計 |
| L3 詳細 | API契約+DB+工程表 | コンポーネントツリー+Props+工程表 | マイグレーション+API契約+工程表 | D-API+D-UI+D-CONTRACT+D-DB+D-STATE+工程表 | ツール契約+統合テスト設計+工程表 |
| L4 実装順 | ロジック→API→FE | コンポーネント→スタイル→API繋ぎ | スキーマ→CRUD→API→FE | Phase A: BE Sprint ∥ FE Sprint → Phase B: L4.5結合 | ツール→オーケストレーション→UI |
| L5 重み | 薄い（表示確認） | **厚い**（デザイン駆動） | 薄い（管理画面確認） | 標準（結合後にVisual Refinement） | 会話UI/デモ確認 |
| G2 凍結 | API設計凍結 | Visual設計凍結 | スキーマ凍結 | 接続契約方針凍結（BE+FE+Contract三点セット） | ツール定義凍結 |
| G3 着手 | API/Schema Freeze | Component Contract Freeze | Migration Freeze | API/Schema/UI/Contract全凍結 | Tool Contract Freeze |

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

fullstack 追加条件:
- L4 は Phase A（BE Sprint ∥ FE Sprint）→ Phase B（L4.5 結合）
- L5 は常に必要（結合後の Visual Refinement）

**セキュリティゲート強制条件** → `tools/ai-coding/references/gate-policy.md §セキュリティゲート強制条件` 参照

## スキル群配置（76スキル）

パス: `skills/{カテゴリ}/{スキル名}/SKILL.md`
詳細 I/O → `orchestration-workflow.md` / 遷移条件 → `layer-interface.md`（共に `tools/ai-coding/references/`）

| カテゴリ | スキル |
|---------|--------|
| workflow/ | project-management, dev-policy, estimation, requirements-handover, compliance, design-doc, api-contract, dependency-map, quality-lv5, deploy, dev-setup, incident, observability-sre, postmortem, verification, adversarial-review, context-memory, reverse-analysis, **research**, **poc**, **gate-planning**, **schedule-wbs**, **threat-model**, **runbook**, **debt-register**, **reverse-r0**, **reverse-r1**, **reverse-r2**, **reverse-r3**, **reverse-r4**, **reverse-rgc** |
| common/ | visual-design, design, coding, refactoring, documentation, security, testing, error-fix, performance, code-review, infrastructure, git |
| project/ | ui, api, db, **fe-design**, **fe-component**, **fe-style**, **fe-a11y**, **fe-test** |
| advanced/ | tech-selection, i18n, external-api, ai-integration, migration, legacy |
| tools/ | ai-coding, ide-tools, **web-search**, **ai-search**, **mcp-wrapper-template** |
| integration/ | agent-teams |
| writing/ | japanese, explain, story, presentation, social |
| design-tools/ | diagram, web-system, pptx, graphic, character |
| automation/ | site-mapping, browser-script, flow-optimize |

**2026-04-17 追加分** (21スキル):
- workflow/: research (G1R)・poc (G1.5)・gate-planning (G0.5/G1.5)・schedule-wbs (L3)・threat-model (G2)・runbook (L6)・debt-register (G4)・reverse-r0〜r4 + reverse-rgc (R0-R4 + RGC)
- project/: fe-design・fe-component・fe-style・fe-a11y・fe-test (FE サブエージェント 5種)
- tools/: web-search (Tavily MCP)・ai-search (Perplexity MCP)・mcp-wrapper-template (MCP 統合雛型)

既存 `workflow/reverse-analysis` は各 reverse-r* へのルーターに縮小。既存 `project/ui` は FE 5種のインデックスとして残存。

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

## メンテナンス指針

1. スキル追加時: SKILL_MAP.md を更新。500行超 → references/ に分割
2. 重複防止: 追加前に既存スキルとの重複確認
3. 廃止済みスキル名: architecture / orchestrator / codex / vscode-plugins → **スキル名としての参照**禁止（ツール名 `codex review`・メタデータ `codex: true`・YAML キー `architecture:` は正当な用法）。検出: `rg -wn "orchestrator" skills/ --glob '!SKILL_MAP.md'`
4. metadata.helix_layer 必須。description は具体的用途を記載（「〇〇関連」禁止）

## 自動推挙システム（gpt-5.4-mini）

全 55 スキル + 75+ references を LLM マッチングで自動推挙する CLI を搭載。

```bash
helix skill list [--layer L2] [--category common] [--json]
helix skill show <skill-id> [--with-content]
helix skill catalog rebuild             # SKILL.md frontmatter + references 冒頭 blockquote を parse
helix skill search "<task>" [-n 5]      # Codex gpt-5.4-mini で推挙
helix skill use <id> --task "..." [--dry-run] [--agent NAME] [--references PATHS]
helix skill chain "<task>" [-n 1]       # search → use の一気通貫
helix skill stats [--days 30]           # 使用統計（skill_usage テーブル）
```

### 推挙の仕組み
- catalog: `.helix/cache/skill-catalog.json`（SKILL.md frontmatter + references 冒頭 `> 目的:` blockquote を機械抽出）
- エンジン: `gpt-5.4-mini` (`cli/roles/recommender.conf`、thinking=low)
- プロンプト: `cli/templates/skill-search-prompt.md`（9種の agent 決定マッピング含む）
- キャッシュ: `.helix/cache/recommendations/<sha256>.json` で 1 時間保存
- 使用履歴: `helix.db` (v5) の `skill_usage` テーブル

### 委譲の自動化
`helix skill use` は recommender が選んだ agent へ委譲する:
- `fe-design` / `fe-component` / `fe-style` / `fe-test` / `fe-a11y` はネイティブサブエージェント（`@` mention 指示）
- `tl` / `se` / `pg` / `qa` / `security` / `dba` / `devops` / `docs` / `research` / `legacy` / `perf` は Codex ロール（`helix-codex --role X --task "<bundle>\n\n<task>"` で自動実行）

### 実装ファイル
- `cli/lib/skill_catalog.py` — catalog 生成・読み込み（SKILL.md + references parser）
- `cli/lib/skill_recommender.py` — Codex 呼び出し・キャッシュ
- `cli/lib/skill_dispatcher.py` — context bundle 作成・委譲・DB 記録・stats
- `cli/helix-skill` — bash ディスパッチャ (list/show/catalog/search/use/chain/stats)
- `cli/roles/recommender.conf` — gpt-5.4-mini ロール定義
- `cli/templates/skill-search-prompt.md` — LLM プロンプトテンプレート
