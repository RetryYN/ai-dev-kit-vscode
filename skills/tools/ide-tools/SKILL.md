---
name: ide-tools
description: IDE・AIツール選定とMCP設定の比較検討手順とセットアップ手順を提供
metadata:
  helix_layer: L6
  triggers:
    - IDE設定時
    - 開発ツール選定時
    - 生産性向上時
  verification:
    - "code --list-extensions に必須プラグイン含む"
    - "settings.json: formatOnSave / codeActionsOnSave 設定済み"
compatibility:
  claude: true
  codex: true
---

# IDE/AIツールスキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- 開発ツール選定時
- AIコーディング活用時
- 並列開発時

---

## 1. ツール比較サマリー

| ツール | 強み | 弱み | 用途 |
|--------|------|------|------|
| **Claude Code** | 自律性、大規模変更 | UI実装、精度ムラ | メイン開発 |
| **Antigravity** | 並列実行、ブラウザ統合 | 起動重い | フロントエンド確認 |
| **Cursor** | 補完精度、使いやすさ | 自律性低い | 細かい修正 |
| **Copilot** | 補完速度、安定性 | 大きな変更苦手 | 日常コーディング |
| **Cline** | 柔軟性、ブラウザ連携 | 設定複雑 | 自動デバッグ |

---

## 2. Claude Code

### 特徴

```
✅ 強み
- 高い自律性（考えて動く）
- 大規模ファイル変更
- コンテキスト理解
- マルチファイル操作

❌ 弱み
- トークン消費大
- UI実装の精度ムラ
- フロントエンド接続忘れ
- 長時間タスクでの迷走
```

### 効果的な使い方

```bash
# 起動
claude

# ブラウザ連携（CLI）
claude --chrome

# タスク実行
> APIエンドポイント /api/users を実装して。
> テストコードも一緒に書いて。

# ファイル指定
> @src/api/users.ts を修正して
```

### CLAUDE.md設定

```markdown
# プロジェクト: {{name}}

## 技術スタック
- Frontend: Next.js 14, TypeScript
- Backend: FastAPI, Python 3.12
- DB: PostgreSQL 16

## コーディングルール
- 型は厳格に
- テストは必須
- コミット前にlint

## 禁止事項
- any型
- console.log残し
- 未使用import
```

### トークン節約

```
マルチエージェント構成:
- Opus: オーケストレーター（判断・統合・ディスパッチ。実装しない）
- Codex 5.3: 中〜大規模実装
- Codex 5.2: 小規模実装・軽微修正
- Sonnet: テスト・ドキュメント
- Haiku 4.5: 調査

指示例:
「このタスクはCodex 5.3で実装して」
「Haikuでlint修正だけして」
```

---

## 3. Google Antigravity

### 特徴

```
✅ 強み
- ネイティブブラウザエージェント
- 並列タスク実行
- 実装計画の可視化
- Claude Sonnet/Opus使用可能

❌ 弱み
- 起動が重い
- エージェント生成が遅い
- 独自UIに慣れ必要
```

### 効果的な使い方

```
推奨構成:
1. Antigravityに Claude Code 拡張をインストール
2. 通常はClaude Codeで開発
3. フロントエンド確認時のみブラウザ機能使用
4. 「第2のVSCode」として並列作業

ブラウザエージェント:
- UIの動作確認
- コンソールエラー取得
- スクリーンショット
```

### 設定

```json
// settings.json
{
  "antigravity.defaultModel": "claude-sonnet-4-5",
  "antigravity.browserAgent": {
    "enabled": true,
    "headless": false
  }
}
```

---

## 4. Cursor

### 特徴

```
✅ 強み
- 補完精度が高い
- UIが使いやすい
- Composer機能
- 複数モデル対応

❌ 弱み
- 自律性が低い（指示待ち）
- 攻撃的なオートコンプリート
- Claude Codeと併用で二重課金
```

### 効果的な使い方

```
用途:
- 細かい修正、バグフィックス
- コード補完
- リファクタリング
- ドキュメント生成

避ける用途:
- 大規模な新規実装
- 複数ファイルの同時変更
```

### 設定

```json
// settings.json
{
  "cursor.cpp.disabledLanguages": [],
  "cursor.general.gitDiff": "unified",
  "cursor.chat.defaultModel": "claude-sonnet-4-5"
}
```

### Composer

```
# Composerの使い方
Cmd + K → 選択範囲を指定して指示

例:
- 「この関数をリファクタリング」
- 「エラーハンドリングを追加」
- 「型を追加」
```

---

## 5. GitHub Copilot

### 特徴

```
✅ 強み
- 補完が速い
- 安定している
- IDE統合良好
- Agent mode（auto-fix）

❌ 弱み
- 大きな変更は苦手
- コンテキスト理解限定
- カスタマイズ性低い
```

### Agent Mode設定

```json
// settings.json
{
  "github.copilot.chat.agent.autoFix": true,
  "github.copilot.enable": {
    "*": true,
    "yaml": true,
    "plaintext": false,
    "markdown": false
  }
}
```

### 効果的なプロンプト

```
# コメントで指示
// ユーザー認証関数
// 引数: email, password
// 戻り値: User | null
// bcryptでパスワード検証

// 補完が良い例
function validateUser(email: string, password: string): User | null {
  // ここでTabを押すと補完
}
```

---

## 6. Cline

### 特徴

```
✅ 強み
- @problems でVSCode診断取得
- ブラウザ自動起動
- コンソールエラー取得→自動修正
- 柔軟なモデル選択（OpenRouter）

❌ 弱み
- 設定が複雑
- Claude Code非ネイティブ
- 動作が不安定な時あり
```

### 効果的な使い方

```
# @problems 機能
# VSCodeの全エラー・警告を取得して修正

> @problems fix all errors

# ブラウザ連携
> test the app

→ 自動でブラウザ起動
→ コンソールログ取得
→ エラー検出
→ 自動修正
```

### 設定

```json
// cline設定
{
  "model": "anthropic/claude-sonnet-4-5",
  "apiProvider": "openrouter",
  "browser": {
    "enabled": true,
    "headless": false
  }
}
```

---

## 7. 使い分け戦略

### タスク別推奨

| タスク | 推奨ツール | 理由 |
|--------|-----------|------|
| 新規API実装 | Claude Code | 自律性、複数ファイル |
| UI実装 | Cursor + Antigravity | 補完＋ブラウザ確認 |
| バグ修正 | Cline | @problems + 自動修正 |
| リファクタリング | Cursor Composer | 範囲指定しやすい |
| コード補完 | Copilot | 速度、安定性 |
| 大規模変更 | Claude Code (Multi-agent) | トークン効率 |

### 並列開発構成

```
メインウィンドウ: VSCode + Claude Code
  - バックエンド開発
  - API実装

サブウィンドウ: Antigravity
  - フロントエンド開発
  - ブラウザ確認

補助: Copilot
  - 常時補完ON
```

### コスト最適化

```
Claude Max ($200/月):
- メイン開発にはClaude Code
- Opus: オーケストレーター（実装しない）
- Codex 5.3: 中〜大規模実装
- Codex 5.2: 軽微な修正

追加コスト回避:
- Cursorは無料枠で補完のみ
- Copilotは会社契約
- Clineは OpenRouter 従量制
```

---

## 8. LLMモデル選択

### モデル特性

| モデル | 得意 | 苦手 | コスト |
|--------|------|------|--------|
| Claude Opus | 複雑な判断、設計、オーケストレーション | 単純作業 | 高 |
| Claude Sonnet | テスト、ドキュメント | 複雑な実装 | 中 |
| Claude Haiku 4.5 | 速度、単純タスク | 複雑な判断 | 低 |
| GPT-4o | 汎用、安定 | 長いコンテキスト | 中 |
| Gemini 2.0 | マルチモーダル | コード特化度 | 中 |
| Codex | コード補完 | 対話 | 低 |

### タスク別モデル

```
Opus:
- アーキテクチャ設計
- コードレビュー
- 複雑なバグ調査
- 詰めの実装・仕上げ（エッジケース、型厳密化等）

Sonnet:
- 機能実装
- テスト作成
- ドキュメント生成

Haiku 4.5:
- lint修正
- 変数リネーム
- コメント追加
```

---

## 9. 推奨MCPサーバー

→ 詳細セットアップ・活用例は `references/mcp-setup.md` を参照

### クイックリファレンス

| カテゴリ | MCP | セットアップコマンド |
|---------|-----|---------------------|
| ブラウザ | **Playwright** (推奨) | `claude mcp add playwright -- npx @playwright/mcp@latest` |
| ブラウザ | **Chrome DevTools** | `claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest` |
| DB | **Supabase** | `claude mcp add supabase -- npx -y supabase-mcp-server` |
| DB | **PostgreSQL** | `claude mcp add postgres -- npx -y @modelcontextprotocol/server-postgres $URL` |
| ドキュメント | **Context7** | `claude mcp add context7 -- npx -y @upstash/context7-mcp@latest` |

### 推奨構成（2-3個に絞る）

```
フロントエンド: Playwright + Context7
バックエンド:   DB系1つ + Context7
フルスタック:   Playwright + DB系1つ + Context7
```

---

## 10. トラブルシューティング

### Claude Codeが迷走する

```
対策:
1. タスクを小さく分割
2. 明確な完了条件を指示
3. 途中で軌道修正
4. CLAUDE.md に禁止事項追記
```

### フロントエンドとバックエンドが繋がらない

```
対策:
1. API仕様書を先に作成
2. 型定義を共有
3. OpenAPI/Swagger生成
4. 実装後にcurlで確認指示
```

### トークン消費が激しい

```
対策:
1. マルチエージェント化
2. スキルファイル分離
3. 不要なコンテキスト削除
4. 完了タスクのサマリー化
```

---

## チェックリスト

### ツール選定

```
[ ] タスクの性質を確認
[ ] コスト制約を確認
[ ] チームスキルを確認
[ ] 既存ツールとの連携確認
```

### 効果的な利用

```
[ ] CLAUDE.md設定済み
[ ] マルチエージェント設定
[ ] ブラウザ連携設定
[ ] コスト監視設定
```
