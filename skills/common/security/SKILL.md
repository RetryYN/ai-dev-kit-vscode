---
name: security
description: 脆弱性対策・OWASP・秘密情報管理を提供
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

## OWASP Top 10 自動スキャン

OWASP Top 10 を `rg` で一次検出し、ヒット箇所をレビュー対象にする。
このスキャンは「脆弱性の可能性」を見つけるための補助であり、確定診断ではない。

| OWASP | 検出観点 | `rg` パターン例 |
|------|----------|------------------|
| A01: Broken Access Control | 管理権限の直書き・認可チェック漏れ | `rg -n "isAdmin\\s*=\\s*true|role\\s*==\\s*['\\\"]admin['\\\"]|/admin" --type py --type js --type ts` |
| A02: Cryptographic Failures | 弱いハッシュ・平文保存 | `rg -n "md5\\(|sha1\\(|AES-ECB|password.*plain|base64.*password" --type py --type js --type ts` |
| A03: Injection（SQLi） | 文字列連結SQL・危険なフォーマット | `rg -n "f['\\\"].*SELECT|execute\\(.*\\+|format\\(.*SELECT" --type py` |
| A03: Injection（XSS） | 危険な HTML 挿入 | `rg -n "innerHTML|dangerouslySetInnerHTML|v-html" --type js --type ts` |
| A04: Insecure Design | 開発用バックドア・デバッグ分岐残存 | `rg -n "bypass|backdoor|debug.*auth|skip.*auth" --type py --type js --type ts` |
| A05: Security Misconfiguration | デバッグ有効・危険な設定値 | `rg -n "DEBUG\\s*=\\s*True|CORS_ORIGINS:\\s*\\[\"\\*\"\\]|allow_origins=\\[\"\\*\"\\]" --type py --type js --type ts --type yaml` |
| A06: Vulnerable and Outdated Components | 古い依存・保守停止依存の放置 | `rg -n "(deprecated|unmaintained|end-of-life|known-vulnerable)" package.json package-lock.json requirements*.txt go.mod` |
| A07: Identification and Authentication Failures | 証明書検証無効・認証情報の直書き | `rg -n "verify=False|VERIFY_SSL.*False|password.*=.*['\\\"]" --type py` |
| A08: Software and Data Integrity Failures | 署名検証スキップ・unsafe deserialize | `rg -n "verify_signature\\s*=\\s*False|yaml\\.load\\(|pickle\\.loads\\(" --type py --type js --type ts` |
| A09: Security Logging and Monitoring Failures | 例外握り潰し・監査ログ不足 | `rg -n "except\\s+Exception:\\s+pass|logger\\.debug\\(.*token|print\\(.*password" --type py --type js --type ts` |
| A10: SSRF | 外部URLをそのまま取得 | `rg -n "requests\\.(get|post)\\(.*(url|uri)|axios\\.(get|post)\\(.*(url|uri)|fetch\\(.*(req\\.query|req\\.body)" --type py --type js --type ts` |

### 運用手順

```bash
# 例: まず OWASP A03（Injection）を重点スキャン
rg -n "f['\\\"].*SELECT|execute\\(.*\\+|format\\(.*SELECT" --type py
rg -n "innerHTML|dangerouslySetInnerHTML|v-html" --type js --type ts
```

```
1. ヒット箇所を分類（真陽性 / 偽陽性）
2. 真陽性は修正PRにリンクし、再スキャンしてクローズ
3. 偽陽性は理由を記録（次回の除外パターン改善）
```

---

## OWASP Agentic Top 10 対策

エージェント実行時のリスクを OWASP Agentic Top 10 観点で管理する。

### AG01 プロンプトインジェクション

- 入力バリデーション: ユーザー入力をシステムプロンプトと分離し、命令文をそのまま昇格しない
- 出力フィルタリング: 生成物に悪意あるコードや危険コマンドが含まれないかを検査する
- HELIX: `helix-codex` に渡す task テキストを sanitize し、危険トークンを除去してから実行する

### AG02 不適切な権限管理

- 最小権限原則: `sandbox: workspace-write` をデフォルトにし、`danger-full-access` は明示承認時のみ許可する
- ツール制限: `allowed-tools` で必要最小限のツールのみを許可する
- HELIX: role ごとの許可ツールリストを定義し、実行前に照合する

### AG03 過度な自律性

- 承認ゲート: 重要操作（破壊的変更・本番影響）前に人間承認を必須にする
- HELIX: Phase Guard + `helix plan review` を承認境界として運用する

### AG04 安全でないツール使用

- ツール呼び出し前にパラメータ検証（パス、正規表現、危険コマンド）を行う
- HELIX: `helix-hook` の advisory と `gate-checks` で事前検知する

### AG05 情報漏洩

- コンテキストに秘密情報を含めない（キー、トークン、PII を除外）
- 出力時に redaction を実行し、漏えい文字列を伏せる
- HELIX: `store.py` / `global_store.py` の redaction ルールを適用する

### AG06-AG10（概要）

- AG06: エージェント記憶・コンテキスト汚染のリスク  
  HELIX対策: 参照元の provenance を記録し、未検証メモリを実行判断に直結させない
- AG07: ツール連携・依存チェーンの脆弱性リスク  
  HELIX対策: allowlist、依存監査、危険プリミティブ検出をゲート化する
- AG08: 監視不足・異常検知遅延のリスク  
  HELIX対策: hook ログ、freeze-break 検知、異常イベントの即時アラートを有効化する
- AG09: 意図逸脱・目標ハイジャックのリスク  
  HELIX対策: 計画固定（plan review）と逸脱時の `blocked`/`interrupted` 判定を徹底する
- AG10: 監査不能・責任追跡不可のリスク  
  HELIX対策: SQLite 実行ログ、ミニレトロ、Learning Engine で証跡を保持する

---

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
