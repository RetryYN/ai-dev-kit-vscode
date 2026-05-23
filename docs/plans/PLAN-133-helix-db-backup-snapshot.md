---
plan_id: PLAN-133
title: helix.db backup auto-snapshot framework (SessionStart hook + restore CLI)
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
kind: impl
drive: be
layer: L4
size: S
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — SessionStart hook 実装・retention ロジック・bats test 起草"
  - role: pmo-sonnet
    slot_label: "PMO — hook 設計 drift 確認・既存 hook 一覧との整合チェック"
generates:
  - artifact_type: hook
    path: .claude/hooks/session-start-helix-db-backup.sh
  - artifact_type: cli_extension
    path: cli/helix-db
  - artifact_type: config
    path: .claude/settings.json
  - artifact_type: test
    path: .claude/hooks/tests/test_helix_db_backup_hook.bats
dependencies:
  requires: []
  blocks: []
  parent: null
related_adr: []
related_docs:
  - cli/helix-db
  - cli/lib/helix_db.py
  - .claude/settings.json
  - .claude/hooks/
acceptance_criteria:
  - "SessionStart hook が .helix/backup/helix-db-<timestamp>.db に自動 snapshot を作成する"
  - "直近 7 snapshot を保持し、それ以前を自動削除する (retention ポリシー)"
  - "helix db restore <timestamp> で snapshot から helix.db を復旧できる"
  - "helix db backup list で snapshot 一覧を表示できる"
  - "bash -n .claude/hooks/session-start-helix-db-backup.sh PASS"
  - "bats test (5 case) 全 PASS"
  - "既存 SessionStart hook と干渉しない"
---

# PLAN-133: helix.db backup auto-snapshot framework

## L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 SessionStart hook framework の拡張** であり、
新規の大局判断 (新 framework 採用 / fail-close 化 / 外部仕様採用) を含まない。
ADR snapshot は不要。

根拠:
- SessionStart hook 機構は既存 `.claude/hooks/` で稼働済
- helix db サブコマンド体系は PLAN-086 (helix db rollback dev) で確立済
- retention ポリシー (直近 7 件) は既存 HELIX backup 慣習と同型

## 背景

helix.db は session 跨ぎの重要 state (task_queue / skill_usage / invocation 履歴 / gate audit 等)
を保持する SQLite file。現状は以下の問題がある:

1. **session 跨ぎ破損リスク**: migration 失敗・hook 異常終了・disk full 等で
   helix.db が破損した場合に復旧経路が存在しない
2. **手動 snapshot 漏れ**: 実装中に `cp .helix/helix.db .helix/helix.db.bak` を
   手動実施しているが、忘れることが多く session 開始時の state を保証できない
3. **PLAN-086 dev rollback との補完**: PLAN-086 は dev 環境向け migration ロールバックを
   提供するが、session 単位の定期 snapshot は別 framework として確立が必要

SessionStart hook による自動 snapshot で、session 開始時点の state を常に保持し、
復旧経路を確立する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は **HELIX 内部 SessionStart hook の拡張** であり、
外部ライブラリ / 業界 standard への新規依存なし。WebSearch **skip**。

skip 理由:
- SessionStart hook 機構は本 repo 内で既稼働 (`session-start-hook-catalog.sh` 等)
- SQLite backup は標準の `cp` / `.backup` pragma のみ使用
- retention ロジック (ls + sort + tail + rm) は POSIX sh 標準機能のみ

## 設計方針

### 1. SessionStart hook トリガー

- **hook type**: SessionStart
- **実行タイミング**: session 開始時 (Claude Code セッション起動直後)
- **対象 file**: `.helix/helix.db` (存在する場合のみ実行)

Claude Code SessionStart hook stdin JSON:

```json
{
  "session_id": "...",
  "session_type": "new|resumed|cleared|compacted"
}
```

いずれの session_type でも snapshot を作成する (resumed も session 跨ぎの境界として扱う)。

### 2. snapshot 保存先と命名規則

```
.helix/backup/
  helix-db-20260523-143000.db
  helix-db-20260522-091512.db
  ...
```

- ディレクトリ: `.helix/backup/` (hook が mkdir -p で自動作成)
- ファイル名: `helix-db-<YYYYMMDD>-<HHMMSS>.db`
- タイムスタンプ: hook 実行時点の UTC (date -u +%Y%m%d-%H%M%S)

### 3. retention ポリシー (直近 7 snapshot)

```bash
BACKUP_DIR="${HELIX_HOME}/.helix/backup"
# snapshot が 7 件超の場合は古い順に削除
ls -t "${BACKUP_DIR}"/helix-db-*.db 2>/dev/null | tail -n +8 | xargs -r rm -f
```

7 件は約 1 週間分の session を想定。変更が必要な場合は `.helix/doctor-suppress.yaml`
または future PLAN で設定可能にする。

### 4. snapshot 作成方法

SQLite の `.backup` pragma ではなく単純 `cp` を採用する:

```bash
cp "${HELIX_DB}" "${BACKUP_DIR}/helix-db-${TIMESTAMP}.db"
```

理由:
- WAL mode 非使用時は `cp` で整合性が保たれる
- WAL mode 使用時は checkpoint 後に `cp` (hook 内で `sqlite3 helix.db "PRAGMA wal_checkpoint(FULL);"` を事前実行)
- `.backup` pragma は `sqlite3` binary 必須だが、`cp` は依存なし

### 5. helix db restore / list CLI 拡張

既存 `cli/helix-db` に 2 サブコマンドを追加する:

#### helix db backup list

```
$ helix db backup list
Available snapshots (newest first):
  helix-db-20260523-143000.db  (2.1 MB)
  helix-db-20260522-091512.db  (2.1 MB)
  helix-db-20260521-174433.db  (2.0 MB)
  ...
```

#### helix db restore <timestamp>

```
$ helix db restore 20260522-091512
Restoring .helix/helix.db from backup helix-db-20260522-091512.db ...
Current helix.db saved as .helix/helix.db.pre-restore
Restore complete. Run 'helix db status' to verify.
```

restore 前に現在の helix.db を `.helix/helix.db.pre-restore` として保存する
(二重安全網)。

## 実装計画

### Sprint .1: SessionStart hook 実装 (Codex se 委譲、size S)

実施内容:

1. `.claude/hooks/session-start-helix-db-backup.sh` 新規作成
   - stdin JSON から session_id を jq 抽出 (ログ用)
   - HELIX_HOME / HELIX_DB path 解決
   - `.helix/helix.db` 存在確認 (不在は skip)
   - `.helix/backup/` mkdir -p
   - WAL checkpoint 試行 (sqlite3 available の場合のみ)
   - `cp` で snapshot 作成
   - retention: ls -t + tail -n +8 + xargs rm
   - 実行完了ログを stderr に出力 (hook は stdout を Claude に返さない)
   - `bash -n` PASS を mandatory in sprint とする

Sprint .1 完了条件:
- `bash -n .claude/hooks/session-start-helix-db-backup.sh` PASS
- 手動実行で `.helix/backup/helix-db-<timestamp>.db` が作成される
- retention: 8 件目が自動削除される

### Sprint .2: helix db restore + list CLI 追加 (Codex se 委譲、size S)

実施内容:

1. `cli/helix-db` の `case` 分岐に `backup` サブコマンド追加:
   - `helix db backup list`: `.helix/backup/` 一覧を新しい順に表示
   - `helix db restore <timestamp>`: 指定 snapshot から復旧
     - pre-restore save → cp restore → 完了メッセージ
   - `helix db backup help`: 使い方表示

2. `.claude/settings.json` の SessionStart 節に hook 登録:
   ```json
   {
     "hooks": {
       "SessionStart": [
         {
           "hooks": [
             {
               "type": "command",
               "command": ".claude/hooks/session-start-helix-db-backup.sh"
             }
           ]
         }
       ]
     }
   }
   ```

Sprint .2 完了条件:
- `helix db backup list` で snapshot 一覧が表示される
- `helix db restore <timestamp>` で復旧が完了する
- settings.json 登録が `merge_settings.py` で HELIX hook として認識される

### Sprint .3: bats test + 動作実証 (Codex se 委譲、size S)

実施内容:

1. `.claude/hooks/tests/test_helix_db_backup_hook.bats` 新規作成 (5 case):
   - `test_creates_snapshot_on_session_start`: hook 実行で snapshot file が作成される
   - `test_skips_when_no_helix_db`: `.helix/helix.db` 不在時は snapshot 作成しない
   - `test_retention_removes_oldest`: 8 件目の snapshot が自動削除される
   - `test_restore_replaces_helix_db`: `helix db restore` で helix.db が置き換わる
   - `test_restore_saves_pre_restore`: restore 前に `.helix/helix.db.pre-restore` が作成される

2. 既存 SessionStart hook との干渉確認:
   - `session-start-hook-catalog.sh` 等と同時発火した場合の動作確認

Sprint .3 完了条件:
- bats test 全 5 case PASS
- helix doctor pass 数が現行以上 (regression なし)

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `bash -n .claude/hooks/session-start-helix-db-backup.sh` PASS
- [ ] bats test 全 5 case PASS
- [ ] 既存 SessionStart hook smoke test 全 PASS (干渉なし確認)
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .3 完了時)
- [ ] commit message に `PLAN-133 sprint .X` 明示

## DoD (Definition of Done)

- [ ] `.claude/hooks/session-start-helix-db-backup.sh` 実装済
- [ ] `bash -n` PASS
- [ ] `.claude/settings.json` SessionStart hook 登録済
- [ ] session 開始時に `.helix/backup/helix-db-<timestamp>.db` が自動作成される
- [ ] 直近 7 snapshot 保持・それ以前自動削除が動作する
- [ ] `helix db backup list` で snapshot 一覧表示
- [ ] `helix db restore <timestamp>` で復旧が完了し、pre-restore 保存も動作
- [ ] bats test 5 case PASS
- [ ] helix doctor pass 数が現行以上

## carry / 学び (起票時記録)

- **WAL mode 確認**: 現行 helix.db が WAL mode かどうかは Sprint .1 着手前に
  `sqlite3 .helix/helix.db "PRAGMA journal_mode;"` で確認する。WAL の場合は
  checkpoint 必須。非 WAL (DELETE mode) なら `cp` のみで整合
- **backup dir の .gitignore**: `.helix/backup/` は runtime state であり
  `.gitignore` に追加が必要。既存 `.gitignore` に `.helix/` が含まれていれば不要
- **restore 後の migration 状態**: snapshot は restore 時点の schema version を持つ。
  restore 後に現行コードと schema version が異なる場合は `helix db migrate` を
  手動実行する必要がある。`helix db restore` の完了メッセージに案内を追記する

## 関連 reference

- [[feedback_design_doc_web_search_required]] (PLAN-087 ガード、本 PLAN は skip 適用)
- [[feedback_adr_before_plan_violation]] (ADR snapshot 要否判定、本 PLAN は不要と確認)
- [[feedback_merge_settings_helix_hook_judge_bug]] (settings.json 登録時の干渉リスク)
- PLAN-086 (helix db rollback dev、restore の設計前身)
- PLAN-087 (Web 検索ガード framework)
- PLAN-089 (PostToolUse hook fail-close 設計)
- cli/helix-db (helix db サブコマンド実装)
- cli/lib/helix_db.py (SQLite access layer)
