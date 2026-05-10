---
plan_id: PLAN-056
title: "PLAN-056（Category F-codex: codex 系 misc tests 18 件、PLAN-051 carry）"
status: finalized
created: 2026-05-11
author: "PM (Opus)"
priority: medium
size: M
phases_affected: "cli/tests/test-helix-codex.bats / test_codex_role_intent.bats / test_helix_codex_allowed_files.bats / test_helix_codex_footer.bats / test_helix_codex_audit.bats / test-helix-codex-write-audit.bats / test-helix-bats-cleanup.bats / test-helix-routing.bats"
parent_plan: PLAN-051
acceptance:
  skip_label_normalized:
    verification_commands: { command: "grep -c 'PLAN-056B' cli/tests/test-helix-codex.bats cli/tests/test_codex_role_intent.bats cli/tests/test_helix_codex_allowed_files.bats cli/tests/test_helix_codex_footer.bats cli/tests/test_helix_codex_audit.bats cli/tests/test-helix-codex-write-audit.bats cli/tests/test-helix-bats-cleanup.bats cli/tests/test-helix-routing.bats | awk -F: '{s+=$2} END {print s}", expected: "0 (W-1 step 2 完了後、PLAN-056B skip ラベル削除済)" }
  no_other_plan_skip_corrupted:
    verification_commands: { command: "grep -c 'PLAN-055\\|PLAN-057' cli/tests/test_helix_codex_footer.bats cli/tests/test_helix_codex_audit.bats | awk -F: '{s+=$2} END {print s}", expected: "PLAN-055 残 2 件 (env-dep) は維持、PLAN-057 ラベルは存在しない" }
  tests_pass_direct:
    verification_commands: { command: "bats cli/tests/test-helix-codex.bats cli/tests/test_codex_role_intent.bats cli/tests/test_helix_codex_allowed_files.bats cli/tests/test_helix_codex_footer.bats cli/tests/test_helix_codex_audit.bats cli/tests/test-helix-codex-write-audit.bats cli/tests/test-helix-bats-cleanup.bats cli/tests/test-helix-routing.bats", expected: "exit 0 / 全 PASS" }
  tests_pass_via_helix_test:
    verification_commands: { command: "cli/helix test --no-pytest --bats-only", expected: "exit 0 / bats: 全 PASS (regression check)" }
finalized: 2026-05-10
---

# PLAN-056: Category F-codex - codex 系 misc tests 18 件

## §1 背景

PLAN-051 で skip annotation した Category F の codex 系 18 件を実 fix。
**PLAN-055 完了後に着手**: 一部ファイル (test_helix_codex_audit.bats / test_helix_codex_footer.bats) は PLAN-055 と共有するため、line ownership 衝突回避のため逐次実行。

## §2 解消対象 (18 件)

| ファイル | 件数 | line |
|---|---|---|
| test-helix-codex.bats | 2 | 200, 217 |
| test_codex_role_intent.bats | 1 | 22 |
| test_helix_codex_allowed_files.bats | 6 | 133, 146, 159, 171, 185, 199 |
| test_helix_codex_footer.bats | 2 | 138, 175 (env-dep 1 件 line 160 は PLAN-055) |
| test_helix_codex_audit.bats | 2 | 43, 62 (env-dep 1 件 line 81 は PLAN-055) |
| test-helix-codex-write-audit.bats | 1 | 47 |
| test-helix-bats-cleanup.bats | 1 | 16 |
| test-helix-routing.bats | 3 | 78, 116, 132 |

## §3 修正方針

- 主に assertion 側 (現行 cli/helix-codex 出力構造に揃える) で吸収
- routing / role / footer の各テストは PLAN-022〜050 で進化した仕様に追従
- 実装側変更が必須と判断したら escalate

## §4 Sprint 構成

| Sprint | 内容 | 委譲先 | 想定 commit |
|---|---|---|---|
| W-0 | draft + TL Round 1 + finalize (size=M) | PM 直接 | 本 commit |
| W-1 step 1 | 対象 18 line のみの skip ラベルを `PLAN-055` → `PLAN-056B` に置換 (line range 指定 sed)。同一ファイル内の他 line (PLAN-055/057 対象) は触らない | Codex SE (編集・テスト・報告) | (checkpoint、commit は Opus) |
| W-1 step 2 | 18 件 skip 削除 + assertion 修正 | Codex SE (編集・テスト・報告) | (checkpoint、commit は Opus) |
| W-1 commit | Codex SE 報告内容を Opus が検証して commit | Opus (commit 判断) | feat(plan-056): W-1 |
| W-final | 統合検証 + retro + status completed + push | Opus | feat(plan-056): W-final |

## §5 Out of Scope

- PLAN-055 (helix plan + env-dep)
- PLAN-057 (non-codex misc)
- 実装側 (cli/helix-codex / cli/lib/*) の挙動変更
