---
name: reverse-rgc
description: Reverse Gap Closure スキル。Forward HELIX の L6/L8 pass 後に Reverse で特定した gap が閉塞したか検証
metadata:
  helix_layer: R4
  triggers:
    - RGC Gap Closure 検証時
    - Forward 通過後の Reverse 閉塞確認時
    - RGC Evidence Bundle 生成時
  verification:
    - "RGC Evidence Bundle が docs/reverse/rgc/ に存在"
    - "各 gap に closure_evidence (test ref / deploy ref / PO承認) が記載"
compatibility:
  claude: true
  codex: true
---

# Reverse RGC スキル

## 適用タイミング

このスキルは以下の場合に読み込む:
- Forward HELIX の L6/L8 通過後
- Reverse で特定した gap の閉塞確認を実施する時
- `docs/reverse/rgc/` 配下に証跡束を作成する時

---

## 1. RGC の目的

RGC は Forward 実装完了後に、Reverse で発見した gap が本当に閉じたかを再検証する層である。

目的:
- Forward pass と Reverse gap 閉塞を接続する
- `gap_register` の open/partial/closed を確定する
- 閉塞済み gap の証拠を束ねる
- 未閉塞 gap を次ループへ戻す

---

## 2. 前提条件

実行前に以下を満たす:
- Forward の L6 または L8 が `pass`
- `docs/reverse/gap_register.md` が存在
- 各 gap に owner と routing が定義済み

補足（重要）:
- `gate-policy.md` 正本では「RGC は CLI 未実装、Forward L6/L8 pass 後に手動実施」と定義される
- 現行 `cli/helix-reverse` には `rgc` サブコマンドが存在する
- ただし現実装は「集計表示補助」であり、閉塞判定の完全自動化ではない
- よって本スキルでは **手動検証を正** とし、CLI は補助として利用する

---

## 3. 入力と出力

### 入力
- `docs/reverse/gap_register.md`
- Forward 側の検証証跡（テスト/デプロイ/承認）
- `skills/tools/ai-coding/references/gate-policy.md`

### 出力
- `docs/reverse/rgc/RGC-evidence-bundle.md`
- 必要に応じて `docs/reverse/rgc/RGC-summary.yaml`

---

## 4. Evidence Bundle テンプレート

```markdown
# RGC Evidence Bundle

## メタ情報
- generated_at: YYYY-MM-DD
- source_gap_register: docs/reverse/gap_register.md
- forward_status: L6 pass / L8 pass

## Gap Closure Matrix
| gap_id | closure_status | closure_evidence | test_ref | deploy_ref | po_approval |
|---|---|---|---|---|---|
| GAP-001 | closed | 入力値バリデーション追加で再発なし | tests/api/order.spec.ts#negative_amount | deploy-2026-04-16-01 | PO-2026-04-16 |
| GAP-002 | partial | 設計修正は完了、移行タスク残 | tests/arch/service-boundary.spec.ts | deploy-2026-04-16-01 | pending |

## Open Gap
- GAP-002: 残課題と次 routing を明記
```

必須列:
- `gap_id`
- `closure_evidence`
- `test_ref`
- `deploy_ref`
- `po_approval`

---

## 5. 閉塞判定ルール

判定値:
- `closed`: 再発防止証拠あり、受入条件を満たす
- `partial`: 一部解消、残課題あり
- `open`: 未解消

判定基準:
- test ref が再現テストとして有効
- deploy ref が該当修正を含む
- PO 承認が必要な gap は承認が付与済み

判定禁止:
- 証拠が口頭のみ
- test/deploy のいずれかが欠けている

---

## 6. `helix-reverse rgc` 連携

利用方法（補助）:

```bash
helix-reverse rgc
```

想定用途:
- `R4-gap-register` ベースで open/partial/resolved の概数を把握
- 優先度別の未閉塞 gap を抽出

注意:
- CLI 出力だけでは `closure_evidence` は充足しない
- 最終判定は Evidence Bundle 記録で行う

---

## 7. R4 gap_register 参照ルール

RGC は R4 出力を正本入力として扱う。

参照時の必須チェック:
- `gap_id` が一意
- `routing` が空でない
- `status` が open/partial/closed のいずれか

不整合時:
- R4 に差し戻して gap_register を修正
- RGC を一時 `blocked` にする

---

## 8. L8 受入との紐付け

RGC は L8 受入結果と独立ではなく、次の関係を持つ:
- L8 pass は Forward 受入の証拠
- RGC pass は Reverse gap 閉塞の証拠

紐付け方法:
- Evidence Bundle に `forward_acceptance_ref` を記録
- PO 承認が必要な gap は `po_approval` を必須化

例:

```yaml
acceptance_link:
  forward_acceptance_ref: L8-acceptance-2026-04-16
  po_approval: PO-2026-04-16
```

---

## 9. open_gap 残存時のエスカレーション

open または partial が残る場合:
1. 残存 gap を列挙
2. 次の routing（L1-L4）を再設定
3. owner と期限を再設定
4. 人間承認が必要な項目をエスカレーション

必須エスカレーション対象:
- 本番影響
- 認証/決済
- 個人情報
- ライセンス

---

## 10. 運用シーケンス

```text
Forward L6/L8 pass
  -> R4 gap_register 読み込み
  -> Evidence Bundle 作成
  -> gap ごとに closed/partial/open 判定
  -> open_gap の再 routing
  -> RGC 結果確定
```

---

## 11. 完了判定

RGC を `done` とする条件:
- `docs/reverse/rgc/RGC-evidence-bundle.md` が存在
- 全 gap に `closure_evidence` が記載
- open_gap は次 routing と owner が設定済み
- L8 受入参照が記録済み

