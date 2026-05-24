# L7 CLI HELIX Recovery 実装設計

- PLAN: `docs/plans/L7/L7-cli-helix-recovery-implplan.md`
- parent design: `HELIX-workflows/helix-process/recovery-workflow.md`
- addendum: `docs/adr/ADR-042-recommended-command-machine-vs-display-decision.md`
- 実装ファイル: `cli/helix-recovery`, `cli/lib/recovery_workflow_engine.py`, `.claude/hooks/stop-recovery-update.sh`
- テスト設計: `docs/v2/L7-test-design/L7-cli-helix-recovery-impl-test-design.md`

## 1. 目的

`helix recover` が持つ単発の診断・PLAN 起票責務とは分離し、`helix recovery` で Recovery mode workflow 全体の session 管理を担う。

## 2. CLI 契約

### `start`

- 入力: `--plan-id`, 任意で `--reopen-point`, `--dry-run`
- 振る舞い:
  - `kind: recovery` の PLAN を検証
  - `helix recover check --json` を呼び、発火条件を session に保存
  - `.helix/recovery/CURRENT.json` と `recovery-log-<PLAN_ID>.md` を初期化
  - stop-hook 未登録時は警告する

### `status`

- active session を text/json で表示
- 7 日超の active session には stale 警告を出す

### `phase`

- `--show` で現在 phase を表示
- `--advance --from RP-X --to RP-Y` で前進のみ許可

### `log`

- `--show` で recovery-log を表示
- `--append` で認識訂正履歴へ追記
- `--export` で任意 path に複製

### `postmortem`

- `cli/templates/plan/recovery/postmortem-template.md` を優先
- 不在時は `cli/templates/plan/recovery/template.md` を fallback とする

### `done`

- 通常系は `cutover_preflight()` → `cutover_execute(confirm_token=...)`
- `--skip-cutover --skip-reason` は docs-only recovery を想定
- 成功時は session を `completed` へ更新

## 3. session schema

`CURRENT.json` は以下を保持する。

- `plan_id`
- `status`
- `started_at`
- `current_phase`
- `triggered_conditions`
- `reopen_point`
- `log_path`
- `forward_target`
- `warnings`
- `completed_at`
- `skip_reason`
- `last_snapshot_at`

## 4. 発火条件と phase 選択

- `C2` を最優先し `RP-1`
- `C1`, `C4` は `RP-2`
- `C3` は `RP-3`
- 同時発火時は severity 優先、同順位なら `C2 > C1 > C3 > C4`

## 5. stop-hook 連携

- `.claude/hooks/stop-recovery-update.sh` は active session のときだけ `snapshot_on_stop()` を呼ぶ
- hook 自体の自動登録は行わない
- snapshot は `CURRENT.json.last_snapshot_at` と recovery-log timeline に反映する

## 6. 4 artifact trace

- ① 設計: この文書
- ② 実装: `cli/helix-recovery`, `cli/lib/recovery_workflow_engine.py`, `.claude/hooks/stop-recovery-update.sh`
- ③ テスト設計: `docs/v2/L7-test-design/L7-cli-helix-recovery-impl-test-design.md`
- ④ テストコード: `cli/lib/tests/test_helix_recovery.py`, `cli/tests/helix-recovery.bats`
