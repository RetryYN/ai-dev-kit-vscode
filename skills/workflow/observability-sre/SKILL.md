---
name: observability-sre
description: SLO/SLI設計・アラート戦略・ダッシュボード構築に加え、リアルタイム監視設計の可観測性指針を提供
metadata:
  helix_layer: L7
  triggers:
    - 監視設計時
    - SLO/SLI定義時
    - アラート設計時
    - ダッシュボード構築時
  verification:
    - "SLO定義: availability/latency/correctness 3種 定義済み（欠落 0件）"
    - "エラーバジェット計算済み（SLO 99.9% = 月43.2分許容）"
    - "アラートルール設定（P1: SLO違反, P2: バジェット50%超）"
    - "可観測性の三本柱実装（Metrics/Logs/Traces）"
    - "ダッシュボード構築（L1-L4の4レイヤー）"
compatibility:
  claude: true
  codex: true
---

# 可観測性・SREスキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- 監視基盤設計時
- SLO/SLI/SLA定義時
- アラート戦略策定時
- ダッシュボード設計時
- オンコール体制構築時

---

## 1. 可観測性の三本柱

### Metrics / Logs / Traces

```
┌─────────────────────────────────────────────┐
│           可観測性（Observability）           │
├───────────┬───────────┬─────────────────────┤
│  Metrics  │   Logs    │      Traces         │
│  数値指標  │  イベント │  リクエスト追跡      │
│           │  ログ     │                     │
│  "何が"   │  "なぜ"   │  "どこで"           │
│  起きたか  │  起きたか │  起きたか           │
└───────────┴───────────┴─────────────────────┘
     ↓            ↓             ↓
 Prometheus   Loki/ELK     Jaeger/Tempo
 Datadog      CloudWatch   OpenTelemetry
```

### ツール選定

| カテゴリ | OSS | マネージド | 用途 |
|---------|-----|-----------|------|
| Metrics | Prometheus + Grafana | Datadog, CloudWatch | 数値監視 |
| Logs | Loki, ELK Stack | CloudWatch Logs, Datadog | ログ集約 |
| Traces | Jaeger, Tempo | Datadog APM, X-Ray | 分散トレーシング |
| 統合 | OpenTelemetry | Datadog, New Relic | 全統合 |

---

## 2. SLO/SLI/SLA設計

### 用語定義

| 用語 | 意味 | 例 |
|------|------|-----|
| **SLI** (Service Level Indicator) | 測定指標 | レスポンス200ms以内の割合 |
| **SLO** (Service Level Objective) | 目標値 | 99.9%のリクエストが200ms以内 |
| **SLA** (Service Level Agreement) | 契約 | SLO未達時に返金 |

### SLO設計テンプレート

```yaml
service: user-api
slos:
  - name: availability
    description: APIが正常に応答する割合
    sli:
      type: availability
      good_event: "status_code < 500"
      total_event: "all requests"
    target: 99.9%
    window: 30d
    error_budget: 0.1%  # 月43.2分のダウンタイム

  - name: latency
    description: レスポンス時間
    sli:
      type: latency
      threshold: 200ms
      percentile: p99
    target: 99.5%
    window: 30d

  - name: correctness
    description: 正しいレスポンスの割合
    sli:
      type: correctness
      good_event: "response matches expected schema"
    target: 99.99%
    window: 30d
```

### エラーバジェット

```
エラーバジェット = 1 - SLO目標

例: SLO 99.9%（30日間）
  エラーバジェット = 0.1%
  許容ダウンタイム = 30日 × 24時間 × 0.1% = 43.2分

バジェット消費状況:
  ├─ 0-50%: 通常開発（機能追加優先）
  ├─ 50-75%: 注意（リスクの高いリリース控える）
  ├─ 75-100%: 警戒（信頼性改善に注力）
  └─ 100%超: 凍結（信頼性改善のみ）
```

---

## 3. メトリクス設計

### REDメソッド（サービス向け）

| 指標 | 意味 | 例 |
|------|------|-----|
| **R**ate | リクエスト数/秒 | `http_requests_total` |
| **E**rrors | エラー率 | `http_errors_total / http_requests_total` |
| **D**uration | レイテンシ | `http_request_duration_seconds` |

### USEメソッド（リソース向け）

| 指標 | 意味 | 例 |
|------|------|-----|
| **U**tilization | 使用率 | CPU 80% |
| **S**aturation | 飽和度 | キュー長 |
| **E**rrors | エラー数 | ディスクエラー |

→ Prometheus実装例は `references/implementations.md` を参照

---

## 4. アラート設計

### アラートレベル

| レベル | 条件 | 対応 | 通知先 |
|--------|------|------|--------|
| **P1 Critical** | SLO違反、サービスダウン | 即時対応 | PagerDuty + Slack |
| **P2 Warning** | エラーバジェット50%超 | 当日対応 | Slack |
| **P3 Info** | 異常傾向検出 | 計画対応 | Slack (低優先) |

→ アラートルール例・Grafana構成例は `references/implementations.md` を参照

### アラート設計原則

```
□ アクション可能か（対応方法が明確）
□ 誤報率は低いか（ノイズにならない）
□ 適切な粒度か（細かすぎない）
□ エスカレーションパスがあるか
□ ランブック（対応手順書）があるか
```

---

## 5. ダッシュボード設計

### レイヤー別ダッシュボード

```
Level 1: サービス概要（経営層向け）
  └─ SLO達成率、エラーバジェット、障害数

Level 2: サービス詳細（チーム向け）
  └─ RED指標、レイテンシ分布、エラー分類

Level 3: インフラ（SRE向け）
  └─ USE指標、ノード状態、リソース使用率

Level 4: デバッグ（オンコール向け）
  └─ トレース、ログ検索、依存関係マップ
```

---

## 6. OpenTelemetry統合

→ セットアップ・実装例は `references/implementations.md` を参照

---

## 7. 劣化レベルとSLO対応表（Helix Policy）

> 出典: docs/archive/v-model-reference-cycle-v2.md §運用ポリシー5。品質劣化の段階別定義と対応アクション。
>
> **L7 デプロイフェーズでの参照**: L7.3（本番安定性ゲート）はこの劣化レベル表を**唯一の合否基準**として使用する。
> 15分の観測ウィンドウ（Canary は30分）で劣化レベル `none` を維持すれば L7.3 pass。
> 詳細は `tools/ai-coding/references/layer-interface.md §L7.3` を参照。

### SLOメトリクス

| メトリクス | 説明 |
|-----------|------|
| availability | 可用性（%） |
| p95_latency_ms | 95パーセンタイル応答時間（ms） |
| error_rate_percent | エラー率（%） |
| task_success_rate_percent | タスク成功率（%） |
| cost_overrun_percent | コスト超過率（%） |

### 劣化レベル別閾値

| レベル | availability | p95_latency | error_rate | success_rate | cost_overrun | 対応アクション |
|--------|-------------|-------------|------------|-------------|-------------|---------------|
| none | ≥99.9% | ≤200ms | ≤0.5% | ≥98.0% | ≤5% | 継続 |
| low | ≥99.5% | ≤400ms | ≤1.0% | ≥97.0% | ≤10% | 次サイクルで最適化 |
| medium | ≥99.0% | ≤800ms | ≤2.0% | ≥95.0% | ≤20% | 調査開始 + 軽減策適用 |
| high | ≥98.0% | ≤1500ms | ≤5.0% | ≥90.0% | ≤35% | 即時軽減 + ロールバック検討 + 人間通知 |
| critical | <98.0% | >1500ms | >5.0% | <90.0% | >35% | 自動停止 + ロールバック + 人間即時通知 |

### 劣化検知時のアクションフロー

```
劣化検知
  │
  ├─ none/low → ログ記録のみ → 次サイクルで対応
  │
  ├─ medium → 調査チケット作成 → 軽減策適用 → 効果確認
  │
  ├─ high → 即時対応 → ロールバック検討 → 人間通知 → 根本原因調査
  │
  └─ critical → 自動停止 → ロールバック実行 → 人間即時通知 → インシデント対応
```

---

## SLO/SLI 設計テンプレート

### SLI 定義テンプレート

```yaml
service: sample-api
slis:
  availability:
    good_event: "HTTP status < 500"
    total_event: "all requests"
  latency:
    metric: "p95 response time"
    threshold_ms: 300
  throughput:
    metric: "requests per second"
    target_rps: 120
  error_rate:
    metric: "5xx / total requests"
    threshold_percent: 0.5
```

### SLO 設定ガイド（30日換算の目安）

| SLO | 許容ダウンタイム |
|-----|------------------|
| 99.99% | 約4.3分/月 |
| 99.9% | 約43.2分/月 |
| 99.0% | 約7.2時間/月 |
| 98.8% | 約8.7時間/月 |

### エラーバジェット運用

```text
error_budget = 1 - SLO

運用基準:
- 消費 < 50%: 通常開発
- 50%〜75%: リスクの高い変更を抑制
- 75%〜100%: 信頼性改善を優先
- 100%超: 機能開発を凍結し復旧・再発防止を優先
```

### アラート設計（閾値ベース vs バーンレート）

- 閾値ベース:
  - 例: `error_rate > 2%` が 5 分継続
  - 単純で導入しやすいが、短時間の急劣化を見逃す場合がある
- バーンレート:
  - 例: 1時間窓でバジェット消費速度が `14x` 超過
  - SLO違反リスクを早期に検知しやすい

---

## 構造化ログ設計

### JSON ログフォーマット標準

```json
{
  "timestamp": "2026-04-04T12:00:00Z",
  "level": "INFO",
  "message": "request completed",
  "context": {
    "service": "sample-api",
    "path": "/v1/items",
    "status_code": 200,
    "duration_ms": 42
  },
  "trace_id": "trc-1234abcd"
}
```

### ログレベル使い分け

- `DEBUG`: 開発時の詳細調査情報
- `INFO`: 正常系の主要イベント
- `WARN`: 要注意だが継続可能な異常
- `ERROR`: リクエスト失敗や処理不能
- `FATAL`: サービス継続不能（即時復旧対象）

### 分散トレーシング実装パターン（trace_id/span_id）

1. 入口（API Gateway/HTTPミドルウェア）で `trace_id` を生成または受信
2. 各内部処理で `span_id` を発行し、親子関係を保持
3. ログ・メトリクス・トレースへ同一 `trace_id` を付与
4. 失敗時は `trace_id` をインシデント票へ転記して追跡する

---

## ダッシュボード設計

### RED メソッド（Rate, Errors, Duration）

- `Rate`: 秒間リクエスト数
- `Errors`: 4xx/5xx 比率と件数
- `Duration`: p50/p95/p99 レイテンシ

### USE メソッド（Utilization, Saturation, Errors）

- `Utilization`: CPU/メモリ/接続使用率
- `Saturation`: キュー長、接続待ち、スレッド枯渇
- `Errors`: ノード/ディスク/ネットワークの異常件数

### ゴールデンシグナル 4 指標

1. Latency（遅延）
2. Traffic（トラフィック）
3. Errors（エラー）
4. Saturation（飽和）

---

## AI エージェントメトリクス

### エージェント固有の監視項目

- API 呼び出し回数 / エラー率 / レイテンシ
- トークン消費量 / コスト
- タスク成功率 / リトライ率
- コンテキストウィンドウ使用率

### HELIX `helix.db` との統合（SQLite 抽出例）

```sql
-- タスク成功率（直近7日）
SELECT
  COUNT(*) AS total_runs,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS success_runs
FROM task_runs
WHERE started_at >= datetime('now', '-7 day');
```

```sql
-- 失敗アクションの種別分布
SELECT action_type, COUNT(*) AS failed_count
FROM action_logs
WHERE status = 'failed'
GROUP BY action_type
ORDER BY failed_count DESC;
```

```sql
-- 失敗観測理由の上位
SELECT reason, COUNT(*) AS cnt
FROM observations
WHERE passed = 0
GROUP BY reason
ORDER BY cnt DESC
LIMIT 10;
```

---

## リアルタイム監視設計

Netdata の「ゼロ設定で即時可視化」コンセプトを参考に、導入初日から監視の最低ラインを確保する。

### HELIX プロジェクト監視テンプレート

| 監視レイヤー | 主要メトリクス | 目的 |
|-------------|---------------|------|
| アプリケーション層 | HTTP レスポンスタイム / エラー率 / スループット | ユーザー影響の早期検知 |
| インフラ層 | CPU / メモリ / ディスクI/O / ネットワーク | リソース飽和の検知 |
| DB 層 | クエリレイテンシ / コネクションプール / スロークエリ | データ層のボトルネック検知 |
| AI エージェント層 | API コール数 / トークン消費 / コスト | 生成系運用コスト管理 |

### アラート設計ベストプラクティス

1. ノイズ削減: 一過性スパイクで鳴らさず、継続時間と閾値の両方で判定
2. エスカレーション: `severity` ごとに通知先を段階化（Slack → PagerDuty → 電話）
3. 自動復旧: ヘルスチェック失敗時に `自動再起動 → 再判定 → 手動介入` の順で実行

### D-OBS 成果物テンプレート

```yaml
d_obs:
  service: "sample-api"
  dashboards:
    - name: "app-red"
      metrics: ["http_latency_p95", "http_error_rate", "http_rps"]
    - name: "infra-use"
      metrics: ["cpu_utilization", "memory_usage", "disk_io", "network_io"]
    - name: "db-health"
      metrics: ["db_query_latency_p95", "db_pool_usage", "db_slow_query_count"]
    - name: "agent-cost"
      metrics: ["agent_api_calls", "agent_token_usage", "agent_cost_daily"]
  alerts:
    - severity: "critical"
      condition: "error_rate > 5% for 5m"
      notify: ["pagerduty", "phone"]
    - severity: "high"
      condition: "latency_p95 > 800ms for 10m"
      notify: ["slack", "pagerduty"]
  runbook:
    healthcheck: "docs/runbooks/healthcheck.md"
    rollback: "docs/runbooks/rollback.md"
```

---

## チェックリスト

### 監視設計時

```
□ 可観測性の三本柱（Metrics/Logs/Traces）設計
□ SLO/SLI定義
□ エラーバジェット計算
□ アラートルール設計
□ ダッシュボード設計
□ ランブック作成
□ オンコール体制確認
```

### 導入後

```
□ アラートノイズ率の確認
□ SLO達成率のレビュー
□ ダッシュボードの有用性確認
□ インシデント対応時間の改善確認
```
