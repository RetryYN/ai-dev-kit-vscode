> 目的: 認証/認可設計と実装パターンを適用するときに参照する

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

