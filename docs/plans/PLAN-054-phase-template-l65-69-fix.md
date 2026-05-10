---
plan_id: PLAN-054
title: 'PLAN-054（Category D: phase template L6.5-L6.9 + G6.5/.7/.9 修正、PLAN-051 carry）'
status: draft
created: 2026-05-11
author: 'PM (Opus)'
priority: medium
size: S
phases_affected: phase template / cli/tests/test-helix-gate-pre-release.bats
parent_plan: PLAN-051
acceptance:
  skip_removed:
    verification_commands:
      command: "grep -rc 'PLAN-054' cli/tests/ | awk -F: '{s+=$2} END {print s}'"
      expected: "0 (skip annotation 削除済)"
  tests_pass:
    verification_commands:
      command: "bats cli/tests/test-helix-gate-pre-release.bats"
      expected: "exit 0 / 全 PASS"
---

# PLAN-054: Category D - phase template L6.5-L6.9 + G6.5/.7/.9 修正

## §1 背景

PLAN-051 で skip annotation した Category D の 7 件を実 fix。
PLAN-044 で導入した G6.5/6.7/6.9 関連 bats が phase template に L6.5-L6.9 を期待するが
実態と乖離。

## §2 解消対象 (7 件)

- "phase template has L6.5 / L6.7 / L6.9 defined"
- "phase template keeps L6.5/L6.7/L6.9 grep match" (3 件)
- "helix gate G6.5/G6.7/G6.9 dry-run smoke is accepted" (3 件)

## §3 Sprint 構成

- W-0 draft + TL + finalize
- W-1 phase template 修正 OR test 修正 (実装と test の整合判断)
- W-final 統合検証 + retro + push
