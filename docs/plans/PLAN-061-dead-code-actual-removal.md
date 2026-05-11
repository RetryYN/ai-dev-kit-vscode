---
plan_id: PLAN-061
title: "PLAN-061（dead code 実削除、PLAN-058 W-3 carry）"
status: completed
created: 2026-05-11
completed: 2026-05-11
author: "PM (Opus)"
priority: low
size: L
phases_affected: "cli/lib/* / cli/helix-* / 関連 test"
parent_plan: PLAN-058
acceptance:
  audit_review_complete:
    verification_commands: { command: "test -f docs/audit/dead-code-final-2026-05.md", expected: "exists (PLAN-058 audit doc を 1 件ずつ精査した最終リスト)" }
  removal_safe:
    verification_commands: { command: "cli/helix test", expected: "exit 0 / 削除後も全 PASS" }
finalized: 2026-05-10
---

# PLAN-061: dead code 実削除 (PLAN-058 W-3 carry)

## §1 背景

PLAN-058 W-3 で vulture 119 件の dead code candidate を `docs/audit/dead-code-candidates-2026-05.md` に抽出。
HELIX の動的 dispatch (auto-discover / dynamic import / CLI hook) で false positive 多発のため、
実削除には grep + dynamic call 確認 + テスト実行の精査が必要。

本 PLAN で 119 件を 1 件ずつ精査し、安全な dead code のみ削除。

## §2 解消対象 (vulture 60% 候補 119 件)

カテゴリ別精査:

### Category 1: 確定 false positive (削除しない、約 30-50 件)
- `_auto_discover_builders` 経由 dynamic import (16 件確定)
- SQLite cursor.row_factory (10+ 件)
- argparse subparser callback 経由関数

### Category 2: 要 grep 精査 (約 50-80 件)
- audit_a1 / audit_inventory / deferred_findings / code_catalog 系 関数
- learning_engine / global_store / matrix_advisor 系
- llm_guard / merge_settings 系 helper

### Category 3: 確定削除可能 (精査後判明、推定 5-20 件)
- 廃止 PLAN で deprecate 宣言済の helper
- 過去の PoC で残った関数

## §3 Sprint 構成

| Sprint | 内容 | 委譲先 |
|---|---|---|
| W-0 | draft + TL Round 1 + finalize (size=L) | PM |
| W-1 | 119 件精査 (1 件ずつ grep + dynamic call 確認)、最終削除候補リスト生成 | Codex docs |
| W-2 | docs/audit/dead-code-final-2026-05.md レビュー、Opus 最終判定 | PM + Opus |
| W-3 | 確定削除実装 (推定 5-20 件)、test PASS 確認 | Codex SE |
| W-final | 統合検証 + retro + push | Opus |

## §4 Out of Scope

- skills/* / docs/* (PLAN-059/060 で扱う)
- 動的 import / hook / CLI dispatch 経由関数の削除 (false positive risk)

## §5 リスク

- 削除後に dynamic call で発覚 → git revert で復元
- 大量削除で diff レビュー困難 → ファイル単位 commit + 各 commit で test PASS
