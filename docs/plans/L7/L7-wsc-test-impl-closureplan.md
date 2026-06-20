---
plan_id: L7-wsc-test-impl-closureplan
title: "L7-wsc-test-impl-closureplan: WSC-TEST-IMPL carry 12件のテスト実装 closure (UT-WSC unit/E2E)"
kind: impl
layer: L7
drive: be
status: completed
tl_review: approve  # tl-advisor impl review changes_required(P1×2/P2×2/P3×1) → round2 で 5 DbC 反証ケース追加 → re-review approve(P0-P3 なし)。本体不変・trace L6↔L7 1.0・carry 12→0
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: "docs/v2/L6-functional-design/whole-source-coverage-機能設計.md"
dependencies:
  requires: []
  blocks: []
pairs_test_design:
  - cli/tests/test-wsc-hook-posttooluse-design-doc-web-search-revert.bats
  - cli/tests/test-wsc-hook-posttooluse-helix-job-enqueue.bats
  - cli/tests/test-wsc-hook-posttooluse-plan-auto-register.bats
  - cli/tests/test-wsc-hook-posttooluse-skill-catalog-rebuild.bats
  - cli/tests/test-wsc-hook-precompact-state-snapshot.bats
  - cli/tests/test-wsc-hook-pretooluse-opus-repo-block.bats
  - cli/tests/test-wsc-hook-sessionstart-harness-summary.bats
  - cli/tests/test-wsc-hook-stop-recovery-update.bats
  - cli/tests/test-wsc-hook-userpromptsubmit-context-bundle.bats
  - cli/lib/tests/test_zizmor_ignore_lint_unit.py
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE — UT-WSC DbC 反証テストの verify-first 実装 (bats E2E + pytest)"
  - role: qa
    slot_label: "QA — fail-close/fail-open 方向と副作用 ensures のテスト網羅判定"
generates:
  - artifact_path: cli/tests/test-wsc-hook-*.bats
    artifact_type: test
  - artifact_path: cli/lib/tests/test_zizmor_ignore_lint_unit.py
    artifact_type: test
created: 2026-06-07
revised: 2026-06-07
owner: SE
related_docs:
  - docs/v2/L7-test-design/whole-source-coverage-単体テスト設計.md
  - docs/v2/L1-requirements/helix-workflows-verification-strategy.md
  - docs/plans/process/process-2026-06-07-whole-source-design-coverage-closure.md
---

# L7-wsc-test-impl-closureplan: WSC-TEST-IMPL carry 12件のテスト実装 closure

## 目的

直近 session の whole-source design coverage zero-omission Recovery は **設計 freeze（FN-WSC/UT-WSC 54）完遂・LANDED** 済み。残 carry `WSC-TEST-IMPL`（[L7 単体テスト設計 §carry](../../v2/L7-test-design/whole-source-coverage-単体テスト設計.md) / [verification-strategy §13](../../v2/L1-requirements/helix-workflows-verification-strategy.md)）= **設計済 UT のうち 12 件のテスト実装が weak**。本 PLAN はこの 12 件を L7 sprint として閉じる。

**設計は frozen・不変**（`design_change_class: pure_impl`、再凍結 pair 不要）。本 PLAN は対象 hook/lib の振る舞いを**変更せず**、テスト実体のみを追加する。

## 作業正本 / 合格基準（先に固定）

各 UT-WSC-NN は対の L6 FN-WSC-NN の DbC を反証するテストを持つこと（合格基準を先に置く = TDD 規律）。

- **hook（bash, bats）**: fail-close / fail-open の決定方向 + ensures（verdict / 副作用）を反証する。
- **lib（Python, pytest）**: 主関数の invariant（エラー時 / fail-close）+ ensures（戻り値 / 出力）を反証する。

## スコープ（12件、verify-first）

実体調査で **台帳（L7 doc）と既存テストにズレあり**。盲目的に 12 本新規作成せず、**各 UT につき既存テストが DbC を満たすか先に検証 → 不足分のみ実装 → 台帳を実体に是正**する。

| UT-WSC | 対象（READ-ONLY） | 既存テスト実体 | アクション |
|---|---|---|---|
| 02 | `.claude/hooks/posttooluse-design-doc-web-search-revert.sh` | 専用なし | **新規 bats** |
| 05 | `.claude/hooks/posttooluse-skill-catalog-rebuild.sh` | 専用なし | **新規 bats** |
| 15 | `.claude/hooks/stop-recovery-update.sh` | 専用なし | **新規 bats** |
| 218 | `cli/lib/zizmor_ignore_lint.py` | 専用なし | **新規 pytest** |
| 03 | `.claude/hooks/posttooluse-helix-job-enqueue.sh` | `test-layer-1-3-hooks.bats` に言及 | 言及が DbC を満たすか検証 → 不足なら専用 bats |
| 06 | `.claude/hooks/precompact-state-snapshot.sh` | `test-layer-1-3-hooks.bats` に言及 | 同上 |
| 10 | `.claude/hooks/pretooluse-codex-slot-check.sh` | `tests/harness-hooks.bats` に言及 | 同上 |
| 13 | `.claude/hooks/sessionstart-harness-summary.sh` | `tests/harness-hooks.bats` に言及 | 同上 |
| 17 | `.claude/hooks/userpromptsubmit-context-bundle.sh` | `test-layer-4-5-integration.bats` に言及 | 同上 |
| 04 | `.claude/hooks/posttooluse-plan-auto-register.sh` | **`test-posttooluse-plan-auto-register.bats` 専用実在** | DbC 充足を確認 → 充足なら**台帳是正（実装済）**、不足なら補強 |
| 12 | `.claude/hooks/pretooluse-opus-repo-block.sh` | **`test-pretooluse-opus-repo-block.bats` 専用実在** | 同上 |
| 213 | `cli/lib/uuid7_generator.py` | **`test_uuid7_generator_unit.py` 専用実在（U-UUID-001..005）** | 同上 |

> verify-first 実測結果: `FN-WSC-10` は既存テストで DbC 充足と判明した。`FN-WSC-04` / `FN-WSC-12` は既存専用テストに不足観点があり、`FN-WSC-213` は既存 pytest に `os.urandom` 失敗時 `RuntimeError` invariant の補助 1 ケースが必要だったため、補助テストを追加して閉塞した。

## 進め方

1. Codex se が各 UT を verify-first で実装（既存テスト精読 → DbC ギャップのみ実装）。
2. PM が `cli/helix test`（bats + pytest）を独立再実行し全 green を確認。
3. L7 doc `§carry` と verification-strategy §13 台帳を**実体に是正**（実装済になった件数を反映、trace_symmetry L6↔L7 balance≥1.0 維持）。
4. tl-advisor impl review → approve。
5. commit（テスト追加 + 台帳是正で分割）→ gate-driven push 判断。

## 合格基準（G7 単体 / exit）

- 12 UT-WSC それぞれに DbC を反証するテストが存在し green（既存充足は台帳是正で充足扱い）。
- 既存 42 + 充足判明分の pytest/bats が green を維持（回帰なし）。
- 対象 hook/lib のプロダクションコードは無変更（テストのみ追加）。
- trace_symmetry L6↔L7 balance≥1.0 / coverage100% を維持。
- L7 §carry 台帳 と verification-strategy §13 が実体と一致（件数 SSoT 是正）。

## forward_return / 収束

- `design_change_class: pure_impl`（設計 frozen・不変、再凍結 pair なし）。
- 戻し先 = L7 単体テスト実施（既存 V-model 正本）。本 PLAN は Process 兼務 L PLAN（`plan_scope` 強制なし）。
- closure = 上記合格基準成立 + 台帳是正で `WSC-TEST-IMPL` carry を closed。
