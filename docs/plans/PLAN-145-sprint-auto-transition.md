---
plan_id: PLAN-145
title: "helix sprint 自動遷移 framework (PostToolUse commit 解析 → mandatory check → next 自動進行)"
kind: impl
layer: L4
drive: be
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
size: M
created: "2026-05-23"
owner: PM
phases: L3, L4
gates: G3, G4
agent_slots:
  - role: se
    slot_label: "SE — PostToolUse hook commit 解析 logic + helix sprint complete --auto-check 実装"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-077 Sprint Plan 標準構造との drift 確認・hook 設計整合レビュー"
  - role: tl-advisor
    slot_label: "TL adversarial check — mandatory in sprint チェック設計・自動遷移条件の境界ケース review"
  - role: qa
    slot_label: "QA — fake commit message fixture + mandatory check pass/fail 全シナリオ検証"
generates:
  - artifact_path: docs/plans/PLAN-145-sprint-auto-transition.md
    artifact_type: design_doc
  - artifact_path: .claude/hooks/posttooluse-sprint-auto-transition.sh
    artifact_type: hook
  - artifact_path: cli/lib/sprint_auto_check.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_sprint_auto_transition.py
    artifact_type: test
dependencies:
  parent: null
  requires:
    - PLAN-077
  blocks: []
related_adr:
  - ADR-050
related_plans:
  - PLAN-077 (Sprint Plan 標準化 framework — mandatory in sprint 8 ステップ正本)
  - PLAN-099 (自動走行 framework 5-layer — PostToolUse hook 連携)
---

# PLAN-145: helix sprint 自動遷移 framework

## L2 凍結 (ADR snapshot)

本 PLAN tree は **PostToolUse hook で commit message を解析し Sprint 状態を自動遷移する新規 framework 採用**を含む。

ADR-050 snapshot として別文書で凍結する。

根拠:
- PostToolUse の commit 解析による Sprint 遷移は既存 PLAN-077/PLAN-099 の適用外
- mandatory in sprint 自動チェック (py_compile / lint / test / review) の実行順・停止条件はポリシー決定
- WARN 止まりか auto-skip かの判断は運用合意が必要

## 背景

PLAN-077 で確立した Sprint Plan 標準構造 (8 ステップ) では、各 Sprint `.X` の終了条件判定と
`.X+1` への遷移は手動コマンド (`helix sprint next` / `helix sprint complete`) に依存している。

具体的な問題:

1. Sprint Exit 時の mandatory in sprint チェック (py_compile / 該当 test / 全回帰 / レビュー) を
   PM や Codex が手動でトリガーする必要があり、skip されるリスクがある
2. L4 実装中の commit ごとに `PLAN-X sprint .Y` 形式が含まれているが、
   それを PostToolUse hook で検出して自動 mandatory チェックに接続する仕組みが不在
3. PLAN-099 の Layer 1 (PostToolUse hook → helix.db.task_queue auto-enqueue) と
   Sprint 遷移ロジックが連携していない

`helix sprint complete --auto-check` の skeleton は PLAN-077 で構想済みだが、
実装が不在のため本 PLAN で具体化する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は HELIX 内部の Sprint 状態管理拡張であり、外部ライブラリ / 業界 standard への新規依存なし。

WebSearch **skip**。

skip 理由:
- commit message 解析は POSIX bash + grep で完結
- mandatory チェック (py_compile / pytest / bash -n) は既存 HELIX toolchain に準拠
- Sprint 状態管理は helix.db の既存テーブル拡張で対応 (PLAN-077/092 の migration 規約準拠)

## 設計方針

### 1. commit message 解析パターン (PostToolUse hook)

#### hook trigger

- **hook type**: PostToolUse (matcher: Bash)
- **trigger 条件**: `tool_output` に `git commit` 成功メッセージが含まれる場合

#### commit message 解析正規表現

```bash
SPRINT_RE='PLAN-[0-9]+ sprint \.([0-9]+)'
```

例:

- `feat(helix-sprint): PLAN-145 sprint .1 — runtime_status.py 実装` → Sprint `.1` 検出
- `fix(pytest): PLAN-145 sprint .2 — fixture timeout 修正` → Sprint `.2` 検出
- `chore: minor fix` → Sprint パターン不在 → hook 何もしない

#### helix.db sprint_progress テーブル連携

```sql
UPDATE sprint_progress
SET current_sprint = ?, last_commit_at = datetime('now')
WHERE plan_id = ?;
```

### 2. mandatory in sprint 自動チェック (cli/lib/sprint_auto_check.py)

#### チェック順序 (PLAN-077 §Sprint .X 標準 8 ステップ準拠)

| ステップ | コマンド | 失敗時挙動 |
|---|---|---|
| Step 4a | `python3 -m py_compile <changed_files>` | WARN + auto-transition 停止 |
| Step 4b | `bash -n <changed_bash_files>` | WARN + auto-transition 停止 |
| Step 4c | `python3 -m pytest <targeted_tests> -q` | WARN + auto-transition 停止 |
| Step 5 | `python3 -m pytest cli/lib/tests/ -q` (全回帰) | WARN (non-blocking、継続可) |

全回帰は Sprint Exit 直前に実施。Step 4a/4b/4c は blocking チェック。

#### `helix sprint complete --auto-check` 実装仕様

```bash
helix sprint complete --auto-check [--plan-id PLAN-NNN] [--sprint N]
```

- `--plan-id` 省略時は `HELIX_CURRENT_PLAN_ID` 環境変数または `.helix/phase.yaml` から取得
- `--sprint` 省略時は helix.db `sprint_progress.current_sprint` から取得
- mandatory チェック全 PASS → Sprint `.X` を `completed` に遷移し、`.X+1` を `in_progress` に設定
- いずれか WARN → 遷移停止、stderr に WARN 列挙

### 3. hook 実装 (.claude/hooks/posttooluse-sprint-auto-transition.sh)

```
PostToolUse (matcher: Bash)
  → tool_output を parse して git commit 成功 + Sprint pattern 検出
  → helix sprint complete --auto-check --plan-id <PLAN-ID> --sprint <N>
  → PASS: "Sprint .N → .N+1 auto-transition complete" を stdout
  → WARN: 停止理由を stderr + helix doctor warn に積む
```

fail-safe 設計:
- hook 内でエラー発生時は `exit 0` (fail-open) で通常処理を継続する
- auto-check 中の pytest 実行エラーは WARN 扱い、hook が Claude の tool 実行を妨げない

## 実装計画

### Sprint .1: sprint_auto_check.py + helix sprint complete --auto-check (Codex se 委譲、size M)

**Entry 条件**: PLAN-077 status 確認 (sprint_progress テーブル現状把握)

実施内容:

1. `cli/lib/sprint_auto_check.py` 新規作成
   - `run_mandatory_checks(plan_id, sprint_num, changed_files)` 実装
   - py_compile / bash -n / pytest targeted / pytest full-regression の 4 ステップ
   - 結果を `CheckResult` dataclass で返す (passed / warned / blocked)
2. `helix sprint complete --auto-check` subcommand 実装
3. `python3 -m py_compile cli/lib/sprint_auto_check.py` PASS (mandatory in sprint)

受入条件:
- `run_mandatory_checks` が 4 ステップを順番に実行し CheckResult を返す
- blocking チェック失敗時に遷移を停止する
- `helix sprint complete --auto-check` が helix.db `sprint_progress` を更新する

### Sprint .2: PostToolUse hook 実装 (Codex se 委譲、size S)

**Entry 条件**: Sprint .1 `helix sprint complete --auto-check` 動作確認済

実施内容:

1. `.claude/hooks/posttooluse-sprint-auto-transition.sh` 新規作成
   - git commit 成功検出 + Sprint pattern 解析
   - `helix sprint complete --auto-check` 呼び出し
   - fail-open (exit 0) 保証
2. `bash -n .claude/hooks/posttooluse-sprint-auto-transition.sh` PASS (mandatory in sprint)
3. `cli/claude/settings.json` への hook 登録

受入条件:
- `PLAN-145 sprint .1` 形式の commit message でトリガーされる
- Sprint pattern 不在の commit では何もしない
- hook エラー時も Claude の tool 実行が継続される (fail-open)

### Sprint .3: fixture 検証 (Codex qa 委譲、size S)

**Entry 条件**: Sprint .2 hook 実装完了

実施内容:

1. `cli/lib/tests/test_sprint_auto_transition.py` 新規作成
   - 4 シナリオ: mandatory_all_pass / py_compile_fail / pytest_fail / no_sprint_pattern
   - `datetime.now(timezone.utc)` ベースで動的 timestamp 生成
2. `python3 -m pytest cli/lib/tests/test_sprint_auto_transition.py -v` 全 PASS

受入条件:
- 4 シナリオ全 PASS
- commit pattern なし → hook no-op 確認

## テスト設計 (V-model L4 単体テスト設計、Sprint .3 対応)

| テスト ID | シナリオ | 入力 | 期待結果 |
|---|---|---|---|
| T145-001 | mandatory 全 PASS | py_compile OK / pytest OK | Sprint `.N+1` に遷移 |
| T145-002 | py_compile 失敗 | `.py` に syntax error | WARN + 遷移停止 |
| T145-003 | pytest 失敗 | targeted test 1 件 fail | WARN + 遷移停止 |
| T145-004 | commit に Sprint pattern なし | 通常 commit message | hook no-op、DB 変更なし |

## DoD (Definition of Done)

- [ ] `python3 -m py_compile cli/lib/sprint_auto_check.py` PASS
- [ ] `bash -n .claude/hooks/posttooluse-sprint-auto-transition.sh` PASS
- [ ] `helix sprint complete --auto-check` が helix.db を正しく更新する
- [ ] mandatory チェック失敗時に遷移が停止する
- [ ] hook が fail-open (exit 0) で動作する
- [ ] 4 シナリオ fixture テスト全 PASS (T145-001〜T145-004)
- [ ] ADR-050 snapshot 起票済 (L2 大局判断凍結)
- [ ] `helix doctor` warn 増加なし

## V-model 4 artifact trace

| artifact | 対象 |
|---|---|
| ① 設計 (本 PLAN) | §設計方針 / §実装計画 |
| ③ テスト設計 | 本 PLAN §テスト設計 (T145-001〜T145-004) |
| ② 実装コード | cli/lib/sprint_auto_check.py + .claude/hooks/posttooluse-sprint-auto-transition.sh |
| ④ テストコード | cli/lib/tests/test_sprint_auto_transition.py (Sprint .3 で実装) |

双方向 trace:
- 本 PLAN → テスト設計: Sprint .3 ケース一覧に T145 番号明記
- テストコード → 設計: pytest test に `# PLAN-145 T145-NNN` コメントで対応付け
- テスト設計 → テストコード: test 関数名で T145-NNN 対応

## risks

| リスク | 影響 | 緩和策 |
|---|---|---|
| mandatory チェックの誤 WARN | 正常実装の Sprint 遷移が止まる | fail-open 設計 + PM 手動 override `helix sprint next --force` |
| hook が重い pytest を毎 commit 実行 | 全回帰は時間コスト大 | 全回帰は Sprint Exit 直前のみ (Step 5)、targeted test は即時 (Step 4c) |
| sprint_progress テーブル不在 | helix.db migration 未適用環境で crash | migration check + graceful skip |
| pattern 誤検出 | 関係ない commit で trigger | PLAN ID 完全一致 `PLAN-\d{3}` + sprint 語を AND 条件で絞る |

## 関連 reference

- PLAN-077 §Sprint Plan 標準構造 (mandatory in sprint 8 ステップ正本)
- PLAN-099 §Layer 1 (PostToolUse → helix.db auto-enqueue、連携候補)
- PLAN-092 §helix.db sprint_progress テーブル (DB 正本)
- CLAUDE.md §Sprint Plan 標準構造 (PLAN-077 要約)
- ADR-050 (本 PLAN の L2 snapshot、起票予定)
