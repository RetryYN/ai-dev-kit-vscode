---
plan_id: PLAN-207
title: "PLAN-207: HELIX runtime PoC sandbox (実 framework 分離実験環境)"
kind: impl
layer: L4
drive: be
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-099-autonomous-runtime-framework-5layer.md   # from dependencies.parent
size: M
created: 2026-05-23
revised: 2026-05-23
owner: PM
agent_slots:
  - role: se
    slot_label: "SE — helix sandbox CLI 実装 (start/stop/reset/merge-to-main) + sandbox_manager.py + helix.db 分離"
  - role: qa
    slot_label: "QA — sandbox isolation テスト (main helix.db への不意の書き込みがないことの検証)"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-099 / PLAN-092 helix.db 設計との整合確認・merge-to-main 境界条件レビュー"
generates:
  - artifact_path: cli/helix-sandbox
    artifact_type: cli_extension
  - artifact_path: cli/lib/sandbox_manager.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_sandbox_manager.py
    artifact_type: test
  - artifact_path: docs/commands/sandbox.md
    artifact_type: markdown_doc
dependencies:
  parent: PLAN-099
  requires:
    - PLAN-092
    - PLAN-099
  blocks: []
related_adr: []
related_plans:
  - PLAN-099 (自動走行 framework 5-layer — Layer 4/5 PoC の主な利用場)
  - PLAN-092 (PostToolUse plan 自動登録 — helix.db schema 正本)
  - PLAN-086 (helix db rollback — sandbox 不在時の代替手段)
acceptance_criteria:
  - "helix sandbox start が .helix-sandbox/ を作成し、HELIX_SANDBOX_MODE=1 配下で helix.db / handover / settings を分離した状態で動作する"
  - "sandbox 動作中は main .helix/helix.db への書き込みが発生しない (isolation test PASS)"
  - "helix sandbox stop / reset / status / merge-to-main --dry-run が正常動作する"
  - "python3 -m py_compile cli/lib/sandbox_manager.py PASS"
  - "unit test 12 case PASS (start / stop / reset / isolation 2 件 / merge dry-run / merge 実行 / HELIX_SANDBOX_MODE 検出 / 既存 sandbox 上書き guard / main 汚染なし / settings 分離 / handover 分離 / cleanup)"
---

# PLAN-207: HELIX runtime PoC sandbox (実 framework 分離実験環境)

## L2 凍結 (ADR snapshot)

sandbox の実現方式 (env var override vs `.helix-sandbox/` shim) の選択は
L2 大局判断に相当する可能性がある。Sprint .1 での技術調査で既存 CLI との
非互換が明らかになった場合、ADR snapshot を後追い起票する。

## 背景

HELIX は `.helix/helix.db` / `.helix/handover/CURRENT.json` / `.claude/settings.json`
を runtime state として使用する。PoC・検証目的で新しい hook や CLI を試す際、
これらが本番の実行履歴・handover 状態を汚染するリスクがある。

具体的な課題を 3 件挙げる。

1. **PLAN-099 Layer 4/5 PoC**: SessionStart + ScheduleWakeup heartbeat の動作確認を
   本番 session 内で行うと main helix.db の scheduler log・session record が混在する
2. **hook 設計変更の試行**: PreToolUse / PostToolUse の新実装を settings.json に
   追加して試す際、既存 hook の安定動作を保証しながらテストできない
3. **helix.db migration テスト**: schema migration のリハーサルを本番 DB で行うと
   `helix db rollback` (PLAN-086) を消費する

## WebSearch 履歴

- Query 1: "shell environment variable override test isolation helix db path sandbox pattern"
  → `XDG_DATA_HOME` 等の path override env var で state dir を切り替えるパターンが標準的。
     `TMPDIR` override と組み合わせて完全 isolation を実現する例を確認
- Query 2: "python tempfile sandbox isolation testing helix db cli integration test pattern"
  → `tempfile.mkdtemp()` + `os.environ.update({'HELIX_DB_PATH': tmp_path})` で
     pytest integration test の isolation を実現するパターンが標準
- Query 3: "git worktree sandbox isolation runtime state separation CLI tool best practice 2025"
  → git worktree は branch 分離、sandbox は同一 worktree 内の runtime state 分離で役割を明確化できる

## 設計方針

### 分離方式: 環境変数 override

`.helix-sandbox/` を作成した後、以下の env var を設定して子プロセスを起動する:

```
HELIX_SANDBOX_MODE=1
HELIX_DB_PATH=.helix-sandbox/helix.db
HELIX_HANDOVER_DIR=.helix-sandbox/handover
HELIX_SETTINGS_PATH=.helix-sandbox/settings.json
```

main `.helix/` は読み取り専用の参照元として残す (初期 copy の元データ)。
`cli/lib/helix_db.py` に sandbox 検出処理を追加し、`HELIX_SANDBOX_MODE=1` かつ
`HELIX_DB_PATH` が main `.helix/helix.db` を指す場合は警告して abort する。

### helix sandbox コマンド仕様

```
helix sandbox start [--copy-from-main] [--clean]
  .helix-sandbox/ 作成、sandbox を開始。
  --copy-from-main: main helix.db / handover / settings を初期値として copy。
  --clean: 既存 .helix-sandbox/ を削除してから作成。

helix sandbox stop
  HELIX_SANDBOX_MODE 解除の案内を表示。.helix-sandbox/ は保持。

helix sandbox reset
  .helix-sandbox/ を削除して clean state に戻す。

helix sandbox status
  sandbox 動作中かどうかを表示 (HELIX_SANDBOX_MODE + .helix-sandbox/ 存在確認)。

helix sandbox merge-to-main [--dry-run] [--select <table>]
  sandbox helix.db を main helix.db にマージ。
  --dry-run: 差分表示のみ。重複 plan_id / task_id は insert-or-ignore。
```

### sandbox_manager.py

```python
class SandboxManager:
    def start(self, copy_from_main=False, clean=False) -> dict[str, str]: ...
    def stop(self) -> None: ...
    def reset(self) -> None: ...
    def status(self) -> dict: ...
    def merge_to_main(self, dry_run=True, select=None) -> list[str]: ...
```

merge-to-main の拒否条件: sandbox helix.db 不在 / main DB が sandbox より新しい /
`--select` テーブルが sandbox DB に不在。

## 実装計画

### Sprint .1: sandbox_manager.py skeleton (Codex se、size S)

既存 CLI の env var 参照状況を確認し実現可能性を検証。
sandbox_manager.py の start / stop / reset / status を実装。
`python3 -m py_compile` PASS + unit test 6 case PASS が完了条件。
技術選定で既存 CLI と非互換が判明した場合は ADR snapshot を起票。

### Sprint .2: helix sandbox CLI + merge-to-main (Codex se、size S)

`cli/helix-sandbox` の 5 サブコマンドを実装。`merge_to_main()` 追加。
unit test 6 case (merge dry-run / merge 実行 / main 汚染なし / settings 分離 /
handover 分離 / cleanup) PASS が完了条件。

### Sprint .3: QA isolation テスト + docs (Codex qa → Codex docs、size S)

sandbox start → helix plan lint → main DB 汚染なし の end-to-end 確認。
`docs/commands/sandbox.md` 起草。pmo-sonnet review が完了条件。

## mandatory in sprint

- [ ] `python3 -m py_compile cli/lib/sandbox_manager.py` PASS
- [ ] unit test 12 case 全 PASS
- [ ] sandbox 動作中の main helix.db 非汚染確認
- [ ] `bash -n cli/helix-sandbox` PASS
- [ ] pmo-sonnet review (Sprint .3)

## DoD

- [ ] helix sandbox start / stop / reset / status / merge-to-main 実装完了
- [ ] HELIX_SANDBOX_MODE=1 で sandbox 参照、main env 非汚染
- [ ] merge-to-main --dry-run で安全な差分確認が可能
- [ ] unit test 12 case PASS
- [ ] docs/commands/sandbox.md 起草完了

## V-model 4 artifact trace

| artifact | 対象 |
|---|---|
| ① 設計 | 本 PLAN §設計方針 |
| ③ テスト設計 | cli/lib/tests/test_sandbox_manager.py (Sprint .1-.2 同時起票) |
| ② 実装コード | cli/helix-sandbox + cli/lib/sandbox_manager.py |
| ④ テストコード | cli/lib/tests/test_sandbox_manager.py |

双方向 trace:
- 本 PLAN → テストコード: acceptance_criteria に 12 case の検証内容を記載
- テストコード → 本 PLAN: docstring に「PLAN-207 §acceptance_criteria」明記

## 関連 reference

- PLAN-099 (自動走行 framework 5-layer — Layer 4/5 PoC の主な利用者)
- PLAN-092 (PostToolUse plan 自動登録 — helix.db schema 正本)
- PLAN-086 (helix db rollback — sandbox 不在時の代替手段)
- cli/lib/helix_db.py (helix.db 操作ロジック)
