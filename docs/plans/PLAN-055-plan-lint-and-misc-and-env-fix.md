---
plan_id: PLAN-055
title: 'PLAN-055（Category E + F + G: helix plan lint/reset + misc 33 件 + env-dependent 9 件、PLAN-051 carry）'
status: draft
created: 2026-05-11
author: 'PM (Opus)'
priority: medium
size: L
phases_affected: 多数 (test-helix-plan-lint / 各 misc fixture / cli/helix-test の env override)
parent_plan: PLAN-051
acceptance:
  skip_removed:
    verification_commands:
      command: "grep -rc 'PLAN-055' cli/tests/ | awk -F: '{s+=$2} END {print s}'"
      expected: "0 (skip annotation 削除済、48 件すべて実 fix)"
  tests_pass:
    verification_commands:
      command: "cli/helix test"
      expected: "exit 0 / 全 PASS"
---

# PLAN-055: Category E + F + G - 残 48 件一斉対処

## §1 背景

PLAN-051 で skip annotation した残 48 件を実 fix。

## §2 解消対象 (48 件 = E 6 + F 33 + G 9)

### Category E: helix plan lint/reset (6 件)
- helix plan lint --duplicates / reset finalized 系

### Category F: misc 33 件
- D-DB / --list bats / impl_task_no_diff_warns / claude shim (2)
- G6 retro headings Japanese / helix reverse design (3) / handover dump
- codex missing error / top-level help / docs / framework / scrum backlog
- PLAN-024 W-2d / block_repo edits (2) / 記入済み retro / --dry-run debt-register
- docs role / plan baseline (5) / helix-codex (4) / G5 PASS/FAIL (2)

### Category G: env-dependent (9 件、cli/helix-test の env override が原因)
- usage_limit + AUTO_FALLBACK 系 (5)
- HELIX_DISABLE_SPARK 系 (2)
- helix-codex audit mkdir fails (1)
- marker 付き summary block (1)

## §3 Sprint 構成 (再分割の可能性あり)

48 件が 1 PLAN には大きすぎる場合、PLAN-055a/b/c に分割を検討:
- PLAN-055a: Category E (helix plan lint/reset) + Category G (env-dependent、cli/helix-test 修正)
- PLAN-055b: Category F の前半 (codex / handover / docs 等)
- PLAN-055c: Category F の後半 (plan baseline / helix-codex / G5)

W-0 draft 段階で再分割判定。

## §4 Out of Scope

- DS-120 Reverse 反映 (PLAN-049 OOS)
- helix-reverse worked-example スキャフォールド
- adversarial-review Reverse 専用 worked checklist
