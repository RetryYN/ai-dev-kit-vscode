---
name: security
description: セキュリティ対策で環境別設定ガイド・認証認可実装パターン・脆弱性対策チェックリストとOWASP検証手順を提供
metadata:
  helix_layer: L2
  triggers:
    - 認証・認可実装時
    - 機密情報の扱い時
    - 本番環境デプロイ時
    - セキュリティレビュー時
  verification:
    - "npm audit / pip-audit 0 critical/high"
    - ".env/.env.* が .gitignore 登録済み"
    - "HTTPS強制 + セキュリティヘッダー設定（本番）"
    - "認証: JWT有効期限 ≤1h, bcrypt cost ≥12"
    - "レート制限設定（一般API: 100req/15min, ログイン: 5req/1h）"
compatibility:
  claude: true
  codex: true
---

# セキュリティスキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- 認証・認可実装時
- 機密情報の扱い時
- 本番環境デプロイ時
- セキュリティレビュー時

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

## 3. 認証（Authentication）

### 認証方式比較

| 方式 | 用途 | 特徴 |
|------|------|------|
| Session | Webアプリ | サーバー側で状態管理 |
| JWT | API、SPA | ステートレス |
| OAuth2 | 外部連携 | 認可も含む |
| API Key | サービス間 | シンプル |

### JWT実装

```typescript
// トークン生成
const token = jwt.sign(
  { userId: user.id, role: user.role },
  process.env.JWT_SECRET,
  { 
    expiresIn: '15m',      // アクセストークン: 短め
    algorithm: 'HS256'
  }
)

// リフレッシュトークン: 長め
const refreshToken = jwt.sign(
  { userId: user.id },
  process.env.JWT_REFRESH_SECRET,
  { expiresIn: '7d' }
)
```

### トークン管理

```
アクセストークン:
  - 有効期限: 15分〜1時間
  - 保存: メモリ（推奨）or httpOnly cookie

リフレッシュトークン:
  - 有効期限: 7日〜30日
  - 保存: httpOnly cookie
  - ローテーション: 使用時に再発行
```

### パスワードポリシー

```
最小要件:
- 8文字以上
- 大文字、小文字、数字を含む
- 一般的なパスワードリスト除外

ハッシュ化:
- bcrypt（cost factor 12以上）
- argon2（推奨）
```

```typescript
// bcrypt
import bcrypt from 'bcrypt'
const saltRounds = 12
const hash = await bcrypt.hash(password, saltRounds)
const isValid = await bcrypt.compare(password, hash)
```

---

## 4. 認可（Authorization）

### 認可モデル

| モデル | 説明 | 用途 |
|--------|------|------|
| RBAC | ロールベース | 一般的なWebアプリ |
| ABAC | 属性ベース | 複雑な条件 |
| ACL | リソース単位 | ファイルシステム等 |

### RBAC実装

```typescript
// ロール定義
enum Role {
  ADMIN = 'admin',
  MANAGER = 'manager',
  USER = 'user',
  GUEST = 'guest',
}

// 権限定義
const permissions = {
  [Role.ADMIN]: ['read', 'write', 'delete', 'admin'],
  [Role.MANAGER]: ['read', 'write', 'delete'],
  [Role.USER]: ['read', 'write'],
  [Role.GUEST]: ['read'],
}

// 認可チェック
function authorize(user: User, permission: string): boolean {
  return permissions[user.role]?.includes(permission) ?? false
}
```

### ミドルウェア実装

```typescript
// 認証ミドルウェア
async function authenticate(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1]
  if (!token) return res.status(401).json({ error: 'Unauthorized' })
  
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET)
    req.user = decoded
    next()
  } catch {
    return res.status(401).json({ error: 'Invalid token' })
  }
}

// 認可ミドルウェア
function requirePermission(permission: string) {
  return (req, res, next) => {
    if (!authorize(req.user, permission)) {
      return res.status(403).json({ error: 'Forbidden' })
    }
    next()
  }
}
```

---

## 5. 入力バリデーション

### バリデーション原則

```
✅ サーバーサイドで必ずバリデーション
✅ クライアントサイドはUX用（信頼しない）
✅ ホワイトリスト方式（許可するものを定義）
✅ 型変換前にバリデーション
```

### SQLインジェクション対策

```typescript
// ❌ 危険
const query = `SELECT * FROM users WHERE id = ${userId}`

// ✅ パラメータ化クエリ
const query = 'SELECT * FROM users WHERE id = $1'
const result = await db.query(query, [userId])

// ✅ ORM使用
const user = await prisma.user.findUnique({ where: { id: userId } })
```

### XSS対策

```typescript
// ❌ 危険
element.innerHTML = userInput

// ✅ エスケープ
element.textContent = userInput

// ✅ サニタイズ
import DOMPurify from 'dompurify'
element.innerHTML = DOMPurify.sanitize(userInput)
```

### CSRF対策

```typescript
// CSRFトークン生成
app.use(csrf())

// フォームに埋め込み
<input type="hidden" name="_csrf" value="{{csrfToken}}">

// API: SameSite Cookie
res.cookie('session', token, {
  httpOnly: true,
  secure: true,
  sameSite: 'strict'
})
```

---

## 6. 通信セキュリティ

### HTTPS必須

```nginx
# HTTP → HTTPS リダイレクト
server {
  listen 80;
  return 301 https://$host$request_uri;
}

server {
  listen 443 ssl;
  ssl_certificate /path/to/cert.pem;
  ssl_certificate_key /path/to/key.pem;
  ssl_protocols TLSv1.2 TLSv1.3;
}
```

### セキュリティヘッダー

```typescript
// Helmet.js使用
import helmet from 'helmet'
app.use(helmet())

// または手動設定
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff')
  res.setHeader('X-Frame-Options', 'DENY')
  res.setHeader('X-XSS-Protection', '1; mode=block')
  res.setHeader('Strict-Transport-Security', 'max-age=31536000')
  res.setHeader('Content-Security-Policy', "default-src 'self'")
  next()
})
```

### CORS設定

```typescript
// 本番環境
const corsOptions = {
  origin: ['https://example.com'],
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
  maxAge: 86400,
}
app.use(cors(corsOptions))
```

---

## 7. レート制限

```typescript
import rateLimit from 'express-rate-limit'

// 一般API
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分
  max: 100, // 100リクエスト
  message: 'Too many requests'
})

// ログインAPI（厳しめ）
const loginLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1時間
  max: 5, // 5回
  message: 'Too many login attempts'
})

app.use('/api/', apiLimiter)
app.use('/api/auth/login', loginLimiter)
```

---

## 8. ログとモニタリング

### ログに含める

```
✅ タイムスタンプ
✅ リクエストID
✅ ユーザーID（認証後）
✅ IPアドレス
✅ アクション
✅ 結果（成功/失敗）
```

### ログに含めない

```
❌ パスワード
❌ トークン
❌ 個人情報
❌ 機密データ
```

### 監視アラート

```
- 認証失敗の急増
- 500エラーの急増
- レート制限ヒット
- 異常なアクセスパターン
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
