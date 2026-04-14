# ADR-013: R4 専用ゲートの要否

> Status: Accepted
> Date: 2026-04-14
> Deciders: PM, TL

---

## Context

`helix-reverse` の stage_gates マッピングでは、R3 と R4 が同じ RG3 ゲートを参照している:

```bash
# cli/helix-reverse line 102-106
["R0"]="RG0"
["R1"]="RG1"
["R2"]="RG2"
["R3"]="RG3"
["R4"]="RG3"   # ← R3 と同一
```

これは GAP-042 として検出された。R4（Gap Register + Forward ルーティング）に専用ゲート RG4 が必要かを判断する必要がある。

### 各フェーズの責務

| フェーズ | 主成果物 | 検証対象 |
|---------|---------|---------|
| R0 | evidence-map.yaml | コード・DB・設定の証拠網羅性 |
| R1 | observed-contracts.yaml | API/DB/型の機械抽出 + characterization tests |
| R2 | as-is-design.md | アーキテクチャ復元 + ADR 推定 |
| R3 | intent-hypotheses.md | 要件仮説 + PO 検証（自開発の場合は N/A） |
| R4 | gap-register.md | Gap 集約 + Forward HELIX ルーティング |

R3 と R4 は性質が異なる:

- **R3**: 外部ステークホルダー（PO）との対話で要件仮説を検証
- **R4**: R0-R3 の成果から Gap を機械的に集約し、Forward フェーズに接続

---

## Decision

**R4 に専用 RG4 ゲートは設けない。R4 の完了判定は RG3 で兼用する方針を維持する**。

### 理由

1. **R4 は機械的集約**: R0-R3 で検証済みの情報から Gap を集約するのみ。新たな人間判定を要求しない
2. **Forward 接続は別プロセス**: R4 完了 → Forward HELIX 接続は `helix mode forward` + 個別 Sprint 起票で管理。ゲートでの検証対象ではない
3. **ゲート数の増加を回避**: 現在 RG0-RG3 の4ゲートで十分、RG4 追加は運用複雑化
4. **RGC（Reverse Gap Closure）で将来補完**: Forward での Gap 閉塞確認は RGC フェーズで実施（GAP-032、別途）

### 運用ルール

- R4 の完了条件は「R4-gap-register.md が存在し、全 Gap が Forward ルーティング済み」
- `helix reverse rgc`（将来実装）で Forward 側の閉塞確認を行う
- 現状の RG3 兼用は「Reverse フェーズ全体の完了ゲート」として解釈

---

## Alternatives

### A1: RG4 を新設して R4 の独立ゲートとする

- 利点: 各フェーズに固有ゲートが対応する一貫性
- 欠点: R4 は機械的集約のため、RG4 の自動チェック内容が R3 と重複、ゲート運用コスト増

### A2: R4 を R3 に統合する

- 利点: フェーズ数削減
- 欠点: Gap Register 作成は独立した成果物として価値が高い、統合は実装の大規模変更を要する

### A3: RG3 を RG3_4 に改名して兼用を明示する

- 利点: 名前で兼用を示せる
- 欠点: 他の ADR・ドキュメントとの整合性が崩れる、改名のコスト

---

## Consequences

### 正の影響

- **運用継続性**: 現状の helix-reverse 実装を変更不要
- **明示的な設計判断**: 「なぜ RG4 がないか」が ADR として記録される
- **RGC への接続**: R4 完了後の Forward 閉塞確認を RGC に委譲する設計を明確化

### 負の影響

- **命名の非対称性**: R0→RG0, R1→RG1, ... R3→RG3, R4→RG3 と非対称
- **新規開発者の混乱**: 「なぜ R4 だけ RG4 がないか」の疑問に ADR で回答する必要

### リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| R4 固有の品質問題を見逃す | R4-gap-register.md のテンプレート検証を `helix-reverse status` で実施 |
| 「R4 完了」の判定が曖昧 | 判定基準を SKILL_MAP / reverse-analysis スキルに明記 |
| RGC 未実装状態での運用 | GAP-032 完了まで手動で Forward 側進捗を確認 |

---

## References

- `cli/helix-reverse` line 102-106（stage_gates マッピング）
- [GAP-032: RGC CLI 未実装](/.helix/reverse/R4-gap-register.md)
- [skills/workflow/reverse-analysis/SKILL.md]
- [SKILL_MAP.md §HELIX Reverse](../../skills/SKILL_MAP.md)
