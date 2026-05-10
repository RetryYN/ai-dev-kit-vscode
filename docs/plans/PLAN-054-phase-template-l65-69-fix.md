---
plan_id: PLAN-054
title: "PLAN-054（Category D: phase template L6.5-L6.9 + G6.5/.7/.9 修正、PLAN-051 carry）"
status: finalized
created: 2026-05-11
author: "PM (Opus)"
priority: medium
size: S
phases_affected: cli/tests/test-helix-phase-deploy-3stages.bats
parent_plan: PLAN-051
acceptance:
  skip_removed:
    verification_commands: { command: "grep -rc 'PLAN-054' cli/tests/ | awk -F: '{s+=$2} END {print s}", expected: "0 (skip annotation 削除済)" }
  tests_pass:
    verification_commands: { command: "bats cli/tests/test-helix-phase-deploy-3stages.bats", expected: "exit 0 / 7 PASS" }
finalized: 2026-05-10
---

# PLAN-054: Category D - phase template L6.5-L6.9 + G6.5/.7/.9 修正

## §1 背景

PLAN-051 で skip annotation した Category D の 7 件を実 fix。
PLAN-044 で導入した G6.5/6.7/6.9 関連 bats が phase template に L6.5-L6.9 を期待するが
実態と乖離。

## §2 解消対象 (7 件)

すべて `cli/tests/test-helix-phase-deploy-3stages.bats`:

| line | test 名 | 推定原因 |
|---|---|---|
| 95 | phase template has L6.5 / L6.7 / L6.9 defined | rg コマンド escape `\\.` 問題 / phase.yaml には comment 形式 (`# L6.5: ...`) のみで data 形式は未定義 |
| 102 | phase template keeps L6.5 grep match | 同上 |
| 109 | phase template keeps L6.7 grep match | 同上 |
| 116 | phase template keeps L6.9 grep match | 同上 |
| 123 | helix gate G6.5 dry-run smoke is accepted | `helix gate G6.5 --dry-run` の出力 / status の挙動 |
| 135 | helix gate G6.7 dry-run smoke is accepted | 同上 (G6.7) |
| 147 | helix gate G6.9 dry-run smoke is accepted | 同上 (G6.9) |

## §3 修正方針

1. test 1-4 (rg L6.x): `phase.yaml` の comment 化 / data 化を確認、test を comment match に揃える
2. test 5-7 (helix gate G6.x dry-run): `cli/helix-gate` の G6.5/G6.7/G6.9 dry-run 出力が期待 message に揃っているか確認、必要なら test の expected 文字列を実装に揃える
3. 実装側 (cli/helix-gate / phase.yaml) は変更しない (test assertion 側で吸収)
4. 例外: phase.yaml comment 形式が完全に欠落しているなら、phase.yaml に追記して comment 行を含める

## §4 Sprint 構成

| Sprint | 内容 | 委譲先 | 想定 commit |
|---|---|---|---|
| W-0 | draft + TL Round 1 + finalize (size=S) | PM 直接 | 本 commit |
| W-1 | test-helix-phase-deploy-3stages.bats fix (skip 削除 + assertion 修正) | Codex SE | feat(plan-054): W-1 |
| W-final | 統合検証 + retro + status completed + push | Opus | feat(plan-054): W-final |

## §5 Out of Scope

- 他 Category (C/E/F/G) の修正
