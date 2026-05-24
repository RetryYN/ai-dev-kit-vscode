---
name: cross-detection
description: 単一 detector では見えない横断的劣化を複数 axis の組合せで集約して検出する workflow スキル。aggregate signal を生成し、owner_role / mandatory_agents / recommended_agents / recommended_skills / recommended_commands / orchestration_mode を持つ後続ルーティングへ渡す
metadata:
  helix_layer: L4-L9
  category: workflow
  triggers:
    - helix doctor 相当の横断確認をしたい時
    - 複数 axis が同時に WARN または FAIL した時
    - 依存漏れと契約漏れが連鎖している時
    - connection 欠損と regression が同時に見えている時
    - detection-routing に集約済シグナルを渡したい時
  verification:
    - "複数 axis の結果から aggregate signal を説明できる"
    - "aggregate signal が detection-routing へ渡る"
    - "baseline と比較したデグレ検知の扱いが定義済"
    - "fail-close 条件が明記されている"
compatibility:
  claude: true
  codex: true
---

# Cross Detection

## 対応 workflow doc

- [cross-detection](../../../HELIX-workflows/helix-process/cross-detection.md)

## 目的

単一 detector 単位では弱い異常を、複数 axis の組合せで意味のある signal にする。

- 入力: axis-07 / axis-10 / axis-11 / axis-12 などの detector 結果
- 出力: aggregate signal
- 位置づけ: `workflow/detection-routing` の前段にある集約器

正本: [HELIX-workflows/helix-process/cross-detection.md](../../../HELIX-workflows/helix-process/cross-detection.md)

## 責務境界

| 対象 | 役割 | 本スキルとの違い |
|---|---|---|
| `workflow/cross-detection` | detector 結果を集約して aggregate signal を作る | 本スキル本体 |
| `workflow/detection-routing` | aggregate signal を受けて mode を決める | 集約はしない |
| `workflow/learning-engine` | 頻出パターンを学習する | 検出ではなく学習 |
| `workflow/verification` | ゲート全体の検証観点を持つ | detector 集約器ではない |

使い分け:

- detector を横断して signal を作る時は本スキル
- 作った signal の mode 判定は `workflow/detection-routing`
- 同じ組合せが何度も出る時の学習は `workflow/learning-engine`

## 対象 axis

詳細は [references/cross-axis-evaluation.md](references/cross-axis-evaluation.md) を参照。

- `axis-07`: doc / contract drift
- `axis-10`: relation graph and dependency leakage
- `axis-11`: regression against baseline
- `axis-12`: connection deficiency

## Aggregate Signal

語彙の一覧は [references/aggregate-signal-vocabulary.md](references/aggregate-signal-vocabulary.md) を参照。

代表例:

- `drift_degradation`
- `doc_connection_gap`
- `regression_dependency`
- `runaway_feedback_loop`

## 横断集約フロー

1. detector ごとの WARN / FAIL を収集する
2. 同時発生した axis を組み合わせる
3. 組合せごとに aggregate signal を決める
4. signal に severity と evidence を添える
5. `workflow/detection-routing` へ渡す

## デグレ回避

- 回帰は baseline 比較を基準にする
- baseline 差分が説明できない時は fail-close 側へ倒す
- 依存漏れや接続欠損を伴う regression は単独より優先度を上げる

## Forward 接続

| aggregate signal | 主な接続先 | 意味 |
|---|---|---|
| `drift_degradation` | Reverse | 設計整理が先 |
| `doc_connection_gap` | Reverse | 契約と接続の穴埋めが先 |
| `regression_dependency` | Recovery または Incident | 回帰が依存欠損と絡んでいる |
| `runaway_feedback_loop` | Recovery | 収束と再発防止が先 |

## エスカレーション基準

- 3 つ以上の axis が同時に FAIL した時
- baseline の信頼性自体が崩れている時
- aggregate signal の語彙にない新しい組合せが出た時
- 本番デグレを含む横断障害の時

## 関連スキル / コマンド

| 種別 | ID | 用途 |
|---|---|---|
| skill | `workflow/detection-routing` | aggregate signal の引き渡し先 |
| skill | `workflow/verification` | ゲート観点の補完 |
| skill | `workflow/learning-engine` | 頻出パターンの学習 |
| command | `helix gate` | ゲート前後の横断確認 |
| command | `helix review --uncommitted` | detector 起因の差分確認 |
| command | `helix plan` | routing 後の PLAN 起票 |

## 完了チェック

- [ ] 複数 axis の結果から aggregate signal を作れる
- [ ] `workflow/detection-routing` との役割分担が明確
- [ ] baseline と fail-close の扱いが定義されている
- [ ] 新しい組合せが出た時のエスカレーション先が決まっている
