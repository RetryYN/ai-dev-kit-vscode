---
plan_id: L7-handover-compaction-sync-cliplan
title: "L7-handover-compaction-sync-cliplan: cli/helix-handover に compaction-sync を追加"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-25
revised: 2026-05-25
process_layer: L7
parent_design: HELIX-workflows/HELIX-process-L0-L14.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - docs/plans/L7/L7-auto-run-compaction-handover-syncplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — cli/helix-handover に compaction-sync subcommand を追加"
  - role: qa
    slot_label: "QA — bats 1件、bash -n、plan lint、settings 差分を検証"
generates:
  - artifact_path: docs/plans/L7/L7-handover-compaction-sync-cliplan.md
    artifact_type: design_doc
  - artifact_path: cli/helix-handover
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-handover.bats
    artifact_type: bats
---

## §0 PLAN concept

W37 で実装済みの `sync_handover_after_compaction()` を `cli/helix-handover` から直接起動できるようにし、dry-run と apply を軽量に切り替えられる `compaction-sync` subcommand を追加する。

## §1 背景

- compaction 後の handover snapshot helper は `cli/lib/compaction_adapter.py` に実装済み
- 現状は helper を CLI から直接叩けず、監査や手動確認に再利用しにくい
- 今回は既存 helper をそのまま呼び出し、CLI だけを薄く拡張する

## §2 scope

1. `cli/helix-handover` に `compaction-sync [--apply] [--json]` を追加する
2. default は dry-run とし、snapshot を表示する
3. `--apply` は `sync_handover_after_compaction(..., dry_run=False)` を実行する
4. `--json` は payload を構造化 JSON で返す
5. `cli/tests/test-handover.bats` に crash しないことを保証する 1 test を追加する

scope 外:

- `cli/lib/compaction_adapter.py` の仕様変更
- `cli/lib/tests/test_compaction_adapter.py` の変更
- handover schema の変更
- `.claude/settings.json` / `.vscode/settings.json` の変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + bats 1件追加 (Red) | `helix handover compaction-sync` が crash しない契約を test で固定化 | planned |
| .2 | `cli/helix-handover` 実装 | dry-run / apply / json の 3 モードが既存 helper 経由で動作する | planned |
| .3 | 回帰検証 + review | `bash -n` / bats / grep / plan lint / settings diff が通る | planned |

## §4 受入条件

- `helix handover compaction-sync` が exit 0 で dry-run payload を返す
- `helix handover compaction-sync --apply` が既存 helper の apply 分岐を呼べる
- `helix handover compaction-sync --json` が JSON を返す
- 既存 40 handover bats を壊さず、41 件以上 PASS を維持する
- `cli/lib/compaction_adapter.py` と `cli/lib/tests/test_compaction_adapter.py` は変更しない
- `helix doctor` 前提の settings 監視を壊さない

## §5 検証

- `git status --short`
- `bash -n cli/helix-handover`
- `bats cli/tests/test-handover.bats`
- `grep -c 'compaction-sync\\|sync_handover' cli/helix-handover cli/tests/test-handover.bats`
- `helix plan lint docs/plans/L7/L7-handover-compaction-sync-cliplan.md`
- `git diff -- .claude/settings.json .vscode/settings.json`

## §11 carry

- `auto_run_engine` や他 CLI からの compaction orchestration は別 wave で扱う
