---
name: dev-setup
description: dev-setup関連タスク時に使用
---

# 開発環境構築スキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- 新規メンバー参画時
- 新規プロジェクト開始時
- 環境トラブル発生時

---

## 1. 必須ソフトウェア

### Mac

```bash
# Homebrew（パッケージ管理）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Git
brew install git

# Node.js（バージョン管理付き）
brew install fnm
fnm install 20
fnm use 20

# Python（バージョン管理付き）
brew install pyenv
pyenv install 3.12
pyenv global 3.12

# Docker
brew install --cask docker

# VSCode
brew install --cask visual-studio-code
```

### Windows

```powershell
# Chocolatey（管理者PowerShell）
Set-ExecutionPolicy Bypass -Scope Process -Force
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# Git
choco install git

# Node.js
choco install fnm
fnm install 20

# Python
choco install pyenv-win
pyenv install 3.12

# Docker Desktop
choco install docker-desktop

# VSCode
choco install vscode
```

### 初期設定

```bash
# Git設定
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git config --global init.defaultBranch main
git config --global core.autocrlf input  # Mac/Linux
git config --global core.autocrlf true   # Windows

# SSH鍵生成
ssh-keygen -t ed25519 -C "your.email@example.com"
cat ~/.ssh/id_ed25519.pub  # GitHubに登録
```

---

## 2. VSCode プラグイン

```
⚠️ 詳細は /skills/tools/vscode-plugins.md を参照
```

### 最低限インストール

```bash
# 基本
code --install-extension ms-ceintl.vscode-language-pack-ja
code --install-extension eamodio.gitlens
code --install-extension usernamehw.errorlens

# フロントエンド
code --install-extension bradlc.vscode-tailwindcss
code --install-extension dsznajder.es7-react-js-snippets

# バックエンド
code --install-extension ms-python.python
code --install-extension dbaeumer.vscode-eslint

# AI
code --install-extension anthropic.claude-code
```

詳細なプラグイン一覧、設定例は `/skills/tools/vscode-plugins.md` を参照。

---

## 3. VSCode 設定

### settings.json（推奨）

```json
{
  // エディタ基本
  "editor.fontSize": 14,
  "editor.tabSize": 2,
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit",
    "source.organizeImports": "explicit"
  },
  
  // 括弧
  "editor.bracketPairColorization.enabled": true,
  "editor.guides.bracketPairs": true,
  
  // ファイル
  "files.autoSave": "onFocusChange",
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,
  
  // 検索除外
  "search.exclude": {
    "**/node_modules": true,
    "**/.git": true,
    "**/dist": true,
    "**/.next": true
  },
  
  // ターミナル
  "terminal.integrated.defaultProfile.osx": "zsh",
  "terminal.integrated.fontSize": 13,
  
  // Git
  "git.autofetch": true,
  "git.confirmSync": false,
  
  // 言語別設定
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.tabSize": 4
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### キーボードショートカット（必須）

| ショートカット | 機能 | 覚え方 |
|---------------|------|--------|
| `Cmd/Ctrl + P` | ファイル検索 | **P**roject file |
| `Cmd/Ctrl + Shift + P` | コマンドパレット | - |
| `Cmd/Ctrl + Shift + F` | 全文検索 | **F**ind all |
| `Cmd/Ctrl + D` | 同じ単語を複数選択 | **D**uplicate select |
| `Cmd/Ctrl + /` | コメントトグル | - |
| `Cmd/Ctrl + B` | サイドバー開閉 | - |
| `Cmd/Ctrl + J` | ターミナル開閉 | - |
| `F12` | 定義へジャンプ | - |
| `Shift + F12` | 参照を検索 | - |
| `F2` | リネーム | - |

---

## 4. プロジェクト初期設定

### フロントエンド（Next.js）

```bash
# 作成
npx create-next-app@latest my-app --typescript --tailwind --eslint --app --src-dir

# 追加パッケージ
cd my-app
npm install zod react-hook-form @hookform/resolvers
npm install -D prettier prettier-plugin-tailwindcss

# .prettierrc
{
  "semi": false,
  "singleQuote": true,
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

### バックエンド（FastAPI）

```bash
# 仮想環境
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows

# パッケージ
pip install fastapi uvicorn sqlalchemy alembic pydantic-settings
pip install -D ruff pytest pytest-asyncio

# pyproject.toml
[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W"]

[tool.ruff.isort]
known-first-party = ["app"]
```

### Docker開発環境

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
      POSTGRES_DB: myapp_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

```bash
# 起動
docker-compose -f docker-compose.dev.yml up -d

# 停止
docker-compose -f docker-compose.dev.yml down
```

---

## 5. トラブルシューティング

### よくあるエラー

| エラー | 原因 | 解決 |
|--------|------|------|
| `command not found: node` | PATHが通っていない | ターミナル再起動、シェル設定確認 |
| `EACCES permission denied` | npm権限問題 | `sudo chown -R $(whoami) ~/.npm` |
| `port already in use` | ポート競合 | `lsof -i :3000` で確認して kill |
| `Cannot find module` | パッケージ未インストール | `npm install` |
| `docker: command not found` | Docker未起動 | Docker Desktop起動 |

### 環境リセット

```bash
# Node.js
rm -rf node_modules package-lock.json
npm install

# Python
rm -rf .venv
python -m venv .venv
pip install -r requirements.txt

# Docker
docker-compose down -v
docker system prune -a
docker-compose up -d --build
```

---

## 6. 初心者向けTips

### ターミナル基本コマンド

```bash
cd folder      # フォルダ移動
cd ..          # 上の階層へ
ls             # ファイル一覧（Mac/Linux）
dir            # ファイル一覧（Windows）
pwd            # 現在のパス
mkdir name     # フォルダ作成
touch file     # ファイル作成（Mac/Linux）
rm file        # ファイル削除
rm -rf folder  # フォルダ削除
```

### Git基本コマンド

```bash
git clone URL          # リポジトリ取得
git pull               # 最新取得
git status             # 状態確認
git add .              # 全変更をステージ
git commit -m "msg"    # コミット
git push               # プッシュ
git checkout -b name   # ブランチ作成＆切り替え
git switch main        # mainに切り替え
```

### 困ったときは

```
1. エラーメッセージを読む（最初の行が重要）
2. エラーメッセージでググる
3. ChatGPT/Claudeに聞く
4. チームメンバーに聞く
```

---

## チェックリスト

### 環境構築完了

```
[ ] Git設定完了（name, email）
[ ] SSH鍵をGitHubに登録
[ ] Node.js/Pythonインストール
[ ] Dockerインストール・起動確認
[ ] VSCode設定完了
[ ] プロジェクトclone・起動確認
```
