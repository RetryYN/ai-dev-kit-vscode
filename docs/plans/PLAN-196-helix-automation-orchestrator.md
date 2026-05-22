---
plan_id: PLAN-196
title: "PLAN-196: helix automation orchestrator (cron / event trigger 統合 CLI)"
layer: L4
kind: impl
status: draft
size: M
drive: be
created: 2026-05-23
revised: "2026-05-23 (初版起票)"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: se
    slot_label: "SE — orchestrator.yaml parser + helix orchestrator CLI + automation_runs 統合"
  - role: devops
    slot_label: "DevOps — cron 設定 / file-event watcher / push event hook 統合"
  - role: pmo-sonnet
    slot_label: "PMO — skills/automation/ 既存資産との整合確認・重複・drift チェック"
  - role: tl-advisor
    slot_label: "TL adversarial check — G4 凍結判定・trigger 設計 review・スケジューラ競合評価"
generates:
  - artifact_path: docs/plans/PLAN-196-helix-automation-orchestrator.md
    artifact_type: design_doc
  - artifact_path: cli/helix-orchestrator
    artifact_type: cli_extension
  - artifact_path: cli/lib/orchestrator.py
    artifact_type: python_module
  - artifact_path: cli/templates/orchestrator/example-workflow.yaml
    artifact_type: yaml_config
  - artifact_path: cli/lib/tests/test_orchestrator.py
    artifact_type: test
dependencies:
  parent: PLAN-099
  requires:
    - PLAN-099
  blocks: []
related_adr: []
related_plans:
  - PLAN-099 (自動走行 framework 5-layer — Layer 5 heartbeat scheduler と trigger 設計が統合点)
  - PLAN-088 (TodoWrite × agent slot framework — agent_slot 発火と orchestrator trigger の責務分離)
test_design: docs/v2/L4-test-design/PLAN-196-unit-test-design.md (別 session 起票予定)
---

# PLAN-196: helix automation orchestrator

> **位置付け**: skills/automation/ 配下に散在する cron / event trigger を
> `helix orchestrator` CLI で統合管理する。PLAN-099 Layer 5 heartbeat を補完し、
> 定型ワークフローの宣言的実行を実現する。

## 1. 目的

HELIX の automation skill (`skills/automation/scheduler` / `job-queue` 等) は個別スクリプトが
散在しており横断的な管理・監視手段がない。本 PLAN は:

1. **orchestrator.yaml による宣言的 trigger 定義** — cron / file-event / manual を YAML で定義
2. **helix.db automation_runs との統合** — 実行履歴を helix.db に記録、`helix orchestrator status` で可視化
3. **PLAN-099 Layer 5 との責務境界確定** — heartbeat (session 継続管理) と orchestrator (バッチワークフロー) の分離

## 2. 背景

### 2.1 現状の散在

| スキル | 役割 | 課題 |
|---|---|---|
| skills/automation/scheduler | cron 設計ガイド | 実行 CLI なし |
| skills/automation/job-queue | job queue 設計ガイド | helix job と二重管理 |
| PLAN-099 Layer 5 heartbeat | 15min carry check | 単一目的のみ |

### 2.2 PLAN-099 Layer 5 との責務分離

```
PLAN-099 Layer 5 (heartbeat): carry > 0 かつ bg task なし → task pop 促進。session 管理専用
PLAN-196 orchestrator:        定型ワークフロー (日次 helix doctor / 週次 skill sweep 等)
```

両者は **異なるスケジューラ** として共存し、役割が重複しない。

## 3. 設計方針

### 3.1 orchestrator.yaml 形式

```yaml
name: nightly-health-check
trigger:
  type: cron           # cron | file-event | manual
  schedule: "0 2 * * *"
steps:
  - name: helix-doctor
    run: helix doctor
  - name: code-stats
    run: helix code stats --scope core5 --bucket coverage_eligible
on_failure: notify     # notify | ignore | stop
```

### 3.2 CLI サブコマンド

```bash
helix orchestrator list                          # 登録済みワークフロー一覧
helix orchestrator run --workflow <name>         # 手動実行
helix orchestrator run --workflow <name> --dry-run
helix orchestrator status [--workflow <name>]    # automation_runs から履歴表示
helix orchestrator enable  --workflow <name>     # cron 有効化 (crontab 登録)
helix orchestrator disable --workflow <name>     # cron 無効化
helix orchestrator logs    --workflow <name> [-n 20]
```

### 3.3 helix.db automation_runs

既存テーブルがなければ Sprint .1 で追加する (idempotent `CREATE TABLE IF NOT EXISTS`):

```sql
CREATE TABLE IF NOT EXISTS automation_runs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow     TEXT NOT NULL,
    trigger_type TEXT NOT NULL,  -- cron | file-event | manual
    status       TEXT NOT NULL,  -- running | success | failure | skipped
    started_at   TEXT NOT NULL DEFAULT (datetime('now','utc')),
    finished_at  TEXT,
    exit_code    INTEGER,
    log_summary  TEXT
);
```

## 4. 実装 Sprint

**Sprint .1** (se): orchestrator.yaml parser + 基本 CLI + automation_runs 統合
- `cli/lib/orchestrator.py`: `load_workflow()` / `run_workflow(dry_run)` / `list_workflows()`
- `cli/helix-orchestrator` (bash router): list / run / status サブコマンド
- `cli/templates/orchestrator/example-workflow.yaml` 新規
- automation_runs テーブル確認 + なければ migration 追加
- `cli/helix` router への `orchestrator` 登録

**Entry**: helix.db 存在確認 / **Exit**: `helix orchestrator list` / `run --dry-run` / `status` 動作確認

**Sprint .2** (se + devops): cron 統合 + enable/disable
- `enable_workflow_cron(wf)` — crontab 登録 (`crontab -l | { cat; echo "..."; } | crontab -`)
- `disable_workflow_cron(wf)` — crontab から該当行を削除
- `helix orchestrator enable` / `disable` サブコマンド実装
- devops: PLAN-099 Layer 5 との scheduler 競合評価

**Entry**: Sprint .1 完遂 / **Exit**: crontab 登録・削除 idempotent 確認

**Sprint .3** (se + pmo-sonnet): pytest + review + G4
- `test_orchestrator.py`: load_workflow valid/invalid / run_workflow dry-run (mock subprocess) /
  automation_runs INSERT 確認 / list_workflows 列挙 / cron enable/disable idempotent (fake crontab)
- pmo-sonnet: skills/automation/ 既存資産との重複・drift 確認
- tl-advisor: G4 凍結判定

**Entry**: Sprint .2 完遂 / **Exit**: pytest 全 PASS + 全回帰 PASS + G4 passed

## 5. DoD

- [ ] `cli/lib/orchestrator.py` 実装済み (load_workflow / run_workflow / list_workflows)
- [ ] `cli/helix-orchestrator` 実装済み (list / run / status / enable / disable / logs)
- [ ] `cli/helix` router に orchestrator 登録済み
- [ ] `cli/templates/orchestrator/example-workflow.yaml` 存在
- [ ] automation_runs テーブル: 実行ごとに INSERT 確認
- [ ] `test_orchestrator.py` 全 PASS (parser / dry-run / DB 登録 / cron enable/disable)
- [ ] `python3 -m py_compile` + 全回帰 PASS (`helix test`)
- [ ] pmo-sonnet review 承認 / tl-advisor G4 passed

## 6. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 | docs/plans/PLAN-196-helix-automation-orchestrator.md |
| ② 実装コード | 未着手 | cli/helix-orchestrator / cli/lib/orchestrator.py |
| ③ テスト設計 | 未起票 | docs/v2/L4-test-design/PLAN-196-unit-test-design.md |
| ④ テストコード | 未着手 | cli/lib/tests/test_orchestrator.py |

双方向 reference: 本 PLAN → PLAN-099 (parent) / PLAN-088 (requires)。
実装コード → 本 PLAN: docstring に `# 契約: PLAN-196 §3` を明示 (実装時)。

## 7. 関連リンク

| 文書 | パス |
|---|---|
| PLAN-099 (親 PLAN、自動走行 framework) | docs/plans/PLAN-099-autonomous-runtime-framework-5layer.md |
| PLAN-088 (TodoWrite × agent slot) | docs/plans/PLAN-088-todowrite-agent-slot-framework.md |
| skills/automation/scheduler | skills/automation/scheduler/SKILL.md |
| skills/automation/job-queue | skills/automation/job-queue/SKILL.md |
