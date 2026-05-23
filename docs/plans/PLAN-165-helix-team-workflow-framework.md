---
plan_id: PLAN-165
title: "PLAN-165: helix-team workflow framework (multi-role coordination)"
kind: impl
layer: L4
drive: be
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
size: M
created: 2026-05-23
owner: PM
agent_slots:
  - role: tl
    slot_label: "TL — workflow YAML schema 設計・DAG 実行エンジン設計レビュー"
  - role: se
    slot_label: "SE — cli/lib/team_runner.py 実装 + helix-team 拡張"
  - role: qa
    slot_label: "QA — bats test 設計・workflow fixture 実装"
  - role: pmo-sonnet
    slot_label: "PMO — 既存 helix team run 整合確認・PLAN-130 重複確認"
generates:
  - artifact_path: cli/templates/team/tl-se-qa.yaml
    artifact_type: template
  - artifact_path: cli/lib/team_runner.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_team_runner.py
    artifact_type: test
  - artifact_path: docs/commands/team-workflow.md
    artifact_type: doc_update
dependencies:
  parent: null
  requires: []
  blocks: []
related_adr: []
related_plans:
  - PLAN-130
related_docs:
  - CLAUDE.md §並列実行ルール
  - helix/HELIX_CORE.md §工程別 subagent 起動マップ
  - docs/commands/index.md
---

# PLAN-165: helix-team workflow framework (multi-role coordination)

> **kind**: impl / **layer**: L4 / **drive**: be
> `helix team run --definition ...` が参照する multi-role 協調 workflow を declarative YAML で定義・実行する framework を整備する。

---

## §0. 背景

`helix team run --definition ...` はエントリーポイントとして存在するが、workflow 定義形式・実行順序・並列可否の決定・結果統合ロジックが散在している。再現性と再利用性が低く、TL→SE→QA のような標準フローを毎回手作りしている。

**解決方針**:
- `cli/templates/team/<name>.yaml` に declarative workflow 定義を置く
- ステップ毎に `role`, `task`, `depends_on` を宣言。依存なし = 並走可、依存あり = 先行完了待ち
- `helix team run --definition <name>` で DAG 実行エンジンが解釈・実行
- PLAN-130 のプロンプトテンプレートを `task_template` で optional 参照

---

## §1. 業界 standard 参照

| 参照 | source | 引用用途 |
|---|---|---|
| GitHub Actions workflow syntax | https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions | `jobs.needs` による DAG 宣言の業界標準形式 |
| Apache Airflow DAG | https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html | DAG task 依存定義・実行順序決定の参照実装 |
| CrewAI Process types | https://docs.crewai.com/concepts/processes | sequential / hierarchical / parallel の 3 プロセス分類 |
| LangGraph multi-agent | https://langchain-ai.github.io/langgraph/concepts/multi_agent/ | role 分担・状態受け渡し・supervisor パターン |

---

## §2. workflow YAML schema

```yaml
# cli/templates/team/tl-se-qa.yaml
name: tl-se-qa
description: "TL 設計 → SE 実装 → QA テスト"
version: "1"
steps:
  - id: design
    role: tl
    task: "設計レビューと API 契約の凍結"
    depends_on: []
    timeout_minutes: 30
    aggregate: false
  - id: implement
    role: se
    task: "API 契約に基づく実装"
    depends_on: [design]
    timeout_minutes: 60
    aggregate: false
  - id: test
    role: qa
    task: "実装の結合テスト + bats test 設計"
    depends_on: [implement]
    timeout_minutes: 30
    aggregate: true
```

**並列判定**: `depends_on: []` ステップ群は相互に並走可能。`aggregate: true` ステップは全先行ステップ完了後に実行。

---

## §3. Sprint 計画

| Sprint | 内容 | 担当 | 完了条件 |
|---|---|---|---|
| **.1** | workflow YAML schema 確定 + load/validate (cycle 検出 + role 検証) | tl + se | schema validate T1-T3 PASS |
| **.2** | DAG 実行エンジン (topological sort + execute_step + collect_results) | se | T4-T6 PASS、`--dry-run` 実行計画表示 |
| **.3** | helix-team 接続 + bats test 追加 | qa | bats PASS、既存 team test 回帰なし |

**単体テスト 6 件** (T1: YAML load 正常, T2: cycle → ValueError, T3: role 不正値検出, T4: topological sort 順序正当性, T5: aggregate なしで前段出力不合成, T6: depends_on 空ステップが並走可と判定)

---

## §4. DoD

1. `cli/templates/team/tl-se-qa.yaml` が schema validate PASS
2. T1-T6 全 PASS
3. `helix team run --definition tl-se-qa --dry-run` が DAG 計画を stdout 出力
4. bats test PASS、既存 `helix team` bats 回帰なし
5. `python3 -m py_compile cli/lib/team_runner.py` PASS
6. `python3 cli/lib/plan_validator.py docs/plans/PLAN-165-*.md` PASS

---

## §5. V-model 4 artifact trace

| Artifact | ファイル |
|---|---|
| ① 設計 (本 PLAN) | docs/plans/PLAN-165-helix-team-workflow-framework.md |
| ② 実装コード | cli/lib/team_runner.py, cli/helix-team, cli/templates/team/tl-se-qa.yaml |
| ③ テスト設計 | docs/v2/L4-test-design/PLAN-165-team-workflow-test-design.md (予定) |
| ④ テストコード | cli/lib/tests/test_team_runner.py |

---

## §6. リスク

| リスク | 緩和策 |
|---|---|
| DAG cycle 検出漏れ | Sprint .1 で T2 (cycle → ValueError) を最初に通過させる |
| aggregate ステップ前段 fail | exit code 確認し 1 件でも fail なら aggregate skip + WARN |
| ROLE_MAP.md role 追加追従 | `load_valid_roles()` を毎回 ROLE_MAP.md から読む設計で対応 |
