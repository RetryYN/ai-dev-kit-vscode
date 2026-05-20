---
plan_id: PLAN-093
title: "drift 検出 + 進捗 trace dashboard + Curator 自動化"
kind: impl
layer: cross
drive: be
status: proposed
created: 2026-05-20
author: pmo-sonnet
agent_slots:
  - role: pm-advisor
    slot_label: "PM 級難判断 — 大局判断・最終 finalize・P0 承認境界管理"
  - role: pmo-sonnet
    slot_label: "PMO — 起票・整合確認・ドキュメントチェック"
  - role: se
    slot_label: "SE — plan_drift_checker.py / curator_engine.py / escalation_matrix.py 実装"
  - role: docs
    slot_label: "Docs — helix doctor 拡張 check 実装 / helix-dashboard plan-progress 拡張"
  - role: qa
    slot_label: "QA — テスト設計補完・drift 検出回帰テスト・Curator 境界テスト追加"
generates:
  - artifact_path: cli/helix-dashboard
    artifact_type: cli_extension
  - artifact_path: cli/lib/plan_drift_checker.py
    artifact_type: python_module
  - artifact_path: cli/lib/curator/__init__.py
    artifact_type: python_module
  - artifact_path: cli/lib/curator/curator_engine.py
    artifact_type: python_module
  - artifact_path: cli/lib/curator/escalation_matrix.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_plan_drift_checker.py
    artifact_type: test
  - artifact_path: cli/lib/tests/test_curator_engine.py
    artifact_type: test
  - artifact_path: docs/adr/ADR-027-plan-drift-detection-curator-decision.md
    artifact_type: adr_snapshot
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-091
    - PLAN-092
    - PLAN-MM-001
  blocks:
    - PLAN-095
    - PLAN-097
    - PLAN-098
related_adr:
  - ADR-027
test_design: docs/v2/L4-test-design/PLAN-093-test-design.md
---

# PLAN-093: drift 検出 + 進捗 trace dashboard + Curator 自動化

## §1. 目的

PLAN-092 が構築する `helix.db v35` の `plan_registry` / `sprint_progress` / `failure_log` / `plan_generates` を読み取り、以下 3 機能を実現する。

1. **Drift 検出**: PLAN frontmatter `generates:` に記載された成果物が実ファイルとして存在するか自動確認し、不在 / stale / orphan を `helix doctor` でレポートする。
2. **進捗 trace dashboard**: `sprint_progress` テーブルを読み取り、PLAN / Layer / Sprint 単位の進捗を `helix dashboard plan-progress` で可視化する。
3. **Curator 自動化**: `failure_log` / `refactor_degrade_pattern` を分析し、ルールの昇格（escalation）と降格（demotion）を自動判定する。

V5 framework 18 要素のうち **#9 drift 検出** / **#10 進捗 trace** / **#16 helix_improvement Phase 6 統合** を担当する。

---

## §2. 背景

### 2.1 問題状況

HELIX V2 構築が進むにつれ、PLAN doc と実実装の間に以下の乖離が発生する:

- PLAN `generates:` に `cli/lib/foo.py` を宣言したが、実際には別パスに配置
- Sprint が `completed` だが対応テストファイルが存在しない
- recovery kind PLAN が 7 日以上更新されず stale 化
- active PLAN が 30 日更新なしで放置

これらの drift は手動 audit では検出困難であり、機械的な自動検出が必要。

### 2.2 Curator 不在の問題

`helix_improvement_plan_draft.md` Phase 4 で設計したレビュー注入機構 (agent / council / human 切替) と Phase 6 の Curator 機構が実装されておらず、failure_log に蓄積したデータが活用されていない。

- 同種失敗が複数回再発しても自動昇格しない
- 違反検出ゼロが続いても自動降格しない
- handover メモが肥大化し、sprint_progress DB から引けば不要な情報を毎回手書きしている

---

## §3. 業界 standard 参照

### Query 1: "drift detection software architecture documentation"

- **Architectural Drift: The Hidden Nemesis of Long-lived Software** — InfoQ 2024
  - https://www.infoq.com/articles/architectural-drift/
  - 「設計意図と実装の乖離を定期的に機械検出し、drift が蓄積する前に是正するのがアーキテクチャ寿命を延ばす最重要施策」と結論。HELIX の `check_plan_drift` はこの原則を PLAN generates ↔ 実ファイル突合として具体化する。
- **ArchUnit — Architecture as Code** (TNG Technology Consulting)
  - https://www.archunit.org/
  - Java エコシステムで広く使われる「コードとして記述したアーキテクチャルールを自動テスト」する OSS。HELIX の helix doctor check は同思想を Python / SQLite 上で再実装する。
- **Continuous Architecture Compliance (CAC)** — ThoughtWorks Technology Radar
  - https://www.thoughtworks.com/radar/techniques/continuous-architecture-compliance
  - 「アーキテクチャ準拠をビルドパイプラインに組み込む」を Adopt レベルで推奨。HELIX は CI gate として helix doctor を G2/G4 ゲートに接続する形で同技術採用。

### Query 2: "automated rule promotion demotion curator engine design pattern"

- **Curator Pattern in Data Governance** — AWS Well-Architected Framework Data Analytics
  - https://docs.aws.amazon.com/wellarchitected/latest/analytics-lens/data-governance.html
  - 「データカタログのエントリを発火回数・品質スコアに基づき自動的に昇格（Certified / Promoted）または降格（Deprecated / Archived）する Curator role」を規定。HELIX Curator はこの pattern をルールライフサイクル管理に適用する。
- **Feature Flag Lifecycle (LaunchDarkly)** — LaunchDarkly Best Practices 2024
  - https://docs.launchdarkly.com/home/flags/flag-archive-delete
  - 「フラグは 30 日 stale で archive 候補、90 日で自動削除候補」という lifecycle 管理。HELIX Curator の降格閾値設計の根拠。
- **Adaptive Rules Engine (Martin Fowler bliki)**
  - https://martinfowler.com/bliki/RulesEngine.html
  - 「ルールエンジンは発火データを蓄積してルールの優先度・有効期間を自動調整する仕組みを持つべき」と示唆。HELIX escalation_matrix はこの adaptive principle を採用する。

### Query 3: "Linear Jira project progress dashboard developer tools"

- **Linear Progress Tracking** — Linear Docs
  - https://linear.app/docs/project-progress
  - 「プロジェクト内の Issues を Milestone × Status で進捗バーとして可視化し、blocked 状態を赤ハイライトする」。HELIX `helix dashboard plan-progress` の Layer A/B/C 別進捗バーはこれに倣う。
- **Jira Work Item Hierarchy** — Atlassian Documentation
  - https://support.atlassian.com/jira-software-cloud/docs/what-is-an-epic/
  - Epic → Story → Task の階層と progress % 表示。HELIX の PLAN → Sprint → Step 階層と対応させる設計根拠。
- **GitHub Projects Roadmap View** — GitHub Documentation
  - https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/changing-the-layout-of-a-view
  - 「Roadmap ビューで Date field + Status field をクロス集計し、PLAN 単位の進捗を時系列バーで表示」。HELIX dashboard の blocked PLAN 列挙機能の根拠。

---

## §4. V5 framework 担当要素

| V5 要素 | 内容 | PLAN-093 の対応 |
|---------|------|-----------------|
| **#9 PLAN ↔ 設計 doc drift 検出** | helix doctor で drift を機械検出 | `plan_drift_checker.py` + helix doctor 4 check 追加 |
| **#10 進捗 trace** | sprint_progress + handover メモ短縮化 | `helix dashboard plan-progress` subcommand |
| **#16 helix_improvement Phase 6 統合** | Curator 自動化 (昇格/降格/レビュー注入) | `curator_engine.py` + `escalation_matrix.py` |

---

## §5. helix doctor 拡張仕様

### 5.1 前提: PLAN-092 helix.db v35 schema (read-only 参照)

PLAN-093 は以下のテーブルを **読み取り専用** で参照する (スキーマ変更禁止):

| テーブル | 参照列 | 用途 |
|---------|--------|------|
| `plan_registry` | plan_id / status / kind / updated_at | freshness チェック |
| `plan_generates` | plan_id / artifact_path / artifact_type | drift チェック |
| `sprint_progress` | plan_id / sprint_id / status / timestamp | 進捗 dashboard |
| `failure_log` | plan_id / failure_type / count / last_seen | Curator 昇格判定 |
| `refactor_degrade_pattern` | pattern_id / escalation_level / last_fired | Curator 降格判定 |

### 5.2 check_plan_drift

```
目的: PLAN frontmatter generates: に記載された artifact_path が実ファイルとして存在するか確認
入力: plan_generates テーブル全行
判定:
  - artifact_path が存在しない → WARNING: drift 検出 (advisory mode)
  - artifact_path は存在するが plan status = completed → OK
  - artifact_path は存在するが plan status = active かつ最終更新 > 30 日 → WARNING: stale generates
出力: {plan_id, artifact_path, status: ok|warning|error}[]
fail-close: P2 以降 (Phase 2 で fail-close 昇格、P1 は advisory)
```

### 5.3 check_plan_freshness

```
目的: status=active の PLAN が N 日以上更新されていないか検出
パラメータ: --freshness-days N (default: 30)
入力: plan_registry WHERE status='active'
判定:
  - NOW - updated_at > N 日 → WARNING: stale active PLAN
出力: {plan_id, last_updated, days_stale}[]
fail-close: なし (advisory のみ、helix doctor summary に件数表示)
```

### 5.4 check_recovery_plan_freshness

```
目的: kind=recovery の PLAN が 7 日以上更新されていないか検出
パラメータ: --recovery-days N (default: 7)
入力: plan_registry WHERE kind='recovery'
判定:
  - NOW - updated_at > N 日 → WARNING: stale recovery PLAN
出力: {plan_id, last_updated, days_stale}[]
fail-close: なし (advisory のみ)
根拠: session 終了前チェックリスト §4 "リカバリープラン起票済" の機械的補完
```

### 5.5 check_plan_dependency_cycle

```
目的: plan_dependencies テーブルの requires/blocks 関係に cycle が存在しないか確認
入力: plan_dependencies 全行
アルゴリズム: DFS + 訪問済みノードセット (標準 cycle 検出)
出力: 検出 cycle の PLAN ID chain
fail-close: P1 以降 (cycle は即時 ERROR、PLAN 起票を block)
```

---

## §6. cli/helix-dashboard plan-progress 拡張仕様

### 6.1 サブコマンド追加

既存の `helix dashboard` に `plan-progress` サブコマンドを追加する (既存 subcommand には触れない)。

```bash
helix dashboard plan-progress [--layer A|B|C|all] [--status active|blocked|all] [--json]
```

### 6.2 表示形式 (text mode)

```
PLAN Progress Dashboard (Layer A/B/C)
=====================================

Layer A: 工程・doc 運用ルール整備
  PLAN-091 [framework-core    ] ████████░░ 80%  (Sprint 4/5)
  PLAN-100 [retrofit          ] ░░░░░░░░░░  0%  (not started)
  PLAN-095 [poc-matrix        ] ░░░░░░░░░░  0%  [BLOCKED by PLAN-091]
  PLAN-097 [abstraction-layer ] ░░░░░░░░░░  0%  [BLOCKED by PLAN-093]
  PLAN-098 [recovery-kind     ] ░░░░░░░░░░  0%  [BLOCKED by PLAN-093]

Layer B: helix.db 型ハーネス
  PLAN-092 [auto-register     ] ██░░░░░░░░ 20%  (Sprint 1/5)
  PLAN-093 [drift-curator     ] ██░░░░░░░░ 20%  (Sprint 1/5)

Layer C: 連携自動化ハーネス
  PLAN-099 [auto-run-5layer   ] ░░░░░░░░░░  0%  (not started)

Blocked PLANs: PLAN-095, PLAN-097, PLAN-098
Active PLANs:  PLAN-091, PLAN-092, PLAN-093
```

### 6.3 進捗算出ロジック

```python
progress_pct = (completed_sprints / total_sprints) * 100
# sprint_progress テーブルの status='completed' を completed_sprints に計上
# total_sprints は plan_registry の frontmatter から sprint_count を読む
```

### 6.4 BLOCKED 判定

```python
# plan_dependencies.requires に含まれる PLAN の status が 'completed' でない場合
# 当該 PLAN を BLOCKED 表示する
```

---

## §7. Curator 機構仕様

### 7.1 概要

`helix_improvement_plan_draft.md` Phase 4 (昇格判定エンジン) + Phase 6 (Curator) を HELIX に実装する。Curator は failure_log を定期分析し、ルールの昇格/降格を自動判定する。

### 7.2 curator_engine.py

```python
# cli/lib/curator/curator_engine.py

class CuratorEngine:
    """
    failure_log + refactor_degrade_pattern を分析し、
    ルール昇格/降格候補を escalation_matrix に渡す
    """

    ESCALATION_THRESHOLD = 3       # 同種失敗 N 回で昇格候補
    DEMOTION_STALE_DAYS  = 30      # N 日未発火で降格候補
    ARCHIVE_STALE_DAYS   = 90      # N 日未発火で archive 候補

    def analyze_failures(self, db_path: str) -> list[dict]:
        """
        failure_log を読み取り、failure_type ごとの発火回数を集計
        → escalation_threshold 超過で promotion_candidate=True
        """

    def analyze_demotion(self, db_path: str) -> list[dict]:
        """
        refactor_degrade_pattern を読み取り、last_fired が
        DEMOTION_STALE_DAYS 超過したパターンを降格候補として返す
        """

    def run_cycle(self, db_path: str) -> dict:
        """
        analyze_failures + analyze_demotion を実行し、
        昇格/降格候補を escalation_matrix に渡して
        レビュー注入 (agent / council / human) を決定する
        """
```

### 7.3 escalation_matrix.py

```python
# cli/lib/curator/escalation_matrix.py

class EscalationMatrix:
    """
    昇格/降格候補に対してレビュー種別を決定する matrix
    helix_improvement Phase 4 の "レビュアー種別切替" を実装
    """

    REVIEW_LEVELS = {
        "agent":   {"threshold": 1, "reviewer": "pmo-sonnet"},   # 軽微
        "council": {"threshold": 3, "reviewer": "tl-advisor"},   # 中程度
        "human":   {"threshold": 5, "reviewer": "human"},        # 重大
    }

    def decide_review_level(self, failure_count: int, severity: str) -> str:
        """
        failure_count と severity から適切な review_level を返す
        """

    def inject_review(self, candidate: dict) -> dict:
        """
        decide_review_level の結果を candidate に注入し、
        helix doctor summary / handover memo に表示する情報を返す
        """
```

### 7.4 Curator 発火タイミング

| タイミング | トリガー | 処理 |
|-----------|---------|------|
| G4 ゲート通過時 | `helix gate g4` | `curator run --check promotion` |
| `helix doctor` 実行時 | CLI 呼び出し | `curator run --check demotion` |
| 週次 scheduled (Layer C) | PLAN-099 heartbeat | `curator run --full` |
| 手動 | `helix curator run` | フル実行 |

### 7.5 レビュー注入 3 段階 (PLAN-097 連動)

Curator が昇格候補を検出した場合、PLAN-097 の抽象化層エスカレーション機構と連動する:

1. **agent** (failure_count = 1-2): pmo-sonnet が自動レビュー、合格で promote
2. **council** (failure_count = 3-4): tl-advisor を召喚し adversarial check
3. **human** (failure_count >= 5): Opus (PM) に escalate し人間承認を必須化

---

## §8. 段階導入計画

### Phase 1: helix doctor advisory 追加 (Sprint .1)

- `plan_drift_checker.py` 実装
- helix doctor に 4 check を advisory mode で追加
- 既存 helix doctor の動作に影響ゼロ (新 check は独立 function)
- DoD: `python3 -m py_compile cli/lib/plan_drift_checker.py` PASS
- DoD: `pytest cli/lib/tests/test_plan_drift_checker.py -q` PASS (fake fixture)

### Phase 2: dashboard plan-progress (Sprint .2)

- `cli/helix-dashboard` に `plan-progress` subcommand 追加
- `sprint_progress` テーブルを PLAN-092 DB が存在しない環境では graceful fallback (空表示)
- DoD: `cli/helix-dashboard plan-progress --json` が valid JSON を返す
- DoD: `bash -n cli/helix-dashboard` PASS

### Phase 3: Curator 自動化 (Sprint .3-.4)

- `cli/lib/curator/__init__.py` / `curator_engine.py` / `escalation_matrix.py` 実装
- `helix curator run` コマンド追加
- DoD: `pytest cli/lib/tests/test_curator_engine.py -q` PASS (昇格/降格境界テスト)
- DoD: PLAN-097 とのインターフェース仕様 (escalation 結果の受け渡し型) を `docs/adr/ADR-027.md` に明記

### Phase 4: fail-close 昇格 (Sprint .5、PLAN-097 接続後)

- Phase 1 の advisory check を fail-close に昇格 (check_plan_dependency_cycle のみ即時 fail-close)
- PLAN-097 のレビュー注入機構と Curator を接続
- DoD: `helix doctor` で cycle 検出時に exit 2 を返す
- DoD: PLAN-097 統合テスト PASS

---

## §9. テスト戦略

### 9.1 Unit test: test_plan_drift_checker.py

| テスト ID | シナリオ | 期待値 |
|-----------|---------|--------|
| U-093-001 | generates 全ファイル存在 | drift なし |
| U-093-002 | generates の 1 ファイルが存在しない | WARNING 1 件 |
| U-093-003 | generates 全ファイル不在 | WARNING N 件 |
| U-093-004 | status=active、updated_at = 31 日前 | freshness WARNING |
| U-093-005 | status=active、updated_at = 29 日前 | OK |
| U-093-006 | kind=recovery、updated_at = 8 日前 | recovery freshness WARNING |
| U-093-007 | kind=recovery、updated_at = 6 日前 | OK |
| U-093-008 | dependency cycle A→B→C→A | ERROR 検出 |
| U-093-009 | dependency 非 cycle A→B→C | OK |

### 9.2 Unit test: test_curator_engine.py

| テスト ID | シナリオ | 期待値 |
|-----------|---------|--------|
| U-093-010 | failure_count = 2 → agent review | REVIEW_LEVEL=agent |
| U-093-011 | failure_count = 3 → council review | REVIEW_LEVEL=council |
| U-093-012 | failure_count = 5 → human escalation | REVIEW_LEVEL=human |
| U-093-013 | last_fired = 31 日前 → demotion 候補 | demotion=True |
| U-093-014 | last_fired = 29 日前 → OK | demotion=False |
| U-093-015 | last_fired = 91 日前 → archive 候補 | archive=True |

### 9.3 Integration test

- fake `plan_registry` / `plan_generates` / `sprint_progress` / `failure_log` を SQLite in-memory で作成
- `helix dashboard plan-progress --json` が Layer 別集計を正確に返す
- `helix doctor` が drift / freshness / cycle の 4 check を全 PASS する

---

## §10. DoD (完了条件)

- [ ] `cli/lib/plan_drift_checker.py` 実装完了、`py_compile` PASS
- [ ] helix doctor に 4 check (check_plan_drift / check_plan_freshness / check_recovery_plan_freshness / check_plan_dependency_cycle) が advisory mode で追加
- [ ] `cli/helix-dashboard plan-progress` subcommand が `--json` で valid JSON を返す
- [ ] `cli/lib/curator/curator_engine.py` + `escalation_matrix.py` 実装完了
- [ ] `pytest cli/lib/tests/test_plan_drift_checker.py` 全 PASS (9 ケース)
- [ ] `pytest cli/lib/tests/test_curator_engine.py` 全 PASS (6 ケース)
- [ ] 既存 `helix dashboard` の既存 subcommand に影響がない (既存テスト全 PASS)
- [ ] 既存 `helix doctor` の既存 check に影響がない (既存テスト全 PASS)
- [ ] `docs/adr/ADR-027.md` 起票完了 + PLAN-093 frontmatter に `related_adr: [ADR-027]` 明記
- [ ] PLAN-097 との escalation インターフェース仕様を ADR-027 §Implementation Plan に明記

---

## §11. V-model 4 artifact trace

| Artifact | ファイル |
|---------|---------|
| ① 設計 (本 PLAN §5-§8) | docs/plans/PLAN-093-plan-drift-detection-curator.md |
| ② 実装コード | cli/lib/plan_drift_checker.py / cli/lib/curator/*.py / cli/helix-dashboard |
| ③ テスト設計 | docs/v2/L4-test-design/PLAN-093-test-design.md (PLAN-093 起票後に別途起票) |
| ④ テストコード | cli/lib/tests/test_plan_drift_checker.py / test_curator_engine.py |

- 設計 → テスト設計: テスト設計ファイル `docs/v2/L4-test-design/PLAN-093-test-design.md`
- テスト設計 → 設計: 対象設計 `PLAN-093 §5-§9`
- 設計 → 実装コード: 実装ファイル `cli/lib/plan_drift_checker.py` / `curator/`
- テストコード → テスト設計: DoD 検証 `PLAN-093 U-093-001〜015`

**QA 追加テスト (V-model TDD 補足)**:
- drift detector は L6 QA 追加テスト範疇 (regression / exploratory / edge-case)
- `qa` agent_slot (frontmatter 追加済み) が L4 Sprint 完了後に追加テストを実施する
- QA 追加テストは L3.5 単体テスト設計 (PLAN-093 §9.1/9.2) を置換しない独立レイヤーとして扱う (PLAN-091 §10.2 準拠)

---

## §12. 関連

- **親 PLAN**: PLAN-MM-001 (V5 全体構想)
- **requires**: PLAN-091 (frontmatter 語彙定義) / PLAN-092 (helix.db v35 schema + plan_generates テーブル)
- **blocks**: PLAN-095 (PoC matrix は drift 検出前提) / PLAN-097 (Curator レビュー注入と連動) / PLAN-098 (recovery kind freshness check)
- **ADR**: ADR-027 (drift 検出 + Curator 採用判断)
- **参考**: helix_improvement_plan_draft.md §Phase 4 / §Phase 6 / ADR-018 (ADR template)
