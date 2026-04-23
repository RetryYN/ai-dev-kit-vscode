## 5. キャッシュ戦略

### キャッシュレイヤー

```
┌─────────────────────────────────────────┐
│  L1: インメモリ（LRU）                  │
│  └─ 超高速、容量小                      │
├─────────────────────────────────────────┤
│  L2: Redis                              │
│  └─ 高速、共有可能                      │
├─────────────────────────────────────────┤
│  L3: Embedding Cache（Vector DB）       │
│  └─ 類似クエリでヒット                  │
└─────────────────────────────────────────┘
```

### 実装例

```python
import hashlib
import json
from functools import lru_cache
import redis

class LLMCache:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379)
        self.ttl = 3600 * 24  # 24時間
    
    def _make_key(self, model: str, messages: list, **kwargs) -> str:
        """キャッシュキー生成"""
        data = json.dumps({"model": model, "messages": messages, **kwargs}, sort_keys=True)
        return f"llm:{hashlib.sha256(data.encode()).hexdigest()}"
    
    def get(self, model: str, messages: list, **kwargs) -> str | None:
        """キャッシュ取得"""
        key = self._make_key(model, messages, **kwargs)
        cached = self.redis.get(key)
        return cached.decode() if cached else None
    
    def set(self, model: str, messages: list, response: str, **kwargs):
        """キャッシュ保存"""
        key = self._make_key(model, messages, **kwargs)
        self.redis.setex(key, self.ttl, response)
    
    def cached_call(self, client, model: str, messages: list, **kwargs) -> str:
        """キャッシュ付きLLM呼び出し"""
        # キャッシュ確認
        cached = self.get(model, messages, **kwargs)
        if cached:
            return cached
        
        # LLM呼び出し
        response = client.messages.create(
            model=model,
            messages=messages,
            **kwargs
        )
        result = response.content[0].text
        
        # キャッシュ保存
        self.set(model, messages, result, **kwargs)
        
        return result
```

### Semantic Cache（類似クエリキャッシュ）

```python
class SemanticCache:
    def __init__(self, vector_store: VectorStore, threshold: float = 0.95):
        self.vector_store = vector_store
        self.threshold = threshold
        self.cache = {}  # query_hash -> response
    
    def get(self, query: str) -> str | None:
        """類似クエリのキャッシュを検索"""
        results = self.vector_store.search(query, limit=1)
        
        if results and results[0]["score"] >= self.threshold:
            cache_key = results[0]["content"]
            return self.cache.get(cache_key)
        
        return None
    
    def set(self, query: str, response: str):
        """キャッシュ保存"""
        self.vector_store.add_documents([{"content": query}])
        self.cache[query] = response
```

---

## 6. 並列処理

### 並列実行パターン

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ParallelLLM:
    def __init__(self, client, max_workers: int = 5):
        self.client = client
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def parallel_calls(self, prompts: list[str], model: str) -> list[str]:
        """複数プロンプトを並列実行"""
        tasks = [
            self._call_async(prompt, model)
            for prompt in prompts
        ]
        return await asyncio.gather(*tasks)
    
    async def _call_async(self, prompt: str, model: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._call_sync,
            prompt,
            model
        )
    
    def _call_sync(self, prompt: str, model: str) -> str:
        response = self.client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

# 使用例
> 目的: LLM統合のRAG・評価・運用設計を進める際の実装指針として参照。

async def main():
    llm = ParallelLLM(anthropic_client)
    
    prompts = [
        "記事Aを要約して",
        "記事Bを要約して",
        "記事Cを要約して",
    ]
    
    results = await llm.parallel_calls(prompts, "claude-sonnet-4-5-20250929")
    print(results)
```

### バッチ処理

```python
async def batch_process(items: list, batch_size: int = 10, model: str = "claude-haiku-4-5-20251001"):
    """バッチで処理してレート制限を回避"""
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        # 並列実行
        batch_results = await parallel_calls(batch, model)
        results.extend(batch_results)
        
        # レート制限対策
        await asyncio.sleep(1)
    
    return results
```

---

## 7. トークントラッカー

### トークン計算

```python
import tiktoken

class TokenTracker:
    def __init__(self):
        # Claude用の概算（tiktoken cl100k_baseで近似）
        self.encoder = tiktoken.get_encoding("cl100k_base")
        self.usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_cost": 0.0
        }
    
    # 料金表（2026年2月時点）
    PRICING = {
        "claude-opus-4-6-20260203": {"input": 15.0, "output": 75.0},
        "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
        "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    }
    
    def count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))
    
    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """コスト見積もり（$/1M tokens）"""
        pricing = self.PRICING.get(model, {"input": 3.0, "output": 15.0})
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def track(self, model: str, input_text: str, output_text: str):
        """使用量を追跡"""
        input_tokens = self.count_tokens(input_text)
        output_tokens = self.count_tokens(output_text)
        cost = self.estimate_cost(model, input_tokens, output_tokens)
        
        self.usage["input_tokens"] += input_tokens
        self.usage["output_tokens"] += output_tokens
        self.usage["total_cost"] += cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost
        }
    
    def get_report(self) -> dict:
        return self.usage
```

### 使用量ダッシュボード

```python
class UsageDashboard:
    def __init__(self):
        self.tracker = TokenTracker()
        self.history = []
    
    def log_request(self, model: str, prompt: str, response: str, metadata: dict = None):
        usage = self.tracker.track(model, prompt, response)
        
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            **usage,
            "metadata": metadata
        })
    
    def daily_report(self) -> dict:
        today = datetime.now().date()
        today_requests = [
            r for r in self.history
            if datetime.fromisoformat(r["timestamp"]).date() == today
        ]
        
        return {
            "date": str(today),
            "requests": len(today_requests),
            "input_tokens": sum(r["input_tokens"] for r in today_requests),
            "output_tokens": sum(r["output_tokens"] for r in today_requests),
            "cost": sum(r["cost"] for r in today_requests),
            "by_model": self._group_by_model(today_requests)
        }
    
    def _group_by_model(self, requests: list) -> dict:
        result = {}
        for r in requests:
            model = r["model"]
            if model not in result:
                result[model] = {"requests": 0, "cost": 0}
            result[model]["requests"] += 1
            result[model]["cost"] += r["cost"]
        return result
```

---

## 8. API料金早見表（2026年2月）

### Anthropic Claude

| モデル | 入力 ($/1M) | 出力 ($/1M) | コンテキスト |
|--------|------------|------------|-------------|
| Claude Opus | $15.00 | $75.00 | 200K |
| Claude Sonnet | $3.00 | $15.00 | 200K |
| Claude Haiku 4.5 | $0.80 | $4.00 | 200K |

### OpenAI

| モデル | 入力 ($/1M) | 出力 ($/1M) | コンテキスト |
|--------|------------|------------|-------------|
| GPT-4o | $2.50 | $10.00 | 128K |
| GPT-4o mini | $0.15 | $0.60 | 128K |
| GPT-4 Turbo | $10.00 | $30.00 | 128K |
| o1 | $15.00 | $60.00 | 200K |
| o1-mini | $3.00 | $12.00 | 128K |

### Google

| モデル | 入力 ($/1M) | 出力 ($/1M) | コンテキスト |
|--------|------------|------------|-------------|

### Embedding

| モデル | 料金 ($/1M tokens) | 次元 |
|--------|-------------------|------|
| text-embedding-3-large | $0.13 | 3072 |
| text-embedding-3-small | $0.02 | 1536 |
| Voyage-3 | $0.06 | 1024 |
| Cohere embed-v3 | $0.10 | 1024 |

### コスト比較例（1万リクエスト/月）

| シナリオ | Haiku 4.5 | Sonnet | Opus |
|---------|-------|--------|------|
| 短い応答（500 in/200 out） | $6 | $22 | $120 |
| 中程度（2K in/1K out） | $20 | $75 | $405 |
| 長い応答（5K in/2K out） | $48 | $180 | $975 |

---

## 9. Web検索ルール

### 検索が必要な場面

```
✅ 必ずWeb検索（2026年で検索）
- LLM APIの最新料金
- 最新のベストプラクティス
- 新しいライブラリ/フレームワーク
- セキュリティ脆弱性情報
- 認証/OAuth実装方法

❌ 検索不要
- 基本的なアルゴリズム
- 安定した数学/統計手法
- 古典的なデザインパターン
```

### 検索指示テンプレート

```
「{{トピック}}について、2026年の最新情報を検索して実装に反映して」
「{{ライブラリ}}の最新バージョンのAPIを確認して」
「{{サービス}}の現在の料金体系を調べて」
```

---

