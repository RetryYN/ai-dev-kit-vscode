# Runbook: helix migrate (template migration)

## 概要

HELIX framework のテンプレート (`.helix/*.yaml`, CLAUDE.md, AGENTS.md, .claude/settings.json) を最新版に追従させる。target registry は `cli/lib/migrate.py`、settings 専用 merge は `cli/lib/merge_settings.py`。

## 正常系の動作確認

```bash
helix migrate --dry-run    # 差分のみ表示
helix migrate --yes        # 適用
helix migrate --rollback   # 直近の backup から復元
```

backup は `.helix/migrate-backups/<timestamp>/` に隔離される (secret/PII を含む可能性のある settings.json を別領域に保存するため)。

## よくある障害パターン

### 1. `.claude/settings.json` が invalid JSON

**症状**: `migrate --yes` が exit code 3 で fail-close、apply されない。

**対応**: settings.json を手動で修正 → 再度 `migrate --yes`。fail-close なので破壊はない。

### 2. CLAUDE.md / AGENTS.md の text_append で重複

**症状**: 既存の HELIX セクションが二重に追記される。

**対応**: target registry の `text_append` strategy はマーカー区切りで idempotent。重複が出る場合は migrate.py の section marker (`<!-- HELIX-SECTION-BEGIN -->` 等) を確認。

### 3. rollback が backup を見つけない

**確認**: `.helix/migrate-backups/` 配下に最新 timestamp ディレクトリがあるか。
```bash
ls -lt .helix/migrate-backups/ | head -3
```

backup は apply 時にのみ作成される。dry-run では作られない。

## エスカレーション基準

- target registry に新規 entry を追加する場合 → schema 拡張に該当、TL モード Codex で設計レビュー
- secret を含む settings backup を残すか削除するか → セキュリティ判断、人間確認
