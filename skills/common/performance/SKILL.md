---
name: performance
description: performance関連タスク時に使用
---

# パフォーマンススキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- パフォーマンス改善時
- ボトルネック調査時
- 負荷テスト時

---

## 1. パフォーマンス目標

### Core Web Vitals（2026年基準）

| 指標 | 良好 | 要改善 | 不良 |
|------|------|--------|------|
| **LCP**（最大コンテンツ描画） | ≤2.5s | ≤4.0s | >4.0s |
| **INP**（次の描画への応答性） | ≤200ms | ≤500ms | >500ms |
| **CLS**（累積レイアウトシフト） | ≤0.1 | ≤0.25 | >0.25 |

### バックエンド目標

| 指標 | 目標 | 警告 | 危険 |
|------|------|------|------|
| API応答時間（p95） | <200ms | <500ms | >1s |
| API応答時間（p99） | <500ms | <1s | >2s |
| エラー率 | <0.1% | <1% | >1% |
| スループット | 要件依存 | - | - |

---

## 2. フロントエンド最適化

### バンドルサイズ

```bash
# 分析
npx next build
npx @next/bundle-analyzer

# 目標
- 初期JS: <100KB（gzip）
- 初期CSS: <20KB（gzip）
- 画像: WebP/AVIF使用
```

### コード分割

```typescript
// 動的インポート
const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <Skeleton />,
  ssr: false  // 必要に応じて
})

// ルートベース分割（Next.js App Router）
// app/dashboard/page.tsx → 自動的に分割
```

### 画像最適化

```tsx
// Next.js Image
import Image from 'next/image'

<Image
  src="/hero.jpg"
  alt="Hero"
  width={1200}
  height={600}
  priority  // LCP画像
  placeholder="blur"
  blurDataURL="data:image/jpeg;base64,..."
/>

// サイズ指定
// - モバイル: 640w
// - タブレット: 1024w
// - デスクトップ: 1920w
```

### レンダリング最適化

```typescript
// メモ化
const MemoizedComponent = memo(ExpensiveComponent)

// useMemo
const computed = useMemo(() => {
  return expensiveCalculation(data)
}, [data])

// useCallback
const handleClick = useCallback(() => {
  doSomething(id)
}, [id])

// 仮想スクロール（大量リスト）
import { useVirtualizer } from '@tanstack/react-virtual'
```

### リソースヒント

```html
<!-- プリロード（重要リソース） -->
<link rel="preload" href="/fonts/main.woff2" as="font" crossorigin>

<!-- プリコネクト（外部ドメイン） -->
<link rel="preconnect" href="https://api.example.com">

<!-- プリフェッチ（次のページ） -->
<link rel="prefetch" href="/dashboard">
```

---

## 3. バックエンド最適化

### N+1問題

```python
# ❌ N+1問題
users = User.query.all()
for user in users:
    posts = Post.query.filter_by(user_id=user.id).all()  # N回クエリ

# ✅ Eager Loading
users = User.query.options(joinedload(User.posts)).all()

# ✅ IN句
user_ids = [u.id for u in users]
posts = Post.query.filter(Post.user_id.in_(user_ids)).all()
```

### クエリ最適化

```sql
-- インデックス確認
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123;

-- 改善前: Seq Scan（全件スキャン）
-- 改善後: Index Scan（インデックス使用）

-- 複合インデックス
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- カバリングインデックス
CREATE INDEX idx_orders_covering ON orders(user_id) INCLUDE (total, created_at);
```

### キャッシュ戦略

```python
import redis
from functools import wraps

redis_client = redis.Redis()

def cache(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # キャッシュ確認
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
            
            # 実行＆キャッシュ
            result = await func(*args, **kwargs)
            redis_client.setex(key, ttl, json.dumps(result))
            
            return result
        return wrapper
    return decorator

@cache(ttl=60)
async def get_user_stats(user_id: int):
    # 重い処理
    return await calculate_stats(user_id)
```

### 接続プール

```python
# SQLAlchemy
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # 常時接続数
    max_overflow=10,       # 追加接続数
    pool_timeout=30,       # 接続待ちタイムアウト
    pool_recycle=1800,     # 接続リサイクル間隔
)

# Redis
import redis

pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50
)
redis_client = redis.Redis(connection_pool=pool)
```

### 非同期処理

```python
# バックグラウンドタスク
from fastapi import BackgroundTasks

@app.post("/orders")
async def create_order(order: Order, background_tasks: BackgroundTasks):
    # 同期的に保存
    saved = await save_order(order)
    
    # 非同期でメール送信
    background_tasks.add_task(send_confirmation_email, saved.id)
    
    return saved

# キュー（Celery）
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379')

@celery.task
def process_heavy_task(data):
    # 重い処理
    pass
```

---

## 4. データベース最適化

### インデックス設計

```sql
-- 基本ルール
-- 1. WHERE句で使うカラム
-- 2. JOIN条件のカラム
-- 3. ORDER BY句のカラム
-- 4. カーディナリティが高いカラム

-- 複合インデックスの順序
-- 等価条件 → 範囲条件 → ソート
CREATE INDEX idx_orders ON orders(status, created_at);

-- 部分インデックス
CREATE INDEX idx_active_users ON users(email) WHERE status = 'active';

-- 式インデックス
CREATE INDEX idx_lower_email ON users(LOWER(email));
```

### クエリプラン分析

```sql
-- 実行計画確認
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM orders WHERE user_id = 123 ORDER BY created_at DESC LIMIT 10;

-- 確認ポイント
-- - Seq Scan → Index Scanに変更すべき
-- - Sort → インデックスで解決できるか
-- - Nested Loop → Hash Joinの方が良い場合
-- - actual time → 実際の実行時間
```

### パーティショニング

```sql
-- 日付でパーティション
CREATE TABLE orders (
    id SERIAL,
    user_id INTEGER,
    created_at TIMESTAMP
) PARTITION BY RANGE (created_at);

CREATE TABLE orders_2025 PARTITION OF orders
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

CREATE TABLE orders_2026 PARTITION OF orders
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
```

---

## 5. 計測方法

### フロントエンド計測

```typescript
// Web Vitals
import { onLCP, onINP, onCLS } from 'web-vitals'

onLCP(metric => sendToAnalytics('LCP', metric))
onINP(metric => sendToAnalytics('INP', metric))
onCLS(metric => sendToAnalytics('CLS', metric))

// Performance API
const timing = performance.getEntriesByType('navigation')[0]
console.log('DOM Content Loaded:', timing.domContentLoadedEventEnd)
console.log('Load Complete:', timing.loadEventEnd)

// ユーザータイミング
performance.mark('feature-start')
// ... 処理 ...
performance.mark('feature-end')
performance.measure('feature', 'feature-start', 'feature-end')
```

### バックエンド計測

```python
import time
from functools import wraps

def timing(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        duration = time.perf_counter() - start
        
        # メトリクス送信
        metrics.histogram('api_duration', duration, tags={'endpoint': func.__name__})
        
        return result
    return wrapper

@timing
async def get_users():
    return await db.fetch_all("SELECT * FROM users")
```

### 負荷テスト

```python
# Locust
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)
    
    @task(3)
    def view_dashboard(self):
        self.client.get("/api/dashboard")
    
    @task(1)
    def create_order(self):
        self.client.post("/api/orders", json={"item": "test"})

# 実行
# locust -f locustfile.py --host=http://localhost:8000
```

```bash
# k6
k6 run --vus 100 --duration 60s script.js
```

---

## 6. ボトルネック特定

### フローチャート

```
パフォーマンス問題
    │
    ├─ フロントエンド遅い？
    │   ├─ 初期表示 → バンドルサイズ、SSR
    │   ├─ 操作応答 → レンダリング、状態管理
    │   └─ ネットワーク → API応答、キャッシュ
    │
    ├─ API遅い？
    │   ├─ 全API遅い → サーバーリソース
    │   ├─ 特定API遅い → コード、クエリ
    │   └─ 負荷時のみ → スケーリング
    │
    └─ DB遅い？
        ├─ 特定クエリ → インデックス、クエリ最適化
        ├─ 全体的 → 接続数、リソース
        └─ 書き込み → ロック競合、トランザクション
```

### 調査ツール

| レイヤー | ツール |
|---------|--------|
| ブラウザ | Chrome DevTools, Lighthouse |
| フロントエンド | React DevTools, Next.js Analytics |
| API | Postman, curl, k6 |
| アプリケーション | APM（Datadog, New Relic） |
| データベース | EXPLAIN ANALYZE, pg_stat_statements |
| インフラ | top, htop, vmstat, iostat |

---

## 7. 最適化チェックリスト

### フロントエンド

```
[ ] バンドルサイズ分析
[ ] 不要な依存削除
[ ] コード分割実装
[ ] 画像最適化
[ ] フォント最適化
[ ] キャッシュヘッダー設定
[ ] CDN設定
```

### バックエンド

```
[ ] N+1クエリ解消
[ ] インデックス最適化
[ ] キャッシュ導入
[ ] 接続プール設定
[ ] 非同期処理化
[ ] レスポンス圧縮
```

### データベース

```
[ ] スロークエリ分析
[ ] インデックス見直し
[ ] クエリ最適化
[ ] 不要データ削除
[ ] バキューム実行
[ ] 統計情報更新
```

---

## チェックリスト

### 計測時

```
[ ] 目標値を設定
[ ] ベースライン計測
[ ] ボトルネック特定
[ ] 改善実施
[ ] 効果測定
```
