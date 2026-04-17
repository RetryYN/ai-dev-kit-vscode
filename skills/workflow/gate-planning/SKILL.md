---
name: gate-planning
description: G0.5/G1.5 企画突合・PoC ゲート専用スキル。企画書との突合 + 技術スタック選定 + PoC 結果集約
metadata:
  helix_layer: L1
  triggers:
    - G0.5 企画突合ゲート時
    - G1.5 PoC ゲート時
    - 競合調査レポート生成時
    - D-TECH-STACK 選定書生成時
    - PoC 結果報告書生成時
  verification:
    - "競合調査レポートが docs/research/ に .md で存在 (G0.5用)"
    - "D-TECH-STACK が docs/ または adr/ に存在 (G1.5用)"
    - "企画項目カバー率 100%"
compatibility:
  claude: true
  codex: true
---

# Gate Planning スキル

## 適用タイミング

このスキルは以下の場合に読み込む:
- G0.5 企画突合ゲートを実施する時
- G1.5 PoC ゲートを実施する時
- 企画比較・技術選定・PoC集約文書を作成する時

---

## 1. 目的

G0.5 と G1.5 の間で分断しがちな文書を統合し、
「企画整合」「技術選定」「PoC 検証」を同一トレーサブル単位で管理する。

到達目標:
- 企画書項目と L1 要件の 1対1 対応
- 競合調査の根拠付き比較
- D-TECH-STACK の評価理由明確化
- PoC 結果の採否判断可能化

---

## 2. G0.5 企画突合チェックリスト

`gate-policy.md` の G0.5 通過条件に準拠し、以下を確認する。

```markdown
# G0.5 チェック

## 企画 vs L1 マッピング
| 企画項目ID | 企画項目 | L1対応ID | D-REQ-F/NF/ACC | 状態 |
|---|---|---|---|---|
| P-001 | 会員登録 | REQ-001 | D-REQ-F | mapped |
| P-002 | 個人情報保護 | NFR-004 | D-REQ-NF | mapped |

## 判定
- unmapped 0件
- 追加提案項目は明示済み
```

必須条件:
- 企画項目カバー率 100%
- 企画にあって L1 にない項目 0
- L1 独自項目は「追加提案」としてラベル付け

---

## 3. 競合調査レポート テンプレート

出力先: `docs/research/competitive-YYYYMMDD.md`

```markdown
# 競合調査レポート

## 対象テーマ
- 例: B2B 請求管理SaaS

## 比較対象
| サービス | 強み | 弱み | 価格帯 | 根拠URL |
|---|---|---|---|---|
| A社 | 導入が速い | API制限 | 中 | ... |
| B社 | 拡張性高い | UI複雑 | 高 | ... |

## 当社要件への示唆
- 要件IDごとの差分と採用判断

## 結論
- 何を踏襲し、何を差別化するか
```

品質要件:
- 一次情報または公式情報を優先
- 推測は「推測」と明記
- 参照日を記載

---

## 4. D-TECH-STACK 選定書 テンプレート

出力先候補:
- `docs/D-TECH-STACK.md`
- `adr/ADR-TECH-STACK.md`

```markdown
# D-TECH-STACK

## 候補一覧
| 領域 | 候補 | 評価軸 | スコア | 推奨 |
|---|---|---|---|---|
| Backend | FastAPI | 学習コスト/性能/運用性 | 4.2 | yes |
| Backend | NestJS | 学習コスト/性能/運用性 | 3.7 | no |

## 評価軸定義
- 学習コスト
- 保守性
- 性能
- セキュリティ
- エコシステム

## 推奨構成
- 採用技術と不採用理由

## リスクと緩和策
- 主要リスク
- PoC で確認すべき項目
```

運用メモ:
- `advanced/tech-selection` の評価マトリクスを利用
- G1.5 判定時に kill criteria を併記

---

## 5. PoC 結果報告書 集約テンプレート

出力先: `docs/research/poc-result-YYYYMMDD.md`

```markdown
# PoC 結果報告書

## 仮説
- H1: 1000 req/min でも応答 200ms 未満

## 成功条件 / kill criteria
- success: p95 < 200ms
- kill: p95 > 400ms が継続

## 実施内容
- テスト条件
- 実装差分

## 結果
| 指標 | 目標 | 実測 | 判定 |
|---|---|---|---|
| p95 latency | <200ms | 180ms | pass |

## 結論
- 採用 / 再試行 / 不採用

## 次アクション
- L2 設計へ反映する項目
```

必須:
- 仮説と結果の対応
- pass/fail の明示
- 次レイヤーへの入力を定義

---

## 6. G0.5 → G1.5 連結手順

1. G0.5 で企画-要件整合を確定
2. 競合調査で外部比較を補完
3. D-TECH-STACK で候補評価を固定
4. PoC で不確実性を検証
5. G1.5 で採否を確定して L2 へ接続

不整合時:
- 企画未整合は L1 差戻し
- PoC 未達は再仮説化または代替案決定

---

## 7. スキル連携

主連携:
- `skills/advanced/tech-selection/SKILL.md`
- `skills/workflow/design-doc/SKILL.md`

PoC 連携:
- `workflow/poc` が導入済みの場合は同スキルを優先
- 未導入環境では本スキルの PoC テンプレートを正本として運用

補助連携:
- `skills/common/documentation/SKILL.md`（文書品質）
- `skills/workflow/api-contract/SKILL.md`（契約観点）

---

## 8. 判定出力フォーマット

```yaml
gate_planning_result:
  g0_5:
    status: passed
    coverage: 100
    unmapped: 0
  g1_5:
    status: passed
    uncertainty_open: 0
    decision: adopt
  artifacts:
    - docs/research/competitive-YYYYMMDD.md
    - docs/D-TECH-STACK.md
    - docs/research/poc-result-YYYYMMDD.md
```

---

## 9. 失敗パターン

- 企画項目IDと L1 ID の紐付けが曖昧
- D-TECH-STACK が感覚評価のみ
- PoC が成功条件なしで実施される
- 調査結果が次フェーズへ接続されない

対処:
- ID ベースで追跡
- 評価軸と重みを明示
- kill criteria を先に固定

---

## 10. 完了判定

このスキルの完了条件:
- `docs/research/` に G0.5 用競合調査レポートが存在
- `docs/` または `adr/` に D-TECH-STACK が存在
- 企画項目カバー率 100%
- G1.5 の PoC 結果報告書が存在

