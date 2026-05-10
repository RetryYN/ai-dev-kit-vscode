---
plan_id: PLAN-055
title: "PLAN-055（Category E + G: helix plan lint/reset + env-dependent failure 15 件、PLAN-051 carry）"
status: finalized
created: 2026-05-11
author: "PM (Opus)"
priority: medium
size: M
phases_affected: "cli/tests/test-helix-plan-lint.bats / test-helix-plan-reset.bats / test-helix-codex-auto-fallback.bats / test_helix_codex_audit.bats / test_helix_codex_footer.bats"
parent_plan: PLAN-051
acceptance:
  skip_label_normalized:
    verification_commands: { command: "grep -c 'PLAN-055A' cli/tests/test-helix-plan-lint.bats cli/tests/test-helix-plan-reset.bats cli/tests/test-helix-codex-auto-fallback.bats cli/tests/test_helix_codex_audit.bats cli/tests/test_helix_codex_footer.bats | awk -F: '{s+=$2} END {print s}", expected: "0 (W-1 step 2 完了後、PLAN-055A skip ラベル削除済)" }
  tests_pass_direct:
    verification_commands: { command: "bats cli/tests/test-helix-plan-lint.bats cli/tests/test-helix-plan-reset.bats cli/tests/test-helix-codex-auto-fallback.bats cli/tests/test_helix_codex_audit.bats cli/tests/test_helix_codex_footer.bats", expected: "exit 0 / 全 PASS (直接 bats 実行)" }
  tests_pass_via_helix_test:
    verification_commands: { command: "cli/helix test --no-pytest --bats-only", expected: "exit 0 / bats: 全 PASS (Category G env-dependent failure mode 再現条件で検証)" }
finalized: 2026-05-10
---

# PLAN-055: Category E + G - helix plan lint/reset + env-dependent failure

## §1 背景

PLAN-051 で skip annotation した残 48 件を 3 PLAN (055/056/057) に分割。
本 PLAN-055 は Category E (helix plan 系 6 件) + Category G (env-dependent 9 件) の 15 件を扱う。

env-dependent failure (Category G) は cli/helix-test の env override (HELIX_PROJECT_ROOT / CODEX_BIN mock) で発生し、
直接 bats では PASS する。 fix は cli/helix-test の env override 修正または test 側の env 復元の 2 系統。

## §2 解消対象 (15 件)

### Category E: helix plan (6 件)
- cli/tests/test-helix-plan-lint.bats: 4 件 (line 144/171/185/238)
- cli/tests/test-helix-plan-reset.bats: 2 件 (line 40/92)

### Category G: env-dependent (9 件)
- cli/tests/test-helix-codex-auto-fallback.bats: 7 件 (line 121/144/166/181/197/233/249)
- cli/tests/test_helix_codex_audit.bats: 1 件 (line 81)
- cli/tests/test_helix_codex_footer.bats: 1 件 (line 160)

## §3 修正方針

### Category E
- helix plan lint --duplicates / reset finalized 系の挙動が現行 cli/helix-plan と乖離
- 主に assertion 側 (現行出力に揃える) で吸収、必要なら test fixture 修正

### Category G
- cli/helix-test の env override (`export HELIX_PROJECT_ROOT=$TMP_ROOT/...` 等) で発生
- 各 test setup で env を意図的に復元するか、cli/helix-test 側で test に env override を伝播しない
- bats-lite の env 隔離仕様調査 → 明文化

## §4 Sprint 構成

| Sprint | 内容 | 委譲先 | 想定 commit |
|---|---|---|---|
| W-0 | draft + TL Round 1 + finalize (size=M) | PM 直接 | 本 commit |
| W-1 step 1 | 対象 15 line のみの skip ラベルを `PLAN-055` → `PLAN-055A` に置換 (line range 指定 sed)。同一ファイル内の他 line (PLAN-056/057 対象) は触らない | Codex SE (編集・テスト・報告) | (checkpoint、commit は Opus) |
| W-1 step 2 | Category E + G (15 件) skip 削除 + assertion 修正 + cli/helix-test 経由でも PASS 確認 | Codex SE (編集・テスト・報告) | (checkpoint、commit は Opus) |
| W-1 commit | Codex SE 報告内容を Opus が検証して commit | Opus (commit 判断) | feat(plan-055): W-1 |
| W-final | 統合検証 + retro + status completed + push | Opus | feat(plan-055): W-final |

## §5 Out of Scope

- PLAN-056 (Category F の codex 系 misc 18 件)
- PLAN-057 (Category F の non-codex misc 15 件)
- bats-lite VAR=value 形式本格 fix (PLAN-052 carry → 別 PLAN へ route)

## §6 リスク

- env-dependent fix が cli/helix-test 構造変更を伴う場合、scope 拡大 → W-1.2 を 055.W-1.2.A / W-1.2.B に再分割
- PLAN-055A label は本 PLAN 専用、W-1.1 で他 line を誤置換しないよう sed -i 範囲を line range で限定
