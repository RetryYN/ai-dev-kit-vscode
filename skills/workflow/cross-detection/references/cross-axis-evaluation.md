> 目的: cross-detection が複数 axis をどう組み合わせて aggregate signal を作るかを定義する

# Cross Axis Evaluation

## 対象 axis

| axis | 主な意味 | 典型 output |
|---|---|---|
| `axis-07` | doc / contract drift | missing doc, model drift |
| `axis-10` | dependency / relation graph | orphan, missing, cycle |
| `axis-11` | regression | baseline からのデグレ |
| `axis-12` | connection deficiency | 接続欠損、受け渡し漏れ |

## 組合せルール

| 組合せ | aggregate signal | 読み方 |
|---|---|---|
| 07 + 10 | `drift_degradation` | 契約 drift と依存劣化が連鎖している |
| 07 + 12 | `doc_connection_gap` | 文書上の契約不足と接続欠損が同時発生 |
| 10 + 11 | `regression_dependency` | 依存欠損が回帰を引き起こしている |
| 11 + 12 | `regression_dependency` | 接続欠損を伴う回帰 |
| 07 + 10 + 12 | `doc_connection_gap` | 設計整理が先 |

## 評価順序

1. FAIL を WARN より優先して拾う
2. regression を含む時は baseline の説明可能性を確認する
3. signal を 1 つに畳んだ後で `workflow/detection-routing` に渡す

## fail-close 条件

- `axis-11` が FAIL で、同時に `axis-10` または `axis-12` も FAIL
- `axis-07` と `axis-12` が同時に FAIL で、契約の参照先が不明
- baseline が欠けていて regression の真偽が判定できない
