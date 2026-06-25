---
plan_id: L7-v3-engine-c2-projection-writerplan
title: "L7-v3-engine-c2-projection-writerplan: V3 engine C2 projection-writer (rebuild ⊥ append_event, Python, cli/lib/v3/projection/, test-first)"
kind: impl
layer: L7
drive: be
status: draft
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: "docs/v3/engine/projection-writer.md"
dependencies:
  requires:
    - L7-v3-engine-c1-schema-registryplan
  blocks: []
pairs_test_design:
  - cli/lib/v3/tests/test_projection_writer.py
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE — C2 projection-writer の verify-first 実装 (rebuild⊥append_event / idempotent / deletion / stale / secret guard)"
  - role: qa
    slot_label: "QA — 2x rebuild bit-identical / truncate=projection のみ / append 残存 / secret 非保存 / source 列挙 git→fs fallback の境界網羅判定"
generates:
  - artifact_path: cli/lib/v3/projection/writer.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/projection/upsert.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/projection/sources.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/projection/secret_guard.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/projection/projectors.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/projection/__init__.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/tests/test_projection_writer.py
    artifact_type: test
created: 2026-06-26
revised: 2026-06-26
owner: SE
related_docs:
  - docs/v3/engine/projection-writer.md
  - docs/v3/engine/schema-registry.md
  - docs/v3/L0-L14/L5-detailed-design.md
---

# L7-v3-engine-c2-projection-writerplan

## 0. 目的

V3 engine keystone **C2 = 単一 projection-writer**（`rebuild_projection` ⊥ `append_event`）を Python で実装する（[C2 設計正本](../../v3/engine/projection-writer.md)）。doc/workflow/code/test/FR/設計 を rule で DB へ投影する単一の口。**idempotent / deletion-aware / stale-aware / secret-safe** を最優先契約に固定。

## 0.5 unit 位置づけ（[C6 §4.5 unitized L5-L7 descent](../../v3/engine/doc-workflow-rules.md)）

- **unit_id**: U-ENG-C2
- **parent_l4_component**: L4 §1 「C2 単一 projection-writer」コンポーネント
- **trace_edges（上流接続）**: L4 §1 C2 → [L5 §1.5/§2 投影キー + projection rule](../../v3/L0-L14/L5-detailed-design.md) → [L6 FN-DET-11 db-projection-coverage](../../v3/L0-L14/L6-functional-design.md) → 本 PLAN
- **依存**: U-ENG-C1（schema registry の `TABLE_BY_NAME` / `kind` / `logical_key` を供給）。C1 green 後に着手。
- **descent**: L5/L6 frozen → 本 PLAN は L7（test-first）のみ。

## 1. 受入条件（DoD）

[projection-writer.md §3/§6](../../v3/engine/projection-writer.md) の DbC を満たし、下記 UT が全 green:

1. **idempotent**: 同一 sources で `rebuild_projection` 2 回 → DB 状態 bit-identical（重複行 0）。
2. **truncate scope**: `rebuild_projection` は `kind=="projection"`(49) table のみ TRUNCATE。`config`(6) / `append_event`(3) は rebuild 後も残存。
3. **deletion**: source 削除 → rebuild → 対応 projection 行が消える（orphan 0）。append_event 行は残存。
4. **stale**: source 在 + content_hash 不一致 → `stale_status=stale`（行は残す。消さない）。
5. **deletion ⊥ stale（C-2）**: source 消失 = deletion（行消失）/ source 在 + 変化 = stale（行残置）の排他。
6. **secret guard（C-5）**: `assert_no_sensitive_payload(row, table)` が free-form 列の secret 様値（SECRET_PATTERN）/ raw transcript / PII を投影前に raise（PK・`*_id` 参照列は除外）。
7. **append_event 冪等**: 同一 logical_key で 2 回 append → 1 行（ON CONFLICT DO NOTHING/UPDATE）。
8. **upsert / stable_id**: `upsert_row` が `INSERT ... ON CONFLICT(logical_key) DO UPDATE`、`stable_id(prefix,value)` が決定的 PK（再投影で同一行同一 PK）。
9. **unresolved-join**: 外部キー（`plan_id` 等）が参照先 registry 不在 → `findings` に `unresolved-join`（SQLite FK 制約でなく projection 層の論理整合）。
10. **fail/warn 分離**: 壊れた frontmatter / 契約違反 artifact は fail と warn を分離報告（黙って投影を飛ばさない）。投影不能 artifact は `findings` へ。
11. **source 列挙の完全性（fork bug #3 予防）**: `sources` の file 集合は git(`git ls-files --cached --others --exclude-standard`) → 失敗時 filesystem-walk fallback で完全列挙。`.git` 不在で対象が縮小したら fail-close（silent narrow 禁止）。

## 2. 工程（test-first / verify-first）

1. **RED**: `cli/lib/v3/tests/test_projection_writer.py` に UT-C2-01..11（§1 DoD を 1:1）を先に書き fail 確認。
2. **GREEN**: `cli/lib/v3/projection/{writer,upsert,sources,secret_guard,projectors,__init__}.py` を実装し UT を green に。
3. 3 点レビュー（SE → QA 境界網羅 → PM 検証）。
4. `python3 -m pytest cli/lib/v3/tests/test_projection_writer.py -q` green + `python3 -m py_compile cli/lib/v3/projection/*.py`。

## 3. 実装方針

- **stdlib のみ**（`sqlite3` + `hashlib` + `re` + `subprocess`(git) + `os.walk`(fallback)）。
- `rebuild_projection(db, sources)` = `BEGIN IMMEDIATE → truncate_projection_tables(db)(kind==projection のみ DELETE) → for project_fn in PROJECTORS → COMMIT`（失敗時 ROLLBACK）。
- C1 の `TABLE_BY_NAME[name].kind` / `.logical_key` を参照（C1 と契約結合、再実装しない）。
- projector は本 unit では**最小セット**（`project_plans` / `project_artifacts` / `project_trace_edges` / `project_test_evidence` / `project_gate_runs`）で DbC を満たす範囲。残り ~30 projector は後続 unit（推測実装しない）。
- secret guard の SECRET_PATTERN は projection-writer.md の契約に従う（PK・`*_id` は除外）。

## 4. allowed_files（scope）

- `cli/lib/v3/projection/*.py`（新規）
- `cli/lib/v3/tests/test_projection_writer.py`（新規）
- **既存 V2 file / cli/lib/v3/schema/（C1）は触らない**（C1 は import するのみ。cutover まで V2 不変）。

## 5. escalation

- C1 が未 green の場合は着手しない（依存 unit）。設計矛盾は実装を止めて PM へ。
- secret/PII の取り扱いは C-5 契約厳守（DB に raw を保存しない、redacted summary のみ）。

## 6. 用語 delta

なし（[C2 設計正本](../../v3/engine/projection-writer.md) に準拠）。

## 7. FR delta

なし（REQ-PRJ-01..06 の実装。新規 FR 発明禁止）。
