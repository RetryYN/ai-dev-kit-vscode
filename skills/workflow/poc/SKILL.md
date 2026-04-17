---
name: poc
description: G1.5 PoC ゲート専用。kill criteria を伴う最小検証を行い実装着手可否を判定する
metadata:
  helix_layer: L1
  triggers:
    - G1.5 PoC ゲート時
    - kill criteria 策定時
    - 実装着手前の技術検証時
    - PoC 結果報告書生成時
  verification:
    - "kill criteria が事前文書化"
    - "PoC 成果物に yes/no 判定"
    - "PoC コード量 ≤200行 or 超過理由記載"
compatibility:
  claude: true
  codex: true
---

# PoC スキル（G1.5 最小検証）

## 目的

G1.5 PoC ゲートで技術不確実性を短時間で潰し、
実装着手の可否を yes/no で判定する。

このスキルは「試す行為」に限定し、
選定そのものは別スキルに委譲する。

---

## 責務境界（重要）

`advanced/tech-selection` と `workflow/poc` の境界を厳密に分ける。

- `tech-selection`: 候補列挙 → 評価マトリクス → 選定（選ぶ行為）
- `poc`: 選定後の検証実装 → kill criteria 判定（試す行為）

禁止:

- PoC 中に候補比較へ戻って選定をやり直す
- 選定根拠なしで PoC を開始する

必要なら `tech-selection` に差し戻してから再開する。

---

## 使用タイミング

以下のいずれかに該当したら適用する。

- 新技術導入で失敗コストが高い
- 性能・安定性・連携性に不確実性がある
- 実装前に最小実験で可否判断したい
- G1.5 の通過判定資料が必要

不確実性がない場合は PoC をスキップし、
スキップ理由を記録して次フェーズへ進む。

---

## PoC kill criteria テンプレート

```yaml
kill_criteria:
  objective: "何を検証するか"
  hypothesis:
    - "仮説1"
    - "仮説2"
  success_metrics:
    - metric: "p95 latency"
      threshold: "<= 200ms"
      method: "計測手順"
    - metric: "error rate"
      threshold: "< 1%"
      method: "計測手順"
  failure_triggers:
    - "セキュリティ要件を満たせない"
    - "必須機能が timebox 内に実証不能"
    - "運用コストが許容上限を超える"
  timebox:
    start: "YYYY-MM-DD"
    end: "YYYY-MM-DD"
    max_effort_hours: 16
  constraints:
    code_limit: "<= 200 LOC"
    production_data_usage: false
```

ルール:

- `kill_criteria` は PoC 開始前に文書化する
- 成功指標・失敗トリガー・timebox を必須にする

---

## PoC スコープ制限

PoC は「最小で判定できる範囲」に限定する。

必須制限:

- 本番機能を作り込まない
- UI/運用改善は対象外
- 永続化設計や詳細最適化は後工程へ送る
- コード量は原則 200 行以下

200 行超過が必要な場合:

- 超過理由
- 追加で得られる検証価値
- 代替案で 200 行以内に収まらない理由

を結果報告書に明記する。

---

## PoC 結果報告書テンプレート

```markdown
# PoC Result: {topic}

## 結論
- 判定: yes | no
- 要約: 1-3 行

## 証拠
- 計測ログ:
- 再現手順:
- 主要データ:

## 判定
- success_metrics 達成状況:
- failure_triggers 発火有無:
- kill criteria 最終判定:

## 次アクション
- confirmed: L2 へ接続（設計反映）
- rejected: 撤退 or tech-selection へ差戻し
```

必須要件:

- yes/no を明示
- 証拠リンク（ログ、ベンチ結果、再現手順）を含める
- 次アクションを Forward HELIX に接続する

---

## Forward HELIX 接続規則

PoC 判定後の遷移は固定する。

- confirmed（yes）: L2 へ接続し設計へ反映
- rejected（no）: 当該案から撤退し、必要なら `tech-selection` へ戻る

判定保留（defer）は例外扱い。
`defer` を使う場合は、追加検証項目と期限を必ず指定する。

---

## 実行手順（標準）

1. 前提確認（選定済み案か）
2. `kill_criteria` を先に確定
3. timebox 内で最小実装
4. 計測・証拠収集
5. yes/no 判定
6. 報告書作成と次フェーズ接続

---

## エスカレーション基準

以下は人間確認にエスカレーションする。

- 認証・決済・個人情報・ライセンス影響
- 本番運用に直結する不可逆な判断
- timebox 超過が避けられない
- yes/no を技術的に確定できない

提出物:

- kill_criteria
- PoC 結果報告書
- 推奨判断と残存リスク

---

## G1.5 判定チェック（実務用）

- kill criteria が事前に文書化されている
- PoC 成果物に yes/no 判定がある
- PoC コード量が 200 行以下、または超過理由が記載されている
- 次アクションが L2 または撤退に接続されている

PoC の完了条件は「コードがあること」ではなく、
「実装着手可否が根拠付きで判定できること」。
