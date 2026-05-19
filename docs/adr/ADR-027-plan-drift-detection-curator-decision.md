# ADR-027: drift 検出 + Curator 自動化採用判断

## Status

Proposed (2026-05-20)

> proposed (2026-05-20、pmo-sonnet 起票)

## Deciders

- PM (Opus)
- PO (yoshiyuki0907yn@gmail.com)

## Related

- ADR-025 (V5 framework 本体採用判断)
- ADR-026 (PostToolUse 自動登録 + helix.db v35 schema 採用判断)
- PLAN-091 (framework 本体)
- PLAN-092 (PostToolUse 自動登録 + schema v35)
- PLAN-093 (drift 検出 + dashboard + Curator 実装)
- PLAN-097 (抽象化層 + エスカレーション接続)

---

## 業界 standard 参照 (Web 検索 3 query)

### Query 1: "drift detection software architecture documentation"

- **Architectural Drift: The Hidden Nemesis of Long-lived Software** — InfoQ 2024
  - https://www.infoq.com/articles/architectural-drift/
  - 「設計意図と実装の乖離を定期的に機械検出することがアーキテクチャ品質維持の最重要施策」
- **ArchUnit — Architecture as Code** (TNG Technology Consulting)
  - https://www.archunit.org/
  - 設計ルールをコードとして記述し、CI で自動テストする OSS アーキテクチャ準拠ツール
- **Continuous Architecture Compliance (CAC)** — ThoughtWorks Technology Radar
  - https://www.thoughtworks.com/radar/techniques/continuous-architecture-compliance
  - CI パイプラインへのアーキテクチャ準拠チェック組み込みを Adopt 推奨

### Query 2: "automated rule promotion demotion curator engine design pattern"

- **Curator Pattern in Data Governance** — AWS Well-Architected Framework Data Analytics
  - https://docs.aws.amazon.com/wellarchitected/latest/analytics-lens/data-governance.html
  - 発火回数・品質スコアに基づく自動昇格/降格ライフサイクル管理の Curator role 規定
- **Feature Flag Lifecycle (LaunchDarkly)**
  - https://docs.launchdarkly.com/home/flags/flag-archive-delete
  - 30 日 stale = archive 候補、90 日 = 削除候補という lifecycle 閾値設計の業界標準
- **Adaptive Rules Engine (Martin Fowler bliki)**
  - https://martinfowler.com/bliki/RulesEngine.html
  - 発火データ蓄積によるルール優先度自動調整を提唱する adaptive principle

### Query 3: "Linear Jira project progress dashboard developer tools"

- **Linear Progress Tracking** — Linear Docs
  - https://linear.app/docs/project-progress
  - Milestone × Status 進捗バー + blocked 赤ハイライトの可視化設計
- **Jira Work Item Hierarchy** — Atlassian Documentation
  - https://support.atlassian.com/jira-software-cloud/docs/what-is-an-epic/
  - Epic → Story → Task 階層と progress % 表示設計
- **GitHub Projects Roadmap View** — GitHub Documentation
  - https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/changing-the-layout-of-a-view
  - Date × Status クロス集計の Roadmap ビュー設計

---

## Context

### 問題

HELIX V2 構築の進行につれて、PLAN doc と実実装の間に以下 4 種類の drift が発生する:

1. **generates drift**: PLAN `generates:` に記載された成果物が実ファイルとして存在しない
2. **freshness drift**: status=active の PLAN が 30 日以上更新されず放置
3. **recovery drift**: kind=recovery の PLAN が 7 日以上更新されず stale 化
4. **dependency cycle**: requires/blocks の依存グラフが cycle を形成

また、`failure_log` テーブル (PLAN-092 v35) に蓄積された失敗データが活用されておらず、以下の問題がある:

- 同種失敗の再発が自動昇格されない
- 違反検出ゼロが続いても自動降格されない
- handover メモが肥大化し、sprint_progress DB から引けば不要な情報を毎回手書き

### 業界 standard との対応

- ArchUnit / CAC の「CI でアーキテクチャ準拠を機械検証する」思想を HELIX helix doctor に適用
- AWS Curator pattern の「発火回数ベース昇格/降格」をルールライフサイクルに適用
- LaunchDarkly の 30 日/90 日 lifecycle 閾値を HELIX のデフォルト閾値設計根拠に採用
- Linear / GitHub Projects の Milestone × Status 進捗可視化を `helix dashboard plan-progress` 設計根拠に採用

---

## Decision

以下の 3 機能を PLAN-093 で実装する:

### 決定 1: helix doctor による drift 検出 (advisory → fail-close 段階)

helix doctor に 4 check を追加する:

| Check | 対象 | advisory | fail-close |
|-------|------|---------|------------|
| check_plan_drift | generates ↔ 実ファイル突合 | P1 | P2 以降 |
| check_plan_freshness | active PLAN 30 日未更新 | 常時 | 追加予定なし |
| check_recovery_plan_freshness | recovery PLAN 7 日未更新 | 常時 | 追加予定なし |
| check_plan_dependency_cycle | depends cycle 検出 | なし | 即時 fail-close |

**採用根拠**:
- ArchUnit / CAC 思想: 「アーキテクチャルールを CI テストとして記述し、自動化」
- 段階 advisory → fail-close は PLAN-089 (gate fail-close 段階遷移) の確立手法と整合
- dependency cycle は設計上の致命的矛盾であるため即時 fail-close が妥当

### 決定 2: `helix dashboard plan-progress` による進捗可視化

`sprint_progress` テーブルを読み取り、Layer A/B/C × PLAN 単位の進捗バーを表示する。

**採用根拠**:
- Linear / GitHub Projects の Milestone 別進捗可視化思想
- handover メモ肥大化の解消 (DB から引けば手書き不要)
- blocked PLAN の赤ハイライトは Linear 設計に倣う

### 決定 3: Curator 自動化 (failure_log 分析 + 昇格/降格判定 + レビュー注入 3 段階)

`helix_improvement_plan_draft.md` Phase 4/6 を以下の実装で具体化する:

- **CuratorEngine**: failure_log 集計 → 昇格候補 / refactor_degrade_pattern 集計 → 降格候補
- **EscalationMatrix**: failure_count に応じて agent / council / human のレビュー種別を決定

閾値設計 (業界 standard 準拠):
- 昇格閾値: failure_count >= 3 (council level)
- 降格閾値: last_fired > 30 日 (LaunchDarkly 30 日 stale 準拠)
- archive 閾値: last_fired > 90 日 (LaunchDarkly 90 日削除候補準拠)

**採用根拠**:
- AWS Curator pattern: 発火回数ベースの自動昇格/降格
- Martin Fowler adaptive rules engine: ルール優先度の自動調整

---

## Alternatives

### 代替 A: 手動 audit のみ (棄却)

- 理由: PLAN 数が増加するほど手動 audit の見落としリスクが増大。ArchUnit / CAC の業界知見と逆行。

### 代替 B: 完全自動 (Curator が自動 promote / archive) (棄却)

- 理由: HELIX discipline では重大判断は人間確認を残す原則 (HELIX_CORE.md §エスカレーション)。failure_count >= 5 の重大ルールは human escalation を必須化する。

### 代替 C: 本 Decision 採用 (採用)

- advisory → fail-close 段階導入で blast radius を抑制しつつ機械化を段階進展
- Curator はレビュー注入 3 段階で「完全自動」と「手動のみ」の中間を実現

---

## Consequences

### Positive

- generates drift を自動検出し、PLAN と実実装の乖離を早期発見できる
- dashboard で blocked PLAN が即座に可視化され、進行阻害要因を早期解消できる
- Curator が stale ルールを自動降格し、failure_log の肥大化を防ぐ
- handover メモが短縮化され、sprint_progress DB から引く設計に移行できる

### Negative

- Curator の閾値 (30 日/90 日) が最適でない場合、誤判定リスクがある
  - 緩和策: 閾値は `--freshness-days` / `--recovery-days` でパラメータ化し、運用で調整可能にする
- check_plan_dependency_cycle の DFS が大規模 dependency graph でパフォーマンス劣化する可能性
  - 緩和策: PLAN 数は通常 O(100) 以下、DFS は O(V+E) で実用上問題なし
- EscalationMatrix の review_level 決定ロジックが PLAN-097 (抽象化層) 完成前は不完全
  - 緩和策: PLAN-093 Phase 1-2 (advisory + dashboard) を先行し、Phase 3 (Curator) は PLAN-097 接続後に実装

---

## Implementation Plan

### PLAN-093 段階導入

| Phase | 内容 | DoD |
|-------|------|-----|
| P1 (Sprint .1) | helix doctor 4 check advisory 追加 | test_plan_drift_checker.py 9 ケース PASS |
| P2 (Sprint .2) | dashboard plan-progress subcommand | `--json` valid JSON、既存 dashboard PASS |
| P3 (Sprint .3-.4) | Curator 実装 | test_curator_engine.py 6 ケース PASS |
| P4 (Sprint .5) | fail-close 昇格 + PLAN-097 接続 | cycle 検出 exit 2 / PLAN-097 統合テスト PASS |

### PLAN-097 連動

PLAN-097 (抽象化層 + エスカレーション) が起票・実装完了した後、EscalationMatrix の `inject_review` が PLAN-097 の抽象化階層 (skills/ / workflows/ / harness/) へ escalation 結果を渡すインターフェースを確立する。

インターフェース仕様 (暫定):
```python
# EscalationMatrix.inject_review の返り値型
{
  "plan_id": str,
  "candidate_type": "promotion" | "demotion" | "archive",
  "review_level": "agent" | "council" | "human",
  "reviewer": str,          # e.g. "pmo-sonnet" / "tl-advisor" / "human"
  "context": str,           # failure summary or stale summary
  "escalation_layer": str,  # "skills" | "workflows" | "harness" (PLAN-097 連動)
}
```

この型は PLAN-097 起票時に確定し、ADR-027 を retrofit する。
