> 目的: G1.5 で PoC の可否判定を短時間で行うための4点セットを標準化する。

# PoC Design Template

## 1. PoC 4点セット（必須）
1. 仮説（Hypothesis）
2. 検証方法（Method）
3. 成功条件（Success Criteria）
4. ロールバック（Rollback）

チェックリスト:
- [ ] 仮説が「観測可能な結果」で書かれている
- [ ] 計測方法と計測点が定義されている
- [ ] 成功条件が数値閾値を持つ
- [ ] 失敗時のロールバック手順が5ステップ以内である

## 2. 設計テンプレート
```yaml
poc_design:
  topic: "<テーマ>"
  timebox_hours: 16
  hypothesis:
    - "H1: ..."
  method:
    environment: "local|staging"
    data: "synthetic|anonymized"
    steps:
      - "..."
    metrics:
      - name: "latency_p95"
        target: "<= 200ms"
      - name: "error_rate"
        target: "< 1%"
  success_criteria:
    must:
      - "必須条件"
    nice_to_have:
      - "任意条件"
  rollback:
    trigger:
      - "閾値超過"
    procedure:
      - "feature flag off"
      - "route rollback"
      - "smoke test"
```

## 3. 実施・判定フロー
1. kill criteria を先に確定する
2. 最小実装で検証する（原則200 LOC以内）
3. 計測ログを保存する
4. yes/no を決める
5. 次フェーズへ接続する

判定テンプレート:
```yaml
poc_result:
  decision: "yes|no|defer"
  evidence:
    logs: ["path or url"]
    benchmark: ["path or url"]
  criteria_check:
    - criterion: "latency_p95 <= 200ms"
      actual: "185ms"
      status: "pass"
  next_action: "L2へ反映|tech-selectionへ差戻し"
```

## 4. 具体例（外部API統合）
仮説:
- H1: Circuit Breaker + Retry で失敗率を 1% 未満に維持できる

検証方法:
- 5分間に 5000 req 相当の負荷
- 外部API擬似障害（5xx 連続）を注入

成功条件:
- p95 < 300ms
- error_rate < 1%
- 復旧時間 < 2分

ロールバック:
1. 外部API経路を旧経路に戻す
2. feature flag `ff_external_api_v2` を OFF
3. 監視ダッシュボードで成功率を確認

## 5. PoC 報告書テンプレート
```markdown
# PoC Result: <topic>
## 結論
- 判定: yes|no|defer
## 仮説
- ...
## 検証方法
- ...
## 成功条件と実測
| 指標 | 目標 | 実測 | 判定 |
|---|---|---|---|
| latency_p95 | <=200ms | 185ms | pass |
## ロールバック結果
- ...
## 次アクション
- ...
```

完了条件:
- [ ] yes/no/defer の明記
- [ ] 証拠ログへの参照
- [ ] ロールバック手順の再現確認
- [ ] L2/L3 への入力項目を列挙

## 6. PoC 詳細チェックリスト
### 6.1 事前チェック
- [ ] 対象機能は限定されている
- [ ] 本番データは利用しない
- [ ] 検証環境が準備済み
- [ ] 計測方法が定義済み
- [ ] 終了条件が数値化済み
- [ ] ロールバック責任者を定義
- [ ] 監視観点を定義
- [ ] セキュリティ制約を確認
- [ ] ライセンス制約を確認
- [ ] 実施期限を確定

### 6.2 実施中チェック
- [ ] 変更点を時系列で記録
- [ ] 計測値を3回以上採取
- [ ] 異常系テストを実施
- [ ] 再現手順を更新
- [ ] 想定外挙動を記録
- [ ] 失敗条件の発火確認
- [ ] ロールバック手順を検証
- [ ] 証拠ファイルを保存
- [ ] PoC 範囲外実装を抑止
- [ ] 工数超過を監視

### 6.3 判定後チェック
- [ ] yes/no/defer 理由を記載
- [ ] リスクを列挙
- [ ] L2 入力項目を列挙
- [ ] 追加検証の要否を明記
- [ ] 廃棄コードの扱いを決定


## 7. レビュー質問 (厳選)

G1.5 レビュー時に使う具体質問:
- [ ] 仮説が「何を否定できれば失敗とみなすか」まで定義されているか
- [ ] 成功条件は測定可能な数値または明確な合否基準で記載されているか
- [ ] 検証項目が技術リスク上位から優先され、順序に妥当性があるか
- [ ] データセット・テスト入力・前提環境が再現可能な形で残されているか
- [ ] rollback 条件と中止判断者が明記され、運用時に迷いがないか
- [ ] PoC 結果を L2 設計へ引き継ぐ入力項目が具体化されているか
