# ADR-028: PoC = Scrum × Reverse 連携 matrix 採用判断

## Status

Proposed (2026-05-20、PLAN-095 と同時起票)

> 遷移予定: Proposed → Accepted (PLAN-095 tl-advisor adversarial check PASS + PO 承認で Accepted)

## Deciders

- PM (Opus、設計判断・最終承認)
- TL (Codex tl-advisor gpt-5.5 high、adversarial check)
- PO (yoshiyuki0907yn@gmail.com、Accepted 承認)

## Supersedes

なし (新規採用判断)

## Related

- [PLAN-095](../plans/PLAN-095-poc-scrum-reverse-matrix.md): 本 ADR の実装 tree
- [PLAN-MM-001](../plans/PLAN-MM-001-v5-framework-master-plan.md): V5 全体構想
- [PLAN-091](../plans/PLAN-091-v5-framework-core.md): frontmatter 語彙正本 (本 ADR の depends)
- [ADR-025](ADR-025-v5-framework-core-decision.md): V5 framework 本体採用判断 (前段 L2 凍結)
- [ADR-026](ADR-026-posttooluse-plan-auto-register-decision.md): poc_validation_log table の DB 基盤

---

## 業界 standard 参照 (PLAN-095 §3 と同一 Sources)

### 3 query 検索結果

| Query | 参照 | Source URL | 引用箇所 |
|---|---|---|---|
| Q1: "proof of concept hypothesis driven development lifecycle 2026" | Scrum.org — What is a Spike? | https://www.scrum.org/resources/what-is-a-spike | Scrum 6 type 分類の根拠 (spike 公式定義) |
| Q1 | Agile Alliance — Spikes | https://agilealliance.org/glossary/spikes/ | hypothesis-test / tech-spike / design-spike 分類の根拠 |
| Q1 | Martin Fowler — Exploratory Testing | https://martinfowler.com/bliki/ExploratoryTesting.html | ux-spike 検証アプローチの業界整合 |
| Q2: "reverse engineering existing code documentation framework 2026" | OMG MOF 2.0 | https://www.omg.org/spec/MOF/2.0/PDF | Reverse type: code/design の設計復元モデル根拠 |
| Q2 | arc42 — Reverse Engineering Integration | https://docs.arc42.org/section-1/ | R0-R4 段階的文書化の業界整合 |
| Q2 | Refactoring.guru — Pattern Catalog | https://refactoring.guru/design-patterns/catalog | Reverse type: normalization (設計 drift 正規化) の参照 |
| Q3: "Scrum spike PoC validation lifecycle 2026" | SAFe — Spikes | https://www.scaledagileframework.com/spikes/ | perf-spike / security-spike の SAFe enabler spike との対応 |
| Q3 | Mike Cohn — Spikes | https://www.mountaingoatsoftware.com/blog/spikes | time-box + validated 判定基準の業界整合 |
| Q3 | Basecamp Shape Up — Chapter 6 | https://basecamp.com/shapeup/1.5-chapter-06 | PoC confirmed/rejected 決定フローの業界整合 |

### 業界 standard との整合まとめ

- **Scrum spike (Scrum.org)**: spike は time-boxed な実験。結果を confirmed/rejected として共有するフローが本 ADR の S4 decide --confirmed と一致する。
- **SAFe enabler spike**: perf-spike / security-spike は SAFe enabler story (技術的不確実性解消) に相当する。Reverse type: upgrade / normalization との対応が取れている。
- **arc42 逆引き設計**: R0 で証拠収集し段階的に設計文書を復元するアプローチは arc42 の「目的から始め、制約・コンテキストを明示する」思想と整合する。
- **Shape Up 不確実性削減**: Shape Up の「rabbit hole の回避」と「証拠ベースの Bet」は本 matrix の「PoC 成果を Reverse で文書化してから Forward 本実装に橋渡し」に対応する。

---

## Context

### C1. 現状の問題

HELIX V2 構築において、Scrum モード (S0-S4) と Reverse モード (R0-R4) は独立したフローとして設計されており、以下の問題が顕在化した。

| 問題 | 影響 |
|---|---|
| S4 decide --confirmed 後の Reverse 橋渡しが手動 | PoC 成果が Forward 本実装で再実装される属人的エラーが発生 |
| どの Scrum type をどの Reverse type で文書化すべきかのルールがない | 毎回 PM + TL の相談が必要で自動化できない |
| poc_validation_log の操作 module が未実装 | helix.db v35 に schema だけ存在し追跡できない |

### C2. V5 framework での位置付け

V5 framework 18 要素の **#14** として確立: 「PoC = Scrum × Reverse 連携 matrix (Scrum 6 type × Reverse 5 type = 30 cell)」。

PLAN-079 (UPS + SRF) が確立した「Scrum interlocked chain」の延長として、本 ADR は Scrum 6 type × Reverse 5 type の組み合わせを機械決定可能な matrix で定義する。

### C3. 既存 CLI との関係

- `cli/helix-scrum`: `helix scrum decide` が既実装。`--reverse-merge` フラグ追加が必要。
- `cli/helix-reverse`: `helix reverse from-scrum` が既実装 (`cmd_from_scrum`)。`--scrum-hypothesis` フラグ追加が必要。
- 既存 `VALID_SCRUM_TYPES` (poc/ui/unit/sprint/post-deploy) とは別概念。本 ADR の Scrum 6 type は上位仮説分類レイヤー。

---

## Decision

### D1. 30 cell matrix の採用

Scrum 6 type × Reverse 5 type の 30 cell matrix を rule table として定義し、CLI で機械決定を実現する。

```
Scrum 6 type: hypothesis-test / tech-spike / design-spike / perf-spike / security-spike / ux-spike
Reverse 5 type: code / design / upgrade / normalization / fullback
```

各 cell に Primary (デフォルト routing) / Alternative (明示指定で許可) / - (通常不使用) を割り当てる。

**matrix 概要 (詳細は PLAN-095 §7)**:

| Scrum type | Primary Reverse type | Alternative |
|---|---|---|
| hypothesis-test | code | design, fullback |
| tech-spike | design | code, upgrade |
| design-spike | design | normalization, fullback |
| perf-spike | upgrade | normalization, fullback |
| security-spike | normalization | code, design |
| ux-spike | design | normalization, fullback |

### D2. CLI 拡張設計

```bash
# S4 Decide + Reverse 自動 routing
helix scrum decide --confirmed --reverse-merge [--scrum-type <type>] [--reverse-type <type>]

# Reverse 側の from-scrum 拡張
helix reverse from-scrum --scrum-loop-id <id> [--reverse-type <type>] [--scrum-hypothesis <id>]
```

### D3. poc_validation_log 記録

`helix scrum decide --confirmed --reverse-merge` 実行時に `poc_validation_log` テーブルへ自動記録する:

```
{hypothesis_id, scrum_type, reverse_type, result="confirmed", timestamp}
```

### D4. 段階導入

- **P1** (本 PLAN 起票): matrix doc 化 + ADR-028 凍結
- **P2** (PLAN-095 Phase 2): CLI 拡張実装 (PLAN-092 DB 基盤確立後)
- **P3** (PLAN-095 Phase 3): テスト + poc_validation_log 自動記録

---

## Consequences

### Positive

| 結果 | 詳細 |
|---|---|
| PoC → Reverse → Forward の連携自動化 | S4 --reverse-merge で R0 を自動起動、手動橋渡しエラーが解消 |
| 仮説 → 設計 → 実装の trace 確立 | poc_validation_log で「どの仮説が、どの設計を通じて、どの Forward 実装に繋がったか」を DB 追跡可能 |
| Scrum type 選択のガイドライン整備 | 6 type の明示的な分類で仮説の性質を明確化、PM/TL の判断コスト削減 |
| 既存 CLI との後方互換性 | 新規フラグは optional、既存コマンドはそのまま動作 |

### Negative

| リスク | 緩和策 |
|---|---|
| matrix 設定変更コスト | matrix は `scrum_reverse_matrix.py` に集約、設定変更時は 1 箇所のみ修正 |
| 30 cell 全 case 検証コスト | `test_scrum_reverse_matrix.py` で 30 cell 自動検証、CI に組み込み |
| Primary/Alternative の境界判断 | tl-advisor adversarial check で matrix 設計を検証後に確定 |
| PLAN-092 への依存 | poc_validation_log table が未実装の場合 Phase 2 は着手不可。Phase 1 (doc 化) は PLAN-092 不要 |

---

## Alternatives Considered

### Alt-1: Scrum / Reverse 独立維持 (棄却)

**棄却理由**: S4 confirmed 後の手動橋渡しが属人的エラーの温床となっている。自動 routing なしでは V5 framework の工程自動化目標が達成できない。

### Alt-2: 6×5 を 1-1 mapping に简化 (棄却)

**棄却理由**: 1-1 mapping では柔軟性が失われる。例えば `tech-spike` で具体的な実装コードが生成された場合は `code` type が適切だが、1-1 では `design` type しか選べない。Primary + Alternative の 2 層設計が最適。

### Alt-3: Scrum type を既存 VALID_SCRUM_TYPES に統合 (棄却)

**棄却理由**: 既存 `VALID_SCRUM_TYPES` は helix.db の scrum_trigger テーブル種別であり、上位仮説検証モードの分類とは別レイヤー。統合すると既存 DB schema への破壊的変更が必要で、PLAN-092 の schema 設計と衝突する。別レイヤーとして独立させることが正しい。

### Alt-4: 本 Decision (採用)

**採用理由**:
- 30 cell matrix で機械決定可能にすることで、PM/TL の手動判断を削減
- Primary + Alternative の 2 層設計で柔軟性を維持しながら deault routing を自動化
- 既存 CLI への後方互換性を保ちながら段階導入 (P1: doc → P2: CLI → P3: テスト)

---

## Implementation Plan

本 ADR の実装は PLAN-095 の 3 Phase で行う。

| Phase | 内容 | 依存 |
|---|---|---|
| P1 | matrix doc 化 + 本 ADR 起票 | PLAN-091 (語彙正本) |
| P2 | CLI 拡張実装 | PLAN-092 (poc_validation_log table 実装済み) |
| P3 | テスト + 自動記録確認 | P2 完了 |

詳細: [PLAN-095 §10 段階導入計画](../plans/PLAN-095-poc-scrum-reverse-matrix.md#10-段階導入計画)
