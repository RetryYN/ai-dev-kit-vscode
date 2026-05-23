---
plan_id: PLAN-158
title: "helix-codex output diff verify (completion claim vs actual git diff 不整合検出)"
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-MM-001-v5-framework-master-plan.md   # from dependencies.parent
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — git diff --stat 取得モジュール + claim パーサ + WARN/fail-close ロジック実装 + helix-codex 統合"
  - role: pmo-sonnet
    slot_label: "PMO — helix-codex 出力フロー精読・CODEX_TL_MODE.md 最終報告フォーマットとの整合確認"
generates:
  - artifact_type: python_module
    path: cli/lib/codex_diff_verifier.py
  - artifact_type: test
    path: cli/lib/tests/test_codex_diff_verifier.py
  - artifact_type: script
    path: cli/helix-codex
dependencies:
  requires:
    - PLAN-138
  blocks: []
  parent: PLAN-MM-001
related_adr: []
related_docs:
  - cli/helix-codex
  - cli/lib/codex_output_validator.py
  - helix/CODEX_TL_MODE.md §最終報告の最小フォーマット
  - CLAUDE.md §コミット規約
acceptance_criteria:
  - "helix-codex 呼び出し前後で git diff --stat を取得し、claim と actual の file 数を比較する"
  - "actual diff が 0 file (全 0 diff = sandbox fail 等) の場合は fail-close で exit 1 する"
  - "claim N file vs actual M file の不整合 (|N-M| >= 2) で WARN を stderr に出力する"
  - "helix doctor に check_codex_diff_verify_enabled を追加し、helix-codex 統合の有無を確認する"
  - "python3 -m py_compile cli/lib/codex_diff_verifier.py PASS"
  - "pytest cli/lib/tests/test_codex_diff_verifier.py -q 全 PASS (7 scenario)"
  - "bash -n cli/helix-codex PASS"
---

# PLAN-158: helix-codex output diff verify (completion claim vs actual git diff 不整合検出)

## L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 helix-codex 出力検証 framework の強化** であり、
新規の大局判断 (新 framework 採用 / fail-close 化方針転換 / 外部仕様採用) を含まない。
ADR snapshot は不要。

根拠:
- fail-close / WARN ポリシーは PLAN-089 / PLAN-138 で凍結済
- `git diff --stat` は POSIX git コマンドで外部依存なし
- PLAN-138 の `codex_output_validator.py` と同層の検証モジュールとして追加

## 背景

`[[feedback_codex_completion_vs_actual_output]]` が確立した課題:
Codex の completion 報告が実際の git patch と乖離するケースがある。sandbox fail 時は
0 patch が出力されるにもかかわらず完了メッセージが返り、次 Sprint の前提条件が崩れる。

PLAN-138 の `codex_output_validator.py` が section 欠落を WARN するのに対し、
本 PLAN は **git の実状態 (actual diff)** と **Codex の claim** を突き合わせる直交レイヤー。

## WebSearch (PLAN-087 ガード遵守)

`git diff --stat` / subprocess / WARN-fail-close ポリシーはすべて POSIX git + Python stdlib + 既存 HELIX パターン内。WebSearch **skip**。

## 設計方針

### 1. 検証フロー全体

```
helix-codex 呼び出し開始
  → git_stat_before = get_git_diff_stat()   # pre-snapshot
  → Codex 実行 (既存フロー)
  → codex_output = <Codex の stdout>
  → git_stat_after = get_git_diff_stat()    # post-snapshot
  → actual_files = parse_diff_stat(git_stat_after) - parse_diff_stat(git_stat_before)
  → claim_files  = extract_claim_from_output(codex_output)
  → verify(actual_files, claim_files)
       actual == 0  → fail-close (exit 1)
       |actual - claim| >= 2  → WARN
       else  → pass
```

### 2. git diff 取得

```python
def get_git_diff_stat(cwd=None) -> str:
    result = subprocess.run(["git", "diff", "--stat", "HEAD"], capture_output=True, text=True, cwd=cwd)
    return result.stdout

def parse_diff_file_count(stat_output: str) -> int:
    match = re.search(r"(\d+) file[s]? changed", stat_output)
    return int(match.group(1)) if match else 0
```

### 3. claim パーサ

`## File List` section (PLAN-138 で強制化) の行数を claim file 数として使用する。
不在の場合は claim=-1 (不明) として WARN に留め、fail-close しない。

```python
def extract_claim_file_count(codex_output: str) -> int:
    match = re.search(r"## File List\n((?:.+\n?)+)", codex_output)
    if not match:
        return -1
    return len([l for l in match.group(1).splitlines() if l.strip()])
```

### 4. 不整合判定ロジック

| 条件 | 挙動 | 理由 |
|---|---|---|
| actual == 0 | fail-close (exit 1) | sandbox fail / 全 0 diff は実装未完とみなす |
| claim == -1 (不明) | WARN のみ | `## File List` 不在は PLAN-138 で別途 WARN される |
| `|actual - claim|` >= 2 | WARN | ±1 は mtime-only change 等で誤差が出るため許容 |
| それ以外 | pass | 正常 |

```python
def verify(actual: int, claim: int) -> tuple[str, str | None]:
    if actual == 0:
        return "fail", "actual diff = 0 files (sandbox fail 疑い)"
    if claim == -1:
        return "warn", "## File List 不在のため claim 不明"
    if abs(actual - claim) >= 2:
        return "warn", f"claim={claim} files, actual={actual} files"
    return "pass", None
```

### 5. helix-codex 統合

helix-codex の Codex 実行前後で `codex_diff_verifier.py` を呼び出す (CLI mode: `--snapshot` / `--verify`)。
actual=0 の fail-close のみ exit 1。WARN は stderr 出力で exit 0 維持。

### 6. helix doctor 統合

`check_codex_diff_verify_enabled`: `cli/helix-codex` に `codex_diff_verifier.py` 呼び出しが存在するかを grep で確認。不在なら WARN。

## 実装計画

### Sprint .1: codex_diff_verifier.py 実装 (se 委譲、size M)

Entry 条件: `cli/helix-codex` を Read して Codex 実行後の output 取得箇所を確認

実施内容:
1. `cli/lib/codex_diff_verifier.py` 新規作成 (4 関数 + CLI mode `--snapshot` / `--verify`)
2. `python3 -m py_compile cli/lib/codex_diff_verifier.py` PASS (mandatory in sprint)

完了条件: `verify(0,5)` → fail / `verify(3,5)` → warn / `verify(3,3)` → pass

### Sprint .2: helix-codex 統合 (se 委譲、size S)

実施内容:
1. `cli/helix-codex` の Codex 実行前後に `codex_diff_verifier.py` 呼び出し追加
2. fail-close (actual==0) 時に exit 1
3. `bash -n cli/helix-codex` PASS (mandatory in sprint)

### Sprint .3: pytest + helix doctor (se 委譲、size S)

実施内容:
1. `cli/lib/tests/test_codex_diff_verifier.py` 新規作成 (7 scenario):
   - `test_parse_diff_zero` / `test_parse_diff_n`
   - `test_extract_claim_present` / `test_extract_claim_absent`
   - `test_verify_zero_actual` (fail) / `test_verify_large_diff` (warn) / `test_verify_pass`
2. `pytest cli/lib/tests/test_codex_diff_verifier.py -q` 全 PASS
3. `helix doctor check_codex_diff_verify_enabled` 実装

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/codex_diff_verifier.py` PASS
- [ ] `bash -n cli/helix-codex` PASS
- [ ] pytest 全 7 scenario PASS
- [ ] fail-close (actual==0) の動作手動確認
- [ ] セルフレビュー + pmo-sonnet review (Sprint .3 完了時)

## DoD (Definition of Done)

- [ ] `cli/lib/codex_diff_verifier.py` 実装済 (4 関数 + CLI mode)
- [ ] `cli/helix-codex` に pre/post snapshot + verify 呼び出し追加済
- [ ] actual=0 時に fail-close (exit 1) が動作する
- [ ] claim 不整合時に WARN が stderr に出力される
- [ ] pytest 7 scenario 全 PASS + `py_compile` + `bash -n` PASS
- [ ] `helix doctor check_codex_diff_verify_enabled` pass
- [ ] helix doctor pass 数が現行以上

## リスク

| リスク | 緩和策 |
|---|---|
| staged-only changes を git diff HEAD が含まない | staged + unstaged 両方を含む。staged のみは P2 carry |
| ## File List が claim として不正確 | claim は参考値のみ。fail-close は actual=0 のみで独立動作 |
| PLAN-138 未完了時に claim parser が機能しない | claim=-1 (不明) として WARN のみ |
| subprocess git call が git 未インストール環境で失敗 | FileNotFoundError → WARN のみ、fail-close しない |

## V-model trace

- 設計: 本 file (PLAN-158)
- 実装: `cli/lib/codex_diff_verifier.py` / `cli/helix-codex` → docstring に「設計: PLAN-158」
- テスト設計: §2 Sprint .3 を正本とする
- テストコード: `cli/lib/tests/test_codex_diff_verifier.py` → docstring に「DoD 検証: PLAN-158」

## 関連 reference

- PLAN-138 (codex detailed report 強制出力、本 PLAN の依存元)
- [[feedback_codex_completion_vs_actual_output]] (本 PLAN の起票根拠 feedback)
- [[feedback_design_doc_web_search_required]] (PLAN-087 ガード、本 PLAN は skip 適用)
- [[feedback_adr_before_plan_violation]] (ADR snapshot 要否判定、本 PLAN は不要と確認)
- helix/CODEX_TL_MODE.md §最終報告の最小フォーマット (claim の参照元)
- cli/lib/codex_output_validator.py (PLAN-138 の section 欠落検証、直交レイヤー)
