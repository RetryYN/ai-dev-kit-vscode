---
plan_id: PLAN-048
title: 'PLAN-048（Codex docs/PG 委譲 prompt template に write 必須要求 default 化 + audit-only failure 機械検知）'
status: completed
completed: 2026-05-10
created: 2026-05-10
finalized: 2026-05-10
author: 'PM (Opus)'
priority: high
size: M
phases_affected: helix-codex / docs.conf / pg.conf / codex-review.md / runtime audit
parent_plan: PLAN-047
acceptance:
  prompt_write_default:
    verification_commands:
      command: "grep -cE '\\[タスク種別\\] 実装.*apply_patch|write 必須' cli/roles/docs.conf cli/roles/pg.conf"
      expected: "各ファイル ≥ 1"
  summary_format_diff_lines:
    verification_commands:
      command: "HELIX_CODEX_NO_FOOTER=0 cli/helix-codex --role pg --task '[タスク種別] 実装' --dry-run | grep -c 'diff_lines:'"
      expected: "≥ 1"
  audit_runtime_check_pytest:
    verification_commands:
      command: "python3 -m pytest cli/lib/tests/test_codex_post_validation.py -k 'write_expected or diff_lines' -q"
      expected: "exit 0 / ≥ 7 tests passed (diff_zero_warns, diff_positive_silent, readonly_silent, diff_lines_missing_warns, diff_lines_zero_warns, diff_lines_mismatch_warns, diff_lines_match_silent)"
  audit_runtime_integration:
    verification_commands:
      command: "bats cli/tests/test-helix-codex-write-audit.bats"
      expected: "exit 0 / ≥ 2 tests passed (impl_task_no_diff_warns, review_task_no_diff_silent)"
  tests_all_pass:
    verification_commands:
      command: "cli/helix test"
      expected: "exit 0 / 0 failed"
  branch_minimal_footprint:
    verification_commands:
      command: "git branch --list 'improvements/plan-048*' | wc -l"
      expected: "0"
---

# PLAN-048: Codex 委譲 prompt template に write 必須要求 default 化 + audit-only failure 機械検知

## §1 背景

PLAN-044 W-4 / PLAN-046 W-1 / PLAN-047 W-0 と、3 度連続で同一の **audit-only failure** が発生した。

- **症状**: Codex docs/PG が write 必須タスクを受領 → analysis JSON を返すのみで実ファイル編集なし
- **検知**: PM が git status / git diff で「変更ファイル 0」を発見 → 再投入で完遂
- **再投入コスト**: PLAN あたり 2-4 分の round-trip ロス × 3 PLAN = 6-12 分の累計ロス
- **memory feedback** (PLAN-046 で feedback_codex_completion_distrust.md 起票) は個別対応で限界

memory feedback だけでは「Codex 側の prompt 解釈」を変えられないため、根本対策として
**helix-codex prompt template と runtime audit に write 必須要求を default 化** する。

## §2 解消対象 (3 層 + 責務分離)

### Layer 1: Prompt 強化 (W-1) — **自己申告ルートの底上げ**

- `cli/roles/docs.conf` system_prompt: 「`[タスク種別] 実装` 時は必ず apply_patch / Edit で実ファイル編集」を明記
- `cli/roles/pg.conf` system_prompt: 同上を明記
- 既存の docs.conf には部分的に書かれているが、SUMMARY 必須出力との連携が弱い
- **責務**: Codex 側に "write が必須" であることを認識させる (model 側強化)

### Layer 2: SUMMARY format 拡張 (W-2) — **自己申告フィールド追加**

- `cli/helix-codex` の `HELIX_CODEX_OUTPUT_FOOTER` に `diff_lines:` フィールド追加 (model 出力要求)
- task_type=実装 で `diff_lines: 0` または欠落 → SUMMARY parser (W-3 内) が後段で検査
- 出力例も更新
- **責務**: Codex 側の自己申告に diff_lines を追加させる (parser 検査の入口提供)
- **本 Sprint 内では parser 実装はしない**。footer prompt 追記のみ (cli/helix-codex 1 ファイル変更)

### Layer 3: Runtime audit + SUMMARY parser cross-check 実装 (W-3) — **実測検知 + 自己申告検査**

- `cli/lib/codex_post_validation.py` に `--check-write-expected` オプション追加
- task_type=実装 かつ `--allowed-files` 不指定でも、git diff (before vs after) を検査
- diff 0 件 → 「audit-only failure suspected」 warning を stderr に emit (stop はしない、再投入判断は PM)
- **cli/helix-codex の呼び出し条件追加も本 Sprint 範囲**: `--check-write-expected` を task_type=実装 時に常時 invoke
- **SUMMARY stdout capture を validator へ渡す導線追加**: cli/helix-codex の `STDOUT_FILE` を `--summary-stdout` で codex_post_validation.py へ渡す。emit 後の rm を post-validation 後に移動
- **W-2 で導入した `diff_lines:` field の parser 実装**:
  - missing → warning ("self-report missing diff_lines")
  - zero → warning ("self-report claims zero diff")
  - 実測 git diff lines と mismatch → warning ("self-report mismatches actual: claimed=N, actual=M")
  - match → silent
- **責務**: 実測 git diff + 自己申告 SUMMARY の cross-check で audit-only failure を機械検知

### W-2 / W-3 の依存関係

- W-2 は cli/helix-codex の **prompt footer のみ**変更
- W-3 は cli/helix-codex の **post-validation invocation 追加** + cli/lib/codex_post_validation.py 拡張
- 両者は cli/helix-codex の異なる行を編集 → 直列実行 (W-2 → W-3) で merge conflict 回避

## §3 Sprint 構成

| Sprint | 内容 | 委譲先 | 想定 commit |
|---|---|---|---|
| W-0 | draft + 2R TL + finalize | docs / TL ×2 | (本) |
| W-1 | docs.conf / pg.conf system_prompt 強化 | PG | feat(plan-048): W-1 |
| W-2 | helix-codex SUMMARY footer に diff_lines: 追加要求 (prompt のみ) | PG | feat(plan-048): W-2 |
| W-3 | helix-codex --check-write-expected invocation + codex_post_validation.py 拡張 + bats/pytest | SE | feat(plan-048): W-3 |
| W-final | 統合検証 + retro + status completed + push | Opus | feat(plan-048): W-final |

### 並列性

- **W-1** (cli/roles/docs.conf, cli/roles/pg.conf) と **W-2/W-3** (cli/helix-codex, cli/lib/codex_post_validation.py) は完全独立 → 並列可能
- **W-2 と W-3** はどちらも cli/helix-codex を編集するため **直列** (W-2 → W-3)
- 結果: W-1 ∥ (W-2 → W-3) の構造

## §4 受入条件

- 6 acceptance criteria すべて通過 (frontmatter 参照: prompt_write_default / summary_format_diff_lines / audit_runtime_check_pytest / audit_runtime_integration / tests_all_pass / branch_minimal_footprint)
- helix-test 614 / pytest 1042 / bats 414 / tests 23 全 PASS 維持
- 5 commits 程度 push 済 (W-0 / W-1 / W-2 / W-3 / W-final、W-final で main merge)

## §5 Out of Scope

- DS-120 PDF 統合版取得 (PLAN-049+ carry)
- --auto-thinking 利用統計 (PLAN-049+ carry)
- mapping table 自動 link 検証 (PLAN-049+ carry)
- 既存 audit-only failure log 蓄積 (本 PLAN は予防策、observability は別 PLAN)

## §6 リスク

- W-1 prompt 変更で過剰反応 (read-only タスクで write しようとする) → consent_mode=plan-only と整合性確認必須
- W-2 SUMMARY format breaking change → 既存 marker filter (PLAN-040/041) と互換性必須
- W-3 false positive (read-only タスクで warning emit) → task_type 判定との連動必須

## §7 検証方法

- W-1 単体: docs.conf 改訂後に dry-run でプロンプト出力確認、`実装` 文字列が含まれること
- W-2 単体: HELIX_CODEX_NO_FOOTER=0 で footer に `diff_lines:` 含まれること、=1 で従来通り
- W-3 単体: pytest unit test で `--check-write-expected` 動作確認 (diff 0 → warning, diff > 0 → silent)
- 統合: cli/helix-test で 614/0、bats 414/0、pytest cli/lib/tests 1042/0 維持
