> 目的: 環境別設定と秘密情報管理の基準を確認するときに参照する

## 適用タイミング

このスキルは以下の場合に読み込む：
- 認証・認可実装時
- 機密情報の扱い時
- 本番環境デプロイ時
- セキュリティレビュー時

> **責務境界**
> - security (本スキル): 脆弱性・OWASP・秘密情報・AI生成コード品質
> - compliance: 法令遵守・ライセンス・規制対応 (GDPR/個人情報保護法など)
> - adversarial-review: 批判的レビュー手法 (脅威モデル特化は workflow/threat-model 参照)

---

## 1. 環境別セキュリティ

### 環境分類

| 環境 | 用途 | セキュリティレベル |
|------|------|-------------------|
| local | 開発者のPC | 低 |
| development | 共有開発環境 | 中 |
| staging | 本番同等検証 | 高 |
| production | 本番 | 最高 |

### 環境別設定

```yaml
# development
DEBUG: true
LOG_LEVEL: debug
CORS_ORIGINS: ["*"]
RATE_LIMIT: なし
SSL: 任意

# staging
DEBUG: false
LOG_LEVEL: info
CORS_ORIGINS: ["https://staging.example.com"]
RATE_LIMIT: あり（緩め）
SSL: 必須

# production
DEBUG: false
LOG_LEVEL: warn
CORS_ORIGINS: ["https://example.com"]
RATE_LIMIT: あり（厳格）
SSL: 必須
```

---

## 2. 機密情報管理

### 絶対禁止

```
❌ コードに直接記述
❌ Gitにコミット
❌ ログに出力
❌ エラーメッセージに含める
❌ フロントエンドに露出
```

### 機密情報の種類

```
- APIキー、シークレット
- DBパスワード
- JWT秘密鍵
- OAuth認証情報
- 暗号化キー
- 個人情報（PII）
```

### 管理方法

| 環境 | 方法 |
|------|------|
| local | `.env.local`（gitignore） |
| development | 環境変数 or Secrets Manager |
| staging/production | Secrets Manager（AWS/GCP/Azure） |

### .gitignore必須項目

```gitignore
# 環境変数
.env
.env.*
!.env.example

# 認証情報
*.pem
*.key
credentials.json
service-account.json

# ローカル設定
.vscode/settings.json
*.local
```

### 環境変数チェック

```typescript
// 起動時に必須環境変数を検証
const requiredEnvVars = [
  'DATABASE_URL',
  'JWT_SECRET',
  'API_KEY',
]

for (const envVar of requiredEnvVars) {
  if (!process.env[envVar]) {
    throw new Error(`Missing required env var: ${envVar}`)
  }
}
```

---

