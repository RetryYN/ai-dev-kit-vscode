> 目的: G0.5/G1.5/G1R の entry/exit criteria を同一様式で管理しゲート判定を安定化する。

# Gate Entry/Exit Criteria

## 1. 適用対象と運用ルール
対象ゲート:
- G0.5 企画突合
- G1.5 PoC
- G1R 事前調査

共通ルール:
- entry を満たさない場合は開始しない
- exit は証跡ファイルで判定する
- fail/block は理由を1行で残す

## 2. G0.5 企画突合 criteria
Entry:
- [ ] 企画書の項目一覧がある
- [ ] L1 要件ドラフトがある
- [ ] 担当と期限が決まっている

Exit:
- [ ] 企画項目カバー率100%
- [ ] unmapped 0件
- [ ] 追加提案項目がラベル化済み

証跡:
- `docs/planning/g0_5-mapping.md`

テンプレート:
```markdown
# G0.5 Mapping
| 企画ID | 企画項目 | L1要件ID | 状態 |
|---|---|---|---|
```

## 3. G1.5 PoC criteria
Entry:
- [ ] 技術不確実性の定義あり
- [ ] kill criteria 定義済み
- [ ] timebox 設定済み

Exit:
- [ ] yes/no/defer 判定あり
- [ ] 成功条件の実測がある
- [ ] defer の場合は追加検証期限あり

証跡:
- `docs/research/poc-result-YYYYMMDD.md`

## 4. G1R 事前調査 criteria
Entry:
- [ ] 調査テーマと範囲が明確
- [ ] 判断が必要な論点が列挙されている

Exit:
- [ ] 一次情報 URL 3件以上
- [ ] adoption 判定（採用/不採用/保留）
- [ ] open_blockers が明記されている

証跡:
- `docs/research/YYYY-MM-DD-<topic>.md`

## 5. 判定フォーマット（共通）
```yaml
gate_decision:
  gate: "G0.5|G1.5|G1R"
  entry: "passed|failed"
  exit: "passed|failed|blocked"
  evidence:
    - "path/to/doc.md"
  reason: "1行"
  next: "次フェーズ"
```

具体例:
```yaml
gate_decision:
  gate: "G1R"
  entry: "passed"
  exit: "passed"
  evidence:
    - "docs/research/2026-04-19-auth-options.md"
  reason: "一次情報5件でadoption確定"
  next: "L2"
```

## 6. ゲート運用台帳テンプレート
```markdown
# Gate Ledger
| Date | Gate | Entry | Exit | Owner | Evidence | Note |
|---|---|---|---|---|---|---|
| 2026-04-19 | G0.5 | pass | pass | @tl | docs/planning/g0_5-mapping.md | coverage 100% |
| 2026-04-20 | G1R | pass | pass | @tl | docs/research/2026-04-20-auth.md | sources 5 |
| 2026-04-21 | G1.5 | pass | pass | @tl | docs/research/poc-result-20260421.md | yes |
```

### 6.1 例外時の扱い
- [ ] entry fail は即差し戻し
- [ ] exit blocked は期限付き保留
- [ ] defer は次判定日を必ず設定
- [ ] fail 理由は再発防止に接続

### 6.2 監査向け最小記録
- [ ] 誰が判定したか
- [ ] いつ判定したか
- [ ] 何を根拠にしたか
- [ ] 何を次に行うか


## 7. レビュー質問 (厳選)

ゲート計画レビューで使う具体質問:
- [ ] 各ゲートの entry 条件に必要証跡の保存場所が 1 対 1 で対応しているか
- [ ] fail 時の差し戻し先フェーズと再判定条件が明文化されているか
- [ ] 条件付きゲート（G1.5/G1R/G5）の発火条件が曖昧語なしで定義されているか
- [ ] セキュリティゲート（G2/G4/G6/G7）での必須確認項目が欠けていないか
- [ ] 判定者と承認者の責務が分離され、自己承認が起きない設計になっているか
- [ ] ゲート遅延時の暫定運用（期限・責任者・リスク許容）が定義されているか
