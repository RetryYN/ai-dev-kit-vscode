## Prometheus メトリクス実装例

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

## Prometheus アラートルール例

```yaml
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

---

## Grafana ダッシュボード構成例

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

## OpenTelemetry統合

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
