> 目的: 秘密情報スキャンと AI 生成コード品質検査を運用するときに参照する

## 秘密情報スキャン

APIキー、トークン、パスワード、証明書などの漏えいを `rg` で検出する。

### 基本スキャン

```bash
rg -n "(?i)(api[_-]?key|secret|token|password|credential|bearer)\\s*[=:]\\s*['\\\"][^'\\\"]{8,}" --type-not md
```

### 証明書・鍵ファイルの混入確認

```bash
rg --files -g "*.pem" -g "*.key" -g "*.p12" -g "*.pfx"
```

### `.env` の Git 追跡チェック

```bash
git ls-files | rg '^\\.env(\\..+)?$'
```

```
期待値:
- 出力なし（.env / .env.* は Git 管理対象外）
- 必要な場合は .env.example のみ追跡
```

### HELIX ゲート統合

```
- G4（実装凍結）: static check に秘密情報スキャンを追加
- G7（安定性）: リリース前の最終スキャンとして再実行
```

---

## AI 生成コード品質チェック

OpenClaw の cacheforge-vibe-check コンセプトを参考に、AI 生成コードの
「品質の癖」を検出してレビューを促進する。判定は advisory（非ブロッキング）。

### 典型パターンの検出例

| 観点 | `rg` パターン例 | レビュー意図 |
|------|------------------|--------------|
| 過剰なコメント | `rg -n "^(\\s*//\\s*(This|Set|Get|Initialize|Handle)|\\s*#\\s*(This|Set|Get|Initialize|Handle))" --type js --type ts --type py` | コメント頼みのコードを分解・命名改善できるか確認 |
| 不要な try/except | `rg -n "except\\s+Exception\\s+as\\s+e:|except\\s+Exception:\\s+pass|catch\\s*\\(e\\)\\s*\\{\\s*\\}" --type py --type js --type ts` | 例外を握り潰していないか確認 |
| 冗長な変数名 | `rg -n "\\b[a-zA-Z_][a-zA-Z0-9_]{30,}\\b" --type py --type js --type ts` | 意味を保った短い命名へ改善 |

### 運用ルール

```
- このチェックは品質レビューを促進するための補助で、merge ブロック条件にはしない
- 指摘は [Should]/[Nit] を基本とし、可読性・保守性の改善提案として扱う
- セキュリティや正確性に直結する場合のみ [Must] に格上げする
```

---

## チェックリスト

### 開発環境

```
[ ] .env.exampleを用意
[ ] 機密情報がgitignoreに
[ ] ローカルでHTTPS不要設定
```

### 本番デプロイ前

```
[ ] DEBUG=false
[ ] 機密情報がSecrets Managerに
[ ] HTTPS強制
[ ] セキュリティヘッダー設定
[ ] CORS適切に設定
[ ] レート制限設定
[ ] ログに機密情報なし
[ ] 依存関係の脆弱性チェック
```
