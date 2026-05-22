---
plan_id: PLAN-185
title: "PLAN-185: helix.db ACID transaction wrapper (multi-step DB op 安全化)"
layer: L4
kind: refactor
status: draft
size: M
drive: db
created: 2026-05-23
revised: "2026-05-23 (初版起票)"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: dba
    slot_label: "DBA — context manager 設計 + BEGIN/COMMIT/ROLLBACK 制御実装"
  - role: se
    slot_label: "SE — 既存 helix.db 操作の wrap 置換 + regression test"
  - role: pmo-sonnet
    slot_label: "PMO — 設計整合確認・PLAN-116/092/093 との依存整合チェック"
  - role: tl-advisor
    slot_label: "TL adversarial check — G4 凍結判定・partial commit リスク解消確認"
generates:
  - artifact_path: cli/lib/helix_db_transaction.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_helix_db_transaction.py
    artifact_type: test
  - artifact_path: docs/plans/PLAN-185-helix-db-acid-transaction.md
    artifact_type: design_doc
dependencies:
  parent: PLAN-116
  requires:
    - PLAN-116
  blocks: []
related_plans:
  - PLAN-116 (親 PLAN、plan_registry / task_queue / plan_dependencies / sprint_progress の schema)
  - PLAN-092 (PostToolUse plan 自動登録、複数 table 更新で本 PLAN の wrap が必要)
  - PLAN-093 (drift 検出 Curator、plan_registry + plan_dependencies の同時更新で wrap 対象)
  - PLAN-088 (agent slot framework、agent_slots + task_queue 同時更新で wrap 対象)
---

# PLAN-185: helix.db ACID transaction wrapper

> **本 PLAN の位置付け**: PLAN-116 (helix.db v36 schema) 完遂後の安全化。  
> 複数 table 更新が partial commit で不整合になるリスクを ACID context manager で根絶する。

---

## 1. 目的

helix.db への複数 table 更新が中断時に partial commit となるリスクを排除する。
`with helix_db_transaction(conn) as txn:` 形式の context manager を提供し、
BEGIN IMMEDIATE / COMMIT / ROLLBACK を自動制御する。

---

## 2. 背景

### 2.1 partial commit リスク

PLAN-116 (v36) 追加の 4 table への書き込みは複数箇所から呼ばれる:

- PLAN-092 PostToolUse hook: plan_registry + task_queue を個別 INSERT
- PLAN-088 agent slot: agent_slots + task_queue を個別 UPDATE
- PLAN-093 drift 検出: plan_registry + plan_dependencies を個別 UPDATE

いずれも中断時に half-write が残り helix.db 整合性が壊れる。

### 2.2 SQLite ACID 活用方針

SQLite WAL mode + BEGIN IMMEDIATE で ACID を保証する。
Python `sqlite3` の implicit commit を回避するため明示的な BEGIN/COMMIT/ROLLBACK が必要。

---

## 3. 設計方針

### 3.1 context manager API

```python
# cli/lib/helix_db_transaction.py
@contextmanager
def helix_db_transaction(conn):
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
```

### 3.2 ネスト禁止・WAL フォールバック

ネスト (二重 wrap) は RuntimeError を raise する。
WAL mode 未設定環境では transaction 実行前に自動有効化するフォールバックを持つ。

### 3.3 wrap 対象

Sprint .2 で以下を順次 wrap する:

- `cli/lib/plan_registry.py`: upsert_plan + upsert_dependencies
- `cli/lib/agent_mandatory.py`: fire / release の DB 書き込み部

---

## 4. 実装 Sprint

### Sprint .1: context manager 実装

**担当**: dba  
**scope**: `cli/lib/helix_db_transaction.py` 新規 (BEGIN/COMMIT/ROLLBACK / ネスト禁止 / WAL フォールバック)  
**Entry**: PLAN-116 Sprint .1 完遂 (v36 適用済み)  
**Exit**: py_compile PASS + 手動 smoke 確認

### Sprint .2: 既存操作の wrap 置換

**担当**: se  
**scope**: plan_registry.py + agent_mandatory.py の DB 書き込みを wrap 置換  
**Entry**: Sprint .1 完遂  
**Exit**: py_compile PASS + test_helix_db_v36 / test_agent_mandatory 全 PASS

### Sprint .3: test + review

**担当**: se + pmo-sonnet  
**scope**: `cli/lib/tests/test_helix_db_transaction.py` (正常 commit / 例外 ROLLBACK / ネスト禁止 / WAL フォールバック)  
**Entry**: Sprint .2 完遂  
**Exit**: pytest 全 PASS + 全回帰 PASS + tl-advisor G4 passed

---

## 5. DoD

- [ ] `cli/lib/helix_db_transaction.py` 実装済み (BEGIN/COMMIT/ROLLBACK / ネスト禁止 / WAL フォールバック)
- [ ] plan_registry.py / agent_mandatory.py の DB 書き込みを wrap 置換
- [ ] `cli/lib/tests/test_helix_db_transaction.py` 全 PASS (正常 commit / ROLLBACK / ネスト禁止 / WAL)
- [ ] `python3 -m py_compile` 全対象 PASS + 全回帰 PASS (`helix test`)
- [ ] pmo-sonnet review 承認 + tl-advisor G4 passed

---

## 6. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 | docs/plans/PLAN-185-helix-db-acid-transaction.md |
| ② 実装コード | 未着手 | cli/lib/helix_db_transaction.py |
| ③ テスト設計 | 未起票 | docs/v2/L4-test-design/PLAN-185-unit-test-design.md |
| ④ テストコード | 未着手 | cli/lib/tests/test_helix_db_transaction.py |

双方向 reference:
- 本 PLAN → PLAN-116: `dependencies.parent: PLAN-116`
- 実装コード → 本 PLAN: docstring に `# 契約: PLAN-185 §3.1` を明示 (実装時)

---

## 7. 関連リンク

| 文書 | パス |
|---|---|
| PLAN-116 (親 PLAN、v36 schema) | docs/plans/PLAN-116-helix-db-v36-schema.md |
| PLAN-092 (PostToolUse plan 自動登録) | docs/plans/PLAN-092-posttooluse-plan-auto-register.md |
| PLAN-093 (drift 検出 Curator) | docs/plans/PLAN-093-plan-drift-detection-curator.md |
| PLAN-088 (agent slot framework) | docs/plans/PLAN-088-todowrite-agent-slot-framework.md |
