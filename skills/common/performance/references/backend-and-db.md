> 目的: バックエンド/DB ボトルネックを改善する実装時に参照する

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

