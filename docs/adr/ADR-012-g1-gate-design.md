# ADR-012: G1 ゲート運用方針

> Status: Accepted
> Date: 2026-04-14
> Deciders: PM, TL

---

## Context

`phase.yaml` テンプレートには `G1: { status: pending }` が定義されている一方、`helix-gate` コマンドの valid_values 正規表現 `^G(0\.5|[2-7])$` には G1 が含まれていない。

この不整合は GAP-041 として検出された。考えられる解釈:

1. **意図的な設計**: G1 は helix-gate による自動検証の対象外（人間の PO/PM 承認のみ）
2. **実装漏れ**: G1 も自動検証すべきだが未実装

SKILL_MAP.md のオーケストレーションフローでは G1 は以下のように定義されている:

```
L1  要件定義（要件構造化 + 受入条件定義）
  ↓ G0.5 企画突合ゲート       [PM]       ★企画書の全項目が L1 に反映されているか
  ↓ G1   要件完了ゲート         [PM+PO]
  ↓ G1.5 PoC ゲート            [TL+PM]    条件付き
```

G1 の担当は **[PM+PO]** であり、自動化よりも人間の承認が本質的に必要なゲート。

---

## Decision

**G1 は helix-gate の自動検証対象外とし、phase.yaml の status 更新のみを行う運用とする**。

### 運用ルール

- `helix gate G1` コマンドは **サポートしない**（現状の valid_values を維持）
- G1 通過は `yaml_parser.py write phase.yaml gates.G1.status passed` で手動記録
- G1 の通過条件は **PM + PO の承認** を前提とし、要件定義書の受入条件に対して人間が判定
- 今後 `helix-gate` に G1 を追加する場合は、対話式プロンプト（PO/PM の承認入力）を必須とする

### 理由

1. **要件完了判定は本質的に人間の判断**: PO の要求と L1 要件定義書の整合性確認は自動化困難
2. **G0.5 で企画書との突合は既に自動化済み**: G1 段階ではより高次の合意形成が必要
3. **誤った自動判定の害**: G1 を自動で通すと、実装着手後に「本当は要件を満たしていなかった」が発覚するリスク

---

## Alternatives

### A1: G1 を helix-gate に追加して自動検証

- 利点: 一貫した CLI 体験、valid_values の完全性
- 欠点: 要件完了の自動判定は技術的に困難、AI 判定で通してしまうと PO 承認が形骸化

### A2: G1 そのものを削除

- 利点: valid_values 不整合が解消
- 欠点: L1→L2 遷移の明示的チェックポイントがなくなる、PO 承認プロセスが形骸化

---

## Consequences

### 正の影響

- **人間承認の重み維持**: G1 は PM+PO の承認が必須であることを明示
- **自動化の境界明確化**: 「何を自動化すべきでないか」が ADR として残る
- **CLI の一貫性**: G2〜G7 の自動検証モデルと G1 の人間承認モデルが分離される

### 負の影響

- **運用が2系統になる**: G0.5, G2-G7 は `helix gate`, G1 は手動 `yaml_parser.py write` が必要
- **運用ミス可能性**: G1 の通過記録を忘れる可能性（ただし `helix status` 表示で気付ける）

### リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| G1 未通過のまま G2 着手 | `helix-sprint` / `helix-gate G2` が G1 status を事前チェック（将来拡張） |
| PO 承認なしで G1 を手動通過 | L8 受入時に L1 要件との突合で検知可能 |
| valid_values 不整合の混乱 | 本 ADR を `helix gate --help` にリンク表示（将来拡張） |

---

## References

- `cli/helix-gate` line 57-64（valid_values 検証）
- `cli/templates/phase.yaml`（G1 定義）
- [SKILL_MAP.md §オーケストレーションフロー](../../skills/SKILL_MAP.md)
- [ADR-001: Deliverable Matrix as Source of Truth](./ADR-001-deliverable-matrix-as-source-of-truth.md)
