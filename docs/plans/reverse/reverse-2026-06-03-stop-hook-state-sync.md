---
plan_id: reverse-2026-06-03-stop-hook-state-sync
title: "Action: Phase3 readiness — handover/session-log state 永続化基盤の修復（PLAN-081 Stop 統合片肺の回収 + head_sha 同期契約）"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
workflow: reverse
kind: reverse
layer: L7
drive: reverse
status: completed
created: 2026-06-03
owner: PM
agent_slots:
  - role: tl-advisor
    slot_label: "TL — 修正スコープ / Stop hook 共存設計 / 正本判定 / 再発防止 test 戦略 adversarial check（完了 2026-06-03、passed）"
  - role: se
    slot_label: "SE — merge_settings/context_guard/handover の Python 修正 + bats/pytest 追加（Codex）"
generates:
  - artifact_path: cli/lib/merge_settings.py
    artifact_type: python_module
  - artifact_path: cli/lib/context_guard.py
    artifact_type: python_module
  - artifact_path: cli/lib/handover.py
    artifact_type: python_module
  - artifact_path: .claude/settings.json
    artifact_type: config
  - artifact_path: cli/tests/test-helix-stop-hook-wiring.bats
    artifact_type: test
  - artifact_path: cli/lib/tests/test_handover_git_sync.py
    artifact_type: test
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
  - docs/plans/PLAN-081-stop-hook-auto-handover.md
  - cli/lib/merge_settings.py
  - cli/lib/context_guard.py
  - cli/lib/handover.py
  - docs/v2/L1-requirements/helix-workflows-verification-strategy.md
---

# Action: handover/session-log state 永続化基盤の修復

V2 実装計画 Process（親）の **Phase 3 readiness** 子 Action。`workflow: reverse`（normalization）で、PLAN-081 が「Stop 時に handover dump 自動実行」を受入条件に掲げながら **Stop への統合配線と統合テストを未了のまま完了主張した片肺**を既存実態から復元・正規化し、L7 実装 + L8 統合検証として Forward へ戻す。tl-advisor 2026-06-03 判定（**decision: passed / 条件付き推奨**）に基づく。

Phase 3（detector の fail-close gate 化 + CI 連動 + ST→TV→L4 推移 trace）は **現在地 state（handover/CURRENT.json）を読んで合否を出す**。その state 永続化が一度も自動発火していない（下記 BUG-1）まま gate を建てると false pass / false block を生む。よって本 Action は **Phase 3 の blocker 解消**であり、Phase 3 着手の前提。

## 1. 診断 baseline（read-only verified、file:line 証跡付き、2026-06-03）

| ID | 欠陥 | 証跡 | severity |
|---|---|---|---|
| **BUG-1** | `cli/helix-stop-hook`（auto_dump=git HEAD 再取得して CURRENT.json 更新、実装完成済）が hook 正本に**一度も配線されていない**。Stop には `helix-session-summary`（cost_log INSERT のみ）だけ | pickaxe `git log -S 'helix-stop-hook' -- .claude/settings.json` = 空 / `merge_settings.py:95-107` Stop に session-summary のみ / `context_guard.py:243` required_hooks に Stop=session-summary のみ | **P0** |
| **BUG-2** | `handover update`（`cmd_update`）が git HEAD を再取得せず既存 git ブロックを継承 | `handover.py:847-997` | P1 |
| **BUG-3** | `handover resume` が `current_sha` を取得するが CURRENT.json の `git.head_sha` に代入しない | `handover.py:1183-1223` | P1 |
| **BUG-4** | stale 判定の reachability window が `git log -n 50` 固定。50 commit 超で false-negative | `handover.py:660` | P2 |
| **BUG-5** | session-summaries 無制限蓄積（rotation 無し、handover と decoupled、20 files） | `helix-gate:885-896` | P2（**carry**） |

**真因の性格（重要）**: BUG-1 は事故（settings.json auto-regen 脱落）ではなく、**PLAN-081（[docs/plans/PLAN-081](docs/plans/PLAN-081-stop-hook-auto-handover.md) §4.5）が「動作確認は手動（helix-stop-hook 単独実行）」「統合 test は内部 Phase4 carry」と記載し、Stop 統合と end-to-end fire test を未了のまま受入条件充足を主張した片肺**。HELIX Core §0 が禁じる「未検証の実装主張」。fire を assert する test が無いため gap が silent 化し、CURRENT.json head_sha が stale（14705bb vs 実 HEAD）化していた。

**正本の所在（TL が特定）**: hook 配線の canonical source は `.claude/settings.json` ではなく **`cli/lib/merge_settings.py` の `HELIX_HOOKS`**。`.claude/settings.json` はそこから materialize される出力。直接編集では regen で落ちるため不十分。drift 検出役の `context_guard.py required_hooks` に `helix-stop-hook` が無いことが未検出の構造的原因。

## 2. TL 裁定（2026-06-03、passed / 条件付き）

- **スコープ**: P0(BUG-1) + PLAN-081 が defer した統合 fire test + P1(BUG-2/3) + P2(BUG-4) を **1 単位で修復**。BUG-5 は carry。
- **Stop hook 設計**: `helix-session-summary` と `helix-stop-hook` を **2 entry 並列登録**（統合せず=failure domain / test 責務を分離）。`blockOnFailure:false` 維持、timeout 8/10。
- **正本**: `merge_settings.py HELIX_HOOKS` を編集。`.claude/settings.json` は regen で更新。配布契約は merge_settings.py + setup.sh/helix init で閉じる。
- **drift 防止**: `context_guard.py required_hooks` に `("Stop","helix-stop-hook","")` 追加（core_manifest_drift と同型の機械検出）。
- **BUG-4**: 固定 window 廃止 → `git merge-base --is-ancestor <saved_sha> HEAD`（または `cat-file -e <sha>^{commit}` + ancestor）へ。
- **refactor 許容**: `collect_git_snapshot(project_root)` helper を `handover_auto_dump` / `cmd_update` / `cmd_resume` で共通化（大きな module 分割・summary rotation 設計には広げない）。

## 3. 作業（実装=Codex se 委譲、Opus が成果物検証）

1. **BUG-1 配線**: `merge_settings.py HELIX_HOOKS` の `Stop` に `helix-stop-hook` entry を追加（type=command / `_hook_command(helix_home,"cli/helix-stop-hook")` / timeout=10 / blockOnFailure=False）→ session-summary と 2 entry 並列。`.claude/settings.json` を merge 経路で再生成。
2. **drift guard**: `context_guard.py required_hooks` に `("Stop","helix-stop-hook","")` 追加。
3. **BUG-2/3 同期**: `collect_git_snapshot()` helper を新設し、`cmd_update`（owner/status/complete/note 更新時）と `cmd_resume`（復帰時）で `git.branch/head_sha/dirty` を再取得・代入。`handover_auto_dump` も同 helper へ寄せる。
4. **BUG-4 ancestor 判定**: `handover.py:660` の固定 window を ancestor 判定へ置換。

## 4. 再発防止 test（Codex、必須 5 本 + 任意）

- **bats E2E**: settings を merge_settings.py / helix init 相当で生成し、Stop hooks に `helix-session-summary` と `helix-stop-hook` が**両方**在ることを assert。
- **bats E2E**: fixture repo で CURRENT.json を古い head_sha にし、`cli/helix-stop-hook` 実行 → `git rev-parse HEAD == CURRENT.json.git.head_sha` + revision++ を assert。
- **pytest**: `cmd_update` が更新時に git branch/head_sha/dirty を再取得すること。
- **pytest**: `cmd_resume` が CURRENT.json の `git.head_sha` を current HEAD に更新すること。
- **drift guard test**: `context_guard`（または merge_settings）test が `helix-stop-hook` 欠落を `missing_hook` として検出すること。
- 任意: stale 判定の ancestor ロジックを `run_git` mock で固定する unit test。

## 5. acceptance / 再凍結条件（L8）

- 上記 5 必須 test が全 PASS（`bash -n cli/helix-stop-hook` / 対象 pytest / 対象 bats）。
- 手動 smoke: 実 Stop（または `cli/helix-stop-hook` 直接 invoke）で CURRENT.json head_sha が実 HEAD と一致し revision++ することを evidence に残す（Claude Code runtime の Stop fire 挙動は外部依存のため手動 evidence 必須）。
- `helix doctor` が baseline（24-0-105）を維持または改善（stale locks / mode・phase 整合の悪化なし）。
- `context_guard` drift guard が helix-stop-hook 欠落を検出する状態になっている。
- handover CURRENT.json の git.head_sha が今後 session 終了ごとに自動同期される（BUG-1 解消の実証）。

## 6. forward_return

L7（実装: 配線 + handover 同期 + drift guard + test）→ **L8 統合検証**（Stop hook fire + settings drift guard を通して再凍結）。親 Process（V2 roadmap）の forward_return = 全 pair 収束に従属し、本 Action は Phase 3 着手の前提条件として L7/L8 へ戻す。PLAN-081 の受入契約と実態の gap を回収するものであり、要件追加ではない。

## 7. carry

- **BUG-5**（session-summaries rotation / 蓄積 governance）= P2 carry。Phase 3 gate の合否正当性に二次的なため本 Action 必須スコープ外。
- グローバル `~/.claude/settings.json`（ユーザー環境 state）はリポ内 test だけでは保証不可 → setup.sh merge と helix init の両導線での検査を carry として明示。

## 8. closure（L8 passed、2026-06-03）

- 実装 commit `10a6412` `fix(hook): Stop hook 配線 + head_sha 同期で PLAN-081 片肺回収`（9 files、472+/31-）。
- **PM 独立検証**（Codex summary を鵜呑みにせず実体確認）:
  - 独立 pytest 42 passed + merge_settings 22 passed + 新規 test_handover_git_sync。
  - フル bats suite green（not ok 0 件）+ 新規 test-helix-stop-hook-wiring.bats 2/2 + session-summary 回帰 8/8。
  - `helix doctor` 24-0-105 baseline 維持（回帰なし）。
  - settings.json: 他 hook 脱落ゼロ / helix-stop-hook 重複なし / content idempotent。
  - 手動 Stop smoke: 実 repo で `helix-stop-hook` invoke → head_sha=実 HEAD 一致 / revision++。
- BUG-1(P0) / BUG-2,3(P1) / BUG-4(P2) 解消。context_guard drift guard で再発を機械封鎖。
- **forward_return 達成**: PLAN-081 の「Stop 統合 + 統合 test」未了契約を回収（L7 実装 → L8 統合検証 passed）。
- **carry**: BUG-5（summaries rotation）/ global `~/.claude/settings.json` の setup.sh・helix init 両導線検査。

## 9. forward-return-discipline 遡及適用（2026-06-03、deferred finding）

[forward-return-discipline.md](../../../HELIX-workflows/helix-process/forward-return-discipline.md) 新設に伴い本 PLAN の forward_return を遡及再評価する（retrofit-2026-06-03-driving-forward-return-discipline §7）。

- `touched_layers`: L7（実装）+ L8（統合検証）。
- `design_change_class`: **`design_or_contract_changed`**（`pure_impl` ではない）。理由: `collect_git_snapshot` / `refresh_git_snapshot` / `previous_head_sha` 機構を**新設**し、`cmd_update` / `cmd_resume` の関数責務（head_sha 再取得）を**変更**した = 関数仕様（L6 DbC）が変わる変更。
- `required_refreeze_pairs`: **L6↔L7**（変更/新設関数の DbC 機能設計）。
- `refreeze_evidence`: 実装・統合テスト（L7→L8）は passed だが、**L6 機能設計（DbC: requires/ensures）の再凍結は未実施＝片肺**。
- **判定**: 本 PLAN は機能（実装+統合テスト）として完了しているが、V-model 基準（§forward-return-discipline R1）では L6↔L7 design 対が片肺。**§8 の `completed` は「機能完了」を指し、V-model pair 完全凍結ではない**。
- **deferred finding `DF-FRD-001`**: 変更/新設関数（collect_git_snapshot 等）の L6 機能設計 DbC 再凍結を Phase A 後の carry とする（forward-return-discipline Phase C で detector が機械検出する対象の第 1 号）。本 finding を残すことで「片肺を completed で放置しない」規律を満たす。
