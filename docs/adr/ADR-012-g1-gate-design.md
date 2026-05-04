# ADR-012: G1 ゲート運用方針

> Status: Accepted (2026-05 implementation-aligned)
> Date: 2026-04-14
> Deciders: PM, TL

---

## Context

`phase.yaml` テンプレートには `G1: { status: pending }` が定義されている。過去の `helix gate` は G1 を valid_values に含めておらず、G1 の扱いが CLI と状態定義でずれていた。

この不整合は GAP-041 として検出された。ADR 作成時点で考えられた解釈:

1. **意図的な設計**: G1 は `helix gate` による整合チェック対象だが、完了判断は人間の PO/PM 承認を前提にする
2. **実装漏れ**: G1 も自動検証対象に含めるべき

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

**G1 は `helix gate G1` の fail-closed な整合チェック対象に含める。ただし、G1 の通過判断は PM+PO 承認を前提とし、CLI は承認前後の成果物整合を検証する補助線として扱う。**

### 運用ルール

- `helix gate G1` コマンドは L1 成果物の整合チェックとして利用する
- G1 通過は機械チェック結果に加えて PM+PO 承認を前提に記録する
- G1 の通過条件は **PM + PO の承認** を前提とし、要件定義書の受入条件に対して人間が判定

### 理由

1. **要件完了判定は本質的に人間の判断**: PO の要求と L1 要件定義書の整合性確認は自動化困難
2. **G0.5 で企画書との突合は既に自動化済み**: G1 段階ではより高次の合意形成が必要
3. **誤った自動判定の害**: G1 を自動で通すと、実装着手後に「本当は要件を満たしていなかった」が発覚するリスク

---

## Alternatives

### A1: G1 を `helix gate` から除外する

- 利点: 人間承認の境界が明確
- 欠点: G1 だけ手動更新となり、CLI 体験と phase.yaml の整合が崩れる

### A2: G1 そのものを削除

- 利点: valid_values 不整合が解消
- 欠点: L1→L2 遷移の明示的チェックポイントがなくなる、PO 承認プロセスが形骸化

---

## Consequences

### 正の影響

- **人間承認の重み維持**: G1 は PM+PO の承認が必須であることを明示
- **自動化の境界明確化**: 「何を自動化すべきでないか」が ADR として残る
- **CLI の一貫性**: G0.5〜G11 まで `helix gate` で扱いつつ、G1 の人間承認責任を維持できる

### 負の影響

- **自動承認と誤解される可能性**: G1 は機械チェックだけでは完了しないため、PM+PO 承認前提を運用文書で明示する必要がある

### リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| G1 未通過のまま G2 着手 | `helix sprint` / `helix gate G2` が G1 status を事前チェック |
| PO 承認なしで G1 を CLI 通過 | L8 受入時に L1 要件との突合で検知可能。運用上は PM+PO 承認記録を G1 通過条件に含める |
| valid_values 不整合の混乱 | `helix gate --help` と本 ADR を G1 利用可能な前提に合わせる |

---

## References

- `cli/helix-gate`（valid_values 検証）
- `cli/templates/phase.yaml`（G1 定義）
- [SKILL_MAP.md §オーケストレーションフロー](../../skills/SKILL_MAP.md)
- [ADR-001: Deliverable Matrix as Source of Truth](./ADR-001-deliverable-matrix-as-source-of-truth.md)
