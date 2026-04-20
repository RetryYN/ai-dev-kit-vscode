# D-MIG-PLAN: マイグレーション計画 — helix.db v6 → v7

**Feature**: helix-budget-autothinking
**Target**: `.helix/helix.db`
**Migration ID**: v6→v7

---

## 1. 前提

### 1.1 環境前提

- HELIX CLI v5 が稼働中 (`helix test` 全 PASS)
- `.helix/helix.db` が存在 (v5 スキーマ)
- SQLite バージョン 3.35+ (DROP COLUMN サポート)
- プロジェクトが clean 状態 (未コミット変更なし推奨)

### 1.2 依存モジュール前提

- `cli/lib/db_migrate.py` (既存) にマイグレーション関数を追加できる構造
- `cli/helix` dispatcher が `migrate` サブコマンドを持つ (未存在なら追加)

### 1.3 前提チェックスクリプト

```bash
~/ai-dev-kit-vscode/cli/helix migrate --check --target 7
# 期待出力: "Current version: 6, target: 7, migration available: YES"
```

### 1.4 実行タイミング

- **初回セットアップ**: L4 実装中の bootstrap スクリプトで自動実行
- **既存プロジェクト**: `helix migrate` サブコマンドを明示実行 (ユーザー操作)
- **自動実行**: `helix-budget` 系コマンド初回呼び出し時に検知 + 警告 + 中断 (強制マイグレーションしない、ユーザー確認必要)

---

## 2. 手順

### 2.1 事前手順 (必須)

```bash
# 1. バックアップ作成
cp ~/ai-dev-kit-vscode/.helix/helix.db ~/ai-dev-kit-vscode/.helix/helix.db.backup-v6-$(date +%Y%m%d-%H%M%S)

# 2. スキーマバージョン確認
sqlite3 .helix/helix.db "SELECT version FROM schema_version WHERE id=1;"
# 期待出力: 5

# 3. データ件数記録
sqlite3 .helix/helix.db "SELECT COUNT(*) FROM skill_usage;" > /tmp/migration-pre-counts.txt
```

### 2.2 マイグレーション本体

```sql
BEGIN TRANSACTION;

-- 2.2.1 skill_usage 拡張
ALTER TABLE skill_usage ADD COLUMN effort_estimated TEXT;
ALTER TABLE skill_usage ADD COLUMN effort_actual TEXT;
ALTER TABLE skill_usage ADD COLUMN timeout_occurred INTEGER DEFAULT 0;
ALTER TABLE skill_usage ADD COLUMN tokens_used INTEGER;
ALTER TABLE skill_usage ADD COLUMN model_used TEXT;
ALTER TABLE skill_usage ADD COLUMN fallback_applied INTEGER DEFAULT 0;

-- 2.2.2 budget_events 作成
CREATE TABLE budget_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  occurred_at TEXT NOT NULL,
  event_type TEXT NOT NULL CHECK(event_type IN
    ('exhaustion', 'fallback', 'warning', 'forecast_miss', 'limit_observed')),
  model TEXT,
  pct_used REAL,
  details_json TEXT
);

-- 2.2.3 インデックス作成
CREATE INDEX idx_budget_events_at ON budget_events(occurred_at);
CREATE INDEX idx_budget_events_type ON budget_events(event_type);
CREATE INDEX idx_skill_usage_model ON skill_usage(model_used) WHERE model_used IS NOT NULL;

-- 2.2.4 version 更新
UPDATE schema_version SET version = 6, migrated_at = datetime('now') WHERE id = 1;

COMMIT;
```

### 2.3 事後検証

```bash
# バージョン確認
sqlite3 .helix/helix.db "SELECT version FROM schema_version WHERE id=1;"
# 期待: 6

# スキーマ確認
sqlite3 .helix/helix.db ".schema skill_usage" | grep -c "effort_estimated"
# 期待: 1

sqlite3 .helix/helix.db ".schema budget_events" | grep -c "CREATE TABLE"
# 期待: 1

# データ件数一致
sqlite3 .helix/helix.db "SELECT COUNT(*) FROM skill_usage;" > /tmp/migration-post-counts.txt
diff /tmp/migration-pre-counts.txt /tmp/migration-post-counts.txt
# 期待: no diff
```

---

## 3. ロールバック

### 3.1 自動ロールバック条件

以下のいずれかで自動ロールバック:
- `ALTER TABLE` / `CREATE TABLE` が SQLite エラー
- `COMMIT` 失敗
- 事後検証 (2.3) のいずれかが fail

### 3.2 ロールバック手順 (手動)

```bash
# 方法 A: バックアップから復元 (推奨)
cp .helix/helix.db.backup-v6-YYYYMMDD-HHMMSS .helix/helix.db

# 方法 B: DDL で逆マイグレーション (SQLite 3.35+)
sqlite3 .helix/helix.db <<'EOF'
BEGIN TRANSACTION;
DROP INDEX IF EXISTS idx_skill_usage_model;
DROP INDEX IF EXISTS idx_budget_events_type;
DROP INDEX IF EXISTS idx_budget_events_at;
DROP TABLE IF EXISTS budget_events;
ALTER TABLE skill_usage DROP COLUMN fallback_applied;
ALTER TABLE skill_usage DROP COLUMN model_used;
ALTER TABLE skill_usage DROP COLUMN tokens_used;
ALTER TABLE skill_usage DROP COLUMN timeout_occurred;
ALTER TABLE skill_usage DROP COLUMN effort_actual;
ALTER TABLE skill_usage DROP COLUMN effort_estimated;
UPDATE schema_version SET version = 5 WHERE id = 1;
COMMIT;
EOF
```

### 3.3 ロールバック後の確認

- `helix test` 全 PASS を確認
- `helix log report` が既存通り動作
- `.helix/budget/` ディレクトリは削除 (cached データも失効)

### 3.4 ロールバック不能ケース

- SQLite < 3.35 (DROP COLUMN 未サポート) → バックアップから復元必須
- 新規 `budget_events` にデータ投入済み → 事前に export 推奨
  ```bash
  sqlite3 .helix/helix.db ".dump budget_events" > /tmp/budget_events-backup.sql
  ```

---

## 4. リハーサル

### 4.1 開発環境でのリハーサル手順

1. **dry-run 環境作成**
   ```bash
   cp .helix/helix.db /tmp/helix-rehearsal.db
   export HELIX_DB=/tmp/helix-rehearsal.db
   ```

2. **マイグレーション実行**
   ```bash
   ~/ai-dev-kit-vscode/cli/helix migrate --target 7 --db /tmp/helix-rehearsal.db
   ```

3. **検証**
   ```bash
   sqlite3 /tmp/helix-rehearsal.db "SELECT version FROM schema_version;"
   # 期待: 6
   ```

4. **新機能テスト**
   ```bash
   HELIX_DB=/tmp/helix-rehearsal.db ~/ai-dev-kit-vscode/cli/helix budget status
   ```

5. **ロールバックリハーサル**
   ```bash
   ~/ai-dev-kit-vscode/cli/helix migrate --rollback --target 6 --db /tmp/helix-rehearsal.db
   ```

6. **環境クリーンアップ**
   ```bash
   rm /tmp/helix-rehearsal.db
   unset HELIX_DB
   ```

### 4.2 CI リハーサル

- bats テスト `cli/tests/helix-migrate-v6.bats` で自動化
- GitHub Actions で毎 push 時に migration forward + rollback + forward を実行
- 失敗時は PR ブロック

### 4.3 本番リハーサル (ユーザー環境)

1. `helix budget --help` を叩く前に `helix migrate --check` で影響確認を促す
2. 事前バックアップを必須化 (cli/helix-migrate がバックアップ失敗時は exit 1)
3. マイグレーション失敗時の復旧手順を `.helix/rules/MIGRATION-RULE.md` に記載

### 4.4 リハーサル時の既知リスク

| リスク | 発生条件 | 回避策 |
|-------|---------|-------|
| バックアップ取得失敗 | 権限不足 / 容量不足 | 事前チェック + エラー時 exit 1 |
| 既存レコードの NULL 解釈ミス | report サブコマンドの集計バグ | COALESCE で NULL → 'unknown' 変換 |
| 並列マイグレーション | 複数プロセスが同時実行 | file lock (`.helix/migrate.lock`) |
| SQLite 3.35 未満 | 旧環境 | `helix migrate --check` で version 検証 + ロールバック方式を backup のみに限定 |

---

## 5. 監視 / 検知

- マイグレーション実行時は stdout + `.helix/migrate.log` に記録
- 所要時間 > 5 秒で warning (想定 1 秒以下)
- 失敗時は必ず non-zero exit + stderr に復旧手順表示

## 6. 関連ドキュメント

- `D-DB/db-schema.md` — スキーマ詳細
- `D-DEP/dependency-map.md` — SQLite version 依存
- `D-TEST/test-design.md` — マイグレーションテスト設計
