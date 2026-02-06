---
name: ai-integration
description: ai-integration関連タスク時に使用
metadata:
  helix_layer: L3
  triggers:
    - LLM組み込み時
    - AIエージェント統合時
    - プロンプト設計時
  verification:
    - AI機能動作確認
    - レスポンス品質確認
compatibility:
  claude: true
  codex: true
---

# AI統合スキル（LLM/エージェント組み込み）

## 適用タイミング

このスキルは以下の場合に読み込む：
- AIエージェント開発時
- LLM API連携時
- RAG実装時
- マルチエージェント設計時

---

## 1. LLMルーティング

### ルーティング戦略

```
┌─────────────────────────────────────────┐
│           Router（振り分け）            │
├─────────────────────────────────────────┤
│ 入力解析 → 難易度判定 → モデル選択      │
└─────────────────────────────────────────┘
         ↓           ↓           ↓
    ┌────────┐  ┌────────┐  ┌────────┐
    │ Haiku  │  │ Sonnet │  │  Opus  │
    │ 軽量   │  │ 標準   │  │ 高度   │
    └────────┘  └────────┘  └────────┘
```

### 難易度判定基準

| レベル | 条件 | モデル | 例 |
|--------|------|--------|-----|
| **Low** | 単純Q&A、分類、抽出 | Haiku | FAQ回答、感情分析 |
| **Medium** | 生成、要約、変換 | Sonnet | 記事作成、コード生成 |
| **High** | 推論、分析、設計 | Opus | アーキテクチャ設計、複雑な判断 |

### 実装例

```python
from enum import Enum
from anthropic import Anthropic

class Difficulty(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ModelRouter:
    MODEL_MAP = {
        Difficulty.LOW: "claude-haiku-4-5-20251001",
        Difficulty.MEDIUM: "claude-sonnet-4-5-20250929",
        Difficulty.HIGH: "claude-opus-4-6-20260203",
    }
    
    def __init__(self):
        self.client = Anthropic()
    
    def classify_difficulty(self, prompt: str) -> Difficulty:
        """プロンプトの難易度を分類"""
        # キーワードベースの簡易判定
        high_keywords = ["設計", "アーキテクチャ", "分析", "戦略"]
        low_keywords = ["〜とは", "FAQ", "分類", "抽出"]
        
        if any(kw in prompt for kw in high_keywords):
            return Difficulty.HIGH
        if any(kw in prompt for kw in low_keywords):
            return Difficulty.LOW
        return Difficulty.MEDIUM
    
    def route(self, prompt: str, force_model: str = None) -> str:
        """適切なモデルにルーティング"""
        if force_model:
            model = force_model
        else:
            difficulty = self.classify_difficulty(prompt)
            model = self.MODEL_MAP[difficulty]
        
        response = self.client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
```

### LLMによる動的ルーティング

```python
ROUTING_PROMPT = """
以下のタスクの難易度を判定してください。

タスク: {task}

判定基準:
- LOW: 単純なQ&A、情報抽出、分類
- MEDIUM: 文章生成、要約、コード生成
- HIGH: 複雑な推論、分析、設計、マルチステップ

回答形式: LOW, MEDIUM, HIGH のいずれか1つだけ
"""

async def smart_route(task: str) -> str:
    # Haikuでルーティング判定（コスト最小）
    difficulty = await call_llm(
        model="claude-haiku-4-5-20251001",
        prompt=ROUTING_PROMPT.format(task=task)
    )
    
    model = MODEL_MAP[difficulty.strip()]
    return await call_llm(model=model, prompt=task)
```

---

## 2. ベクトル検索/Embedding

### アーキテクチャ

```
Document → Chunk → Embedding → Vector DB
                                  ↓
Query → Embedding → Similar Search → Results
```

### チャンキング戦略

| 戦略 | サイズ | 用途 |
|------|--------|------|
| 固定長 | 500-1000トークン | シンプル、汎用 |
| 文単位 | 文ごと | 精度重視 |
| 段落単位 | 段落ごと | 文脈保持 |
| セマンティック | 意味で分割 | 高精度 |

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 推奨設定
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,        # 約250トークン
    chunk_overlap=200,       # 文脈維持
    separators=["\n\n", "\n", "。", "、", " "]
)

chunks = splitter.split_text(document)
```

### Embeddingモデル比較（2026年）

| モデル | 次元 | 性能 | コスト | 用途 |
|--------|------|------|--------|------|
| OpenAI text-embedding-3-large | 3072 | 最高 | $0.13/1M | 高精度検索 |
| OpenAI text-embedding-3-small | 1536 | 高 | $0.02/1M | バランス |
| Cohere embed-v3 | 1024 | 高 | $0.10/1M | 多言語 |
| Voyage-3 | 1024 | 高 | $0.06/1M | コスパ良 |
| BGE-M3 | 1024 | 高 | 無料 | OSS |

### Vector DB比較

| DB | 特徴 | 用途 | コスト |
|----|------|------|--------|
| **Pinecone** | マネージド、簡単 | 本番環境 | 有料 |
| **Qdrant** | 高性能、OSS | 大規模 | 無料/有料 |
| **Weaviate** | マルチモーダル | 画像+テキスト | 無料/有料 |
| **Chroma** | 軽量、OSS | 開発、小規模 | 無料 |
| **pgvector** | PostgreSQL拡張 | 既存PG活用 | 無料 |

### 実装例（Qdrant）

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import openai

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(host="localhost", port=6333)
        self.collection = "documents"
        self.embedding_model = "text-embedding-3-small"
    
    def create_collection(self):
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(
                size=1536,
                distance=Distance.COSINE
            )
        )
    
    def embed(self, text: str) -> list[float]:
        response = openai.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    def add_documents(self, documents: list[dict]):
        points = []
        for i, doc in enumerate(documents):
            embedding = self.embed(doc["content"])
            points.append(PointStruct(
                id=i,
                vector=embedding,
                payload={"content": doc["content"], "metadata": doc.get("metadata", {})}
            ))
        
        self.client.upsert(
            collection_name=self.collection,
            points=points
        )
    
    def search(self, query: str, limit: int = 5) -> list[dict]:
        query_embedding = self.embed(query)
        
        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_embedding,
            limit=limit
        )
        
        return [
            {"content": r.payload["content"], "score": r.score}
            for r in results
        ]
```

---

## 3. RAG（Retrieval-Augmented Generation）

### RAGアーキテクチャ

```
┌─────────────────────────────────────────────┐
│                  RAG Pipeline                │
├─────────────────────────────────────────────┤
│  1. Query Expansion（クエリ拡張）           │
│     └─ 同義語、言い換え                     │
│                                             │
│  2. Retrieval（検索）                       │
│     ├─ Sparse: BM25, TF-IDF                │
│     └─ Dense: Vector Search                 │
│                                             │
│  3. Reranking（再ランキング）               │
│     └─ Cross-encoder で精度向上            │
│                                             │
│  4. Generation（生成）                      │
│     └─ コンテキスト + クエリ → LLM          │
└─────────────────────────────────────────────┘
```

### RAG実装例

```python
class RAGPipeline:
    def __init__(self, vector_store: VectorStore, llm_client):
        self.vector_store = vector_store
        self.llm = llm_client
    
    def retrieve(self, query: str, k: int = 5) -> list[str]:
        """関連文書を検索"""
        results = self.vector_store.search(query, limit=k)
        return [r["content"] for r in results if r["score"] > 0.7]
    
    def generate(self, query: str, contexts: list[str]) -> str:
        """コンテキストを使って回答生成"""
        context_text = "\n\n---\n\n".join(contexts)
        
        prompt = f"""以下のコンテキストを参考に、質問に回答してください。
コンテキストに情報がない場合は「情報がありません」と回答してください。

## コンテキスト
{context_text}

## 質問
{query}

## 回答
"""
        
        response = self.llm.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    def query(self, question: str) -> str:
        """RAGパイプライン実行"""
        # 1. 検索
        contexts = self.retrieve(question)
        
        if not contexts:
            return "関連する情報が見つかりませんでした。"
        
        # 2. 生成
        answer = self.generate(question, contexts)
        
        return answer
```

### Hybrid Search（BM25 + Vector）

```python
from rank_bm25 import BM25Okapi

class HybridSearch:
    def __init__(self, documents: list[str], vector_store: VectorStore):
        # BM25用
        tokenized = [doc.split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized)
        self.documents = documents
        
        # Vector用
        self.vector_store = vector_store
    
    def search(self, query: str, k: int = 5, alpha: float = 0.5) -> list[str]:
        """Hybrid検索: alpha=0.5 で BM25 と Vector を均等に"""
        
        # BM25スコア
        bm25_scores = self.bm25.get_scores(query.split())
        
        # Vectorスコア
        vector_results = self.vector_store.search(query, limit=k*2)
        vector_scores = {r["content"]: r["score"] for r in vector_results}
        
        # スコア統合
        combined = []
        for i, doc in enumerate(self.documents):
            bm25_score = bm25_scores[i] / max(bm25_scores)  # 正規化
            vec_score = vector_scores.get(doc, 0)
            
            final_score = alpha * bm25_score + (1 - alpha) * vec_score
            combined.append((doc, final_score))
        
        # 上位k件
        combined.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in combined[:k]]
```

---

## 4. コンテキスト管理

### コンテキストウィンドウ

| モデル | 入力上限 | 出力上限 | 推奨使用量 |
|--------|---------|---------|-----------|
| Claude Opus 4.6 | 200K | 32K | 〜150K |
| Claude Sonnet 4.5 | 200K | 64K | 〜150K |
| Claude Haiku 4.5 | 200K | 64K | 〜150K |
| GPT-4o | 128K | 16K | 〜100K |
| Gemini 2.0 Pro | 2M | 8K | 〜1.5M |

### コンテキスト圧縮戦略

```python
class ContextManager:
    def __init__(self, max_tokens: int = 150000):
        self.max_tokens = max_tokens
        self.messages = []
    
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        self._compress_if_needed()
    
    def _compress_if_needed(self):
        """コンテキストが上限を超えたら圧縮"""
        total = self._count_tokens()
        
        if total > self.max_tokens:
            # 戦略1: 古いメッセージを要約
            self._summarize_old_messages()
            
            # 戦略2: 中間メッセージを削除（最初と最後を保持）
            # self._trim_middle_messages()
    
    def _summarize_old_messages(self):
        """古いメッセージを要約に置き換え"""
        if len(self.messages) < 10:
            return
        
        # 最初の5メッセージを要約
        old_messages = self.messages[:5]
        summary = self._create_summary(old_messages)
        
        # 要約で置き換え
        self.messages = [
            {"role": "system", "content": f"過去の会話要約: {summary}"}
        ] + self.messages[5:]
    
    def _create_summary(self, messages: list) -> str:
        """メッセージを要約（Haikuで実行）"""
        content = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
        response = anthropic.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"以下の会話を100語以内で要約:\n{content}"
            }]
        )
        return response.content[0].text
```

### 動的コンテキスト選択

```python
def select_relevant_context(query: str, available_contexts: list[dict], max_tokens: int = 50000) -> list[dict]:
    """クエリに関連するコンテキストを動的に選択"""
    
    # 関連度スコアリング
    scored = []
    for ctx in available_contexts:
        relevance = calculate_relevance(query, ctx["content"])
        scored.append({**ctx, "relevance": relevance})
    
    # 関連度順にソート
    scored.sort(key=lambda x: x["relevance"], reverse=True)
    
    # トークン上限まで追加
    selected = []
    total_tokens = 0
    
    for ctx in scored:
        tokens = count_tokens(ctx["content"])
        if total_tokens + tokens > max_tokens:
            break
        selected.append(ctx)
        total_tokens += tokens
    
    return selected
```

---


---

## 応用パターン

以下は references/advanced.md を参照:
- キャッシュ戦略
- 並列処理
- トークントラッカー
- API料金早見表

---

## チェックリスト

### LLM統合開発時

```
[ ] モデルルーティング設計
[ ] コンテキスト管理設計
[ ] キャッシュ戦略設計
[ ] コスト見積もり
[ ] トークン追跡実装
[ ] エラーハンドリング
[ ] レート制限対策
```

### RAG実装時

```
[ ] チャンキング戦略決定
[ ] Embeddingモデル選定
[ ] Vector DB選定
[ ] 検索精度テスト
[ ] Reranking検討
```
