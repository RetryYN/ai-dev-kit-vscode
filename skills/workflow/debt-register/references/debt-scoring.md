> 目的: 技術的負債を影響×緊急度で採点し、返済優先順位と計画を一貫して管理する。

# Debt Scoring

## 1. スコアリングモデル
基本式:
`Debt Score = Impact(1-5) * Urgency(1-5)`

補助係数（任意）:
- Security Critical: +3
- Customer Visible: +2
- Wide Blast Radius: +2

優先度区分:
- P1: 18点以上
- P2: 10-17点
- P3: 9点以下

## 2. 評価基準
Impact:
- 5: 重大障害/法令違反リスク
- 4: 顧客影響が継続
- 3: 開発速度を恒常的に低下
- 2: 局所品質問題
- 1: 軽微

Urgency:
- 5: 1スプリント以内に是正必須
- 4: 次リリースまでに必要
- 3: 四半期内に対応
- 2: 計画対応可
- 1: 低優先

## 3. 台帳テンプレート
```markdown
# Debt Register
| ID | 概要 | category | Impact | Urgency | Score | Priority | Owner | Target Sprint | Status |
|---|---|---|---:|---:|---:|---|---|---|---|
| DEBT-001 | 認可チェック重複 | security | 5 | 4 | 20 | P1 | @team-a | 25.1 | open |
| DEBT-002 | テスト欠落 | test | 4 | 3 | 12 | P2 | @team-b | 25.2 | open |
```

必須項目:
- [ ] Impact/Urgency/Score
- [ ] Owner/Target Sprint
- [ ] Status（open/triaged/in_progress/done/accepted_risk）

## 4. 返済計画テンプレート
```yaml
debt_repayment_plan:
  debt_id: "DEBT-001"
  objective: "..."
  scope:
    in:
      - "..."
    out:
      - "..."
  tasks:
    - id: "T1"
      summary: "..."
      estimate: "0.5d"
  acceptance:
    - "回帰テスト pass"
    - "監視指標悪化なし"
  rollout:
    strategy: "feature flag"
    rollback: "flag off + route restore"
```

## 5. 運用ルール
- P1 は owner 未設定禁止
- P1 は target sprint 未設定禁止
- accepted_risk は再評価日必須
- G4 前に `open` の P1 を必ずレビュー

判定チェック:
- [ ] `docs/debt/YYYY-MM-DD-debt-register.md` に保存
- [ ] 高スコア負債の返済計画あり
- [ ] スプリント連携済み
- [ ] ブロッカー有無を明記

## 6. 詳細運用チェック
### 6.1 登録時
- [ ] 事象の再現条件を記録
- [ ] 発生頻度を記録
- [ ] 影響範囲を記録
- [ ] 暫定対策を記録
- [ ] 恒久対策候補を記録

### 6.2 優先度レビュー
- [ ] 週次で P1 を確認
- [ ] スプリント計画に反映
- [ ] 期限超過を可視化
- [ ] owner 未設定を解消
- [ ] accepted_risk の再評価

### 6.3 返済完了条件
- [ ] 修正差分がマージ済み
- [ ] 回帰テストが pass
- [ ] 監視悪化なし
- [ ] ドキュメント更新済み
- [ ] status を done 化


## 7. レビュー質問 (厳選)

Debt レビューで使う具体質問:
- [ ] 影響度・緊急度・再発率の採点根拠が定量値または事例で説明されているか
- [ ] 返済コスト見積もりに依存作業（テスト・移行・周知）が含まれているか
- [ ] 先送り判断には期限と再評価トリガーが設定されているか
- [ ] 返済後に削減できる運用負荷や障害確率が測定指標として定義されているか
- [ ] 高スコア負債がロードマップに紐付き、担当者と予定時期が確定しているか
- [ ] 新規負債の流入を防ぐ予防策（ガードレール・レビュー観点）が記載されているか
