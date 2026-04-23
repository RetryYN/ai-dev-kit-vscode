# VSCode プラグインカタログ
> 目的: VSCode プラグインカタログ の要点を把握し、設計・実装判断を行う際のクイックリファレンスとして参照

> ide-tools スキルの参照資料。カテゴリ別プラグインリストと一括インストールスクリプト。

---

## 1. 必須プラグイン（全員）

### 基本

| プラグイン | ID | 用途 |
|-----------|-----|------|
| Japanese Language Pack | ms-ceintl.vscode-language-pack-ja | 日本語化 |
| GitLens | eamodio.gitlens | Git履歴、blame |
| Git Graph | mhutchie.git-graph | ブランチ可視化 |
| Error Lens | usernamehw.errorlens | エラー行内表示 |
| Path Intellisense | christian-kohler.path-intellisense | パス補完 |
| EditorConfig | editorconfig.editorconfig | エディタ設定統一 |

### インストールコマンド

```bash
code --install-extension ms-ceintl.vscode-language-pack-ja
code --install-extension eamodio.gitlens
code --install-extension mhutchie.git-graph
code --install-extension usernamehw.errorlens
code --install-extension christian-kohler.path-intellisense
code --install-extension editorconfig.editorconfig
```

---

## 2. フロントエンド

### React/Next.js

| プラグイン | ID | 用途 |
|-----------|-----|------|
| ES7+ React Snippets | dsznajder.es7-react-js-snippets | Reactスニペット |
| Tailwind CSS IntelliSense | bradlc.vscode-tailwindcss | Tailwind補完 |
| Auto Rename Tag | formulahendry.auto-rename-tag | タグ自動リネーム |
| CSS Peek | pranaygp.vscode-css-peek | CSS定義ジャンプ |
| Pretty TypeScript Errors | yoavbls.pretty-ts-errors | TSエラー読みやすく |
| Headwind | heybourn.headwind | Tailwindクラス整列 |

```bash
code --install-extension dsznajder.es7-react-js-snippets
code --install-extension bradlc.vscode-tailwindcss
code --install-extension formulahendry.auto-rename-tag
code --install-extension pranaygp.vscode-css-peek
code --install-extension yoavbls.pretty-ts-errors
code --install-extension heybourn.headwind
```

### Vue

| プラグイン | ID | 用途 |
|-----------|-----|------|
| Vue - Official | vue.volar | Vue言語サポート |
| Vue VSCode Snippets | sdras.vue-vscode-snippets | スニペット |

---

## 3. バックエンド

### TypeScript/Node.js

| プラグイン | ID | 用途 |
|-----------|-----|------|
| ESLint | dbaeumer.vscode-eslint | Linter |
| Prettier | esbenp.prettier-vscode | Formatter |
| npm Intellisense | christian-kohler.npm-intellisense | npm補完 |
| Import Cost | wix.vscode-import-cost | インポートサイズ表示 |

```bash
code --install-extension dbaeumer.vscode-eslint
code --install-extension esbenp.prettier-vscode
code --install-extension christian-kohler.npm-intellisense
code --install-extension wix.vscode-import-cost
```

### Python

| プラグイン | ID | 用途 |
|-----------|-----|------|
| Python | ms-python.python | Python言語サポート |
| Pylance | ms-python.vscode-pylance | 型チェック、補完 |
| Ruff | charliermarsh.ruff | Linter/Formatter |
| Python Debugger | ms-python.debugpy | デバッグ |
| Jupyter | ms-toolsai.jupyter | Notebook |

```bash
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension charliermarsh.ruff
code --install-extension ms-python.debugpy
```

---

## 4. AI/コーディング支援

| プラグイン | ID | 用途 | 備考 |
|-----------|-----|------|------|
| Claude Code | anthropic.claude-code | AIエージェント | CLI連携 |
| GitHub Copilot | github.copilot | AI補完 | 有料 |
| GitHub Copilot Chat | github.copilot-chat | AIチャット | 有料 |
| Cline | saoudrizwan.claude-dev | AIエージェント | OpenRouter |
| TabNine | tabnine.tabnine-vscode | AI補完 | 無料枠あり |

```bash
code --install-extension anthropic.claude-code
code --install-extension github.copilot
code --install-extension github.copilot-chat
```

---

## 5. インフラ/DevOps

| プラグイン | ID | 用途 |
|-----------|-----|------|
| Docker | ms-azuretools.vscode-docker | Docker管理 |
| YAML | redhat.vscode-yaml | YAML補完 |
| DotENV | mikestead.dotenv | .env色分け |
| HashiCorp Terraform | hashicorp.terraform | Terraform |
| Remote - SSH | ms-vscode-remote.remote-ssh | SSH接続 |
| Remote - Containers | ms-vscode-remote.remote-containers | Devcontainer |

```bash
code --install-extension ms-azuretools.vscode-docker
code --install-extension redhat.vscode-yaml
code --install-extension mikestead.dotenv
code --install-extension ms-vscode-remote.remote-ssh
```

---

## 6. データベース/API

| プラグイン | ID | 用途 |
|-----------|-----|------|
| Database Client | cweijan.vscode-database-client2 | DB接続 |
| Thunder Client | rangav.vscode-thunder-client | APIテスト |
| REST Client | humao.rest-client | HTTPリクエスト |
| Prisma | prisma.prisma | Prisma補完 |

```bash
code --install-extension cweijan.vscode-database-client2
code --install-extension rangav.vscode-thunder-client
code --install-extension humao.rest-client
```

---

## 7. テスト/デバッグ

| プラグイン | ID | 用途 |
|-----------|-----|------|
| Jest | orta.vscode-jest | Jestテスト実行 |
| Vitest | vitest.explorer | Vitestテスト |
| Test Explorer UI | hbenl.vscode-test-explorer | テストUI |
| Debug Visualizer | hediet.debug-visualizer | デバッグ可視化 |

```bash
code --install-extension orta.vscode-jest
code --install-extension vitest.explorer
```

---

## 8. ドキュメント/Markdown

| プラグイン | ID | 用途 |
|-----------|-----|------|
| Markdown All in One | yzhang.markdown-all-in-one | Markdown編集 |
| Markdown Preview Enhanced | shd101wyy.markdown-preview-enhanced | プレビュー |
| Draw.io Integration | hediet.vscode-drawio | 図作成 |
| Mermaid | bierner.markdown-mermaid | Mermaid図 |

```bash
code --install-extension yzhang.markdown-all-in-one
code --install-extension shd101wyy.markdown-preview-enhanced
code --install-extension hediet.vscode-drawio
```

---

## 9. 便利ツール

| プラグイン | ID | 用途 |
|-----------|-----|------|
| Todo Tree | gruntfuggly.todo-tree | TODO管理 |
| Bookmarks | alefragnani.bookmarks | コードブックマーク |
| Better Comments | aaron-bond.better-comments | コメント色分け |
| Code Spell Checker | streetsidesoftware.code-spell-checker | スペルチェック |
| Color Highlight | naumovs.color-highlight | 色コード可視化 |
| indent-rainbow | oderwat.indent-rainbow | インデント可視化 |

```bash
code --install-extension gruntfuggly.todo-tree
code --install-extension alefragnani.bookmarks
code --install-extension aaron-bond.better-comments
code --install-extension streetsidesoftware.code-spell-checker
```

---

## 10. チーム共有設定

### .vscode/extensions.json

```json
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "eamodio.gitlens",
    "usernamehw.errorlens",
    "ms-azuretools.vscode-docker"
  ],
  "unwantedRecommendations": []
}
```

### .vscode/settings.json（チーム共有）

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "files.exclude": {
    "**/.git": true,
    "**/node_modules": true,
    "**/.next": true
  }
}
```

---

## 11. 一括インストールスクリプト

### Mac/Linux

```bash
#!/bin/bash
# install-extensions.sh

extensions=(
  "ms-ceintl.vscode-language-pack-ja"
  "eamodio.gitlens"
  "mhutchie.git-graph"
  "usernamehw.errorlens"
  "dbaeumer.vscode-eslint"
  "esbenp.prettier-vscode"
  "bradlc.vscode-tailwindcss"
  "ms-azuretools.vscode-docker"
  "redhat.vscode-yaml"
  "mikestead.dotenv"
)

for ext in "${extensions[@]}"; do
  code --install-extension "$ext"
done
```

### Windows (PowerShell)

```powershell
# install-extensions.ps1

$extensions = @(
  "ms-ceintl.vscode-language-pack-ja"
  "eamodio.gitlens"
  "mhutchie.git-graph"
  "usernamehw.errorlens"
  "dbaeumer.vscode-eslint"
  "esbenp.prettier-vscode"
)

foreach ($ext in $extensions) {
  code --install-extension $ext
}
```

---

## チェックリスト

### 新規メンバー

```
[ ] 必須プラグインインストール
[ ] 言語別プラグインインストール
[ ] チーム設定同期
[ ] ショートカット確認
```

### プロジェクト開始

```
[ ] .vscode/extensions.json作成
[ ] .vscode/settings.json作成
[ ] .editorconfig作成
```
