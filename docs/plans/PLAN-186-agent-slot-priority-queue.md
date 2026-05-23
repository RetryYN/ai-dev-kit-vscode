---
plan_id: PLAN-186
title: "PLAN-186: agent slot priority queue (urgent / normal / background 3 level)"
layer: L4
kind: refactor
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
size: M
drive: be
created: 2026-05-23
revised: "2026-05-23 (初版起票)"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: dba
    slot_label: "DBA — agent_slots priority column 追加 + v37 migration 設計"
  - role: se
    slot_label: "SE — queue worker priority pop + helix-agent --priority flag 実装"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-088/116 との依存整合・priority 設計確認"
  - role: tl-advisor
    slot_label: "TL adversarial check — G4 凍結判定・priority starve リスク確認"
generates:
  - artifact_path: cli/lib/migrations/v37_agent_slot_priority.py
    artifact_type: schema_migration
  - artifact_path: cli/lib/agent_slot_queue.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_agent_slot_priority.py
    artifact_type: test
  - artifact_path: docs/plans/PLAN-186-agent-slot-priority-queue.md
    artifact_type: design_doc
dependencies:
  parent: PLAN-088
  requires:
    - PLAN-088
    - PLAN-116
  blocks: []
related_plans:
  - PLAN-088 (親 PLAN、agent slot framework、agent_slots table 正本)
  - PLAN-116 (helix.db v36 schema、task_queue と agent_slots 依存元)
  - PLAN-185 (ACID transaction wrapper、priority pop 時の slot 更新を wrap 対象)
---

# PLAN-186: agent slot priority queue

> **本 PLAN の位置付け**: PLAN-088 (agent slot framework) の拡張。  
> 並列 8 slot 全占有時に urgent task が background task に埋もれる問題を
> priority queue (urgent / normal / background 3 level) で解消する。

---

## 1. 目的

agent slot の並列上限 8 に達した際、carry blocker / hotfix (urgent) が
background task (memory persist / stats 集計) に押し出されるリスクを排除する。
`priority` column を agent_slots table に追加し、urgent 優先 pop を実現する。

---

## 2. 背景

### 2.1 現状の問題

PLAN-088 の agent_slots は全 slot を FIFO 管理する。
並列 8 上限到達時に carry blocker が background task と同列で待機する。

| シナリオ | 現状 | 理想 |
|---|---|---|
| carry blocker | background 8 slot 全占有時に待機 | 即 urgent 割り込み |
| hotfix | normal と同列 | urgent 最優先 |
| memory persist | carry blocker と同列 | background に降格 |

### 2.2 PLAN-088 との関係

本 PLAN は PLAN-088 の schema 拡張 + queue worker 変更。
agent prefix / in_progress 重複防止 / 上限 8 の基本設計は変更しない。

---

## 3. 設計方針

### 3.1 priority 3 level

| level | 値 | 用途 |
|---|---|---|
| urgent | 0 | carry blocker / hotfix / G4 fail 対応 |
| normal | 1 | 通常 Codex 委譲 / PMO review (デフォルト) |
| background | 2 | memory persist / stats / doc 生成 |

ORDER BY priority ASC, created_at ASC で pop する。

### 3.2 schema 変更

```sql
-- v37 migration
ALTER TABLE agent_slots ADD COLUMN priority INTEGER NOT NULL DEFAULT 1;
CREATE INDEX IF NOT EXISTS idx_agent_slots_priority ON agent_slots(priority, created_at);
```

既存 slot は `priority=1 (normal)` に初期化 (DEFAULT 1)。

### 3.3 urgent 割り込み制御

background を強制解放する preempt は **本 PLAN では採用しない**。
進行中 background task の中断は成果物不整合を招くため。
代わりに: urgent は background 完了待ちなしに **上限 8 + urgent 数** の一時超過を許容する。

### 3.4 background starve 防止 (aging)

background slot が `created_at` から 30 分超 pending の場合、priority を 1 (normal) に自動昇格する。
閾値は `agent_slot_aging_minutes` config で変更可能 (default=30)。

### 3.5 CLI flag

```bash
helix agent fire --role se --priority urgent   # urgent 指定
helix agent fire --role se                     # 省略時 normal
```

---

## 4. 実装 Sprint

### Sprint .1: schema migration 実装

**担当**: dba  
**scope**: `cli/lib/migrations/v37_agent_slot_priority.py` (up: ALTER + index / down: column drop / idempotent)  
**Entry**: PLAN-088 完遂 + PLAN-116 Sprint .1 完遂  
**Exit**: `helix db migrate` v37 適用 PASS + rollback PASS

### Sprint .2: queue worker + CLI flag 実装

**担当**: se  
**scope**: `cli/lib/agent_slot_queue.py` (pop_next_slot / enqueue_slot / age_background_slots) + `cli/helix-agent fire --priority` オプション追加 + PLAN-185 ACID wrap  
**Entry**: Sprint .1 完遂  
**Exit**: py_compile PASS + 手動 smoke (urgent → normal → background pop 順確認)

### Sprint .3: test + review

**担当**: se + pmo-sonnet  
**scope**: `cli/lib/tests/test_agent_slot_priority.py` (priority pop 順 / urgent 割り込み / aging 昇格 / starve 防止 / ACID wrap)  
**Entry**: Sprint .2 完遂  
**Exit**: pytest 全 PASS + 全回帰 PASS + tl-advisor G4 passed

---

## 5. DoD

- [ ] `cli/lib/migrations/v37_agent_slot_priority.py` 実装済み (up / down / idempotent)
- [ ] `agent_slots.priority` column + index 追加 PASS
- [ ] `cli/lib/agent_slot_queue.py` 実装済み (pop_next_slot / enqueue_slot / age_background_slots)
- [ ] `cli/helix-agent fire --priority urgent|normal|background` 動作確認
- [ ] background aging (30 分超 → normal 昇格) 動作確認
- [ ] PLAN-185 ACID transaction で slot 更新を wrap 済み
- [ ] `cli/lib/tests/test_agent_slot_priority.py` 全 PASS
- [ ] `python3 -m py_compile` 全対象 PASS + 全回帰 PASS (`helix test`)
- [ ] pmo-sonnet review 承認 + tl-advisor G4 passed

---

## 6. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 | docs/plans/PLAN-186-agent-slot-priority-queue.md |
| ② 実装コード | 未着手 | cli/lib/migrations/v37_agent_slot_priority.py / cli/lib/agent_slot_queue.py |
| ③ テスト設計 | 未起票 | docs/v2/L4-test-design/PLAN-186-unit-test-design.md |
| ④ テストコード | 未着手 | cli/lib/tests/test_agent_slot_priority.py |

双方向 reference:
- 本 PLAN → PLAN-088: `dependencies.parent: PLAN-088`
- 本 PLAN → PLAN-116: `dependencies.requires: PLAN-116`
- 実装コード → 本 PLAN: docstring に `# 契約: PLAN-186 §3.1` を明示 (実装時)

---

## 7. 関連リンク

| 文書 | パス |
|---|---|
| PLAN-088 (親 PLAN、agent slot framework) | docs/plans/PLAN-088-todowrite-agent-slot-framework.md |
| PLAN-116 (helix.db v36 schema) | docs/plans/PLAN-116-helix-db-v36-schema.md |
| PLAN-185 (ACID transaction wrapper) | docs/plans/PLAN-185-helix-db-acid-transaction.md |
