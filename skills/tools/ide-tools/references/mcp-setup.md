# MCP サーバー詳細セットアップ
> 目的: MCP サーバー詳細セットアップ の要点を把握し、設計・実装判断を行う際のクイックリファレンスとして参照

## ブラウザ操作

| MCP | 提供元 | 用途 | セットアップ |
|-----|--------|------|-------------|
| **Playwright MCP** | Microsoft | 日常のフロントエンド開発・E2Eテスト | `claude mcp add playwright -- npx @playwright/mcp@latest` |
| **Chrome DevTools MCP** | Google | CSSデバッグ・パフォーマンス分析 | `claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest` |

### Playwright MCP（推奨）

```
特徴:
- アクセシビリティツリーベース（スクリーンショット不要）
- トークン消費が少なく、コーディングエージェントと相性良好
- マルチブラウザ対応（Chrome, Firefox, WebKit）

活用例:
- 「localhost:3000を開いてフォームの動作確認して」
- 「ボタンをクリックして遷移先のDOM構造を確認して」
- 「E2Eテストを実行して失敗箇所を修正して」

オプション:
  --headless        ヘッドレス実行
  --browser chrome  ブラウザ指定
  --viewport-size 1280x720  画面サイズ
```

### Chrome DevTools MCP（詳細分析用）

```
特徴:
- Chrome DevToolsのフルパワー（26ツール）
- スクリーンショット撮影、コンソールログ取得
- パフォーマンストレース（Lighthouse的分析）
- ネットワークリクエスト監視

活用例:
- 「パフォーマンスを計測してボトルネックを特定して」
- 「コンソールエラーを取得して修正して」
- 「ネットワークリクエストを確認してAPI呼び出しを検証」
```

### 使い分け

```
日常開発: Playwright MCP（軽量・高速）
  → 実装 → ブラウザ確認 → 修正のループ

詳細分析: Chrome DevTools MCP
  → CSSデバッグ、パフォーマンス問題、ネットワーク調査

両方併用可（競合しない）
```

---

## データベース

| MCP | 対象DB | セットアップ |
|-----|--------|-------------|
| **Supabase MCP** | Supabase (PostgreSQL+) | `claude mcp add supabase -- npx -y supabase-mcp-server` |
| **PostgreSQL MCP** | PostgreSQL | `claude mcp add postgres -- npx -y @modelcontextprotocol/server-postgres postgresql://user:pass@localhost:5432/dbname` |
| **MongoDB MCP** | MongoDB | `claude mcp add mongo -- npx -y mongodb-mcp-server --connectionString mongodb://localhost:27017/dbname` |
| **MySQL MCP** | MySQL/MariaDB | `claude mcp add mysql --env MYSQL_HOST=127.0.0.1 --env MYSQL_USER=root --env MYSQL_PASS=pass --env MYSQL_DB=dbname -- npx -y @benborla29/mcp-server-mysql` |

### Supabase MCP

```
特徴:
- ブラウザログインで認証（PAT不要）
- テーブル設計・マイグレーション・RLS・Auth操作可能
- PostgreSQL生MCPより高機能

活用例:
- 「このテーブルのスキーマを確認して」
- 「ユーザーテーブルから直近1週間のデータを取得して」
- 「このクエリの実行計画を確認して最適化して」

注意:
- 本番DBには読み取り専用ユーザーで接続推奨
- 接続文字列にパスワードを含む場合は --env で環境変数化
```

### Docker環境での接続

```
- 公開ポート経由で接続（localhost:公開ポート）
- 例: docker-compose で 5432:5432 → postgresql://localhost:5432/...
- docker network 内の名前は使えない（MCPはホスト側で動作）
```

---

## ドキュメント参照

| MCP | 用途 | セットアップ |
|-----|------|-------------|
| **Context7** | ライブラリ最新ドキュメント取得 | `claude mcp add context7 -- npx -y @upstash/context7-mcp@latest` |

```
活用例:
- プロンプトに「use context7」を追加するだけ
- 「Next.js 15のApp Routerについて use context7」
- 「Prismaの最新マイグレーション方法 use context7」

効果:
- 訓練データにない最新APIを正確に参照
- バージョン固有のコード例を取得
```
