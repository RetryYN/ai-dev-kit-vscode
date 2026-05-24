> 目的: cross-detection が使う aggregate signal の語彙と意味を固定する

# Aggregate Signal Vocabulary

## 語彙一覧

| aggregate signal | 意味 | 主な接続先 |
|---|---|---|
| `drift_degradation` | drift と劣化が複合し、設計整理が先に必要 | Reverse |
| `doc_connection_gap` | 契約漏れと接続欠損が同時に起きている | Reverse |
| `regression_dependency` | 回帰が依存関係の欠損と結び付いている | Recovery or Incident |
| `runaway_feedback_loop` | 暴走と同種障害の再発が循環している | Recovery |

## 生成ルール

- aggregate signal は 1 回の doctor 実行につき 1 件以上作ってよい
- 単一 signal へ潰せる場合は無理に aggregate signal を増やさない
- 語彙を追加する時は `workflow/detection-routing` 側の受け口も同時に定義する

## 単一 signal との関係

| 単一 signal | aggregate signal に昇格する例 |
|---|---|
| `drift` | `drift_degradation` |
| `debt_degradation` | `drift_degradation` |
| `regression_dev` | `regression_dependency` |
| `runaway` | `runaway_feedback_loop` |

## 避けるべき語彙

- 意味が広すぎる名前
- detector 名をそのまま並べただけの名前
- mode と signal を混ぜた名前
