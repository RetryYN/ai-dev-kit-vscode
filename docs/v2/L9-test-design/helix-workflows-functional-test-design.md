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

## §2 ST-F1〜ST-F5

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

## §3 5 機能領域 × 機械処理 ↔ ST-F1〜F5 双方向 trace

| ST | 対応 ST | check | hook | CLI / DB |
|---|---|---|---|---|
| ST-F1 | F1 | check_doc_lifecycle / check_4_domain_separation / check_ssot_sync / check_4_artifact_trace | pre-commit doc lint / pre-tool-use | helix doctor, helix.db.event_log |
| ST-F2 | F2 | check_plan_frontmatter_completeness / check_plan_naming_convention / check_plan_adr_snapshot | pre-commit plan validate | helix plan, helix.db.plan_registry |
| ST-F3 | F3 | check_skill_catalog_freshness / check_skill_usage | post-task skill log | helix skill, helix.db.skill_usage |
| ST-F4 | F4 | check_mode_routing / check_pair_freeze | SessionStart mode hint | helix init/reverse/research/sprint, helix.db.mode_transition |
| ST-F5 | F5 | check_role_assignment / check_parallel_compliance | pretooluse-agent-guard | helix codex/claude/agent, helix.db.role_audit |

→ pair: L4 §6

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

## 付録 A 実行メモ

### A.1 実行順序

1. `ST-F1`（ドキュメント体系）
2. `ST-F2`（PLAN ルール）
3. `ST-F3`（skill）
4. `ST-F4`（workflow）
5. `ST-F5`（orchestration）
6. `§4 非機能`（性能 / 信頼性 / 保守性）

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
