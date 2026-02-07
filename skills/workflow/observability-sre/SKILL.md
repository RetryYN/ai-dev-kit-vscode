---
name: observability-sre
description: SLO/SLI設計・アラート戦略・ダッシュボード構築の可観測性指針を提供
metadata:
  helix_layer: L6
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

> 出典: v-model-reference-cycle-v2.md §運用ポリシー5。品質劣化の段階別定義と対応アクション。

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
