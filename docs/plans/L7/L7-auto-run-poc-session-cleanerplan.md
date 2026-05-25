---
plan_id: L7-auto-run-poc-session-cleanerplan
title: "L7-auto-run-poc-session-cleanerplan: Codex session cleaner PoC 起票"
kind: poc
layer: L7
drive: be
status: completed
revised: '2026-05-25'
process_layer: L7
parent_design: HELIX-workflows/helix-process/continuous-run-context-management.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - HELIX-workflows/helix-process/continuous-run-context-management.md
    - HELIX-workflows/helix-process/integration-map.md
    - docs/plans/L7/L7-auto-run-loop-frameworkplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — 実装"
  - role: qa
    slot_label: "QA — 検証"
  - role: tl-advisor
    slot_label: "TL-Advisor — Review"
generates:
  - artifact_path: docs/plans/L7/L7-auto-run-poc-session-cleanerplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/session_cleaner.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_session_cleaner.py
    artifact_type: test
  - artifact_path: verify/auto-run-poc.sh
    artifact_type: test
---

## §0 PLAN concept

`HELIX-workflows/helix-process/continuous-run-context-management.md` で定義された本命 PoC（Claude オーケストレーション + Codex セッションクリーナー）を Discovery mode の D2 + D3 で実行し、本実装を昇格できる材料を短期で固める。  
対象は `cli/lib/session_cleaner.py` の fake adapter + dry-run PoC 実装、`verify/auto-run-poc.sh` 検証、`cli/lib/tests/test_session_cleaner.py` の単体観点、`auto_run_engine.py` の `session_control` 接続点拡張（本設計は D4 / 人間判定で分離）。

## §1 背景

- `L7-auto-run-loop-frameworkplan` で `cli/helix-auto-run` 系の skeleton が完成済み (`auto_run_engine.py` を含む)。
- carry-3 の full autonomous loop 本格検証は第三者 harness 判定・handover 喪失・runaway の P0 リスクがあり、kind=poc 前提の D2 / D3 確認が必要。
- tl-advisor 助言(P0 3件)を受け、`fake adapter` と `dry-run` で実害を起こさず接続経路の実現性を確認する。

## §2 scope

1. `cli/lib/session_cleaner.py` を新規作成し、fake Claude/tmux adapter、dry-run mode、atomic handover preflight を実装する。
2. `cli/lib/tests/test_session_cleaner.py` を作成し、fake fixture ベースで以下を実装する:  
   - `start`  
   - `handover_missing`  
   - `terminate_blocked`  
   - `restart_success`  
   - `runaway_guard`
3. `verify/auto-run-poc.sh` を作成し、以下条件を fail-close で検証する:  
   - carry==0 no-op  
   - bg_task_active block  
   - budget expired stop  
   - max restart count 過負荷ガード
4. `auto_run_engine.py` の `session_control` を拡張し、`mode` を `dry_run|tmux`、`status` を `idle|handover_required|ready_to_restart|restarted|blocked` で取り扱う。
5. `integrations.session_cleaner = active` の接続点を更新し、PoC に必要な統合状態を反映する。

scope 外:
- 実 tmux / 実 Claude 起動（PoC confirmed 後の本実装として別PLAN実施）
- compaction API 統合（drift 混入回避のため別 PoC）
- third-party harness 規約判定（PM/人間確認、CLI 範囲外）
- drive-agent L1-L9 state 拡張（検証軸増加抑制、別 PLAN）

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | `session_cleaner.py` skeleton + fake adapter | dry-run `start` / `terminate` / `restart` が型レベルで通る | completed |
| .2 | atomic handover preflight + runaway guard (`max_restart_count`) | P0 リスク3件中2件を fake test で fail-close 再現・保護 | completed |
| .3 | unit test + verify script + `auto_run_engine.session_control` 接続 | `pytest` + `bats` + verify script 全 PASS | completed |

## §4 実装結果

- W2 3 並列で完遂
  - W2-A: `cli/lib/session_cleaner.py` 新規 (233 行) + `cli/lib/tests/test_session_cleaner.py` (129 行、5 test PASS)
  - W2-B: `cli/lib/auto_run_engine.py` 拡張 (`start --until` / `budget_window.source` / `session_control` field、+58/-6 行) + `cli/lib/tests/test_auto_run_engine.py` 拡張 (4 test 追加、9 test PASS)
  - W2-C: `verify/auto-run-poc.sh` 新規 (176 行、4 negative case fail-close 全 PASS)
- `SessionCleaner` API
  - `SessionCleaner(project_root, *, claude_adapter, tmux_adapter, dry_run=True, max_restart_count=5)`
  - `preflight() -> {ready, blockers, handover_ok, budget_ok, restart_count_ok}`
  - `restart() -> {status: restarted|blocked|dry_run, old_session, new_session, restart_count, reason}`
  - `reset() ->` `restart_count` を `0` に戻す
  - `FakeClaudeAdapter` / `FakeTmuxAdapter`（テスト用）
- state file
  - `.helix/auto-run/session.json`（`auto_run_engine` の `current.json` とは別）
- P0 リスク 3 件（tl-advisor 助言）対応
  - third-party harness 判定: fake adapter で本番起動なし、PoC confirmed 後 human gate (carry-2)
  - handover 喪失: atomic preflight 実装、`handover_missing` で fail-close
  - runaway: `max_restart_count=5` default で fail-close

## §5 検証

- `python3 -m pytest cli/lib/tests/test_session_cleaner.py -v`: 5/5 PASS
- `python3 -m pytest cli/lib/tests/test_auto_run_engine.py -v`: 9/9 PASS（既存 5 + 新規 4、回帰 0）
- `bash verify/auto-run-poc.sh`: 4/4 PASS（Case 1 carry==0 / Case 2 bg_active / Case 3 budget expired / Case 4 max_restart）
- `helix plan lint`: PASS（frontmatter 11 field + `§0-§5 + §11` 完備）
- `python3 -m py_compile cli/lib/session_cleaner.py cli/lib/auto_run_engine.py`: PASS
- Discovery mode 判定
  - D2（PoC 実装） + D3（verify）完遂
  - D4（decide）は本 session 内では未実施（carry-2 third-party harness 規約確認待ち）
  - 暫定判定: P0 リスク 3 件のうち 2 件（atomic preflight + runaway）は fail-close で確認済、1 件（third-party harness）は人間確認待ち

## §11 carry

- carry-1: 実 tmux / 実 Claude 起動は PoC confirmed 後に human gate 付きで本実装化する
- carry-2: third-party harness 規約判定は PM/人間判断（本 session 外）
- carry-3: compaction API 統合は別 PoC に分離して drift 評価を実施
- carry-4: drive-agent L1-L9 state 拡張は別 PLAN へ持ち越し
