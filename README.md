# @ai-dev-kit/vscode

> **エディタ × 企画書 → 開発環境完成**

VSCode用 AI開発環境セットアップキット。Claude Code / Codex 対応。

## ★ 差別化ポイント: 企画書から自動生成

**競合ツールとの違い:**

| ツール | アプローチ |
|--------|-----------|
| superpowers (27.9k stars) | スキルコレクション + /plan コマンド |
| claude-flow (11.4k stars) | マルチエージェントオーケストレーション |
| skill-codex | Codex CLI 連携 |
| SkillsMP | 71,000+ スキルマーケットプレイス |
| **ai-dev-kit** | **企画書 → 開発環境 自動生成** ★ |

他のツールは「スキルを提供する」か「エージェントを連携する」。
**ai-dev-kit は企画書（ビジネス要件）から逆算して開発環境をセットアップする。**

---

## インストール

```bash
npx @ai-dev-kit/vscode init --spec docs/spec.md
```

## 使い方

### 1. 企画書から自動生成（推奨）

```bash
# 企画書を用意
cat > docs/spec.md << 'EOF'
# 機能企画書: TaskFlow

## 技術仕様
Next.js 14 + FastAPI + PostgreSQL

### API設計
| Method | Endpoint | 説明 |
| GET | /api/tasks | タスク一覧 |
| POST | /api/tasks | タスク作成 |

### 機能要件
1. ユーザー認証（JWT）
2. タスクCRUD
EOF

# 自動生成
npx @ai-dev-kit/vscode init --spec docs/spec.md
```

**生成されるAGENTS.md:**
- 技術スタック自動検出（Next.js, FastAPI, PostgreSQL等）
- API設計の抽出
- 機能要件の抽出
- ディレクトリ構成の推定
- 適切なコマンドの提案

### 2. クイックセットアップ

```bash
npx @ai-dev-kit/vscode init --quick
```

### 3. 対話式セットアップ

```bash
npx @ai-dev-kit/vscode init
```

## 生成される構造

```
my-project/
├── .agent/
│   └── skills/           # 33スキル（Progressive Disclosure対応）
├── .claude/
│   └── skills -> ../.agent/skills
├── .codex/
│   └── skills -> ../.agent/skills
├── .vscode/
│   └── settings.json
├── AGENTS.md             # 企画書から自動生成 or テンプレート
├── CLAUDE.md -> AGENTS.md
└── docs/
    ├── spec.md           # 元の企画書（--spec使用時）
    └── spec-template.md
```

## 技術スタック自動検出

企画書内で検出されるキーワード:

| カテゴリ | 検出パターン |
|----------|-------------|
| Frontend | Next.js, React, Vue.js, Svelte, Angular, TypeScript |
| Backend | FastAPI, Django, Flask, Express, NestJS, Go, Rust |
| Database | PostgreSQL, MySQL, MongoDB, Redis, SQLite, Supabase |
| Infra | Docker, Kubernetes, AWS, GCP, Azure, Vercel |
| Auth | JWT, OAuth, Clerk, Auth0, NextAuth |

## 33 Skills（Progressive Disclosure対応）

全スキル500行以下。必要な時だけロード。

| カテゴリ | スキル |
|----------|--------|
| **common** | coding, testing, git, error-fix, design, refactoring, security, infrastructure, performance, documentation, code-review |
| **workflow** | design-doc, dev-setup, project-management, dev-policy, estimation, deploy, incident |
| **tools** | ide-tools, vscode-plugins, ai-coding |
| **advanced** | ai-integration, tech-selection, external-api, migration, legacy, i18n |
| **project** | architecture, api, db, ui |
| **integration** | codex, orchestrator |

## コマンド

```bash
npx @ai-dev-kit/vscode init              # 対話式セットアップ
npx @ai-dev-kit/vscode init --quick      # クイックセットアップ
npx @ai-dev-kit/vscode init --spec <file> # 企画書から自動生成 ★
npx @ai-dev-kit/vscode sync-agents       # CLAUDE.md → AGENTS.md 同期
npx @ai-dev-kit/vscode list              # スキル一覧
npx @ai-dev-kit/vscode --help            # ヘルプ
```

## Codex 連携

AGENTS.md / CLAUDE.md 内で:

```
Use codex to review this PR
```

→ 自動的に codex スキルが発動し、Codex CLI でレビュー実行

## AGENTS.md のベストプラクティス

生成される AGENTS.md は以下を含む:

- **WHY**: プロジェクトの目的・概要
- **WHAT**: 技術スタック、ディレクトリ構成
- **HOW**: コマンド、ワークフロー
- **Gotchas**: プロジェクト固有の注意点
- **Progressive Disclosure**: Skills/docs への参照

## ライセンス

MIT

## 関連パッケージ（予定）

- `@ai-dev-kit/antigravity` - Antigravity (Gemini) 対応
- `@ai-dev-kit/cursor` - Cursor マルチエージェント対応
