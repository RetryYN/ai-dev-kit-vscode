> 目的: learning-engine が取り込む入力源を整理し、どの feedback を recipe 化に使うかを固定する

# Feedback Input Sources

## 入力源一覧

| source | 代表データ | 用途 |
|---|---|---|
| `feedback_hook` | 5 軸評価、通過 / 差戻し理由 | ゲート後の振り返り |
| detector 結果 | drift, regression, dependency, connection の履歴 | 再発パターン検出 |
| `recovery-log` | 暴走や収束の経緯 | Recovery の再発防止 |
| G9 / L9 | 総合検証の不具合、再現条件 | 設計と検証の学習 |
| G10 / L10 | UX フィードバック、操作迷い | UI / UX 改善の学習 |
| G11 / L11 | RC 判定とユーザー観点の差分 | 受入直前の改善 |
| G14 / L14 | 運用での課題、改善点 | 次サイクルへの持ち戻し |

## 最低限そろえる項目

| 項目 | 例 |
|---|---|
| `pattern_key` | `regression:dependency:missing-contract` |
| `observed_at` | `G9` / `L14` / `recovery-log` |
| `context` | どの工程、どの差分、どの条件で起きたか |
| `evidence` | review、doctor、feedback の根拠 |
| `recommended_followup` | PLAN draft か PR candidate か |

## 入力の優先順位

1. 反復回数が多いもの
2. 本番や RC に近いもの
3. 既存ルールへ昇格しやすいもの
4. `workflow/layer-context-injection` に反映すると再発抑止できるもの

## 使わない入力

- 単発で文脈不足のメモ
- 根拠が追えない口頭情報
- 既存 evidence に紐付かない推測
