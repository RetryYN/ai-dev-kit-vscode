> 目的: 検出シグナルと対応モードを固定で結び付ける語彙表。SIGNAL_TO_MODE の設計根拠として使う

# Signal To Mode Mapping

## Active Signals

| signal | mode | kind | subtype | 典型例 | 主な入力元 |
|---|---|---|---|---|---|
| `drift` | Reverse | reverse | normalization | 設計と実装の不整合 | drift-check, doctor |
| `debt_degradation` | Refactor | refactor | - | 複雑度増大、保守性低下 | detector axis, review |
| `regression_prod` | Incident | recovery | - | 本番デグレ、SLO 悪化 | monitoring, post-deploy |
| `regression_dev` | Recovery | recovery | - | 開発中デグレ、認識ズレ | test baseline, doctor |
| `runaway` | Recovery | recovery | - | AI 暴走、工程逸脱 | budget, audit, recovery-log |
| `incident` | Incident | troubleshoot or recovery | env dependent | 障害対応の即時判断 | runbook, on-call, SLO |
| `unknown_design` | Reverse | reverse | code | 設計不明箇所の多発 | reverse intake, explorer |

## Deprecated Alias

| alias | 扱い | 理由 |
|---|---|---|
| `degradation` | 非推奨 | 劣化の性質が負債起因か回帰起因か曖昧なため |

`degradation` を見つけたら、以下へ分解して扱う。

- コード劣化や負債の蓄積なら `debt_degradation`
- 開発中の回帰なら `regression_dev`
- 本番デグレなら `regression_prod`

## Aggregate Signals

| aggregate_signal | 推奨 mode | 意味 |
|---|---|---|
| `drift_degradation` | Reverse | drift と劣化が同時に起き、設計復元が先 |
| `doc_connection_gap` | Reverse | 契約漏れと接続欠損が併発 |
| `regression_dependency` | Incident or Recovery | 回帰と依存欠損が同時発生 |
| `runaway_feedback_loop` | Recovery | 暴走と同種障害の再発が循環している |

aggregate signal は `workflow/cross-detection` から渡される。最終判断は `workflow/detection-routing` が行う。

## 運用ルール

- signal から mode を決める段階では、priority を混ぜない
- priority と action は別 reference の 4 象限評価で決める
- 新しい signal を足す時は、mode / kind / subtype / 典型入力元を必ず 1 セットで定義する
