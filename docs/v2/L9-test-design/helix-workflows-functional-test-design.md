---
doc_id: l9-helix-workflows-functional-test-design
title: "HELIX-workflows V2 機能テスト設計 (functional test design)"
status: implemented
created: 2026-05-27
owner: PM
process_layer: L9
parent_plan: L4-helix-workflows-機能設計plan
pairs_design: docs/v2/L4-architecture/helix-workflows-functional-design.md
industry_standards:
  - IEEE 829-2008 (test documentation)
  - ISO/IEC/IEEE 29119-3 (test design)
---

# HELIX-workflows V2 機能テスト設計 (functional test design)

## §0 概要

本書は `docs/v2/L4-architecture/helix-workflows-functional-design.md` の 5 機能領域（F1〜F5）と 1 対 1 で対応する ST-F1〜ST-F5 を定義する。
本体化済み設計を `helix doctor` / hook / CLI / DB schema で再現することを目的とし、`L4↔L9` の pair freeze を実装可能状態で検証する。

この test design は次の前提で記述する。

- fixture 実体は `tests/fixtures/l9/st-f1` 配下に wave 後半で作成
- コマンドは必須観点を満たす最短実行ライン
- 主要出力は数値条件（DoD）を持ち、pass のみで pair freeze 遷移可能

### §0.1 テスト前提（pair 固定）

- `design_doc`: `docs/v2/L4-architecture/helix-workflows-functional-design.md`
- `pairs`: `docs/v2/L9-test-design/helix-workflows-functional-test-design.md` ↔ `docs/v2/L4-architecture/helix-workflows-functional-design.md`
- `plan`: `docs/plans/L4/L4-helix-workflows-機能設計plan.md`
- `schema`: `cli/lib/dispatch`, `helix.db.*` 系
- `adr_snapshot`:
  - **ADR-044** (構造/永続化/ratchet/audit): ST-F1〜ST-F5 と pair freeze
  - **ADR-045** (F6-F10 governance): ST-F6〜ST-F10 と Decision-1〜5 pair freeze
    - ST-F6 ↔ ADR-045 Decision-1 (Homeostasis Governance)
    - ST-F7 ↔ ADR-045 Decision-3 (Evolution Promotion Guard)
    - ST-F8 ↔ ADR-045 Decision-4 (Reproduction Order)
    - ST-F9 ↔ ADR-045 Decision-2 (Survival Operations)
    - ST-F10 ↔ ADR-045 Decision-5 (Symbiosis DDD ACL)

## §1 機能テスト方針

ST-F1〜ST-F5 は以下の三層で検証する。

- 機能検証: F1〜F5 の要件を設計・実装の中間状態含め検証
- 機械処理検証: `helix doctor` / `helix plan` / `helix skill` / guard の出力状態を検証
- trace 検証: 4 artifact の双方向（設計→テスト、実装→設計）を検証

### §1.1 事前条件

| 条件 | 必須 | 検証 | 実装_status |
|---|---|---|---|
| 設計 doc status | in_progress または finalized | frontmatter 読込 | planned |
| plan file | L4 plan 存在 | `test_plan_path` 解決 | planned |
  | テスト doc | 対応 L4 設計節存在 | pairs_design/pairs_test_design | planned |
| DB | helix.db migration 完了 | `sqlite3` 接続確認 | planned |

### §1.2 観点

- AC mapping を固定し、未実装の失敗条件は `planned` で明示して carry
- 仕様の有意誤差を避けるため、全ステップで同じ `fixture root` を参照
- `pair_design` と `pairs_test_design` の相互指向性を検証

### §1.3 受け入れルール

- 実施した check/CLI の結果が `DoD` 条件を満たすこと
- ST テスト完了で `finalized → pair_verified` 遷移を更新可能
- `implementation_status` が `planned` の項目は次 wave carry のみ

## §2 ST-F1〜ST-F10

### ST-F1 ドキュメント体系

- **観点**: 4 ドメイン分離 + ライフサイクル遷移 + SSoT sync + 4 artifact trace
- **入力 / fixture**: `tests/fixtures/l9/st-f1/`
- **期待結果**: 設計 4 ドメイン構造と trace が断絶なしで機械評価できる
- **検証コマンド**:

```bash
helix doctor --check-doc-lifecycle --json
helix doctor --check-4-domain-separation --json
helix doctor --check-ssot-sync --json
helix doctor --check-4-artifact-trace --json
```

- **DoD**:
  - 4 ドメイン分離違反 0 件
  - doc lifecycle state 遷移エラー 0 件
  - SSoT drift レポートが 0 件（許容 drift のみ）
  - `pairs_design` と `pairs_test_design` の双方向参照が 100%
- **AC-mapping**: AC-12 / AC-13 / AC-15
- **実行時間**: 10 秒以内で完了
- **implementation_status**: planned
- **fixture contract**:

```yaml
fixture:
  path: tests/fixtures/l9/st-f1
  files:
    - plan.yml
    - doc_frontmatter.jsonl
    - domain_map.csv
    - trace_edges.ndjson
  expected:
    mismatch_threshold: 0
```

→ pair: L4 §1

### ST-F2 PLAN テンプレート規約

- **観点**: frontmatter completeness + 命名規則 + template usage + 工程表内蔵 + ADR snapshot
- **入力 / fixture**: `tests/fixtures/l9/st-f2/`
- **期待結果**: PLAN 要素が完備し、`check_*` の想定失敗が再現可能
- **検証コマンド**:

```bash
helix plan validate --plan docs/plans/L4/L4-helix-workflows-機能設計plan.md
helix doctor --check-plan-frontmatter-completeness --json --plan docs/plans/L4/L4-helix-workflows-機能設計plan.md
helix doctor --check-plan-naming-convention --json
helix doctor --check-plan-adr-snapshot --json
```

- **DoD**:
  - required fields 達成率 100%
  - naming mismatch 0 件
  - テンプレート不整合 0 件
  - ADR 紐づけ欠落 0 件
- **AC-mapping**: AC-FR-XX（PLAN frontmatter 検証）
- **実行時間**: 5 秒以内
- **implementation_status**: planned
- **fixture contract**:

```yaml
fixture:
  path: tests/fixtures/l9/st-f2
  files:
    - plan_frontmatter_cases.csv
    - naming_negative.json
    - template_manifest.yml
  expected:
    mandatory_errors: 0
    warn_limit: 2
```

→ pair: L4 §2

### ST-F3 skill 体系 + 推挙 framework

- **観点**: 9 カテゴリ責務分離 + 推挙 framework 動作 + catalog rebuild + 使用統計 + 組合せルール
- **入力 / fixture**: `tests/fixtures/l9/st-f3/`
- **期待結果**: `helix skill chain` が期待 skill set を返し、catalog/stats が更新可能
- **検証コマンド**:

```bash
helix skill chain "L4 方式設計の F3 を検証"
helix skill catalog rebuild
helix skill stats --days 30 --by skill_id
```

- **DoD**:
  - 推奨精度 ≥ 80%（人間レビューとの一致）
  - catalog load error 0
  - mandatory subagent と on_demand の role 一致率 100%
- **AC-mapping**: AC-AG-01 / AC-AG-02
- **実行時間**: 10 秒以内
- **implementation_status**: planned
- **fixture contract**:

```yaml
fixture:
  path: tests/fixtures/l9/st-f3
  files:
    - task_query_set.md
    - catalog_diff.golden.json
    - skill_stats_gold.csv
  expected:
    precision_min: 80
    catalog_errors_max: 0
    guard_exit_expected: [0, 2]
```

→ pair: L4 §3

### ST-F4 ワークフロー / 9 mode 入口分岐

- **観点**: 9 mode 入口分岐動作 + Forward 回帰 + V-model 4 artifact trace + 工程専門 workflow
- **入力 / fixture**: `tests/fixtures/l9/st-f4/`
- **期待結果**: mode 切替が `mode_transition` に記録され、Forward 接続が成功
- **検証コマンド**:

```bash
helix init --mode forward
helix reverse design --step R2
helix discovery init
helix sprint status
helix doctor --check-mode-routing --json
```

- **DoD**:
  - mode_transition event >= 1
  - 9 mode 入口から forward に戻る成功率 100%
  - 工程専門 workflow doc 参照が不足しない
- **AC-mapping**: AC-MOD-01 / AC-MOD-02
- **実行時間**: 8 秒以内
- **implementation_status**: planned
- **fixture contract**:

```yaml
fixture:
  path: tests/fixtures/l9/st-f4
  files:
    - mode_entry_cases.csv
    - forward_routing_cases.yml
    - process_transition.ndjson
  expected:
    forward_success: 1.0
    transition_events_min: 1
    unresolved_events_max: 0
```

→ pair: L4 §4

### ST-F5 オーケストレーション

- **観点**: モデル割当遵守 + 並列 8 達成 + 委譲決定木自動推挙 + guard + advisor 召喚
- **入力 / fixture**: `tests/fixtures/l9/st-f5/`
- **期待結果**: 委譲先が規約どおり選択され、guard が不正入力を停止
- **検証コマンド**:

```bash
helix codex --role tl-advisor --task "test"
helix claude --role pm-advisor --execute --task "scope"
pretooluse-agent-guard.sh --payload '{"subagent_type":"agent","tool":"helix.codex","tool_input":{"model":"gpt-5.5","role":"tl"}}'
pretooluse-agent-guard.sh --payload '{"subagent_type":"unknown","tool":"helix.codex","tool_input":{"model":"gpt-5.5","role":"tl"}}'
```

- **DoD**:
  - 並列達成回数 8 を 1 回以上記録
  - guard で invalid role を確実に block
  - advisor 呼び出しが evidence に残る
  - モデル/役割の不一致率 0
- **AC-mapping**: AC-ORCH-01 / AC-ORCH-02
- **実行時間**: 12 秒以内
- **implementation_status**: planned
- **fixture contract**:

```yaml
fixture:
  path: tests/fixtures/l9/st-f5
  files:
    - delegation_cases.csv
    - guard_payloads.json
    - advisor_log_golden.json
    - parallel_metrics.csv
  expected:
    parallel_target: 8
    max_exit_code_invalid: 2
    advisory_coverage_min: 1
```

→ pair: L4 §5

### ST-F6 恒常性 monitoring

- **観点**: context 使用率 / workspace 規模 / token 消費 / 並列度 / balance_ratio の動的 throttle 動作
- **入力 / fixture**: `tests/fixtures/l9/st-f6/`
- **期待結果**: context 使用率 / workspace 規模 / token 消費 / 並列度 / balance_ratio の制御で auto throttle が発火
- **検証コマンド**:

```bash
helix budget status --homeostasis
```

- **DoD**:
  - 6 metric 全て threshold 設定
  - warning 100% 発火
  - auto throttle 90% 成功
- **AC-mapping**: AC-FR-17
- **実行時間**: 20 秒以内
- **implementation_status**: planned
- **fixture contract**:

```yaml
fixture:
  path: tests/fixtures/l9/st-f6
  files:
    - metrics_homeostasis.csv
    - warning_threshold.yml
  expected:
    warning_fire_rate: 1.0
    auto_throttle_success: 0.9
```

#### pair freeze (ADR-045 Decision-1: Homeostasis Governance)

本 ST の合格判定は **ADR-045 Decision-1** と双方向 trace する。

- L4 機能設計 §6 (F6 恒常性) ↔ 本 ST-F6 の pair freeze
- governance ルール:
  - 監視 metric 6 種 (opus_residual_ratio / delegation_ratio / parallel_compliance_ratio / gate_pass_rate / audit_drift_count / carry_residual_count)
  - 監視周期: statusLine (毎 turn) + PreCompact + 週次 `helix budget --homeostasis`
  - homeostatic response: 閾値超過 → `helix doctor --check-homeostasis` 警告 → PM エスカレーション
- 安全境界: 自動修復は行わず人間判断介在を保持
- 関連 doc: `docs/adr/ADR-045-helix-workflows-f6-f10-governance-snapshot.md` §Decision-1

→ pair: L4 §6



### ST-F7 進化 (fork + promote / deprecate)

- **観点**: PLAN fork → experiment → accuracy_score 計測 → promote/deprecate の自動 cycle
- **入力 / fixture**: `tests/fixtures/l9/st-f7/`
- **期待結果**: `helix plan fork` / `helix evolution score` / `helix evolution promote` または `deprecate` の event が記録される
- **検証コマンド**:

```bash
helix plan fork PLAN-X --mutation "experiment"
helix evolution score PLAN-X-experiment
helix evolution promote PLAN-X-experiment
```

- **DoD**:
  - experiment cycle 1 回完遂
  - score 計測
  - retire/deprecate event 記録
- **AC-mapping**: AC-FR-18
- **実行時間**: 30 秒以内
- **implementation_status**: planned
- **fixture contract**:

```yaml
fixture:
  path: tests/fixtures/l9/st-f7
  files:
    - evolution_cycle.yml
    - score_threshold.json
  expected:
    cycle_completed: true
    score_recorded: true
    event_count_min: 1
```

#### pair freeze (ADR-045 Decision-3: Evolution Promotion Guard)

本 ST の合格判定は **ADR-045 Decision-3** と双方向 trace する。

- L4 機能設計 §7 (F7 進化) ↔ 本 ST-F7 の pair freeze
- governance ルール:
  - 進化サイクル: Variation (fork) → Selection (score) → Promotion (promote) → Deprecation
  - 安全境界: score 閾値 + dry-run/canary 期間 + 人間承認 / advisor 承認 + revert 経路
- 安全境界: parent_design / accepted ADR 改変は人間承認必須、promote 後 N session 以内なら無条件 revert 可
- 関連 doc: `docs/adr/ADR-045-helix-workflows-f6-f10-governance-snapshot.md` §Decision-3

→ pair: L4 §7

### ST-F8 繁殖 (version migration)

- **観点**: HELIX-workflows V → V+1 の migration、portable package export/import の往復、過去 PLAN 継承
- **入力 / fixture**: `tests/fixtures/l9/st-f8/`
- **期待結果**: version bump 後に portable と migration が往復し整合が保たれる
- **検証コマンド**:

```bash
helix version bump --minor
helix portable export
helix portable adopt path/to/adr.tar.gz
helix migrate v1 --to v2
```

- **DoD**:
  - 双方向 migration round-trip 100% 整合
  - 過去 PLAN 全件継承
- **AC-mapping**: AC-FR-19
- **実行時間**: 45 秒以内
- **implementation_status**: planned
- **fixture contract**:

```yaml
fixture:
  path: tests/fixtures/l9/st-f8
  files:
    - migration_matrix.csv
    - plan_catalog.json
  expected:
    roundtrip_success: 1.0
    plan_retain_count: 1.0
```

#### pair freeze (ADR-045 Decision-4: Reproduction Order)

本 ST の合格判定は **ADR-045 Decision-4** と双方向 trace する。

- L4 機能設計 §8 (F8 繁殖) ↔ 本 ST-F8 の pair freeze
- governance ルール:
  - 固定 6 step: schema_version bump → plan_version bump → portable export → project apply → rollback evidence → smoke test
  - 互換性: backward compat 1 stage 保証 + forward compat warn-only + breaking change cap (1 release 内で複数 schema bump 禁止)
- 安全境界: 順序逸脱は data loss リスク、rollback evidence (`.helix/audit/migration-YYYYMMDD.yaml`) で always-available 性確保
- 関連 doc: `docs/adr/ADR-045-helix-workflows-f6-f10-governance-snapshot.md` §Decision-4

→ pair: L4 §8

### ST-F9 排泄 (PLAN apoptosis)

- **観点**: stale PLAN 自動 detection / superseded marking / archive / DB autophagy 全フロー
- **入力 / fixture**: `tests/fixtures/l9/st-f9/`
- **期待結果**: stale candidate / warning / archive / obsolete marking が end-to-end で進行する
- **検証コマンド**:

```bash
helix plan apoptosis --dry-run
helix plan apoptosis --execute
```

- **DoD**:
  - 5 lifecycle 状態の自動 action 発火
  - archive 100% 成功
- **AC-mapping**: AC-FR-20
- **実行時間**: 60 秒以内
- **implementation_status**: planned
- **fixture contract**:

```yaml
fixture:
  path: tests/fixtures/l9/st-f9
  files:
    - apoptosis_candidates.csv
    - autophagy_report.yml
  expected:
    action_count_min: 5
    archive_success: 1.0
```

#### pair freeze (ADR-045 Decision-2: Survival Operations)

本 ST の合格判定は **ADR-045 Decision-2** と双方向 trace する。

- L4 機能設計 §9 (F9 排泄) ↔ 本 ST-F9 の pair freeze
- governance ルール:
  - apoptosis (能動的排除): `helix plan apoptosis` 手動 + 週次 cron
  - autophagy (自浄): `helix db autophagy` 週次
- 安全ゲート 4 段 (★ 必須): dry-run 先行 + 保護対象リスト (accepted ADR / implemented PLAN / 直近 N 日 event) + idempotency + production 承認ゲート + rollback evidence (`.helix/audit/apoptosis-YYYYMMDD.yaml`)
- 関連 doc: `docs/adr/ADR-045-helix-workflows-f6-f10-governance-snapshot.md` §Decision-2

→ pair: L4 §9

### ST-F10 共生 (multi-framework)

- **観点**: 他 framework との並走宣言 + ADR 取り込み + namespace 競合回避
- **入力 / fixture**: `tests/fixtures/l9/st-f10/`
- **期待結果**: coexist 宣言、既存 ADR 取り込み、競合回避 namespace が成立する
- **検証コマンド**:

```bash
helix coexist --framework rails
helix coexist adopt path/to/adr
helix coexist status
```

- **DoD**:
  - 並走 framework 1 件以上
  - ADR 取り込み 1 件以上
  - namespace 競合 0
- **AC-mapping**: AC-FR-21
- **実行時間**: 20 秒以内
- **implementation_status**: planned
- **fixture contract**:

```yaml
fixture:
  path: tests/fixtures/l9/st-f10
  files:
    - coexist_frameworks.csv
    - adr_adopt_log.json
  expected:
    framework_count_min: 1
    namespace_conflict_max: 0
```

#### pair freeze (ADR-045 Decision-5: Symbiosis DDD Anti-Corruption Layer)

本 ST の合格判定は **ADR-045 Decision-5** と双方向 trace する。

- L4 機能設計 §10 (F10 共生) ↔ 本 ST-F10 の pair freeze
- governance ルール:
  - Internal context (HELIX core) ↔ External context (Codex / Claude / GitHub / MCP / 他 OSS)
  - Anti-Corruption Layer: adapter (`cli/helix-<external>`) + translator (schema 変換) + guard (fail-close)
  - 共生受入規約: `helix coexist framework <name>` + `helix coexist adopt --compatibility-adr <ADR-NNN>`
- 安全境界: namespace 競合は宣言時 rejection、`helix doctor check_framework_coexist` で機械化
- 関連 doc: `docs/adr/ADR-045-helix-workflows-f6-f10-governance-snapshot.md` §Decision-5

→ pair: L4 §10

### ST-F6〜ST-F10 実行補助ルール

- ST-F6〜ST-F10 は fixture 実体未作成時でも planned 仕様として計画可能で、`tests/fixtures/l9/` 配下の未整備を carry として明記する
- ST-F7/ST-F9 の併用実行時は `dry-run` 実行を先に行い、`execute` は承認ゲートを経てから開始する
- ST-F8 と ST-F10 は順序依存を持つため、migration → coexist の順で `tests order` を固定する
- ST-F9 の weekly cron は環境差分により schedule drift が起きるため、再現用 fixture で `timezone` を固定する
- いずれの ST でも `implementation_status: planned` は次 wave carry へ明示し、done 化条件はステータス更新で判定する
- DoD 判定は全項目で `pass` のみを carry 可能条件とし、`warn` 以上は未決定として保留する
- L9 pair freeze 時は `tests/fixtures` の期待値ファイル更新と併せて実施し、`pair_completeness` を維持する

## §3 10 機能領域 × 機械処理 ↔ ST-F1〜F10 双方向 trace

| ST | 対応 F | check | hook | CLI / DB | ADR Decision |
|---|---|---|---|---|---|
| ST-F1 | F1 | check_doc_lifecycle / check_4_domain_separation / check_ssot_sync / check_4_artifact_trace | pre-commit doc lint / pre-tool-use | helix doctor, helix.db.event_log | ADR-044 Decision-1, Decision-2 |
| ST-F2 | F2 | check_plan_frontmatter_completeness / check_plan_naming_convention / check_plan_adr_snapshot | pre-commit plan validate | helix plan, helix.db.plan_registry | ADR-044 Decision-3 |
| ST-F3 | F3 | check_skill_catalog_freshness / check_skill_usage | post-task skill log | helix skill, helix.db.skill_usage | ADR-044 Decision-1 |
| ST-F4 | F4 | check_mode_routing / check_pair_freeze | SessionStart mode hint | helix init/reverse/research/sprint, helix.db.mode_transition | ADR-044 Decision-1 |
| ST-F5 | F5 | check_role_assignment / check_parallel_compliance | pretooluse-agent-guard | helix codex/claude/agent, helix.db.role_audit | ADR-044 Decision-4 |
| ST-F6 | F6 | check_homeostasis | statusLine + PreCompact | helix budget --homeostasis, helix doctor | **ADR-045 Decision-1** |
| ST-F7 | F7 | check_plan_fork / check_evolution_score | mutation hook | helix plan fork, helix evolution {score,promote,deprecate} | **ADR-045 Decision-3** |
| ST-F8 | F8 | check_version_migration | migration event hook | helix version bump, helix portable {export,import,adopt}, helix migrate | **ADR-045 Decision-4** |
| ST-F9 | F9 | check_plan_apoptosis | weekly cron | helix plan apoptosis, helix db autophagy | **ADR-045 Decision-2** |
| ST-F10 | F10 | check_framework_coexist | coexist event hook | helix coexist {framework,status,adopt} | **ADR-045 Decision-5** |

## §4 非機能テスト

### 性能テスト

- `helix doctor` 95 パーセンタイルは 30 秒以内
- `helix plan validate` は 5 秒以内
- `helix skill chain` は 10 秒以内
- 失敗時は `tests/fixtures/l9/perf/` のメトリクスを比較

```yaml
perf_threshold:
  doctor_complete_seconds: 30
  plan_validate_seconds: 5
  skill_chain_seconds: 10
  failure_retry_limit: 3
implementation_status: planned
```

### 信頼性テスト

- hook fail-close: 不正 12 種外 subagent は 100% 失敗
- SessionStart fail-open: `mode_transition` 不正時に復帰ルートがあること
- 再試行後の回復率 95% 以上

```yaml
reliability:
  guard_fail_rate_accept: 1.0
  session_start_fail_open: true
  recovery_success_min: 0.95
  implementation_status: planned
```

### 保守性テスト

- detector drift（許可 subagent enum）を検出し、変更時に plan carry
- 断線チェック: `pairs_design` と `pairs_test_design` の 1 対 1 が外れない
- fixture と doc schema の不整合を CI で fail-close 化

```yaml
maintainability:
  enum_drift: enabled
  pair_completeness: required
  schema_invariant_check: required
  implementation_status: planned
```

## §5 残課題（本 wave carry）

- fixture 実体（`tests/fixtures/l9/st-f*/`）を実ファイルとして追加
- ST 全項目の `implementation_status` を implemented へ更新（L7-L9 本体化で）
- ST-F4/ST-F5 の mode/guard 実測値を本番運用前に確定
- ST 全体を CI 実行パイプラインに接続
- ST-F6〜ST-F10 の fixture も同時に投入し、監査観点を一貫維持

## 付録 A 実行メモ

### A.1 実行順序

1. `ST-F1`（ドキュメント体系）
2. `ST-F2`（PLAN ルール）
3. `ST-F3`（skill）
4. `ST-F4`（workflow）
5. `ST-F5`（orchestration）
6. `ST-F6`（homeostasis）
7. `ST-F7`（evolution）
8. `ST-F8`（reproduction）
9. `ST-F9`（apoptosis）
10. `ST-F10`（symbiosis）
11. `§4 非機能`（性能 / 信頼性 / 保守性）

### A.2 失敗時の carry ルール

- planned 実装対象の失敗は `implementation_status: planned` の carry note へ保存
- 失敗値は `docs/v2/L4-architecture/helix-workflows-functional-design.md` の残課題へ 1 箇所ずつ転記
- 前提 fixture が存在しない場合は 0 降格ではなく `pending fixture` で carry

### A.3 監査出力例

```yaml
test_run:
  suite: L9-ST-functional
  plan_ref: L4-helix-workflows-機能設計plan
  started_at: 2026-05-27T00:00:00Z
  counts:
    passed: 0
    planned: 5
    todo: 0
  exit_code: 0
  evidence:
    - docs/v2/L4-architecture/helix-workflows-functional-design.md
    - docs/plans/L4/L4-helix-workflows-機能設計plan.md
```

生物学対応: 本章は全体として F1〜F5 対応の検証系を担保
