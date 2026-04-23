> 目的: 計測設計・負荷試験・ボトルネック診断を行うときに参照する

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

