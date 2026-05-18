# helix db コマンドガイド

`helix db rollback` は **dev 限定** の rollback 試演ツールです。production retreat は `v32_undo_v31.py` のような **forward-only undo migration** を優先してください。根拠は `docs/adr/ADR-020-cutover-rollback-gates.md` Decision.2。

## 使い方

```bash
helix db rollback --to v30 --backup-path .helix/backups/<timestamp>_pre_v31.db [--confirm] [--discard-diff|--export-diff <path>]
```

## 挙動

- `--confirm` なし:
  preflight のみ実行し、現在の `schema_version`、backup の `schema_version`、archive 先、diff event 件数を表示します。
- `--confirm` あり:
  `.helix/helix.db` を `.helix/helix.db.pre-rollback.bak` に退避し、backup を restore します。
- split DB archive:
  `.helix/{orchestration,vmodel,scrum,plan,backend,frontend}.db` を `.helix/v31-archive/<timestamp>/` に退避します。
- diff event:
  デフォルトは `--discard-diff` です。`--export-diff <path>` を付けると archive 済み DB の `event_envelope` を SQLite `.dump` ベースの JSON で保存します。

## 実装メモ

- schema version 判定は `PRAGMA user_version` ではなく `schema_version` table を使用します。
- `cli/lib/rollback_orchestrator.py` の preflight は advisory として再利用し、confirm token などの SaaS 前提は CLI 側で要求しません。
- rollback 完了後は `helix doctor` を実行し、ローカル環境の健全性を再確認します。
