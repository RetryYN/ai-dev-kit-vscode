---
name: observability-sre
description: 監視・可観測性・SRE実践。SLO/SLI設計、アラート戦略、ダッシュボード構築時に使用
metadata:
  helix_layer: L6
  triggers:
    - 監視設計時
    - SLO/SLI定義時
    - アラート設計時
    - ダッシュボード構築時
  verification:
    - SLO定義の妥当性
    - アラート閾値の適切性
    - 可観測性の三本柱カバレッジ
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

### Prometheus メトリクス実装例

```python
from prometheus_client import Counter, Histogram, Gauge

# REDメトリクス
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# USEメトリクス
ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

# ミドルウェア
async def metrics_middleware(request, call_next):
    ACTIVE_CONNECTIONS.inc()

    with REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).time():
        response = await call_next(request)

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    ACTIVE_CONNECTIONS.dec()
    return response
```

---

## 4. アラート設計

### アラートレベル

| レベル | 条件 | 対応 | 通知先 |
|--------|------|------|--------|
| **P1 Critical** | SLO違反、サービスダウン | 即時対応 | PagerDuty + Slack |
| **P2 Warning** | エラーバジェット50%超 | 当日対応 | Slack |
| **P3 Info** | 異常傾向検出 | 計画対応 | Slack (低優先) |

### アラートルール例

```yaml
# Prometheus alerting rules
groups:
  - name: slo-alerts
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m]))
          /
          sum(rate(http_requests_total[5m]))
          > 0.001
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "エラー率がSLO閾値超過"
          description: "5分間のエラー率: {{ $value | humanizePercentage }}"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.99,
            rate(http_request_duration_seconds_bucket[5m])
          ) > 0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P99レイテンシが200ms超過"

      - alert: ErrorBudgetBurn
        expr: |
          slo:error_budget_remaining:ratio < 0.25
        labels:
          severity: critical
        annotations:
          summary: "エラーバジェット残り25%未満"
```

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

### Grafana ダッシュボード構成例

```json
{
  "dashboard": {
    "title": "Service Overview",
    "panels": [
      {
        "title": "SLO: Availability",
        "type": "gauge",
        "targets": [{"expr": "slo:availability:ratio"}],
        "thresholds": [
          {"value": 0.999, "color": "green"},
          {"value": 0.995, "color": "yellow"},
          {"value": 0, "color": "red"}
        ]
      },
      {
        "title": "Error Budget Remaining",
        "type": "stat",
        "targets": [{"expr": "slo:error_budget_remaining:ratio * 100"}]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [{"expr": "sum(rate(http_requests_total[5m]))"}]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [{"expr": "sum(rate(http_requests_total{status=~'5..'}[5m])) / sum(rate(http_requests_total[5m]))"}]
      },
      {
        "title": "Latency Distribution",
        "type": "heatmap",
        "targets": [{"expr": "rate(http_request_duration_seconds_bucket[5m])"}]
      }
    ]
  }
}
```

---

## 6. OpenTelemetry統合

### 基本セットアップ

```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# トレーサー設定
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317"))
)

# メトリクス設定
metrics.set_meter_provider(MeterProvider(
    metric_readers=[PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint="http://otel-collector:4317")
    )]
))

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)
```

### 分散トレーシング実装

```python
@tracer.start_as_current_span("process_order")
async def process_order(order_id: str):
    span = trace.get_current_span()
    span.set_attribute("order.id", order_id)

    # 子スパン
    with tracer.start_as_current_span("validate_order"):
        await validate(order_id)

    with tracer.start_as_current_span("charge_payment"):
        await charge(order_id)

    with tracer.start_as_current_span("send_notification"):
        await notify(order_id)
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
