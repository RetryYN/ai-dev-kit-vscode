---
name: site-mapping
description: Crawl4AIとFirecrawlの使い分けでサイト構造抽出・Reverse証拠収集・構造化データ抽出を自動化
metadata:
  helix_layer: R0
  triggers:
    - Reverse R0 証拠収集時
    - 競合サイト分析時
    - 既存システムの画面一覧作成時
  verification:
    - "sitemap.json 生成成功"
    - "Markdown corpus 出力"
    - "対象ドメインが allowlist に登録済み"
compatibility:
  claude: true
  codex: true
---

# サイト構造抽出スキル（Crawl4AI + MCP）

## 適用タイミング

このスキルは以下の場合に読み込む：
- Reverse R0 の証拠収集時
- 競合サイト分析時
- 既存システムの画面一覧作成時

---

## 1. セットアップ手順

```bash
python -m venv .venv
source .venv/bin/activate
pip install crawl4ai crawl4ai-mcp-server
```

最低限の出力先を作る：

```bash
mkdir -p artifacts/site-mapping
```

---

## 2. crawl4ai-mcp-server 設定（Claude Code 直結）

`mcp.json` 例：

```json
{
  "servers": {
    "crawl4ai": {
      "command": "crawl4ai-mcp-server",
      "args": ["--isolated"],
      "env": {
        "CRAWL4AI_OUTPUT_DIR": "artifacts/site-mapping",
        "CRAWL4AI_ALLOWLIST": "example.com,docs.example.com"
      }
    }
  }
}
```

運用ルール：

- `--isolated` をデフォルト推奨
- allowlist 未設定では実行しない
- MCP 側の origin 制約は `browser-safety.md` に準拠

---

## 3. セキュリティ制約

共通定義は `skills/tools/ai-coding/references/browser-safety.md` を参照。

必須ルール：

1. allowlist に対象ドメインを明示
2. private network（`192.168.*`, `10.*`, `localhost`）への接続禁止
3. 認証情報ファイルは `.gitignore` に登録
4. セッション終了時に保存データをクリーンアップ

---

## 4. HELIX Reverse R0 との統合手順

1. 対象システムのドメインと収集範囲を確定
2. allowlist を更新
3. Crawl4AI でクローリングを実行
4. `sitemap.json` と Markdown corpus を出力
5. R0 証拠台帳に URL、画面タイトル、取得日時を記録
6. RG0 判定用の「網羅率」と「未到達URL」を添付

---

## 5. サイトマップ出力形式

### JSON（機械処理用）

```json
{
  "root": "https://example.com",
  "pages": [
    {"url": "https://example.com/", "title": "Home", "depth": 0},
    {"url": "https://example.com/docs", "title": "Docs", "depth": 1}
  ]
}
```

### Markdown（レビュー用）

```markdown
# Site Map
- / (Home)
- /docs (Docs)
- /pricing (Pricing)
```

### HTML（共有用）

- 階層リスト形式で出力
- ノードに URL と最終取得時刻を表示

---

## 6. 認証が必要なサイトの扱い

### storage-state 運用

- ログイン済み状態を `storage-state.json` に保存
- 実行時に `storage-state` を明示指定
- 期限切れ時は再取得

`.gitignore` 必須：

```gitignore
auth.json
storage-state.json
artifacts/site-mapping/sessions/
```

禁止事項：

- 認証情報を `README` やコードに直書き
- 共有環境に平文トークンを保存

---

## 7. レート制限設定

推奨初期値：

- `max_concurrency`: 2
- `request_delay_ms`: 1000
- `timeout_ms`: 10000
- `max_retries`: 2

運用ルール：

1. `robots.txt` を尊重する
2. 429 が出たら遅延を増やす
3. サイト運用者の規約を優先する

---

## Firecrawl 統合（代替クローラー）

Firecrawl は `/scrape` / `/crawl` / `/map` / `/extract` を統一 API で扱えるクローラー基盤。
構造化抽出の強さを活かし、Crawl4AI と用途で使い分ける。

### Crawl4AI vs Firecrawl

| 観点 | Crawl4AI | Firecrawl |
|------|----------|-----------|
| 実行形態 | ローカル完結 | 外部 API ベース |
| HELIX 連携 | MCP 直結しやすい | API アダプタ経由 |
| コスト | 無料運用しやすい | 有料プランあり |
| 強み | 監査しやすいローカル処理 | 構造化抽出（表/フォーム/API）の精度 |

### HELIX Reverse R0 での活用

1. `/map` で対象サイトの URL 構造を一括取得
2. `/extract` でテーブル、フォーム、API エンドポイント候補を抽出
3. R0 証拠台帳へ「取得元 URL / 抽出日時 / 抽出方法」を記録
4. RG0 では Crawl4AI の結果と Firecrawl 結果を突合し、欠落ページを補完

### セキュリティ注意

- Firecrawl は外部 API のため、`allowlist` と API キー管理を必須化する
- 送信データは最小化し、機密情報や内部URLを含めない
- API キーは `.env` で管理し、`SKILL.md` / `README` / スクリプトに直書きしない
- 本番系ドメインへのクロールは人間承認後に実行する

---

## 8. 完了判定

- `sitemap.json` 生成成功
- Markdown corpus 出力済み
- allowlist 登録済みドメインのみ収集
