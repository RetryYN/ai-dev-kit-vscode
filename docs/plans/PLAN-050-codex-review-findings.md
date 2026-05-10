---
plan_id: PLAN-050
title: 'PLAN-050（Codex review findings 解消 - bats hidden failure + HELIX_CORE.md ドリフト + phase.yaml mode 整合性 + audit 精緻化）'
status: completed
completed: 2026-05-11
created: 2026-05-10
finalized: 2026-05-10
author: 'PM (Opus)'
priority: high
size: M
phases_affected: cli/tests/test-helix-code.bats / helix/HELIX_CORE.md / cli/helix-doctor / cli/lib/codex_post_validation.py
parent_plan: PLAN-049
acceptance:
  bats_run_wrapped:
    verification_commands:
      command: "grep -cE 'run python3 - .*helix.*db' cli/tests/test-helix-code.bats"
      expected: "≥ 2 (line 647 + 687 が run wrap 化)"
  bats_schema_version_dynamic:
    verification_commands:
      command: "grep -cE 'helix_db\\.CURRENT_SCHEMA_VERSION|from helix_db import CURRENT_SCHEMA_VERSION' cli/tests/test-helix-code.bats"
      expected: "≥ 1 (定数参照で hardcode drift 回避、helix_db.CURRENT_SCHEMA_VERSION import)"
  bats_hidden_failure_caught:
    verification_commands:
      command: "bash -c 'set -e; cp cli/tests/test-helix-code.bats /tmp/plan050-bats.bak; trap \"cp /tmp/plan050-bats.bak cli/tests/test-helix-code.bats; rm -f /tmp/plan050-bats.bak\" EXIT; sed -i s/CURRENT_SCHEMA_VERSION/CURRENT_SCHEMA_VERSION_FORCE_FAIL/g cli/tests/test-helix-code.bats; bats cli/tests/test-helix-code.bats 2>&1 | grep -q not.ok'"
      expected: "exit 0 (intentional fail で bats が not ok 報告 = hidden failure 解消の証明、trap で確実に復元)"
  helix_core_role_pg:
    verification_commands:
      command: "grep -c 'helix codex --role pe' helix/HELIX_CORE.md"
      expected: "0 (--role pe を pg に修正済)"
  helix_core_g4_uncovered:
    verification_commands:
      command: "grep -c 'helix code stats --uncovered --scope core5' helix/HELIX_CORE.md"
      expected: "≥ 1 (--uncovered が --scope の前に追加済)"
  doctor_phase_mode_check_section:
    verification_commands:
      command: "grep -cE 'mode/phase|phase_mode_consistency' cli/helix-doctor"
      expected: "≥ 1 (mode/phase 整合性 check section 追加)"
  doctor_phase_mode_unit_tests:
    verification_commands:
      command: "python3 -m pytest cli/lib/tests/ -k 'phase_mode or mode_phase' -q"
      expected: "exit 0 / ≥ 4 tests passed (forward_l_phase_pass, reverse_r_phase_pass, scrum_s_phase_pass, mismatch_warns)"
  audit_modified_files_detected:
    verification_commands:
      command: "python3 -m pytest cli/lib/tests/test_codex_post_validation.py -k 'modified or actual_modified' -q"
      expected: "exit 0 / ≥ 2 tests passed (modified_file_counted, modified_zero_warns_only_if_no_changes)"
  tests_all_pass:
    verification_commands:
      command: "cli/helix test"
      expected: "exit 0 / 0 failed"
  branch_minimal_footprint:
    verification_commands:
      command: "git branch --list 'improvements/plan-050*' | wc -l"
      expected: "0"
---

# PLAN-050: Codex review findings 解消 + audit 精緻化

## §1 背景

PLAN-049 W-final 直前にユーザーから Codex review findings (4 件、HIGH×2 + MEDIUM×2) が提供された。
本 PLAN scope 外と判定し carry したが、HIGH 級が CI integrity (bats hidden failure) と
正本ドキュメント整合性 (HELIX_CORE.md `--role pe` 誤記) に関わるため即時対応。

加えて、PLAN-048 で導入した audit-only failure 機械検知が **modified existing files を
検知できない** 既知制限を併せて精緻化する (新規 file count のみで判定する設計)。

## §2 解消対象 (4 finding + 1 改善)

### Finding 1: bats hidden failure (W-1) — HIGH

**症状**: `cli/tests/test-helix-code.bats` line 647 / 687 で Python heredoc を `run` 無しで実行。
AssertionError が swallow され bats は PASS と報告。`assert version == 15` が現状 schema 19 と乖離、
CI が migration regression を検知できない状態。

**修正**:
- Python heredoc を `run python3 - "$ARG1" "$ARG2" <<'PY'` 形式に変更
- assertion `assert version == 15` を `helix_db.CURRENT_SCHEMA_VERSION` を import して動的検証 (将来 drift 回避)
- `[ "$status" -eq 0 ]` の前に `run` を必ず置く構造を強制

**検証**:
- 意図的に `version == 99` に書き換えたら bats が not ok を報告すること (hidden failure 解消の証明)

### Finding 2: HELIX_CORE.md `--role pe` 誤記 (W-2) — HIGH

**症状**: `helix/HELIX_CORE.md` line 42 で `helix codex --role pe` を案内するが、実装側の
valid role は `pg` (cli/roles/pg.conf)。`--role pe` は invalid_role で fail。
SKILL_MAP.md (`pg`) との正本間不整合。

**修正**: HELIX_CORE.md の該当箇所を `pg` に修正。

### Finding 3: G4 coverage gate コマンド `--uncovered` 不在 (W-2 統合) — MEDIUM

**症状**: `helix/HELIX_CORE.md` line 51 の
`helix code stats --scope core5 --bucket coverage_eligible --fail-under 80` は
`--uncovered` flag が無く、実行すると 「不明なオプションです: --scope」 で fail。

**修正**: `helix code stats --uncovered --scope core5 --bucket coverage_eligible --fail-under 80` に修正。
W-2 と同じ HELIX_CORE.md 編集なので統合。

### Finding 4: phase.yaml mode/phase 不整合 (W-3) — MEDIUM

**症状**: `.helix/phase.yaml` で `current_mode: reverse` + `current_phase: L1`。
L1 は Forward phase (VALID_PHASES = L1-L11)、Reverse mode なら R0-R4/RGC が正解。
`helix status` は Forward の `helix plan draft` を案内、判断曖昧化。

**修正**: `cli/helix-doctor` に mode/phase 整合性 check を追加:
- mode=reverse なら phase は R0-R4 / RGC のいずれか
- mode=forward なら phase は L1-L11 のいずれか
- mode=scrum なら phase は S0-S4 のいずれか
- 不整合は WARNING (phase.yaml は user runtime state なので fix までは強制しない)

### 改善 1: PLAN-048 audit-only failure 検知精緻化 (W-4)

**現状制約**: `count_actual_diff_files()` は `(after - before) | untracked_after` で計算。
**既存 tracked file の修正 (M state)** は after も before も同じパスを含むため delta 0、
audit-only failure WARNING を誤発火する。実際に PLAN-049 で 5 SKILL を modify した際、
全て「actual=0」と誤判定された。

**修正**:
- `git diff --shortstat` の insertions+deletions 行数を取得する関数追加
- `actual_files` を `after - before` 集合 + `git diff --name-only` (modified) の合算に変更
- task_type=実装 で `actual=0` と判定するのは「全くファイル変更なし」のケースのみに限定

## §3 Sprint 構成

| Sprint | 編集対象 | 委譲先 | 想定 commit |
|---|---|---|---|
| W-0 | draft + 2R TL + finalize | docs / TL ×2 | feat(plan-050): W-0 |
| W-1 | cli/tests/test-helix-code.bats を run-wrap + CURRENT_SCHEMA_VERSION 動的検証 | SE | feat(plan-050): W-1 |
| W-2 | helix/HELIX_CORE.md の --role pe → pg + G4 --uncovered | docs | feat(plan-050): W-2 |
| W-3 | cli/helix-doctor に mode/phase 整合性 check 追加 + pytest | PG | feat(plan-050): W-3 |
| W-4 | cli/lib/codex_post_validation.py に modified file 検知 + pytest | SE | feat(plan-050): W-4 |
| W-final | 統合検証 + retro + status completed + push | Opus | feat(plan-050): W-final |

### 編集ファイル衝突マトリクス (本体 + テストファイル)

| Sprint | 本体ファイル | テストファイル |
|---|---|---|
| W-1 | cli/tests/test-helix-code.bats | (本体が test ファイル自体、別途 test 不要) |
| W-2 | helix/HELIX_CORE.md | (docs 変更、test 不要) |
| W-3 | cli/helix-doctor | cli/lib/tests/test_helix_doctor_phase_mode.py (新規) |
| W-4 | cli/lib/codex_post_validation.py | cli/lib/tests/test_codex_post_validation.py (既存に追記) |

**全 Sprint の本体ファイル + テストファイルとも完全独立** → W-1 ∥ W-2 ∥ W-3 ∥ W-4 の
**4 並列実行可能**。最大の効率化、Stage は W-final 1 段のみ。

W-3 は新規 pytest ファイル、W-4 は既存 pytest ファイル末尾追記なので衝突なし。

## §4 受入条件

- 10 acceptance criteria (frontmatter)
- helix-test 614 / pytest 1049+ / bats 416+ / tests 23 全 PASS 維持
- 6 commits 程度 push 済 (W-0 / W-1 / W-2 / W-3 / W-4 / W-final、W-final で main merge)

## §5 Out of Scope

- DS-120 の Reverse 反映 (PLAN-051+ carry)
- helix-reverse CLI worked-example スキャフォールド (PLAN-049 §8 carry、PLAN-051+)
- adversarial-review の Reverse 専用 worked checklist (PLAN-049 §8 carry)
- phase.yaml の自動修正 (runtime state、user 操作領域、本 PLAN は doctor 警告のみ)

## §6 リスク

- **W-1 schema hardcode 再発**: 将来 schema 20 にするとまた drift。
  → **緩和**: `helix_db.CURRENT_SCHEMA_VERSION` 定数を import して動的検証、acceptance も
  定数参照 (import 行 grep) でカバー、hardcode 19 を acceptance に固定しない
- **W-3 mode/phase check の false positive**: phase 遷移中の中間状態で警告が出る可能性
  → 緩和: WARNING のみ、stop しない
- **W-4 git diff 呼び出しコスト**: post-validation のたびに git diff 実行
  → 緩和: --shortstat だけなので軽量、in-memory cache 不要
- **4 並列実行の Codex usage limit**: PLAN-047 で 5 並列実証済、4 並列は問題なし想定

## §7 検証方法

- W-1 単体: bats 1 件意図的に書き換え → not ok 報告 (hidden failure 解消の証明)
- W-2 単体: HELIX_CORE.md の grep で `--role pe` 0 + `--uncovered --scope` ≥ 1
- W-3 単体: cli/helix-doctor 実行 + pytest unit test (mode/phase 不整合検出)
- W-4 単体: pytest 2 件以上 (modified file detection)
- 統合: cli/helix-test / pytest / bats が破壊されない

## §8 PLAN-051 候補 (carry)

1. DS-120 の Reverse R0-R4/RGC への Informative reference 追加 (PLAN-049 OOS)
2. helix-reverse CLI に worked-example スキャフォールド (`helix reverse example --type code`)
3. adversarial-review の Reverse 専用 worked checklist
4. mapping table 自動 link 検証 (PLAN-047 carry)
5. --auto-thinking 利用統計 (PLAN-046 carry)
