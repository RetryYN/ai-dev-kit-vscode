---
plan_id: PLAN-052
title: "PLAN-052（Category B: schema migration tests 修正、PLAN-051 carry）"
status: completed
completed: 2026-05-11
created: 2026-05-11
finalized: 2026-05-10
author: "PM (Opus)"
priority: medium
size: S
phases_affected: cli/tests/helix-budget-migration.bats
parent_plan: PLAN-051
acceptance:
  skip_removed:
    verification_commands: { command: "grep -c 'PLAN-052' cli/tests/helix-budget-migration.bats", expected: "0 (4 件すべて skip 削除済)" }
  schema_dynamic_or_relaxed:
    verification_commands: { command: "grep -cE 'version >= 7|CURRENT_SCHEMA_VERSION' cli/tests/helix-budget-migration.bats", expected: "≥ 1 (hardcode 7 を緩めた)" }
  tests_pass:
    verification_commands: { command: "bats cli/tests/helix-budget-migration.bats", expected: "exit 0 / 4 PASS (skip 含まず)" }
  tests_all_pass:
    verification_commands: { command: "cli/helix test", expected: "exit 0 / 0 failed" }
  branch_minimal_footprint:
    verification_commands: { command: "git branch --list 'improvements/plan-052*' | wc -l", expected: 0 }
---

# PLAN-052: Category B - schema migration tests 修正

## §1 背景

PLAN-051 で skip annotation した Category B の 4 件を実 fix。
`cli/tests/helix-budget-migration.bats` が schema v7 hardcode で current schema 19 と乖離。

## §2 解消対象 (4 件)

すべて `cli/tests/helix-budget-migration.bats`:
1. line 69: "v7 migration forward: version=7 と新カラム追加" — `assert version == 7` が問題
2. line 89: "skill_usage 新カラムに INSERT/SELECT 可能" — migrate 経由で v7 列利用
3. line 113: "budget_events テーブル CRUD 動作" — migrate 経由で v7 テーブル利用
4. line 139: "既存 skill_usage レコード数保持 + 新カラム互換" — migrate 経由で挙動確認

## §3 修正方針

- 4 件すべての `skip "PLAN-052: ..."` を削除
- test 1 の `assert version == 7` を `assert version >= 7` に緩める (migrate() は current=19 まで進む、v7 通過確認)
  - test 1 は v7 introduced columns ({"effort_estimated", ...}) の存在も検査済 → v7 通過の証跡は維持
- test 2, 3, 4 は assertion 修正不要 (migrate が正常完了すれば PASS する設計)

## §4 Sprint 構成

| Sprint | 内容 | 委譲先 | 想定 commit |
|---|---|---|---|
| W-0 | draft + TL Round 1 + finalize (size=S なので Round 1 のみ) | PM 直接 | 本 commit |
| W-1 | helix-budget-migration.bats fix (skip 削除 + assert 緩和) | PG | feat(plan-052): W-1 |
| W-final | 統合検証 + retro + status completed + push | Opus | feat(plan-052): W-final |

## §5 Out of Scope

- PLAN-053/054/055 の各 Category 修正

## §6 リスク

- migrate() が将来 v20+ を導入した場合、`version >= 7` は引き続き OK (互換性確保)
- v7 introduced columns の名前が将来変わった場合、`required` set の更新が必要
  → 緩和: 本 PLAN scope 内では現行 required set を維持
