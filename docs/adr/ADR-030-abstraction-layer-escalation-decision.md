# ADR-030: 抽象化層 3 層 (スキル/ワークフロー/ハーネス) + エスカレーション機構採用判断

## Status

Proposed (2026-05-20、PLAN-097 と同時起票)

> 遷移予定: Proposed → Accepted (PLAN-097 tl-advisor adversarial check PASS 後、PO 承認で Accepted)

## Deciders

- PM (Opus、設計判断・最終承認)
- TL (Codex tl-advisor gpt-5.5 high、adversarial check)
- PO (yoshiyuki0907yn@gmail.com、Accepted 承認)

## Related

- [PLAN-097](../plans/PLAN-097-abstraction-layer-escalation.md): 本 ADR の実装 tree (本 ADR は PLAN-097 の L2 大局判断 snapshot)
- [PLAN-MM-001](../plans/PLAN-MM-001-v5-framework-master-plan.md): V5 全体構想 (親設計)
- [ADR-025](ADR-025-v5-framework-core-decision.md): V5 framework 本体採用判断 (本 ADR の前段)
- [ADR-027](ADR-027-plan-drift-detection-curator-decision.md): drift 検出 + Curator 採用判断 (escalation_matrix テーブルの根拠)
- PLAN-091: V5 framework 本体 (本 ADR の frontmatter 規約基盤)
- PLAN-093: drift 検出 + Curator (本 ADR のエスカレーション Curator 連動の実装担当)

---

## 業界 standard 参照 (Web 検索 3 query)

### Query 1: "abstraction layer architecture skills workflows orchestration framework"

| Source | URL | 引用箇所 |
|---|---|---|
| AWS Step Functions — Amazon States Language | https://docs.aws.amazon.com/step-functions/latest/dg/concepts-amazon-states-language.html | Decision §1 ワークフロー層 DSL 設計 (steps/retry/catch) |
| Temporal.io Workflow Abstraction | https://docs.temporal.io/workflows | Decision §1 DAG ステップ retry policy |
| Prefect Flows & Tasks (Prefect 3.x) | https://docs.prefect.io/3.0/develop/write-flows | Decision §1 スキル=Task / ワークフロー=Flow の抽象化整合 |
| Google Cloud Workflows | https://cloud.google.com/workflows/docs/overview | Decision §1 YAML ベースワークフロー定義 + 条件分岐 |

### Query 2: "escalation matrix automated agent human review promotion demotion"

| Source | URL | 引用箇所 |
|---|---|---|
| PagerDuty Escalation Policy Design | https://support.pagerduty.com/main/docs/escalation-policies | Decision §2 agent → council → human 3 段階の業界整合 |
| AWS Incident Manager Escalation Plans | https://docs.aws.amazon.com/incident-manager/latest/userguide/escalation.html | Decision §2 発火回数・時間経過による reviewer_type 切替 |
| Martin Fowler: Approval Workflow Pattern | https://martinfowler.com/bliki/ApprovalWorkflow.html | Decision §2 review_inject gate 設計 |
| Google SRE Book: Being On-Call | https://sre.google/sre-book/being-oncall/ | Decision §2 再失敗 M 回で上位 reviewer 自動昇格の SRE 実績 |

### Query 3: "rule promotion demotion engine software framework automation"

| Source | URL | 引用箇所 |
|---|---|---|
| Martin Fowler: Rules Engine bliki | https://martinfowler.com/bliki/RulesEngine.html | Decision §3 adaptive rules engine 原則 |
| AWS Curator Pattern (Well-Architected) | https://docs.aws.amazon.com/wellarchitected/latest/analytics-lens/data-governance.html | Decision §3 昇格/降格 Curator role |
| LaunchDarkly Flag Lifecycle | https://docs.launchdarkly.com/home/flags/flag-archive-delete | Decision §3 30 日/90 日 lifecycle 閾値 |
| Netflix Conductor Workflow Lifecycle | https://conductor.netflix.com/ | Decision §3 ワークフロー ACTIVE/DEPRECATED/ARCHIVED 状態遷移 |

---

## Context

### 現状の問題

HELIX V2 時点での知識・実行制御の管理状況:

1. **単層 SKILL_MAP**: 107 skills は「何をすべきか」の知識を定義するが、スキル間の呼び出し順序 (DAG) が非形式的。Sprint 標準 8 ステップは HELIX_CORE.md に記述されているが、機械実行可能な形式で宣言されていない

2. **手動エスカレーション**: レビュー注入強度が人間判断に依存。failure_log (PLAN-092 v35) に失敗データが蓄積されても、自動で reviewer_type が上がる機構がない

3. **降格機構の不在**: 使われなくなったルール・ワークフローを検出・archive する機構がない。LaunchDarkly / Netflix Conductor のような lifecycle 管理が存在しない

4. **失敗学習ループの断絶**: 失敗 → failure_log 蓄積 → Curator 昇格判定 (PLAN-093) までの道筋は設計されているが、エスカレーション tier (agent/council/human) への自動昇格・降格が実装されていない

### 解決すべき設計判断

以下の 3 点が L2 大局判断として本 ADR で凍結が必要:

1. **3 層構造採用**: スキル層 (既存) / ワークフロー層 (新設) / ハーネス層 (新設) の 3 層で抽象化レベルを分離するか
2. **エスカレーション 3 段階**: agent → council → human の reviewer_type 自動切替を採用するか
3. **降格閾値の業界標準採用**: 30 日/90 日 (LaunchDarkly) を HELIX の demotion_checker デフォルトとして採用するか

---

## Decision

### 決定 1: 3 層抽象化構造の採用

**採用する**: スキル層 / ワークフロー層 / ハーネス層の 3 層を採用する。

```
[層 1] スキル層    skills/*.md    何をすべきかの知識 (既存 SKILL_MAP 107 skills)
[層 2] ワークフロー層 workflows/*.yaml  どの順序で実行するか (DAG 宣言)
[層 3] ハーネス層  harness/*.yaml ゲート発火条件とレビュー強度の宣言
```

採用根拠:
- AWS Step Functions / Prefect の「Task (= スキル) → Flow (= ワークフロー) → State Machine (= ハーネス)」という 3 層抽象化は業界標準パターンである
- HELIX_CORE.md §Sprint Plan 標準構造 (8 ステップ) を workflows/l4-sprint-workflow.yaml として宣言的に表現することで、機械実行可能な形式に昇格できる
- 3 層の責務分離により「知識の更新 (スキル層)」「実行順序の変更 (ワークフロー層)」「ガードレール強度の変更 (ハーネス層)」が独立して可能になる

**既存 SKILL_MAP との関係**: 補完関係 (競合しない)。SKILL_MAP = スキルの知識定義、ワークフロー層 = スキルの組み合わせ順序。SKILL_MAP に 107 skills を追加・削除することはしない (デグレ禁止)。derived_from_failures メタデータ追加は PLAN-100 retrofit 担当。

### 決定 2: エスカレーション 3 段階の採用

**採用する**: agent → council → human の reviewer_type 自動切替を採用する。

| エスカレーションレベル | reviewer_type | 発火閾値 |
|---|---|---|
| L0 (Normal) | agent (pmo-sonnet) | 初期状態 |
| L1 (Elevated) | agent + tl-advisor | 同種失敗 N >= 3 OR 再失敗 M >= 1 |
| L2 (Council) | council (PM + TL + pmo-sonnet) | 同種失敗 N >= 7 OR 再失敗 M >= 3 |
| L3 (Human) | human (PO 直接) | 同種失敗 N >= 15 OR 再失敗 M >= 7 |

採用根拠:
- PagerDuty / AWS Incident Manager の「N 回発火でエスカレーション tier を上げ、MTTR 短縮と品質強化を両立する」設計は SRE の実証済みパターン (Google SRE Book 参照)
- HELIX の agent → council → human 3 段階は、HELIX の既存ロール体系 (pmo-sonnet / PM+TL / PO) と 1:1 対応する。新ロール追加不要
- Martin Fowler Approval Workflow Pattern の「ゲート発火条件次第で reviewer を切り替える」原則に合致

**P0 制約 (TL v5 round 5 指摘準拠)**: エスカレーション昇格は `escalation_engine.trigger()` → Curator → reviewer_type 切替まで自動化可。ただし L3 (human) への昇格後の **降格** は必ず human 承認後に `EscalationEngine.reset()` を呼び出す。自動降格 (PO 承認なし) は禁止。

### 決定 3: 降格閾値の業界標準採用

**採用する**: LaunchDarkly / Netflix Conductor の業界標準閾値をデフォルトとして採用する。

| 閾値 | 値 | 根拠 |
|---|---|---|
| stale_warning_days | 30 日 | LaunchDarkly flag archive 候補の業界標準 |
| archive_candidate_days | 90 日 | LaunchDarkly flag 削除候補の業界標準 |
| zero_violation_demotion_days | 90 日 | Netflix Conductor DEPRECATED 遷移タイムアウト参照 |

採用根拠:
- LaunchDarkly の 30 日/90 日 lifecycle 閾値は、feature flag 管理の業界標準として広く採用されている
- HELIX のルールは feature flag と類似した lifecycle (アクティブ → stale → archive) をたどる
- 閾値は `DemotionConfig` で上書き可能 (HELIX プロジェクト固有の調整を許容)

---

## Alternatives Considered

### 代替案 A: 単層 SKILL_MAP 維持 (棄却)

**棄却理由**: スキル間の実行順序が宣言的に管理されず、HELIX_CORE.md §Sprint Plan 標準構造の機械実行が不可能。失敗学習ループも手動のまま。V5 framework の #16 要素統合が達成できない。

### 代替案 B: 完全エージェント化 (棄却)

全ての判断を LLM agent に委ねる構成。

**棄却理由**: 本番影響・認証・PII に関わる判断を agent が自動確定させることは HELIX の escalation 原則 (人間確認必須) に違反する。L3 (human) へのエスカレーションが失われ、PM/PO の最終判断権が侵食される。TL v5 round 5 P0 指摘「承認なし task pop は HELIX discipline 破壊」と同じ問題。

### 代替案 C: 2 層 (スキル + ハーネス) 構成 (棄却)

ワークフロー層を省略し、スキルとハーネスの 2 層にする案。

**棄却理由**: スキル間の組み合わせ順序 (DAG) を宣言できず、Sprint 標準 8 ステップの機械実行に必要な依存関係制御が不可能。AWS Step Functions / Prefect も 2 層ではなく 3 層 (Task/Flow/State) を採用している。

---

## Consequences

### Positive

1. **再利用 workflow 標準化**: l4-sprint-workflow.yaml 等の標準 workflow が共有資産として管理される。新 PLAN 起票時に既存 workflow を参照・拡張できる
2. **自動エスカレーション**: failure_log の蓄積が reviewer_type の自動強化につながり、再失敗リスクを低減する
3. **failure → 学習自動化**: Curator (PLAN-093) ↔ escalation_engine の連動で、失敗から学習してルールが自動的に強化される closed loop が完成する
4. **降格 lifecycle**: demotion_checker による未使用ルールの archive 候補化で、HELIX のルールベースが肥大化しない

### Negative

1. **DSL 設計コスト**: workflows/*.yaml / harness/*.yaml の DSL を設計・実装するコストが発生する (Phase 1-2 で対応)
2. **既存 SKILL_MAP retrofit 必要**: derived_from_failures メタデータ追加は PLAN-100 で別途 retrofit が必要。本 ADR 範囲外
3. **レビュー注入の人間負荷管理**: L2 (council) / L3 (human) エスカレーションが増加した場合、PO の review 負荷が高まる可能性。閾値設計 (§決定 3) で頻度を抑制する

### Risks

| リスク | 影響 | 緩和策 |
|---|---|---|
| Curator (PLAN-093) 未実装でエスカレーション連動不能 | Phase 2-3 が blocks される | Phase 2 の前提として PLAN-093 draft 以上を要求 (§11 Phase 2 前提) |
| escalation_matrix テーブル未初期化 | escalation_engine が fail | fail-open 設計 (L0 自動 INSERT) で対応 |
| 降格の自動実行による HELIX discipline 違反 | PO 承認なし task pop と同等の問題 | `demote()` は human 確認後のみ呼び出し可の設計ルール (§10.3) |

---

## Implementation Plan

PLAN-097 の 3 Phase で段階導入する。

| Phase | 内容 | 前提 |
|---|---|---|
| Phase 1 (本 PLAN 起票) | ADR-030 + workflows/ harness/ 骨格 YAML + DSL JSON Schema | なし |
| Phase 2 | escalation_engine.py + demotion_checker.py 実装 + helix doctor 追加 | PLAN-093 draft 以上 |
| Phase 3 | harness interpreter + workflow validate CLI + Curator 双方向連携 | PLAN-092 + PLAN-093 完了 |

詳細: [PLAN-097 §11](../plans/PLAN-097-abstraction-layer-escalation.md#11-段階導入計画-p1--p2--p3)
