> 目的: 自己ベンチマーク運用と最終チェックリストを確認するときに参照する

## 自己ベンチマーク（SWE-EVO コンセプト）

### コンセプト

HELIX のバージョン間で「前より良くなったか」を定量化し、改善を継続可能にする。

### 計測指標

| 指標 | 定義 | 観測ポイント |
|------|------|-------------|
| タスク成功率 | `helix learn` の recipe 成功率推移 | 週次・月次 |
| ゲート通過率 | G2-G7 の一発通過率推移 | ゲート別 |
| 手戻り回数 | `interrupt` / `CC` / `LPR` の発動回数推移 | タスク単位 |
| コスト効率 | トークン消費量 / 成果物数 の推移 | モデル別 |
| テスト品質 | Mutation Score の推移 | モジュール別 |
| ドキュメント品質 | textlint エラー数の推移 | 文書種別別 |

### ベンチマーク実行方法

1. SQLite（`helix.db` / `global.db`）から対象メトリクスを集計する
2. 週次/月次レポートをテンプレート化して自動生成する
3. `helix log report benchmark` を将来コマンドとして統合し、定期実行する

```sql
-- 例: 直近30日のゲート通過率（概念）
SELECT gate_name,
       SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) AS passed,
       COUNT(*) AS total
FROM gate_logs
WHERE created_at >= date('now', '-30 day')
GROUP BY gate_name;
```

### HELIX Learning Engine との統合

- recipe の `quality_score` 推移グラフを記録し、学習効果を可視化する
- promote された recipe 群の導入前後で、成功率改善効果を比較する

---

## チェックリスト

### 計測時

```
[ ] 目標値を設定
[ ] ベースライン計測
[ ] ボトルネック特定
[ ] 改善実施
[ ] 効果測定
```
