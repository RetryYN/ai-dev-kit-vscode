# Browser Automation Safety Baseline
> 目的: Browser Automation Safety Baseline の要点を把握し、設計・実装判断を行う際のクイックリファレンスとして参照

automation 系スキル（`site-mapping`, `browser-script`）で共通適用する安全基準。

## 1. allowlist 必須

- 実行前に対象ドメインを明示する
- allowlist 未設定時は実行しない

例：

```text
allowed-origins:
  - https://example.com
  - https://staging.example.com
```

## 2. private network 接続禁止

以下への接続はデフォルトで禁止：

- `localhost`
- `127.0.0.1`
- `10.*`
- `192.168.*`
- `172.16.*` - `172.31.*`

業務上必要な場合のみ、人間承認後に一時許可する。

## 3. `--isolated` モード推奨

- ブラウザ操作とセッションを分離するため、`--isolated` をデフォルト推奨
- 共有プロファイルの再利用を避ける

## 4. 認証ファイルの管理

- `auth.json`, `storage-state.json` は `.gitignore` 必須
- 認証状態は最短寿命で運用し、使い回しを避ける

`.gitignore` 例：

```gitignore
auth.json
storage-state.json
artifacts/site-mapping/sessions/
```

## 5. MCP 設定（allowed / blocked origins）

```json
{
  "allowed-origins": [
    "https://example.com",
    "https://staging.example.com"
  ],
  "blocked-origins": [
    "http://localhost",
    "http://127.0.0.1",
    "http://10.*",
    "http://192.168.*"
  ]
}
```

## 6. セッションデータのクリーンアップ

- 実行終了後に一時セッションを削除する
- レポートに機密値が含まれていないか確認する

例：

```bash
rm -rf artifacts/site-mapping/sessions/*
rm -f storage-state.json auth.json
```

## 7. 監査ログ

最低限、以下を作業記録に残す：

- 実行日時
- 実行者
- 対象URL
- allowlist 設定値
- 取得成果物の保存先
