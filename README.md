# ai-dev-kit-vscode

Claude Code / Codex CLI 向けの HELIX スキルフレームワーク。
`~/.claude/CLAUDE.md` に 1 行追加するだけで、40 のスキルが全プロジェクトで使えるようになる。

## セットアップ

```bash
# 1. クローン
git clone https://github.com/RetryYN/ai-dev-kit-vscode.git ~/ai-dev-kit-vscode

# 2. グローバル CLAUDE.md を作成
mkdir -p ~/.claude
cat > ~/.claude/CLAUDE.md << 'EOF'
# Global Settings

@~/ai-dev-kit-vscode/skills/SKILL_MAP.md

## HELIX スキル利用ルール

- スキルは `~/ai-dev-kit-vscode/skills/` に配置
- SKILL_MAP.md（上記 @import）でスキル一覧を把握する
- タスクに該当するスキルがあれば、そのスキルの SKILL.md を Read してから作業する
- スキルの triggers に該当する作業を検出したら、自発的にスキルを読み込む
- 全スキルを一度に読み込まない（コンテキスト節約）
EOF
```

これで次回の Claude Code セッションから有効になる。

## しくみ

```
~/.claude/CLAUDE.md          ← 全プロジェクト共通（User レベル）
  └── @import SKILL_MAP.md   ← 40 スキルの一覧（常時読み込み、~120行）
        └── 各 SKILL.md      ← タスクに応じてオンデマンド Read
```

- `~/.claude/CLAUDE.md` は Claude Code が**毎セッション自動で読み込む**
- `@import` で SKILL_MAP.md を取り込み、Claude にスキル一覧を認識させる
- 個々のスキルは triggers に該当したとき Claude が自発的に Read する
- 全スキル一括読み込みはしない（コンテキストウィンドウ節約）

## プロジェクトでの使い方

### 1. セッション開始時（毎回自動）

Claude Code がセッション開始時に以下の軽量チェックを**必ず実行**する（スキップ不可）：

```
✅ ./CLAUDE.md または ./.claude/CLAUDE.md の存在確認
✅ .gitignore に CLAUDE.local.md / .claude/settings.local.json が含まれているか
→ 問題なければ「OK: 初期化チェック完了」で終了
```

### 2. CLAUDE.md がない場合 → 新規作成

```
context-memory スキルの §1.3 テンプレートで新規作成を提案する。
既存コードがある場合（引継ぎ等）は、コードベースを分析して内容を補完する。
作成はユーザー承認後に実行。
```

### 3. CLAUDE.md がある場合（初回 or 更新時）→ テンプレート照合

```
§1.3 テンプレートの全項目と照合し、過不足を一覧で報告する。
（毎セッションではなく、初回アクセス時または CLAUDE.md 更新検出時のみ）
修正はユーザー承認後に実行。
```

### 4. 開発中

- スキルは triggers に該当すると Claude が自発的に読み込む（手動不要）
- デバッグ知見や設計判断は auto memory（`~/.claude/projects/` 配下）に自動蓄積される
- 個人設定は `CLAUDE.local.md` に分離する（git に含めない）

### 5. プロジェクト終了・クリーンアップ

```
残すもの（git管理）:
  CLAUDE.md              ← プロジェクト知識（次の人が使う）
  .claude/settings.json  ← チーム共有パーミッション
  .claude/rules/*.md     ← チームルール

消してよいもの（個人）:
  CLAUDE.local.md              ← 個人設定
  .claude/settings.local.json  ← 個人パーミッション
```

グローバル設定（`~/.claude/CLAUDE.md`、`~/ai-dev-kit-vscode/`）はプロジェクトを消しても残る。

## スキル一覧（40 スキル）

### L1: 要件定義

| スキル | 説明 |
|--------|------|
| project-management | プロジェクト計画・進捗管理 |
| dev-policy | 開発方針策定 |
| estimation | 見積もり |
| tech-selection | 技術選定 |
| requirements-handover | 要件未定義・引継ぎ |
| compliance | コンプライアンス・規制対応 |

### L2: 全体設計

| スキル | 説明 |
|--------|------|
| design-doc | 設計書作成 |
| design | UI/UXデザイン |
| ui | UI設計 |
| db | DB設計 |
| coding | コーディング規約 |
| refactoring | リファクタリング |
| documentation | ドキュメント作成 |
| security | セキュリティ |
| i18n | 多言語対応 |

### L3: 詳細設計 + API契約 + テスト設計 + 工程表

| スキル | 説明 |
|--------|------|
| api-contract | APIコントラクト検証 |
| api | API設計 |
| external-api | 外部API連携 |
| ai-integration | AI統合 |
| dependency-map | 依存関係検証 |
| migration | システム移行 |
| legacy | レガシーコード対応 |

### L4: 実装（マイクロスプリント）

| スキル | 説明 |
|--------|------|
| testing | テスト作成 |
| quality-lv5 | テスト品質検証 |
| error-fix | エラー修正 |
| performance | パフォーマンス |
| code-review | コードレビュー |

### L5: Visual Refinement

| スキル | 説明 |
|--------|------|
| visual-design | ビジュアルデザイン |

### L6: 統合検証

| スキル | 説明 |
|--------|------|
| verification | L1-L8検証 |

### L7: デプロイ

| スキル | 説明 |
|--------|------|
| infrastructure | インフラ構築 |
| deploy | デプロイ・リリース |
| dev-setup | 開発環境構築 |
| observability-sre | 監視・可観測性・SRE |

### L8: 受入 / 横断

| スキル | 説明 |
|--------|------|
| incident | 障害対応 |
| postmortem | インシデント振り返り |
| git | Git運用 |
| adversarial-review | AI対立的レビュー |
| context-memory | AIコンテキスト・メモリ管理 |
| ai-coding | AIコーディング |
| agent-teams | Agent Teams 協調設計・レビュー |
| ide-tools | IDE/AIツール・MCP |

## ディレクトリ構造

```
skills/
├── SKILL_MAP.md              ← エントリポイント（@import 対象）
├── common/                   ← 汎用スキル（11）
│   ├── coding/SKILL.md
│   ├── testing/SKILL.md
│   └── ...
├── workflow/                  ← ワークフロースキル（17）
│   ├── verification/SKILL.md
│   ├── context-memory/SKILL.md
│   └── ...
├── project/                   ← プロジェクト固有スキル（3）
├── advanced/                  ← 高度なスキル（6）
├── tools/                     ← ツール連携スキル（2）
└── integration/               ← マルチエージェント連携（1）
```

## カスタマイズ

`~/.claude/CLAUDE.md` に個人設定を追加できる：

```markdown
# Global Settings

@~/ai-dev-kit-vscode/skills/SKILL_MAP.md

## HELIX スキル利用ルール
（省略）

## 言語
- 日本語で応答する

## 禁止事項
- any型の使用
- console.log残し
```

プロジェクト固有の設定は各プロジェクトの `CLAUDE.md` または `CLAUDE.local.md` に書く。

## Codex CLI 対応

各スキルは `compatibility: codex: true` を持つ。Codex CLI で使うには：

```bash
# CLAUDE.md → AGENTS.md の symlink を作成
ln -s CLAUDE.md AGENTS.md
```

詳細は `skills/workflow/context-memory/SKILL.md` の §1.4 を参照。

## Remote SSH / 複数マシン

`~/.claude/CLAUDE.md` 内のパスは `~` ベースなので、各マシンで同じ手順を実行すれば動く：

```bash
git clone https://github.com/RetryYN/ai-dev-kit-vscode.git ~/ai-dev-kit-vscode
# ~/.claude/CLAUDE.md をコピー or dotfiles で同期
```

## ライセンス

MIT
