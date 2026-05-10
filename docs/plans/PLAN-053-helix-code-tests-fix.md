---
plan_id: PLAN-053
title: 'PLAN-053（Category C: helix code 系 tests 修正、PLAN-051 carry）'
status: draft
created: 2026-05-11
author: 'PM (Opus)'
priority: medium
size: M
phases_affected: cli/tests/test-helix-code*.bats
parent_plan: PLAN-051
acceptance:
  skip_removed:
    verification_commands:
      command: "grep -rc 'PLAN-053' cli/tests/ | awk -F: '{s+=$2} END {print s}'"
      expected: "0 (skip annotation 削除済)"
  tests_pass:
    verification_commands:
      command: "bats cli/tests/test-helix-code.bats cli/tests/test-helix-code-find.bats"
      expected: "exit 0 / 全 PASS"
---

# PLAN-053: Category C - helix code 系 tests 修正

## §1 背景

PLAN-051 で skip annotation した Category C の 8 件を実 fix。
PLAN-011/012/013 で実装した helix code 系の bats が pre-existing failures。

## §2 解消対象 (8 件)

- helix code find: cached result / falls back locally (2 件)
- helix code list: --json / --domain (2 件)
- helix code stats --uncovered: --seed-candidate / --scope cli-lib --fail-under 50 / TSV (3 件)
- helix code build: v15 schema (1 件)

## §3 Sprint 構成

- W-0 draft + TL + finalize
- W-1 fixture / assertion / DB schema 整合確認、データ drift 修正
- W-final 統合検証 + retro + push
