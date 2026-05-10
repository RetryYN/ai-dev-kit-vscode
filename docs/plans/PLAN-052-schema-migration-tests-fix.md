---
plan_id: PLAN-052
title: 'PLAN-052（Category B: schema migration tests 修正、PLAN-051 carry）'
status: draft
created: 2026-05-11
author: 'PM (Opus)'
priority: medium
size: S
phases_affected: cli/tests/helix-budget-migration.bats
parent_plan: PLAN-051
acceptance:
  skip_removed:
    verification_commands:
      command: "grep -c 'PLAN-052' cli/tests/helix-budget-migration.bats"
      expected: "0 (skip annotation 削除済)"
  schema_dynamic:
    verification_commands:
      command: "grep -cE 'CURRENT_SCHEMA_VERSION|helix_db.CURRENT_SCHEMA_VERSION' cli/tests/helix-budget-migration.bats"
      expected: "≥ 1 (動的参照化)"
  tests_pass:
    verification_commands:
      command: "bats cli/tests/helix-budget-migration.bats"
      expected: "exit 0 / 4 PASS"
---

# PLAN-052: Category B - schema migration tests 修正

## §1 背景

PLAN-051 で skip annotation した Category B の 4 件を実 fix。
`cli/tests/helix-budget-migration.bats` が schema v7 hardcode で current schema 19 と乖離。

## §2 解消対象 (4 件)

- "v7 migration forward: version=7 と新カラム追加"
- "skill_usage 新カラムに INSERT/SELECT 可能"
- "budget_events テーブル CRUD 動作"
- "既存 skill_usage レコード数保持 + 新カラム互換"

## §3 Sprint 構成

- W-0 draft + TL + finalize
- W-1 helix-budget-migration.bats を CURRENT_SCHEMA_VERSION 動的参照化 + skip 削除
- W-final 統合検証 + retro + push

## §4 Out of Scope

PLAN-053/054/055 carry (各 Category 専用 PLAN)。
