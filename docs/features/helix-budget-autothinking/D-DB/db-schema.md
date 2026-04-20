# D-DB: DB スキーマ設計 — helix-budget + auto-thinking

**Feature**: helix-budget-autothinking
**DB**: `.helix/helix.db` (SQLite)
**Schema Version**: v6 → v7

---

## 1. エンティティ

### 1.1 既存 `skill_usage` (拡張)

```sql
-- v6 時点のスキーマ (既存、result_stdout/result_stderr まで含む)
CREATE TABLE skill_usage (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  invoked_at TEXT NOT NULL,
  skill_id TEXT NOT NULL,
  agent TEXT,
  task_hash TEXT,
  success INTEGER,
  duration_sec INTEGER,
  notes TEXT
);

-- v7 追加カラム
ALTER TABLE skill_usage ADD COLUMN effort_estimated TEXT;       -- low/medium/high/xhigh
ALTER TABLE skill_usage ADD COLUMN effort_actual TEXT;          -- 実際に指定した thinking level
ALTER TABLE skill_usage ADD COLUMN timeout_occurred INTEGER DEFAULT 0;
ALTER TABLE skill_usage ADD COLUMN tokens_used INTEGER;         -- Codex state.db から取得
ALTER TABLE skill_usage ADD COLUMN model_used TEXT;             -- gpt-5.3-codex 等
ALTER TABLE skill_usage ADD COLUMN fallback_applied INTEGER DEFAULT 0;
```

### 1.2 新規 `budget_events`

```sql
CREATE TABLE budget_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  occurred_at TEXT NOT NULL,
  event_type TEXT NOT NULL CHECK(event_type IN
    ('exhaustion', 'fallback', 'warning', 'forecast_miss', 'limit_observed')),
  model TEXT,
  pct_used REAL,
  details_json TEXT
);
```

### 1.3 新規 `schema_version` (未存在なら)

```sql
CREATE TABLE IF NOT EXISTS schema_version (
  id INTEGER PRIMARY KEY CHECK(id = 1),
  version INTEGER NOT NULL,
  migrated_at TEXT
);
INSERT OR IGNORE INTO schema_version (id, version) VALUES (1, 6);
UPDATE schema_version SET version = 7, migrated_at = datetime('now') WHERE id = 1;
```

---

## 2. 制約

| エンティティ | 制約 | 理由 |
|-----------|------|------|
| `skill_usage.effort_estimated` | NULL 許容 | 既存 v5 レコードは classifier 未使用なので NULL |
| `skill_usage.timeout_occurred` | DEFAULT 0 | 既存レコード互換 |
| `budget_events.event_type` | CHECK 制約 | 想定外 type の混入防止 |
| `budget_events.pct_used` | REAL (範囲チェックは Python 層) | 異常値 (負数/>100) は Python で破棄 |
| `schema_version.id` | CHECK(id = 1) | シングルトン保証 |

### 整合性ルール (Python 層)

- `skill_usage.fallback_applied = 1` の場合、`budget_events` に対応する `fallback` event が必ず存在する
- `timeout_occurred = 1` の場合、`notes` にエラー内容が記録される
- `pct_used` は 0.0〜100.0 の範囲に正規化 (範囲外は破棄 + warning ログ)

---

## 3. インデックス

```sql
-- budget_events は時系列クエリが主 (週次集計)
CREATE INDEX IF NOT EXISTS idx_budget_events_at ON budget_events(occurred_at);
CREATE INDEX IF NOT EXISTS idx_budget_events_type ON budget_events(event_type);

-- skill_usage の model 別集計用
CREATE INDEX IF NOT EXISTS idx_skill_usage_model ON skill_usage(model_used) WHERE model_used IS NOT NULL;

-- 既存インデックス (v5) は変更なし
-- idx_skill_usage_invoked_at (既存)
-- idx_skill_usage_skill_id (既存)
```

### インデックス設計理由

- 時系列集計 (`helix log report budget`) は `occurred_at` レンジ検索が中心
- モデル別コスト分析は `model_used` でフィルタ、`WHERE NOT NULL` で index サイズ最小化
- `event_type` は 5 種しかないが、warning/exhaustion のみ抽出するケースで効く

---

## 4. 変更影響

### 4.1 v6 → v7 マイグレーション影響

| 項目 | 影響 | 対応 |
|------|------|------|
| 既存 `skill_usage` データ | 新カラムは NULL で埋まる | NULL 許容設計、集計時は COALESCE |
| 既存コード (cli/lib/skill_dispatcher.py) | 互換性保持 (INSERT 時に追加カラム無視で動く) | SQLite の DEFAULT 機能で対応 |
| 既存テスト (bats 453件) | skill_usage schema 想定箇所を確認 | `helix test` で regression 検証 (G4 前) |
| `helix log report` | 既存 report は不変、新規 `report budget` を追加 | 新規サブコマンド |

### 4.2 ロールバック影響

SQLite は `DROP COLUMN` を v3.35+ でサポート。マイグレーションは以下の順で逆実行:

```sql
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
UPDATE schema_version SET version = 6 WHERE id = 1;
```

ロールバック手順は `D-MIG-PLAN/migration-plan.md` で詳細化。

### 4.3 パフォーマンス影響

- `skill_usage` は 1 週間で ~100-500 レコード追加想定 → 1 年で max 26000 レコード
- 新インデックス追加による INSERT 遅延: < 1ms (microbenchmark)
- `budget_events` は exhaustion/fallback のみ記録 → 週 10-20 レコード、年 1000 レコード

### 4.4 バックアップ

- `helix init --backup` で `.helix/helix.db.backup-v5` に自動バックアップ
- マイグレーション失敗時は backup から復元する手順を runbook に記載

---

## 5. JSON Blob の設計

`budget_events.details_json` の構造例:

```json
// event_type=fallback
{"from_model": "gpt-5.3-codex-spark", "to_model": "gpt-5.4-mini",
 "reason": "spark_weekly_usage > 90", "task_hash": "sha256:abcd..."}

// event_type=limit_observed
{"observed_limit_tokens": 12000000, "plan": "max",
 "week_start": "2026-04-14", "source": "exhaustion_detection"}

// event_type=forecast_miss
{"predicted_exhaustion_days": 5.5, "actual_days": 3.2,
 "delta_pct": -41, "week_start": "2026-04-14"}
```

将来 JSON Schema 検証を追加する場合は `cli/lib/budget_events_schema.json` に外出し。

---

## 6. 運用クエリ例

```sql
-- 週次 effort ミスマッチ率
SELECT
  effort_estimated,
  effort_actual,
  COUNT(*) as count,
  SUM(timeout_occurred) as timeouts
FROM skill_usage
WHERE invoked_at >= date('now', '-7 days')
GROUP BY effort_estimated, effort_actual;

-- モデル別消費
SELECT
  model_used,
  SUM(tokens_used) as total_tokens,
  AVG(duration_sec) as avg_duration
FROM skill_usage
WHERE invoked_at >= date('now', '-7 days')
AND tokens_used IS NOT NULL
GROUP BY model_used;

-- 枯渇予測精度検証
SELECT
  occurred_at,
  details_json
FROM budget_events
WHERE event_type = 'forecast_miss'
ORDER BY occurred_at DESC
LIMIT 10;
```

これらを `helix log report budget` サブコマンドで実行する。
