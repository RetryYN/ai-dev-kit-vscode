# プロジェクトセットアップガイド

既存プロジェクトに Claude Code + HELIX スキルを導入するための手順書。
上から順番に実行すれば完了する。

---

## 前提条件

- Claude Code がインストール済み（`claude --version` で確認）
- Node.js 18+ がインストール済み（MCP サーバーの実行に必要）
- ai-dev-kit-vscode がクローン済み（`~/ai-dev-kit-vscode/`）

```bash
# まだの場合
git clone https://github.com/RetryYN/ai-dev-kit-vscode.git ~/ai-dev-kit-vscode
```

---

## Step 1: グローバル設定（初回のみ）

マシンごとに 1 回だけ実行する。既に設定済みなら Step 2 へ。

### 1.1 ~/.claude/CLAUDE.md

全プロジェクト共通の指示ファイル。Claude Code が毎セッション自動で読み込む。

```bash
mkdir -p ~/.claude
```

以下の内容で `~/.claude/CLAUDE.md` を作成:

```markdown
# Global Settings

@~/ai-dev-kit-vscode/skills/SKILL_MAP.md

## 言語

- 日本語で応答する

## HELIX スキル利用ルール

- スキルは `~/ai-dev-kit-vscode/skills/` に配置
- SKILL_MAP.md（上記 @import）でスキル一覧を把握する
- タスクに該当するスキルがあれば、そのスキルの SKILL.md を Read してから作業する
- スキルの triggers に該当する作業を検出したら、自発的にスキルを読み込む
- 全スキルを一度に読み込まない（コンテキスト節約）
```

**ポイント:**
- `@~/ai-dev-kit-vscode/skills/SKILL_MAP.md` が HELIX 全 40 スキルへのエントリポイント
- 言語や個人的な好みはここに書く（全プロジェクトに適用される）

### 1.2 ~/.claude/settings.json

パーミッション設定。よく使うコマンドを事前許可しておくとプロンプトが減る。

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git push:*)",
      "Bash(git mv:*)",
      "Bash(git rm:*)",
      "Bash(gh:*)",
      "Bash(wc:*)",
      "Bash(ls:*)",
      "Bash(mkdir:*)"
    ]
  }
}
```

**カスタマイズ例:**

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test *)",
      "Bash(npm run build)"
    ],
    "deny": [
      "Bash(curl *)",
      "Read(./.env)",
      "Read(./secrets/**)"
    ]
  }
}
```

### 1.3 グローバル MCP サーバー（任意）

全プロジェクトで使う MCP は `--scope user` で追加:

```bash
# ドキュメント参照（ライブラリの最新ドキュメントを取得）
claude mcp add context7 --scope user -- npx -y @upstash/context7-mcp@latest
```

---

## Step 2: プロジェクト設定

プロジェクトのルートディレクトリで実行する。

### 2.1 .gitignore の確認

以下のエントリが含まれているか確認し、なければ追加:

```gitignore
# Claude Code（個人設定）
CLAUDE.local.md
.claude/settings.local.json
```

### 2.2 CLAUDE.md の作成

プロジェクトのルートに `CLAUDE.md`（または `.claude/CLAUDE.md`）を作成する。
これはチーム全員が共有するプロジェクト知識ファイル。

```markdown
# プロジェクト名

## 概要
一文でプロジェクトを説明（例: "Next.js + Stripe の EC アプリ"）

## 技術スタック
- Frontend: Next.js 14, TypeScript, Tailwind CSS
- Backend: FastAPI, Python 3.12
- DB: PostgreSQL 16
- インフラ: Vercel + Supabase

## アーキテクチャ
主要コンポーネントとその役割を簡潔に

## コーディング規約
- 命名: camelCase（TypeScript） / snake_case（Python）
- テスト: 必須
- 型: strict

## ディレクトリ構造
src/
├── app/          # Next.js App Router
├── components/   # React コンポーネント
├── lib/          # ユーティリティ
└── api/          # API Routes

## コマンド
- ビルド: `npm run build`
- テスト: `npm test`
- lint: `npm run lint`
- dev: `npm run dev`

## 禁止事項
- any 型の使用
- console.log 残し
- 未使用 import
```

#### CLAUDE.md の書き方のコツ

```
✅ やるべき
- 具体的に書く（"2-space indent" ◯ / "format properly" ✗）
- コマンドはコピペ可能にする
- 禁止事項は明示する（Claude が勝手にやりがちなこと）
- 技術スタック・バージョンは正確に

❌ やらないこと
- 500 行を超えない（超える場合は @import や .claude/rules/ で分割）
- グローバル CLAUDE.md と同じ内容を重複しない
- 曖昧な指示を書かない
```

### 2.3 .claude/rules/ の活用（任意）

トピック別にルールを分離できる。自動で全て読み込まれる。

```
.claude/rules/
├── coding-style.md    ← 命名規約・フォーマット
├── testing.md         ← テスト方針
├── security.md        ← セキュリティルール
└── api.md             ← API 設計規約
```

特定のファイルパターンにのみ適用するルール:

```yaml
---
paths:
  - "src/api/**/*.ts"
---
# API ルール
- REST 規約に従う
- エラーは RFC 7807 形式で返す
```

### 2.4 .claude/settings.json（チーム共有）

チーム共通のパーミッション設定。git 管理する。

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test *)",
      "Bash(npm run build)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ]
  }
}
```

### 2.5 CLAUDE.local.md（個人設定、任意）

個人のプロジェクト固有設定。`.gitignore` に含まれるため共有されない。

```markdown
## 個人設定
- DB 接続先: localhost:5432
- テスト実行: `npm test -- --watch`
```

### 2.6 .claude/settings.local.json（個人パーミッション、任意）

個人だけの追加パーミッション。`.gitignore` に含まれるため共有されない。

```json
{
  "permissions": {
    "allow": [
      "Bash(docker compose *)",
      "WebFetch(domain:internal-docs.example.com)"
    ]
  }
}
```

---

## Step 3: MCP サーバー設定

### 3.1 スコープの理解

| スコープ | コマンド | 保存先 | 共有 |
|---------|---------|--------|------|
| `local` (デフォルト) | `claude mcp add <name> ...` | `~/.claude.json` 内のプロジェクトパス | 個人 |
| `project` | `claude mcp add --scope project ...` | `.mcp.json` | チーム（git 管理） |
| `user` | `claude mcp add --scope user ...` | `~/.claude.json` | 個人（全プロジェクト） |

### 3.2 推奨 MCP サーバー

#### ブラウザ操作

```bash
# Playwright（推奨）— アクセシビリティツリーベース、トークン効率良い
claude mcp add playwright -- npx @playwright/mcp@latest

# Chrome DevTools — スクリーンショット、コンソールログ、パフォーマンストレース
claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest
```

#### DB 接続

```bash
# Supabase
claude mcp add supabase -- npx -y supabase-mcp-server

# PostgreSQL
claude mcp add postgres -- npx -y @modelcontextprotocol/server-postgres "postgresql://user:pass@localhost:5432/dbname"

# MongoDB
claude mcp add mongo -- npx -y mongodb-mcp-server --connectionString "mongodb://localhost:27017/dbname"
```

#### ドキュメント参照

```bash
# Context7 — ライブラリの最新ドキュメントをリアルタイム取得
claude mcp add context7 -- npx -y @upstash/context7-mcp@latest
```

### 3.3 チーム共有 MCP（.mcp.json）

チーム全員で使う MCP は `--scope project` で追加するか、`.mcp.json` を直接作成:

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "${DATABASE_URL}"],
      "env": {}
    }
  }
}
```

環境変数 `${VAR}` は実行時に展開される。接続文字列を `.env` に置けばセキュア。

### 3.4 MCP 管理コマンド

```bash
claude mcp list              # 一覧
claude mcp get <name>        # 詳細
claude mcp remove <name>     # 削除
```

---

## Step 4: VSCode プラグイン

### 4.1 必須

```bash
code --install-extension ms-ceintl.vscode-language-pack-ja
code --install-extension eamodio.gitlens
code --install-extension usernamehw.errorlens
code --install-extension editorconfig.editorconfig
```

### 4.2 フロントエンド

```bash
code --install-extension bradlc.vscode-tailwindcss
code --install-extension formulahendry.auto-rename-tag
code --install-extension christian-kohler.path-intellisense
```

### 4.3 バックエンド

```bash
code --install-extension dbaeumer.vscode-eslint
code --install-extension esbenp.prettier-vscode
code --install-extension ms-python.python
code --install-extension charliermarsh.ruff
```

### 4.4 インフラ

```bash
code --install-extension ms-azuretools.vscode-docker
code --install-extension redhat.vscode-yaml
code --install-extension mikestead.dotenv
```

### 4.5 チーム共有設定

`.vscode/extensions.json` でチーム推奨プラグインを定義:

```json
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "editorconfig.editorconfig",
    "usernamehw.errorlens"
  ]
}
```

`.vscode/settings.json`:

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },
  "typescript.preferences.importModuleSpecifier": "relative"
}
```

---

## Step 5: Codex CLI 対応（任意）

Codex CLI を併用する場合の追加設定。

### 5.1 AGENTS.md の作成

```bash
# CLAUDE.md と同じ内容を使う場合は symlink
ln -s CLAUDE.md AGENTS.md
```

### 5.2 CLAUDE.md と AGENTS.md の差分

| 項目 | Claude Code | Codex CLI |
|------|-------------|-----------|
| 指示ファイル | `CLAUDE.md` | `AGENTS.md` |
| 個人上書き | `CLAUDE.local.md` | `AGENTS.override.md` |
| モジュラールール | `.claude/rules/*.md` | なし |
| 設定ファイル | `settings.json`（JSON） | `config.toml`（TOML） |

### 5.3 config.toml

```toml
model = "o3"
approval_mode = "suggest"
```

---

## Step 6: 動作確認

### 6.1 チェックリスト

```bash
# グローバル設定
[ -f ~/.claude/CLAUDE.md ] && echo "OK: CLAUDE.md" || echo "NG: CLAUDE.md なし"
[ -f ~/.claude/settings.json ] && echo "OK: settings.json" || echo "NG: settings.json なし"

# プロジェクト設定
[ -f ./CLAUDE.md ] || [ -f ./.claude/CLAUDE.md ] && echo "OK: Project CLAUDE.md" || echo "NG: Project CLAUDE.md なし"
grep -q "CLAUDE.local.md" .gitignore 2>/dev/null && echo "OK: .gitignore" || echo "NG: .gitignore にエントリなし"
grep -q "settings.local.json" .gitignore 2>/dev/null && echo "OK: .gitignore" || echo "NG: .gitignore にエントリなし"

# MCP
claude mcp list
```

### 6.2 セッション開始テスト

```bash
# プロジェクトディレクトリで Claude Code を起動
claude

# 以下を確認:
# 1. CLAUDE.md が読み込まれている（初期化チェックが実行される）
# 2. SKILL_MAP.md が認識されている（スキルの存在を質問して確認）
# 3. MCP サーバーが接続されている（/mcp で確認）
```

---

## 設定ファイル早見表

### 優先度（高→低）

| # | ファイル | スコープ | 共有 |
|---|---------|---------|------|
| 1 | `/etc/claude-code/managed-settings.json` | 組織 | 強制 |
| 2 | CLI 引数 | セッション | - |
| 3 | `.claude/settings.local.json` | プロジェクト | 個人 |
| 4 | `.claude/settings.json` | プロジェクト | チーム |
| 5 | `~/.claude/settings.json` | 全プロジェクト | 個人 |

### CLAUDE.md の読み込み順

| # | 種別 | パス | 共有 |
|---|------|------|------|
| 1 | Managed | `/etc/claude-code/CLAUDE.md` | 組織 |
| 2 | Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` | チーム |
| 3 | Rules | `./.claude/rules/*.md` | チーム |
| 4 | User | `~/.claude/CLAUDE.md` | 個人 |
| 5 | Local | `./CLAUDE.local.md` | 個人 |
| 6 | Auto | `~/.claude/projects/<id>/memory/` | 個人 |

**探索ルール:**
- cwd からルートまで上方向に再帰探索（見つかった全 CLAUDE.md を読み込む）
- 子ディレクトリの CLAUDE.md はオンデマンド（該当ファイルアクセス時）
- `@path/to/file.md` で外部ファイルをインポート（最大 5 ホップ）

---

## トラブルシューティング

### CLAUDE.md が読み込まれない

```
原因: ファイル名の大文字小文字が違う
対策: 必ず CLAUDE.md（全大文字）にする
```

### @import が効かない

```
原因: パスが間違っている / ファイルが存在しない
対策:
  - 相対パスはインポート元ファイル基準
  - ~ はホームディレクトリに展開される
  - ネスト上限 5（超えると無視される）
```

### MCP サーバーが起動しない

```
原因: npx がパスにない / Node.js バージョンが古い
対策:
  - node -v で 18+ を確認
  - which npx でパスを確認
  - MCP_TIMEOUT 環境変数でタイムアウトを延長
```

### パーミッションプロンプトが多すぎる

```
対策:
  - ~/.claude/settings.json によく使うコマンドを allow に追加
  - セッション中に許可したものは自動で settings.local.json に追加される
  - deny は allow より優先される（deny に入れたら allow では上書きできない）
```

### MEMORY.md が大きくなりすぎた

```
制限: 先頭 200 行のみがシステムプロンプトに読み込まれる
対策:
  - 簡潔に記述する
  - 詳細はトピック別ファイル（debugging.md 等）に分離
  - 古い/誤った情報は削除する
```

---

## 次のステップ

セットアップ完了後:

1. **開発中**: スキルは triggers に該当すると Claude が自発的に読み込む（手動不要）
2. **知見の蓄積**: デバッグ知見や設計判断は auto memory に自動蓄積される
3. **CLAUDE.md の更新**: 新ライブラリ導入時、アーキテクチャ変更時、頻繁な AI ミス発見時に更新する
4. **スキルの確認**: 全スキル一覧は `~/ai-dev-kit-vscode/skills/SKILL_MAP.md` を参照
