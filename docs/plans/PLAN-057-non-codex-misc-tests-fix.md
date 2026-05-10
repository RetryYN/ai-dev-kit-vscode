---
plan_id: PLAN-057
title: "PLAN-057（Category F-other: non-codex misc tests 15 件、PLAN-051 carry）"
status: finalized
created: 2026-05-11
author: "PM (Opus)"
priority: medium
size: M
phases_affected: "cli/tests/test-helix-reverse-*.bats / test-pretooluse-opus-repo-block.bats / test_helix_gate_g5_design_md.bats / test-helix-scrum.bats / test-helix-skill.bats / test-helix-review-internal-skip.bats / test-drift-check-dbschema.bats / test-helix-gate-readiness.bats / test-retro-auto-enqueue.bats"
parent_plan: PLAN-051
acceptance:
  skip_label_normalized:
    verification_commands: { command: "grep -c 'PLAN-057C\\|PLAN-055' cli/tests/test-helix-reverse-review.bats cli/tests/test-helix-reverse-design.bats cli/tests/test-pretooluse-opus-repo-block.bats cli/tests/test_helix_gate_g5_design_md.bats cli/tests/test-helix-scrum.bats cli/tests/test-helix-skill.bats cli/tests/test-helix-review-internal-skip.bats cli/tests/test-drift-check-dbschema.bats cli/tests/test-helix-gate-readiness.bats cli/tests/test-retro-auto-enqueue.bats | awk -F: '{s+=$2} END {print s}", expected: "0 (W-1 step 2 完了後、PLAN-057C も PLAN-055 残 skip もすべて削除済)" }
  tests_pass_direct:
    verification_commands: { command: "bats cli/tests/test-helix-reverse-review.bats cli/tests/test-helix-reverse-design.bats cli/tests/test-pretooluse-opus-repo-block.bats cli/tests/test_helix_gate_g5_design_md.bats cli/tests/test-helix-scrum.bats cli/tests/test-helix-skill.bats cli/tests/test-helix-review-internal-skip.bats cli/tests/test-drift-check-dbschema.bats cli/tests/test-helix-gate-readiness.bats cli/tests/test-retro-auto-enqueue.bats", expected: "exit 0 / 全 PASS" }
  tests_pass_via_helix_test:
    verification_commands: { command: "cli/helix test --no-pytest --bats-only", expected: "exit 0 / bats: 全 PASS" }
finalized: 2026-05-10
---

# PLAN-057: Category F-other - non-codex misc tests 15 件

## §1 背景

PLAN-051 で skip annotation した Category F の non-codex 15 件を実 fix。
**PLAN-056 完了後に着手**: 全ファイルが PLAN-055/056 と独立 (重複なし) だが、grep ベース acceptance の検証ノイズを避けるため逐次実行。

## §2 解消対象 (15 件)

| ファイル | 件数 | line |
|---|---|---|
| test-helix-reverse-review.bats | 1 | 79 |
| test-helix-reverse-design.bats | 3 | 25, 44, 79 |
| test-pretooluse-opus-repo-block.bats | 2 | 31, 38 |
| test_helix_gate_g5_design_md.bats | 2 | 185, 199 |
| test-helix-scrum.bats | 1 | 28 |
| test-helix-skill.bats | 1 | 82 |
| test-helix-review-internal-skip.bats | 1 | 29 |
| test-drift-check-dbschema.bats | 1 | 115 |
| test-helix-gate-readiness.bats | 1 | 99 |
| test-retro-auto-enqueue.bats | 2 | 33, 46 |

## §3 修正方針

- 各分野 (reverse / pretooluse hook / gate G5 / scrum / skill / drift / readiness / retro) の assertion を現行実装出力に揃える
- pretooluse hook 系は Opus 直接 Edit block で挙動変化、test 側で fixture 整備
- 実装側変更が必須と判断したら escalate

## §4 Sprint 構成

| Sprint | 内容 | 委譲先 | 想定 commit |
|---|---|---|---|
| W-0 | draft + TL Round 1 + finalize (size=M) | PM 直接 | 本 commit |
| W-1 step 1 | 対象 15 line の skip ラベルを `PLAN-055` → `PLAN-057C` に置換 (line range 指定 sed) | Codex SE (編集・テスト・報告) | (checkpoint、commit は Opus) |
| W-1 step 2 | 15 件 skip 削除 + assertion 修正 | Codex SE (編集・テスト・報告) | (checkpoint、commit は Opus) |
| W-1 commit | Codex SE 報告内容を Opus が検証して commit | Opus (commit 判断) | feat(plan-057): W-1 |
| W-final | 統合検証 + retro + status completed + push | Opus | feat(plan-057): W-final |

## §5 Out of Scope

- PLAN-055 (helix plan + env-dep)
- PLAN-056 (codex 系 misc)
- 実装側 (cli/helix-* / cli/lib/*) の挙動変更
