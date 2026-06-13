---
name: learning-engine
description: 検出結果、recovery-log、運用フィードバックを学習して再発パターンを整理し、PLAN draft や PR candidate に昇格させる workflow スキル。gate や detector を直接変更せず、owner_role / mandatory_agents / recommended_agents / recommended_skills / recommended_commands / orchestration_mode を持つ次サイクル改善候補へ接続する
metadata:
  helix_layer: L14
  category: workflow
  triggers:
    - 同種 incident が再発した時
    - recovery PLAN が複数回起票された時
    - drift や regression が反復している時
    - G9 / L9 総合検証の結果を次サイクルへ持ち込みたい時
    - G10 / L10 UX 検証の学びを残したい時
    - G11 / L11 RC やユーザー検証の知見を定着させたい時
    - G14 / L14 運用学習 / 運用改善のフィードバックを次の L0 に渡したい時
  verification:
    - "学習入力が feedback_hook / detector / recovery-log / G9-G14 のいずれかから取得済"
    - "同種パターンが recipe として要約済"
    - "学習結果が PLAN draft または PR candidate に変換済"
    - "gate や detector への直接変更は TL 確認が必要と明記されている"
compatibility:
  claude: true
  codex: true
---

# Learning Engine

## 対応 workflow doc

- [learning-engine](../../../HELIX-workflows/helix-process/learning-engine.md)

## 目的

同じ失敗や同じ成功を、次の工程で再利用できる形に変換する。

- 入力: detector 結果、recovery-log、gate 後の feedback、運用結果
- 出力: recipe、PLAN draft 候補、PR candidate、注入セット更新候補
- 位置づけ: `HELIX-workflows/helix-process/learning-engine.md` の実務向けスキル化

正本: [HELIX-workflows/helix-process/learning-engine.md](../../../HELIX-workflows/helix-process/learning-engine.md)

## 責務境界

| 対象 | 役割 | 本スキルとの違い |
|---|---|---|
| `workflow/learning-engine` | 知見を recipe と改善候補へ変換する | 本スキル本体 |
| `workflow/layer-context-injection` | 学習結果を工程別注入セットへ反映する | 反映先の定義と実行を担う |
| `workflow/cross-detection` | 再発しやすい異常を検出する | 学習ではなく検出を担う |
| `workflow/detection-routing` | いま発生している signal の mode を決める | 将来改善ではなく現在判断を担う |

使い分け:

- いま起きている異常に対処する時は `workflow/detection-routing`
- 異常や成功の履歴を横断して学ぶ時は本スキル
- 学習結果を工程別の実行文脈へ落とす時は `workflow/layer-context-injection`

## 学習入力

入力源の一覧は [references/feedback-input-sources.md](references/feedback-input-sources.md) を参照。

特に優先する入力:

- `feedback_hook`
- detector 結果
- `recovery-log`
- G9 / L9 総合検証
- G10 / L10 UX 検証
- G11 / L11 RC / ユーザー検証
- G14 / L14 運用学習 / 運用改善

## 学習フロー

1. 同種の成功または失敗を収集する
2. pattern key を切り、再現条件と観測結果をまとめる
3. recipe に落とす
4. その recipe を PLAN draft 候補または PR candidate に変換する
5. 必要なら `workflow/layer-context-injection` に注入セット改善案として渡す

## 出力ルール

### PLAN / PR 候補化

学習結果は、直接 `gate` や `detector` を書き換えず、まず候補に変換する。

- PLAN draft:
  - 工程改善
  - detector 強化
  - review 強化
  - runbook 追補
- PR candidate:
  - 既存 docs の更新
  - 既存テストの強化
  - 既存コマンドのガード改善

変換フォーマットは [references/plan-pr-candidate-format.md](references/plan-pr-candidate-format.md) を参照。

### 直接変更しないもの

- `gate-policy.md`
- detector 実装
- vmodel 注入セット本体

これらは TL 確認後に別 PLAN として扱う。

## Forward 接続

| 学びの発生点 | 次に渡す先 | 目的 |
|---|---|---|
| G9 / L9 | 次サイクルの設計・検証改善 | 総合検証で見えた構造問題を定着 |
| G10 / L10 | UI / UX の改善候補 | UX の繰り返し課題を標準化 |
| G11 / L11 | RC 直前の不足補強 | 受入前の詰まりをルール化 |
| G14 / L14 | 次の L0 / L1 | 運用知見を前工程へ持ち戻す |

## エスカレーション基準

以下は TL または人間判断が必要。

- gate 基準の変更が必要な時
- detector の fail-close 条件を変えたい時
- 学習結果が本番運用ルールに直結する時
- 同じパターンでも、根本原因が複数に分岐している時

## 関連スキル / コマンド

| 種別 | ID | 用途 |
|---|---|---|
| skill | `workflow/layer-context-injection` | 学習結果の反映先 |
| skill | `workflow/postmortem` | 障害学習の入力元 |
| skill | `workflow/verification` | 検証結果の入力元 |
| skill | `workflow/runbook` | 運用知見の固定先 |
| command | `helix plan` | PLAN draft 候補の起票先 |
| command | `helix review --uncommitted` | PR candidate 前の差分確認 |
| command | `helix skill list` | skill catalog 上の反映確認 |

## 完了チェック

- [ ] 入力源が特定できている
- [ ] recipe または pattern key に正規化できている
- [ ] PLAN draft または PR candidate に落とせている
- [ ] `workflow/layer-context-injection` へ渡す時の境界が明記されている
