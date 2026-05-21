---
plan_id: PLAN-097
title: "PLAN-097: 抽象化層 3 層構造 (スキル/ワークフロー/ハーネス) + エスカレーション機構 (helix_improvement Phase 4 統合)"
layer: L2
kind: impl
status: draft
size: L
drive: agent
created: 2026-05-20
revised: 2026-05-20 (pmo-sonnet 初回起票、PLAN-091 Round 2 修正版整合済)
owner: PM
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・ADR-030 承認・Curator 設計判断・P0 エスカレーション対応"
  - role: pmo-sonnet
    slot_label: "PMO — ドキュメントチェック・3 層構造整合確認・draft 起票支援"
  - role: se
    slot_label: "SE — escalation_engine.py / demotion_checker.py 実装・harness DSL 検証"
  - role: docs
    slot_label: "Docs — workflows/ harness/ 骨格 YAML + DSL spec 起草"
generates:
  - artifact_path: workflows/
    artifact_type: workflow_config
  - artifact_path: harness/
    artifact_type: workflow_config
  - artifact_path: cli/lib/escalation_engine.py
    artifact_type: python_module
  - artifact_path: cli/lib/demotion_checker.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_escalation_engine.py
    artifact_type: test
  - artifact_path: docs/adr/ADR-030-abstraction-layer-escalation-decision.md
    artifact_type: adr_snapshot
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-091
    - PLAN-100
    - PLAN-MM-001
    - PLAN-093-plan-drift-detection-curator
  blocks: []
related_adr:
  - ADR-030-abstraction-layer-escalation-decision
related_docs:
  - docs/plans/PLAN-MM-001-v5-framework-master-plan.md
  - docs/plans/PLAN-091-v5-framework-core.md
  - docs/plans/PLAN-093-plan-drift-detection-curator.md
  - docs/adr/ADR-027-plan-drift-detection-curator-decision.md
  - helix_improvement_plan_draft.md §Phase 4
  - skills/SKILL_MAP.md (既存 107 skills = 層 1 スキル層の現状実装)
test_design:
  unit: cli/lib/tests/test_escalation_engine.py (本 PLAN §12 定義)
  integration: cli/lib/tests/test_demotion_checker.py (本 PLAN §12 定義)
---

# PLAN-097: 抽象化層 3 層構造 + エスカレーション機構

## §1. 目的

HELIX の実行制御知識を **3 層抽象化** (スキル層 / ワークフロー層 / ハーネス層) に整理し、
失敗データ (failure_log、refactor_degrade_pattern) から自動的にルールを昇格・降格する
**エスカレーション機構** を構築する。

これにより以下の問題を解消する:

1. 既存 SKILL_MAP (107 skills) はスキル単層のみで、スキル間の呼び出し順序 (DAG) が非形式的
2. レビュー注入の強度が手動判断に依存し、失敗学習からの自動強化ループが存在しない
3. ルールの「使われなくなる」状態を検出・archive する機構がない

本 PLAN は V5 framework の要素 #16 (`helix_improvement_plan_draft.md Phase 4 統合`) を実装する。

## §2. 背景

### 現状 (V2 時点)

```
[知識層]  skills/SKILL_MAP.md + 107 × SKILL.md
            ↕ 単層。スキル間の順序・組み合わせは人間が毎回判断
[実行制御] HELIX CLI + agent_slots + handover
            ↕ ルール昇格/降格は人間が手動、failure_log は蓄積のみ
[監視]     helix doctor (drift 検出) → PLAN-093 Curator
```

問題: スキルは「何をすべきか」を定義するが、「どの順序で・何が失敗したら・どう強化するか」は宣言的に管理されていない。

### 目指す姿 (V5 + 本 PLAN 後)

```
[層 1] スキル層 (skills/*.md、107 skills)
  ← 既存 SKILL_MAP 維持、derived_from_failures メタデータ追加 (PLAN-100 retrofit 担当)
         ↓ 組み合わせ定義
[層 2] ワークフロー層 (workflows/*.yaml)
  ← スキル呼び出し順序の DAG。ステップ失敗時の retry/skip/escalate 分岐
         ↓ 自動実行・ガードレール適用
[層 3] ハーネス層 (harness/*.yaml)
  ← ワークフロー自動実行 + ゲート発火条件 + レビュー注入強度の宣言
```

エスカレーション機構 (本 PLAN) が 3 層を横断して失敗 → 学習 → 強化のループを閉じる。

## §3. 業界 standard 参照 (Web 検索 3 query)

### Query 1: "abstraction layer architecture skills workflows orchestration framework"

| Source | URL | 本 PLAN との対応 |
|---|---|---|
| **AWS Step Functions — State Machine Abstraction** | https://docs.aws.amazon.com/step-functions/latest/dg/concepts-amazon-states-language.html | ワークフロー層 DAG の Amazon States Language (ASL) 設計を参照。steps / retry / catch 構造の業界整合 |
| **Temporal.io Workflow Abstraction** | https://docs.temporal.io/workflows | DAG ステップ間のデータフロー + retry policy 設計の業界標準。ハーネス層 gate 設計に参照 |
| **Google Cloud Workflows** | https://cloud.google.com/workflows/docs/overview | YAML ベースのワークフロー定義 + 条件分岐 + エラーハンドリング設計パターン |
| **Prefect Flows & Tasks** (Prefect 3.x) | https://docs.prefect.io/3.0/develop/write-flows | スキル = Task、ワークフロー = Flow の抽象化パターン。on_failure hook の設計参照 |

採用根拠: HELIX の workflows/*.yaml は ASL / Prefect Flow に倣い、`steps` 列 + `on_failure` 分岐 + `input/output` スキーマを宣言的 YAML として設計する。クラウドマネージド実行基盤への依存は持たせず、HELIX CLI が interpreter として動作する軽量設計を採用する。

### Query 2: "escalation matrix automated agent human review promotion demotion"

| Source | URL | 本 PLAN との対応 |
|---|---|---|
| **PagerDuty Escalation Policy Design** | https://support.pagerduty.com/main/docs/escalation-policies | agent → council → human の 3 段階エスカレーション設計の業界整合 |
| **AWS Incident Manager Escalation Plans** | https://docs.aws.amazon.com/incident-manager/latest/userguide/escalation.html | 発火回数・時間経過による reviewer_type 自動切替の設計参照 |
| **Martin Fowler: Approval Workflow Pattern** | https://martinfowler.com/bliki/ApprovalWorkflow.html | レビュー注入 (review_inject) の approval gate 設計パターン |
| **Google Site Reliability Engineering: Escalation** | https://sre.google/sre-book/being-oncall/ | N 回以上の再失敗で上位 reviewer への自動昇格を推奨。MTTR 短縮効果の実績 |

採用根拠: エスカレーション 3 段階 (agent → council → human) は PagerDuty / AWS Incident Manager の「発火回数 N 回でエスカレーション tier を上げ、解消後に降格する」lifecycle と整合する。HELIX では failure_log の `escalation_level` フィールドで現在 tier を追跡する。

### Query 3: "rule promotion demotion engine software framework automation"

| Source | URL | 本 PLAN との対応 |
|---|---|---|
| **Martin Fowler: Rules Engine bliki** | https://martinfowler.com/bliki/RulesEngine.html | 発火データ蓄積によるルール優先度自動調整 (adaptive rules engine) の提唱 |
| **AWS Curator Pattern (Well-Architected)** | https://docs.aws.amazon.com/wellarchitected/latest/analytics-lens/data-governance.html | 発火回数・品質スコアに基づく昇格/降格ライフサイクル Curator role |
| **LaunchDarkly Flag Lifecycle** | https://docs.launchdarkly.com/home/flags/flag-archive-delete | 30 日 stale = archive 候補、90 日 = 削除候補の lifecycle 閾値設計 |
| **Netflix Conductor Workflow Lifecycle** | https://conductor.netflix.com/ | ワークフロー定義の lifecycle 管理 (ACTIVE / DEPRECATED / ARCHIVED) + 使用統計ベースの状態遷移 |

採用根拠: demotion_checker.py の閾値設計 (未使用 30 日 → warning、90 日 → archive 候補) は LaunchDarkly / Netflix Conductor の業界標準閾値を採用する。Curator (PLAN-093) の昇格判定は Martin Fowler の adaptive rules engine 原則に準拠する。

## §4. V5 framework 担当要素

本 PLAN は V5 framework 18 要素の **#16 helix_improvement_plan_draft.md 6 Phase 統合** (Phase 4: 抽象化層 3 層エスカレーション) を実装する。

| V5 要素 | 本 PLAN の担当箇所 |
|---|---|
| #5 生成物 trace | workflows/ + harness/ を generates に登録。PLAN-092 DB (plan_generates) で追跡 |
| #6 依存関係 graph | requires: PLAN-091 (matrix) + PLAN-093 (Curator 連動) |
| #7 agent slot 割当 | SE + docs + opus + pmo-sonnet の 4 slot 定義 |
| #16 helix_improvement Phase 4 | 本 PLAN の中核テーマ (3 層構造 + エスカレーション 3 段階 + Curator 連動) |
| #13 V-model TDD 駆動 | §12 テスト設計に unit + integration pair freeze を定義 |

## §5. 抽象化層 3 層構造

### 層 1: スキル層 (既存、SKILL_MAP.md)

```
skills/{category}/{skill-name}/SKILL.md
```

- **現状**: 107 skills。スキルは「何をすべきか」の知識を定義する
- **本 PLAN での拡張**: `derived_from_failures` メタデータフィールドを SKILL.md frontmatter に追加する設計を定義 (実際の retrofit は PLAN-100 担当)
- **デグレ禁止**: 本 PLAN では既存 SKILL_MAP / 107 skills のファイルを一切変更しない

```yaml
# SKILL.md frontmatter 拡張仕様 (PLAN-100 で retrofit 実施)
derived_from_failures:
  - failure_id: F-2026-001
    description: "設計 doc 作成時 Web 検索未実施による根拠薄弱"
    escalation_level: L2
```

### 層 2: ワークフロー層 (新設、workflows/*.yaml)

スキルの呼び出し順序を DAG として宣言的に定義する。

```
workflows/
  l2-design-workflow.yaml          # L2 設計フェーズの標準ワークフロー
  l4-sprint-workflow.yaml          # L4 Sprint 標準 8 ステップ
  reverse-r0-r4-workflow.yaml      # Reverse R0 → R4 → Forward 接続
  g2-gate-workflow.yaml            # G2 凍結ゲート前チェックリスト
  escalation-review-workflow.yaml  # エスカレーション時のレビュー注入フロー
```

**DSL 設計 (YAML)**:

```yaml
# workflows/l4-sprint-workflow.yaml (骨格例)
workflow_id: l4-sprint-standard
version: "1.0"
description: "L4 Sprint 標準 8 ステップ (HELIX_CORE.md §Sprint Plan 標準構造準拠)"
drive: [be, fe, fullstack, agent]

steps:
  - id: step-1-entry
    skill: workflow/project-management
    description: "Entry 条件確認 (前 Sprint 完遂 / dependency)"
    input:
      plan_id: "{{plan_id}}"
      sprint_id: "{{sprint_id}}"
    output:
      entry_ok: bool
    on_failure:
      action: escalate
      escalation_target: PM

  - id: step-2-pre-impl
    skill: workflow/project-management
    description: "着手前 (helix code find / pmo-project-scout)"
    depends_on: [step-1-entry]
    on_failure:
      action: skip
      note: "着手前スキャン失敗は carry note に記録して続行"

  - id: step-3-impl
    skill: common/coding
    description: "実装 (Codex 委譲 or Opus 直接)"
    depends_on: [step-2-pre-impl]
    on_failure:
      action: retry
      max_retries: 2
      on_max_retries: escalate

  - id: step-4-machine-check
    skill: common/testing
    description: "機械チェック mandatory (py_compile / lint)"
    depends_on: [step-3-impl]
    mandatory: true
    on_failure:
      action: escalate
      escalation_target: TL

  - id: step-5-test
    skill: common/testing
    description: "テスト起動 mandatory (unit / integration / 全回帰)"
    depends_on: [step-4-machine-check]
    mandatory: true
    on_failure:
      action: escalate
      escalation_target: TL

  - id: step-6-review
    skill: common/code-review
    description: "レビュー mandatory (セルフ / pmo-sonnet)"
    depends_on: [step-5-test]
    mandatory: true
    on_failure:
      action: escalate
      escalation_target: PM

  - id: step-7-commit
    skill: workflow/git
    description: "commit + carry note"
    depends_on: [step-6-review]
    on_failure:
      action: escalate
      escalation_target: PM

  - id: step-8-exit
    skill: workflow/project-management
    description: "Exit 条件確認 (DoD)"
    depends_on: [step-7-commit]
    on_failure:
      action: escalate
      escalation_target: PM

dag:
  type: linear
  mandatory_steps: [step-4-machine-check, step-5-test, step-6-review]
```

### 層 3: ハーネス層 (新設、harness/*.yaml)

ワークフローの自動実行条件と、ゲート発火・レビュー注入強度を宣言的に定義する。

```
harness/
  default-harness.yaml         # 全ワークフローに適用するデフォルトガードレール
  g2-gate-harness.yaml         # G2 凍結ゲート専用ハーネス
  g4-gate-harness.yaml         # G4 実装凍結ゲート専用ハーネス
  escalation-harness.yaml      # エスカレーション検出時の強化ガードレール
```

**DSL 設計 (YAML)**:

```yaml
# harness/g4-gate-harness.yaml (骨格例)
harness_id: g4-gate-harness
version: "1.0"
description: "G4 実装凍結ゲート — テスト・レビュー網羅チェック + エスカレーション判定"
workflow: l4-sprint-standard

gates:
  - id: gate-test-coverage
    condition: "step-5-test.result == 'pass' AND coverage >= 80"
    action: continue
    on_fail: reject

  - id: gate-review-mandatory
    condition: "step-6-review.result == 'pass'"
    action: continue
    on_fail: review_inject
    reviewer_type: pmo-sonnet

  - id: gate-escalation-check
    condition: "escalation_engine.current_level(plan_id) >= L2"
    action: review_inject
    reviewer_type: council
    note: "エスカレーションレベル L2 以上は council レビュー注入"

escalation_override:
  enabled: true
  check_interval_minutes: 5

reviewer_type_matrix:
  L0: agent      # pmo-sonnet
  L1: agent      # pmo-sonnet + tl-advisor
  L2: council    # PM + TL + pmo-sonnet の 3 者
  L3: human      # PO (yoshiyuki0907yn@gmail.com) 直接確認必須
```

## §6. ワークフロー層 DSL 詳細仕様

### 6.1 ステップ定義

| フィールド | 型 | 説明 |
|---|---|---|
| `id` | str | ステップ ID (DAG ノード識別子) |
| `skill` | str | `{category}/{skill-name}` (SKILL_MAP のパス形式) |
| `description` | str | ステップの目的 |
| `depends_on` | list[str] | 上流ステップ ID (空 = DAG の起点) |
| `mandatory` | bool | true = Sprint Exit 前に必須 |
| `input` | dict | 入力パラメータ (Jinja2 template 変数使用可) |
| `output` | dict | 出力スキーマ定義 |
| `on_failure.action` | enum | `retry` / `skip` / `escalate` |
| `on_failure.max_retries` | int | retry 上限 (action=retry の場合) |
| `on_failure.escalation_target` | str | `PM` / `TL` / `Pmo` |

### 6.2 DAG 依存関係ルール

- `depends_on` が空のステップ = DAG 起点 (並列実行可)
- `depends_on` に複数指定 = 全先行ステップ完了後に起動
- 循環依存は `helix plan validate` で fail-close 検出 (PLAN-091 連動)
- `type: linear` = 直列実行のみ (並列起点なし)
- `type: parallel` = 依存なしステップは並列実行

### 6.3 失敗時アクション

| アクション | 動作 |
|---|---|
| `retry` | `max_retries` 回まで再実行。上限到達で `on_max_retries` アクションへ |
| `skip` | carry note を記録してステップをスキップし次ステップへ |
| `escalate` | `escalation_engine.trigger()` を呼び出し、reviewer_type を上げる |

### 6.4 JSON Schema バージョニング

ステップ間のデータは JSON Schema でバージョン管理する:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12",
  "workflow_schema_version": "1.0",
  "step_output": {
    "type": "object",
    "required": ["result", "timestamp"],
    "properties": {
      "result": {"enum": ["pass", "fail", "skip", "escalate"]},
      "timestamp": {"type": "string", "format": "date-time"},
      "note": {"type": "string"}
    }
  }
}
```

## §7. ハーネス層 DSL 詳細仕様

### 7.1 ゲート定義

| フィールド | 型 | 説明 |
|---|---|---|
| `id` | str | ゲート ID |
| `condition` | str | Python 式 (True = 通過) |
| `action` | enum | `continue` / `reject` / `review_inject` |
| `reviewer_type` | enum | `agent` / `council` / `human` |
| `on_fail` | enum | condition 偽の場合のアクション |

### 7.2 レビュー注入 (review_inject) 詳細

```
reviewer_type = agent   → pmo-sonnet review を自動発火
reviewer_type = council → PM + TL + pmo-sonnet の 3 者レビュー (helix council コマンド)
reviewer_type = human   → PO (yoshiyuki0907yn@gmail.com) への直接通知 + 作業一時停止
```

### 7.3 ゲート発火条件の対応

| HELIX ゲート | ハーネス ID | 主な condition |
|---|---|---|
| G2 設計凍結 | g2-gate-harness | 4 artifact 揃い + ADR snapshot 存在 |
| G3 実装着手 | g3-gate-harness | API/Schema Freeze + テスト設計 pair freeze |
| G4 実装凍結 | g4-gate-harness | テスト coverage >= 80 + レビュー通過 |

## §8. エスカレーション機構 3 段階

### 8.1 エスカレーションレベル定義

| レベル | 名称 | 発火条件 | reviewer_type |
|---|---|---|---|
| L0 | Normal | 初期状態 / 正常動作中 | agent (pmo-sonnet) |
| L1 | Elevated | 同種失敗 N >= 3 回 OR 再失敗 M >= 1 回 | agent (pmo-sonnet + tl-advisor) |
| L2 | Council | 同種失敗 N >= 7 回 OR 再失敗 M >= 3 回 | council (PM + TL + pmo-sonnet) |
| L3 | Human | 同種失敗 N >= 15 回 OR 再失敗 M >= 7 回 | human (PO 直接) |

**デフォルト閾値** (LaunchDarkly / PagerDuty 業界標準参照):
- N (同種失敗回数): 3 / 7 / 15
- M (再失敗回数): 1 / 3 / 7
- 未使用期間 stale 警告: 30 日
- 未使用期間 archive 候補: 90 日

### 8.2 昇格判定フロー

```
failure_log に INSERT
  ↓
escalation_engine.evaluate(plan_id, failure_type)
  ↓
  同種失敗カウント >= 閾値N ?
    Yes → current_level を +1 (L0→L1→L2→L3)
    No  → 同種再失敗カウント >= 閾値M ?
            Yes → current_level を +1
            No  → current_level 維持
  ↓
harness が current_level を参照して reviewer_type を切替
  ↓
review_inject 発火 (Curator 連動: PLAN-093 escalation_matrix.py 呼び出し)
```

### 8.3 降格判定フロー (demotion_checker.py)

```
定期実行 (helix doctor check_escalation_stale)
  ↓
plan_id × failure_type ごとに確認:
  未使用期間 >= 30 日 → warning (carry note 記録)
  未使用期間 >= 90 日 → archive 候補 (human 確認後に非アクティブ化)
  違反検出ゼロ期間 >= 90 日 → current_level を -1 (降格)
    L3→L2→L1→L0 と段階的に降格
    L0 で 90 日継続ゼロ → archive 候補
  ↓
helix.db failure_log に demotion イベントを INSERT
```

### 8.4 PLAN-093 Curator との連動

```
escalation_engine.py → Curator escalation_matrix.py を呼び出し
demotion_checker.py  → Curator refactor_degrade_pattern を参照
```

Curator (PLAN-093) が管理する:
- `escalation_matrix` テーブル: plan_id × failure_type × current_level × threshold_n × threshold_m
- `refactor_degrade_pattern` テーブル: pattern_id / trigger / escalation_level

本 PLAN の `escalation_engine.py` は Curator のデータを読み取り専用 (read-only) で参照し、書き込みは Curator 側が担当する責務分離を維持する。

## §9. cli/lib/escalation_engine.py 設計

### 9.1 公開 API

```python
# @helix:index id=escalation-engine domain=cli/lib summary=エスカレーションレベル評価・昇格判定エンジン

class EscalationEngine:
    """
    failure_log と escalation_matrix を参照し、plan_id × failure_type の
    現在エスカレーションレベルを評価・更新する。
    """

    def __init__(self, db_path: str, config: EscalationConfig):
        ...

    def evaluate(self, plan_id: str, failure_type: str) -> EscalationLevel:
        """
        failure_log の最新カウントを集計し、閾値比較でレベルを返す。
        昇格が発生した場合は escalation_matrix を更新する (Curator 委譲)。
        Returns: EscalationLevel (L0 / L1 / L2 / L3)
        """
        ...

    def current_level(self, plan_id: str) -> EscalationLevel:
        """現在の escalation level を返す (harness から呼び出し)。"""
        ...

    def trigger(self, plan_id: str, failure_type: str, context: str) -> ReviewAction:
        """
        失敗発生時に呼び出す。evaluate() 後に review_inject 指示を返す。
        Returns: ReviewAction (reviewer_type + inject_target)
        """
        ...

    def reset(self, plan_id: str, failure_type: str, reason: str) -> None:
        """解消後のリセット (human 承認後に L0 へ戻す)。"""
        ...
```

### 9.2 EscalationConfig

```python
@dataclass
class EscalationConfig:
    threshold_n: list[int] = field(default_factory=lambda: [3, 7, 15])
    threshold_m: list[int] = field(default_factory=lambda: [1, 3, 7])
    reviewer_types: list[str] = field(
        default_factory=lambda: ["agent", "agent+tl", "council", "human"]
    )
```

### 9.3 エラーハンドリング

- DB 接続失敗時: fail-open (L0 を返す、log に記録)
- escalation_matrix 未初期化: 自動初期化 (plan_id × failure_type を L0 で INSERT)
- Curator (PLAN-093) 未起動: 警告のみ、自己完結モードで動作

## §10. cli/lib/demotion_checker.py 設計

### 10.1 公開 API

```python
# @helix:index id=demotion-checker domain=cli/lib summary=未使用・違反ゼロ継続によるエスカレーション降格チェッカー

class DemotionChecker:
    """
    定期実行で未使用期間・違反検出ゼロ期間を確認し、降格・archive 候補を返す。
    """

    def __init__(self, db_path: str, config: DemotionConfig):
        ...

    def check_stale(self, plan_id: str | None = None) -> list[StaleResult]:
        """
        未使用 30 日 → warning / 90 日 → archive_candidate を返す。
        plan_id 省略時は全 plan_id を検査。
        """
        ...

    def check_zero_violation(self, plan_id: str | None = None) -> list[DemotionResult]:
        """
        違反検出ゼロ 90 日継続を検出し、current_level -1 の降格推奨を返す。
        """
        ...

    def demote(self, plan_id: str, failure_type: str, reason: str) -> None:
        """
        降格を実行する (human 確認後に呼び出す。自動実行禁止)。
        """
        ...
```

### 10.2 DemotionConfig

```python
@dataclass
class DemotionConfig:
    stale_warning_days: int = 30    # LaunchDarkly 30 日基準
    archive_candidate_days: int = 90  # LaunchDarkly 90 日基準
    zero_violation_demotion_days: int = 90
```

### 10.3 自動実行禁止ルール

降格 (`demote()`) は **human 確認後にのみ呼び出す**。`check_stale()` / `check_zero_violation()` は候補を返すだけで実行しない。これは PO 承認なし task pop の禁止 (TL v5 round 5 P0 指摘) と同じ原則。

## §11. 段階導入計画 (P1 → P2 → P3)

### Phase 1: 骨格 doc + DSL 仕様確定 (本 PLAN 起票 = Phase 1 完了)

- [x] PLAN-097 起票 (本 doc)
- [x] ADR-030 起票 (大局判断 snapshot)
- [ ] workflows/ ディレクトリ作成 + l4-sprint-workflow.yaml 骨格 YAML
- [ ] harness/ ディレクトリ作成 + g4-gate-harness.yaml 骨格 YAML
- [ ] DSL JSON Schema ドラフト (step_output.schema.json)

### Phase 2: escalation_engine.py + demotion_checker.py 実装

前提: PLAN-093 (Curator / escalation_matrix テーブル) が draft 以上であること

- [ ] cli/lib/escalation_engine.py 実装 (Codex SE 委譲)
- [ ] cli/lib/demotion_checker.py 実装 (Codex SE 委譲)
- [ ] cli/lib/tests/test_escalation_engine.py 実装 (§12 テスト設計準拠)
- [ ] helix doctor check_escalation_stale 追加 (PLAN-093 連動)
- [ ] pytest 全回帰 PASS 確認

### Phase 3: Curator 自動化連動 + harness interpreter

前提: PLAN-092 (helix.db v35) + PLAN-093 (Curator 本実装) 完了後

- [ ] harness/*.yaml interpreter 実装 (`helix harness run --workflow <id>`)
- [ ] escalation_engine ↔ Curator escalation_matrix 双方向連携
- [ ] workflows/*.yaml の `helix workflow validate` CLI 実装 (DAG cycle 検出)
- [ ] E2E テスト: workflow 実行 → 失敗 → escalation → review_inject

## §12. テスト戦略 (V-model TDD)

### テスト設計 (③ artifact) — 本 §で定義

本 §は V-model artifact ③ (テスト設計) の位置付け。実装コード (artifact ②) と対応関係:

| テスト設計 (③) | 実装コード (②) | 双方向 trace |
|---|---|---|
| 本 §12 §12.1 unit 設計 | cli/lib/escalation_engine.py | 本 §→実装: §9 API 設計参照 |
| 本 §12 §12.2 unit 設計 | cli/lib/demotion_checker.py | 本 §→実装: §10 API 設計参照 |
| 本 §12 §12.3 integration 設計 | workflows/ + harness/ + engine | 本 §→実装: §6/§7 DSL 参照 |

テストコード (④ artifact) は `cli/lib/tests/test_escalation_engine.py` / `test_demotion_checker.py` に分離実装する (テスト設計と同一ファイルに統合しない)。

### 12.1 escalation_engine.py unit test 設計

| Test ID | 内容 | 期待結果 |
|---|---|---|
| U-097-001 | 初期状態で evaluate() を呼ぶ | L0 を返す |
| U-097-002 | 同種失敗 3 回で evaluate() | L1 に昇格 |
| U-097-003 | 同種失敗 7 回で evaluate() | L2 に昇格 |
| U-097-004 | 同種失敗 15 回で evaluate() | L3 に昇格 (human) |
| U-097-005 | 再失敗 1 回で evaluate() | L1 に昇格 |
| U-097-006 | trigger() 呼び出し — L0 状態 | ReviewAction(reviewer_type="agent") |
| U-097-007 | trigger() 呼び出し — L2 状態 | ReviewAction(reviewer_type="council") |
| U-097-008 | reset() 後の current_level() | L0 を返す |
| U-097-009 | DB 接続失敗時の evaluate() | fail-open (L0 返却、例外非送出) |
| U-097-010 | escalation_matrix 未初期化時 | 自動 L0 INSERT + L0 返却 |

### 12.2 demotion_checker.py unit test 設計

| Test ID | 内容 | 期待結果 |
|---|---|---|
| U-097-011 | 未使用 15 日 → check_stale() | 結果なし (threshold 未満) |
| U-097-012 | 未使用 31 日 → check_stale() | StaleResult(level="warning") |
| U-097-013 | 未使用 91 日 → check_stale() | StaleResult(level="archive_candidate") |
| U-097-014 | 違反ゼロ 89 日 → check_zero_violation() | 結果なし |
| U-097-015 | 違反ゼロ 91 日 → check_zero_violation() | DemotionResult(current_level - 1) |
| U-097-016 | demote() は human 確認後のみ呼出 | 直接呼び出し可 (guard は caller 側) |

### 12.3 integration test 設計 (Phase 3 実施)

| Test ID | 内容 | 期待結果 |
|---|---|---|
| I-097-001 | workflow DAG (l4-sprint) 実行 → step-4 失敗 → escalate | EscalationEngine.trigger() 呼び出し確認 |
| I-097-002 | harness gate (g4-gate) — coverage 70% → review_inject | reviewer_type="pmo-sonnet" で注入 |
| I-097-003 | 同種失敗 3 回 → harness が council 切替 | reviewer_type="council" に変更 |
| I-097-004 | 90 日未使用 → demotion_checker が archive_candidate 返却 | StaleResult.level="archive_candidate" |

### 12.4 fake fixture 方針

- `fake_failure_log` fixture: SQLite in-memory + 動的タイムスタンプ (`datetime.now(timezone.utc) - timedelta(days=N)`)
- `fake_escalation_matrix` fixture: 初期 L0 エントリのみ
- 固定 timestamp 禁止 (境界条件 flake 防止、[[feedback_pytest_fixture_time_dependent_flake]] 参照)

## §13. DoD (完了条件)

### Phase 1 DoD

- [ ] PLAN-097 起票完了 (本 doc)
- [ ] ADR-030 起票完了 (同時)
- [ ] workflows/l4-sprint-workflow.yaml 骨格 YAML (ステップ定義のみ、interpreter 不要)
- [ ] harness/g4-gate-harness.yaml 骨格 YAML (ゲート定義のみ)
- [ ] DSL JSON Schema draft (step_output.schema.json v1.0)

### Phase 2 DoD

- [ ] escalation_engine.py 公開 API §9.1 全実装
- [ ] demotion_checker.py 公開 API §10.1 全実装
- [ ] test_escalation_engine.py: U-097-001〜010 全 PASS
- [ ] test_demotion_checker.py: U-097-011〜016 全 PASS
- [ ] `helix doctor check_escalation_stale` 追加 (advisory mode)
- [ ] pytest 全回帰 PASS (`python3 -m pytest cli/lib/tests/ -q --tb=short`)

### Phase 3 DoD

- [ ] `helix harness run --workflow <id>` CLI 実装
- [ ] `helix workflow validate` CLI 実装 (DAG cycle 検出)
- [ ] Curator ↔ escalation_engine 双方向連携動作確認
- [ ] I-097-001〜004 全 PASS
- [ ] E2E: workflow 実行 → 失敗 → escalation → review_inject の一気通貫動作確認

## §14. V-model 4 artifact 双方向 trace

```
① 設計 (本 PLAN §5/§6/§7/§8/§9/§10)  ←対応→  ③ テスト設計 (別 file 計画: docs/v2/L4-test-design/PLAN-097-unit-test-design.md、別 session 起票)
       ↓ 実装                                           ↓ 実装
② 実装コード                           ←対応→  ④ テストコード
   escalation_engine.py                             test_escalation_engine.py
   demotion_checker.py                              test_demotion_checker.py
   workflows/*.yaml                                 I-097-001〜004
   harness/*.yaml
```

| Artifact | ファイル | 双方向 trace |
|---|---|---|
| ① 設計 | 本 PLAN §5-§10 | → ②: §9/§10 API が実装コードと 1:1 対応 / → ③: docs/v2/L4-test-design/PLAN-097-unit-test-design.md (別 session 起票)。本 PLAN §12 はテスト戦略概要のみ |
| ② 実装コード | escalation_engine.py / demotion_checker.py | → ①: docstring に「DoD: PLAN-097 §9 / §10」を明記 |
| ③ テスト設計 | docs/v2/L4-test-design/PLAN-097-unit-test-design.md (別 session 起票予定) | → ①: 対象設計「PLAN-097 §9 / §10」明示 / → ④: test file 名を別 file §X に明示。本 PLAN §12 はテスト戦略概要のみ |
| ④ テストコード | test_escalation_engine.py / test_demotion_checker.py | → ③: docstring に「DoD 検証: PLAN-097 §12 U-097-XXX」明示 |

## §15. 関連 PLAN / ADR

| 関連 | 接続方向 | 内容 |
|---|---|---|
| PLAN-MM-001 | parent | V5 全体構想 (本 PLAN の親設計) |
| PLAN-091 | requires | V5 framework 本体 (matrix + 種別 + template embed) — 本 PLAN の frontmatter 規約基盤 |
| PLAN-093 | requires | drift 検出 + Curator — escalation_engine が Curator を read-only 参照 |
| PLAN-100 | side-by-side | 既存 SKILL_MAP retrofit — derived_from_failures メタデータ追加担当 |
| ADR-027 | related | drift 検出 + Curator 採用判断 — escalation_matrix テーブル設計の根拠 |
| ADR-030 | self | 本 PLAN の L2 大局判断 snapshot |
| helix_improvement Phase 4 | source | 本 PLAN の素材 (3 層構造 + 昇格/降格基準の初期設計) |
