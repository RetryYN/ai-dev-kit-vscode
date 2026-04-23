> 目的: 技術選定の原則・比較枠組み・推奨スタックを確認するときに参照する

## 適用タイミング

このスキルは以下の場合に読み込む：
- 新規プロジェクト技術選定時
- 技術スタック見直し時
- ライブラリ選定時

---

## 1. 技術選定の原則

### 基本方針

```
1. 要件から逆算する
   - 技術ありきで考えない
   - 解決したい問題は何か

2. 退屈な技術を選ぶ
   - 枯れた技術 > 最新技術
   - 実績 > 話題性

3. チームを考慮する
   - 学習コスト
   - 既存スキル
   - 採用市場

4. 長期視点で考える
   - 5年後も使えるか
   - メンテナンス性
   - コミュニティの活発さ
```

### 選定基準

| 観点 | 確認項目 |
|------|---------|
| 機能要件 | 必要な機能を満たせるか |
| 非機能要件 | 性能、セキュリティ、スケーラビリティ |
| 成熟度 | 安定性、バグの少なさ |
| コミュニティ | 活発さ、ドキュメント、サポート |
| 学習コスト | チームが習得できるか |
| 採用 | エンジニアを採用できるか |
| コスト | ライセンス、インフラ、運用 |
| 将来性 | 継続的に開発されるか |

---

## 2. 比較フレームワーク

### 評価マトリクス

```markdown
## 技術選定: データベース

| 観点 | 重み | PostgreSQL | MySQL | MongoDB |
|------|------|-----------|-------|---------|
| 機能要件 | 30% | 5 | 4 | 3 |
| 性能 | 20% | 4 | 5 | 4 |
| 運用性 | 20% | 4 | 5 | 3 |
| チームスキル | 15% | 5 | 4 | 2 |
| コスト | 15% | 5 | 5 | 4 |
| **合計** | 100% | **4.5** | **4.5** | **3.2** |

### 決定: PostgreSQL
理由:
- JSON対応が優れている
- チームに経験者が多い
- 拡張性が高い
```

### SWOT分析

```markdown
## Next.js SWOT分析

| Strengths（強み） | Weaknesses（弱み） |
|------------------|-------------------|
| SSR/SSG対応 | 学習曲線がある |
| React互換 | Vercel依存の懸念 |
| 豊富なエコシステム | 設定が複雑になりがち |

| Opportunities（機会） | Threats（脅威） |
|---------------------|-----------------|
| App Routerの進化 | 競合フレームワーク |
| エッジ対応強化 | React自体の変化 |
```

---

## 3. 技術スタック推奨（2026年）

### Webアプリケーション

| レイヤー | 推奨 | 代替 |
|---------|------|------|
| Frontend | Next.js 15 | Remix, Nuxt |
| Language | TypeScript | - |
| Styling | Tailwind CSS | CSS Modules |
| State | TanStack Query | SWR, Zustand |
| Form | React Hook Form + Zod | - |
| Backend | FastAPI | NestJS, Go |
| ORM | Prisma | Drizzle, SQLAlchemy |
| Database | PostgreSQL | MySQL |
| Cache | Redis | Memcached |
| Search | Elasticsearch | Meilisearch |

### AIアプリケーション

| 用途 | 推奨 |
|------|------|
| LLM API | Anthropic Claude, OpenAI |
| Embedding | OpenAI, Voyage, Cohere |
| Vector DB | Qdrant, Pinecone, pgvector |
| Orchestration | LangChain, LlamaIndex |
| Monitoring | LangSmith, Weights & Biases |

### インフラ

| 用途 | 推奨 |
|------|------|
| クラウド | AWS, GCP |
| コンテナ | Docker, Kubernetes |
| CI/CD | GitHub Actions |
| 監視 | Datadog, Grafana |
| ログ | Loki, CloudWatch |

---

