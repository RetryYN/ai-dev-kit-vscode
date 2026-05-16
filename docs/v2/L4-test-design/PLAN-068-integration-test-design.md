---
plan_id: PLAN-068
doc_id: PLAN-068-integration-test-design
title: "PLAN-068 結合テスト設計 (V-model carry retrofit)"
status: maintained
artifact_role: "③ テスト設計 (V-model 4 artifact のうち)"
created: 2026-05-17
status_history:
  - 2026-05-17: 初期作成 (PLAN-075 Phase 4.3a retrofit)
owner: PM
related_docs:
  - docs/plans/PLAN-075-vmodel-design-test-mapping.md
  - docs/plans/PLAN-068-vmodel-strengthening-improvements.md
  - docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md
  - cli/lib/tests/test_helix_db.py
  - cli/lib/tests/test_helix_db_v22.py
  - cli/lib/tests/test_helix_db_v23.py
  - cli/lib/tests/test_helix_gate_subgate.py
  - cli/lib/tests/test_drive_decisions.py
  - cli/lib/tests/test_drive_decisions_atomic.py
  - cli/lib/tests/test_drive_decisions_idempotent.py
  - cli/lib/tests/test_migrate.py
phases: L4
gates: G4
---

> 本書は PLAN-068 の ③ テスト設計 artifact。① 設計 (PLAN-068 本文書) と ④ テストコード
> (`cli/lib/tests/test_helix_db*.py` / `test_drive_decisions*.py` / `test_helix_gate_subgate.py` / `test_migrate.py`)
> を双方向 trace で繋ぐ。

# PLAN-068 結合テスト設計 (③ D-TEST-DESIGN-INT)

## §1 概要

### 1.1 目的

PLAN-068 の carry 対象である v22/v23 migration、drive switch、void/correction、
functional_freeze、pair_status を結合テストとして固定する。

### 1.2 V-model 4 artifact trace

- **対象設計 (①)**: `docs/plans/PLAN-068-vmodel-strengthening-improvements.md` §2〜§7
- **対応実装 (②)**: `cli/lib/helix_db.py` / `cli/lib/helix-gate`
- **本文書 (③)**: `docs/v2/L4-test-design/PLAN-068-integration-test-design.md`
- **対応テストコード (④)**: `cli/lib/tests/test_helix_db*.py` / `test_drive_decisions*.py` / `test_helix_gate_subgate.py` / `test_migrate.py`

### 1.3 case 命名

- `I-068-001`〜`I-068-010`: migration / schema
- `I-068-011`〜`I-068-020`: functional_freeze / correction / switch
- `I-068-021`〜`I-068-027`: drive decision / atomicity / idempotency
- `I-068-028`〜`I-068-031`: PLAN-068 固有の switch rollback / void rollback

### 1.4 fixture 方針

- migration は `helix_db.init_db()` / `helix_db.migrate()`
- correction / rollback は trigger または monkeypatch で failure 注入
- functional_freeze は `query_functional_freeze_status()` と CLI subgate
- drive decision は row count / payload / transaction で確認

## §2 既存 test code mapping

| case ID | test 関数 | file | 要点 |
|---|---|---|---|
| I-068-001 | `test_migrate_v21_to_current_adds_drive_switch_and_correction_columns` | `cli/lib/tests/test_helix_db_v22.py` | v21→current の列整合 |
| I-068-002 | `test_migrate_v21_to_v22_is_idempotent` | `cli/lib/tests/test_helix_db_v22.py` | v22 冪等 |
| I-068-003 | `test_v22_to_v23_migrate_succeeds` | `cli/lib/tests/test_helix_db_v23.py` | v23 拡張 |
| I-068-004 | `test_v23_to_v23_migrate_is_idempotent` | `cli/lib/tests/test_helix_db_v23.py` | v23 冪等 |
| I-068-005 | `test_void_entry_with_correction_voids_old_and_appends_new` | `cli/lib/tests/test_helix_db_v23.py` | void/correction |
| I-068-006 | `test_void_entry_with_correction_rolls_back_on_invalid_payload` | `cli/lib/tests/test_helix_db_v23.py` | invalid payload rollback |
| I-068-007 | `test_list_active_entries_excludes_voided_rows` | `cli/lib/tests/test_helix_db_v23.py` | active row のみ抽出 |
| I-068-008 | `test_void_artifact_link_with_correction_voids_old_and_appends_new` | `cli/lib/tests/test_helix_db_v23.py` | link 版 void/correction |
| I-068-009 | `test_migrate_idempotent_individual_versions` | `cli/lib/tests/test_migrate.py` | individual migration 冪等 |
| I-068-010 | `test_v21_to_v22_adds_drive_switch_columns` | `cli/lib/tests/test_migrate.py` | switch columns 追加 |
| I-068-011 | `test_subgate_multi_drive_query_be_fe_db_sequential` | `cli/lib/tests/test_helix_gate_subgate.py` | multi-drive query |
| I-068-012 | `test_subgate_drive_switch_via_v22_api` | `cli/lib/tests/test_helix_gate_subgate.py` | switch + freeze 整合 |
| I-068-013 | `test_subgate_resolves_drive_from_phase_yaml` | `cli/lib/tests/test_helix_gate_subgate.py` | phase.yaml 解決 |
| I-068-014 | `test_subgate_resolves_drive_from_plan_frontmatter` | `cli/lib/tests/test_helix_gate_subgate.py` | frontmatter 解決 |
| I-068-015 | `test_query_functional_freeze_status_returns_missing_when_empty` | `cli/lib/tests/test_helix_gate_subgate.py` | missing verdict |
| I-068-016 | `test_query_functional_freeze_status_returns_passed_when_all_paired` | `cli/lib/tests/test_helix_gate_subgate.py` | passed verdict |
| I-068-017 | `test_query_functional_freeze_status_returns_failed_when_pending` | `cli/lib/tests/test_helix_gate_subgate.py` | pending verdict |
| I-068-018 | `test_query_functional_freeze_status_returns_failed_when_failed` | `cli/lib/tests/test_helix_gate_subgate.py` | failed verdict |
| I-068-019 | `test_insert_drive_decision_records_row` | `cli/lib/tests/test_drive_decisions.py` | decision insert |
| I-068-020 | `test_insert_drive_decision_accepts_waived` | `cli/lib/tests/test_drive_decisions.py` | waived accept |
| I-068-021 | `test_insert_drive_decision_rejects_invalid_decision` | `cli/lib/tests/test_drive_decisions.py` | invalid reject |
| I-068-022 | `test_insert_drive_decision_rejects_cross_plan_target` | `cli/lib/tests/test_drive_decisions.py` | cross-plan reject |
| I-068-023 | `test_insert_drive_decision_rolls_back_when_insert_aborts` | `cli/lib/tests/test_drive_decisions_atomic.py` | abort rollback |
| I-068-024 | `test_same_entry_id_raises_and_no_row_inserted` | `cli/lib/tests/test_drive_decisions_atomic.py` | same entry reject |
| I-068-025 | `test_nonexistent_source_entry_raises_and_rollback` | `cli/lib/tests/test_drive_decisions_atomic.py` | missing source rollback |
| I-068-026 | `test_insert_drive_decision_is_not_idempotent_without_caller_guard` | `cli/lib/tests/test_drive_decisions_idempotent.py` | non-idempotent 可視化 |
| I-068-027 | `test_caller_can_implement_idempotency_via_select_then_insert` | `cli/lib/tests/test_drive_decisions_idempotent.py` | caller guard 冪等 |
| I-068-028 | `test_switch_drive_for_sprint_appends_new_entry` | `cli/lib/tests/test_helix_db.py` | switch append |
| I-068-029 | `test_switch_drive_for_sprint_rejects_duplicate_target_drive` | `cli/lib/tests/test_helix_db.py` | duplicate target reject |
| I-068-030 | `test_switch_drive_for_sprint_atomic_rollback_on_failure` | `cli/lib/tests/test_helix_db.py` | switch rollback |
| I-068-031 | `test_void_entry_with_correction_atomic_rollback_on_failure` | `cli/lib/tests/test_helix_db.py` | correction rollback |

## §3 case 詳細

### §3.1 migration

#### I-068-001
- v21 legacy DB を migrate し、switch / correction 列が揃うことを確認する。

#### I-068-002
- `init_db()` を再実行して v22 列が重複しないことを確認する。

#### I-068-003
- v22 DB を v23 へ進め、entry / link の correction 列が追加されることを確認する。

#### I-068-004
- v23 migration の再実行で重複適用が起きないことを確認する。

#### I-068-009
- 個別 migration の前後で column signature が一致することを確認する。

#### I-068-010
- v21 状態から drive switch 列が追加されることを確認する。

### §3.2 correction / active

#### I-068-005
- voided 旧 row と supersedes 参照付き新 row が作られることを確認する。

#### I-068-006
- 不正 payload で失敗しても DB 状態が変わらないことを確認する。

#### I-068-007
- `list_active_entries()` が voided row を返さないことを確認する。

#### I-068-008
- artifact link も entry と同様に correction できることを確認する。

### §3.3 functional_freeze / drive 解決

#### I-068-011
- `be` / `fe` / `db` を順に評価して verdict が独立することを確認する。

#### I-068-012
- v22 API 経由の switch で old row preserved / new row pending になることを確認する。

#### I-068-013
- phase.yaml から drive が解決されることを確認する。

#### I-068-014
- plan frontmatter から drive が解決されることを確認する。

#### I-068-015
- row なしは `missing` になることを確認する。

#### I-068-016
- all paired は `passed` になることを確認する。

#### I-068-017
- pending 混在は `failed` になることを確認する。

#### I-068-018
- failed row を含む場合に `failed` になることを確認する。

### §3.4 drive decision / atomicity

#### I-068-019
- decision row が 1 件 insert されることを確認する。

#### I-068-020
- waived decision が受理されることを確認する。

#### I-068-021
- invalid decision を reject することを確認する。

#### I-068-022
- cross-plan target を reject することを確認する。

#### I-068-023
- insert abort 時に transaction 全体が rollback されることを確認する。

#### I-068-024
- same entry 指定で insert されないことを確認する。

#### I-068-025
- nonexistent source で rollback されることを確認する。

#### I-068-026
- caller guard なしでは non-idempotent であることを確認する。

#### I-068-027
- caller 側 guard で 1 回に抑えられることを確認する。

### §3.5 PLAN-068 固有の switch / rollback

#### I-068-028
- switch で old row が残り new row が append されることを確認する。

#### I-068-029
- duplicate target drive を reject することを確認する。

#### I-068-030
- switch insert 失敗時に rollback されることを確認する。

#### I-068-031
- correction insert 失敗時に rollback されることを確認する。

## §4 共通 fixture / 環境前提

- SQLite は temp file ベースで初期化する。
- `helix_db.get_connection()` で row_factory / foreign_keys を揃える。
- migration 系は `schema_version` を直接確認する。
- CLI subgate 系は project root / `.helix/phase.yaml` / plan frontmatter を整える。
- rollback 系は trigger または monkeypatch で failure を注入する。

## §5 case 数集計

- migration 整合: 6 case
- correction / active: 4 case
- functional_freeze / drive 解決: 8 case
- drive decision / atomicity: 9 case
- PLAN-068 固有 switch / rollback: 4 case
- **合計: 31 case**

## §6 DoD

- 本書の 31 case が G4 で全 PASS
- `PLAN-068-vmodel-strengthening-improvements.md` から本文書への reference が存在
- `cli/lib/tests/*` の対象 test 関数が本文書の case ID を参照できる
- 未完了項目が本文書に残っていない
