---
name: infrastructure
description: Docker・PostgreSQL・Redis・Nginxの本番構成と安全設定の指針を提供
metadata:
  helix_layer: L6
  triggers:
    - インフラ構築時
    - デプロイ設定時
    - CI/CD構築時
  verification:
    - "docker compose up --build 正常起動（exit code 0）"
    - "docker compose ps: 全コンテナ running"
    - "ヘルスチェックエンドポイント HTTP 200"
compatibility:
  claude: true
  codex: true
---

# インフラスキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- Docker環境構築時
- DB設計・運用時
- サーバー設定時
- デプロイ時

---

## 1. Docker環境

### ディレクトリ構成

```
project/
├── docker/
│   ├── app/
│   │   └── Dockerfile
│   ├── nginx/
│   │   ├── Dockerfile
│   │   └── nginx.conf
│   └── db/
│       └── init.sql
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
└── .dockerignore
```

### Dockerfile（本番用）

```dockerfile
# マルチステージビルド
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# セキュリティ: non-rootユーザー
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 appuser

COPY --from=builder --chown=appuser:nodejs /app/dist ./dist
COPY --from=builder --chown=appuser:nodejs /app/node_modules ./node_modules

USER appuser
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### Dockerfile（開発用）

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: docker/app/Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/db/init.sql:/docker-entrypoint-initdb.d/init.sql
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=mydb
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d mydb"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    build:
      context: ./docker/nginx
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### .dockerignore

```
node_modules
npm-debug.log
.git
.gitignore
.env
.env.*
*.md
tests
coverage
.vscode
.idea
```

### Dockerコマンド

```bash
# ビルド
docker-compose build

# 起動
docker-compose up -d

# ログ確認
docker-compose logs -f app

# コンテナに入る
docker-compose exec app sh

# 停止・削除
docker-compose down

# ボリュームも削除
docker-compose down -v

# 再ビルド起動
docker-compose up -d --build
```

---

## 2. データベース

### PostgreSQL設定

```sql
-- 本番環境推奨設定
-- postgresql.conf

# メモリ（サーバーRAMの25%）
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 64MB
maintenance_work_mem = 512MB

# 接続
max_connections = 200

# WAL
wal_level = replica
max_wal_senders = 3

# ログ
log_statement = 'mod'
log_duration = on
log_min_duration_statement = 1000  # 1秒以上のクエリをログ
```

### インデックス設計

```sql
-- 主キー（自動）
CREATE TABLE users (
  id SERIAL PRIMARY KEY
);

-- 外部キー
CREATE INDEX idx_posts_user_id ON posts(user_id);

-- 検索カラム
CREATE INDEX idx_users_email ON users(email);

-- 複合インデックス（左端から使われる）
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- 部分インデックス
CREATE INDEX idx_orders_pending ON orders(created_at) 
WHERE status = 'pending';

-- 全文検索（PostgreSQL）
CREATE INDEX idx_posts_content_gin ON posts 
USING gin(to_tsvector('japanese', content));
```

### バックアップ戦略

```bash
# 日次フルバックアップ
pg_dump -Fc mydb > backup_$(date +%Y%m%d).dump

# リストア
pg_restore -d mydb backup_20250101.dump

# 継続的アーカイブ（WAL）
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'
```

### マイグレーション

```bash
# Prisma
npx prisma migrate dev --name add_users_table
npx prisma migrate deploy  # 本番

# Alembic（Python）
alembic revision --autogenerate -m "add users table"
alembic upgrade head
```

### 接続プール

```typescript
// Prisma
const prisma = new PrismaClient({
  datasources: {
    db: {
      url: process.env.DATABASE_URL,
    },
  },
  // 接続プール設定はURL側で
  // ?connection_limit=20&pool_timeout=30
})
```

---

## 3. Redis

### 用途別設計

| 用途 | データ構造 | TTL |
|------|-----------|-----|
| セッション | Hash | 24時間 |
| キャッシュ | String/Hash | 1時間 |
| レート制限 | String（カウンター） | 1分〜1時間 |
| キュー | List | なし |
| リアルタイム | Pub/Sub | なし |

### 実装例

```typescript
import Redis from 'ioredis'

const redis = new Redis({
  host: process.env.REDIS_HOST,
  port: 6379,
  password: process.env.REDIS_PASSWORD,
  retryDelayOnFailover: 100,
  maxRetriesPerRequest: 3,
})

// キャッシュ
async function getUser(id: string): Promise<User> {
  const cached = await redis.get(`user:${id}`)
  if (cached) return JSON.parse(cached)
  
  const user = await db.users.findUnique({ where: { id } })
  await redis.setex(`user:${id}`, 3600, JSON.stringify(user))
  return user
}

// レート制限
async function checkRateLimit(ip: string): Promise<boolean> {
  const key = `ratelimit:${ip}`
  const count = await redis.incr(key)
  if (count === 1) await redis.expire(key, 60)
  return count <= 100
}
```

---

## 4. Nginx

### 基本設定

```nginx
# nginx.conf
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    # 基本設定
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript;

    # セキュリティ
    server_tokens off;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # アップストリーム
    upstream app {
        server app:3000;
        keepalive 32;
    }

    server {
        listen 80;
        server_name example.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name example.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

        location / {
            proxy_pass http://app;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }

        # 静的ファイル
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

---

## 5. 詳細ガイド

→ 詳細は `references/advanced.md` を参照（OS設定・モニタリング・デプロイ）

---

## チェックリスト

### Docker

```
[ ] マルチステージビルド
[ ] non-rootユーザー
[ ] .dockerignore設定
[ ] ヘルスチェック設定
[ ] ボリューム永続化
```

### DB

```
[ ] インデックス設計
[ ] バックアップ設定
[ ] 接続プール設定
[ ] スロークエリログ
```

### 本番環境

```
[ ] SSL/TLS設定
[ ] ファイアウォール設定
[ ] モニタリング設定
[ ] ログ収集設定
[ ] バックアップ自動化
```
