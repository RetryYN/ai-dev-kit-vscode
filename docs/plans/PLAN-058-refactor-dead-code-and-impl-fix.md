---
plan_id: PLAN-058
title: "PLAN-058（リファクタリング A: dead code 検出/削除 + 実装 bug fix 4 件 + env-dependent 15 件 carry 解消）"
status: finalized
created: 2026-05-11
author: "PM (Opus)"
priority: medium
size: M
phases_affected: "cli/lib/* / cli/helix-* / cli/tests/* (carry test 解消)"
parent_plan: PLAN-057
acceptance:
  dead_code_removed:
    verification_commands: { command: "helix code stats --uncovered --bucket private_helper --seed-promotable false --json | jq '.items | length", expected: "減少 (削除候補のうち合意済みは反映)" }
  impl_bugs_fixed:
    verification_commands: { command: "grep -rc 'PLAN-058[A-D]' cli/tests/ | awk -F: '{s+=$2} END {print s}", expected: "0 (PLAN-058A〜D 全 carry 解消)" }
  tests_pass_full:
    verification_commands: { command: "cli/helix test", expected: "exit 0 / 全 PASS (614 shell + 1055 pytest + 420 bats)" }
finalized: 2026-05-10
---

# PLAN-058: リファクタリング A - dead code + 実装 bug fix + env-dependent 解消

## §1 背景

3 軸のリファクタリング起票の 1 番目。CI integrity 完遂 + dead code 削減を統合スコープ。
ユーザー指示「使われていない実装をきれいに」「リファクタリング計画」に対応。

PLAN-051〜057 の累積 carry を本 PLAN で完遂:
- **PLAN-058A** (PLAN-057 carry 1 件): cli/helix-gate sprint.ui 真偽値比較不整合
- **PLAN-058B/C** (PLAN-057 carry 2 件): cli/helix-retro count_empty_items 不具合 (記入済み skip / --dry-run debt-register)
- **PLAN-058D** (本 commit 由来 15 件): env-dependent regression (cli/helix test pytest 後 bats env 影響)
- **dead code**: helix code stats --uncovered で抽出される coverage_eligible 0 行カバー or unreferenced helper

## §2 解消対象

### 軸 1: 実装 bug fix (carry 4 種類、計 18 件)

| ID | bug | test | line |
|---|---|---|---|
| PLAN-058A | cli/helix-gate sprint.ui 真偽値比較 | test_helix_gate_g5_design_md.bats | 184 |
| PLAN-058B | cli/helix-retro count_empty_items (記入済み skip) | test-retro-auto-enqueue.bats | 32 |
| PLAN-058C | cli/helix-retro count_empty_items (--dry-run) | test-retro-auto-enqueue.bats | 44 |
| PLAN-058D | cli/helix-test の pytest 後 bats env 隔離不全 | 6 ファイル 15 件 (test-helix-codex-auto-fallback / footer / write-audit / review-internal-skip / allowed_files / audit) | 各 line |

### 軸 2: dead code 検出 + 削除 (size の大半を占める)

- `helix code stats --uncovered --bucket private_helper --seed-promotable false --json` で seed_candidate=false の private_helper を抽出
- coverage=0% の coverage_eligible (公開 symbol だが呼び出し元 0) を抽出
- grep -r で 0 callsite を確認
- 削除候補リスト → Opus レビュー → 削除実装

## §3 修正方針

### Sprint W-0
- draft + TL Round 1 + finalize (size=M)

### Sprint W-1: 実装 bug fix (PLAN-058A/B/C)
- cli/helix-gate の sprint.ui 真偽値比較ロジック調査 + fix (推定 5-10 行)
- cli/helix-retro の count_empty_items 関数を実装に揃える (推定 10-20 行)
- 該当 test 3 件 skip 削除、bats PASS 確認

### Sprint W-2: env-dependent 解消 (PLAN-058D)
- cli/helix-test の bats invocation 前に env を明示クリア (HELIX_PROJECT_ROOT / CODEX_BIN 等の override をリセット)
- bats-lite の args.log 生成 location 固定化 (TMP_ROOT 内に閉じ込め)
- 該当 test 15 件 skip 削除、cli/helix test full で全 PASS 確認

### Sprint W-3: dead code 検出 + 削除
- helix code stats --uncovered で抽出
- 候補リスト作成 (Opus 直接、< 30 件想定)
- 削除実装 (Codex SE)

### Sprint W-final
- 統合検証 + retro + status completed + push

## §4 Out of Scope

- skill 解像度監査 (PLAN-059)
- AI knowledge 重複検証 (PLAN-060)
- 大規模アーキ変更 (CLI / lib の構造変更)

## §5 リスク

- 軸 2 の cli/helix-test env 隔離が大きな構造変更を伴う場合、W-2 を分割
- dead code 削除で副作用 (importer / dynamic call) → grep 漏れ確認必須
- 各軸の commit を分けて bisect 容易にする
