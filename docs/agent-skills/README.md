# HELIX Agent Skills

**HELIX 開発フレームワーク向けのプロダクション品質エンジニアリングスキル集**

MIT ライセンス。Upstream: addyosmani/agent-skills (MIT)

スキルは、シニアエンジニアが実践する開発ワークフロー、品質ゲート、ベストプラクティスを定義します。これらをパッケージ化することで、AI エージェントが開発の各フェーズで一貫して同じ規律に従えるようにします。

```
  DEFINE          PLAN           BUILD          VERIFY         REVIEW          SHIP
 ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐
 │ Idea │ ───▶ │ Spec │ ───▶ │ Code │ ───▶ │ Test │ ───▶ │  QA  │ ───▶ │  Go  │
 │Refine│      │  PRD │      │ Impl │      │Debug │      │ Gate │      │ Live │
 └──────┘      └──────┘      └──────┘      └──────┘      └──────┘      └──────┘
  /spec          /plan          /build        /test         /review       /ship
```

---

## Commands

開発ライフサイクルに対応する 7 つの slash command です。各コマンドが適切なスキルを自動で有効化します。

| 作業内容 | コマンド | 原則 | HELIX フェーズ |
|----------|---------|------|---------------|
| 仕様を定める | `/spec` | Spec before code | L1 要件定義 |
| 計画を立てる | `/plan` | Small, atomic tasks | L3 詳細設計 |
| 実装 | `/build` | One slice at a time | L4 マイクロスプリント |
| テスト | `/test` | Tests are proof | L4.3 / L6 |
| レビュー | `/review` | Improve code health | G4 実装凍結 |
| 簡素化 | `/code-simplify` | Clarity over cleverness | L6 |
| 出荷 | `/ship` | Faster is safer | L7 デプロイ |

実行内容に応じた自動発火にも対応しています。たとえば API 設計では `api-and-interface-design`、UI 実装では `frontend-ui-engineering` が有効化されます。

---

## Quick Start

<details>
<summary><b>Claude Code (recommended)</b></summary>

**Marketplace install:**

```
/plugin marketplace add <YOUR_GITHUB_USER>/helix-agent-skills
/plugin install helix-agent-skills@<YOUR_GITHUB_USER>-helix-agent-skills
```

> **SSH errors?** Marketplace は SSH 経由でリポジトリを clone します。GitHub に SSH キーを設定していない場合は、[SSH キーを追加](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)するか、取得時のみ HTTPS を使う設定に切り替えてください。
> ```bash
> git config --global url."https://github.com/".insteadOf "git@github.com:"
> ```

**ローカル / 開発用:**

```bash
git clone https://github.com/addyosmani/agent-skills.git
claude --plugin-dir /path/to/agent-skills
```

</details>

<details>
<summary><b>Cursor</b></summary>

任意の `SKILL.md` を `.cursor/rules/` にコピーするか、`skills/` ディレクトリ全体を参照してください。詳細は [docs/cursor-setup.md](docs/cursor-setup.md) を参照。

</details>

<details>
<summary><b>Gemini CLI</b></summary>

ネイティブスキルとしてインストールすると自動検出されます。永続コンテキストとして扱う場合は `GEMINI.md` に追加してください。詳細は [docs/gemini-cli-setup.md](docs/gemini-cli-setup.md) を参照。

**リポジトリからインストール:**

```bash
gemini skills install https://github.com/addyosmani/agent-skills.git --path skills
```

**ローカル clone からインストール:**

```bash
gemini skills install ./agent-skills/skills/
```

</details>

<details>
<summary><b>Windsurf</b></summary>

スキル内容を Windsurf の rules 設定へ追加してください。詳細は [docs/windsurf-setup.md](docs/windsurf-setup.md) を参照。

</details>

<details>
<summary><b>OpenCode</b></summary>

AGENTS.md と `skill` ツールを使った、エージェント駆動のスキル実行モデルです。

詳細は [docs/opencode-setup.md](docs/opencode-setup.md) を参照。

</details>

<details>
<summary><b>GitHub Copilot</b></summary>

`agents/` の定義を Copilot の persona として利用し、`.github/copilot-instructions.md` にスキル内容を反映できます。詳細は [docs/copilot-setup.md](docs/copilot-setup.md) を参照。

</details>

<details>
  <summary><b>Kiro IDE & CLI</b></summary>
  Kiro 向けスキルは `.kiro/skills/` 配下に配置します（Project / Global 両レベル対応）。Kiro は Agents.md もサポートします。詳細は https://kiro.dev/docs/skills/ を参照。
</details>

<details>
<summary><b>Codex / Other Agents</b></summary>

スキルはプレーンな Markdown です。system prompt や instruction file を扱える任意のエージェントで利用できます。詳細は [docs/getting-started.md](docs/getting-started.md) を参照。

</details>

---

## 全 28 スキル (上流 20 + メタ 1 + HELIX 独自 7)

上記コマンドはエントリーポイントです。内部では 20 のコアスキル + 1 つのメタスキルに加え、HELIX 独自の **7 スキル** が連携し、手順・検証ゲート・アンチ合理化ルールを実行します。各スキルは直接参照して使うこともできます。

HELIX 独自スキル (7 本):
- `system-design-sizing` / `technical-writing` (外部根拠ベース)
- `adversarial-review` / `debt-register` / `mock-driven-development` / `helix-scrum` / `reverse-helix` (HELIX 本体由来)

### Define (L1 要件定義) — 何を作るか明確化

| Skill | What It Does | Use When |
|-------|--------------|----------|
| [idea-refine](skills/idea-refine/SKILL.md) | 発散と収束の構造化思考で、曖昧なアイデアを具体的な提案に変換する | 粗いコンセプトを探索・具体化したいとき |
| [spec-driven-development](skills/spec-driven-development/SKILL.md) | 実装前に、目的・コマンド・構成・コード規約・テスト・境界条件を含む PRD を作成する | 新規プロジェクト、機能追加、大きな変更を始めるとき |

### Plan (L2-L3 設計) — 実行可能な単位に分解

| Skill | What It Does | Use When |
|-------|--------------|----------|
| [planning-and-task-breakdown](skills/planning-and-task-breakdown/SKILL.md) | 仕様を受入条件付きの小さな検証可能タスクへ分解し、依存順序を整理する | 仕様はあるが、実装可能な作業単位に落とし込みたいとき |

### Build (L4 実装) — コードを書く

| Skill | What It Does | Use When |
|-------|--------------|----------|
| [incremental-implementation](skills/incremental-implementation/SKILL.md) | 薄い縦スライスで「実装→テスト→検証→コミット」を回す。feature flag、安全な既定値、ロールバック容易性を重視する | 2 ファイル以上にまたがる変更を行うとき |
| [test-driven-development](skills/test-driven-development/SKILL.md) | Red-Green-Refactor、テストピラミッド (80/15/5)、テストサイズ、DAMP over DRY、Beyonce Rule、ブラウザテストを適用する | ロジック実装、バグ修正、挙動変更を行うとき |
| [context-engineering](skills/context-engineering/SKILL.md) | ルールファイル、コンテキストパッキング、MCP 連携で、必要な情報を必要なタイミングでエージェントに与える | セッション開始時、作業切替時、出力品質が落ちたとき |
| [source-driven-development](skills/source-driven-development/SKILL.md) | フレームワーク判断を公式ドキュメントに基づいて検証・引用し、未検証事項を明示する | 権威ある一次情報に基づいた実装をしたいとき |
| [frontend-ui-engineering](skills/frontend-ui-engineering/SKILL.md) | コンポーネント設計、デザインシステム、状態管理、レスポンシブ設計、WCAG 2.1 AA 対応を行う | ユーザー向け UI を新規作成・変更するとき |
| [api-and-interface-design](skills/api-and-interface-design/SKILL.md) | Contract-first 設計、Hyrum's Law、One-Version Rule、エラー意味論、境界バリデーションを適用する | API、モジュール境界、公開インターフェースを設計するとき |
| [system-design-sizing](skills/system-design-sizing/SKILL.md) **★HELIX 独自** | 容量計画・CAP トレードオフ・ボトルネック識別でシステム設計規模を見積もる (donnemartin/system-design-primer ベース) | 1M users / 10k QPS / 99.9% 可用性など数量要件が絡む L1-L2 設計時 |

### Verify (L6 検証) — 動作を証明

| Skill | What It Does | Use When |
|-------|--------------|----------|
| [browser-testing-with-devtools](skills/browser-testing-with-devtools/SKILL.md) | Chrome DevTools MCP を使い、DOM 検査、console、network trace、性能プロファイルを実行する | ブラウザ上で動く機能を実装・デバッグするとき |
| [debugging-and-error-recovery](skills/debugging-and-error-recovery/SKILL.md) | 5 段階トリアージ（再現・局所化・最小化・修正・再発防止）と安全なフォールバックを適用する | テスト失敗、ビルド破綻、想定外挙動が発生したとき |

### Review (G2-G6 レビュー) — マージ前の品質ゲート

| Skill | What It Does | Use When |
|-------|--------------|----------|
| [code-review-and-quality](skills/code-review-and-quality/SKILL.md) | 5 軸レビュー、変更サイズ目安（約 100 行）、重要度ラベル（Nit/Optional/FYI）、レビュー速度基準、分割方針を適用する | 変更をマージする前 |
| [code-simplification](skills/code-simplification/SKILL.md) | Chesterton's Fence と Rule of 500 に基づき、挙動を維持したまま複雑さを削減する | 動くが読みづらく保守しにくいコードを改善したいとき |
| [security-and-hardening](skills/security-and-hardening/SKILL.md) | OWASP Top 10 対策、認証パターン、秘密情報管理、依存監査、三層境界モデルを適用する | 入力処理、認証、データ保存、外部連携を扱うとき |
| [performance-optimization](skills/performance-optimization/SKILL.md) | 計測先行で Core Web Vitals 目標、プロファイリング、バンドル分析、アンチパターン検知を行う | 性能要件がある、または性能劣化が疑われるとき |

### Ship (L7 出荷) — 安全にデプロイ

| Skill | What It Does | Use When |
|-------|--------------|----------|
| [git-workflow-and-versioning](skills/git-workflow-and-versioning/SKILL.md) | Trunk-based development、atomic commit、変更サイズ目安（約 100 行）、commit-as-save-point を適用する | すべてのコード変更時（常時） |
| [ci-cd-and-automation](skills/ci-cd-and-automation/SKILL.md) | Shift Left、Faster is Safer、feature flag、品質ゲートパイプライン、失敗フィードバックループを構築する | ビルド/デプロイパイプラインを新設・変更するとき |
| [deprecation-and-migration](skills/deprecation-and-migration/SKILL.md) | Code-as-liability の観点で、必須/推奨の廃止戦略、移行パターン、zombie code 除去を行う | 旧システム削除、ユーザー移行、機能廃止を行うとき |
| [documentation-and-adrs](skills/documentation-and-adrs/SKILL.md) | ADR、API ドキュメント、インライン文書規約を整備し、設計判断の「なぜ」を記録する | アーキテクチャ判断、API 変更、機能出荷時 |
| [shipping-and-launch](skills/shipping-and-launch/SKILL.md) | リリース前チェックリスト、feature flag ライフサイクル、段階的ロールアウト、ロールバック、監視設定を実施する | 本番リリース準備を行うとき |
| [technical-writing](skills/technical-writing/SKILL.md) **★HELIX 独自** | Google Technical Writing の原則 (短文・能動態・用語一貫性・読み手設定) で設計書・API 仕様・README・SKILL.md の品質を底上げ | L2/L3/L7 の文書作成全般、PR 説明・リリースノート作成時 |

### Meta — スキル運用

| Skill | What It Does | Use When |
|-------|--------------|----------|
| [using-agent-skills](skills/using-agent-skills/SKILL.md) | スキルパック全体の使い方、起動方法、適用判断を定義する | 初回導入時や運用ルールを確認したいとき |

---

## HELIX 独自拡張

本フォークでは上流 20 スキルに加えて、HELIX フレームワーク固有の 7 スキルを追加済み:

| Skill | 役割 | Phase / Gate |
|-------|------|--------------|
| [system-design-sizing](skills/system-design-sizing/SKILL.md) | 容量計画・CAP トレードオフ・ボトルネック識別 | L1-L2 / G1.5, G2 |
| [technical-writing](skills/technical-writing/SKILL.md) | Google Tech Writing 原則で文書品質底上げ | L2/L3/L7 / G2, G4, G6 |
| [adversarial-review](skills/adversarial-review/SKILL.md) | 三者分離・Propose/Collide/Challenge/Decide で設計批判 | L2 / **G2 必須** |
| [debt-register](skills/debt-register/SKILL.md) | 技術負債台帳・G4 通過条件・Sprint .5 連携 | L4 / **G4 必須** |
| [mock-driven-development](skills/mock-driven-development/SKILL.md) | FE 駆動の L2 核心・mock.html → 契約導出 → 昇格 | L2-L4 / G2, G4, G6 |
| [helix-scrum](skills/helix-scrum/SKILL.md) | 仮説検証 S0-S4 → Forward HELIX 接続 | S0-S4 |
| [reverse-helix](skills/reverse-helix/SKILL.md) | 既存コードから設計を逆引き R0-R4 + RGC | R0-R4 / RG0-RG3 |

詳細は CLAUDE.md と docs/skill-anatomy.md を参照。

---

## Agent Personas

対象別レビューのための事前定義 persona です。

| Agent | Role | Perspective | Codex ロール |
|-------|------|-------------|-------------|
| [code-reviewer](agents/code-reviewer.md) | Senior Staff Engineer | 5 軸コードレビュー | tl |
| [test-engineer](agents/test-engineer.md) | QA Specialist | テスト戦略・カバレッジ | qa |
| [security-auditor](agents/security-auditor.md) | Security Engineer | 脆弱性検出・脅威モデリング | security |

---

## Reference Checklists

必要に応じてスキルが読み込む、クイック参照用チェックリストです。

| Reference | Covers |
|-----------|--------|
| [testing-patterns.md](references/testing-patterns.md) | テスト構成、命名、モック、React/API/E2E 例、アンチパターン |
| [security-checklist.md](references/security-checklist.md) | commit 前チェック、認証、入力検証、ヘッダー、CORS、OWASP Top 10 |
| [performance-checklist.md](references/performance-checklist.md) | Core Web Vitals 目標、フロント/バックエンドの確認項目、計測コマンド |
| [accessibility-checklist.md](references/accessibility-checklist.md) | キーボード操作、スクリーンリーダー、視覚設計、ARIA、テストツール |

---

## How Skills Work

各スキルは共通の構造（anatomy）に従います。

```
┌─────────────────────────────────────────────────┐
│  SKILL.md                                       │
│                                                 │
│  ┌─ Frontmatter ─────────────────────────────┐  │
│  │ name: lowercase-hyphen-name               │  │
│  │ description: Guides agents through [task].│  │
│  │              Use when…                    │  │
│  └───────────────────────────────────────────┘  │
│  Overview         → このスキルの目的            │
│  When to Use      → 発火条件                    │
│  Process          → 手順化されたワークフロー    │
│  Rationalizations → 言い訳と反証                │
│  Red Flags        → 問題の兆候                  │
│  Verification     → 証拠要件                    │
└─────────────────────────────────────────────────┘
```

**主要な設計方針:**

- **文章よりプロセス。** スキルは読むための解説文ではなく、エージェントが実行する手順です。各スキルはステップ、チェックポイント、終了条件を持ちます。
- **アンチ合理化。** 「後でテストを書く」などの省略言い訳に対し、反証を明文化した表を含みます。
- **検証は必須。** すべてのスキルは、テスト結果、ビルド出力、実行時データなどの証拠要件で終了します。「たぶん正しい」は不可です。
- **段階的開示。** 入口は `SKILL.md` で、補助資料は必要時のみ読み込み、トークン使用量を抑えます。

---

## Project Structure

```
agent-skills/
├── skills/                            # 28 スキル (上流 20 + メタ 1 + HELIX 独自 7)
│   ├── idea-refine/                   #   L1 要件定義
│   ├── spec-driven-development/       #   L1 要件定義
│   ├── planning-and-task-breakdown/   #   L2-L3 設計
│   ├── adversarial-review/            #   ★HELIX 独自 L2 設計批判 (G2 必須)
│   ├── mock-driven-development/       #   ★HELIX 独自 FE 駆動 L2-L4
│   ├── incremental-implementation/    #   L4 実装
│   ├── context-engineering/           #   L4 実装
│   ├── source-driven-development/     #   L4 実装
│   ├── frontend-ui-engineering/       #   L4 実装
│   ├── test-driven-development/       #   L4 実装
│   ├── api-and-interface-design/      #   L4 実装
│   ├── system-design-sizing/          #   ★HELIX 独自 L1-L2 規模見積もり
│   ├── debt-register/                 #   ★HELIX 独自 L4 負債台帳 (G4 必須)
│   ├── browser-testing-with-devtools/ #   L6 検証
│   ├── debugging-and-error-recovery/  #   L6 検証
│   ├── code-review-and-quality/       #   G2-G6 レビュー
│   ├── code-simplification/           #   G2-G6 レビュー
│   ├── security-and-hardening/        #   G2-G6 レビュー
│   ├── performance-optimization/      #   G2-G6 レビュー
│   ├── git-workflow-and-versioning/   #   L7 出荷
│   ├── ci-cd-and-automation/          #   L7 出荷
│   ├── deprecation-and-migration/     #   L7 出荷
│   ├── documentation-and-adrs/        #   L7 出荷
│   ├── shipping-and-launch/           #   L7 出荷
│   ├── technical-writing/             #   ★HELIX 独自 全フェーズ文書品質
│   ├── helix-scrum/                   #   ★HELIX 独自 S0-S4 仮説検証
│   ├── reverse-helix/                 #   ★HELIX 独自 R0-R4 + RGC 逆引き設計
│   └── using-agent-skills/            #   メタ: スキルパックの使い方
├── agents/                            # 3 つの専門 persona
├── references/                        # 4 つの補助チェックリスト
├── hooks/                             # セッションライフサイクル hooks
├── .claude/commands/                  # 7 つの slash command
└── docs/                              # ツール別セットアップガイド
```

---

## Why Agent Skills?

AI コーディングエージェントは最短経路を選びやすく、その結果として仕様定義、テスト、セキュリティレビューなど、信頼性を支える工程が省略されがちです。Agent Skills は、プロダクション品質に必要な規律をエージェントへ組み込むための構造化ワークフローを提供します。

各スキルには、現場で蓄積された実践知が埋め込まれています。*いつ*仕様を書くべきか、*何*をテストすべきか、*どう*レビューすべきか、*いつ*出荷すべきかを具体化しています。これは汎用プロンプトではなく、試作品質と本番品質を分ける、意図的で工程主導のワークフローです。

また Google のエンジニアリング文化に基づく実践も取り込んでいます。例として [Software Engineering at Google](https://abseil.io/resources/swe-book) と Google の [engineering practices guide](https://google.github.io/eng-practices/) の考え方を反映しています。API 設計の Hyrum's Law、テストの Beyonce Rule とテストピラミッド、レビューの変更サイズと速度基準、簡素化の Chesterton's Fence、Git 運用の trunk-based development、CI/CD の Shift Left と feature flag、さらにコードを負債として扱う deprecation スキルまで、原則を手順として実装済みです。

---

## Contributing

スキルは **具体的**（曖昧な助言ではなく実行手順）、**検証可能**（証拠付きの終了条件）、**実戦的**（実運用で検証済み）、**最小限**（必要な情報に絞る）であるべきです。

形式仕様は [docs/skill-anatomy.md](docs/skill-anatomy.md)、投稿ガイドラインは [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

---

## License

MIT - このスキルはプロジェクト、チーム、各種ツールで利用できます。
