> 目的: uncertainty × impact の 4 象限評価で priority と action を決める基準。mode は上書きしない

# 4 Quadrant Evaluation

## 基本原則

- 横軸: `uncertainty`
- 縦軸: `impact`
- 出力: `priority` と `action`
- 注意: mode は signal-to-mode mapping で固定し、この評価では変えない

## 評価マトリクス

| uncertainty | impact | priority | action | 解釈 |
|---|---|---|---|---|
| low | low | P3 | suggest_only | 記録と軽い追跡で足りる |
| low | high | P1 | immediate_plan_draft | 手順は明確だが影響が大きいので即起票する |
| high | low | P2 | discovery_first | 影響は限定的だが不確実性が高く、先に探索が必要 |
| high | high | P0 | emergency_routing | 迷わず収束導線へ回す |

## action の意味

| action | 意味 |
|---|---|
| `suggest_only` | 即時実行はせず、次のゲートやレビューで拾う |
| `immediate_plan_draft` | その場で PLAN draft の候補を切る |
| `discovery_first` | まず検証・調査を入れて誤判定を防ぐ |
| `emergency_routing` | Recovery または Incident の緊急導線へつなぐ |

## 例

| signal | quadrant | 結果 |
|---|---|---|
| `drift` | high / high | mode=Reverse, priority=P0 |
| `debt_degradation` | low / low | mode=Refactor, priority=P3 |
| `runaway` | high / high | mode=Recovery, priority=P0 |
| `incident` | low / high | mode=Incident, priority=P1 |

## 更新ルール

- priority 基準を変える時は、signal-to-mode mapping には触れない
- mode を変えたい時はこの文書ではなく mapping 側を更新する
- aggregate signal を追加した時も、まず mode を固定してから本評価に通す
