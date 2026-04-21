---
name: system-design-sizing
description: システム設計の規模・スケーラビリティを見積もり、容量計画・ボトルネック特定・トレードオフ分析を行う。新規システム設計時や既存システムのスケール判断時、性能/可用性要件が絡む設計判断が必要なときに使う。
helix_layer: [L1, L2]
helix_gate: [G1.5, G2]
codex_role: tl
tier: 1
upstream: donnemartin/system-design-primer (MIT)
---

# System Design Sizing (システム設計サイジング)

## Overview

このスキルは、システム設計の初期段階で「どれくらいの負荷を、どの構成で、どこまで安全に扱うか」を短時間で見積もるための手順を提供する。donnemartin/system-design-primer を根拠に、容量計画、ボトルネック特定、CAP と可用性のトレードオフ整理を行い、HELIX の L2 設計書へ落とし込む。

## When to Use

- 新規システムの L1-L2 で、規模感と設計方針を早期に固めたいとき
- 「1M users」「10k QPS」「99.9% availability」など、数量要件が議論に出たとき
- DB、キャッシュ、キュー、ロードバランサの選定理由を説明可能にしたいとき
- 既存システムのスケール限界や次のボトルネックを評価したいとき
- `api-and-interface-design` と併せて、境界設計だけでなく負荷耐性も設計対象に含めたいとき
- `performance-optimization` の前段として、設計レベルの性能仮説を整理したいとき

**使わないケース**

- 単なる変更規模の見積もりだけが必要なとき: `helix-size` を使う
- 実装後の計測・チューニングが主目的なとき: `performance-optimization` を使う
- API 契約や公開インターフェースの安定性が主題なとき: `api-and-interface-design` を使う

## Core Process

### Step 1: ユースケース・制約・仮定の明確化

最初に「誰が / 何を / どれくらい」を数字で置く。最低限、DAU、ピーク同時接続、読み書き比率、データ保持期間、可用性目標、整合性要求を明文化する。

- Who: internal users / public consumers / batch workers / operators
- What: read-heavy feed / write-heavy transaction / search / analytics / messaging
- How much: DAU, peak QPS, object size, retention days, RPO, RTO
- Assumptions: traffic burst factor, cache hit ratio, replication lag tolerance

### Step 2: 高レベル設計

主要コンポーネントを粗く置き、トラフィックとデータの流れを文章か図で表す。ここでは精密さより、SPOF と責務境界が見えることを優先する。

典型スケッチ:

```text
Client -> DNS -> CDN -> Load Balancer -> App -> Cache -> DB
                                      -> Queue -> Worker -> Object Storage
```

### Step 3: コアコンポーネント深堀

負荷が集中しやすい箇所を対象に、DB 選定、キャッシュ方式、非同期化、ロードバランサ層を決める。すべてを最適化するのではなく、支配的コストを持つコンポーネントから順に判断する。

- DB: strong consistency が必要か、水平分割が必要か
- Cache: read latency を下げたいのか、DB 負荷を逃がしたいのか
- Async: user-facing latency を短縮したいのか、burst を平滑化したいのか
- Load balancing: L4 で十分か、L7 でルーティング制御が必要か

### Step 4: ボトルネック識別 → スケーリング戦略選択

ボトルネックを「CPU / memory / disk IOPS / network / lock / coordination / third-party dependency」に分解し、各ボトルネックに対して縦方向か横方向か、同期か非同期か、整合性をどこまで下げるかを決める。

- Read bottleneck: CDN / cache / replicas / denormalization
- Write bottleneck: sharding / queue / batching / partitioning
- Coordination bottleneck: id generation / leader election / lock contention
- Availability bottleneck: replication / fail-over / multi-region

## Capacity Planning (容量計画)

Back-of-the-envelope は厳密な見積もりではなく、設計の初期ミスを防ぐための現実チェックである。桁が合っていない設計は、詳細設計以前に破綻する。

### Powers of Two

| Unit | Approx Bytes | Exact Power of Two |
|------|--------------|--------------------|
| 1 KB | 10^3 | 2^10 = 1,024 |
| 1 MB | 10^6 | 2^20 = 1,048,576 |
| 1 GB | 10^9 | 2^30 = 1,073,741,824 |
| 1 TB | 10^12 | 2^40 = 1,099,511,627,776 |

### Latency Numbers Every Programmer Should Know

| Operation | Typical Latency | Relative Order |
|-----------|-----------------|----------------|
| L1 cache reference | 0.5 ns | fastest |
| Branch mispredict | 5 ns | L1 より遅い |
| L2 cache reference | 7 ns | CPU cache |
| Mutex lock/unlock | 100 ns | in-process sync |
| Main memory reference | 100 ns | RAM |
| 1 KB over 1 Gbps network | 10 us | local network transfer |
| SSD random read | 150 us | storage |
| Send packet same datacenter | 500 us | intra-DC network |
| Disk seek | 10 ms | HDD class |
| Round trip US-EU | 70-150 ms | WAN |

### QPS / 帯域 / ストレージの計算例

例: 1M DAU の Twitter 類似サービスを概算する。

- 1M DAU
- 1 user/day = 10 reads, 2 writes
- Daily reads = 10M
- Daily writes = 2M
- Average read payload = 20 KB
- Average write payload = 2 KB
- Peak factor = 5x

計算例:

```text
Average read QPS  = 10,000,000 / 86,400  ≒ 116
Peak read QPS     = 116 * 5              ≒ 580
Average write QPS = 2,000,000 / 86,400   ≒ 23
Peak write QPS    = 23 * 5               ≒ 115

Peak read bandwidth  = 580 * 20 KB ≒ 11.6 MB/s
Peak write bandwidth = 115 * 2 KB  ≒ 230 KB/s

Daily storage growth = 2,000,000 * 2 KB ≒ 4 GB/day
Annual raw storage   = 4 GB * 365       ≒ 1.46 TB/year
Replicated x3        = 4.38 TB/year
```

ここでの判断:

- QPS は中規模でも、保持期間とレプリカ係数でストレージは早く膨らむ
- 読み取り優勢なら cache / replica の費用対効果が高い
- 書き込みは低めでも、fan-out 戦略次第で内部 write amplification が発生する

## Performance vs Scalability vs Latency vs Throughput

### 定義と区別

- Performance: 単一リクエストや単一ユーザー視点での速さ、効率
- Scalability: 負荷増加時に性能を維持または合理的に劣化させられる性質
- Latency: 1 リクエスト完了までの時間
- Throughput: 単位時間あたりに処理できる仕事量

### 判断の基本

「単一ユーザーで遅い = Performance 問題」「高負荷で遅い = Scalability 問題」。両者は関連するが同義ではない。低 latency の実装でも、共有リソース競合が強ければ scale しない。

### トレードオフ表

| Focus | 改善策 | 得るもの | 失うもの |
|------|--------|----------|----------|
| Latency | cache, CDN, precompute | 応答時間短縮 | 一貫性、複雑性 |
| Throughput | batching, async, queue | 総処理量向上 | 個別 latency |
| Performance | algorithm, indexing, hot path optimization | 単発効率改善 | 実装コスト |
| Scalability | sharding, stateless app, partitioning | 負荷拡張性 | 運用複雑性 |

## CAP Theorem & Consistency Patterns

### CP / AP の選択基準

| Choice | 向くケース | 代表的な判断 |
|--------|------------|--------------|
| CP | 決済、在庫、重複禁止、権限判定 | 分断時は一部操作を止めても整合性を守る |
| AP | SNS feed、analytics、recommendation、activity log | 一時的不整合を許容しても応答継続を優先 |

### 一貫性パターン

| Pattern | 説明 | 向くケース |
|---------|------|-----------|
| Weak | 読み取り時に最新保証なし | counters, view counts |
| Eventual | 時間経過で収束 | feeds, caches, replicas |
| Strong | 直後 read で write が見える | balances, inventory |

### 可用性パターン

| Pattern | Variants | 特徴 |
|---------|----------|------|
| Fail-over | Active-Passive / Active-Active | 障害時の継続性を高める |
| Replication | Master-Slave / Master-Master | 可用性と読み取り分散を改善する |

### 可用性計算式

```text
Series availability   = A1 * A2 * A3
Parallel availability = 1 - ((1 - A1) * (1 - A2))
```

例:

```text
Two nodes, each 99.9% available
Parallel = 1 - (0.001 * 0.001) = 0.999999 = 99.9999%
```

独立故障を仮定した概算であり、共通障害要因を持つ場合はこの数字をそのまま信用しない。

## Architecture Components (アーキテクチャ構成要素)

| Component | Options | 主な用途 | 主なトレードオフ |
|-----------|---------|----------|------------------|
| DNS | Round-robin / Geo-based | endpoint 振り分け、地域誘導 | health check 粒度が粗い |
| CDN | Push / Pull | 静的配信、edge cache | invalidation と一貫性管理 |
| Load Balancer | L4 / L7 | 接続分散、TLS、routing | L7 は高機能だが高コスト |
| Reverse Proxy | SSL termination / static serving | 接続集約、静的配信、header 制御 | hop 増加、設定複雑化 |
| Application Layer | Monolith / Microservices / Service Discovery | ビジネスロジック分離 | 分散化で運用コスト増 |
| Database | RDBMS / NoSQL | 永続化、検索、整合性担保 | 柔軟性と整合性の交換 |

## Database Scaling Patterns

### Representative Patterns

- Master-Slave Replication: write 主系、read replica で read scaling
- Master-Master Replication: multi-writer、高可用性だが conflict 解決が難しい
- Federation: 機能単位で DB 分離し、責務境界を明確化
- Sharding: データを key ベースで水平分割し、書き込みと容量を分散
- Denormalization: join を減らして read を高速化し、write complexity を受け入れる

### SQL vs NoSQL 判定表

| 判断軸 | SQL 向き | NoSQL 向き |
|--------|----------|------------|
| Schema | 安定、厳格、関係強い | 可変、疎、急速に変わる |
| Transactions | 多い、厳密 | 限定的、最終的整合で可 |
| Query | ad-hoc、join 多い | key-value、document、wide-column |
| Scale | vertical + replica で足りる | early horizontal scale が必要 |
| Consistency | strong 必須 | eventual 許容 |

## Caching Strategies

| Strategy | 特徴 | トレードオフ | 用途 |
|----------|------|--------------|------|
| Cache-Aside | app が miss 時に DB 取得して cache へ格納 | cache miss 時の遅延、stale 管理 | read-heavy 一般用途 |
| Write-Through | write 時に cache と DB を同時更新 | write latency 増、整合維持しやすい | read after write 重視 |
| Write-Behind | まず cache に書き、後で DB 反映 | data loss と整合遅延リスク | write burst 吸収 |
| Refresh-Ahead | expire 前に先読み更新 | 無駄な更新が増える | hot key の latency 安定化 |

## Async & Messaging

同期処理に寄せすぎると、ユーザー latency とバックエンド負荷が直結する。非同期化は throughput と耐障害性を上げるが、順序性、再試行、重複処理、監視責務が増える。

- Message Queues: Redis, RabbitMQ, Amazon SQS
- Task Queues: Celery
- Back Pressure: consumer 処理能力を超える流入を検知し、drop / retry / throttle / shed load を設計する

判断の目安:

- Redis: 軽量、低遅延、単純キュー
- RabbitMQ: routing と ack が必要な業務処理
- Amazon SQS: managed 前提、運用負荷を減らしたいケース
- Celery: Python 系ワーカーのジョブ分散

## Communication Protocols

### TCP vs UDP

| Protocol | 特徴 | 用途 |
|----------|------|------|
| TCP | reliable, ordered, connection-oriented | HTTP, DB, internal RPC |
| UDP | low overhead, unordered, connectionless | streaming, gaming, telemetry |

### HTTP 動詞の冪等性

| Method | Idempotent | Notes |
|--------|------------|-------|
| GET | Yes | read-only |
| PUT | Yes | full replace |
| DELETE | Yes | repeated delete should converge |
| POST | No | create / action |
| PATCH | No | partial update, repeated apply may differ |

## HELIX 連携

- `helix-size` との違い: 本スキルは「システム設計規模」を扱い、`helix-size` は「変更規模」を扱う
- 本スキルの成果物は HELIX L2 設計書 `D-ARCH` に反映する
- API 境界が主要論点なら `api-and-interface-design` を併用する
- 実測やボトルネック改善フェーズに移ったら `performance-optimization` へ接続する
- より大きい設計判断が必要なら `helix-codex --role tl` に追加委譲する

## Common Rationalizations (よくある言い訳)

| 言い訳 | 実態 |
|--------|------|
| MVP なのでスケール設計は不要 | 本番運用時の再設計コストは初期設計より高い。最低限のサイジングは先に必要 |
| クラウドが勝手にスケールしてくれる | 自動スケーリングはボトルネック分析の代替ではない。DB、ロック、下流依存は自動では解決しない |
| 今はユーザーが少ないから後で考える | データモデルや整合性判断は後からの修正コストが高い |
| キャッシュを入れれば全部速くなる | cache は latency を隠せても、整合性と invalidation の複雑性を増やす |
| マイクロサービスにすればスケールする | 分散化はスケール手段の一つでしかなく、早すぎる分割は coordination cost を増やす |

## Red Flags

- QPS や容量の見積もりなしで DB 選定している
- 単一障害点 (SPOF) が明確でない
- CAP トレードオフの意識的な選択がない
- スケール時の再設計前提で設計している
- latency 問題と scalability 問題を区別せず議論している

## Verification

- [ ] ユースケース・制約・仮定が文書化されている
- [ ] QPS / ストレージ / 帯域の概算が数字で示されている
- [ ] 主要コンポーネント (LB / App / DB / Cache / Queue) が図で示されている
- [ ] ボトルネック候補と対策がリスト化されている
- [ ] CAP トレードオフの選択根拠が明示されている
- [ ] 出典: https://github.com/donnemartin/system-design-primer が参照されている
