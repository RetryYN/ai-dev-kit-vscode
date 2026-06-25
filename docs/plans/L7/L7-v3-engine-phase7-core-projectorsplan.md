---
plan_id: L7-v3-engine-phase7-core-projectorsplan
title: "L7-v3-engine-phase7-core-projectorsplan: Phase 7.1 — robust frontmatter (pyyaml) + core projectors が実 V2 source を投影"
kind: impl
layer: L7
drive: be
status: draft
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: "docs/v3/engine/projection-writer.md"
dependencies:
  requires:
    - L7-v3-engine-c2-projection-writerplan
  blocks: []
pairs_test_design:
  - cli/lib/v3/tests/test_core_projectors.py
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE — pyyaml frontmatter + project_plans/artifacts/trace_edges が実 repo を投影 (verify-first)"
  - role: qa
    slot_label: "QA — 実 PLAN/doc 投影行数 / parse_error 健全性 / trace_edges 双方向の境界判定"
generates:
  - artifact_path: cli/lib/v3/projection/sources.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/projection/projectors.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/tests/test_core_projectors.py
    artifact_type: test
created: 2026-06-26
revised: 2026-06-26
owner: SE
related_docs:
  - docs/v3/engine/projection-writer.md
  - docs/v3/engine/doc-workflow-rules.md
---

# L7-v3-engine-phase7-core-projectorsplan

## 0. 目的

Phase 7.1 = V3 engine が **実 V2 source（PLAN / 設計 doc）を正しく DB へ投影**できるようにする。現状 C2 の frontmatter parser は naive 行解析で、実 PLAN の入れ子 YAML list（`pairs_test_design:\n  - ...`）で `parse_error` → `frontmatter={}` → plan_registry 0 行。これを **pyyaml `safe_load`** に置換し、core projector（plans / artifacts / trace_edges）が実 repo を投影するまで完成する。

## 0.5 unit 位置づけ（[C6 §4.5](../../v3/engine/doc-workflow-rules.md)）

- **unit_id**: U-ENG-P7-CORE / **parent_l4_component**: C2 projection-writer（projector 群の完成）
- **依存**: C1（schema）+ C2（rebuild 枠組み・upsert・secret guard）。本 unit は C2 の `sources.py`/`projectors.py` を完成させる（5 projector minimal → core 投影を実 source 対応に）。
- **scope**: PLAN + 設計 doc → plan_registry / artifact_registry / trace_edges。code/test/FR/screen projector は後続 unit（Phase 7.2+）。

## 1. 受入条件（DoD）

1. **frontmatter parser**: `---...---` ブロックを `yaml.safe_load` で dict 化（入れ子 list/dict 対応）。**genuinely 不正な YAML のみ** `parse_error` を立てる（正常 PLAN で parse_error=0）。pyyaml 使用（環境に 6.0.1 在、V2 `plan_validator` と同方式）。
2. **project_plans**: 実 `docs/plans/**/*.md` の frontmatter → `plan_registry`（plan_id/kind/layer/drive/status/parent/sub_doc/updated_at）。docs/plans 配下の全 PLAN が投影される（行数 > 0、parse できる PLAN 数と一致）。
3. **project_artifacts**: 実 `docs/v3/**/*.md`（設計 doc）+ PLAN を `artifact_registry`（artifact_id/path/artifact_type/status/pair_artifact）へ。
4. **project_trace_edges**: frontmatter の `pair_artifact` / `generates` / `dependencies.requires` から `trace_edges`（from_artifact/to_artifact/edge_kind）。
5. **回帰非破壊**: C2 の既存 14 UT（idempotent/truncate/secret/append/source-completeness）は引き続き green。
6. **idempotent 維持**: 実 repo で `rebuild_projection` 2 回 → bit-identical（pyyaml 化後も決定的）。

## 2. 工程（test-first）

1. **RED**: `cli/lib/v3/tests/test_core_projectors.py` に UT（fixture repo + 実 docs/plans/L7 を使った投影行数・parse_error=0・trace_edges 双方向・2x bit-identical）を先に書き fail 確認。
2. **GREEN**: `sources.py`（pyyaml frontmatter）+ `projectors.py`（plans/artifacts/trace_edges 完成）実装。
3. 検証: `python3 -m pytest cli/lib/v3/tests/ -q`（既存 + 新規 全 green）+ 実 repo rebuild で plan_registry/artifact_registry/trace_edges 行数を確認。

## 3. 実装方針

- **frontmatter**: `yaml.safe_load`。`import yaml`（pyyaml）。先頭 `---` / 終端 `---` の抽出は堅牢に（前後空白・CRLF 許容）。空 frontmatter は `{}`、不正 YAML のみ parse_error。
- C2 の rebuild 枠組み（`rebuild_projection`/`upsert_row`/`secret_guard`/kind 分類）は**変更しない**（projector の中身だけ完成）。
- projector は frontmatter dict から C1 schema の実 column へ map（C1 `TABLE_BY_NAME[...].columns` に存在する列のみ。無い列は書かない）。
- artifact_type は path/frontmatter から導出（PLAN=plan / docs/v3=design_doc 等、C1 ArtifactType enum 準拠）。
- 投影できない artifact は **fail/warn 分離で findings**（黙って飛ばさない＝C2 契約維持）。

## 4. allowed_files

- `cli/lib/v3/projection/sources.py` / `projectors.py`（C2 既存を完成）
- `cli/lib/v3/tests/test_core_projectors.py`（新規）
- **既存 V2 / cli/lib/v3/schema / cutover は触らない**。

## 5. escalation

- pyyaml 以外の新規依存を足さない（環境に在るもののみ）。schema に無い column を勝手に足さない（C1 が SSoT）。設計矛盾は止めて PM へ。

## 6. 用語 delta

なし。

## 7. FR delta

なし（REQ-PRJ projector 群の実 source 対応完成。新規 FR なし）。
