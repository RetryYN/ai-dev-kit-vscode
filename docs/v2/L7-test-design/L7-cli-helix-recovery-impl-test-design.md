# L7 CLI HELIX Recovery テスト設計

- 対象設計: `docs/v2/L7-design/L7-cli-helix-recovery-impl-design.md`
- 対象実装: `cli/helix-recovery`, `cli/lib/recovery_workflow_engine.py`, `.claude/hooks/stop-recovery-update.sh`
- テスト実装: `cli/lib/tests/test_helix_recovery.py`, `cli/tests/helix-recovery.bats`

## 1. Unit test

`cli/lib/tests/test_helix_recovery.py`

- U-REC-001: `start` が `CURRENT.json` と recovery-log を初期化する
- U-REC-002: `start --dry-run` は永続化しない
- U-REC-003: `kind!=recovery` PLAN を拒否する
- U-REC-004: active session 重複を拒否する
- U-REC-005: 複数条件の priority で初期 phase を選ぶ
- U-REC-006: session 不在 status
- U-REC-007: phase advance 成功
- U-REC-008: phase mismatch 拒否
- U-REC-009: log append
- U-REC-010: log export
- U-REC-011: postmortem fallback template
- U-REC-012: postmortem 既存出力拒否
- U-REC-013: skip-cutover に skip reason 必須
- U-REC-014: skip-cutover completed 遷移
- U-REC-015: confirm token 形式不正
- U-REC-016: preflight fail-close
- U-REC-017: done --dry-run
- U-REC-018: done 正常系
- U-REC-019: snapshot_on_stop
- U-REC-020: recover check JSON parse
- U-REC-021: CLI main help / status exit code

## 2. Bats

`cli/tests/helix-recovery.bats`

- B-REC-001: `helix recovery --help` と `helix help` に recovery が出る
- B-REC-002: `start --dry-run`
- B-REC-003: `start` → `status`
- B-REC-004: `phase --show` / `--advance`
- B-REC-005: `log --append` / `--show`
- B-REC-006: `postmortem --output`
- B-REC-007: `done --skip-cutover --skip-reason`
- B-REC-008: session 不在 `status`
- B-REC-009: `helix commands check`

## 3. 検証観点

- recover / recovery の責務分離が維持されていること
- `cutover_orchestrator` は `done` からのみ使われること
- stop-hook は active session に限定して snapshot すること
- 4 artifact の参照が双方向で辿れること
