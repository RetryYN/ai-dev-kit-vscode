> 目的: 入力検証・通信防御・監視要件を実装するときに参照する

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

