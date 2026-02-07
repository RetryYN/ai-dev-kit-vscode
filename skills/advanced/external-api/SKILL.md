---
name: external-api
description: 外部API連携で、アダプターパターン・リトライ・サーキットブレーカーによる堅牢化設計を提供
metadata:
  helix_layer: L3
  triggers:
    - 外部API連携時
    - OAuth実装時
    - Webhook実装時
  verification:
    - "外部API呼び出し: 正常レスポンス（HTTP 200 + スキーマ一致）"
    - "リトライ・サーキットブレーカー: 障害時テスト通過"
    - "タイムアウト設定: 全外部呼び出しに設定済み（≤5s）"
compatibility:
  claude: true
  codex: true
---

# 外部API連携スキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- 外部サービス連携時
- OAuth実装時
- Webhook実装時

---

## 1. 外部API連携の基本

### 設計原則

```
1. 疎結合
   - 外部サービスへの依存を最小化
   - アダプターパターンで抽象化

2. 耐障害性
   - タイムアウト設定
   - リトライ処理
   - サーキットブレーカー

3. 可観測性
   - リクエスト/レスポンスログ
   - レイテンシ計測
   - エラー率監視
```

### アダプターパターン

```python
from abc import ABC, abstractmethod

# インターフェース
class PaymentGateway(ABC):
    @abstractmethod
    async def charge(self, amount: int, token: str) -> PaymentResult:
        pass
    
    @abstractmethod
    async def refund(self, payment_id: str) -> RefundResult:
        pass

# Stripe実装
class StripeGateway(PaymentGateway):
    def __init__(self, api_key: str):
        self.client = stripe.Client(api_key)
    
    async def charge(self, amount: int, token: str) -> PaymentResult:
        result = await self.client.charges.create(
            amount=amount,
            currency="jpy",
            source=token
        )
        return PaymentResult(
            id=result.id,
            status="success" if result.paid else "failed"
        )

# 利用側は抽象に依存
class OrderService:
    def __init__(self, payment: PaymentGateway):
        self.payment = payment
    
    async def process_order(self, order: Order):
        result = await self.payment.charge(order.total, order.payment_token)
        # ...
```

---

## 2. HTTPクライアント実装

### 基本実装

```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

class APIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(10.0, connect=5.0)
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> dict:
        try:
            response = await self.client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # エラーハンドリング
            if e.response.status_code == 429:
                raise RateLimitError()
            elif e.response.status_code >= 500:
                raise ExternalServiceError()
            raise
    
    async def get(self, path: str, params: dict = None) -> dict:
        return await self.request("GET", path, params=params)
    
    async def post(self, path: str, data: dict) -> dict:
        return await self.request("POST", path, json=data)
    
    async def close(self):
        await self.client.aclose()
```

### タイムアウト設定

```python
# 推奨タイムアウト値
TIMEOUTS = {
    "connect": 5.0,      # 接続確立
    "read": 30.0,        # レスポンス読み取り
    "write": 10.0,       # リクエスト送信
    "pool": 5.0,         # コネクションプール取得
}

# 用途別
TIMEOUT_PRESETS = {
    "fast_api": httpx.Timeout(5.0, connect=2.0),     # 高速API
    "standard": httpx.Timeout(30.0, connect=5.0),    # 標準
    "slow_api": httpx.Timeout(120.0, connect=10.0),  # 遅いAPI（PDF生成等）
}
```

---

## 3. リトライとサーキットブレーカー

### リトライ戦略

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

# Exponential Backoff
@retry(
    stop=stop_after_attempt(3),                    # 最大3回
    wait=wait_exponential(multiplier=1, max=60),   # 1, 2, 4, 8... 秒
    retry=retry_if_exception_type((
        httpx.TimeoutException,
        httpx.NetworkError,
    ))
)
async def call_external_api():
    pass

# リトライ対象のHTTPステータス
RETRYABLE_STATUS_CODES = {
    408,  # Request Timeout
    429,  # Too Many Requests
    500,  # Internal Server Error
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
}
```

### サーキットブレーカー

```python
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # 正常（リクエスト通過）
    OPEN = "open"          # 遮断（リクエスト拒否）
    HALF_OPEN = "half_open"  # 試行中

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
    
    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # タイムアウト後はHALF_OPENに遷移
            if self._is_recovery_timeout_elapsed():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.half_open_max_calls
        
        return False
    
    def record_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def _is_recovery_timeout_elapsed(self) -> bool:
        if not self.last_failure_time:
            return True
        return datetime.now() > self.last_failure_time + timedelta(seconds=self.recovery_timeout)
```

---

## 4. OAuth/Webhook実装

→ 詳細は `references/oauth-webhook.md` を参照

---

## 5. レート制限対応

### レート制限実装

```python
import asyncio
from collections import deque
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = deque()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        async with self._lock:
            now = datetime.now()
            
            # 古いリクエストを削除
            while self.requests and self.requests[0] < now - self.window:
                self.requests.popleft()
            
            # レート制限チェック
            if len(self.requests) >= self.max_requests:
                wait_time = (self.requests[0] + self.window - now).total_seconds()
                await asyncio.sleep(wait_time)
            
            self.requests.append(now)

# 使用例
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)

async def call_api():
    await rate_limiter.acquire()
    return await client.get("/api/data")
```

---

## チェックリスト

### 連携前

```
[ ] API仕様を確認
[ ] 認証方式を確認
[ ] レート制限を確認
[ ] エラーコードを確認
```

### 実装時

```
[ ] タイムアウト設定
[ ] リトライ実装
[ ] エラーハンドリング
[ ] ログ出力
[ ] 監視設定
```

### 運用時

```
[ ] レスポンス時間監視
[ ] エラー率監視
[ ] レート制限監視
[ ] 認証情報の更新
```
