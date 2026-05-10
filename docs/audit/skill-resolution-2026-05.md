# Skill Resolution Audit (2026-05-11)

## 概要

PLAN-059 W-1: 全 103 SKILL.md を 5 軸でスコアリング。
description / triggers / references / 外部参照 / HELIX キーワードを評価。

## 評価軸 (5 軸 / 各 1 点、description は 2 点)

| 軸 | 採点基準 |
|---|---|
| desc_len | ≥100 文字: 2 点 / ≥60 文字: 1 点 / それ未満: 0 点 |
| triggers | ≥2 件: 1 点 |
| references/ | ≥1 件: 1 点 |
| 外部参照 (cli/roles/template/docs/helix) | ≥1 件: 1 点 |
| HELIX keyword | helix/HELIX/phase.yaml/gate-checks/DESIGN.md/hook/harness/ADR/SKILL_MAP ≥3 出現: 1 点 |

## カテゴリ別件数

- **Low (score ≤2)**: 63 件 (61%) - brush up 推奨
- **Medium (score 3-4)**: 38 件 (37%) - 標準
- **High (score ≥5)**: 2 件 (2%) - 模範

## brush up 優先候補 (score ≤2 のうち高重要度)

外部参照 (ext) が多いのに低解像度な skill = 重要だが説明不足、優先 brush up:

| skill | score (before/after) | desc_len (before/after) | trg | ref | ext | kw (before/after) |
|---|---|---|---|---|---|---|
| `common/testing` | 2→4 | 45→175 | 3 | 0 | 9 | 1→6 |
| `common/coding` | 2→4 | 34→158 | 3 | 0 | 8 | 0→3 |
| `workflow/reverse-analysis` | 2→4 | 18→226 | 5 | 0 | 6 | 1→5 (Reverse) |
| `workflow/design-doc` | 2→4 | 29→151 | 3 | 0 | 5 | 1→11 |
| `workflow/incident` | 2→4 | 28→147 | 3 | 0 | 5 | 0→7 |
| `project/db` | 2→4 | 47→134 | 3 | 0 | 4 | 1→5 |
| `workflow/deploy` | 2→4 | 42→139 | 3 | 0 | 4 | 1→6 |
| `workflow/postmortem` | 2→4 | 35→154 | 4 | 0 | 4 | 0→6 |
| `common/code-review` | 2→4 | 50→147 | 3 | 0 | 3 | 1→4 |
| `advanced/migration` | 2→4 | 49→137 | 3 | 0 | 3 | 1→4 |
| `common/error-fix` | 2→4 | 36→124 | 3 | 0 | 3 | 2→4 |

**W-2 brush up 結果**:
- 全 11 件 score 2 → 4 (desc_len +2 / kw +1) - HELIX 統合キーワード明示で監査盲点解消
- desc_len 中央値: 36 → 147 (+311%)
- HELIX kw 平均: 1.0 → 5.5 (+450%)
- Low 解像度件数: 63 → 52 (-11、約 17% 改善)

## 全 SKILL 評価表

| skill | score | desc_len | trg | ref/ | ext | kw | desc (先頭 80 字) |
|---|---|---|---|---|---|---|---|
| `automation/browser-script` | 1 | 59 | 3 | 0 | 0 | 1 | Playwright codegenによるブラウザ操作記録からE2Eテスト雛形を自動生成し、L6統合検証の効率化を支援... |
| `automation/flow-optimize` | 1 | 56 | 3 | 0 | 0 | 1 | サイトマップとPlaywright操作記録からユーザーフローを分析し、ステップ数削減・導線改善の具体的提案を行う... |
| `automation/site-mapping` | 1 | 56 | 3 | 0 | 0 | 1 | Crawl4AIとFirecrawlの使い分けでサイト構造抽出・Reverse証拠収集・構造化データ抽出を自動化... |
| `writing/japanese` | 1 | 56 | 3 | 0 | 0 | 1 | textlint統合による日本語技術文書の品質自動チェック・AI生成文の不自然さ検出・JTF表記ルール準拠を提供... |
| `design-tools/graphic` | 1 | 54 | 3 | 0 | 0 | 0 | Vercel Satori等によるSVG/OGP画像の動的生成でブログ・リリースのアイキャッチ画像を自動作成... |
| `design-tools/character` | 1 | 52 | 4 | 0 | 0 | 1 | AI画像生成プロンプト設計とスタイルガイド策定でキャラクター・マスコット・アバターのデザイン方針を構造化... |
| `tools/ai-search` | 1 | 50 | 4 | 0 | 0 | 0 | Haiku 4.5 リサーチロールへ委譲する AI 調査スキル。仮説生成・長尺調査要約・多ソース統合... |
| `workflow/estimation` | 1 | 36 | 3 | 0 | 0 | 2 | 三点見積もりとリスク係数を用いた工数・スプリント計画の見積もり手順を提供... |
| `workflow/dev-policy` | 1 | 34 | 3 | 0 | 0 | 0 | 開発方針と品質基準を決めるための完成の定義とチームルールの雛形を提供... |
| `common/testing` | 2 | 45 | 3 | 0 | 9 | 1 | テスト戦略策定でユニット/統合/E2Eテストのテンプレートとカバレッジ目標の検証手順を提供... |
| `common/coding` | 2 | 34 | 3 | 0 | 8 | 0 | コード品質改善(命名・構造・型安全性)のチェック観点と改善手順を提供... |
| `workflow/reverse-analysis` | 2 | 18 | 5 | 0 | 6 | 1 | Reverse フロー全体のルーター... |
| `workflow/design-doc` | 2 | 29 | 3 | 0 | 5 | 1 | 基本設計・詳細設計の設計書テンプレートとレビュー基準を提供... |
| `workflow/incident` | 2 | 28 | 3 | 0 | 5 | 0 | 障害対応での重要度判定・対応手順・連絡テンプレートを提供... |
| `project/db` | 2 | 47 | 3 | 0 | 4 | 1 | データベース設計でスキーマテンプレート・インデックス設計ルール・マイグレーション安全手順を提供... |
| `workflow/deploy` | 2 | 42 | 3 | 0 | 4 | 1 | デプロイ・リリース・ロールバックのBlue/Green戦略と実行チェックリストを提供... |
| `workflow/postmortem` | 2 | 35 | 4 | 0 | 4 | 0 | 障害分析と再発防止アクションをまとめるポストモーテムテンプレートを提供... |
| `common/code-review` | 2 | 50 | 3 | 0 | 3 | 1 | コードレビューでセキュリティ・パフォーマンス・設計の観点チェックリストと建設的フィードバック例を提供... |
| `advanced/migration` | 2 | 49 | 3 | 0 | 3 | 1 | システム移行でETLスクリプト・データ検証手順・Strangler Figパターンの実装手順を提供... |
| `common/error-fix` | 2 | 36 | 3 | 0 | 3 | 2 | エラー修正で原因特定フロー・デバッグ手順・再現テストと修正パターンを提供... |
| `advanced/legacy` | 2 | 50 | 3 | 0 | 2 | 1 | レガシーコード改修で特性テスト・Strangler Figパターン・段階的リファクタリング手順を提供... |
| `common/git` | 2 | 42 | 3 | 0 | 2 | 2 | Git運用でブランチ命名規則・コミットメッセージフォーマット・PRテンプレートを提供... |
| `workflow/requirements-handover` | 2 | 34 | 4 | 0 | 2 | 1 | 要件曖昧時や引継ぎ時の確認質問・仮定管理・引継ぎチェックリストを提供... |
| `workflow/compliance` | 2 | 18 | 4 | 0 | 2 | 0 | 法令遵守・ライセンス・規制対応を提供... |
| `workflow/reverse-r2` | 2 | 59 | 3 | 0 | 1 | 2 | HELIX Reverse R2 As-Is Design 復元スキル。観測契約から内部構造を再構成 + ADR 推定... |
| `writing/explain` | 2 | 49 | 3 | 0 | 1 | 1 | 技術文書の説明品質を「概要・使い方・例・制約」の4部構成で構造化し、読者視点のチェックリストを提供... |
| `automation/init-setup` | 2 | 45 | 3 | 0 | 1 | 2 | HELIX automation の初期化検証、導入、修復、DB 追跡を扱う setup。... |
| `common/design` | 2 | 38 | 3 | 0 | 1 | 0 | UI/UXとコンポーネント設計で、日本市場向けのデザイン原則とUI指針を提供... |
| `workflow/project-management` | 2 | 38 | 3 | 0 | 1 | 2 | ダッシュボードとカンバンテンプレートを用いた計画・進捗・報告の運用手順を提供... |
| `workflow/dev-setup` | 2 | 36 | 3 | 0 | 1 | 1 | OS別セットアップとVSCode設定の手順を含む開発環境構築ガイドを提供... |
| `workflow/dependency-map` | 2 | 33 | 4 | 0 | 1 | 0 | 依存関係マップの作成と脆弱性・ライセンス・循環依存の検証観点を提供... |
| `agent-skills/browser-testing-with-devtools` | 2 | 268 | 0 | 0 | 0 | 1 | Tests in real browsers. Use when building or debugging anything that runs in a b... |
| `agent-skills/api-and-interface-design` | 2 | 251 | 0 | 0 | 0 | 0 | Guides stable API and interface design. Use when designing APIs, module boundari... |
| `agent-skills/debugging-and-error-recovery` | 2 | 249 | 0 | 0 | 0 | 0 | Guides systematic root-cause debugging. Use when tests fail, builds break, behav... |
| `agent-skills/security-and-hardening` | 2 | 245 | 0 | 0 | 0 | 1 | Hardens code against vulnerabilities. Use when handling user input, authenticati... |
| `agent-skills/frontend-ui-engineering` | 2 | 240 | 0 | 0 | 0 | 1 | Builds production-quality UIs. Use when building or modifying user-facing interf... |
| `agent-skills/code-review-and-quality` | 2 | 237 | 0 | 0 | 0 | 0 | Conducts multi-axis code review. Use before merging any change. Use when reviewi... |
| `agent-skills/planning-and-task-breakdown` | 2 | 237 | 0 | 0 | 0 | 0 | Breaks work into ordered tasks. Use when you have a spec or clear requirements a... |
| `agent-skills/test-driven-development` | 2 | 231 | 0 | 0 | 0 | 0 | Drives development with tests. Use when implementing any logic, fixing any bug, ... |
| `agent-skills/performance-optimization` | 2 | 230 | 0 | 0 | 0 | 0 | Optimizes application performance. Use when performance requirements exist, when... |
| `agent-skills/documentation-and-adrs` | 2 | 224 | 0 | 0 | 0 | 1 | Records decisions and documentation. Use when making architectural decisions, ch... |
| `agent-skills/incremental-implementation` | 2 | 221 | 0 | 0 | 0 | 0 | Delivers changes incrementally. Use when implementing any feature or change that... |
| `agent-skills/source-driven-development` | 2 | 219 | 0 | 0 | 0 | 1 | Grounds every implementation decision in official documentation. Use when you wa... |
| `agent-skills/using-agent-skills` | 2 | 218 | 0 | 0 | 0 | 0 | Discovers and invokes agent skills. Use when starting a session or when you need... |
| `agent-skills/shipping-and-launch` | 2 | 213 | 0 | 0 | 0 | 0 | Prepares production launches. Use when preparing to deploy to production. Use wh... |
| `agent-skills/deprecation-and-migration` | 2 | 208 | 0 | 0 | 0 | 0 | Manages deprecation and migration. Use when removing old systems, APIs, or featu... |
| `agent-skills/ci-cd-and-automation` | 2 | 207 | 0 | 0 | 0 | 0 | Automates CI/CD pipeline setup. Use when setting up or modifying build and deplo... |
| `agent-skills/spec-driven-development` | 2 | 202 | 0 | 0 | 0 | 0 | Creates specs before coding. Use when starting a new project, feature, or signif... |
| `agent-skills/context-engineering` | 2 | 198 | 0 | 0 | 0 | 1 | Optimizes agent context setup. Use when starting a new session, when agent outpu... |
| `agent-skills/technical-writing` | 2 | 147 | 0 | 0 | 0 | 2 | Google Technical Writing の原則 (短い文・能動態・用語一貫性・読み手設定・箇条書き・段落構成) を適用し、設計書・API ドキュメント... |
| `agent-skills/idea-refine` | 2 | 135 | 0 | 0 | 0 | 0 | Refines ideas iteratively. Refine ideas through structured divergent and converg... |
| `agent-skills/system-design-sizing` | 2 | 100 | 0 | 0 | 0 | 2 | システム設計の規模・スケーラビリティを見積もり、容量計画・ボトルネック特定・トレードオフ分析を行う。新規システム設計時や既存システムのスケール判断時、性能/可用... |
| `workflow/reverse-rgc` | 2 | 80 | 3 | 0 | 0 | 2 | Reverse Gap Closure スキル。Forward HELIX の L6/L8 pass 後に Reverse で特定した gap が閉塞したか検証... |
| `writing/social` | 2 | 65 | 3 | 0 | 0 | 1 | リリースノート・技術ブログからX(Twitter)/LinkedIn/Bluesky向けSNS投稿案を自動生成し、技術広報を効率化... |
| `writing/presentation` | 2 | 61 | 3 | 0 | 0 | 1 | Marp CLIによるMarkdownからPPTX/PDFスライド自動生成で、レトロ・レビュー・報告のスライド作成を効率化... |
| `design-tools/diagram` | 2 | 60 | 4 | 0 | 0 | 1 | Mermaid/D2によるテキストベース図表生成で設計書のフローチャート・シーケンス図・ER図・アーキテクチャ図を自動化... |
| `design-tools/pptx` | 2 | 60 | 3 | 0 | 0 | 1 | python-pptxによるテンプレートベースPPTX自動生成で定型報告書・提案書・進捗報告のスライドをデータ駆動で作成... |
| `workflow/gate-planning` | 2 | 57 | 5 | 1 | 0 | 1 | G0.5/G1.5 企画突合・PoC ゲート専用スキル。企画書との突合 + 技術スタック選定 + PoC 結果集約... |
| `integration/agent-teams` | 2 | 55 | 3 | 1 | 0 | 2 | 複数エージェント協調の運用手順・役割設計・チーム構成パターン・ビジュアルワークフロー設計・コスト管理指針を提供... |
| `advanced/ai-integration` | 2 | 52 | 3 | 1 | 0 | 2 | LLM組み込み・RAG・エージェント設計で、ルーティング・ベクトル検索・コンテキスト管理の実装指針を提供... |
| `tools/ide-tools` | 2 | 36 | 3 | 2 | 0 | 1 | IDE・AIツール選定とMCP設定の比較検討手順とセットアップ手順を提供... |
| `workflow/runbook` | 2 | 36 | 4 | 1 | 0 | 0 | L6 Runbook (運用準備書) 生成スキル。G6 RC判定通過条件... |
| `workflow/debt-register` | 2 | 20 | 4 | 1 | 0 | 0 | G4 通過条件の負債台帳生成・更新スキル... |
| `common/security` | 3 | 21 | 3 | 5 | 8 | 0 | 脆弱性対策・OWASP・秘密情報管理を提供... |
| `workflow/observability-sre` | 3 | 50 | 4 | 1 | 6 | 1 | SLO/SLI設計・アラート戦略・ダッシュボード構築に加え、リアルタイム監視設計の可観測性指針を提供... |
| `workflow/api-contract` | 3 | 99 | 3 | 0 | 5 | 1 | APIコントラクト定義（D-API/D-CONTRACT）とスキーマ・レスポンス・エラー整合の検証チェックリストを提供（G3 契約凍結後の整合検証に使用。設計段... |
| `common/refactoring` | 3 | 35 | 4 | 0 | 5 | 3 | コード構造改善で責務分離パターン・共通化判断基準・デグレ対策手順を提供... |
| `workflow/adversarial-review` | 3 | 55 | 3 | 0 | 4 | 4 | 設計批判レビュー手法 (G2 固有) — 脅威モデル作成は workflow/threat-model に委譲... |
| `workflow/poc` | 3 | 50 | 4 | 1 | 4 | 1 | G1.5 PoC ゲート専用。kill criteria を伴う最小検証を行い実装着手可否を判定する... |
| `common/infrastructure` | 3 | 45 | 3 | 1 | 4 | 1 | Docker・PostgreSQL・Redis・Nginxの本番構成と安全設定の指針を提供... |
| `project/api` | 3 | 98 | 3 | 0 | 3 | 0 | RESTful/GraphQL API設計でエンドポイント規約・レスポンス形式テンプレート・認証認可パターンを提供（L2-L3 設計時に参照。契約凍結後の検証は... |
| `workflow/quality-lv5` | 3 | 42 | 3 | 1 | 3 | 0 | テスト品質をLv1-5で評価し、テストピラミッド比率とカバレッジ目標の検証手順を提供... |
| `workflow/reverse-r0` | 3 | 80 | 3 | 0 | 2 | 2 | HELIX Reverse R0 証拠収集スキル。code/DB/config/ops の4軸で evidence_map を作成し RG0 通過可否を判定する... |
| `workflow/reverse-r1` | 3 | 80 | 4 | 0 | 2 | 2 | HELIX Reverse R1 Observed Contracts 抽出スキル。API・DB・型の機械抽出 + characterization tests... |
| `project/ui` | 3 | 60 | 3 | 0 | 2 | 1 | FE 設計知識群のインデックス。タスク内容に応じて情報設計・コンポーネント・スタイル・a11y・テストの各知識へ接続する... |
| `workflow/research` | 3 | 57 | 4 | 1 | 2 | 0 | G1R 事前調査ゲートで発火する調査スキル。一次情報収集から research_report 作成までを標準化する... |
| `workflow/schedule-wbs` | 3 | 57 | 4 | 1 | 2 | 2 | L3 工程表 (WBS + feature flag + rollback) 生成スキル。G3 通過条件を直接充足... |
| `advanced/i18n` | 3 | 50 | 3 | 1 | 2 | 0 | 多言語対応で、Next.js/FastAPIのi18n実装パターンとIntl APIの適用方法を提供... |
| `common/documentation` | 3 | 50 | 3 | 1 | 2 | 2 | 技術ドキュメント作成でREADME/API仕様書/ADRのテンプレートと品質確認チェックリストを提供... |
| `agent-skills/helix-scrum` | 3 | 171 | 0 | 0 | 1 | 2 | 要件未確定・実現可能性不明の案件で仮説検証駆動で開発を進める。S0 (Backlog) → S1 (Sprint Plan) → S2 (PoC) → S3 (... |
| `workflow/reverse-r3` | 3 | 78 | 4 | 0 | 1 | 1 | HELIX Reverse R3 Intent Hypotheses スキル。要件仮説生成 + PO 検証 + Session Hypothesis Log... |
| `workflow/reverse-r4` | 3 | 77 | 3 | 0 | 1 | 2 | HELIX Reverse R4 Gap & Routing スキル。R3 Intent と As-Is の差分を Forward HELIX に振り分け... |
| `automation/lock` | 3 | 71 | 3 | 0 | 1 | 2 | HELIX の single-host file lock + DB metadata lock を管理する automation lock。... |
| `automation/scheduler` | 3 | 71 | 3 | 0 | 1 | 2 | HELIX の cron-like 定期実行、単発 at 実行、期限到達 task 実行を管理する automation scheduler。... |
| `automation/observability` | 3 | 67 | 3 | 0 | 1 | 2 | HELIX automation の events と metrics を記録・集計・export する observability。... |
| `tools/web-search` | 3 | 62 | 6 | 0 | 1 | 0 | ビルトイン WebSearch + WebFetch を使った Web 調査スキル。一次情報収集・ドキュメント確認・競合調査... |
| `automation/job-queue` | 3 | 61 | 3 | 0 | 1 | 2 | HELIX の非同期ジョブ登録、worker、retry、list を管理する automation job-queue。... |
| `design-tools/web-system` | 3 | 54 | 3 | 3 | 1 | 1 | shadcn/uiベースのデザインシステム構築でコンポーネント選定・テーマ設定・トークン管理の標準手順を提供... |
| `advanced/tech-selection` | 3 | 48 | 3 | 4 | 1 | 1 | 技術選定で評価マトリクス・SWOT分析フレームワーク・ADRテンプレートと選定プロセス手順を提供... |
| `advanced/external-api` | 3 | 45 | 3 | 1 | 1 | 1 | 外部API連携で、アダプターパターン・リトライ・サーキットブレーカーによる堅牢化設計を提供... |
| `agent-skills/mock-driven-development` | 3 | 216 | 0 | 0 | 0 | 3 | FE 駆動 (fe/fullstack) の L2 設計でモックを起点にユーザー体験を固め、TL が state-events.md から API 契約を導出す... |
| `project/fe-component` | 3 | 99 | 4 | 1 | 0 | 0 | FE コンポーネント実装スキル。Atomic Design に基づくコンポーネントツリー設計と TypeScript Props 型定義を行い、project/... |
| `project/fe-design` | 3 | 90 | 7 | 3 | 0 | 0 | FE 情報アーキテクチャ (D-IA) 設計スキル。ページマップ・ナビゲーション階層・ラベル定義を行い、visual-design §①information ... |
| `workflow/verification` | 4 | 96 | 6 | 1 | 6 | 2 | L1〜V-L6の各検証レイヤーに加え、Spec駆動検証とL8仕様突合チェックを提供（V-L3〜V-L6は本スキル固有番号）。Reverse モード（RG0-RG... |
| `common/performance` | 4 | 61 | 3 | 5 | 4 | 0 | パフォーマンス最適化でCore Web Vitals目標値・ボトルネック診断フローチャート・計測手順とチェックリストを提供... |
| `workflow/threat-model` | 4 | 60 | 4 | 1 | 2 | 0 | G2 通過条件の脅威モデル書生成スキル。STRIDE/DREAD テンプレート + common/security 連携... |
| `integration/agent-design` | 4 | 91 | 5 | 11 | 1 | 1 | LLM駆動 task / agent の設計判断を、判断詰まり時に開く HELIX 対応詳細参照マップ。要素・フレーム・骨格・前段・後段を軸に、LLM 出力の構... |
| `workflow/context-memory` | 4 | 38 | 4 | 2 | 1 | 5 | CLAUDE.md運用を含むAIコンテキスト管理・知識永続化の運用手順を提供... |
| `project/fe-a11y` | 4 | 124 | 4 | 1 | 0 | 0 | FE アクセシビリティスキル。axe-core 検証と WCAG 2.1 AA 準拠チェックリストを提供し、visual-design の accessibil... |
| `project/fe-style` | 4 | 117 | 4 | 1 | 0 | 0 | FE スタイル実装スキル。デザイントークン 3 層定義 (primitive/semantic/component) と CSS/Tailwind の実装方針を... |
| `project/fe-test` | 4 | 111 | 4 | 1 | 0 | 1 | FE テストスキル。Storybook / Playwright E2E / VRT (Visual Regression Test) の設計と実装を担い、co... |
| `tools/ai-coding` | 5 | 69 | 2 | 16 | 13 | 3 | AIツール活用で構造化プロンプトテンプレート・マルチエージェント戦略・CI/CDエージェント統合パターン・出力レビューチェックリストを提供... |
| `common/visual-design` | 5 | 126 | 5 | 10 | 2 | 1 | ビジュアルデザイン基礎（構図・レイアウト・配色・タイポグラフィ・余白・視線誘導）に基づいてSNS画像、Web UI、資料、プレゼンテーションのデザイン判断を支援... |

## 推奨アクション

### Sprint W-2 (brush up): 高重要度 + 低解像度 (ext≥3 & score≤2)
対象: 約 11 件
対応: description を 80 文字以上に充実、HELIX 統合キーワードを 3 つ以上含める、必要なら references/ 追加

### Sprint W-3 (低使用度の見直し): ext=0 & score≤2
対象: 約 41 件
対応: HELIX 内での使用経路を再検証、不要なら PLAN-060 W-2 と同じく廃止検討

## メタデータ

- 監査日: 2026-05-11
- 評価者: Opus 4.7 (python script ベース機械評価)
- 対象: 103 SKILL
- Low: 63 / Medium: 38 / High: 2
