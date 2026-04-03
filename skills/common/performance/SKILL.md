---
name: performance
description: パフォーマンス最適化でCore Web Vitals目標値・ボトルネック診断フローチャート・計測手順とチェックリストを提供
metadata:
  helix_layer: L4
  triggers:
    - パフォーマンス改善時
    - ボトルネック調査時
    - 負荷テスト時
  verification:
    - "LCP ≤2.5s, INP ≤200ms, CLS ≤0.1 (Core Web Vitals)"
    - "API p95 <200ms, p99 <500ms"
    - "バンドルサイズ: 初期JS <100KB (gzip)"
    - "N+1クエリ 0件 (EXPLAIN ANALYZE確認)"
    - "負荷テスト通過（目標スループット達成）"
compatibility:
  claude: true
  codex: true
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

## トークンコスト最適化（90% 削減戦略）

### Prompt Caching

- system prompt（role 定義 + スキル参照）を固定し、キャッシュヒット時に大幅削減を狙う
- HELIX では `helix-codex` の role prompt はセッション内で固定し、キャッシュ対象にする
- 実装例:
  - Anthropic API の prompt caching
  - OpenAI の `cached_tokens`

### Semantic Caching

- 類似クエリの結果をローカル再利用し、同一探索の再実行を減らす
- HELIX では `helix discover` の検索結果をキャッシュ対象にする
- 実装例:
  - `input_hash` をキャッシュキーに採用
  - SQLite に結果を保存

### Model Routing（3軸マトリクス強化）

現行スコア 0-14 のみではなく、`タスク種別 × リスク × コスト` でモデルを選ぶ。

| タスク種別 | 推奨モデル | 目的 |
|-----------|-----------|------|
| 調査/検索 | Haiku | 最小コストで一次調査 |
| テンプレ生成 | Spark | 低コストで反復 |
| 実装 | SE / Codex 5.3 | 中コストで実装品質を確保 |
| レビュー/設計 | TL / Codex 5.4 | 高精度レビュー |
| フロント設計 | Opus | 表現品質重視 |

- 委譲前に推定費用を表示する（例: `推定 $X.XX`）

### Dynamic Context Pruning

- 長時間セッションで古い会話を動的に削除し、必要文脈のみ残す
- HELIX では `helix-codex --task` に渡す参照を最小化する
- 変更対象ファイル中心に限定し、全ファイル Read を避ける

### コスト追跡ダッシュボード設計

```text
helix log report cost:
  今日:    Opus $2.40 / Codex $1.80 / Sonnet $0.30 / Haiku $0.05
  今週:    $22.50（先週比 -15%）
  最適化:  キャッシュヒット率 62%、圧縮率 3.2x
```

---

## AI エージェントコスト追跡

helix-codex 委譲時のトークン使用量とコストを継続的に記録し、モデル選択を最適化する。

### トークン使用量の推定（委譲単位）

```text
input_tokens_est  = ceil(prompt文字数 / 3.2) + 添付コンテキスト補正
output_tokens_est = ceil(応答文字数 / 2.8)
total_tokens_est  = input_tokens_est + output_tokens_est
```

```text
補正例:
- 参照ファイル 1件ごとに +300
- diff 100行ごとに +180
- 長文ログ貼り付け時は実測優先
```

### モデル別コスト表（相対係数）

| モデル | 主用途 | 相対入力コスト | 相対出力コスト |
|--------|--------|----------------|----------------|
| Opus | 設計・難問解析 | 1.00 | 1.00 |
| Sonnet | テスト/文書生成 | 0.35 | 0.35 |
| Haiku | 軽量調査/一次レビュー | 0.08 | 0.08 |
| Codex 5.4 | TLレビュー・高難度実装 | 0.55 | 0.55 |
| Codex 5.3 | SE実装（スコア4+） | 0.28 | 0.28 |
| Codex 5.3 Spark | 軽微修正・高速反復 | 0.12 | 0.12 |

```
換算:
推定コスト = (input_tokens_est × 相対入力コスト) + (output_tokens_est × 相対出力コスト)
```

### プロジェクト単位の集計方法

```text
1. タスク完了ごとに usage レコードを1件保存
2. 日次: project_id + model ごとに合計
3. 週次: タスク種別（実装/レビュー/調査）で再集計
4. 月次: 予算上限と差分比較（見込み超過はモデル再配分）
```

```sql
SELECT project_id, model, SUM(input_tokens) AS in_tok, SUM(output_tokens) AS out_tok
FROM agent_cost_logs
WHERE created_at >= date('now', '-30 day')
GROUP BY project_id, model
ORDER BY project_id, model;
```

### コスト最適化ベストプラクティス

```
- 不要な委譲を減らす（同一質問の多重依頼を禁止）
- low risk は Spark/Haiku、high risk は 5.4/Opus に限定
- レビューは差分最小化して投入トークンを抑制
- 大規模ログ貼り付け前に要約してから委譲
- 失敗リトライは原因修正後に実施（無再考リトライ禁止）
```

### SQLite でのコストログ記録（`helix.db` 拡張提案）

```sql
CREATE TABLE IF NOT EXISTS agent_cost_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  model TEXT NOT NULL,
  role TEXT NOT NULL,
  input_tokens INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  estimated_cost REAL NOT NULL DEFAULT 0,
  status TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_cost_logs_project_created
  ON agent_cost_logs(project_id, created_at);
```

---

## AI セッション記録と再生

### セッションログの構造化記録

- タイムスタンプ付きアクションログを残す
- 入力/出力はハッシュ化またはマスキング（redacted）して保存する
- 使用ツール、実行時間、結果ステータスを1イベント単位で記録する

### Learning Engine 連携

- `helix learn` は成功セッションから recipe を生成する
- `helix publish` で再利用可能なセッションパターンを共有する
- 失敗セッションは failure recipe として分離し、再発防止に使う

### 記録フォーマット（JSONL）

```json
{"ts":"2026-04-04T12:00:00","action":"codex-review","input_hash":"a3f2","result":"approve","duration_ms":5200}
```

運用ルール:
- 1行=1アクション
- 機密値は保存しない（キー名・値の両方を検査）
- 再生時は `ts` 順に並べて依存順序を復元する

---

## 自己ベンチマーク（SWE-EVO コンセプト）

### コンセプト

HELIX のバージョン間で「前より良くなったか」を定量化し、改善を継続可能にする。

### 計測指標

| 指標 | 定義 | 観測ポイント |
|------|------|-------------|
| タスク成功率 | `helix learn` の recipe 成功率推移 | 週次・月次 |
| ゲート通過率 | G2-G7 の一発通過率推移 | ゲート別 |
| 手戻り回数 | `interrupt` / `CC` / `LPR` の発動回数推移 | タスク単位 |
| コスト効率 | トークン消費量 / 成果物数 の推移 | モデル別 |
| テスト品質 | Mutation Score の推移 | モジュール別 |
| ドキュメント品質 | textlint エラー数の推移 | 文書種別別 |

### ベンチマーク実行方法

1. SQLite（`helix.db` / `global.db`）から対象メトリクスを集計する
2. 週次/月次レポートをテンプレート化して自動生成する
3. `helix log report benchmark` を将来コマンドとして統合し、定期実行する

```sql
-- 例: 直近30日のゲート通過率（概念）
SELECT gate_name,
       SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) AS passed,
       COUNT(*) AS total
FROM gate_logs
WHERE created_at >= date('now', '-30 day')
GROUP BY gate_name;
```

### HELIX Learning Engine との統合

- recipe の `quality_score` 推移グラフを記録し、学習効果を可視化する
- promote された recipe 群の導入前後で、成功率改善効果を比較する

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
