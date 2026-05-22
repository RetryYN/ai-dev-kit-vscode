---
plan_id: PLAN-166
title: "PLAN-166: handover protocol v2 (CRDT-like merge support)"
kind: impl
layer: L4
drive: be
status: draft
size: M
created: 2026-05-23
owner: PM
agent_slots:
  - role: tl
    slot_label: "TL — CRDT セマンティクス設計・merge 衝突ケース定義レビュー"
  - role: se
    slot_label: "SE — cli/lib/handover_merge.py 実装 + helix-handover merge 拡張"
  - role: qa
    slot_label: "QA — merge 衝突 fixture test 設計・bats test 実装"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-128 schema 整合確認・フィールド分類妥当性チェック"
generates:
  - artifact_path: cli/lib/handover_merge.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_handover_merge.py
    artifact_type: test
  - artifact_path: docs/commands/handover-merge.md
    artifact_type: doc_update
dependencies:
  parent: PLAN-128
  requires:
    - PLAN-128
  blocks: []
related_adr: []
related_plans:
  - PLAN-128
related_docs:
  - helix/HELIX_CORE.md §BE 実装時の Handover ファイル維持
  - CLAUDE.md §BE 実装時の Handover ファイル維持
  - docs/plans/PLAN-128-handover-schema-enhancement.md
---

# PLAN-166: handover protocol v2 (CRDT-like merge support)

> **kind**: impl / **layer**: L4 / **drive**: be
> PLAN-128 の子 PLAN。Opus / Codex / Sonnet が並列で `CURRENT.json` を更新した時の merge conflict を CRDT-like operation で解消する `helix handover merge` CLI を実装する。

---

## §0. 背景

PLAN-128 で `CURRENT.json` schema に 5 新フィールドが追加された。並列 session (Opus + Codex 委譲 + PMO Sonnet) では複数エージェントが handover を同時更新するケースが発生しうる。現状は last-write-wins の単純上書きのみで、同時更新時に blocker や agent_slot_history が欠落するリスクがある。

**merge セマンティクス分類**:

| セマンティクス | フィールド |
|---|---|
| **LWW** (タイムスタンプ新しい方) | status / owner / task_id / title / plan_id / head_sha / next_action / context_snapshot_path |
| **counter_max** (後退させない) | progress_percent |
| **set_union** (合成・重複排除) | files / tests / blockers / notes |
| **set_union_by_id** (id で重複排除) | blocker_list |
| **set_union_by_key** ((role, timestamp) で重複排除) | agent_slot_history |

conflict 検出時は advisory WARN。`--strict` 指定時は非 0 終了コード。

---

## §1. 業界 standard 参照

| 参照 | source | 引用用途 |
|---|---|---|
| Automerge (CRDT library) | https://automerge.org/docs/cookbook/real-time/ | JSON document フィールド単位 CRDT merge の設計パターン |
| Riak CRDT データ型 | https://docs.riak.com/riak/kv/latest/developing/data-types/index.html | LWW register / Set / Counter の concrete 実装例 |
| RFC 7386 - JSON Merge Patch | https://datatracker.ietf.org/doc/html/rfc7386 | JSON merge の標準仕様。LWW 部分の設計根拠 |
| Kleppmann - Designing Data-Intensive Applications §CRDT | https://dataintensive.net/ | LWW / Set-union / Counter の CRDT セマンティクス理論的根拠 |

---

## §2. 実装設計

### merge 関数シグネチャ

```python
def merge_handovers(
    base: dict,
    target: dict,
    *,
    strict: bool = False,
) -> tuple[dict, list[str]]:
    """
    base と target の CURRENT.json を CRDT-like merge する。
    Returns: (merged_dict, warnings)
    strict=True の場合、warnings 非空で MergeConflictError を raise。
    """
```

### CLI

```
helix handover merge <base-file> <target-file> [--output <out>] [--strict] [--json]
```

- `--output` 省略時: stdout に JSON 出力 (CURRENT.json への自動上書きなし)
- `--strict`: conflict WARN があれば exit 1
- `--json`: warnings も JSON 形式で出力

---

## §3. Sprint 計画

| Sprint | 内容 | 担当 | 完了条件 |
|---|---|---|---|
| **.1** | `handover_merge.py` + 5 merge helper + `MergeConflictError` | tl + se | T1-T6 PASS、py_compile PASS |
| **.2** | `helix handover merge` CLI 実装 | se | `--help` に引数表示、`--output` / `--strict` / `--json` 動作確認 |
| **.3** | unit test 7 件 + bats test 追加 | qa | T7 (旧 schema backward compat) PASS、bats PASS |

**entry 条件**: PLAN-128 Sprint .1 完了 (`BlockerEntry` / `AgentSlotRecord` が import 可能) を確認してから着手。

**単体テスト 7 件** (T1: LWW 新 timestamp 採用, T2: LWW 同時書き込み → WARN, T3: set_union 合成, T4: blocker_list id 重複排除, T5: progress_percent 後退しない, T6: strict + conflict → MergeConflictError, T7: 旧 schema との merge で KeyError なし)

---

## §4. DoD

1. T1-T7 全 PASS
2. `python3 -m py_compile cli/lib/handover_merge.py` PASS
3. `helix handover merge --help` に `--output` / `--strict` / `--json` 表示
4. bats test PASS、既存 `pytest cli/lib/tests/test_handover*.py -q` 全 PASS (回帰なし)
5. `python3 cli/lib/plan_validator.py docs/plans/PLAN-166-*.md` PASS

---

## §5. V-model 4 artifact trace

| Artifact | ファイル |
|---|---|
| ① 設計 (本 PLAN) | docs/plans/PLAN-166-handover-protocol-v2-crdt-merge.md |
| ② 実装コード | cli/lib/handover_merge.py |
| ③ テスト設計 | docs/v2/L4-test-design/PLAN-166-handover-merge-test-design.md (予定) |
| ④ テストコード | cli/lib/tests/test_handover_merge.py |

**双方向 reference**: `handover_merge.py` docstring に「設計: PLAN-166」、test docstring に「DoD 検証: PLAN-166 §4」を追記。

---

## §6. リスク

| リスク | 緩和策 |
|---|---|
| PLAN-128 Sprint .1 未完了での着手 | Sprint .1 entry 条件で `BlockerEntry` import 確認を必須化 |
| resolved blocker の set_union 復活 | `resolved_at` 非 null エントリも merge 後保持 + WARN 出力、削除は将来 `--drop-resolved` で対応 |
| merge 後 JSON の誤上書き | `--output` 省略時は stdout のみ。CURRENT.json 上書きは `helix handover update` 経由を原則とする旨を docs に明記 |
