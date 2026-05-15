# helix DB v21 仕様

## 概要

本書は `helix_db.py` の実装を正本として、`helix.db` v21 スキーマの正式仕様を定義する。
`docs/v2/B-design/v21-migration-sql-draft.sql` はドラフト版であり、本仕様により
運用時の最終合意文書化を行う。

v21 は v20 以降の拡張として、設計ドライブ・起点モード・証跡状態を
`contract_entries` と設計スプリントに追加し、`functional_freeze` ゲート評価を
DB レイヤーで正規化することを目的とする。

## 対象

- `cli/lib/helix_db.py`\n- `DESIGN_SPRINT_ENTRIES_SCHEMA_V21`\n- `DESIGN_SPRINT_ARTIFACT_LINKS_SCHEMA_V21`\n- `VIEW_VMODEL_INTEGRITY_V21`\n- `_migrate_v20_to_v21`\n+- `query_functional_freeze_status`

## v21 導入条件

- `contract_entries` に 3 追加列を追加する。
- `design_sprint_entries` と `design_sprint_artifact_links` の v21 定義を作成。
- `view_vmodel_integrity` の v21 を作成し既存参照を更新。
- 移行は additivie / idempotent であること（既存データを壊さない）。

## 1. `contract_entries` 追加列（実装準拠）

### 新規列
\n
| 列名 | 型 | NOT NULL | 意味 |
| --- | --- | --- | --- |
| `drive` | `TEXT` | はい | 対象ドライブ（`be`, `fe`, `db`, `fullstack`） |
| `origin_mode` | `TEXT` | はい | `forward` / `reverse` / `scrum`（HELIXフロー起点） |
| `evidence_status` | `TEXT` | はい | `pending` / `collected` / `missing` / `invalid` |

### 制約（提案）

本体実装は列追加のため緩い形状だが、運用上は以下を推奨:

- `drive` は vmodel drives と一致する値に限定
- `origin_mode` は enum 化して運用監査を容易化し、値は `forward` / `reverse` / `scrum` とする
- `append` / `fork` / `rebase` は record-level 起源軸（実装準拠）として別管理し、L3 schema で再評価する
- `evidence_status` は列挙値を固定し、監査要件に適合

### DDL（想定）

```sql
ALTER TABLE contract_entries
ADD COLUMN drive TEXT NOT NULL DEFAULT 'be';

ALTER TABLE contract_entries
ADD COLUMN origin_mode TEXT NOT NULL DEFAULT 'forward';

ALTER TABLE contract_entries
ADD COLUMN evidence_status TEXT NOT NULL DEFAULT 'pending';
```

注意: v21 実装は idempotent な追加を担保するため、既存行の欠落は既定値で埋める。

## 2. `design_sprint_entries`（v21）

### 目的

- plan と drive・layer 毎の設計 pair の進捗を追跡。
- `functional_freeze` ゲート判定の直接参照元。
\n
### スキーマ要件

- 既存カラムを拡張し `drive`, `origin_mode`, `evidence_status` が参照可能であること。
- `sprint_type` は `architecture` / `detailed` / `functional` / `impl` のいずれか。
- `layer` は `architecture` / `detailed` / `functional` のみ。
- `pair_status` は `pending`, `design_only`, `test_only`, `paired`, `waived`, `failed`。
- `sprint_type='impl'` の場合は `layer='functional'` を許可。

実装上の CHECK 制約:

```sql
CHECK (
  (sprint_type IN ('architecture','detailed','functional') AND layer IN ('architecture','detailed','functional'))
  OR (sprint_type='impl' AND layer='functional')
)
```

### インデックス方針

```sql
CREATE INDEX IF NOT EXISTS idx_design_sprint_plan_drive_layer
ON design_sprint_entries(plan_id, drive, layer);
```

### 追加列との関係

- `drive` が未指定でも保存可能に見えるケースはあるが、設計上は NOT NULL を推奨。
- `origin_mode` / `evidence_status` は監査性のため、`query_functional_freeze_status` には最小値で参照される。

## 3. `design_sprint_artifact_links`（v21）

### 目的
\n
設計エントリと artifact の関連付けを保持し、pair と設計証跡をトレース可能にする。

### 主要構造

- 複合主キー（`entry_id`,`artifact_id`）を採用。
- `artifact_kind` と `link_kind` は正規化された文字列。\n- `entry_kind` は `design` / `test` / `pair` の文脈に依存。\n
### 代表例

```sql
CREATE TABLE IF NOT EXISTS design_sprint_artifact_links (
  entry_id TEXT NOT NULL,
  artifact_id TEXT NOT NULL,
  artifact_kind TEXT NOT NULL,
  link_kind TEXT NOT NULL,
  details TEXT,
  created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  PRIMARY KEY (entry_id, artifact_id, artifact_kind, link_kind),
  CHECK (artifact_kind IN ('doc', 'sql', 'code', 'test', 'artifact')),
  CHECK (link_kind IN ('implements', 'tests', 'evidence'))
);
```

## 4. `view_vmodel_integrity`（v21）

`view_vmodel_integrity` は 4 層連鎖をまとめて監査するビュー:

1. `contract`（契約基点）\n2. `code_index`（実コード境界）\n3. `test_design`（テスト設計）\n4. `baseline`（実装結果ベースライン）\n
実装 SQL では `FULL OUTER` 相当（SQLite では LEFT JOIN + COALESCE）を使う
ため、欠損も可視化し、missing 系スコアを算出する。

### 表示項目（主要）

- `vmodel_score`\n
- `contract_id`, `plan_id`, `drive`, `layer`\n
- `missing_contract`, `missing_code`, `missing_test`, `missing_baseline`\n
- `paired_count`, `pending_count`, `failed_count`\n

### スコア計算方針

`vmodel_score` は `pairing` と `test` の成立を考慮した集計で、\n
`vmodel_score` 不足時は `missing_` 系フラグで監査時に拾いやすくする。\n
`ROW_NUMBER`, `COUNT` を使った window 的な重複排除ロジックで、同一 design が複数レコードに重複しても過大評価しない。

### DDL 断片

```sql
CREATE VIEW IF NOT EXISTS view_vmodel_integrity AS
SELECT
  c.plan_id AS plan_id,
  d.se_drive AS drive,
  d.layer,
  COUNT(*) AS paired_count,
  SUM(CASE WHEN d.pair_status='failed' THEN 1 ELSE 0 END) AS failed_count,
  SUM(CASE WHEN d.pair_status='pending' THEN 1 ELSE 0 END) AS pending_count,
  COALESCE(MAX(vmodel_score), 0) AS vmodel_score,
  ...
FROM contract_entries c
LEFT JOIN design_sprint_entries d ON c.contract_key = d.contract_key
LEFT JOIN design_sprint_artifact_links l ON l.entry_id = d.id
...
GROUP BY c.plan_id, d.se_drive, d.layer;
```

（SQL は省略版。実装は `cli/lib/helix_db.py` の `VIEW_VMODEL_INTEGRITY_V21` を正本とする。）

## 5. Migration `_migrate_v20_to_v21`

### 目標

- v20 DB を壊さず v21 仕様へ段階移行。
- 既存 table が存在しない場合は作成。
- 同一カラムの再追加を回避（idempotent）。

### 手順（実装準拠）
\n
1. `ALTER TABLE contract_entries` を追加。\n2. `DESIGN_SPRINT_ENTRIES_SCHEMA_V21` 定義で table を作成。\n3. `DESIGN_SPRINT_ARTIFACT_LINKS_SCHEMA_V21` 定義で table を作成。\n4. `CREATE VIEW_VMODEL_INTEGRITY_V21` 作成。\n5. `view_vmodel_integrity` を v21 へ再定義。\n\n
### 擬似フロー

```python
def _migrate_v20_to_v21(conn):
    _safe_add_column(conn, "contract_entries", "drive", "TEXT NOT NULL DEFAULT 'be'")
    _safe_add_column(... "origin_mode", "TEXT NOT NULL DEFAULT 'forward'")
    _safe_add_column(... "evidence_status", "TEXT NOT NULL DEFAULT 'pending'")
    _create_table_if_not_exists("design_sprint_entries", DESIGN_SPRINT_ENTRIES_SCHEMA_V21)
    _create_table_if_not_exists("design_sprint_artifact_links", DESIGN_SPRINT_ARTIFACT_LINKS_SCHEMA_V21)
    _execute(VIEW_VMODEL_INTEGRITY_V21)
    _replace_view("view_vmodel_integrity", VIEW_VMODEL_INTEGRITY_V21)
```
\n
`_safe_add_column` 相当のラッパーにより重複追加防止。

## 6. `query_functional_freeze_status` ヘルパー
\n
### 契約\n+
- 入力: `plan_id`, `drive`\n
- 返却: `passed / failed / missing` と詳細カウント\n
### 判定アルゴリズム

1. `design_sprint_entries` から次の絞り込み:\n
   - `plan_id = ?`\n   - `drive = ?`\n   - `sprint_type='functional'`\n   - `layer='functional'`\n
2. `pair_count`, `failed_count`, `waived_count`, `missing_count` を集計。\n
3. 判定:\n
- `pair_count==0` -> `missing`\n
- `failed_count>0` -> `failed`\n

- `waived` は失敗にならないが、監査上は別途報告。\n
4. 結果を JSON/文字列で呼び出し側へ返却。\n
### 例（SQL）
\n
```sql
SELECT
  COUNT(*) AS pair_count,
  SUM(CASE WHEN pair_status='failed' THEN 1 ELSE 0 END) AS failed_count,
  SUM(CASE WHEN pair_status='waived' THEN 1 ELSE 0 END) AS waived_count,
  SUM(CASE WHEN pair_status IN ('pending','design_only','test_only') THEN 1 ELSE 0 END) AS missing_count
FROM design_sprint_entries
WHERE plan_id=? AND drive=? AND sprint_type='functional' AND layer='functional';
```

## 7. `functional_freeze` ゲートとの整合
\n
`cli/helix-gate` の `--subgate functional_freeze` は本 helper を用いて下記を評価する。

- `drive`: `be/fe/db/fullstack`\n
- サイズルール: `size=L` もしくは `drive in fe,fullstack,db` は実行強制。\n
- 失敗の条件: helper の `failed`。\n- 不足の条件: helper の `missing`。\n
## 8. 監査・運用上の受入条件
\n
- v21 で view/テーブルの自動生成が成功する。\n- 既存 v20 データが `drive/default` 付与で失われない。\n- `gate functional_freeze` が `verdict` を返却し、exit code がマッピングどおりである。\n- `view_vmodel_integrity` の主要列が監査に利用可能。\n\n
## テスト観点（実装整合の確認）
\n
- migration 実行後に `contract_entries` の追加列が存在する。\n- `DESIGN_SPRINT_ENTRIES_SCHEMA_V21` の CHECK 条件で不整合が拒否される。\n- `functional_freeze` の `pair_count=0` は `missing` を返す。\n- `failed_count>0` で `failed` 判定となる。\n- 既存 v20 レコードを削除しない。\n\n
## 実装リンク\n+\n+- `cli/lib/helix_db.py`\n+- `docs/v2/B-design/v21-migration-sql-draft.sql`\n+- `cli/helix-gate`\n+\n+## 変更履歴\n+\n+- v1.0 HELIX V2 Phase2: v21 実装準拠仕様を新規追加\n*** End Patch
